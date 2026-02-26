from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from smc_trading.config.settings import backtest_config_from_args
from smc_trading.ingestion.csv_loader import load_price_csv
from smc_trading.strategy.buy_and_hold import run_buy_and_hold_backtest


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smc-trading",
        description="SMC Trading System CLI",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    backtest = subparsers.add_parser(
        "backtest", help="Run a simple CSV-based buy-and-hold backtest."
    )
    backtest.add_argument("--ticker", required=True, help="Ticker symbol, e.g., AAPL")
    backtest.add_argument(
        "--csv-path",
        type=Path,
        required=True,
        help="Path to a CSV file with at least 'date' and 'close' columns.",
    )
    backtest.add_argument(
        "--initial-cash",
        type=float,
        default=10_000.0,
        help="Starting cash for the backtest (default: 10,000)",
    )
    backtest.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Optional start date (YYYY-MM-DD) to slice the CSV",
    )
    backtest.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="Optional end date (YYYY-MM-DD) to slice the CSV",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "backtest":
        cfg = backtest_config_from_args(args)
        df = load_price_csv(cfg.csv_path)

        prices = df["close"]
        if cfg.start_date:
            prices = prices[prices.index >= pd.to_datetime(cfg.start_date)]
        if cfg.end_date:
            prices = prices[prices.index <= pd.to_datetime(cfg.end_date)]

        if prices.empty:
            raise SystemExit(
                "No price data available for the requested date window. "
                "Check your CSV and the --start-date/--end-date arguments."
            )

        result = run_buy_and_hold_backtest(
            prices,
            ticker=cfg.ticker,
            initial_cash=cfg.initial_cash,
        )

        print("=== Buy & Hold Backtest ===")
        print(f"Ticker          : {result.ticker}")
        print(f"Period          : {result.start.date()} -> {result.end.date()}")
        print(f"Bars            : {result.n_periods}")
        print("")
        print(f"Starting cash   : ${result.starting_cash:,.2f}")
        print(f"Ending value    : ${result.ending_value:,.2f}")
        print(f"Total return    : {result.total_return_pct:6.2f}%")
        print(f"Max drawdown    : {result.max_drawdown_pct:6.2f}%")

        return 0

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
