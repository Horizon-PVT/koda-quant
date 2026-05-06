from risk_manager import PortfolioRiskManager


def test_risk_manager_blocks_consecutive_losses():
    manager = PortfolioRiskManager(max_consecutive_losses=3)
    decision = manager.evaluate([1, -1, -2, -3], equity=1000, current_drawdown=10)
    assert decision.allow is False
    assert decision.reason == "CONSECUTIVE_LOSSES"


def test_risk_manager_approves_normal_case():
    manager = PortfolioRiskManager()
    decision = manager.evaluate([1, -1, 2, -0.5], equity=1000, current_drawdown=5)
    assert decision.allow is True
