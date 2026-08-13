"""Shared fixtures for Agent Genesis tests.

Every test gets an *isolated* memory fabric (SQLite in a tmp dir) so
tests never touch ``~/agent-genesis/memory`` and never interfere with
each other. The plugin module captures global instances at import time,
so ``plugin_env`` rebuilds those globals against the isolated fabric.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _drop_editable_shadow() -> None:
    """Remove stale editable-install finders that shadow this checkout.

    A PEP 660 editable install (e.g. ``pip install -e`` from an older
    location like ``~/agent-genesis``) registers a meta-path finder that
    intercepts ``import agent_genesis`` *before* PathFinder runs, so the
    package under test could silently resolve to the stale copy. Drop it
    so sys.path (the checkout) wins.
    """
    for finder in list(sys.meta_path):
        mapping = getattr(finder, "MAPPING", None)
        if mapping and "agent_genesis" in mapping:
            sys.meta_path.remove(finder)


_drop_editable_shadow()


@pytest.fixture()
def isolated_memory(tmp_path, monkeypatch):
    """A fresh MemoryFabric in a tmp dir, wired as the module singleton."""
    import agent_genesis.memory.fabric as fabric_mod
    from agent_genesis.memory import MemoryFabric

    fabric = MemoryFabric(tmp_path / "memory")
    monkeypatch.setattr(fabric_mod, "_singleton", fabric)
    return fabric


@pytest.fixture()
def plugin_env(isolated_memory, monkeypatch, tmp_path):
    """Rebuild the Hermes plugin globals against the isolated fabric."""
    import agent_genesis.plugins.hermes_genesis as plug
    from agent_genesis.breeder.evolution import BreederAgent
    from agent_genesis.deployer.orchestrator import DeployerAgent
    from agent_genesis.designer.architect import DesignerAgent
    from agent_genesis.finetune.loop import FineTuneLoop
    from agent_genesis.skill_layer.openspace_integration import OpenSpaceLayer

    monkeypatch.setattr(plug, "_memory", isolated_memory)
    monkeypatch.setattr(plug, "_designer", DesignerAgent())
    monkeypatch.setattr(plug, "_breeder", BreederAgent())
    monkeypatch.setattr(plug, "_deployer", DeployerAgent())
    monkeypatch.setattr(
        plug,
        "_finetune",
        FineTuneLoop(adapter_dir=str(tmp_path / "ckpt"), gguf_dir=str(tmp_path / "gguf")),
    )
    monkeypatch.setattr(plug, "_openspace", OpenSpaceLayer(workspace=str(tmp_path / "ws")))
    return plug
