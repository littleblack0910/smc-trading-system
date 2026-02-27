# Backtest JSON Schemas

This document describes the JSON output structures produced by the Week 1 backtest CLIs. It serves as the contract for tools that consume the CLI outputs (API, UI, notebooks, orchestrators).

---

## Single Backtest JSON (acktest)

When you run the single backtest CLI with --output-path, it writes a JSON document with these fields:

- 	icker (string, required) – ticker symbol.
- period_start (string, YYYY-MM-DD, required) – first bar in the backtest window.
- period_end (string, YYYY-MM-DD, required) – last bar in the backtest window.
- starting_cash (number, required) – initial portfolio cash.
- ending_value (number, required) – final portfolio equity (cash + position value).
- 	otal_return_pct (number, required) – total return over the period, in percent.
- max_drawdown_pct (number, required) – maximum peak-to-trough drawdown over the run, in percent.
- 
_periods (integer, required) – number of price bars after any date-window filtering.

These fields correspond directly to the BacktestResult object used by the engine.

---

## Batch Backtest JSON (acktest-batch)

When you run the batch backtest CLI with --summary-path, it writes a JSON document with:

- uns (array, required)
  - One entry per backtest run.
  - Each entry has the same fields as the single-backtest JSON above.
- summary (object, required)
  - 
_runs (integer, required) – total number of runs in the batch.
  - vg_total_return_pct (number or null, required) – average of 	otal_return_pct across all runs.
  - est (object or null, required) – best-performing run by 	otal_return_pct, with:
    - 	icker (string)
    - 	otal_return_pct (number)
  - worst (object or null, required) – worst-performing run by 	otal_return_pct, with the same fields as est.

This mirrors the aggregate information printed in the human-readable  Batch summary line on stdout.

---

## Notes

- These schemas reflect the Week 1 implementation and are covered by tests in 	ests/test_cli_backtest.py and 	ests/test_cli_backtest_batch.py.
- Future changes to the JSON shape should be backwards compatible (additive fields, not breaking existing ones) and must be accompanied by test updates and documentation updates here.
