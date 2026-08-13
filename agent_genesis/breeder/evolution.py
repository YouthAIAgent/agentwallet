"""
Agent Genesis — Breeder Agent (Evolution Engine)
Genetic algorithm for evolving agent genomes (prompts + tools + configs).
"""

from __future__ import annotations

import json
import random
import copy
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from pathlib import Path

from agent_genesis.memory import get_memory_fabric


@dataclass
class Genome:
    """Complete agent configuration that can evolve."""
    agent_id: str
    role: str
    system_prompt: str
    tool_config: Dict[str, Any] = field(default_factory=dict)
    model_params: Dict[str, Any] = field(default_factory=dict)
    few_shot_examples: List[Dict] = field(default_factory=list)
    fitness: float = 0.0
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    mutations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Genome":
        return Genome(**d)


class BreederAgent:
    """
    Genetic algorithm for agent evolution:
    - Population: 20 genomes per role
    - Selection: Tournament (k=3)
    - Crossover: Prompt blending + tool config merge
    - Mutation: Prompt rewrite, tool add/remove, param jitter
    - Evaluation: Run on golden test set, score by metrics
    """

    def __init__(self):
        self.memory = get_memory_fabric()
        self.populations: Dict[str, List[Genome]] = {}  # role -> genomes
        self.golden_sets: Dict[str, List[Dict]] = {}    # role -> test cases

    # ------------------------------------------------------ population init
    def initialize_population(
        self, role: str, base_genome: Genome, size: int = 20
    ) -> List[Genome]:
        """Create initial population from base genome + variations."""
        population = [base_genome]
        for i in range(size - 1):
            mutant = self._mutate(copy.deepcopy(base_genome), mutation_rate=0.3)
            mutant.agent_id = f"{role}_gen0_{i}"
            mutant.generation = 0
            population.append(mutant)
        self.populations[role] = population
        return population

    def load_population(self, role: str) -> List[Genome]:
        """Load previously saved population from memory."""
        skill = self.memory.get_skill(f"population_{role}")
        if skill:
            steps = json.loads(skill["steps"])
            self.populations[role] = [Genome.from_dict(g) for g in steps]
            return self.populations[role]
        return []

    def save_population(self, role: str) -> None:
        """Save current population to procedural memory."""
        if role in self.populations:
            self.memory.learn_skill(
                agent_id="breeder",
                skill_name=f"population_{role}",
                steps=[g.to_dict() for g in self.populations[role]],
                description=f"Evolved population for {role} role",
            )

    # ------------------------------------------------------ golden sets
    def load_golden_set(self, role: str, test_cases: List[Dict]) -> None:
        """Load test cases for a role."""
        self.golden_sets[role] = test_cases
        # Also store in memory
        self.memory.learn_skill(
            agent_id="breeder",
            skill_name=f"golden_set_{role}",
            steps=test_cases,
            description=f"Golden test set for {role}",
        )

    def get_golden_set(self, role: str) -> List[Dict]:
        if role in self.golden_sets:
            return self.golden_sets[role]
        # Try load from memory
        skill = self.memory.get_skill(f"golden_set_{role}")
        if skill:
            return json.loads(skill["steps"])
        return []

    # ------------------------------------------------------ evolution
    def evolve(
        self, role: str, generations: int = 50, population_size: int = 20
    ) -> Genome:
        """Run evolution for a role, return best genome."""
        if role not in self.populations:
            self.load_population(role)

        if not self.populations.get(role):
            raise ValueError(f"Population for {role} not initialized. Call initialize_population first.")

        golden_set = self.get_golden_set(role)
        if not golden_set:
            raise ValueError(f"No golden test set for {role}. Call load_golden_set first.")

        for gen in range(generations):
            # Evaluate all
            for genome in self.populations[role]:
                genome.fitness = self._evaluate_genome(genome, golden_set, role)

            # Sort by fitness descending
            self.populations[role].sort(key=lambda g: g.fitness, reverse=True)

            # Log best
            best = self.populations[role][0]
            self.memory.remember(
                agent_id="breeder",
                event_type="evolution_step",
                content=f"Gen {gen} best {role}: fitness={best.fitness:.4f}",
                metadata={"genome_id": best.agent_id, "fitness": best.fitness, "generation": gen},
            )

            # Elitism: keep top 2
            next_gen = self.populations[role][:2]

            # Fill rest via tournament selection + crossover + mutation
            while len(next_gen) < population_size:
                parent1 = self._tournament_select(self.populations[role])
                parent2 = self._tournament_select(self.populations[role])
                child = self._crossover(parent1, parent2)
                child = self._mutate(child, mutation_rate=0.15)
                child.generation = gen + 1
                child.parent_ids = [parent1.agent_id, parent2.agent_id]
                next_gen.append(child)

            self.populations[role] = next_gen

        # Save final population
        self.save_population(role)

        # Return champion
        champion = self.populations[role][0]
        self._save_champion(role, champion)
        return champion

    # ------------------------------------------------------ evaluation
    def _evaluate_genome(self, genome: Genome, golden_set: List[Dict], role: str) -> float:
        """Run genome on golden test cases, return aggregate score."""
        # In production: deploy to Hermes/Claude Code, run, measure
        # For MVP: simulate based on genome properties
        scores = []
        for test_case in golden_set:
            score = self._simulate_run(genome, test_case, role)
            scores.append(score)
        return sum(scores) / len(scores) if scores else 0.0

    def _simulate_run(self, genome: Genome, test_case: Dict, role: str) -> float:
        """Simulate agent run on test case. Returns 0-1 score."""
        # Heuristic based on genome properties
        base_score = 0.4

        # Reward: few-shot examples
        base_score += min(0.2, len(genome.few_shot_examples) * 0.05)

        # Reward: specific tools configured
        base_score += min(0.2, len(genome.tool_config) * 0.05)

        # Reward: tuned model params
        if genome.model_params.get("temperature", 0.7) < 0.5:
            base_score += 0.05  # deterministic tasks benefit from low temp

        # Small random component
        return min(1.0, base_score + random.uniform(-0.05, 0.05))

    # ------------------------------------------------------ selection
    def _tournament_select(self, population: List[Genome], k: int = 3) -> Genome:
        return max(random.sample(population, k), key=lambda g: g.fitness)

    # ------------------------------------------------------ crossover
    def _crossover(self, parent1: Genome, parent2: Genome) -> Genome:
        """Blend two genomes."""
        child = Genome(
            agent_id=f"cross_{parent1.agent_id[:8]}_{parent2.agent_id[:8]}",
            role=parent1.role,
            system_prompt=self._blend_prompts(parent1.system_prompt, parent2.system_prompt),
            tool_config=self._merge_configs(parent1.tool_config, parent2.tool_config),
            model_params=self._merge_params(parent1.model_params, parent2.model_params),
            few_shot_examples=parent1.few_shot_examples[:2] + parent2.few_shot_examples[:2],
        )
        return child

    def _blend_prompts(self, p1: str, p2: str) -> str:
        """Intelligent prompt crossover - combine best sections."""
        sections1 = self._split_prompt_sections(p1)
        sections2 = self._split_prompt_sections(p2)
        blended = {}
        for key in set(sections1) | set(sections2):
            blended[key] = random.choice([
                sections1.get(key, ""), sections2.get(key, "")
            ])
        return self._assemble_prompt(blended)

    def _split_prompt_sections(self, prompt: str) -> Dict[str, str]:
        sections = {"identity": "", "mission": "", "workflow": "", "constraints": "", "output_format": ""}
        current = "identity"
        for line in prompt.split("\n"):
            if any(k in line.lower() for k in sections.keys()):
                for k in sections:
                    if k in line.lower():
                        current = k
                        break
            sections[current] += line + "\n"
        return sections

    def _assemble_prompt(self, sections: Dict[str, str]) -> str:
        return "\n".join(v for v in sections.values() if v.strip())

    def _merge_configs(self, c1: Dict, c2: Dict) -> Dict:
        merged = c1.copy()
        for k, v in c2.items():
            if k not in merged or random.random() < 0.5:
                merged[k] = v
        return merged

    def _merge_params(self, p1: Dict, p2: Dict) -> Dict:
        merged = {}
        for k in set(p1) | set(p2):
            if k in p1 and k in p2:
                v1, v2 = p1[k], p2[k]
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    merged[k] = (v1 + v2) / 2
                else:
                    merged[k] = random.choice([v1, v2])
            else:
                merged[k] = p1.get(k) or p2.get(k)
        return merged

    # ------------------------------------------------------ mutation
    def _mutate(self, genome: Genome, mutation_rate: float) -> Genome:
        mutations = []

        if random.random() < mutation_rate:
            genome.system_prompt = self._mutate_prompt(genome.system_prompt)
            mutations.append("prompt")

        if random.random() < mutation_rate:
            genome.tool_config = self._mutate_tools(genome.tool_config)
            mutations.append("tools")

        if random.random() < mutation_rate:
            genome.model_params = self._mutate_params(genome.model_params)
            mutations.append("params")

        if random.random() < mutation_rate:
            genome.few_shot_examples = self._mutate_few_shot(genome.few_shot_examples)
            mutations.append("few_shot")

        genome.mutations.extend(mutations)
        return genome

    def _mutate_prompt(self, prompt: str) -> str:
        # Simple mutations: add/remove/rephrase sections
        # In production: use local LLM to rephrase
        lines = prompt.split("\n")
        if random.random() < 0.5 and lines:
            # Remove random line
            lines.pop(random.randrange(len(lines)))
        else:
            # Add clarification
            idx = random.randrange(len(lines) + 1)
            lines.insert(idx, "# [Evolved] Be precise and verify outputs.")
        return "\n".join(lines)

    def _mutate_tools(self, tools: Dict) -> Dict:
        all_tools = [
            "web_search", "pdf_extract", "html_parse", "sql_query",
            "composio_github", "composio_gmail", "composio_notion",
            "composio_linear", "composio_slack", "ssh", "docker",
        ]
        mutated = tools.copy()
        if random.random() < 0.5 and all_tools:
            # Add random tool
            new_tool = random.choice(all_tools)
            mutated[new_tool] = {"enabled": True}
        elif random.random() < 0.3 and mutated:
            # Remove random tool
            del mutated[random.choice(list(mutated.keys()))]
        return mutated

    def _mutate_params(self, params: Dict) -> Dict:
        defaults = {"temperature": 0.7, "top_p": 0.9, "max_tokens": 4096}
        mutated = {**defaults, **params}
        for k in mutated:
            if isinstance(mutated[k], (int, float)):
                mutated[k] = max(0.0, mutated[k] * random.uniform(0.8, 1.2))
        return mutated

    def _mutate_few_shot(self, examples: List) -> List:
        # In production: generate variations using LLM
        return examples

    # ------------------------------------------------------ save champion
    def _save_champion(self, role: str, genome: Genome) -> None:
        """Persist champion genome for deployment."""
        self.memory.learn_skill(
            agent_id="breeder",
            skill_name=f"champion_{role}",
            steps=[{"action": "deploy_genome", "genome": genome.to_dict()}],
            description=f"Evolved champion genome for {role} role (gen {genome.generation}, fitness {genome.fitness:.4f})",
        )

    # ------------------------------------------------------ utility
    def get_champion(self, role: str) -> Optional[Genome]:
        """Get current champion genome for a role."""
        skill = self.memory.get_skill(f"champion_{role}")
        if skill and skill["steps"]:
            return Genome.from_dict(skill["steps"][0].get("genome", {}))
        return None

    def list_champions(self) -> Dict[str, Genome]:
        """Get all champion genomes."""
        champs = {}
        for skill in self.memory.list_skills("breeder"):
            if skill["skill_name"].startswith("champion_"):
                role = skill["skill_name"].replace("champion_", "")
                genome = self.get_champion(role)
                if genome:
                    champs[role] = genome
        return champs


if __name__ == "__main__":
    # Quick test
    b = BreederAgent()
    base = Genome(
        agent_id="scout_base",
        role="scout",
        system_prompt="You are a research scout. Find and verify information.",
        tool_config={"web_search": {"enabled": True}},
        model_params={"temperature": 0.3},
    )
    b.initialize_population("scout", base, size=10)
    b.load_golden_set("scout", [
        {"input": "Find recent AI funding news", "expected": "list of articles"},
        {"input": "Monitor Reddit for AI agent discussions", "expected": "summary"},
    ])
    champion = b.evolve("scout", generations=5, population_size=10)
    print(f"Champion: {champion.agent_id}, fitness: {champion.fitness:.4f}")
