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


def _write_manifest(tmp_path: Path, payload: object) -> Path:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    return manifest_path


def test_manifest_must_be_json_object_with_runs(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]

    # Top-level list instead of object
    manifest_path = _write_manifest(tmp_path, [
        {"runs": []},
    ])
    result = run_cli("backtest-batch", "--manifest", str(manifest_path), cwd=project_root)

    assert result.returncode != 0
    message = result.stdout + result.stderr
    assert "Manifest must be a JSON object with a 'runs' list." in message


def test_manifest_requires_runs_key(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    manifest_path = _write_manifest(tmp_path, {"not_runs": []})

    result = run_cli("backtest-batch", "--manifest", str(manifest_path), cwd=project_root)

    assert result.returncode != 0
    message = result.stdout + result.stderr
    assert "Manifest must include a 'runs' list of backtests." in message


def test_manifest_runs_must_be_non_empty_list(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]

    # runs is not a list
    manifest_path = _write_manifest(tmp_path, {"runs": "not-a-list"})
    result = run_cli("backtest-batch", "--manifest", str(manifest_path), cwd=project_root)
    assert result.returncode != 0
    message = result.stdout + result.stderr
    assert "Manifest 'runs' must be a list of backtest entries." in message

    # runs is an empty list (already covered in test_cli_backtest_batch, but we
    # keep a focused assertion here for manifest semantics)
    manifest_path = _write_manifest(tmp_path, {"runs": []})
    result = run_cli("backtest-batch", "--manifest", str(manifest_path), cwd=project_root)
    assert result.returncode != 0
    message = result.stdout + result.stderr
    assert "Manifest 'runs' must contain at least one backtest entry." in message


def test_default_initial_cash_must_be_numeric_if_present(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]

    manifest_path = _write_manifest(
        tmp_path,
        {
            "default_initial_cash": "not-a-number",
            "runs": [
                {"ticker": "AAPL", "csv_path": "dummy.csv"},
            ],
        },
    )

    result = run_cli("backtest-batch", "--manifest", str(manifest_path), cwd=project_root)

    assert result.returncode != 0
    message = result.stdout + result.stderr
    assert "Manifest field 'default_initial_cash' must be a number if provided." in message


def test_run_entries_must_be_objects_with_string_fields(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]

    # run is not an object
    manifest_path = _write_manifest(tmp_path, {"runs": [123]})
    result = run_cli("backtest-batch", "--manifest", str(manifest_path), cwd=project_root)
    assert result.returncode != 0
    message = result.stdout + result.stderr
    assert "Run 0 must be a JSON object with 'ticker' and 'csv_path' keys." in message

    # ticker is not a string
    manifest_path = _write_manifest(
        tmp_path,
        {"runs": [{"ticker": 123, "csv_path": "dummy.csv"}]},
    )
    result = run_cli("backtest-batch", "--manifest", str(manifest_path), cwd=project_root)
    assert result.returncode != 0
    message = result.stdout + result.stderr
    assert "Run 0 field 'ticker' must be a string." in message

    # csv_path is not a string
    manifest_path = _write_manifest(
        tmp_path,
        {"runs": [{"ticker": "AAPL", "csv_path": 42}]},
    )
    result = run_cli("backtest-batch", "--manifest", str(manifest_path), cwd=project_root)
    assert result.returncode != 0
    message = result.stdout + result.stderr
    assert "Run 0 field 'csv_path' must be a string path." in message


def test_initial_cash_and_dates_are_validated_per_run(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]

    # initial_cash is not numeric
    manifest_path = _write_manifest(
        tmp_path,
        {
            "runs": [
                {
                    "ticker": "AAPL",
                    "csv_path": "dummy.csv",
                    "initial_cash": "not-a-number",
                }
            ]
        },
    )
    result = run_cli("backtest-batch", "--manifest", str(manifest_path), cwd=project_root)
    assert result.returncode != 0
    message = result.stdout + result.stderr
    assert "Run 0 field 'initial_cash' must be a number if provided." in message

    # start_date must be a string when present
    manifest_path = _write_manifest(
        tmp_path,
        {
            "runs": [
                {
                    "ticker": "AAPL",
                    "csv_path": "dummy.csv",
                    "start_date": 20240101,
                }
            ]
        },
    )
    result = run_cli("backtest-batch", "--manifest", str(manifest_path), cwd=project_root)
    assert result.returncode != 0
    message = result.stdout + result.stderr
    assert "Run 0 field 'start_date' must be a string in YYYY-MM-DD format." in message

    # end_date must be a string when present
    manifest_path = _write_manifest(
        tmp_path,
        {
            "runs": [
                {
                    "ticker": "AAPL",
                    "csv_path": "dummy.csv",
                    "end_date": 20240131,
                }
            ]
        },
    )
    result = run_cli("backtest-batch", "--manifest", str(manifest_path), cwd=project_root)
    assert result.returncode != 0
    message = result.stdout + result.stderr
    assert "Run 0 field 'end_date' must be a string in YYYY-MM-DD format." in message
