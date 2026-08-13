"""
Agent Genesis — Hermes Plugin
Exposes Agent Genesis as native Hermes tools.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Core imports
from agent_genesis.memory import get_memory_fabric
from agent_genesis.designer.architect import DesignerAgent, OrganizationSpec as OrganizationSpec
from agent_genesis.breeder.evolution import BreederAgent, Genome
from agent_genesis.deployer.orchestrator import DeployerAgent, RuntimeType as RuntimeType
from agent_genesis.finetune.loop import FineTuneLoop
from agent_genesis.skill_layer.openspace_integration import get_openspace_layer

# Global instances
_memory = get_memory_fabric()
_designer = DesignerAgent()
_breeder = BreederAgent()
_deployer = DeployerAgent()
_finetune = FineTuneLoop()
_openspace = get_openspace_layer()


# =============================================================================
# DESIGNER TOOLS
# =============================================================================

async def genesis_design(
    task: str,
    constraints: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Design an agent organization from a task description.
    
    Args:
        task: Natural language description of the workflow
        constraints: Optional runtime preferences, agent configs, etc.
    
    Returns:
        Organization spec with agents, topology, contracts
    """
    spec = _designer.design(task, constraints or {})
    return {"status": "designed", "spec": spec.to_dict()}


async def genesis_load_org(org_id: str) -> Dict[str, Any]:
    """Load previously saved organization spec."""
    spec = _memory.load_org(org_id)
    if spec:
        return {"status": "loaded", "spec": spec}
    return {"status": "not_found", "org_id": org_id}


async def genesis_list_orgs() -> Dict[str, Any]:
    """List all saved organization specs."""
    orgs = _memory.list_orgs()
    return {"orgs": orgs}


# =============================================================================
# BREEDER TOOLS
# =============================================================================

