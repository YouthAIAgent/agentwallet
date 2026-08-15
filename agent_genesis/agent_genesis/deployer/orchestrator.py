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
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum
from pathlib import Path

from agent_genesis.memory import get_memory_fabric


def _exec_cmd(cmd: List[str]) -> List[str]:
    """Return a spawnable command list on the current platform.

    On Windows, npm-installed CLIs (codex, claude, ...) ship as ``.cmd``
    shims with no ``.exe``. ``asyncio.create_subprocess_exec`` cannot run
    those directly (WinError 2), so wrap them through ``cmd /c``.
    """
    if sys.platform == "win32" and cmd:
        return ["cmd", "/c", *cmd]
    return cmd


class RuntimeType(str, Enum):
    HERMES = "hermes"
    CLAUDE_CODE = "claude_code"
    CODEX = "codex"
    LOCAL_LLM = "local_llm"
    BOX = "box"
    SANDBOX = "sandbox"


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


DEFAULT_MAX_CONCURRENT_AGENTS = 12
"""Default cap on simultaneously running agents (matches VPS capacity: 4vCPU/16GB)."""


class DeployerAgent:
    """
    Orchestrates agent deployment across heterogeneous runtimes.

    Concurrency is capped by ``max_concurrent_agents`` so the host (VPS)
    is never overloaded: at most that many agents run at once, configurable
    via the ``GENESIS_MAX_CONCURRENT_AGENTS`` env var or the constructor arg.
    """

    def __init__(self, box_token: Optional[str] = None, max_concurrent_agents: Optional[int] = None):
        self.memory = get_memory_fabric()
        self.box_token = box_token or os.getenv("BOX_TOKEN")
        self.max_concurrent_agents = max_concurrent_agents or int(
            os.getenv("GENESIS_MAX_CONCURRENT_AGENTS", str(DEFAULT_MAX_CONCURRENT_AGENTS))
        )
        # Semaphore is loop-agnostic on py3.11+; bind at first use inside the event loop.
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._active_agent_count = 0
        self._peak_concurrent = 0
        self.active_processes: Dict[str, AgentProcess] = {}
        self.runtime_configs = self._load_runtime_configs()

    def _get_semaphore(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrent_agents)
        return self._semaphore

    @property
    def active_agent_count(self) -> int:
        """Agents currently running (respects the concurrency cap)."""
        return self._active_agent_count

    @property
    def peak_concurrent(self) -> int:
        """Highest number of agents running simultaneously this session."""
        return self._peak_concurrent

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
            RuntimeType.SANDBOX: {
                "command": "osb",
                "image": "python:3.12",
                "env": {"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
                "create_timeout": 120,
                "run_timeout": 300,
            },
        }

    # ------------------------------------------------------ main deploy
    async def deploy_organization(self, org_spec: Dict) -> Dict[str, Any]:
        """Deploy entire agent organization, return deployment status.

        Agents with no unsatisfied dependencies are deployed in parallel
        waves, bounded by the concurrency cap (never more than
        ``max_concurrent_agents`` at once).
        """
        deployment_id = str(uuid.uuid4())[:8]

        # 1. Provision infrastructure (Box VMs if needed)
        await self._provision_infrastructure(org_spec)

        # 2. Deploy agents in dependency-ordered waves, capped by the semaphore
        agents = list(org_spec.get("agents", []))
        agent_results: Dict[str, Dict] = {}
        deployed_ids: set = set()

        while agents:
            ready = [
                a
                for a in agents
                if all(d in deployed_ids for d in a.get("depends_on", []))
            ]
            if not ready:
                # Circular dependency fallback: deploy the next agent anyway.
                ready = [agents[0]]

            async def _deploy_one(agent_spec: Dict) -> None:
                agent_id = agent_spec["id"]
                # Feed results of already-deployed dependencies into context
                for dep_id in agent_spec.get("depends_on", []):
                    if dep_id in agent_results:
                        agent_spec.setdefault("input_context", {})
                        agent_spec["input_context"][dep_id] = agent_results[dep_id]
                result = await self.deploy_agent(agent_spec, deployment_id)
                agent_results[agent_id] = result
                self.memory.remember(
                    agent_id="deployer",
                    event_type="agent_deployed",
                    content=f"Deployed {agent_id} on {agent_spec['runtime']}",
                    metadata={"deployment_id": deployment_id, "result": result},
                )

            await asyncio.gather(*(_deploy_one(a) for a in ready))
            deployed_ids.update(a["id"] for a in ready)
            agents = [a for a in agents if a["id"] not in deployed_ids]

        return {
            "deployment_id": deployment_id,
            "status": "completed",
            "agents": agent_results,
        }

    async def deploy_agent(self, agent_spec: Dict, deployment_id: str) -> Dict:
        """Deploy single agent to its target runtime.

        The concurrency semaphore is acquired here, so no matter how the
        caller fans out (waves, gather, external scripts) the number of
        simultaneously running agents never exceeds ``max_concurrent_agents``.
        """
        async with self._get_semaphore():
            self._active_agent_count += 1
            self._peak_concurrent = max(self._peak_concurrent, self._active_agent_count)
            try:
                return await self._deploy_agent_inner(agent_spec, deployment_id)
            finally:
                self._active_agent_count -= 1

    async def _deploy_agent_inner(self, agent_spec: Dict, deployment_id: str) -> Dict:
        """Dispatch to the concrete runtime implementation (no concurrency logic)."""
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
        elif runtime == RuntimeType.SANDBOX:
            return await self._deploy_sandbox(agent_spec, deployment_id)
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

        cmd = _exec_cmd([cmd_config["command"]] + args)
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

        # Optional custom provider (e.g. a local OpenAI-compatible proxy):
        #   GENESIS_CODEX_PROVIDER=omniroute -> codex exec ... -c model_provider=omniroute
        provider = os.getenv("GENESIS_CODEX_PROVIDER", "").strip()
        if provider:
            args += ["-c", f"model_provider={provider}"]

        cmd = _exec_cmd([cmd_config["command"]] + args)
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
            import aiohttp  # noqa: F401  (lazy availability check)
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

    # ------------------------------------------------------ sandbox (OpenSandbox)
    async def _deploy_sandbox(self, spec: Dict, deployment_id: str) -> Dict:
        """Deploy agent into an isolated OpenSandbox container.

        Uses the ``osb`` CLI (pointed at the OpenSandbox server, e.g. the
        VPS at 187.77.185.34:8080). The sandbox is created, the agent prompt
        runs inside it, and the sandbox is terminated afterwards so at most
        ``max_concurrent_agents`` containers exist at any moment (semaphore
        held across create+run+kill). Server-side caps (1Gi/0.7 by default)
        protect the host even if a caller requests more.
        """
        cfg = self.runtime_configs[RuntimeType.SANDBOX]
        osb_cmd = cfg["command"]
        image = spec.get("image", cfg["image"])
        env = {**os.environ, **cfg.get("env", {})}
        # Default workload: print the agent id + task, keep container alive briefly.
        task = spec.get("task", "")
        code = (
            f"import time; time.sleep(2); "
            f"print('agent {spec['id']} done | {task[:120]}')"
        )

        sandbox_id: Optional[str] = None
        try:
            create = await asyncio.create_subprocess_exec(
                *_exec_cmd([osb_cmd, "sandbox", "create", "--image", image, "-o", "json"]),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            out, err = await asyncio.wait_for(create.communicate(), timeout=cfg["create_timeout"])
            if create.returncode != 0:
                return {"status": "failed", "error": err.decode()[:500], "runtime": "sandbox"}
            try:
                sandbox_id = json.loads(out.decode())["id"]
            except (json.JSONDecodeError, KeyError):
                return {"status": "failed", "error": out.decode()[:500], "runtime": "sandbox"}

            run = await asyncio.create_subprocess_exec(
                *_exec_cmd(
                    [osb_cmd, "command", "run", sandbox_id, "--", "python3", "-c", code]
                ),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            rout, rerr = await asyncio.wait_for(run.communicate(), timeout=cfg["run_timeout"])
            status = "completed" if run.returncode == 0 else "failed"
            result = rout.decode() or rerr.decode()
            return {
                "status": status,
                "result": result[:1000],
                "runtime": "sandbox",
                "sandbox_id": sandbox_id,
            }
        except asyncio.TimeoutError:
            return {"status": "failed", "error": "timeout", "runtime": "sandbox"}
        except Exception as e:
            return {"status": "failed", "error": str(e), "runtime": "sandbox"}
        finally:
            if sandbox_id:
                try:
                    kill = await asyncio.create_subprocess_exec(
                        *_exec_cmd([osb_cmd, "sandbox", "kill", sandbox_id]),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        env=env,
                    )
                    await asyncio.wait_for(kill.communicate(), timeout=30)
                except Exception:
                    pass

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
            # Check if CLI exists (npm .cmd shims on Windows need cmd /c)
            cmd = "claude" if runtime == RuntimeType.CLAUDE_CODE else "codex"
            try:
                proc = await asyncio.create_subprocess_exec(
                    *_exec_cmd([cmd, "--version"]),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                return proc.returncode == 0
            except Exception:
                return False

        elif runtime == RuntimeType.BOX:
            return bool(self.box_token)

        elif runtime == RuntimeType.SANDBOX:
            # Check the osb CLI exists and the server answers.
            try:
                proc = await asyncio.create_subprocess_exec(
                    *_exec_cmd(["osb", "sandbox", "list"]),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                return proc.returncode == 0
            except Exception:
                return False

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
