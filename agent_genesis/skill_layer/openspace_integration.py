"""
Agent Genesis — OpenSpace Integration Layer
Skill Management Layer: retrieval, evaluation, evolution, sharing.
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from agent_genesis.memory import get_memory_fabric


class OpenSpaceLayer:
    """
    Wrapper for OpenSpace skill management.
    Provides: retrieval, execution with quality records, evaluation, evolution, sharing.
    """

    def __init__(self, workspace: str = "~/agent-genesis/openspace_workspace"):
        self.memory = get_memory_fabric()
        self.workspace = Path(workspace).expanduser()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self._openspace = None
        self._skill_engine = None
        self._harness = None

    def _init_openspace(self) -> None:
        """Lazy initialization of OpenSpace."""
        if self._openspace is not None:
            return

        try:
            from openspace import OpenSpace
            from openspace.skill_engine import SkillEngine
            from openspace.runtime.harness import AgentHarness
        except ImportError:
            raise RuntimeError(
                "OpenSpace not installed. Run: pip install -e /path/to/OpenSpace"
            )

        self._openspace = OpenSpace(
            workspace=str(self.workspace),
            enable_evolution=True,
            enable_quality_tracking=True,
        )
        self._skill_engine = SkillEngine(self._openspace)
        self._harness = AgentHarness(self._openspace)

    # ------------------------------------------------------ retrieval
    async def find_skills(
        self, task: str, role: str = "general", top_k: int = 5
    ) -> List[Dict]:
        """Semantic search for relevant skills."""
        self._init_openspace()
        results = await self._skill_engine.search(
            query=task,
            filters={"role": role, "status": "trusted"},
            top_k=top_k,
        )
        return [s.to_dict() if hasattr(s, "to_dict") else s for s in results]

    async def get_skill(self, skill_id: str) -> Optional[Dict]:
        """Get full skill with quality metadata."""
        self._init_openspace()
        skill = await self._skill_engine.get_skill(skill_id)
        return skill.to_dict() if skill and hasattr(skill, "to_dict") else skill

    # ------------------------------------------------------ execution
    async def run_with_skill(
        self, agent_id: str, skill_id: str, task: str, context: Dict
    ) -> Dict:
        """Run agent with skill, capture quality evidence."""
        self._init_openspace()
        skill = await self._skill_engine.get_skill(skill_id)
        if not skill:
            return {"error": f"Skill {skill_id} not found"}

        # Execute via harness (captures quality records)
        execution = await self._harness.execute(
            agent_id=agent_id,
            skill=skill,
            task=task,
            context=context,
            record_quality=True,
        )

        # Store in Agent Genesis memory
        self.memory.remember(
            agent_id=agent_id,
            event_type="skill_execution",
            content=f"Executed skill {skill_id}: {execution.status}",
            metadata={
                "skill_id": skill_id,
                "execution_id": execution.id,
                "status": execution.status,  # selected, applied, completed, fallback
                "duration_ms": execution.duration_ms,
                "tools_used": execution.tools_used,
                "errors": execution.errors,
            },
        )

        return {
            "result": execution.result,
            "status": execution.status,
            "execution_id": execution.id,
        }

    # ------------------------------------------------------ evaluation
    async def get_skill_quality(self, skill_id: str) -> Dict:
        """Get quality metrics from real executions."""
        self._init_openspace()
        return await self._skill_engine.get_quality_summary(skill_id)

    # ------------------------------------------------------ evolution
    async def propose_evolution(
        self, skill_id: str, execution_id: str, evolution_type: str = "FIX"
    ) -> Dict:
        """
        Propose skill evolution based on execution evidence.
        evolution_type: "FIX" | "DERIVED" | "CAPTURED"
        """
        self._init_openspace()
        return await self._skill_engine.propose_evolution(
            skill_id=skill_id,
            evidence_execution_id=execution_id,
            evolution_type=evolution_type,
        )

    async def validate_evolution(self, proposal_id: str) -> Dict:
        """Validate evolution against test cases before promoting."""
        self._init_openspace()
        return await self._skill_engine.validate_evolution(proposal_id)

    # ------------------------------------------------------ sharing
    async def share_skill(self, skill_id: str, visibility: str = "group") -> Dict:
        """Share skill to OpenSpace cloud (package-based)."""
        self._init_openspace()
        return await self._skill_engine.share(
            skill_id=skill_id,
            visibility=visibility,  # "private", "group", "public"
        )

    async def import_cloud_skill(self, package_id: str, skill_id: str) -> Dict:
        """Import skill from cloud package to local workspace."""
        self._init_openspace()
        skill = await self._skill_engine.import_skill(package_id, skill_id)
        return skill.to_dict() if skill and hasattr(skill, "to_dict") else skill

    # ------------------------------------------------------ local fallback (no OpenSpace)
    def find_skills_local(self, query: str, limit: int = 10) -> List[Dict]:
        """Fallback: search Agent Genesis procedural memory for skills."""
        skills = self.memory.list_skills(limit=limit)
        # Simple keyword match
        results = []
        q = query.lower()
        for s in skills:
            if q in s.get("skill_name", "").lower() or q in s.get("description", "").lower():
                results.append(s)
        return results[:limit]

    def get_skill_local(self, skill_name: str) -> Optional[Dict]:
        """Fallback: get skill from procedural memory."""
        return self.memory.get_skill(skill_name)

    def record_skill_execution(
        self,
        agent_id: str,
        skill_name: str,
        success: bool,
        metadata: Dict = None,
    ) -> None:
        """Record skill execution result locally."""
        skill = self.memory.get_skill(skill_name)
        if skill:
            self.memory.record_skill_result(skill["id"], success)

        self.memory.remember(
            agent_id=agent_id,
            event_type="skill_execution",
            content=f"Local skill {skill_name}: {'success' if success else 'failure'}",
            metadata={"skill_name": skill_name, "success": success, **(metadata or {})},
        )


_singleton: Optional[OpenSpaceLayer] = None


def get_openspace_layer(workspace: str = "~/agent-genesis/openspace_workspace") -> OpenSpaceLayer:
    global _singleton
    if _singleton is None:
        _singleton = OpenSpaceLayer(workspace)
    return _singleton


if __name__ == "__main__":
    # Test local fallback
    layer = get_openspace_layer()
    layer.memory.learn_skill("test", "echo", [{"tool": "echo", "params": {"text": "hi"}}])
    print("Local skills:", layer.find_skills_local("echo"))
    print("Local skill:", layer.get_skill_local("echo"))
