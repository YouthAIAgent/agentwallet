"""
Agent Genesis — Telegram Bot + CLI
Control Agent Genesis from Telegram (like CloddsBot) and command line.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from agent_genesis.memory import get_memory_fabric
from agent_genesis.designer.architect import DesignerAgent
from agent_genesis.breeder.evolution import BreederAgent
from agent_genesis.deployer.orchestrator import DeployerAgent
from agent_genesis.finetune.loop import FineTuneLoop
from agent_genesis.skill_layer.openspace_integration import get_openspace_layer
from agent_genesis.plugins.hermes_genesis import (
    genesis_design, genesis_breed, genesis_deploy,
    genesis_finetune, genesis_memory, genesis_check_runtimes,
    genesis_list_champions, genesis_get_champion, genesis_load_golden,
    genesis_init_population, genesis_load_org, genesis_list_orgs,
    openspace_local_search, openspace_local_skill, openspace_local_record,
)


# =============================================================================
# TELEGRAM BOT
# =============================================================================

class GenesisTelegramBot:
    """Telegram bot for controlling Agent Genesis."""

    def __init__(self, token: str = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        
        self.memory = get_memory_fabric()
        self.designer = DesignerAgent()
        self.breeder = BreederAgent()
        self.deployer = DeployerAgent()
        self.finetune = FineTuneLoop()
        self.openspace = get_openspace_layer()
        
        self.allowed_users = set(
            map(int, os.getenv("TELEGRAM_ALLOWED_USERS", "").split(","))
        ) if os.getenv("TELEGRAM_ALLOWED_USERS") else None

    async def start(self):
        """Start the bot."""
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters

        app = Application.builder().token(self.token).build()

        # Commands
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("help", self.cmd_help))
        app.add_handler(CommandHandler("design", self.cmd_design))
        app.add_handler(CommandHandler("deploy", self.cmd_deploy))
        app.add_handler(CommandHandler("breed", self.cmd_breed))
        app.add_handler(CommandHandler("finetune", self.cmd_finetune))
        app.add_handler(CommandHandler("memory", self.cmd_memory))
        app.add_handler(CommandHandler("runtimes", self.cmd_runtimes))
        app.add_handler(CommandHandler("champions", self.cmd_champions))
        app.add_handler(CommandHandler("orgs", self.cmd_orgs))
        app.add_handler(CommandHandler("skill", self.cmd_skill))
        app.add_handler(CommandHandler("status", self.cmd_status))
        
        # Handle text messages as design requests
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))

        print("🤖 Agent Genesis Telegram Bot started")
        await app.run_polling()

    def _check_auth(self, update) -> bool:
        if self.allowed_users is None:
            return True
        user_id = update.effective_user.id
        return user_id in self.allowed_users

    async def cmd_start(self, update, context):
        if not self._check_auth(update):
            return
        await update.message.reply_text(
            "🧬 *Agent Genesis* — Self-evolving agent organizations\n\n"
            "Commands:\n"
            "/design <task> — Design agent organization\n"
            "/deploy <org_id> — Deploy organization\n"
            "/breed <role> — Evolve agent genomes\n"
            "/finetune — Run nightly fine-tune\n"
            "/memory [query] — Search memory\n"
            "/runtimes — Check runtime availability\n"
            "/champions — List champion genomes\n"
            "/orgs — List saved organizations\n"
            "/skill <name> — Get local skill\n"
            "/status — System status\n\n"
            "Or just send a task description to design.",
            parse_mode="Markdown"
        )

    async def cmd_help(self, update, context):
        await self.cmd_start(update, context)

    async def cmd_design(self, update, context):
        if not self._check_auth(update):
            return
        
        task = " ".join(context.args)
        if not task:
            await update.message.reply_text("Usage: /design <task description>")
            return

        await update.message.reply_text(f"🧠 Designing organization for: `{task}`", parse_mode="Markdown")
        
        try:
            result = await genesis_design(task)
            spec = result.get("spec", {})
            agents = spec.get("agents", [])
            
            msg = f"✅ *Designed:* `{spec.get('name', 'org')}`\n"
            msg += f"📋 *Agents:* {len(agents)}\n"
            for a in agents:
                msg += f"  • {a['id']}: {a['role']} on {a['runtime']} ({a['model']})\n"
            msg += f"\n🆔 Org ID: `{spec.get('id', 'unknown')}`"
            
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def cmd_deploy(self, update, context):
        if not self._check_auth(update):
            return
        
        org_id = " ".join(context.args).strip()
        if not org_id:
            await update.message.reply_text("Usage: /deploy <org_id>")
            return

        await update.message.reply_text(f"🚀 Deploying organization: `{org_id}`", parse_mode="Markdown")
        
        try:
            spec = self.memory.load_org(org_id)
            if not spec:
                await update.message.reply_text(f"❌ Org not found: {org_id}")
                return

            result = await genesis_deploy(spec)
            status = result.get("status", "unknown")
            agents = result.get("agents", {})
            
            msg = f"📦 *Deployment:* {status}\n"
            for aid, aresult in agents.items():
                ast = aresult.get("status", "?")
                msg += f"  {aid}: {ast}\n"
            
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def cmd_breed(self, update, context):
        if not self._check_auth(update):
            return
        
        args = context.args
        if not args:
            await update.message.reply_text("Usage: /breed <role> [generations]")
            return
        
        role = args[0]
        generations = int(args[1]) if len(args) > 1 else 50
        
        await update.message.reply_text(f"🧬 Evolving `{role}` for {generations} generations...", parse_mode="Markdown")
        
        try:
            result = await genesis_breed(role, generations=generations)
            if result.get("status") == "evolved":
                champ = result.get("champion", {})
                await update.message.reply_text(
                    f"✅ *Evolution complete*\n"
                    f"🏆 Champion: `{champ.get('agent_id', '?')}`\n"
                    f"📊 Fitness: {result.get('fitness', 0):.4f}\n"
                    f"🧬 Generation: {result.get('generation', '?')}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(f"❌ {result.get('message', 'Evolution failed')}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def cmd_finetune(self, update, context):
        if not self._check_auth(update):
            return
        
        await update.message.reply_text("🔄 Running nightly fine-tune loop...")
        
        try:
            result = await genesis_finetune(min_samples=10)
            status = result.get("status", "unknown")
            metrics = result.get("metrics", {})
            
            msg = f"🔬 *Fine-tune:* {status}\n"
            if metrics:
                msg += f"  Accuracy: {metrics.get('accuracy', 'N/A')}\n"
                msg += f"  Perplexity: {metrics.get('perplexity', 'N/A')}\n"
            if result.get("gguf_path"):
                msg += f"  GGUF: `{result['gguf_path']}`"
            
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def cmd_memory(self, update, context):
        if not self._check_auth(update):
            return
        
        query = " ".join(context.args)
        await update.message.reply_text(f"🔍 Searching memory for: `{query or 'all'}`", parse_mode="Markdown")
        
        try:
            result = await genesis_memory(query=query or None)
            
            msg = "💾 *Memory Results:*\n"
            for mtype, items in result.items():
                if items:
                    msg += f"\n  *{mtype}:* {len(items)} items\n"
                    for item in items[:3]:
                        text = item.get("content") or item.get("fact") or item.get("skill_name") or str(item)[:80]
                        msg += f"    • {text[:80]}...\n"
            
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def cmd_runtimes(self, update, context):
        if not self._check_auth(update):
            return
        
        await update.message.reply_text("🔍 Checking runtimes...")
        
        try:
            result = await genesis_check_runtimes()
            msg = "⚙️ *Runtime Status:*\n"
            for rt, ok in result.items():
                msg += f"  {rt}: {'✅' if ok else '❌'}\n"
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def cmd_champions(self, update, context):
        if not self._check_auth(update):
            return
        
        try:
            result = await genesis_list_champions()
            champs = result.get("champions", {})
            
            if not champs:
                await update.message.reply_text("No champions yet. Run `/breed <role>` first.")
                return
            
            msg = "🏆 *Champion Genomes:*\n"
            for role, champ in champs.items():
                msg += f"  *{role}:* `{champ.get('agent_id', '?')}` (gen {champ.get('generation', '?')}, fit {champ.get('fitness', 0):.3f})\n"
            
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def cmd_orgs(self, update, context):
        if not self._check_auth(update):
            return
        
        try:
            result = await genesis_list_orgs()
            orgs = result.get("orgs", [])
            
            if not orgs:
                await update.message.reply_text("No organizations saved. Use `/design` first.")
                return
            
            msg = "📁 *Saved Organizations:*\n"
            for org in orgs[:10]:
                msg += f"  • `{org['id']}` — {org.get('created_at', 'unknown')}\n"
            
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def cmd_skill(self, update, context):
        if not self._check_auth(update):
            return
        
        skill_name = " ".join(context.args)
        if not skill_name:
            await update.message.reply_text("Usage: /skill <skill_name>")
            return
        
        try:
            result = await openspace_local_skill(skill_name)
            skill = result.get("skill")
            
            if skill:
                steps = skill.get("steps", [])
                msg = f"🔧 *Skill:* `{skill['skill_name']}`\n"
                msg += f"  Description: {skill.get('description', 'N/A')}\n"
                msg += f"  Success Rate: {skill.get('success_rate', 0):.2%}\n"
                msg += f"  Executions: {skill.get('execution_count', 0)}\n"
                msg += f"  Steps: {len(steps)}\n"
            else:
                msg = f"❌ Skill not found: {skill_name}"
            
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def cmd_status(self, update, context):
        if not self._check_auth(update):
            return
        
        try:
            stats = self.memory.stats()
            runtimes = await genesis_check_runtimes()
            champs = await genesis_list_champions()
            
            msg = "📊 *Agent Genesis Status*\n\n"
            msg += f"💾 Memory: {stats.get('episodic', 0)} episodic, {stats.get('semantic', 0)} semantic, {stats.get('procedural', 0)} skills, {stats.get('orgs', 0)} orgs\n"
            msg += f"⚙️ Runtimes: " + ", ".join([f"{k}={'✅' if v else '❌'}" for k,v in runtimes.items()]) + "\n"
            msg += f"🏆 Champions: {len(champs.get('champions', {}))}\n"
            
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def handle_text(self, update, context):
        """Handle plain text as design request."""
        if not self._check_auth(update):
            return
        
        text = update.message.text
        if len(text) < 10:
            await update.message.reply_text("Task too short. Use /design for longer descriptions.")
            return
        
        # Treat as design request
        await self.cmd_design(update, context)


# =============================================================================
# CLI
# =============================================================================

class GenesisCLI:
    """Command-line interface for Agent Genesis."""

    def __init__(self):
        self.memory = get_memory_fabric()
        self.designer = DesignerAgent()
        self.breeder = BreederAgent()
        self.deployer = DeployerAgent()
        self.finetune = FineTuneLoop()
        self.openspace = get_openspace_layer()

    async def run(self, args: list):
        if not args:
            self.print_help()
            return

        cmd = args[0]
        cmd_args = args[1:]

        try:
            if cmd == "design":
                task = " ".join(cmd_args)
                if not task:
                    print("Usage: genesis design <task>")
                    return
                result = await genesis_design(task)
                spec = result.get("spec", {})
                print(json.dumps(spec, indent=2, ensure_ascii=False))
                
            elif cmd == "deploy":
                org_id = " ".join(cmd_args)
                if not org_id:
                    print("Usage: genesis deploy <org_id>")
                    return
                spec = self.memory.load_org(org_id)
                if not spec:
                    print(f"Org not found: {org_id}")
                    return
                result = await genesis_deploy(spec)
                print(json.dumps(result, indent=2))
                
            elif cmd == "breed":
                if not cmd_args:
                    print("Usage: genesis breed <role> [generations]")
                    return
                role = cmd_args[0]
                generations = int(cmd_args[1]) if len(cmd_args) > 1 else 50
                result = await genesis_breed(role, generations=generations)
                print(json.dumps(result, indent=2))
                
            elif cmd == "finetune":
                result = await genesis_finetune(min_samples=10)
                print(json.dumps(result, indent=2))
                
            elif cmd == "memory":
                query = " ".join(cmd_args) if cmd_args else None
                result = await genesis_memory(query=query)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
            elif cmd == "runtimes":
                result = await genesis_check_runtimes()
                print(json.dumps(result, indent=2))
                
            elif cmd == "champions":
                result = await genesis_list_champions()
                print(json.dumps(result, indent=2))
                
            elif cmd == "orgs":
                result = await genesis_list_orgs()
                print(json.dumps(result, indent=2))
                
            elif cmd == "skill":
                if not cmd_args:
                    print("Usage: genesis skill <skill_name>")
                    return
                skill_name = " ".join(cmd_args)
                result = await openspace_local_skill(skill_name)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
            elif cmd == "status":
                stats = self.memory.stats()
                runtimes = await genesis_check_runtimes()
                champs = await genesis_list_champions()
                print(f"Memory: {stats}")
                print(f"Runtimes: {runtimes}")
                print(f"Champions: {len(champs.get('champions', {}))}")
                
            elif cmd == "init-pop":
                if len(cmd_args) < 2:
                    print("Usage: genesis init-pop <role> <base_prompt>")
                    return
                role = cmd_args[0]
                prompt = " ".join(cmd_args[1:])
                result = await genesis_init_population(role, prompt)
                print(json.dumps(result, indent=2))
                
            elif cmd == "load-golden":
                if len(cmd_args) < 2:
                    print("Usage: genesis load-golden <role> <test_cases_json_file>")
                    return
                role = cmd_args[0]
                file_path = cmd_args[1]
                with open(file_path) as f:
                    test_cases = json.load(f)
                result = await genesis_load_golden(role, test_cases)
                print(json.dumps(result, indent=2))
                
            elif cmd == "search-skill":
                query = " ".join(cmd_args)
                if not query:
                    print("Usage: genesis search-skill <query>")
                    return
                result = await openspace_local_search(query)
                print(json.dumps(result, indent=2, ensure_ascii=False))
                
            else:
                print(f"Unknown command: {cmd}")
                self.print_help()
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    def print_help(self):
        print("""
🧬 Agent Genesis CLI

Commands:
  design <task>                    Design agent organization
  deploy <org_id>                  Deploy organization
  breed <role> [generations]       Evolve agent genomes
  finetune                         Run nightly fine-tune
  memory [query]                   Search memory
  runtimes                         Check runtime availability
  champions                        List champion genomes
  orgs                             List saved organizations
  skill <skill_name>               Get local skill
  status                           System status
  init-pop <role> <prompt>         Initialize population
  load-golden <role> <file.json>   Load golden test set
  search-skill <query>             Search local skills

Examples:
  genesis design "Monitor GeM tenders, parse PDFs, draft proposals"
  genesis deploy abc12345
  genesis breed scout 30
  genesis finetune
  genesis memory "GST compliance"
  genesis runtimes
  genesis champions
""")


def main():
    """Synchronous entry point for console script."""
    cli = GenesisCLI()
    asyncio.run(cli.run(sys.argv[1:]))


if __name__ == "__main__":
    main()
