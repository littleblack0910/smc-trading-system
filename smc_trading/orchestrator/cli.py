from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from smc_trading.config.settings import backtest_config_from_args
from smc_trading.ingestion.csv_loader import load_price_csv
from smc_trading.strategy.buy_and_hold import run_buy_and_hold_backtest, BacktestResult


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
    backtest_batch.add_argument(
        "--summary-path",
        type=Path,
        default=None,
        help="Optional path to write a JSON summary for the entire batch.",
    )

    return parser


def _result_to_dict(result: BacktestResult) -> dict:
    """Convert a BacktestResult into a serialisable dict."""

    return {
        "ticker": result.ticker,
        "period_start": result.start.date().isoformat(),
        "period_end": result.end.date().isoformat(),
        "starting_cash": result.starting_cash,
        "ending_value": result.ending_value,
        "total_return_pct": result.total_return_pct,
        "max_drawdown_pct": result.max_drawdown_pct,
        "n_periods": result.n_periods,
    }


def _load_manifest_runs(manifest_path: Path) -> tuple[list[dict], float]:
    if not manifest_path.exists():
        raise SystemExit(f"Manifest file not found: {manifest_path}")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to parse manifest JSON: {exc}") from exc

    if not isinstance(manifest, dict):
        raise SystemExit("Manifest must be a JSON object with a 'runs' list.")

    if "runs" not in manifest:
        raise SystemExit("Manifest must include a 'runs' list of backtests.")

    runs = manifest["runs"]
    if not isinstance(runs, list):
        raise SystemExit("Manifest 'runs' must be a list of backtest entries.")
    if len(runs) == 0:
        raise SystemExit("Manifest 'runs' must contain at least one backtest entry.")

    default_initial_cash = manifest.get("default_initial_cash", 10_000.0)
    try:
        default_initial_cash = float(default_initial_cash)
    except (TypeError, ValueError):
        raise SystemExit("Manifest field 'default_initial_cash' must be a number if provided.")

    return runs, default_initial_cash


def _validate_run_config(
    run_cfg: object, idx: int, default_initial_cash: float
) -> tuple[str, Path, float, str | None, str | None]:
    """Validate and normalise a single run configuration from the manifest.

    This keeps error messages user-friendly and ensures we only proceed with
    well-formed inputs while maintaining backwards compatibility.
    """

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
    if not isinstance(ticker, str):
        raise SystemExit(f"Run {idx} field 'ticker' must be a string.")

    csv_path_raw = run_cfg["csv_path"]
    if not isinstance(csv_path_raw, str):
        raise SystemExit(f"Run {idx} field 'csv_path' must be a string path.")
    csv_path = Path(csv_path_raw)

    initial_cash_raw = run_cfg.get("initial_cash", default_initial_cash)
    try:
        initial_cash = float(initial_cash_raw)
    except (TypeError, ValueError):
        raise SystemExit(
            f"Run {idx} field 'initial_cash' must be a number if provided."
        )

    start_date = run_cfg.get("start_date")
    if start_date is not None and not isinstance(start_date, str):
        raise SystemExit(
            f"Run {idx} field 'start_date' must be a string in YYYY-MM-DD format."
        )

    end_date = run_cfg.get("end_date")
    if end_date is not None and not isinstance(end_date, str):
        raise SystemExit(
            f"Run {idx} field 'end_date' must be a string in YYYY-MM-DD format."
        )

    return ticker, csv_path, initial_cash, start_date, end_date


def _handle_backtest_batch(manifest_path: Path, summary_path: Path | None = None) -> int:
    runs, default_initial_cash = _load_manifest_runs(manifest_path)

    avg_return = None
    best: BacktestResult | None = None
    worst: BacktestResult | None = None
    results: list[BacktestResult] = []
    for idx, run_cfg in enumerate(runs):
        ticker, csv_path, initial_cash, start_date, end_date = _validate_run_config(
            run_cfg, idx, default_initial_cash
        )

        try:
            df = load_price_csv(csv_path)
        except FileNotFoundError:
            raise SystemExit(f"CSV file not found for run {idx} ({ticker}): {csv_path}")
        except Exception as exc:  # pragma: no cover - defensive
            raise SystemExit(
                f"Failed to load CSV for run {idx} ({ticker}): {exc}"
            ) from exc

        prices = df["close"]
        if start_date:
            prices = prices[prices.index >= pd.to_datetime(start_date)]
        if end_date:
            prices = prices[prices.index <= pd.to_datetime(end_date)]

        if prices.empty:
            raise SystemExit(
                "No price data available for the requested date window in "
                f"run {idx} ({ticker}). Check your CSV and any start/end dates."
            )

        try:
            result = run_buy_and_hold_backtest(
                prices,
                ticker=ticker,
                initial_cash=initial_cash,
            )
        except Exception as exc:  # pragma: no cover - defensive
            raise SystemExit(f"Backtest failed for run {idx} ({ticker}): {exc}") from exc

        results.append(result)
        print(
            f"{result.ticker} | {result.start.date()} -> {result.end.date()} | "
            f"total_return={result.total_return_pct:,.2f}% | "
            f"max_drawdown={result.max_drawdown_pct:,.2f}%"
        )

    if results:
        avg_return = round(
            sum(r.total_return_pct for r in results) / len(results), 6
        )
        best = max(results, key=lambda r: r.total_return_pct)
        worst = min(results, key=lambda r: r.total_return_pct)
        print(
            "Batch summary: "
            f"runs={len(results)} | "
            f"avg_return={avg_return:,.2f}% | "
            f"best={best.ticker} ({best.total_return_pct:,.2f}%) | "
            f"worst={worst.ticker} ({worst.total_return_pct:,.2f}%)"
        )

    if summary_path:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_doc = {
            "runs": [_result_to_dict(r) for r in results],
            "summary": {
                "n_runs": len(results),
                "avg_total_return_pct": avg_return if results else None,
                "best": {
                    "ticker": best.ticker,
                    "total_return_pct": best.total_return_pct,
                }
                if results
                else None,
                "worst": {
                    "ticker": worst.ticker,
                    "total_return_pct": worst.total_return_pct,
                }
                if results
                else None,
            },
        }
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary_doc, f, indent=2)

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
            summary = _result_to_dict(result)
            with cfg.output_path.open("w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

        return 0

    if args.command == "backtest-batch":
        return _handle_backtest_batch(args.manifest, summary_path=args.summary_path)

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
