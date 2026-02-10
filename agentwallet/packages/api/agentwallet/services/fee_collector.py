"""Fee Collector -- calculate and track platform fees per transaction."""

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)

FEE_BPS = {
    "free": 50,       # 0.5%
    "pro": 25,        # 0.25%
    "enterprise": 10, # 0.1%
}


class FeeCollector:
    def calculate_fee(self, amount_lamports: int, tier: str) -> int:
        """Calculate platform fee in lamports.

        Fee is deducted atomically in the same transaction.
        Minimum fee: 1000 lamports.
        """
        settings = get_settings()
        bps = FEE_BPS.get(tier, settings.fee_bps_free)
        fee = (amount_lamports * bps) // 10000
        minimum = settings.fee_minimum_lamports
        return max(fee, minimum) if amount_lamports > minimum else 0

    def get_tier_bps(self, tier: str) -> int:
        return FEE_BPS.get(tier, 50)
