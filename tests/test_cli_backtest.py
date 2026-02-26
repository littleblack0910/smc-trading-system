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
