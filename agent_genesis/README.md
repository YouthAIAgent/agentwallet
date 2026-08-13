# Agent Genesis

**Self-evolving agent organization platform** — Design, breed, deploy, and continuously fine-tune specialized agent teams running locally on your Mac mini M4.

```
Task → DESIGNER → Organization Spec
         ↓
       BREEDER → Evolved Genomes (Genetic Algorithm)
         ↓
      DEPLOYER → Hermes / Claude Code / Codex / Local LLM / Box
         ↓
  MEMORY FABRIC → Episodic / Semantic / Procedural (Shared)
         ↓
   FINE-TUNE LOOP → Nightly LoRA → GGUF → Hot Swap
         ↓
   OPENSPACE → Skill Retrieval / Quality / Evolution / Sharing
```

---

## Features

| Component | Description |
|-----------|-------------|
| **Designer** | Task → Agent Organization Spec (roles, runtimes, contracts, topology) |
| **Breeder** | Genetic algorithm for agent genomes (prompts, tools, params) |
| **Deployer** | Multi-runtime: Hermes, Claude Code, Codex, Ollama, box.ascii.dev |
| **Memory Fabric** | Shared Episodic/Semantic/Procedural memory across all agents |
| **Fine-Tune Loop** | Nightly MLX/Unsloth LoRA on Mac mini M4 → GGUF q4_k_m → Hot swap |
| **OpenSpace** | Skill management: retrieval, quality tracking, evolution, sharing |
| **Telegram Bot** | Control everything from Telegram (like CloddsBot) |
| **CLI** | Full command-line interface |

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
# For MLX fine-tuning (Mac only):
pip install mlx mlx-lm mlx-lora
```

### 2. Initialize Memory
```bash
python -c "from agent_genesis.memory import get_memory_fabric; m=get_memory_fabric(); print('OK:', m.stats())"
```

### 3. Design Your First Organization
```bash
genesis design "Monitor GeM tenders, parse PDF requirements, analyze capabilities, draft proposal, validate compliance, submit"
# Force runtimes per role to target what you actually have installed:
genesis design "parse docs, validate compliance" --runtime parser=local_llm --runtime validator=local_llm
```

### 4. Deploy
```bash
genesis deploy <org_id>
genesis runtimes   # see which runtimes are available before deploying
```

> **Runtimes:** `claude_code` and `codex` spawn their CLIs (`claude`/`codex`,
> npm-installed). `local_llm` deploys to a local Ollama server
> (`http://127.0.0.1:11434`). On Windows, npm `.cmd` shims are handled
> automatically via `cmd /c`.

> **Environment overrides** (per machine):
> - `GENESIS_LOCAL_LLM_MODEL=qwen3:1.7b` — which Ollama model to use
> - `GENESIS_CLAUDE_MODEL` / `GENESIS_CODEX_MODEL` — CLI model names
> - `GENESIS_RUNTIME_PREFS="parser=local_llm,validator=local_llm"` — force
>   runtimes for every design (deploy operators targeting available runtimes)

### 5. Run Fine-Tune (Mac mini M4)
```bash
genesis finetune
```

### 6. Telegram Bot
```bash
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_ALLOWED_USERS=123456789  # optional allow-list
# Console script (installed by pip install -e . / pip install .):
genesis-bot
# Or without installing:
python -m agent_genesis.cli.telegram_bot
```

### 7. Tests & CI
```bash
pip install -e . pytest pytest-asyncio ruff
python -m pytest          # 40+ tests: memory, designer, breeder, CLI, plugins, telegram bot
ruff check --select F .   # undefined names / unused imports (the real bugs)
```
CI (`.github/workflows/agent-genesis.yml`) runs lint + tests + console-script
smoke checks on every push to `agent_genesis/**`.

---

## Architecture

### Memory Fabric (The Backbone)
- **Episodic**: What happened (events, observations, actions, errors)
- **Semantic**: Facts, patterns, concepts learned
- **Procedural**: Skills, how-to procedures with success rates
- **Storage**: SQLite + optional FAISS embeddings

### Designer Agent (Architect)
```
Task → Decompose → Map Roles → Assign Runtimes → Contracts → Topology → Org Spec
```
Roles: SCOUT, PARSER, ANALYZER, WRITER, VALIDATOR, EXECUTOR, COORDINATOR, LEARNER  
Runtimes: Hermes, Claude Code, Codex, Local LLM (Ollama), Box

