use anchor_lang::prelude::*;

/// Agent wallet PDA that holds spending policy for a given org + agent pair.
/// Seeds: ["agent_wallet", org_pubkey, agent_id]
#[account]
#[derive(InitSpace)]
pub struct AgentWallet {
    /// The authority that can update limits and deactivate the wallet.
    pub authority: Pubkey,

    /// The organisation this agent wallet belongs to.
    pub org: Pubkey,

    /// Unique identifier for the agent within the organisation.
    #[max_len(64)]
    pub agent_id: String,

    /// Maximum lamports allowed in a single transaction.
    pub spending_limit_per_tx: u64,

    /// Maximum lamports allowed to be spent within a single calendar day (UTC).
    pub daily_limit: u64,

    /// Lamports already spent during the current calendar day.
    pub daily_spent: u64,

    /// The day number (unix_timestamp / 86400) of the last reset.
    pub last_reset_day: i64,

    /// Whether this wallet is currently active and allowed to transact.
    pub is_active: bool,

    /// PDA bump seed.
    pub bump: u8,
}

/// Escrow account PDA that holds SOL in custody until release or refund.
/// Seeds: ["escrow", escrow_id]
#[account]
#[derive(InitSpace)]
pub struct EscrowAccount {
    /// The party that funded the escrow.
    pub funder: Pubkey,

    /// The intended recipient of the escrowed funds.
    pub recipient: Pubkey,

    /// A neutral third-party that can release or trigger a refund.
    pub arbiter: Pubkey,

    /// The amount of lamports held in escrow.
    pub amount: u64,

    /// Whether the escrow has been funded.
    pub is_funded: bool,

    /// Whether the funds have been released to the recipient.
    pub is_released: bool,

    /// Whether the funds have been refunded to the funder.
    pub is_refunded: bool,

    /// Unix timestamp after which the escrow can be refunded by anyone.
    pub expiry_timestamp: i64,

    /// Unique identifier for this escrow.
    #[max_len(64)]
    pub escrow_id: String,

    /// PDA bump seed.
    pub bump: u8,
}

/// Global platform configuration PDA.
/// Seeds: ["platform_config"]
#[account]
#[derive(InitSpace)]
pub struct PlatformConfig {
    /// The platform administrator that can update config.
    pub authority: Pubkey,

    /// Wallet that collects platform fees.
    pub fee_wallet: Pubkey,

    /// Fee in basis points (e.g. 50 = 0.5%).
    pub fee_bps: u16,

    /// PDA bump seed.
    pub bump: u8,
}
