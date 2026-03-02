# Backtest CLI Reference

This document describes the Week 1 backtesting CLIs and their JSON outputs. It is the detailed companion to the high-level overview in `README.md`.

The CLIs are exposed via the `smc-trading` console script and via `python -m smc_trading`.

## Single-run backtest (`backtest`)

### Command

```bash
python -m smc_trading backtest \
  --ticker AAPL \
  --csv-path data/AAPL_sample.csv \
  --initial-cash 10000 \
  --start-date 2024-01-02 \
  --end-date 2024-01-12 \
  --output-path data/AAPL_backtest_summary.json \
  --equity-curve-path data/AAPL_equity_curve.csv
```

### Arguments

- `--ticker` (required): Ticker symbol, for example `AAPL`.
- `--csv-path` (required): Path to a CSV file with at least `date` and `close` columns.
- `--initial-cash` (optional, default: `10000`): Starting cash for the backtest.
- `--start-date` (optional): Filter rows to dates on or after this date (`YYYY-MM-DD`).
- `--end-date` (optional): Filter rows to dates on or before this date (`YYYY-MM-DD`).
- `--output-path` (optional): When provided, a JSON summary is written to this path.
- `--equity-curve-path` (optional): When provided, the full equity curve is written as CSV.

### Human-readable output

The CLI prints a human summary like:

```text
=== Buy & Hold Backtest ===
Ticker          : AAPL
Period          : 2024-01-02 -> 2024-01-12
Bars            : 9

Starting cash   : $10,000.00
Ending value    : $10,900.00
Total return    :  9.00%
Max drawdown    : -3.50%
```

### JSON summary schema (`--output-path`)

When `--output-path` is provided, the JSON document has the following shape:

```jsonc
{
  "ticker": "AAPL",               // string: ticker symbol
  "period_start": "2024-01-02",   // string: first date in the backtest window (YYYY-MM-DD)
  "period_end": "2024-01-12",     // string: last date in the backtest window (YYYY-MM-DD)
  "starting_cash": 10000.0,        // number: initial cash
  "ending_value": 10900.0,         // number: final portfolio value
  "total_return_pct": 9.0,         // number: total return in percent
  "max_drawdown_pct": -3.5,        // number: max drawdown in percent (negative)
  "n_periods": 9                   // integer: number of bars/rows used in the backtest
}
```

This is produced from the internal `BacktestResult` object and is the canonical schema for single-run summaries.

### Equity curve CSV schema (`--equity-curve-path`)

When `--equity-curve-path` is provided, a CSV with the full equity curve is written with the following columns:

- `date` (YYYY-MM-DD string)
- `price` (float): closing price for that bar
- `position` (float): position size in units of the asset
- `cash` (float): cash held
- `equity` (float): total portfolio value (position * price + cash)

Example (truncated):

```csv
date,price,position,cash,equity
2024-01-02,100.0,100.0,0.0,10000.0
2024-01-03,101.0,100.0,0.0,10100.0
...
```

---

## Batch backtests (`backtest-batch`)

### Command

```bash
python -m smc_trading backtest-batch \
  --manifest data/batch_manifest_example.json \
  --summary-path data/batch_report.json \
  --per-run-output-dir data/per_run \
  --quiet
```

### Manifest schema

The manifest must be a JSON object with:

- `runs` (required): list of run objects.
- `default_initial_cash` (optional): numeric default starting cash.
- `default_start_date` (optional): default start date (YYYY-MM-DD).
- `default_end_date` (optional): default end date (YYYY-MM-DD).

Each entry in `runs` is a JSON object with:

- `ticker` (required): string ticker symbol.
- `csv_path` (required): string path to CSV with `date` and `close` columns.
- `initial_cash` (optional): numeric starting cash (overrides `default_initial_cash` when present).
- `start_date` (optional): start date for this run (YYYY-MM-DD). If omitted, `default_start_date` is used when present.
- `end_date` (optional): end date for this run (YYYY-MM-DD). If omitted, `default_end_date` is used when present.

