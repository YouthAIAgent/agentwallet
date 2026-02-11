use anchor_lang::prelude::*;
use anchor_lang::system_program;

use crate::errors::AgentWalletError;
use crate::state::{AgentWallet, PlatformConfig};

/// Event emitted when a transfer is executed from an agent wallet.
#[event]
pub struct TransferExecuted {
    pub wallet: Pubkey,
    pub recipient: Pubkey,
    pub amount: u64,
    pub fee: u64,
    pub daily_spent_after: u64,
}

#[derive(Accounts)]
#[instruction(amount: u64)]
pub struct TransferWithLimit<'info> {
    /// The authority of the agent wallet (must be signer).
    #[account(mut)]
    pub authority: Signer<'info>,

    /// The agent wallet PDA; authority must match the signer.
    #[account(
        mut,
        has_one = authority,
        seeds = [b"agent_wallet", agent_wallet.org.as_ref(), agent_wallet.agent_id.as_bytes()],
        bump = agent_wallet.bump,
    )]
    pub agent_wallet: Account<'info, AgentWallet>,

    /// The platform config PDA (holds fee parameters).
    #[account(
        seeds = [b"platform_config"],
        bump = platform_config.bump,
    )]
    pub platform_config: Account<'info, PlatformConfig>,

    /// The wallet that receives platform fees.
    /// CHECK: Validated against the fee_wallet stored in platform_config.
    #[account(
        mut,
        constraint = fee_wallet.key() == platform_config.fee_wallet,
    )]
    pub fee_wallet: UncheckedAccount<'info>,

    /// The final recipient of the transfer (after fees).
    /// CHECK: Any valid account can be a recipient.
    #[account(mut)]
    pub recipient: UncheckedAccount<'info>,

    pub system_program: Program<'info, System>,
}

/// Execute a SOL transfer from the authority, subject to per-tx and daily limits.
///
/// # Fee Model
///
/// **The platform fee is deducted FROM the transfer `amount`, not charged on top.**
/// For example, if `amount` = 1 SOL and `fee_bps` = 50 (0.5%), the recipient
/// receives 0.995 SOL and the fee wallet receives 0.005 SOL. The authority's
/// total debit is exactly `amount` (1 SOL).
///
/// This means the `amount` parameter represents the total cost to the sender,
/// NOT the amount the recipient will receive. Clients should account for this
/// when displaying estimated transfer amounts to users.
///
/// # Errors
///
/// - `WalletInactive` — agent wallet has been deactivated
/// - `SpendingLimitExceeded` — `amount` exceeds per-transaction limit
/// - `DailyLimitExceeded` — cumulative daily spend would exceed daily limit
/// - `ArithmeticOverflow` — numeric overflow in fee or limit calculations
/// - `InvalidFeeCalculation` — fee calculation produced an invalid result
pub fn handler(ctx: Context<TransferWithLimit>, amount: u64) -> Result<()> {
    let wallet = &mut ctx.accounts.agent_wallet;
    let config = &ctx.accounts.platform_config;
    let clock = Clock::get()?;

    // --- Check wallet is active ---
    require!(wallet.is_active, AgentWalletError::WalletInactive);

    // --- Per-transaction limit ---
    require!(
        amount <= wallet.spending_limit_per_tx,
        AgentWalletError::SpendingLimitExceeded
    );

    // --- Daily limit (reset if new day) ---
    let current_day = clock.unix_timestamp / 86400;
    if current_day > wallet.last_reset_day {
        wallet.daily_spent = 0;
        wallet.last_reset_day = current_day;
    }

    let new_daily_spent = wallet
        .daily_spent
        .checked_add(amount)
        .ok_or(AgentWalletError::ArithmeticOverflow)?;
    require!(
        new_daily_spent <= wallet.daily_limit,
        AgentWalletError::DailyLimitExceeded
    );
    wallet.daily_spent = new_daily_spent;

    // --- Fee calculation (fee is deducted FROM amount, not added on top) ---
    let fee = (amount as u128)
        .checked_mul(config.fee_bps as u128)
        .ok_or(AgentWalletError::ArithmeticOverflow)?
        .checked_div(10_000u128)
        .ok_or(AgentWalletError::InvalidFeeCalculation)? as u64;

    let transfer_amount = amount
        .checked_sub(fee)
        .ok_or(AgentWalletError::ArithmeticOverflow)?;

    // --- Transfer fee to fee_wallet ---
    if fee > 0 {
        system_program::transfer(
            CpiContext::new(
                ctx.accounts.system_program.to_account_info(),
                system_program::Transfer {
                    from: ctx.accounts.authority.to_account_info(),
                    to: ctx.accounts.fee_wallet.to_account_info(),
                },
            ),
            fee,
        )?;
    }

    // --- Transfer remainder to recipient ---
    if transfer_amount > 0 {
        system_program::transfer(
            CpiContext::new(
                ctx.accounts.system_program.to_account_info(),
                system_program::Transfer {
                    from: ctx.accounts.authority.to_account_info(),
                    to: ctx.accounts.recipient.to_account_info(),
                },
            ),
            transfer_amount,
        )?;
    }

    emit!(TransferExecuted {
        wallet: wallet.key(),
        recipient: ctx.accounts.recipient.key(),
        amount,
        fee,
        daily_spent_after: wallet.daily_spent,
    });

    Ok(())
}
