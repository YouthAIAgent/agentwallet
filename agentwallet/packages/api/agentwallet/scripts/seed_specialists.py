"""Seed the 10 Agency Agents specialists as public marketplace agents.

Registers the specialist roster (from the installed msitarzewski/agency-agents
collection) as public agents under a dedicated "Marketplace Specialists" org,
each with a default wallet, so any organization's posted tasks can auto-assign
the best specialist via TaskService.auto_assign's public fallback.

Idempotent: re-running updates existing specialists by name instead of
duplicating them.

Usage:
    python -m agentwallet.scripts.seed_specialists
"""

import asyncio

from sqlalchemy import select

from ..core.database import Base, get_engine, get_session_factory
from ..core.logging import get_logger
from ..models.agent import Agent
from ..models.organization import Organization
from ..services.agent_registry import AgentRegistry
from ..services.wallet_manager import WalletManager

logger = get_logger(__name__)

SPECIALISTS_ORG = "Marketplace Specialists"
SPECIALISTS_ORG_EMAIL = "specialists@agentwallet.fun"

# 10 specialists pulled from the installed agency-agents roster. Each entry:
#   slug         -> stable capability key (used for task.capability matching)
#   name         -> display name
#   category     -> task category this specialist best serves
#   capabilities -> additional capability aliases so tasks match broadly
#   description  -> from the source agent definition
SPECIALISTS = [
    {
        "slug": "security-architect",
        "name": "Security Architect",
        "category": "security",
        "capabilities": ["security", "audit", "threat-modeling", "architecture"],
        "description": (
            "Expert security architect specializing in threat modeling, "
            "secure-by-design architecture, trust-boundary analysis, defense-in-depth, "
            "and risk-based security reviews across web, API, cloud-native, and "
            "distributed systems."
        ),
    },
    {
        "slug": "sales-engineer",
        "name": "Sales Engineer",
        "category": "sales",
        "capabilities": ["sales", "presales", "demo", "poc", "battlecards"],
        "description": (
            "Senior pre-sales engineer specializing in technical discovery, demo "
            "engineering, POC scoping, competitive battlecards, and bridging product "
            "capabilities to business outcomes."
        ),
    },
    {
        "slug": "product-manager",
        "name": "Product Manager",
        "category": "product",
        "capabilities": ["product", "roadmap", "strategy", "go-to-market", "planning"],
        "description": (
            "Holistic product leader who owns the full product lifecycle from "
            "discovery and strategy through roadmap, stakeholder alignment, "
            "go-to-market, and outcome measurement."
        ),
    },
    {
        "slug": "data-engineer",
        "name": "Data Engineer",
        "category": "data",
        "capabilities": ["data", "etl", "pipeline", "analytics", "database"],
        "description": (
            "Expert data engineer specializing in building reliable data pipelines, "
            "lakehouse architectures, and scalable data infrastructure, turning raw "
            "data into trusted, analytics-ready assets."
        ),
    },
    {
        "slug": "ai-engineer",
        "name": "AI Engineer",
        "category": "coding",
        "capabilities": ["coding", "ai", "ml", "software", "engineering"],
        "description": (
            "Expert AI/ML engineer specializing in machine learning model development, "
            "deployment, and integration into production systems with emphasis on "
            "practical, scalable solutions."
        ),
    },
    {
        "slug": "social-media-strategist",
        "name": "Social Media Strategist",
        "category": "social",
        "capabilities": ["social", "marketing", "content", "community"],
        "description": (
            "Expert social media strategist for LinkedIn, Twitter, and professional "
            "platforms. Creates cross-platform campaigns, builds communities, and "
            "develops thought leadership strategies."
        ),
    },
    {
        "slug": "content-creator",
        "name": "Content Creator",
        "category": "writing",
        "capabilities": ["writing", "content", "copywriting", "storytelling"],
        "description": (
            "Expert content strategist and creator for multi-platform campaigns. "
            "Develops editorial calendars, creates compelling copy, and optimizes "
            "content for engagement across all digital channels."
        ),
    },
    {
        "slug": "support-responder",
        "name": "Support Responder",
        "category": "support",
        "capabilities": ["support", "customer-service", "troubleshooting", "help"],
        "description": (
            "Expert customer support specialist delivering exceptional customer "
            "service, issue resolution, and user experience optimization across "
            "multi-channel support."
        ),
    },
    {
        "slug": "financial-analyst",
        "name": "Financial Analyst",
        "category": "finance",
        "capabilities": ["finance", "modeling", "forecasting", "analysis", "investment"],
        "description": (
            "Expert financial analyst specializing in financial modeling, forecasting, "
            "scenario analysis, and data-driven decision support that drives strategic "
            "planning and investment decisions."
        ),
    },
    {
        "slug": "trend-researcher",
        "name": "Trend Researcher",
        "category": "research",
        "capabilities": ["research", "market-intelligence", "competitive-analysis", "insights"],
        "description": (
            "Expert market intelligence analyst specializing in identifying emerging "
            "trends, competitive analysis, and opportunity assessment that drives "
            "product strategy and innovation."
        ),
    },
]


async def seed() -> int:
    """Create/update the specialist org + agents. Returns count of agents ensured."""
    async with get_engine().begin() as conn:
        # Ensure schema exists (tests may run against a fresh DB)
        await conn.run_sync(Base.metadata.create_all)

    factory = get_session_factory()
    async with factory() as db:
        # 1) Find or create the specialists org
        org = (
            await db.execute(select(Organization).where(Organization.name == SPECIALISTS_ORG))
        ).scalar_one_or_none()
        if not org:
            org = Organization(name=SPECIALISTS_ORG, email=SPECIALISTS_ORG_EMAIL)
            db.add(org)
            await db.flush()
            logger.info("specialists_org_created", org_id=str(org.id))

        registry = AgentRegistry(db)
        wallet_mgr = WalletManager(db)

        count = 0
        for spec in SPECIALISTS:
            # Upsert by name within the specialists org
            agent = (
                await db.execute(
                    select(Agent).where(
                        Agent.org_id == org.id,
                        Agent.name == spec["name"],
                    )
                )
            ).scalar_one_or_none()

            capabilities = [spec["slug"], spec["category"]] + spec["capabilities"]
            if not agent:
                agent = await registry.create_agent(
                    org_id=org.id,
                    org_tier="enterprise",
                    name=spec["name"],
                    description=spec["description"],
                    capabilities=capabilities,
                    is_public=True,
                    metadata={"source": "agency-agents", "slug": spec["slug"], "category": spec["category"]},
                )
                logger.info("specialist_created", name=spec["name"])
            else:
                agent.description = spec["description"]
                agent.capabilities = capabilities
                agent.is_public = True
                agent.status = "active"
                await db.flush()
                logger.info("specialist_updated", name=spec["name"])

            # 2) Ensure a default wallet so the agent can receive escrow payouts
            if not agent.default_wallet_id:
                wallet = await wallet_mgr.create_wallet(
                    org_id=org.id,
                    org_tier="enterprise",
                    agent_id=agent.id,
                    wallet_type="agent",
                    label=f"{spec['name']}-wallet",
                )
                agent.default_wallet_id = wallet.id
                await db.flush()
                logger.info("specialist_wallet_created", name=spec["name"], wallet_id=str(wallet.id))

            count += 1

        await db.commit()
        return count


def main() -> None:
    count = asyncio.run(seed())
    print(f"Seeded {count} public specialist agents for the task marketplace.")


if __name__ == "__main__":
    main()
