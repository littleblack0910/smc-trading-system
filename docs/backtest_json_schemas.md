# Backtest JSON Schemas (Week 1)

This document describes the JSON structures emitted by the Week 1 backtest CLIs.

The goal is to make it easy to:

- Validate outputs in tests.
- Consume results from notebooks, dashboards, or other services.
- Keep the CLI contract stable as we evolve the engine.

---

## Single Backtest Summary (`backtest`)

When `--output-path` is provided to the `backtest` subcommand, a JSON file is written with the following fields:

```jsonc
{
  "ticker": "AAPL",               // string: requested ticker symbol
  "period_start": "2024-01-02",   // string (YYYY-MM-DD): first date actually used
  "period_end": "2024-01-12",     // string (YYYY-MM-DD): last date actually used
  "starting_cash": 10000.0,        // number: initial cash
  "ending_value": 10321.45,        // number: final portfolio value (cash + position value)
  "total_return_pct": 3.21,        // number: total return in percent (ending / starting - 1) * 100
  "max_drawdown_pct": -1.75,       // number: maximum drawdown over the period, in percent
  "n_periods": 9                   // integer: number of rows used in the backtest
}
```

### Notes

- `period_start` and `period_end` reflect the **effective** date window after applying
  `--start-date` / `--end-date` filters and intersecting with the CSV.
- `total_return_pct` and `max_drawdown_pct` are expressed as **percent values**, not fractions.
- `n_periods` counts the number of rows in the filtered OHLCV time series.

---

## Batch Backtest Summary (`backtest-batch`)

When `--summary-path` is provided to the `backtest-batch` subcommand, a JSON file is written with the following shape:

```jsonc
{
  "runs": [
    {
      "ticker": "AAPL",              // string: ticker symbol for this run
      "period_start": "2024-01-02",  // string (YYYY-MM-DD)
      "period_end": "2024-01-12",    // string (YYYY-MM-DD)
      "starting_cash": 10000.0,       // number
      "ending_value": 10321.45,       // number
      "total_return_pct": 3.21,       // number (percent)
      "max_drawdown_pct": -1.75,      // number (percent)
      "n_periods": 9                  // integer
    }
    // ... one entry per manifest run that completed successfully
  ],
  "summary": {
    "n_runs": 2,                       // integer: total number of runs included
    "avg_total_return_pct": 4.12,      // number: average of total_return_pct across runs
    "best": {
      "ticker": "MSFT",             // string: best-performing ticker
      "total_return_pct": 7.89        // number: best total return (percent)
    },
    "worst": {
      "ticker": "AAPL",             // string: worst-performing ticker
      "total_return_pct": 1.23        // number: worst total return (percent)
    }
  }
}
```

### Notes

- The `runs` entries share the same shape as the single backtest JSON summary.
- `n_runs` should match `len(runs)`.
- `avg_total_return_pct` is a simple arithmetic mean of `total_return_pct` over all runs.
- `best` and `worst` are selected by `total_return_pct` and include only the `ticker`
  and `total_return_pct` fields for now; additional fields can be added later if needed.

---

## Manifest Validation Expectations (`backtest-batch`)

The `backtest-batch` CLI expects a manifest JSON file with the following structure:

```jsonc
{
  "default_initial_cash": 7500.0,     // optional number, used when a run omits initial_cash
  "runs": [
    {
      "ticker": "MSFT",              // required string
      "csv_path": "data/MSFT.csv",   // required string
      "initial_cash": 5000.0,         // optional number; falls back to default_initial_cash or 10000
      "start_date": "2024-01-01",    // optional string (YYYY-MM-DD)
      "end_date": "2024-01-31"       // optional string (YYYY-MM-DD)
    }
  ]
}
```

If the manifest is:

- Missing the `runs` key,
- Has a non-list `runs` value,
- Contains a run missing `ticker` or `csv_path`, or
- Is not parseable as JSON,

then the CLI prints a clear error message and exits with a non-zero status.

These behaviors are covered by `tests/test_cli_backtest_batch_manifest_validation.py` to make sure
future changes don't silently break the Week 1 contract.
