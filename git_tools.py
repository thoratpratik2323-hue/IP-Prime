"""
IP Prime Git Automation Tools

Professional-grade Git management: auto-commits, branch management, and syncing.
"""

import asyncio
import logging
from pathlib import Path

log = logging.getLogger("ipprime.git")

async def run_git(args: list[str], cwd: str) -> tuple[bool, str]:
    """Helper to run git commands safely."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            return True, stdout.decode().strip()
        return False, stderr.decode().strip()
    except Exception as e:
        return False, str(e)

async def git_status_check(cwd: str) -> str:
    """Check if there are changes to commit."""
    success, output = await run_git(["status", "--short"], cwd)
    return output if success else "Error checking status"

async def git_commit_and_push(message: str, cwd: str) -> str:
    """Professional commit and push flow."""
    # 1. Add all
    success, _ = await run_git(["add", "."], cwd)
    if not success: return "Failed to stage files."

    # 2. Commit
    success, output = await run_git(["commit", "-m", message], cwd)
    if "nothing to commit" in output.lower():
        return "Nothing to commit, clean tree."
    if not success: return f"Commit failed: {output}"

    # 3. Push
    success, output = await run_git(["push"], cwd)
    if success:
        return f"Successfully committed and pushed: {message}"
    return f"Push failed: {output}"

async def git_new_feature_branch(branch_name: str, cwd: str) -> str:
    """Create and switch to a new branch for a feature."""
    clean_name = branch_name.lower().replace(" ", "-")
    success, output = await run_git(["checkout", "-b", clean_name], cwd)
    if success:
        return f"Switched to new branch: {clean_name}"
    return f"Failed to create branch: {output}"
