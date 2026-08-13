"""
Agent Genesis — Designer Agent (Architect)
Reads a task description → outputs complete Agent Organization Spec (JSON).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from enum import Enum

from agent_genesis.memory import get_memory_fabric


class AgentRole(str, Enum):
    SCOUT = "scout"
    PARSER = "parser"
    ANALYZER = "analyzer"
    WRITER = "writer"
    VALIDATOR = "validator"
    EXECUTOR = "executor"
    COORDINATOR = "coordinator"
    LEARNER = "learner"


class RuntimeTarget(str, Enum):
    HERMES = "hermes"
    CLAUDE_CODE = "claude_code"
    CODEX = "codex"
    LOCAL_LLM = "local_llm"
    BOX = "box"


@dataclass
class AgentSpec:
    id: str
    name: str
    role: AgentRole
    runtime: RuntimeTarget
    model: str
    persona: str
    tools: List[str]
    input_contract: Dict[str, Any]
    output_contract: Dict[str, Any]
    depends_on: List[str]
    config: Dict[str, Any]


@dataclass
class OrganizationSpec:
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    agents: List[AgentSpec] = None
    topology: Dict[str, List[str]] = None
    entry_points: List[str] = None
    exit_points: List[str] = None
    shared_memory: List[str] = None
    global_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.agents is None:
            self.agents = []
        if self.topology is None:
            self.topology = {}
        if self.entry_points is None:
            self.entry_points = []
        if self.exit_points is None:
            self.exit_points = []
        if self.shared_memory is None:
            self.shared_memory = []
        if self.global_config is None:
            self.global_config = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "agents": [asdict(a) for a in self.agents],
            "topology": self.topology,
            "entry_points": self.entry_points,
            "exit_points": self.exit_points,
            "shared_memory": self.shared_memory,
            "global_config": self.global_config,
        }


# ---- Persona library (inline, can be loaded from file later) ----
PERSONAS: Dict[AgentRole, str] = {
    AgentRole.SCOUT: """You are a Research Scout. Your job: find, verify, and summarize information from external sources.
Tools: web_search, agent_reach (Reddit/Twitter/HN/crypto), composio (GitHub, Notion, Gmail).
Output: structured findings with sources and confidence scores.""",
    AgentRole.PARSER: """You are a Data Parser. Extract structured data from unstructured sources (PDF, HTML, JSON, emails).
Tools: pdf_extract, html_parse, json_schema_validate, composio (Gmail, Google Drive).
Output: validated JSON matching provided schema.""",
    AgentRole.ANALYZER: """You are an Analyst. Synthesize, compare, reason, and derive insights from parsed data.
Tools: sql_query, statistical_analysis, comparison_matrix, composio (Sheets, Notion).
Output: analysis report with recommendations and confidence.""",
    AgentRole.WRITER: """You are a Technical Writer. Produce clear, accurate deliverables (proposals, docs, code, reports).
Tools: markdown_render, template_engine, composio (Gmail, Notion, GitHub, Linear).
Output: final deliverable in requested format.""",
    AgentRole.VALIDATOR: """You are a QA Validator. Check correctness, compliance, quality against rules.
Tools: unit_test_runner, lint, schema_check, compliance_rules, composio (Jira, Linear).
Output: pass/fail with evidence and remediation steps.""",
    AgentRole.EXECUTOR: """You are an Executor. Take precise actions via APIs and tools.
Tools: composio (GitHub, Linear, Slack, Gmail, Jira), ssh, docker, k8s, kubernetes.
Output: action confirmation with artifacts.""",
    AgentRole.COORDINATOR: """You are a Coordinator. Orchestrate agents, manage flow, handle retries/branching.
Tools: task_queue, agent_delegate, progress_tracker, composio (Slack, Linear).
Output: orchestration status and routing decisions.""",
    AgentRole.LEARNER: """You are a Learner. Capture patterns, update memory, propose improvements.
