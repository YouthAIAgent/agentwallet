"""
AgentWallet Swarm Example
===========================

Multi-agent coordination using swarm intelligence:
  1. Create an orchestrator agent and worker agents
  2. Create a swarm cluster
  3. Add workers as members
  4. Create a task and decompose into subtasks
  5. Assign subtasks to workers
  6. Workers complete subtasks -- results auto-aggregate

Prerequisites:
  pip install aw-protocol-sdk
  export AW_API_KEY=aw_live_...

Usage:
  python swarm_example.py
"""

import asyncio
import os
import sys

from agentwallet import AgentWallet

API_BASE = os.getenv("AW_API_BASE", "https://api.agentwallet.fun")
API_KEY = os.getenv("AW_API_KEY")

if not API_KEY:
    print("Set AW_API_KEY environment variable first.")
    print("Run quickstart.py to get one.")
    sys.exit(1)


async def main():
    print("=" * 60)
    print("  AgentWallet Swarm Coordination")
    print("=" * 60)

    async with AgentWallet(api_key=API_KEY, base_url=f"{API_BASE}/v1") as aw:

        print("\n[1/7] Creating orchestrator and worker agents...")
        orchestrator = await aw.agents.create(
            name="swarm-orchestrator",
            description="Coordinates research tasks across worker agents",
            capabilities=["orchestration", "task-decomposition"],
        )
        print(f"  Orchestrator: {orchestrator.id}")

        workers = []
        specializations = [
            ("researcher-1", "on-chain analytics", "data"),
            ("researcher-2", "market sentiment", "nlp"),
            ("researcher-3", "technical analysis", "charting"),
        ]
        for name, desc, spec in specializations:
            agent = await aw.agents.create(
                name=name,
                description=f"Specialist in {desc}",
                capabilities=[spec, "research"],
            )
            workers.append((agent, spec))
            print(f"  Worker: {agent.id} ({name}, {spec})")

        print("\n[2/7] Creating research swarm...")
        swarm = await aw.swarms.create(
            name="DeFi Research Swarm",
            description="Distributed research team for DeFi market analysis",
            orchestrator_agent_id=orchestrator.id,
            swarm_type="research",
            max_members=10,
            is_public=False,
            config={
                "auto_aggregate": True,
                "require_consensus": False,
                "timeout_hours": 24,
            },
        )
        print(f"  Swarm ID:   {swarm.id}")
        print(f"  Type:       {swarm.swarm_type}")

        print("\n[3/7] Adding worker agents to swarm...")
        for agent, spec in workers:
            member = await aw.swarms.add_member(
                swarm_id=swarm.id,
                agent_id=agent.id,
                role="worker",
                specialization=spec,
                is_contestable=True,
            )
            print(f"  Added: {agent.name} as {member.role} ({member.specialization})")

        print("\n[4/7] Creating research task...")
        task = await aw.swarms.create_task(
            swarm_id=swarm.id,
            title="Q1 2026 DeFi Market Report",
            description="Comprehensive analysis of DeFi market trends",
            task_type="research",
            client_agent_id=orchestrator.id,
        )
        print(f"  Task ID:    {task.id}")
        print(f"  Status:     {task.status}")

        print("\n[5/7] Assigning subtasks to workers...")
        subtask_specs = [
            ("subtask-onchain", workers[0], "Analyze TVL, volumes, and user growth"),
            ("subtask-sentiment", workers[1], "Aggregate social sentiment"),
            ("subtask-technical", workers[2], "Technical analysis of ETH, SOL, and DeFi tokens"),
        ]
        for subtask_id, (agent, _), description in subtask_specs:
            task = await aw.swarms.assign_subtask(
                swarm_id=swarm.id,
                task_id=task.id,
                subtask_id=subtask_id,
                agent_id=agent.id,
                description=description,
            )
            print(f"  Assigned: {subtask_id} -> {agent.name}")

        print("\n[6/7] Workers completing subtasks...")
        results = [
            ("subtask-onchain", {
                "total_tvl": "$48.2B",
                "tvl_change": "+12.4%",
                "top_protocol": "Lido",
            }),
            ("subtask-sentiment", {
                "overall_sentiment": "bullish",
                "sentiment_score": 0.72,
                "trending_topics": ["restaking", "RWA", "intent-based"],
            }),
            ("subtask-technical", {
                "eth_trend": "uptrend",
                "sol_trend": "consolidation",
                "recommendation": "accumulate on dips",
            }),
        ]
        for subtask_id, result in results:
            task = await aw.swarms.complete_subtask(
                swarm_id=swarm.id,
                task_id=task.id,
                subtask_id=subtask_id,
                result=result,
            )
            print(f"  Completed: {subtask_id} ({task.completed_subtasks}/{task.total_subtasks})")

        print("\n[7/7] Fetching aggregated results...")
        final_task = await aw.swarms.get_task(swarm.id, task.id)
        print(f"  Status:     {final_task.status}")
        print(f"  Completed:  {final_task.completed_subtasks}/{final_task.total_subtasks}")
        if final_task.aggregated_result:
            print(f"  Aggregated: {final_task.aggregated_result}")

    print("\n" + "=" * 60)
    print("  Swarm task complete.")
    print("  Swarm types: general, trading, research, content, security, data")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
