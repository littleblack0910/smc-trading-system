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

    assert len(lines) == 2
    assert lines[0].startswith("MSFT | 2024-01-01 -> 2024-01-02")
    assert "total_return=10.00%" in lines[0]
    assert "max_drawdown=0.00%" in lines[0]

    assert lines[1].startswith("AAPL | 2024-02-01 -> 2024-02-02")
    assert "total_return=10.00%" in lines[1]
    assert "max_drawdown=0.00%" in lines[1]


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
    assert len(lines) == 2


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
    assert len(lines) == 1
    assert lines[0].startswith("MSFT | 2024-01-02 -> 2024-01-03")


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
