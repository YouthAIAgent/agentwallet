use anchor_lang::prelude::*;

pub mod errors;
pub mod instructions;
pub mod state;

use instructions::*;

declare_id!("AWPro1111111111111111111111111111111111111111");

#[program]
pub mod agentwallet {
    use super::*;

    /// Initialise a new agent wallet PDA with spending limits.
    pub fn create_agent_wallet(
        ctx: Context<CreateAgentWallet>,
        agent_id: String,
        spending_limit_per_tx: u64,
        daily_limit: u64,
    ) -> Result<()> {
        instructions::create_agent_wallet::handler(ctx, agent_id, spending_limit_per_tx, daily_limit)
    }

    /// Execute a SOL transfer, enforcing per-tx and daily limits and deducting a platform fee.
    pub fn transfer_with_limit(ctx: Context<TransferWithLimit>, amount: u64) -> Result<()> {
        instructions::transfer_with_limit::handler(ctx, amount)
    }

    /// Update spending limits and active status on an agent wallet (authority only).
    pub fn update_limits(
        ctx: Context<UpdateLimits>,
        spending_limit_per_tx: u64,
        daily_limit: u64,
        is_active: bool,
    ) -> Result<()> {
        instructions::update_limits::handler(ctx, spending_limit_per_tx, daily_limit, is_active)
    }

    /// Create a new escrow, initialise its PDA, and fund it with SOL.
    pub fn create_escrow(
        ctx: Context<CreateEscrow>,
        escrow_id: String,
        amount: u64,
        expiry_timestamp: i64,
    ) -> Result<()> {
        instructions::escrow::handler_create_escrow(ctx, escrow_id, amount, expiry_timestamp)
    }

    /// Release escrowed SOL to the recipient (funder or arbiter).
    pub fn release_escrow(ctx: Context<ReleaseEscrow>) -> Result<()> {
        instructions::escrow::handler_release_escrow(ctx)
    }

    /// Refund escrowed SOL to the funder (arbiter or anyone after expiry).
    pub fn refund_escrow(ctx: Context<RefundEscrow>) -> Result<()> {
        instructions::escrow::handler_refund_escrow(ctx)
    }

    /// Initialise or update the platform configuration (admin only).
    /// This is a bootstrap instruction for setting up fee parameters.
    pub fn initialize_platform_config(
        ctx: Context<InitializePlatformConfig>,
        fee_bps: u16,
    ) -> Result<()> {
        let config = &mut ctx.accounts.platform_config;
        config.authority = ctx.accounts.authority.key();
        config.fee_wallet = ctx.accounts.fee_wallet.key();
        config.fee_bps = fee_bps;
        config.bump = ctx.bumps.platform_config;
        Ok(())
    }
}

// ---------------------------------------------------------------------------
// PlatformConfig bootstrap instruction accounts
// ---------------------------------------------------------------------------

#[derive(Accounts)]
pub struct InitializePlatformConfig<'info> {
    /// The platform administrator.
    #[account(mut)]
    pub authority: Signer<'info>,

    /// The wallet that will receive platform fees.
    /// CHECK: Any valid pubkey; stored as data.
    pub fee_wallet: UncheckedAccount<'info>,

    /// The platform config PDA.
    #[account(
        init,
        payer = authority,
        space = 8 + state::PlatformConfig::INIT_SPACE,
        seeds = [b"platform_config"],
        bump,
    )]
    pub platform_config: Account<'info, state::PlatformConfig>,

    pub system_program: Program<'info, System>,
}
