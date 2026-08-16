"""Task Worker -- executes funded human tasks with a real agent (LLM).

Picks up tasks in 'assigned'/'in_progress' state, calls an OpenAI-
compatible model (X402_LLM_* env vars, same config as the playground x402
demo), writes the delivery payload, and releases the escrow to the agent.
Falls back to a deterministic demo response only when no LLM key is
configured so the payment rail stays demonstrable end to end. When the
provider rate-limits (429/5xx), the task is left queued and retried on the
next tick instead of silently delivering a demo answer.
"""

import asyncio
import os
import random

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
    "security": (
        "You are a security architect. Deliver a threat-model or security review "
        "with concrete, actionable recommendations."
    ),
    "sales": (
        "You are a sales engineer. Deliver a technical pitch, discovery notes, or "
        "proposal that wins the technical decision."
    ),
    "finance": (
        "You are a financial analyst. Deliver financial modeling, forecasts, or "
        "scenario analysis with clear numbers."
    ),
    "support": (
        "You are a customer support responder. Deliver a clear, empathetic "
        "resolution to the customer's issue."
    ),
    "product": (
        "You are a product manager. Deliver a roadmap, requirements, or "
        "go-to-market plan with clear priorities."
    ),
    "general": "You are a capable AI agent. Complete the task precisely and deliver the result.",
}


class LLMRateLimitedError(Exception):
    """Raised when the LLM provider keeps rate-limiting after retries.

    The task is left in the queue and retried on a later tick instead of
    delivering a demo fallback that would look like real AI output.
    """


_LLM_RETRYABLE = {429, 500, 502, 503, 504}

# Cap on consecutive worker execution failures per task before it is marked
# failed and removed from the pickup queue (prevents queue head-of-line
# blocking by a perpetually rate-limited task).
MAX_TASK_FAILURES = int(os.getenv("TASK_MAX_FAILURES", "5"))


async def _call_llm(prompt: str, category: str = "general") -> tuple[str, str, str]:
    """Call the configured OpenAI-compatible model; fall back to demo only when unconfigured.

    Retries 429/5xx with exponential backoff + jitter (respecting Retry-After
    when present). After max retries the call raises LLMRateLimitedError so
    the worker re-queues the task instead of delivering a fake result.

    Returns (provider, model, response_text).
    """
    base = (os.getenv("X402_LLM_BASE_URL") or os.getenv("OPENAI_COMPAT_BASE_URL") or "").rstrip("/")
    key = os.getenv("X402_LLM_KEY") or os.getenv("OPENAI_COMPAT_API_KEY") or ""
    model = os.getenv("X402_LLM_MODEL") or os.getenv("OPENAI_COMPAT_MODEL") or "demo"
    max_attempts = int(os.getenv("X402_LLM_MAX_ATTEMPTS", "4"))

    system_prompt = CATEGORY_PROMPTS.get(category, CATEGORY_PROMPTS["general"])

    if not (base and key):
        return (
            "demo",
            model,
            f"[demo AI · no LLM key configured on the API] Task executed successfully.\n\n"
            f"Prompt: {prompt[:200]}\n\n"
            f"Payment rail verified: the escrow for this task was funded on-chain and will "
            f"release to the agent's wallet on delivery. Point the API at any OpenAI-compatible "
            f"model (X402_LLM_BASE_URL) and this same flow returns a real AI deliverable.",
        )

    last_status = 0
    retry_after_sec = 0.0
    resp = None
    for attempt in range(max_attempts):
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
            last_status = resp.status_code
            if resp.status_code == 200:
                data = resp.json()
                content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
                if content:
                    return "openai-compatible", model, content.strip()
            if resp.status_code not in _LLM_RETRYABLE:
                # Non-retryable (4xx etc.) — not a rate limit, so surface it.
                raise LLMRateLimitedError(f"LLM returned HTTP {resp.status_code}: {resp.text[:200]}")
            # Retryable: read Retry-After for the backoff window
            try:
                ra = resp.headers.get("Retry-After", "0")
                retry_after_sec = float(ra) if ra else 0.0
            except (ValueError, AttributeError):
                retry_after_sec = 0.0
        except (httpx.HTTPError, asyncio.TimeoutError) as e:
            logger.warning("task_llm_call_failed", attempt=attempt + 1, error=str(e))

        if attempt < max_attempts - 1:
            delay = retry_after_sec if retry_after_sec > 0 else min(1.0 * (2**attempt), 8.0)
            delay += random.uniform(0, 0.5)
            logger.warning(
                "task_llm_retry",
                status=last_status,
                attempt=attempt + 1,
                backoff_s=round(delay, 1),
            )
            await asyncio.sleep(delay)
            retry_after_sec = 0.0

    raise LLMRateLimitedError(f"LLM rate-limited after {max_attempts} attempts (last HTTP {last_status})")


class TaskWorker(BaseWorker):
    name = "task_worker"
    interval_seconds = 15.0

    async def tick(self) -> None:
        """Execute one funded/assigned task per tick.

        Only picks tasks whose escrow is funded (a task posted while the
        funder had no SOL stays 'created' forever and would block the queue);
        oldest-first so nothing starves.
        """
        from ..models.escrow import Escrow

        factory = get_session_factory()
        async with factory() as db:
            try:
                svc = TaskService(db)
                result = await db.execute(
                    select(Task)
                    .join(Escrow, Escrow.id == Task.escrow_id)
                    .where(
                        Task.status.in_(["assigned", "in_progress"]),
                        Escrow.status == "funded",
                    )
                    .order_by(Task.created_at)
                    .limit(1)
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

                try:
                    provider, model, content = await _call_llm(prompt, task.category)
                except LLMRateLimitedError as e:
                    # Retry the task on later ticks, but cap consecutive failures
                    # so one perpetually rate-limited task can't block the queue.
                    # Persist the counter (commit, not rollback) so it survives
                    # across ticks; the task stays in_progress/assigned and is
                    # re-picked until it either succeeds or hits the cap.
                    task.failure_count = (task.failure_count or 0) + 1
                    if task.failure_count >= MAX_TASK_FAILURES:
                        await svc.mark_failed(task.id, task.org_id)
                        await db.commit()
                        logger.warning(
                            "task_failed_after_retries",
                            task_id=str(task.id),
                            failure_count=task.failure_count,
                            error=str(e),
                        )
                        return
                    await db.commit()
                    logger.warning(
                        "task_llm_rate_limited",
                        task_id=str(task.id),
                        failure_count=task.failure_count,
                        error=str(e),
                    )
                    return

                # Success — reset the failure counter so a later rate-limit
                # window starts fresh.
                if task.failure_count:
                    task.failure_count = 0
                    await db.flush()

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
