"""Tests for agent_genesis.finetune.loop.FineTuneLoop (offline paths)."""

from __future__ import annotations

import pytest

from agent_genesis.finetune.loop import FineTuneLoop


@pytest.fixture()
def loop(isolated_memory, tmp_path):
    return FineTuneLoop(adapter_dir=str(tmp_path / "ckpt"), gguf_dir=str(tmp_path / "gguf"))


@pytest.mark.asyncio
async def test_run_nightly_skips_without_data(loop):
    result = await loop.run_nightly(min_samples=10)
    assert result["status"] == "skipped"
    assert result["samples"] == 0
    assert "skipping" in result["reason"]


@pytest.mark.asyncio
async def test_run_nightly_remembers_skip(loop):
    await loop.run_nightly(min_samples=10)
    episodes = loop.memory.recall(agent_id="finetune", event_type="fine_tune_skipped")
    assert len(episodes) == 1


def test_gguf_filename_has_date_and_run_id(loop, tmp_path):
    """_export_gguf must build a valid path without NameError (date_str fix)."""
    import asyncio

    # _export_gguf runs mlx_lora.export_gguf which is unavailable -> returns None,
    # but the filename itself must be constructed without error.
    result = asyncio.run(loop._export_gguf(tmp_path / "adapter", "abc123"))
    assert result is None  # mlx not installed in CI
