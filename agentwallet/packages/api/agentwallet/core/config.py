"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://agentwallet:agentwallet@localhost:5432/agentwallet"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Solana
    solana_rpc_url: str = "https://api.devnet.solana.com"
    solana_network: str = "devnet"

    # Platform wallet (receives fees)
    platform_wallet_address: str = ""

    # Encryption for private keys at rest
    encryption_key: str = ""

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:5173,https://agentwallet.fun,https://youthaiagent.github.io"

    # Environment
    environment: str = "development"

    # Stripe billing
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # Rate limits (requests per minute)
    rate_limit_default: int = 60

    # AWS KMS (production key encryption)
    aws_kms_key_id: str = ""
    aws_region: str = "us-east-1"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Fee tiers (basis points)
    fee_bps_free: int = 50  # 0.5%
    fee_bps_pro: int = 25  # 0.25%
    fee_bps_enterprise: int = 10  # 0.1%
    fee_minimum_lamports: int = 1000

    # Tier limits
    tier_free_agents: int = 3
    tier_free_wallets: int = 5
    tier_free_tx_monthly: int = 1000
    tier_free_policies: int = 3
    tier_free_rate_limit: int = 60
    tier_free_analytics_days: int = 7

    tier_pro_agents: int = 25
    tier_pro_wallets: int = 50
    tier_pro_tx_monthly: int = 50000
    tier_pro_rate_limit: int = 600
    tier_pro_analytics_days: int = 90

    tier_enterprise_rate_limit: int = 6000
    tier_enterprise_analytics_days: int = 365

    # EVM / ERC-8004
    evm_rpc_url: str = "https://mainnet.base.org"
    evm_chain_id: int = 8453
    erc8004_identity_address: str = "0x8004A169FB4a3325136EB29fA0ceB6D2e539a432"
    erc8004_reputation_address: str = "0x8004BAa17C55a88189AE136b182e5fdA19dE9b63"
    evm_platform_private_key: str = ""  # Platform's EVM key for signing identity registrations

    # RPC timeouts
    rpc_timeout: int = 15
    rpc_confirm_max_polls: int = 20
    rpc_confirm_poll_interval: float = 2.0

    @field_validator("jwt_secret_key")
    @classmethod
    def jwt_secret_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "jwt_secret_key must be at least 32 characters long. "
                "The default 'change-me-in-production' value is not secure. "
                "Generate a strong secret with: python -c 'import secrets; print(secrets.token_urlsafe(48))'"
            )
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
