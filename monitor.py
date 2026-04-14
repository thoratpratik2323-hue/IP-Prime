"""
IP_PRIME Conversation Monitor

Watches the IP_PRIME server logs in real-time, analyzes conversation quality,
and reports issues that need fixing. Run alongside the IP_PRIME server.

Usage: python monitor.py
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


class ConversationMonitor:
    def __init__(self):
        self.messages: list[dict] = []
        self.issues: list[str] = []
        self.last_report_time = time.time()
        self.report_interval = 30  # Report every 30 seconds if issues found

    def add_message(self, role: str, text: str):
        self.messages.append({
            "role": role,
            "text": text,
            "time": datetime.now().isoformat(),
        })
        self.analyze_latest()

    def analyze_latest(self):
        if len(self.messages) < 2:
            return

        latest = self.messages[-1]
        prev = self.messages[-2] if len(self.messages) > 1 else None

        # ── Check IP_PRIME responses ──
        if latest["role"] == "ipprime":
            text = latest["text"]

            # Too long for voice?
            sentences = text.split(". ")
            if len(sentences) > 4:
                self.flag(f"IP_PRIME response too long for voice ({len(sentences)} sentences): {text[:80]}...")

            # Generic AI patterns that IP_PRIME shouldn't use
            bad_patterns = [
                ("How can I help", "IP_PRIME doesn't ask 'how can I help' — he just acts"),
                ("Is there anything else", "IP_PRIME doesn't ask 'is there anything else'"),
                ("I'd be happy to", "Too corporate — IP_PRIME says 'Will do, sir' or just does it"),
                ("Absolutely!", "IP_PRIME doesn't use filler enthusiasm"),
                ("Great question", "IP_PRIME never says 'great question'"),
                ("I don't have access", "IP_PRIME should say 'I'm afraid I don't have that information, sir'"),
                ("As an AI", "IP_PRIME never breaks character"),
                ("I cannot", "IP_PRIME says 'I'm afraid that's beyond my current capabilities, sir'"),
            ]
            for pattern, issue in bad_patterns:
                if pattern.lower() in text.lower():
                    self.flag(f"BAD PATTERN: '{pattern}' detected. {issue}")

            # Not using "sir" enough?
            ipprime_msgs = [m for m in self.messages if m["role"] == "ipprime"]
            if len(ipprime_msgs) >= 5:
                recent = ipprime_msgs[-5:]
                sir_count = sum(1 for m in recent if "sir" in m["text"].lower())
                if sir_count < 1:
                    self.flag("IP_PRIME hasn't said 'sir' in the last 5 responses — should use it more")

            # Forgot context?
            if prev and prev["role"] == "user":
                user_text = prev["text"].lower()
                # Check if user referenced something from earlier
                if any(w in user_text for w in ["earlier", "before", "you said", "we talked about", "remember"]):
                    if "I don't recall" in text or "I'm not sure what" in text:
                        self.flag("IP_PRIME failed to recall earlier conversation — memory issue")

            # Response references Samantha?
            if "samantha" in text.lower():
                self.flag("IP_PRIME referenced 'Samantha' — should never mention her, he IS the assistant")

        # ── Check user messages for complaints ──
        if latest["role"] == "user":
            text = latest["text"].lower()
            complaint_patterns = [
                "you forgot", "you don't remember", "i already told you",
                "that's wrong", "no that's not right", "you're not listening",
                "i said", "what i meant was", "can you hear me",
                "that doesn't work", "you can't do that",
            ]
            for pattern in complaint_patterns:
                if pattern in text:
                    self.flag(f"USER COMPLAINT detected: '{pattern}' — review IP_PRIME's previous response")

    def flag(self, issue: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {issue}"
        self.issues.append(entry)
        print(f"\n⚠️  {entry}")

    def report(self):
        if not self.issues:
            return

        now = time.time()
        if now - self.last_report_time < self.report_interval:
            return

        self.last_report_time = now
        print("\n" + "=" * 60)
        print(f"MONITOR REPORT — {len(self.issues)} issues found")
        print("=" * 60)
        for issue in self.issues[-10:]:  # Last 10
            print(f"  {issue}")
        print("=" * 60)


def main():
    monitor = ConversationMonitor()

    print("🔍 IP_PRIME Conversation Monitor")
    print("   Watching server output for quality issues...")
    print("   Press Ctrl+C to stop\n")

    # Tail the server process output
    # We'll read from stdin if piped, otherwise watch the process
    try:
        for line in sys.stdin:
            line = line.strip()

            # Parse User messages
            user_match = re.search(r"User: (.+)$", line)
            if user_match:
                text = user_match.group(1)
                print(f"👤 {text}")
                monitor.add_message("user", text)

            # Parse IP_PRIME responses
            ipprime_match = re.search(r"IP_PRIME: (.+)$", line)
            if ipprime_match:
                text = ipprime_match.group(1)
                print(f"🤖 {text[:80]}{'...' if len(text) > 80 else ''}")
                monitor.add_message("ipprime", text)

            # Parse errors
            if "error" in line.lower() or "Error" in line:
                if "LLM error" in line or "TTS error" in line or "WebSocket error" in line:
                    monitor.flag(f"SERVER ERROR: {line}")

            monitor.report()

    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")
        if monitor.issues:
            print(f"\nTotal issues found: {len(monitor.issues)}")
            for issue in monitor.issues:
                print(f"  {issue}")


if __name__ == "__main__":
    main()
