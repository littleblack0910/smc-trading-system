import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "smc_trading", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_backtest_runs_and_prints_summary(tmp_path: Path) -> None:
    # Write a tiny CSV to the temp directory
    csv_path = tmp_path / "AAPL.csv"
    csv_path.write_text(
        "date,close\n2024-01-01,100\n2024-01-02,102\n", encoding="utf-8"
    )

    project_root = Path(__file__).resolve().parents[1]

    result = run_cli(
        "backtest",
        "--ticker",
        "AAPL",
        "--csv-path",
        str(csv_path),
        "--initial-cash",
        "10000",
        cwd=project_root,
    )

    assert result.returncode == 0, result.stderr
    output = result.stdout

    assert "=== Buy & Hold Backtest ===" in output
    assert "Ticker          : AAPL" in output
    assert "Starting cash   : $10,000.00" in output
    assert "Ending value" in output
    assert "Total return" in output


def test_cli_backtest_respects_date_window(tmp_path: Path) -> None:
    csv_path = tmp_path / "AAPL.csv"
    csv_path.write_text(
        "date,close\n2024-01-01,100\n2024-01-02,110\n2024-01-03,120\n",
        encoding="utf-8",
    )

    project_root = Path(__file__).resolve().parents[1]

    result = run_cli(
        "backtest",
        "--ticker",
        "AAPL",
        "--csv-path",
        str(csv_path),
        "--initial-cash",
        "10000",
        "--start-date",
        "2024-01-02",
        "--end-date",
        "2024-01-03",
        cwd=project_root,
    )

    assert result.returncode == 0, result.stderr
    output = result.stdout

    # The reported period should reflect the filtered window.
    assert "Period          : 2024-01-02 -> 2024-01-03" in output


def test_cli_backtest_fails_when_date_window_is_empty(tmp_path: Path) -> None:
    csv_path = tmp_path / "AAPL.csv"
    csv_path.write_text(
        "date,close\n2024-01-01,100\n2024-01-02,110\n2024-01-03,120\n",
        encoding="utf-8",
    )

    project_root = Path(__file__).resolve().parents[1]

    result = run_cli(
        "backtest",
        "--ticker",
        "AAPL",
        "--csv-path",
        str(csv_path),
        "--initial-cash",
        "10000",
        "--start-date",
        "2025-01-01",
        "--end-date",
        "2025-01-31",
        cwd=project_root,
    )

    # We expect a non-zero exit code and a clear error message.
    assert result.returncode != 0
    assert (
        "No price data available for the requested date window" in result.stderr
        or "No price data available for the requested date window" in result.stdout
    )


def test_cli_backtest_writes_json_summary_when_requested(tmp_path: Path) -> None:
    csv_path = tmp_path / "AAPL.csv"
    csv_path.write_text(
        "date,close\n2024-01-01,100\n2024-01-02,110\n", encoding="utf-8"
    )

    output_path = tmp_path / "summary.json"
    project_root = Path(__file__).resolve().parents[1]

    result = run_cli(
        "backtest",
        "--ticker",
        "AAPL",
        "--csv-path",
        str(csv_path),
        "--initial-cash",
        "10000",
        "--output-path",
        str(output_path),
        cwd=project_root,
    )

    assert result.returncode == 0, result.stderr
    assert output_path.exists()

    data = json.loads(output_path.read_text(encoding="utf-8"))
    for key in [
        "ticker",
        "period_start",
        "period_end",
        "starting_cash",
        "ending_value",
        "total_return_pct",
        "max_drawdown_pct",
        "n_periods",
    ]:
        assert key in data, f"Missing key in JSON summary: {key}"

    assert data["ticker"] == "AAPL"
    assert data["period_start"] == "2024-01-01"
    assert data["period_end"] == "2024-01-02"


def test_cli_backtest_writes_equity_curve_csv_when_requested(tmp_path: Path) -> None:
    csv_path = tmp_path / "AAPL.csv"
    csv_path.write_text(
        "date,close\n2024-01-01,100\n2024-01-02,110\n2024-01-03,105\n",
        encoding="utf-8",
    )

    equity_path = tmp_path / "equity.csv"
    project_root = Path(__file__).resolve().parents[1]

    result = run_cli(
        "backtest",
        "--ticker",
        "AAPL",
        "--csv-path",
        str(csv_path),
        "--initial-cash",
        "10000",
        "--equity-curve-path",
        str(equity_path),
        cwd=project_root,
    )

    assert result.returncode == 0, result.stderr
    assert equity_path.exists()

    df = pd.read_csv(equity_path, parse_dates=["date"])
    assert list(df.columns) == ["date", "price", "position", "cash", "equity"]
    assert len(df) == 3
    assert pytest.approx(df.iloc[0]["equity"], rel=1e-6) == 10_000.0
    # Ending equity reflects last price (105 vs first 100)
    assert pytest.approx(df.iloc[-1]["equity"], rel=1e-6) == 10_000.0 * 1.05
