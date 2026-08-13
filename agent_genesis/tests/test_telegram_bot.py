"""Tests for agent_genesis.cli.telegram_bot (the genesis-bot entry point)."""

from __future__ import annotations

import pytest

import agent_genesis.cli.telegram_bot as tb


def test_module_has_main_entry():
    assert callable(tb.main)


def test_main_requires_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    with pytest.raises(SystemExit) as exc:
        tb.main()
    assert "TELEGRAM_BOT_TOKEN" in str(exc.value)


def test_main_starts_bot_with_token(monkeypatch):
    """With a token set, main() must construct the bot and await start()."""

    class FakeBot:
        started = None

        def __init__(self, token=None):
            self.token = token

        async def start(self):
            FakeBot.started = self.token

    monkeypatch.setattr(tb, "GenesisTelegramBot", FakeBot)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    tb.main()
    assert FakeBot.started == "123:ABC"