Tools: memory_fabric (episodic/semantic/procedural), pattern_miner, fine_tune_trigger.
Output: learned facts, new skills, evolution proposals.""",
}

TOOL_MAP: Dict[AgentRole, List[str]] = {
    AgentRole.SCOUT: ["web_search", "agent_reach_search", "composio_github", "composio_notion", "composio_gmail"],
    AgentRole.PARSER: ["pdf_extract", "html_parse", "json_schema_validate", "composio_gmail", "composio_googledrive"],
    AgentRole.ANALYZER: ["sql_query", "statistical_analysis", "comparison_matrix", "composio_googlesheets", "composio_notion"],
    AgentRole.WRITER: ["markdown_render", "template_engine", "composio_gmail", "composio_notion", "composio_github", "composio_linear"],
    AgentRole.VALIDATOR: ["unit_test_runner", "lint", "schema_check", "compliance_rules", "composio_jira", "composio_linear"],
    AgentRole.EXECUTOR: ["composio_github", "composio_linear", "composio_slack", "composio_gmail", "ssh", "docker"],
    AgentRole.COORDINATOR: ["task_queue", "agent_delegate", "progress_tracker", "composio_slack", "composio_linear"],
    AgentRole.LEARNER: ["memory_fabric", "pattern_miner", "fine_tune_trigger"],
}

ROLE_KEYWORDS: Dict[AgentRole, List[str]] = {
    AgentRole.SCOUT: ["search", "find", "monitor", "gather", "discover", "fetch", "watch", "track", "scan"],
    AgentRole.PARSER: ["extract", "parse", "structure", "convert", "normalize", "transform", "process"],
    AgentRole.ANALYZER: ["analyze", "evaluate", "compare", "decide", "reason", "synthesize", "assess"],
    AgentRole.WRITER: ["write", "generate", "draft", "create", "compose", "document", "produce"],
    AgentRole.VALIDATOR: ["validate", "check", "verify", "test", "audit", "compliance", "review"],
    AgentRole.EXECUTOR: ["execute", "deploy", "submit", "send", "create", "update", "delete", "post", "push"],
    AgentRole.COORDINATOR: ["orchestrate", "manage", "coordinate", "schedule", "route", "supervise"],
    AgentRole.LEARNER: ["learn", "capture", "pattern", "improve", "optimize", "evolve", "adapt"],
}

RUNTIME_STRENGTHS: Dict[RuntimeTarget, List[AgentRole]] = {
    RuntimeTarget.CLAUDE_CODE: [AgentRole.WRITER, AgentRole.ANALYZER, AgentRole.PARSER],
    RuntimeTarget.CODEX: [AgentRole.EXECUTOR, AgentRole.VALIDATOR, AgentRole.SCOUT],
    RuntimeTarget.HERMES: [AgentRole.COORDINATOR, AgentRole.LEARNER],
    RuntimeTarget.LOCAL_LLM: [AgentRole.PARSER, AgentRole.VALIDATOR],
    RuntimeTarget.BOX: [AgentRole.EXECUTOR, AgentRole.SCOUT],
}

MODEL_DEFAULTS: Dict[RuntimeTarget, str] = {
    RuntimeTarget.CLAUDE_CODE: "claude-3-5-sonnet-20241022",
    RuntimeTarget.CODEX: "gpt-4o",
    RuntimeTarget.HERMES: "qwen2.5:7b",
    RuntimeTarget.LOCAL_LLM: "qwen2.5:7b",
    RuntimeTarget.BOX: "claude-3-5-sonnet-20241022",
}

INPUT_CONTRACTS: Dict[AgentRole, Dict] = {
    AgentRole.SCOUT: {"task_context": "object", "query": "string", "keywords": "array"},
    AgentRole.PARSER: {"raw_data": "string", "schema": "object", "source_type": "string"},
    AgentRole.ANALYZER: {"parsed_data": "object", "questions": "array", "context": "object"},
    AgentRole.WRITER: {"analysis": "object", "template": "string", "format": "string"},
    AgentRole.VALIDATOR: {"artifact": "object", "rules": "array", "standards": "object"},
    AgentRole.EXECUTOR: {"action_plan": "object", "credentials": "object", "params": "object"},
    AgentRole.COORDINATOR: {"org_state": "object", "pending_tasks": "array", "resources": "object"},
    AgentRole.LEARNER: {"episodes": "array", "feedback": "object", "metrics": "object"},
}

OUTPUT_CONTRACTS: Dict[AgentRole, Dict] = {
    AgentRole.SCOUT: {"findings": "array", "sources": "array", "confidence": "float"},
    AgentRole.PARSER: {"structured_data": "object", "validation": "object", "warnings": "array"},
    AgentRole.ANALYZER: {"insights": "array", "recommendations": "array", "confidence": "float"},
    AgentRole.WRITER: {"deliverable": "string", "format": "string", "metadata": "object"},
    AgentRole.VALIDATOR: {"passed": "boolean", "evidence": "array", "issues": "array"},
    AgentRole.EXECUTOR: {"result": "object", "artifacts": "array", "status": "string"},
    AgentRole.COORDINATOR: {"routing": "array", "status": "string", "next_steps": "array"},
    AgentRole.LEARNER: {"learned_facts": "array", "new_skills": "array", "evolution_proposals": "array"},
}

DEPENDENCY_GRAPH: Dict[AgentRole, List[AgentRole]] = {
    AgentRole.SCOUT: [],
    AgentRole.PARSER: [AgentRole.SCOUT],
    AgentRole.ANALYZER: [AgentRole.PARSER, AgentRole.SCOUT],
    AgentRole.WRITER: [AgentRole.ANALYZER],
    AgentRole.VALIDATOR: [AgentRole.WRITER, AgentRole.EXECUTOR],
    AgentRole.EXECUTOR: [AgentRole.WRITER, AgentRole.VALIDATOR],
    AgentRole.COORDINATOR: [AgentRole.SCOUT, AgentRole.ANALYZER],
    AgentRole.LEARNER: [AgentRole.VALIDATOR, AgentRole.EXECUTOR],
}


class DesignerAgent:
    """
    Task → Organization Spec.
    Uses keyword mapping + simple heuristics to decompose and assign roles/runtimes.
    """

    def __init__(self):
        self.memory = get_memory_fabric()

    def design(self, task: str, constraints: Optional[Dict] = None) -> OrganizationSpec:
        constraints = constraints or {}

        # 1. Decompose into subproblems (simple keyword-based for MVP)
        subproblems = self._decompose_task(task)
        if not subproblems:
            subproblems = [task]

        # 2. Map each subproblem to a role
        roles = self._map_roles(subproblems)

        # 3. Deduplicate roles, keep order
        seen = set()
        unique_roles = []
        for r in roles:
            if r not in seen:
                seen.add(r)
                unique_roles.append(r)
        roles = unique_roles

        # 4. Assign runtimes
        runtime_prefs = constraints.get("runtime_prefs", {})
        runtime_assign = self._assign_runtimes(roles, runtime_prefs)

        # 5. Build agents
        agents = []
        for i, role in enumerate(roles):
            spec = AgentSpec(
                id=f"agent_{i}",
                name=f"{role.value.title()} {i}",
                role=role,
                runtime=runtime_assign[role],
                model=MODEL_DEFAULTS.get(runtime_assign[role], "qwen2.5:7b"),
                persona=PERSONAS.get(role, "You are a specialized agent."),
                tools=TOOL_MAP.get(role, []),
                input_contract=INPUT_CONTRACTS.get(role, {}),
                output_contract=OUTPUT_CONTRACTS.get(role, {}),
                depends_on=[f"agent_{roles.index(d)}" for d in DEPENDENCY_GRAPH.get(role, []) if d in roles],
                config=constraints.get("agent_config", {}).get(role.value, {}),
            )
            agents.append(spec)

        # 6. Build topology
        topology = {a.id: a.depends_on for a in agents}
        entry_points = [a.id for a in agents if not a.depends_on]
        exit_roles = {AgentRole.WRITER, AgentRole.EXECUTOR}
        exit_points = [a.id for a in agents if a.role in exit_roles]

        org = OrganizationSpec(
            id=str(uuid.uuid4())[:8],
            name=self._generate_name(task),
            description=task[:200],
            agents=agents,
            topology=topology,
            entry_points=entry_points,
            exit_points=exit_points,
            shared_memory=["task_context", "global_facts"],
            global_config=constraints.get("global_config", {}),
        )

        # Persist
        self.memory.save_org(org.id, org.to_dict())
        self.memory.remember(
            agent_id="designer",
            event_type="design",
            content=f"Designed org '{org.name}' for: {task}",
            metadata={"org_id": org.id, "spec": org.to_dict(), "constraints": constraints},
        )

        return org

    # ---------- internal helpers ----------
    def _decompose_task(self, task: str) -> List[str]:
        """Simple heuristic decomposition - can be replaced with LLM call later."""
        # Split on common separators, filter noise
        parts = re.split(r"[;,]| and then | then |, then |; then ", task, flags=re.I)
        parts = [p.strip() for p in parts if p.strip()]
        if len(parts) > 8:
            # Too many, keep first 8
            parts = parts[:8]
        return parts if len(parts) > 1 else [task]

    def _map_roles(self, subproblems: List[str]) -> List[AgentRole]:
        roles = []
        for sp in subproblems:
            scores = {role: sum(1 for kw in kws if kw in sp.lower()) for role, kws in ROLE_KEYWORDS.items()}
            best = max(scores, key=scores.get)
            if scores[best] == 0:
                best = AgentRole.ANALYZER
            roles.append(best)
        return roles

    def _assign_runtimes(self, roles: List[AgentRole], prefs: Dict) -> Dict[AgentRole, RuntimeTarget]:
        assign = {}
        for role in set(roles):
            if role.value in prefs:
                assign[role] = RuntimeTarget(prefs[role.value])
            else:
                for rt, strong in RUNTIME_STRENGTHS.items():
                    if role in strong:
                        assign[role] = rt
                        break
                else:
                    assign[role] = RuntimeTarget.HERMES
        return assign

    def _generate_name(self, task: str) -> str:
        words = [w for w in re.split(r"\W+", task.lower()) if w and w not in {"the", "a", "an", "to", "for", "of", "and", "or", "in", "on", "with", "from"}]
        return "-".join(words[:4]) + "-org"


import re  # moved here to avoid circular import issues

if __name__ == "__main__":
    d = DesignerAgent()
    spec = d.design("Monitor GeM tenders, parse PDF requirements, analyze against capabilities, draft proposal, validate compliance, submit")
    print(json.dumps(spec.to_dict(), indent=2))
