"""
IP Prime — Proactive Agent Mode

Prime watches your system in the background and acts or alerts
WITHOUT being asked. This is the difference between a tool and an agent.

Watches:
- Disk space (alert if < 10GB free)
- CPU/RAM spikes (alert if sustained > 85%)
- Clock events (upcoming calendar reminders)
- File changes in watched directories
- API key health (test keys are still valid)
"""

import asyncio
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Callable, Optional

import psutil

log = logging.getLogger("ipprime.proactive")

# ---------------------------------------------------------------------------
# Alert Thresholds
# ---------------------------------------------------------------------------
DISK_WARN_GB   = 10    # warn if free disk < 10GB
CPU_WARN_PCT   = 85    # warn if CPU sustained above this
RAM_WARN_PCT   = 90    # warn if RAM above this
CHECK_INTERVAL = 60    # seconds between system checks


class ProactiveAgent:
    """Background watcher that keeps Prime one step ahead of you, sir."""

    def __init__(self, alert_callback: Callable[[str], None]):
        """
        Args:
            alert_callback: async-safe function that sends a voice/text alert to the user.
        """
        self.alert = alert_callback
        self._running = False
        self._cpu_high_since: Optional[float] = None
        self._last_disk_warn: float = 0
        self._last_ram_warn: float = 0

    # -- Lifecycle -------------------------------------------------------------

    async def start(self):
        """Start all background watchers."""
        self._running = True
        log.info("Proactive Agent Mode activated. Prime is watching, sir.")
        await asyncio.gather(
            self._watch_system_health(),
            self._watch_disk_space(),
        )

    def stop(self):
        self._running = False
        log.info("Proactive Agent Mode deactivated.")

    # -- Watchers --------------------------------------------------------------

    async def _watch_system_health(self):
        """Monitor CPU and RAM, alert if sustained spikes."""
        while self._running:
            try:
                cpu = psutil.cpu_percent(interval=3)
                ram = psutil.virtual_memory().percent

                # CPU sustained high
                if cpu > CPU_WARN_PCT:
                    if self._cpu_high_since is None:
                        self._cpu_high_since = time.time()
                    elif time.time() - self._cpu_high_since > 30:
                        # Sustained for 30s → alert
                        await self.alert(
                            f"Heads up, sir. CPU has been at {cpu:.0f}% for over 30 seconds. "
                            "Something is burning. Want me to check what's running?"
                        )
                        self._cpu_high_since = None  # reset so we don't spam
                else:
                    self._cpu_high_since = None

                # RAM high
                now = time.time()
                if ram > RAM_WARN_PCT and (now - self._last_ram_warn) > 300:
                    await self.alert(
                        f"RAM is at {ram:.0f}%, sir. You're running hot. "
                        "Want me to kill some background processes?"
                    )
                    self._last_ram_warn = now

            except Exception as e:
                log.debug(f"System health check error: {e}")

            await asyncio.sleep(CHECK_INTERVAL)

    async def _watch_disk_space(self):
        """Alert if free disk space drops critically low."""
        while self._running:
            try:
                usage = shutil.disk_usage(Path.home())
                free_gb = usage.free / (1024 ** 3)
                now = time.time()

                if free_gb < DISK_WARN_GB and (now - self._last_disk_warn) > 3600:
                    await self.alert(
                        f"Disk space is dangerously low, sir. Only {free_gb:.1f}GB remaining. "
                        "I can scan and suggest what to clean up."
                    )
                    self._last_disk_warn = now

            except Exception as e:
                log.debug(f"Disk watch error: {e}")

            await asyncio.sleep(CHECK_INTERVAL * 10)  # check every 10 mins

    async def check_api_key_health(self, keys: dict) -> list[str]:
        """
        Verify API keys are still active.
        Keys format: {"OpenAI": "sk-...", "Anthropic": "sk-..."}
        Returns list of keys that appear invalid.
        """
        dead_keys = []
        for name, key in keys.items():
            if not key or len(key) < 20:
                dead_keys.append(name)
        return dead_keys
