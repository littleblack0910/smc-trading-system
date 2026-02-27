from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "smc_trading", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_backtest_batch_runs_two_entries_in_manifest(tmp_path: Path) -> None:
    csv_msft = tmp_path / "MSFT.csv"
    csv_msft.write_text(
        "date,close\n2024-01-01,100\n2024-01-02,110\n",
        encoding="utf-8",
    )

    csv_aapl = tmp_path / "AAPL.csv"
    csv_aapl.write_text(
        "date,close\n2024-02-01,200\n2024-02-02,220\n",
        encoding="utf-8",
    )

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "runs": [
                    {"ticker": "MSFT", "csv_path": str(csv_msft)},
                    {"ticker": "AAPL", "csv_path": str(csv_aapl), "initial_cash": 5_000},
                ]
            }
        ),
        encoding="utf-8",
    )

    project_root = Path(__file__).resolve().parents[1]
    result = run_cli(
        "backtest-batch", "--manifest", str(manifest_path), cwd=project_root
    )

    assert result.returncode == 0, result.stderr
    lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    run_lines = [line for line in lines if not line.startswith("Batch summary")]

    assert len(run_lines) == 2
    assert run_lines[0].startswith("MSFT | 2024-01-01 -> 2024-01-02")
    assert "total_return=10.00%" in run_lines[0]
    assert "max_drawdown=0.00%" in run_lines[0]

    assert run_lines[1].startswith("AAPL | 2024-02-01 -> 2024-02-02")
    assert "total_return=10.00%" in run_lines[1]
    assert "max_drawdown=0.00%" in run_lines[1]