### Breeder Agent (Evolution)
- Population: 20 genomes per role
- Selection: Tournament (k=3)
- Crossover: Prompt blending + tool config merge
- Mutation: Prompt rewrite, tool add/remove, param jitter
- Evaluation: Golden test set → fitness score

### Deployer Agent (Orchestrator)
| Runtime | Method |
|---------|--------|
| Hermes | POST /api/agents/delegate |
| Claude Code | `claude --print` subprocess |
| Codex | `codex exec` subprocess |
| Local LLM | Ollama /api/generate |
| Box | box.ascii.dev API |

### Fine-Tune Loop (Nightly, Mac mini M4)
```
Failures (Episodic) + Successes (Procedural)
        ↓
Synthesize training pairs
        ↓
MLX LoRA (4-bit QLoRA, rank=16, seq_len=1024, batch=2)
        ↓
Validate on golden set
        ↓
Export GGUF q4_k_m
        ↓
Hot-swap into Ollama (if accuracy > 85%)
```

### OpenSpace Integration
- **Retrieval**: Semantic search for relevant skills
- **Quality**: Evidence-based (selected → applied → completed → fallback)
- **Evolution**: FIX / DERIVED / CAPTURED workflows
- **Sharing**: Package-based cloud sync

---

## Project Structure

```
agent-genesis/
├── agent_genesis/           # Core package
├── memory/                  # Memory Fabric
├── designer/                # Designer Agent
├── breeder/                 # Breeder Agent
├── deployer/                # Deployer Agent
├── finetune/                # Fine-Tune Loop
├── skill_layer/             # OpenSpace Integration
├── plugins/hermes_genesis/  # Hermes Plugin
├── cli/                     # CLI + Telegram Bot
├── orgs/                    # Saved organization specs
├── genomes/                 # Evolved champion genomes
├── checkpoints/             # LoRA adapters
├── gguf/                    # Exported GGUF models
├── golden_sets/             # Test cases per role
└── logs/
```

---

## Requirements

### Core (All Platforms)
- Python 3.11+
- aiohttp (async HTTP)
- python-telegram-bot (for Telegram bot)

### Mac mini M4 (Fine-Tuning)
- MLX + MLX-LM + MLX-LoRA
- 16GB unified memory (minimum)

### Runtimes (Optional)
- **Hermes**: Running gateway on port 8799
- **Claude Code**: `npm i -g @anthropic-ai/claude-code` + `claude auth login`
- **Codex**: `npm i -g @openai/codex` + `codex auth login`
- **Ollama**: Local LLMs (`ollama pull qwen2.5:7b`)
- **Box**: box.ascii.dev account + token

---

## Environment Variables

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ALLOWED_USERS=123456789,987654321

# Box (cloud VMs)
BOX_TOKEN=your_box_token

# Composio (pre-configured in OpenMausBot)
COMPOSIO_KEY=ck_...

# Fine-tuning
MODEL_BASE=qwen2.5-1.5b
```

---

## Example: GeM Tender Bot

```bash
# 1. Design
genesis design "Monitor GeM tenders, parse PDF requirements, analyze against capabilities, draft proposal, validate GST compliance, submit"

# 2. Load golden test cases for each role
genesis load-golden scout tests/scout_golden.json
genesis load-golden parser tests/parser_golden.json
# ...

# 3. Evolve champions
genesis breed scout 30
genesis breed parser 30
# ...

# 4. Deploy
genesis deploy <org_id>

# 5. Nightly improvement (cron)
0 3 * * * genesis finetune
```

---

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/design <task>` | Design agent organization |
| `/deploy <org_id>` | Deploy organization |
| `/breed <role> [generations]` | Evolve genomes |
| `/finetune` | Run nightly fine-tune |
| `/memory [query]` | Search memory |
| `/runtimes` | Check runtime availability |
| `/champions` | List champion genomes |
| `/orgs` | List saved organizations |
| `/skill <name>` | Get local skill |
| `/status` | System status |

---

## License

MIT License — Build, evolve, deploy freely.

---

## Credits

- **OpenSpace** (HKUDS) — Skill management layer
- **Agency Agents** (msitarzewski) — 270 agent personas
- **MLX / Unsloth** — Fast local fine-tuning on Apple Silicon
- **Hermes Agent** — Agent runtime
- **box.ascii.dev** — Cheap cloud VMs for agents
- **Composio** — 500+ app integrations