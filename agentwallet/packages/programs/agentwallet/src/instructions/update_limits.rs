use anchor_lang::prelude::*;

use crate::state::AgentWallet;

/// Event emitted when agent wallet limits are updated.
#[event]
pub struct LimitsUpdated {
    pub wallet: Pubkey,
    pub spending_limit_per_tx: u64,
    pub daily_limit: u64,
    pub is_active: bool,
}

#[derive(Accounts)]
pub struct UpdateLimits<'info> {
    /// The authority of the agent wallet (must be signer).
    pub authority: Signer<'info>,

    /// The agent wallet PDA to update; authority must match.
    #[account(
        mut,
        has_one = authority,
        seeds = [b"agent_wallet", agent_wallet.org.as_ref(), agent_wallet.agent_id.as_bytes()],
        bump = agent_wallet.bump,
    )]
    pub agent_wallet: Account<'info, AgentWallet>,
}

/// Update the spending limits and active status of an agent wallet.
/// Only the wallet authority can invoke this instruction.
pub fn handler(
    ctx: Context<UpdateLimits>,
    spending_limit_per_tx: u64,
    daily_limit: u64,
    is_active: bool,
) -> Result<()> {
    let wallet = &mut ctx.accounts.agent_wallet;

    wallet.spending_limit_per_tx = spending_limit_per_tx;
    wallet.daily_limit = daily_limit;
    wallet.is_active = is_active;

    emit!(LimitsUpdated {
        wallet: wallet.key(),
        spending_limit_per_tx,
        daily_limit,
        is_active,
    });

    Ok(())
}
