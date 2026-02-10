use anchor_lang::prelude::*;
use anchor_lang::system_program;

use crate::errors::AgentWalletError;
use crate::state::EscrowAccount;

// ---------------------------------------------------------------------------
// Events
// ---------------------------------------------------------------------------

#[event]
pub struct EscrowCreated {
    pub escrow: Pubkey,
    pub escrow_id: String,
    pub funder: Pubkey,
    pub recipient: Pubkey,
    pub arbiter: Pubkey,
    pub amount: u64,
    pub expiry_timestamp: i64,
}

#[event]
pub struct EscrowReleased {
    pub escrow: Pubkey,
    pub recipient: Pubkey,
    pub amount: u64,
    pub released_by: Pubkey,
}

#[event]
pub struct EscrowRefunded {
    pub escrow: Pubkey,
    pub funder: Pubkey,
    pub amount: u64,
    pub refunded_by: Pubkey,
}

// ---------------------------------------------------------------------------
// CreateEscrow
// ---------------------------------------------------------------------------

#[derive(Accounts)]
#[instruction(escrow_id: String, amount: u64, expiry_timestamp: i64)]
pub struct CreateEscrow<'info> {
    /// The party funding the escrow.
    #[account(mut)]
    pub funder: Signer<'info>,

    /// The intended recipient of the escrowed funds.
    /// CHECK: Any valid pubkey; stored as data, no reads/writes.
    pub recipient: UncheckedAccount<'info>,

    /// The neutral arbiter who can release or trigger a refund.
    /// CHECK: Any valid pubkey; stored as data, no reads/writes.
    pub arbiter: UncheckedAccount<'info>,

    /// The escrow PDA to be initialised and funded.
    #[account(
        init,
        payer = funder,
        space = 8 + EscrowAccount::INIT_SPACE,
        seeds = [b"escrow", escrow_id.as_bytes()],
        bump,
    )]
    pub escrow_account: Account<'info, EscrowAccount>,

    pub system_program: Program<'info, System>,
}

/// Create a new escrow PDA and fund it with SOL in a single instruction.
pub fn handler_create_escrow(
    ctx: Context<CreateEscrow>,
    escrow_id: String,
    amount: u64,
    expiry_timestamp: i64,
) -> Result<()> {
    let escrow = &mut ctx.accounts.escrow_account;

    escrow.funder = ctx.accounts.funder.key();
    escrow.recipient = ctx.accounts.recipient.key();
    escrow.arbiter = ctx.accounts.arbiter.key();
    escrow.amount = amount;
    escrow.is_funded = true;
    escrow.is_released = false;
    escrow.is_refunded = false;
    escrow.expiry_timestamp = expiry_timestamp;
    escrow.escrow_id = escrow_id.clone();
    escrow.bump = ctx.bumps.escrow_account;

    // Transfer SOL from funder into the escrow PDA (the PDA's lamport balance
    // acts as the custodial vault).
    system_program::transfer(
        CpiContext::new(
            ctx.accounts.system_program.to_account_info(),
            system_program::Transfer {
                from: ctx.accounts.funder.to_account_info(),
                to: escrow.to_account_info(),
            },
        ),
        amount,
    )?;

    emit!(EscrowCreated {
        escrow: escrow.key(),
        escrow_id,
        funder: ctx.accounts.funder.key(),
        recipient: ctx.accounts.recipient.key(),
        arbiter: ctx.accounts.arbiter.key(),
        amount,
        expiry_timestamp,
    });

    Ok(())
}

// ---------------------------------------------------------------------------
// ReleaseEscrow
// ---------------------------------------------------------------------------

