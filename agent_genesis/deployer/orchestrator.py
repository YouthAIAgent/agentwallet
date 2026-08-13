"""
Agent Genesis — Deployer Agent (Orchestrator)
Spawns, monitors, and manages agent processes across heterogeneous runtimes:
- Hermes (via plugin API)
- Claude Code (subprocess)
- Codex (subprocess)
- Local LLM (Ollama API)
- Box (box.ascii.dev cloud VM)
"""

from __future__ import annotations

import asyncio
import json
import uuid
import shlex
import os
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from pathlib import Path

from agent_genesis.memory import get_memory_fabric


class RuntimeType(str, Enum):
    HERMES = "hermes"
    CLAUDE_CODE = "claude_code"
    CODEX = "codex"
    LOCAL_LLM = "local_llm"
    BOX = "box"


@dataclass
class AgentProcess:
    id: str
    spec_id: str
    runtime: RuntimeType
    process: Optional[asyncio.subprocess.Process] = None
    status: str = "pending"  # pending, running, completed, failed
    pid: Optional[int] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict] = None
    error: Optional[str] = None


class DeployerAgent:
    """
    Orchestrates agent deployment across heterogeneous runtimes.
    """

    def __init__(self, box_token: Optional[str] = None):
        self.memory = get_memory_fabric()
        self.box_token = box_token or os.getenv("BOX_TOKEN")
        self.active_processes: Dict[str, AgentProcess] = {}
        self.runtime_configs = self._load_runtime_configs()

    def _load_runtime_configs(self) -> Dict:
        return {
            RuntimeType.HERMES: {
                "endpoint": "http://127.0.0.1:8799/api/agents/delegate",
                "health": "http://127.0.0.1:8799/api/health",
            },
            RuntimeType.CLAUDE_CODE: {
                "command": "claude",
                "args_template": ["--print", "--model", "{model}"],
                "env": {"CLAUDE_CONFIG_DIR": str(Path.home() / ".claude")},
            },
            RuntimeType.CODEX: {
                "command": "codex",
                "args_template": ["exec", "--model", "{model}"],
                "env": {},
            },
            RuntimeType.LOCAL_LLM: {
                "endpoint": "http://127.0.0.1:11434/api/generate",
                "health": "http://127.0.0.1:11434/api/tags",
            },
            RuntimeType.BOX: {
                "api_base": "https://api.box.ascii.dev/v1",
                "token": self.box_token,
            },
        }

    # ------------------------------------------------------ main deploy
    async def deploy_organization(self, org_spec: Dict) -> Dict[str, Any]:
        """Deploy entire agent organization, return deployment status."""
        deployment_id = str(uuid.uuid4())[:8]

        # 1. Provision infrastructure (Box VMs if needed)
        await self._provision_infrastructure(org_spec)

        # 2. Deploy agents in topological order
        agent_results = {}
        for agent_spec in org_spec.get("agents", []):
            agent_id = agent_spec["id"]

            # Wait for dependencies
            for dep_id in agent_spec.get("depends_on", []):
                if dep_id in agent_results:
                    agent_spec.setdefault("input_context", {})
                    agent_spec["input_context"][dep_id] = agent_results[dep_id]

            # Deploy
            result = await self.deploy_agent(agent_spec, deployment_id)
            agent_results[agent_id] = result

            # Store in memory
            self.memory.remember(
                agent_id="deployer",
                event_type="agent_deployed",
                content=f"Deployed {agent_id} on {agent_spec['runtime']}",
                metadata={"deployment_id": deployment_id, "result": result},
            )

        return {
            "deployment_id": deployment_id,
            "status": "completed",
            "agents": agent_results,
        }

    async def deploy_agent(self, agent_spec: Dict, deployment_id: str) -> Dict:
        """Deploy single agent to its target runtime."""
        runtime = RuntimeType(agent_spec["runtime"])

        if runtime == RuntimeType.HERMES:
            return await self._deploy_hermes(agent_spec, deployment_id)
        elif runtime == RuntimeType.CLAUDE_CODE:
            return await self._deploy_claude_code(agent_spec, deployment_id)
        elif runtime == RuntimeType.CODEX:
            return await self._deploy_codex(agent_spec, deployment_id)
        elif runtime == RuntimeType.LOCAL_LLM:
            return await self._deploy_local_llm(agent_spec, deployment_id)
        elif runtime == RuntimeType.BOX:
            return await self._deploy_box(agent_spec, deployment_id)
        else:
            raise ValueError(f"Unknown runtime: {runtime}")

    # ------------------------------------------------------ hermes
    async def _deploy_hermes(self, spec: Dict, deployment_id: str) -> Dict:
        """Deploy via Hermes plugin API."""
        try:
            import aiohttp
        except ImportError:
            return {"status": "failed", "error": "aiohttp not installed", "runtime": "hermes"}

        payload = {
            "agent": spec["id"],
            "task": spec.get("task", ""),
            "context": spec.get("input_context", {}),
            "model": spec["model"],
            "tools": spec.get("tools", []),
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://127.0.0.1:8799/api/agents/delegate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as resp:
                    result = await resp.json()
            return {"status": "completed", "result": result, "runtime": "hermes"}
        except Exception as e:
            return {"status": "failed", "error": str(e), "runtime": "hermes"}

    # ------------------------------------------------------ claude code
    async def _deploy_claude_code(self, spec: Dict, deployment_id: str) -> Dict:
        """Deploy via Claude Code CLI."""
        cmd_config = self.runtime_configs[RuntimeType.CLAUDE_CODE]
        args = [arg.format(model=spec["model"]) for arg in cmd_config["args_template"]]

        cmd = [cmd_config["command"]] + args
        prompt = self._build_prompt(spec)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, **cmd_config.get("env", {})},
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode()),
                timeout=300,
            )

            if proc.returncode != 0:
                return {"status": "failed", "error": stderr.decode()[:500], "runtime": "claude_code"}

            return {"status": "completed", "result": stdout.decode(), "runtime": "claude_code"}
        except asyncio.TimeoutError:
            return {"status": "failed", "error": "timeout (300s)", "runtime": "claude_code"}
        except Exception as e:
            return {"status": "failed", "error": str(e), "runtime": "claude_code"}

    # ------------------------------------------------------ codex
    async def _deploy_codex(self, spec: Dict, deployment_id: str) -> Dict:
        """Deploy via Codex CLI."""
        cmd_config = self.runtime_configs[RuntimeType.CODEX]
        args = [arg.format(model=spec["model"]) for arg in cmd_config["args_template"]]

        cmd = [cmd_config["command"]] + args
        prompt = self._build_prompt(spec)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, **cmd_config.get("env", {})},
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode()),
                timeout=300,
            )

            if proc.returncode != 0:
                return {"status": "failed", "error": stderr.decode()[:500], "runtime": "codex"}

            return {"status": "completed", "result": stdout.decode(), "runtime": "codex"}
        except asyncio.TimeoutError:
            return {"status": "failed", "error": "timeout (300s)", "runtime": "codex"}
        except Exception as e:
            return {"status": "failed", "error": str(e), "runtime": "codex"}

    # ------------------------------------------------------ local llm (ollama)
    async def _deploy_local_llm(self, spec: Dict, deployment_id: str) -> Dict:
        """Deploy via Ollama API."""
        try:
            import aiohttp
        except ImportError:
            return {"status": "failed", "error": "aiohttp not installed", "runtime": "local_llm"}

        prompt = self._build_prompt(spec)
        endpoint = self.runtime_configs[RuntimeType.LOCAL_LLM]["endpoint"]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json={
                        "model": spec["model"],
                        "prompt": prompt,
                        "system": spec.get("persona", ""),
                        "stream": False,
                        "options": spec.get("model_params", {}),
                    },
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as resp:
                    result = await resp.json()

            return {"status": "completed", "result": result.get("response", ""), "runtime": "local_llm"}
        except Exception as e:
            return {"status": "failed", "error": str(e), "runtime": "local_llm"}

    # ------------------------------------------------------ box
    async def _deploy_box(self, spec: Dict, deployment_id: str) -> Dict:
        """Deploy to box.ascii.dev cloud VM."""
        if not self.box_token:
            return {"status": "failed", "error": "No Box token configured", "runtime": "box"}

        try:
            import aiohttp
        except ImportError:
            return {"status": "failed", "error": "aiohttp not installed", "runtime": "box"}

        # In production: create box, upload code, execute
        # For MVP: return placeholder
        box_id = f"box-{spec['id']}-{deployment_id}"

        return {
            "status": "completed",
            "result": f"Box {box_id} would execute agent (not implemented in MVP)",
            "runtime": "box",
            "box_id": box_id,
        }

    # ------------------------------------------------------ helpers
    async def _provision_infrastructure(self, org_spec: Dict) -> None:
        """Provision Box VMs for agents that need them."""
        box_agents = [a for a in org_spec.get("agents", []) if a["runtime"] == "box"]
        for agent in box_agents:
            # In production: call box.ascii.dev API to create VM
            pass

    def _build_prompt(self, spec: Dict) -> str:
        """Build complete prompt from agent spec."""
        parts = [
            f"Role: {spec.get('name', 'Agent')}",
            f"Mission: {spec.get('input_context', {}).get('task', '')}",
            f"Input: {json.dumps(spec.get('input_context', {}), indent=2, ensure_ascii=False)}",
            f"Expected Output Format: {json.dumps(spec.get('output_contract', {}), indent=2, ensure_ascii=False)}",
            f"Tools Available: {', '.join(spec.get('tools', []))}",
        ]
        return "\n\n".join(parts)

    # ------------------------------------------------------ health checks
    async def check_runtime_health(self, runtime: RuntimeType) -> bool:
        """Check if a runtime is available."""
        if runtime == RuntimeType.HERMES:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "http://127.0.0.1:8799/api/health", timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        return resp.status == 200
            except Exception:
                return False

        elif runtime == RuntimeType.LOCAL_LLM:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        "http://127.0.0.1:11434/api/tags", timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        return resp.status == 200
            except Exception:
                return False

        elif runtime in (RuntimeType.CLAUDE_CODE, RuntimeType.CODEX):
            # Check if CLI exists
            cmd = "claude" if runtime == RuntimeType.CLAUDE_CODE else "codex"
            try:
                proc = await asyncio.create_subprocess_exec(
                    cmd, "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                return proc.returncode == 0
            except Exception:
                return False

        elif runtime == RuntimeType.BOX:
            return bool(self.box_token)

        return False

    async def list_available_runtimes(self) -> Dict[RuntimeType, bool]:
        """Check all runtimes."""
        results = {}
        for rt in RuntimeType:
            results[rt] = await self.check_runtime_health(rt)
        return results


if __name__ == "__main__":
    async def main():
        d = DeployerAgent()
        runtimes = await d.list_available_runtimes()
        print("Available runtimes:")
        for rt, ok in runtimes.items():
            print(f"  {rt.value}: {'✅' if ok else '❌'}")

    asyncio.run(main())
