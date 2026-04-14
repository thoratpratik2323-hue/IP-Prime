"""
IP Prime Auto-Debug Loop

Wraps command execution with AI-powered error catching and automatic fixing.
"""

import asyncio
import logging
import subprocess
from typing import Optional
from utils_llm import call_llm

log = logging.getLogger("ipprime.debug")

class AutoDebugLoop:
    """Runs a command and fixes it automatically if it fails."""

    def __init__(self, anthropic_client):
        self.client = anthropic_client

    async def run_and_fix(self, command: str, cwd: str, max_retries: int = 3):
        """Execute a command. If it fails, ask AI for a fix and retry."""
        attempt = 0
        current_command = command

        while attempt < max_retries:
            attempt += 1
            log.info(f"Running command (Attempt {attempt}): {current_command}")
            
            # Run the command
            process = await asyncio.create_subprocess_shell(
                current_command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                log.info("Command succeeded!")
                return True, stdout.decode()

            # Command failed — capture error
            error_msg = stderr.decode() or stdout.decode()
            log.warning(f"Command failed with error: {error_msg}")

            if attempt >= max_retries:
                break

            # Ask AI for a fix
            log.info("Requesting fix from AI...")
            fix_response = await call_llm(
                client=self.client,
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                system=(
                    "You are an expert debugger. You take a failed command and its error message, "
                    "and provide a fixed command or a set of shell commands to resolve the issue. "
                    "Respond with ONLY the shell command to run. No explanation."
                ),
                messages=[{
                    "role": "user", 
                    "content": f"Command: {current_command}\nError: {error_msg}\nCWD: {cwd}"
                }],
            )
            
            current_command = fix_response.strip().replace("```", "").replace("shell", "").strip()
            log.info(f"AI proposed fix: {current_command}")

        return False, "Max retries reached without success."
