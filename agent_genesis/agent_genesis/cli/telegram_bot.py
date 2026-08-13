"""
Agent Genesis — Telegram Bot entry point (console script: `genesis-bot`).

Thin wrapper around :class:`GenesisTelegramBot` so the pyproject entry
point `agent_genesis.cli.telegram_bot:main` resolves. The bot itself
lives in :mod:`agent_genesis.cli.genesis` (CLI + Telegram in one module).

Usage:
    export TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
    export TELEGRAM_ALLOWED_USERS=123456789          # optional allow-list
    genesis-bot
"""

from __future__ import annotations

import asyncio
import os

from agent_genesis.cli.genesis import GenesisTelegramBot, _ensure_utf8_stdout


def main() -> None:
    """Start the Telegram bot (requires ``TELEGRAM_BOT_TOKEN``)."""
    _ensure_utf8_stdout()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN not set. Export it first, e.g.\n"
            "  export TELEGRAM_BOT_TOKEN=123456:ABC-DEF...\n"
            "  genesis-bot"
        )

    try:
        asyncio.run(GenesisTelegramBot(token=token).start())
    except ImportError as exc:
        raise SystemExit(
            f"Missing dependency for the Telegram bot: {exc}\n"
            "Install it with: pip install python-telegram-bot>=21.0"
        ) from exc


if __name__ == "__main__":
    main()
