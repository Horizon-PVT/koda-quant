from dataclasses import dataclass
from typing import List


@dataclass
class RiskDecision:
    allow: bool
    reason: str


class PortfolioRiskManager:
    """Sprint B: veto layer before order execution."""

    def __init__(self, max_consecutive_losses: int = 3, max_drawdown_pct: float = 0.03):
        self.max_consecutive_losses = max_consecutive_losses
        self.max_drawdown_pct = max_drawdown_pct

    def evaluate(self, pnl_history: List[float], equity: float, current_drawdown: float) -> RiskDecision:
        if equity <= 0:
            return RiskDecision(False, "EQUITY_ZERO")
        if current_drawdown >= equity * self.max_drawdown_pct:
            return RiskDecision(False, "MAX_DRAWDOWN")

        consecutive_losses = 0
        for pnl in reversed(pnl_history[-10:]):
            if pnl < 0:
                consecutive_losses += 1
            else:
                break
        if consecutive_losses >= self.max_consecutive_losses:
            return RiskDecision(False, "CONSECUTIVE_LOSSES")

        return RiskDecision(True, "APPROVED")