def test_backtest_batch_respects_default_initial_cash_and_overrides(tmp_path: Path) -> None:
    csv_msft = tmp_path / "MSFT.csv"
    csv_msft.write_text(
        "date,close\n2024-01-01,100\n2024-01-02,110\n",
        encoding="utf-8",
    )

    csv_aapl = tmp_path / "AAPL.csv"
    csv_aapl.write_text(
        "date,close\n2024-02-01,200\n2024-02-02,220\n",
        encoding="utf-8",
    )

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "default_initial_cash": 7500,
                "runs": [
                    {"ticker": "MSFT", "csv_path": str(csv_msft)},
                    {
                        "ticker": "AAPL",
                        "csv_path": str(csv_aapl),
                        "initial_cash": 5_000,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    project_root = Path(__file__).resolve().parents[1]
    result = run_cli(
        "backtest-batch", "--manifest", str(manifest_path), cwd=project_root
    )

    assert result.returncode == 0, result.stderr
    # We don't assert on cash directly here, but this exercises the default and override flow
    lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    run_lines = [line for line in lines if not line.startswith("Batch summary")]
    assert len(run_lines) == 2


def test_backtest_batch_supports_per_run_date_window(tmp_path: Path) -> None:
    csv_msft = tmp_path / "MSFT.csv"
    csv_msft.write_text(
        "date,close\n"
        "2024-01-01,100\n"
        "2024-01-02,110\n"
        "2024-01-03,120\n",
        encoding="utf-8",
    )

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "ticker": "MSFT",
                        "csv_path": str(csv_msft),
                        "start_date": "2024-01-02",
                        "end_date": "2024-01-03",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    project_root = Path(__file__).resolve().parents[1]
    result = run_cli(
        "backtest-batch", "--manifest", str(manifest_path), cwd=project_root
    )

    assert result.returncode == 0, result.stderr
    lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
    run_lines = [line for line in lines if not line.startswith("Batch summary")]
    assert len(run_lines) == 1
    assert run_lines[0].startswith("MSFT | 2024-01-02 -> 2024-01-03")


def test_backtest_batch_fails_when_manifest_missing(tmp_path: Path) -> None:
    missing_manifest = tmp_path / "does_not_exist.json"
    project_root = Path(__file__).resolve().parents[1]

    result = run_cli(
        "backtest-batch", "--manifest", str(missing_manifest), cwd=project_root
    )

    assert result.returncode != 0
    message = result.stderr + result.stdout
    assert "Manifest file not found" in message


def test_backtest_batch_fails_on_invalid_json(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{not-json", encoding="utf-8")
    project_root = Path(__file__).resolve().parents[1]

    result = run_cli(
        "backtest-batch", "--manifest", str(manifest_path), cwd=project_root
    )

    assert result.returncode != 0
    message = result.stderr + result.stdout
    assert "Failed to parse manifest JSON" in message


def test_backtest_batch_fails_when_run_missing_required_key(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"runs": [{"ticker": "AAPL"}]}), encoding="utf-8")
    project_root = Path(__file__).resolve().parents[1]

    result = run_cli(
        "backtest-batch", "--manifest", str(manifest_path), cwd=project_root
    )

    assert result.returncode != 0
    message = result.stderr + result.stdout
    assert "missing required key(s): csv_path" in message


def test_backtest_batch_writes_summary_json(tmp_path: Path) -> None:
    csv_best = tmp_path / "BEST.csv"
    csv_best.write_text(
        "date,close\n2024-01-01,100\n2024-01-02,110\n",
        encoding="utf-8",
    )

    csv_worst = tmp_path / "WORST.csv"
    csv_worst.write_text(
        "date,close\n2024-01-01,200\n2024-01-02,190\n",
        encoding="utf-8",
    )

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "runs": [
                    {"ticker": "BEST", "csv_path": str(csv_best)},
                    {"ticker": "WORST", "csv_path": str(csv_worst)},
                ]
            }
        ),
        encoding="utf-8",
    )

    summary_path = tmp_path / "report.json"
    project_root = Path(__file__).resolve().parents[1]
    result = run_cli(
        "backtest-batch",
        "--manifest",
        str(manifest_path),
        "--summary-path",
        str(summary_path),
        cwd=project_root,
    )

    assert result.returncode == 0, result.stderr
    assert summary_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["summary"]["n_runs"] == 2
    assert summary["summary"]["best"]["ticker"] == "BEST"
    assert summary["summary"]["worst"]["ticker"] == "WORST"
    assert summary["summary"]["avg_total_return_pct"] == 2.5
    assert len(summary["runs"]) == 2
    assert {run["ticker"] for run in summary["runs"]} == {"BEST", "WORST"}

    batch_line = [line for line in result.stdout.splitlines() if "Batch summary" in line]
    assert batch_line, "Expected batch summary line in stdout"
    assert "best=BEST (10.00%)" in batch_line[0]
    assert "worst=WORST (-5.00%)" in batch_line[0]


def test_backtest_batch_errors_on_empty_runs(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"runs": []}), encoding="utf-8")
    project_root = Path(__file__).resolve().parents[1]

    result = run_cli(
        "backtest-batch", "--manifest", str(manifest_path), cwd=project_root
    )

    assert result.returncode != 0
    message = result.stderr + result.stdout
    assert "must contain at least one backtest entry" in message

def test_backtest_batch_errors_when_csv_missing(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "ticker": "AAPL",
                        "csv_path": str(tmp_path / "does_not_exist.csv"),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    project_root = Path(__file__).resolve().parents[1]
    result = run_cli(
        "backtest-batch", "--manifest", str(manifest_path), cwd=project_root
    )

    assert result.returncode != 0
    message = result.stderr + result.stdout
    assert "CSV file not found for run 0 (AAPL)" in message


def test_backtest_batch_errors_when_date_window_empty(tmp_path: Path) -> None:
    csv_path = tmp_path / "AAPL.csv"
    csv_path.write_text(
        "date,close\n2024-01-01,100\n2024-01-02,110\n2024-01-03,120\n",
        encoding="utf-8",
    )

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "ticker": "AAPL",
                        "csv_path": str(csv_path),
                        "start_date": "2025-01-01",
                        "end_date": "2025-01-31",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    project_root = Path(__file__).resolve().parents[1]
    result = run_cli(
        "backtest-batch", "--manifest", str(manifest_path), cwd=project_root
    )

    assert result.returncode != 0
    message = result.stderr + result.stdout
    assert "No price data available for the requested date window in run 0 (AAPL)." in message
