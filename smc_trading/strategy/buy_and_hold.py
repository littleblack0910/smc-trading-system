from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    ticker: str
    start: pd.Timestamp
    end: pd.Timestamp
    starting_cash: float
    ending_value: float
    total_return_pct: float
    max_drawdown_pct: float
    n_periods: int
    equity_curve: pd.DataFrame


def _max_drawdown(equity_curve: pd.Series) -> float:
    """Compute max drawdown (%) for an equity curve.

    This is a simple, standard metric that's cheap to compute and
    sufficient for an initial Week 1 backtest.
    """

    cumulative_max = equity_curve.cummax()
    drawdowns = (equity_curve - cumulative_max) / cumulative_max
    return float(drawdowns.min() * 100.0)


def run_buy_and_hold_backtest(
    prices: pd.Series,
    *,
    ticker: str,
    initial_cash: float = 10_000.0,
) -> BacktestResult:
    """Run a minimal buy-and-hold backtest.

    Strategy:
    - At the first bar, invest all cash into the asset at the close price.
    - Hold until the final bar; never rebalance.

    This gives us a deterministic, easy-to-validate baseline that
    exercises the ingestion + orchestration plumbing.
    """

    if prices.empty:
        raise ValueError("Price series is empty; nothing to backtest.")

    prices = prices.sort_index()

    first_price = float(prices.iloc[0])
    n_shares = initial_cash / first_price
    position = pd.Series(n_shares, index=prices.index)
    cash = pd.Series(0.0, index=prices.index)
    equity = position * prices + cash

    ending_value = float(equity.iloc[-1])
    total_return_pct = (ending_value / initial_cash - 1.0) * 100.0
    max_dd_pct = _max_drawdown(equity)

    equity_curve = pd.DataFrame(
        {
            "date": prices.index,
            "price": prices.astype(float).values,
            "position": position.astype(float).values,
            "cash": cash.astype(float).values,
            "equity": equity.astype(float).values,
        }
    )

    return BacktestResult(
        ticker=ticker,
        start=prices.index[0],
        end=prices.index[-1],
        starting_cash=initial_cash,
        ending_value=ending_value,
        total_return_pct=total_return_pct,
        max_drawdown_pct=max_dd_pct,
        n_periods=int(len(prices)),
        equity_curve=equity_curve.reset_index(drop=True),
    )