#[derive(Accounts)]
pub struct ReleaseEscrow<'info> {
    /// The signer releasing the escrow (must be the funder or the arbiter).
    #[account(mut)]
    pub signer: Signer<'info>,

    /// The escrow PDA.
    #[account(
        mut,
        seeds = [b"escrow", escrow_account.escrow_id.as_bytes()],
        bump = escrow_account.bump,
        constraint = escrow_account.is_funded @ AgentWalletError::EscrowNotFunded,
        constraint = !escrow_account.is_released @ AgentWalletError::InvalidEscrowState,
        constraint = !escrow_account.is_refunded @ AgentWalletError::InvalidEscrowState,
    )]
    pub escrow_account: Account<'info, EscrowAccount>,

    /// The recipient who will receive the escrowed funds.
    /// CHECK: Validated against the recipient stored in escrow_account.
    #[account(
        mut,
        constraint = recipient.key() == escrow_account.recipient,
    )]
    pub recipient: UncheckedAccount<'info>,

    pub system_program: Program<'info, System>,
}

/// Release the escrowed SOL to the recipient.
/// Only the funder or the arbiter may release.
pub fn handler_release_escrow(ctx: Context<ReleaseEscrow>) -> Result<()> {
    let escrow = &mut ctx.accounts.escrow_account;
    let signer_key = ctx.accounts.signer.key();

    // Authorization: funder or arbiter only.
    require!(
        signer_key == escrow.funder || signer_key == escrow.arbiter,
        AgentWalletError::UnauthorizedArbiter
    );

    let amount = escrow.amount;

    // Transfer lamports out of the escrow PDA to the recipient.
    // Because the escrow PDA is owned by this program we can directly
    // manipulate lamports (no CPI needed for PDA-owned accounts).
    **escrow.to_account_info().try_borrow_mut_lamports()? -= amount;
    **ctx
        .accounts
        .recipient
        .to_account_info()
        .try_borrow_mut_lamports()? += amount;

    escrow.is_released = true;

    emit!(EscrowReleased {
        escrow: escrow.key(),
        recipient: ctx.accounts.recipient.key(),
        amount,
        released_by: signer_key,
    });

    Ok(())
}

// ---------------------------------------------------------------------------
// RefundEscrow
// ---------------------------------------------------------------------------

#[derive(Accounts)]
pub struct RefundEscrow<'info> {
    /// The signer requesting the refund (arbiter, or anyone if expired).
    #[account(mut)]
    pub signer: Signer<'info>,

    /// The escrow PDA.
    #[account(
        mut,
        seeds = [b"escrow", escrow_account.escrow_id.as_bytes()],
        bump = escrow_account.bump,
        constraint = escrow_account.is_funded @ AgentWalletError::EscrowNotFunded,
        constraint = !escrow_account.is_released @ AgentWalletError::InvalidEscrowState,
        constraint = !escrow_account.is_refunded @ AgentWalletError::InvalidEscrowState,
    )]
    pub escrow_account: Account<'info, EscrowAccount>,

    /// The original funder who will receive the refund.
    /// CHECK: Validated against the funder stored in escrow_account.
    #[account(
        mut,
        constraint = funder.key() == escrow_account.funder,
    )]
    pub funder: UncheckedAccount<'info>,

    pub system_program: Program<'info, System>,
}

/// Refund the escrowed SOL back to the funder.
/// The arbiter may refund at any time. Anyone may refund after expiry.
pub fn handler_refund_escrow(ctx: Context<RefundEscrow>) -> Result<()> {
    let escrow = &mut ctx.accounts.escrow_account;
    let signer_key = ctx.accounts.signer.key();
    let clock = Clock::get()?;

    // Authorization: arbiter can refund any time; anyone can refund after expiry.
    let is_arbiter = signer_key == escrow.arbiter;
    let is_expired = clock.unix_timestamp >= escrow.expiry_timestamp;

    require!(
        is_arbiter || is_expired,
        AgentWalletError::UnauthorizedArbiter
    );

    let amount = escrow.amount;

    // Transfer lamports out of the escrow PDA back to the funder.
    **escrow.to_account_info().try_borrow_mut_lamports()? -= amount;
    **ctx
        .accounts
        .funder
        .to_account_info()
        .try_borrow_mut_lamports()? += amount;

    escrow.is_refunded = true;

    emit!(EscrowRefunded {
        escrow: escrow.key(),
        funder: ctx.accounts.funder.key(),
        amount,
        refunded_by: signer_key,
    });

    Ok(())
}
