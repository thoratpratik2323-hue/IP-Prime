"""
IP Prime — AI Code Review Engine

Point Prime at any file or diff and he'll give a structured,
no-nonsense review like a senior engineer: bugs, security issues,
performance wins, and readability notes.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional
from utils_llm import call_llm

log = logging.getLogger("jarvis.codereview")

CODE_REVIEW_SYSTEM = """You are Prime's AI Code Reviewer — an elite senior engineer.
You review code with ruthless precision and zero fluff.

Your review format is ALWAYS:
## 🔴 Critical Issues (must fix)
## 🟡 Warnings (should fix)
## 🟢 Suggestions (nice to have)
## ✅ What's Good

Be specific. Reference line numbers. Do not be vague.
If the code is clean and solid, say so confidently. Don't pad with unnecessary suggestions.
"""


class CodeReviewer:
    """AI-powered code review on any file or snippet."""

    def __init__(self, anthropic_client):
        self.client = anthropic_client

    async def review_file(self, file_path: str) -> str:
        """Review a single file. Returns a formatted review string."""
        path = Path(file_path)
        if not path.exists():
            return f"Error: File not found — {file_path}"

        content = path.read_text(encoding="utf-8", errors="ignore")
        if len(content) > 15000:
            content = content[:15000] + "\n\n... [truncated for review]"

        log.info(f"Reviewing file: {path.name}")
        return await self._request_review(
            f"File: {path.name}\n\n```\n{content}\n```"
        )

    async def review_diff(self, diff_text: str) -> str:
        """Review a git diff output. Returns a formatted review string."""
        log.info("Reviewing git diff...")
        return await self._request_review(
            f"Git Diff:\n\n```diff\n{diff_text}\n```"
        )

    async def review_snippet(self, code: str, language: str = "python") -> str:
        """Quick review of a code snippet dropped into chat."""
        return await self._request_review(
            f"Language: {language}\n\n```{language}\n{code}\n```"
        )

    async def get_current_diff(self, repo_path: str) -> str:
        """Get the current git diff of the repo and trigger a review."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "diff", "--staged",
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            diff = stdout.decode().strip()
            if not diff:
                # Fall back to unstaged
                proc2 = await asyncio.create_subprocess_exec(
                    "git", "diff",
                    cwd=repo_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout2, _ = await proc2.communicate()
                diff = stdout2.decode().strip()

            if not diff:
                return "No changes detected in the current repository."

            return await self.review_diff(diff)
        except Exception as e:
            return f"Failed to get diff: {e}"

    async def _request_review(self, code_content: str) -> str:
        """Send code to the AI and get back a structured review."""
        try:
            review = await call_llm(
                client=self.client,
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                system=CODE_REVIEW_SYSTEM,
                messages=[{"role": "user", "content": code_content}],
                temperature=0.1,
            )
            return review
        except Exception as e:
            return f"Code review failed: {e}"
