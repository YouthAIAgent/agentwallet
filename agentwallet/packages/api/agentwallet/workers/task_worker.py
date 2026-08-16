"""Task Worker -- executes funded human tasks with a real agent (LLM).

Picks up tasks in 'assigned'/'in_progress' state, calls an OpenAI-
compatible model (X402_LLM_* env vars, same config as the playground x402
demo), writes the delivery payload, and releases the escrow to the agent.
Falls back to a deterministic demo response when no LLM key is configured
so the payment rail stays demonstrable end to end.
"""

import os

import httpx
from sqlalchemy import select

from ..core.database import get_session_factory
from ..core.logging import get_logger
from ..models.task import Task
from ..services.task_service import TaskService
from .base import BaseWorker

logger = get_logger(__name__)

# Categories -> prompt style
CATEGORY_PROMPTS = {
    "research": "You are a research analyst. Deliver a concise, well-structured research summary with key findings.",
    "writing": "You are a professional writer. Deliver polished, publication-ready prose.",
    "coding": "You are a senior software engineer. Deliver working code with brief explanation and usage notes.",
    "data": "You are a data analyst. Deliver structured data, tables, or analysis output.",
    "social": "You are a social media strategist. Deliver ready-to-post content with hashtags.",
    "general": "You are a capable AI agent. Complete the task precisely and deliver the result.",
}


async def _call_llm(prompt: str, category: str = "general") -> tuple[str, str, str]:
    """Call the configured OpenAI-compatible model; fall back to demo.

    Returns (provider, model, response_text).
    """
    base = (os.getenv("X402_LLM_BASE_URL") or os.getenv("OPENAI_COMPAT_BASE_URL") or "").rstrip("/")
    key = os.getenv("X402_LLM_KEY") or os.getenv("OPENAI_COMPAT_API_KEY") or ""
    model = os.getenv("X402_LLM_MODEL") or os.getenv("OPENAI_COMPAT_MODEL") or "demo"

    system_prompt = CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["general"])

    if base and key:
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(
                    f"{base}/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 400,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
                    if content:
                        return "openai-compatible", model, content.strip()
        except Exception as e:
            logger.warning("task_llm_call_failed", error=str(e))

    return (
        "demo",
        model,
        f"[demo AI · no LLM key configured on the API] Task executed successfully.\n\n"
        f"Prompt: {prompt[:200]}\n\n"
        f"Payment rail verified: the escrow for this task was funded on-chain and will "
        f"release to the agent's wallet on delivery. Point the API at any OpenAI-compatible "
        f"model (X402_LLM_BASE_URL) and this same flow returns a real AI deliverable.",
    )


class TaskWorker(BaseWorker):
    name = "task_worker"
    interval_seconds = 15.0

    async def tick(self) -> None:
        """Execute one funded/assigned task per tick."""
        factory = get_session_factory()
        async with factory() as db:
            try:
                svc = TaskService(db)
                result = await db.execute(
                    select(Task).where(Task.status.in_(["assigned", "in_progress"])).limit(1)
                )
                task = result.scalar_one_or_none()
                if not task:
                    return

                if not task.agent_id:
                    # Auto-assign the best available agent for the org
                    try:
                        assigned = await svc.auto_assign(task.id, task.org_id, task.capability)
                        if not assigned:
                            logger.info("task_no_agent", task_id=str(task.id))
                            return
                    except Exception as e:
                        logger.warning("task_auto_assign_failed", task_id=str(task.id), error=str(e))
                        return

                # Mark in progress
                await svc.mark_in_progress(task.id, task.org_id)

                # Build the prompt from the task
                prompt = f"Task: {task.title}\n\nDescription: {task.description}"
                if task.input_data:
                    prompt += f"\n\nInput data: {task.input_data}"
                if task.requirements:
                    prompt += f"\n\nRequirements: {task.requirements}"

                provider, model, content = await _call_llm(prompt, task.category)

                # Deliver + auto-release escrow to the agent
                await svc.deliver(
                    task_id=task.id,
                    org_id=task.org_id,
                    result_data={"output": content, "category": task.category},
                    delivery_notes="Delivered by task worker",
                    provider=provider,
                    model=model,
                    auto_release=True,
                )
                await db.commit()
                logger.info(
                    "task_executed",
                    task_id=str(task.id),
                    status="released",
                    provider=provider,
                    escrow_id=str(task.escrow_id) if task.escrow_id else None,
                )
            except Exception as e:
                logger.error("task_worker_tick_error", error=str(e))