async def genesis_breed(
    role: str,
    generations: int = 50,
    population_size: int = 20,
    base_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evolve agent genomes for a role using genetic algorithm.
    
    Requires golden test set to be loaded first via genesis_load_golden.
    """
    golden_set = _breeder.get_golden_set(role)
    if not golden_set:
        return {
            "status": "error",
            "message": f"No golden test set for '{role}'. Load test cases first with genesis_load_golden."
        }

    # Initialize population if needed
    if role not in _breeder.populations:
        _breeder.load_population(role)
    
    if not _breeder.populations.get(role):
        if not base_prompt:
            return {
                "status": "error",
                "message": "Population not initialized. Provide base_prompt or call genesis_init_population first."
            }
        base_genome = Genome(
            agent_id=f"{role}_base",
            role=role,
            system_prompt=base_prompt,
            tool_config={},
            model_params={"temperature": 0.3},
        )
        _breeder.initialize_population(role, base_genome, size=population_size)

    champion = _breeder.evolve(role, generations=generations, population_size=population_size)
    return {
        "status": "evolved",
        "champion": champion.to_dict(),
        "fitness": champion.fitness,
        "generation": champion.generation,
    }


async def genesis_init_population(
    role: str,
    base_prompt: str,
    size: int = 20,
) -> Dict[str, Any]:
    """Initialize population for a role with a base prompt."""
    base_genome = Genome(
        agent_id=f"{role}_base",
        role=role,
        system_prompt=base_prompt,
        tool_config={},
        model_params={"temperature": 0.3},
    )
    _breeder.initialize_population(role, base_genome, size=size)
    return {"status": "initialized", "role": role, "size": size}


async def genesis_load_golden(
    role: str,
    test_cases: List[Dict],
) -> Dict[str, Any]:
    """Load golden test set for a role."""
    _breeder.load_golden_set(role, test_cases)
    return {"status": "loaded", "role": role, "count": len(test_cases)}


async def genesis_list_champions() -> Dict[str, Any]:
    """List all champion genomes."""
    champs = _breeder.list_champions()
    return {
        "champions": {role: g.to_dict() for role, g in champs.items()}
    }


async def genesis_get_champion(role: str) -> Dict[str, Any]:
    """Get champion genome for a role."""
    champ = _breeder.get_champion(role)
    if champ:
        return {"status": "found", "champion": champ.to_dict()}
    return {"status": "not_found", "role": role}


# =============================================================================
# DEPLOYER TOOLS
# =============================================================================

async def genesis_deploy(
    spec: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deploy agent organization across runtimes.
    
    Args:
        spec: Organization spec from genesis_design
    """
    result = await _deployer.deploy_organization(spec)
    return result


async def genesis_check_runtimes() -> Dict[str, Any]:
    """Check availability of all runtimes."""
    results = await _deployer.list_available_runtimes()
    return {rt.value: ok for rt, ok in results.items()}


async def genesis_deploy_agent(
    agent_spec: Dict[str, Any],
    deployment_id: str = "manual",
) -> Dict[str, Any]:
    """Deploy a single agent."""
    result = await _deployer.deploy_agent(agent_spec, deployment_id)
    return result


# =============================================================================
# FINE-TUNE TOOLS
# =============================================================================

async def genesis_finetune(min_samples: int = 50) -> Dict[str, Any]:
    """Run nightly fine-tune loop manually."""
    result = await _finetune.run_nightly(min_samples=min_samples)
    return result


async def genesis_finetune_status() -> Dict[str, Any]:
    """Get recent fine-tune runs."""
    runs = _memory.recall(agent_id="finetune", limit=10)
    return {"runs": runs}


# =============================================================================
# MEMORY TOOLS
# =============================================================================

async def genesis_memory(
    query: Optional[str] = None,
    agent_id: Optional[str] = None,
    memory_type: str = "all",
    limit: int = 20,
) -> Dict[str, Any]:
    """Query shared memory fabric."""
    results = {}
    
    if memory_type in ("all", "episodic"):
        results["episodic"] = _memory.recall(agent_id=agent_id, limit=limit)
    
    if memory_type in ("all", "semantic"):
        results["semantic"] = _memory.query_facts(query, agent_id=agent_id, limit=limit)
    
    if memory_type in ("all", "procedural"):
        if query:
            skill = _memory.get_skill(query, agent_id)
            results["procedural"] = [skill] if skill else []
        else:
            results["procedural"] = _memory.list_skills(agent_id=agent_id, limit=limit)
    
    if memory_type in ("all", "orgs"):
        results["orgs"] = _memory.list_orgs()
    
    return results


async def genesis_memory_stats() -> Dict[str, Any]:
    """Get memory fabric statistics."""
    return _memory.stats()


async def genesis_search_memory(query: str, limit: int = 20) -> Dict[str, Any]:
    """Keyword search across memory."""
    results = _memory.keyword_search(query, limit=limit)
    return {"results": results}


# =============================================================================
# OPENSPACE TOOLS
# =============================================================================

async def openspace_search(
    task: str,
    role: str = "general",
    top_k: int = 5,
) -> Dict[str, Any]:
    """Search OpenSpace skill library."""
    skills = await _openspace.find_skills(task, role, top_k)
    return {"skills": skills}


async def openspace_run_skill(
    agent_id: str,
    skill_id: str,
    task: str,
    context: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Execute task with specific skill, capturing quality evidence."""
    result = await _openspace.run_with_skill(agent_id, skill_id, task, context or {})
    return result


async def openspace_skill_quality(skill_id: str) -> Dict[str, Any]:
    """Get quality metrics for a skill."""
    return await _openspace.get_skill_quality(skill_id)


async def openspace_evolve_skill(
    skill_id: str,
    execution_id: str,
    evolution_type: str = "FIX",
) -> Dict[str, Any]:
    """Propose skill evolution based on execution evidence."""
    return await _openspace.propose_evolution(skill_id, execution_id, evolution_type)


async def openspace_import(package_id: str, skill_id: str) -> Dict[str, Any]:
    """Import skill from OpenSpace cloud package."""
    skill = await _openspace.import_cloud_skill(package_id, skill_id)
    return {"skill": skill, "status": "imported"}


# Local fallback tools (no OpenSpace required)
async def openspace_local_search(query: str, limit: int = 10) -> Dict[str, Any]:
    """Search local procedural memory for skills."""
    skills = _openspace.find_skills_local(query, limit)
    return {"skills": skills}


async def openspace_local_skill(skill_name: str) -> Dict[str, Any]:
    """Get skill from local procedural memory."""
    skill = _openspace.get_skill_local(skill_name)
    return {"skill": skill} if skill else {"status": "not_found"}


async def openspace_local_record(
    agent_id: str,
    skill_name: str,
    success: bool,
    metadata: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Record skill execution result locally."""
    _openspace.record_skill_execution(agent_id, skill_name, success, metadata)
    return {"status": "recorded"}


# =============================================================================
# TOOL REGISTRY
# =============================================================================

TOOLS = [
    # Designer
    {"name": "genesis_design", "func": genesis_design, "description": "Design agent organization from task"},
    {"name": "genesis_load_org", "func": genesis_load_org, "description": "Load saved organization spec"},
    {"name": "genesis_list_orgs", "func": genesis_list_orgs, "description": "List all saved orgs"},
    
    # Breeder
    {"name": "genesis_breed", "func": genesis_breed, "description": "Evolve agent genomes for a role"},
    {"name": "genesis_init_population", "func": genesis_init_population, "description": "Initialize population for evolution"},
    {"name": "genesis_load_golden", "func": genesis_load_golden, "description": "Load golden test set for role"},
    {"name": "genesis_list_champions", "func": genesis_list_champions, "description": "List all champion genomes"},
    {"name": "genesis_get_champion", "func": genesis_get_champion, "description": "Get champion genome for role"},
    
    # Deployer
    {"name": "genesis_deploy", "func": genesis_deploy, "description": "Deploy organization across runtimes"},
    {"name": "genesis_check_runtimes", "func": genesis_check_runtimes, "description": "Check runtime availability"},
    {"name": "genesis_deploy_agent", "func": genesis_deploy_agent, "description": "Deploy single agent"},
    
    # Fine-tune
    {"name": "genesis_finetune", "func": genesis_finetune, "description": "Run nightly fine-tune loop"},
    {"name": "genesis_finetune_status", "func": genesis_finetune_status, "description": "Get fine-tune run history"},
    
    # Memory
    {"name": "genesis_memory", "func": genesis_memory, "description": "Query shared memory fabric"},
    {"name": "genesis_memory_stats", "func": genesis_memory_stats, "description": "Get memory statistics"},
    {"name": "genesis_search_memory", "func": genesis_search_memory, "description": "Keyword search memory"},
    
    # OpenSpace
    {"name": "openspace_search", "func": openspace_search, "description": "Search OpenSpace skill library"},
    {"name": "openspace_run_skill", "func": openspace_run_skill, "description": "Run skill with quality tracking"},
    {"name": "openspace_skill_quality", "func": openspace_skill_quality, "description": "Get skill quality metrics"},
    {"name": "openspace_evolve_skill", "func": openspace_evolve_skill, "description": "Propose skill evolution"},
    {"name": "openspace_import", "func": openspace_import, "description": "Import skill from cloud"},
    
    # OpenSpace Local Fallback
    {"name": "openspace_local_search", "func": openspace_local_search, "description": "Search local skills"},
    {"name": "openspace_local_skill", "func": openspace_local_skill, "description": "Get local skill"},
    {"name": "openspace_local_record", "func": openspace_local_record, "description": "Record local skill execution"},
]

# Plugin metadata for Hermes
PLUGIN_METADATA = {
    "name": "agent-genesis",
    "version": "0.1.0",
    "description": "Self-evolving agent organization platform",
    "tools": [t["name"] for t in TOOLS],
}


# Helper for Hermes tool registration
def register_all_tools(register_func):
    """Register all tools with Hermes register_func."""
    for tool in TOOLS:
        register_func(
            name=tool["name"],
            description=tool["description"],
            func=tool["func"],
        )


if __name__ == "__main__":
    # Test imports work
    print("Agent Genesis Hermes Plugin loaded")
    print(f"Tools: {len(TOOLS)}")
    for t in TOOLS:
        print(f"  - {t['name']}")
