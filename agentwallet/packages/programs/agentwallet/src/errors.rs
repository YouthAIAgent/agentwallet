use anchor_lang::prelude::*;

#[error_code]
pub enum AgentWalletError {
    #[msg("Transaction amount exceeds the per-transaction spending limit")]
    SpendingLimitExceeded,

    #[msg("Transaction would exceed the daily spending limit")]
    DailyLimitExceeded,

    #[msg("Agent wallet is inactive and cannot process transactions")]
    WalletInactive,

    #[msg("Escrow account has already been funded")]
    EscrowAlreadyFunded,

    #[msg("Escrow account has not been funded yet")]
    EscrowNotFunded,

    #[msg("Escrow has expired and can only be refunded")]
    EscrowExpired,

    #[msg("Only the designated arbiter can perform this action")]
    UnauthorizedArbiter,

    #[msg("Escrow is in an invalid state for this operation")]
    InvalidEscrowState,

    #[msg("Arithmetic overflow occurred")]
    ArithmeticOverflow,

    #[msg("Fee calculation resulted in an invalid amount")]
    InvalidFeeCalculation,
}
