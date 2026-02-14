use anchor_lang::prelude::*;

use crate::errors::AgentWalletError;
use crate::state::AgentWallet;

/// Event emitted when a new agent wallet is created.
#[event]
pub struct AgentWalletCreated {
    pub authority: Pubkey,
    pub org: Pubkey,
    pub agent_id: String,
    pub spending_limit_per_tx: u64,
    pub daily_limit: u64,
    pub wallet: Pubkey,
}

#[derive(Accounts)]
#[instruction(agent_id: String, spending_limit_per_tx: u64, daily_limit: u64)]
pub struct CreateAgentWallet<'info> {
    /// The authority that will own and manage this agent wallet.
    #[account(mut)]
    pub authority: Signer<'info>,

    /// The organisation pubkey used as a seed (can be any pubkey representing the org).
    /// CHECK: This is only used as a PDA seed; no data is read or written.
    pub org: UncheckedAccount<'info>,

    /// The agent wallet PDA to be initialised.
    #[account(
        init,
        payer = authority,
        space = 8 + AgentWallet::INIT_SPACE,
        seeds = [b"agent_wallet", org.key().as_ref(), agent_id.as_bytes()],
        bump,
    )]
    pub agent_wallet: Account<'info, AgentWallet>,

    pub system_program: Program<'info, System>,
}

/// Creates a new agent wallet PDA with the specified spending limits.
pub fn handler(
    ctx: Context<CreateAgentWallet>,
    agent_id: String,
    spending_limit_per_tx: u64,
    daily_limit: u64,
) -> Result<()> {
    // Validate agent_id length (max 64 bytes as declared in state)
    require!(!agent_id.is_empty(), AgentWalletError::InvalidAmount);
    require!(agent_id.len() <= 64, AgentWalletError::InvalidAmount);

    let wallet = &mut ctx.accounts.agent_wallet;
    let clock = Clock::get()?;

    wallet.authority = ctx.accounts.authority.key();
    wallet.org = ctx.accounts.org.key();
    wallet.agent_id = agent_id.clone();
    wallet.spending_limit_per_tx = spending_limit_per_tx;
    wallet.daily_limit = daily_limit;
    wallet.daily_spent = 0;
    wallet.last_reset_day = clock.unix_timestamp / 86400;
    wallet.is_active = true;
    wallet.bump = ctx.bumps.agent_wallet;

    emit!(AgentWalletCreated {
        authority: ctx.accounts.authority.key(),
        org: ctx.accounts.org.key(),
        agent_id,
        spending_limit_per_tx,
        daily_limit,
        wallet: wallet.key(),
    });

    Ok(())
}
