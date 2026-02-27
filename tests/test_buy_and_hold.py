import pandas as pd
import pytest

from smc_trading.strategy.buy_and_hold import (
    BacktestResult,
    _max_drawdown,
    run_buy_and_hold_backtest,
)


def test_max_drawdown_basic() -> None:
    # Equity goes 100 -> 120 -> 90 -> 130
    equity = pd.Series([100, 120, 90, 130])
    dd = _max_drawdown(equity)
    # Max drawdown occurs from 120 down to 90: -25%
    assert pytest.approx(dd, rel=1e-6) == -25.0


def test_run_buy_and_hold_backtest_happy_path() -> None:
    idx = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.Series([100.0, 110.0, 120.0], index=idx)

    result = run_buy_and_hold_backtest(prices, ticker="AAPL", initial_cash=10_000.0)

    assert isinstance(result, BacktestResult)
    assert result.ticker == "AAPL"
    assert result.start == idx[0]
    assert result.end == idx[-1]
    assert result.starting_cash == 10_000.0
    # Buy-and-hold: ending value should scale with last price / first price
    expected_ending_value = 10_000.0 * (120.0 / 100.0)
    assert pytest.approx(result.ending_value, rel=1e-6) == expected_ending_value
    assert result.n_periods == 3
    assert list(result.equity_curve.columns) == [
        "date",
        "price",
        "position",
        "cash",
        "equity",
    ]
    assert len(result.equity_curve) == 3
    assert pytest.approx(result.equity_curve.loc[0, "equity"], rel=1e-6) == 10_000.0


def test_run_buy_and_hold_backtest_empty_series() -> None:
    prices = pd.Series(dtype=float)

    with pytest.raises(ValueError):
        run_buy_and_hold_backtest(prices, ticker="AAPL")
