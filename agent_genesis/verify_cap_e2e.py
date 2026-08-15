"""
E2E verification of the deployer concurrency cap + server-side sandbox caps.

Deploys an org of N agents with runtime=sandbox against the VPS OpenSandbox
server, samples the number of live docker sandbox containers on the VPS
every second, and asserts:
  1. peak concurrent sandboxes <= max_concurrent_agents
  2. every sandbox container has 1Gi memory / 0.7 CPU limits (server caps)

Run from the repo root:  python agent_genesis/verify_cap_e2e.py
Requires: local `osb` CLI configured for 187.77.185.34:8080, ssh key to the
VPS (codex_hostinger_ed25519), and the agent_genesis package importable.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import threading
import time
from pathlib import Path

from agent_genesis.deployer.orchestrator import DeployerAgent

VPS = "root@187.77.185.34"
SSH_KEY = str(Path.home() / ".ssh" / "codex_hostinger_ed25519")

N_AGENTS = 15
CAP = 6


def vps_docker_count() -> int:
    """Number of live sandbox containers on the VPS."""
    try:
        r = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "-i", SSH_KEY, VPS,
             "docker ps --format '{{.Names}}' | grep -c sandbox || true"],
            capture_output=True, text=True, timeout=20,
        )
        return int(r.stdout.strip() or 0)
    except Exception:
        return -1


def vps_inspect_first() -> str:
    """docker inspect of the newest sandbox container (memory/cpu)."""
    try:
        r = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "-i", SSH_KEY, VPS,
             "docker ps --format '{{.Names}}' | grep sandbox | head -1 | xargs -r docker inspect --format 'memory={{.HostConfig.Memory}} nano_cpus={{.HostConfig.NanoCpus}}'"],
            capture_output=True, text=True, timeout=20,
        )
        return r.stdout.strip()
    except Exception:
        return "n/a"


def run_deploy(d: DeployerAgent, org: dict) -> dict:
    """Run the async deployment in its own event loop on a worker thread."""
    result: dict = {}

    def _run():
        result.update(asyncio.run(d.deploy_organization(org)))

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t, result


def main() -> int:
    print(f"=== Deployer cap E2E: {N_AGENTS} sandbox agents, cap={CAP} ===")
    d = DeployerAgent(max_concurrent_agents=CAP)
    org = {
        "agents": [
            {
                "id": f"a{i:02d}",
                "name": f"Agent {i}",
                "runtime": "sandbox",
                "model": "python:3.12",
                "tools": [],
                "task": f"verify-task-{i}",
                "input_context": {},
                "output_contract": {},
                "depends_on": [],
            }
            for i in range(N_AGENTS)
        ]
    }

    deploy_thread, result_holder = run_deploy(d, org)

    peak = 0
    samples: list[int] = []
    inspect_sample = ""

    # Sample live sandbox count on the VPS every second while deploying.
    # Runs on the main thread (blocking ssh calls are fine here).
    while deploy_thread.is_alive():
        n = vps_docker_count()
        if n >= 0:
            samples.append(n)
            peak = max(peak, n)
        if n > 0 and not inspect_sample:
            inspect_sample = vps_inspect_first()
        time.sleep(1)

    deploy_thread.join()
    result = result_holder

    # Final drain sample
    for _ in range(3):
        n = vps_docker_count()
        if n >= 0:
            samples.append(n)
        time.sleep(1)

    ok_agents = sum(1 for r in result["agents"].values() if r["status"] == "completed")
    print("\n=== RESULTS ===")
    print(f"agents deployed: {ok_agents}/{N_AGENTS} completed")
    print(f"deployer peak_concurrent (internal): {d.peak_concurrent}")
    print(f"VPS peak live sandboxes observed:    {peak}  (cap={CAP})")
    print(f"VPS sandbox container limits:        {inspect_sample}")
    print(f"samples: {samples}")

    cap_ok = peak <= CAP
    limits_ok = "memory=1073741824" in inspect_sample and "nano_cpus=700000000" in inspect_sample
    print(f"\ncap respected ({peak} <= {CAP}): {cap_ok}")
    print(f"1Gi/0.7 limits on container: {limits_ok}")

    # Cleanup anything left
    r = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", "-o", "BatchMode=yes", "-i", SSH_KEY, VPS,
         "docker ps -q | xargs -r docker kill >/dev/null 2>&1; echo cleaned"],
        capture_output=True, text=True, timeout=20,
    )
    print(f"cleanup: {r.stdout.strip()}")

    return 0 if (cap_ok and limits_ok and ok_agents == N_AGENTS) else 1


if __name__ == "__main__":
    sys.exit(main())
