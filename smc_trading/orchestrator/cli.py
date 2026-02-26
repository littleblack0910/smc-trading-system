from __future__ import annotations

import argparse
import json
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
    backtest.add_argument(
        "--output-path",
        type=Path,
        default=None,
        help="Optional path to write a JSON summary of the backtest result.",
    )

    backtest_batch = subparsers.add_parser(
        "backtest-batch",
        help="Run multiple buy-and-hold backtests described in a JSON manifest.",
    )
    backtest_batch.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to a JSON manifest with a top-level 'runs' list.",
    )

    return parser


def _load_manifest_runs(manifest_path: Path) -> list[dict]:
    if not manifest_path.exists():
        raise SystemExit(f"Manifest file not found: {manifest_path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse manifest JSON: {exc}") from exc

    if not isinstance(manifest, dict) or "runs" not in manifest:
        raise SystemExit("Manifest must be a JSON object with a 'runs' list.")

    runs = manifest["runs"]
    if not isinstance(runs, list):
        raise SystemExit("Manifest must be a JSON object with a 'runs' list.")

    return runs


def _handle_backtest_batch(manifest_path: Path) -> int:
    runs = _load_manifest_runs(manifest_path)

    for idx, run_cfg in enumerate(runs):
        if not isinstance(run_cfg, dict):
            raise SystemExit(
                f"Run {idx} must be a JSON object with 'ticker' and 'csv_path' keys."
            )

        missing = [key for key in ("ticker", "csv_path") if key not in run_cfg]
        if missing:
            raise SystemExit(
                f"Run {idx} is missing required key(s): {', '.join(missing)}"
            )

        ticker = run_cfg["ticker"]
        csv_path = Path(run_cfg["csv_path"])
        initial_cash = float(run_cfg.get("initial_cash", 10_000.0))

        try:
            df = load_price_csv(csv_path)
        except FileNotFoundError:
            raise SystemExit(f"CSV file not found for run {idx} ({ticker}): {csv_path}")
        except Exception as exc:  # pragma: no cover - defensive
            raise SystemExit(f"Failed to load CSV for run {idx} ({ticker}): {exc}") from exc

        try:
            result = run_buy_and_hold_backtest(
                df["close"],
                ticker=ticker,
                initial_cash=initial_cash,
            )
        except Exception as exc:  # pragma: no cover - defensive
            raise SystemExit(f"Backtest failed for run {idx} ({ticker}): {exc}") from exc

        print(
            f"{result.ticker} | {result.start.date()} -> {result.end.date()} | "
            f"total_return={result.total_return_pct:,.2f}% | "
            f"max_drawdown={result.max_drawdown_pct:,.2f}%"
        )

    return 0


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

        if cfg.output_path:
            cfg.output_path.parent.mkdir(parents=True, exist_ok=True)
            summary = {
                "ticker": result.ticker,
                "period_start": result.start.date().isoformat(),
                "period_end": result.end.date().isoformat(),
                "starting_cash": result.starting_cash,
                "ending_value": result.ending_value,
                "total_return_pct": result.total_return_pct,
                "max_drawdown_pct": result.max_drawdown_pct,
                "n_periods": result.n_periods,
            }
            with cfg.output_path.open("w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

        return 0

    if args.command == "backtest-batch":
        return _handle_backtest_batch(args.manifest)

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
