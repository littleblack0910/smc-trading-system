# SMC Trading System

A 24/7 AI-assisted trading system for monitoring selected stocks, ingesting market and fundamental data, and executing strategy-driven trades via broker APIs.

## High-Level Architecture

- **ingestion/**
  - Connectors for market data (price, volume, OHLC) and fundamentals (financial statements, ratios, news).
- **strategy/**
  - Signal generation logic (rule-based to start, then ML/AI models).
- **execution/**
  - Order routing, risk checks, and interaction with broker APIs (paper trading first).
- **orchestrator/**
  - Scheduler/daemon that coordinates ingestion, strategy evaluation, and execution.
- **config/**
  - Environment and strategy configuration (tickers, risk limits, broker keys, etc.).
- **docs/**
  - Design docs, ADRs, and notes.
- **tests/**
  - Unit and integration tests.

## Roadmap (Initial)

1. **Repo & Skeleton (Week 1)**
   - Create folder structure, basic config, and simple CLI entrypoint.
   - Add a simple backtest on historical price data for a few tickers.

2. **Data Ingestion (Weeks 1鈥?)**
   - Implement market data ingestion (historical + live) from chosen provider.
   - Store data in local DB or files; define canonical data schema.

3. **Strategy & Backtesting (Weeks 2鈥?)**
   - Implement a simple baseline strategy (e.g., momentum + volatility filters).
   - Build a small backtesting harness.

4. **Execution Engine (Weeks 3鈥?)**
   - Integrate with broker paper-trading API.
   - Implement risk checks and position sizing.

5. **24/7 Orchestration & Monitoring (Weeks 4鈥?)**
   - Build a scheduler/daemon to run the loop.
   - Add logging, metrics, and basic monitoring dashboard.

This file will evolve as we refine requirements and the product direction.

## Usage

### Setup

1. Create and activate a Python 3.11 virtual environment:

   ```bash
   python -m venv .venv
   # On macOS/Linux
   source .venv/bin/activate
   # On Windows
   .venv\\Scripts\\activate
   ```

2. Install dependencies (editable mode so the CLI entrypoint is available during development):

   ```bash
   pip install -e .
   ```

### Running tests

From the project root:

```bash
pytest
```

### Running the CLI backtest

The CLI entrypoint is exposed as the `smc-trading` console script, and is also runnable via `python -m smc_trading`.

Assuming you have a CSV with at least `date` and `close` columns (for example `data/AAPL_sample.csv`):

```bash
python -m smc_trading backtest \
  --ticker AAPL \
  --csv-path data/AAPL_sample.csv \
  --initial-cash 10000
```

#### Optional arguments

- `--start-date YYYY-MM-DD` 鈥?only use rows on or after this date.
- `--end-date YYYY-MM-DD` 鈥?only use rows on or before this date.
- `--output-path path/to/summary.json` 鈥?write a machine-readable JSON summary of the backtest result.
- `--equity-curve-path path/to/equity.csv` 鈥?write the full equity curve (date, price, position, cash, equity) to CSV.

Example with a date window and JSON summary output:

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

The human-readable summary is printed to stdout, and when `--output-path` is provided a JSON file is written containing:

- `ticker`
- `period_start`
- `period_end`
- `starting_cash`
- `ending_value`
- `total_return_pct`
- `max_drawdown_pct`
- `n_periods`

This makes it easy to plug the backtest into higher-level tooling (dashboards, notebooks, or orchestrators) while preserving a concise CLI summary.

### Running batch CLI backtests

You can run multiple buy-and-hold backtests in one command using the `backtest-batch` subcommand and a JSON manifest file.

The manifest must be a JSON object with a top-level `runs` list. Each entry in `runs` is an object with:

- `ticker` (required): the ticker symbol, e.g. `"AAPL"`.
- `csv_path` (required): path to a CSV file with at least `date` and `close` columns.
- `initial_cash` (optional): starting cash for that run. If omitted, the value from `default_initial_cash` is used when present, otherwise `10000`.
- `start_date` (optional): start date for that run, in `YYYY-MM-DD` format.
- `end_date` (optional): end date for that run, in `YYYY-MM-DD` format.

The top-level manifest may also include:

- `default_initial_cash` (optional): a numeric default starting cash applied to runs that omit `initial_cash`.
- `default_start_date` (optional): a default start date (YYYY-MM-DD) applied to runs that omit `start_date`.
- `default_end_date` (optional): a default end date (YYYY-MM-DD) applied to runs that omit `end_date`.

Example `manifest.json`:

```json
{
  "default_initial_cash": 7500,
  "runs": [
    {
      "ticker": "MSFT",
      "csv_path": "data/MSFT_sample.csv",
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    },
    {
      "ticker": "AAPL",
      "csv_path": "data/AAPL_sample.csv",
      "initial_cash": 5000
    }
  ]
}
```

Run the batch backtest from the project root (for example, using the sample manifest in data/backtest_batch_manifest_example.json):

```bash
python -m smc_trading backtest-batch --manifest path/to/manifest.json
```

Each run prints a single summary line to stdout in the form:

```text
TICKER | YYYY-MM-DD -> YYYY-MM-DD | total_return=XX.XX% | max_drawdown=YY.YY%
```

You can also emit a machine-readable batch report by adding `--summary-path path/to/report.json`. The JSON file contains the per-run results plus a small aggregate section (number of runs, average return, best/worst by total return).

The batch summary JSON has the following shape:

- `runs`: a list of per-run objects with the same fields as the single backtest JSON summary (`ticker`, `period_start`, `period_end`, `starting_cash`, `ending_value`, `total_return_pct`, `max_drawdown_pct`, `n_periods`).
- `summary`: an aggregate object with:
  - `n_runs`: total number of runs in the batch.
  - `avg_total_return_pct`: the average total return across all runs.
  - `best`: an object with `ticker` and `total_return_pct` for the best-performing run.
  - `worst`: an object with `ticker` and `total_return_pct` for the worst-performing run.

This makes it easier to feed the batch output into dashboards, notebooks, or other tooling without re-deriving aggregate metrics.

Additional useful flags for batch runs:

- `--quiet`: suppress per-run summary lines and only print the final batch summary (useful when you are mainly interested in aggregate metrics).
- `--skip-missing`: skip any runs whose CSV files are missing instead of failing the entire batch. Each skipped run is reported to stdout so you can see what was ignored.

If the manifest file is missing, invalid JSON, or a run is missing required keys (`ticker` or `csv_path`), the command exits with an error message describing the problem.

Example manifest file:

An example manifest is included at `data/batch_manifest_example.json`, which you can run with:

```bash
python -m smc_trading backtest-batch --manifest data/batch_manifest_example.json
```