Example manifest:

```json
{
  "default_initial_cash": 7500,
  "default_start_date": "2024-01-02",
  "default_end_date": "2024-01-12",
  "runs": [
    {
      "ticker": "AAPL",
      "csv_path": "data/AAPL_sample.csv"
    },
    {
      "ticker": "MSFT",
      "csv_path": "data/MSFT_sample.csv",
      "initial_cash": 5000,
      "start_date": "2024-01-05",
      "end_date": "2024-01-31"
    }
  ]
}
```

### CLI flags

- `--manifest` (required): path to the manifest JSON file.
- `--summary-path` (optional): when provided, write an aggregate JSON report for the batch.
- `--per-run-output-dir` (optional): when provided, write one JSON summary per executed run.
- `--quiet` (optional): if set, suppress per-run summary lines and only print the batch summary.
- `--skip-missing` (optional): if set, skip runs whose CSV files are missing instead of failing the whole batch.

### Human-readable output

By default, the CLI prints one line per executed run plus a final batch summary line. Example:

```text
AAPL | 2024-01-02 -> 2024-01-12 | total_return=9.00% | max_drawdown=-3.50%
MSFT | 2024-01-05 -> 2024-01-31 | total_return=4.20% | max_drawdown=-2.10%
Batch summary: runs=2 | avg_return=6.60% | best=AAPL (9.00%) | worst=MSFT (4.20%)
```

When `--quiet` is used, only the final `Batch summary:` line is printed.

### Batch summary JSON schema (`--summary-path`)

When `--summary-path` is provided, the JSON document has the following shape:

```jsonc
{
  "runs": [
    {
      "ticker": "AAPL",
      "period_start": "2024-01-02",
      "period_end": "2024-01-12",
      "starting_cash": 7500.0,
      "ending_value": 8175.0,
      "total_return_pct": 9.0,
      "max_drawdown_pct": -3.5,
      "n_periods": 9
    },
    {
      "ticker": "MSFT",
      "period_start": "2024-01-05",
      "period_end": "2024-01-31",
      "starting_cash": 5000.0,
      "ending_value": 5210.0,
      "total_return_pct": 4.2,
      "max_drawdown_pct": -2.1,
      "n_periods": 20
    }
  ],
  "summary": {
    "n_runs": 2,
    "avg_total_return_pct": 6.6,
    "best": {
      "ticker": "AAPL",
      "total_return_pct": 9.0
    },
    "worst": {
      "ticker": "MSFT",
      "total_return_pct": 4.2
    }
  }
}
```

- `runs` contains one entry per executed run, each with the same schema as the single backtest JSON summary.
- `summary` contains aggregate metrics that make it easier to consume the batch output programmatically.

### Per-run JSON summaries (`--per-run-output-dir`)

When `--per-run-output-dir` is provided, the CLI writes one JSON summary per executed run. The files are named:

```text
<ticker>_<index>.json
```

where `<index>` is the zero-based index of the run in the manifest `runs` list.

Each document has the same schema as the single backtest JSON summary:

```jsonc
{
  "ticker": "AAPL",
  "period_start": "2024-01-02",
  "period_end": "2024-01-12",
  "starting_cash": 10000.0,
  "ending_value": 10900.0,
  "total_return_pct": 9.0,
  "max_drawdown_pct": -3.5,
  "n_periods": 9
}
```

---

## Error handling

Both CLIs use clear, user-facing error messages and non-zero exit codes when something goes wrong:

- Missing CSV files
- Empty price windows after applying date filters
- Invalid manifest shapes or types
- Empty `runs` lists in batch manifests

Tests in `tests/test_cli_backtest.py`, `tests/test_cli_backtest_batch.py`, and
`tests/test_cli_backtest_batch_manifest_validation.py` cover these cases to keep
behavior stable as the engine evolves.
