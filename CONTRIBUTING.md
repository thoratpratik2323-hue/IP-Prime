# Contributing to IP_PRIME

Thanks for your interest in contributing! Here's how to get involved.

## Getting Started

1. Fork the repo
2. Clone your fork
3. Follow the setup instructions in the README
4. Make your changes
5. Test that IP_PRIME still works (start the server, talk to him)
6. Submit a PR

## What We're Looking For

- **Bug fixes** — if something's broken, fix it
- **New integrations** — Spotify, Slack, Notion, etc.
- **Windows/Linux support** — the AppleScript integrations are macOS-only, cross-platform alternatives welcome
- **Better error handling** — things fail silently in places
- **Voice improvements** — alternative TTS providers, better speech recognition
- **New actions** — extend what IP_PRIME can do

## Code Style

Yes, `server.py` is a 2400-line monolith. It works. If you want to refactor parts into modules, that's welcome — just make sure nothing breaks.

- Keep voice responses short (1-2 sentences max)
- Don't add dependencies unless necessary
- Test your changes by actually talking to IP_PRIME
- Keep the personality consistent — British butler, dry wit, economy of language

## What NOT to Do

- Don't add telemetry or analytics
- Don't send data to external services beyond the existing API calls (Anthropic, Fish Audio)
- Don't add features that modify or delete user data in connected services (Mail, Calendar, Notes)
- Don't break the existing voice loop

## Reporting Issues

Open an issue with:
- What you expected to happen
- What actually happened
- Your OS and Python version
- Any error messages from the terminal

## Questions?

Open an issue or start a discussion. Keep it simple.
