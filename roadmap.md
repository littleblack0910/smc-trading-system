# SMC Trading – Project Roadmap

**North Star:**
A live, AI-assisted trading system using **Smart Money Concepts (SMC)** that can:

- Continuously monitor markets
- Apply SMC-based strategies (structure, liquidity, order blocks, FVG, etc.)
- Execute trades via a broker API (paper first, then live)
- Provide a clear UI for configuration, monitoring, and analysis

This roadmap is organized into phases (Weeks 1+). Each phase builds on the previous ones.

---

## Phase 1 – Backtest Engine & CLIs (Week 1)

Goal: Build a **reliable, tested backtesting engine** with CLIs and JSON outputs that are easy to script and later wrap in an API/UI.

### Deliverables

- **Core backtest logic**
- Start with a simple baseline strategy (e.g., buy-and-hold).
- Operate on OHLCV time series from CSV or equivalent.

- **Single-run CLI**
- Command: `backtest` (exact interface in `smc_trading/orchestrator/cli.py`).
- Inputs: ticker, csv path, start/end dates, initial cash, output options.
- Outputs:
- Human-readable summary line on stdout.
- Optional JSON file with key metrics (e.g., total return, max drawdown).

- **Batch backtest CLI**
- Command: `backtest-batch`.
- Inputs: JSON manifest describing multiple runs (ticker, csv_path, cash, dates, etc.).
- Outputs:
- Per-run results.
- Optional `--summary-path` JSON report with aggregates:
- `n_runs`
- `avg_total_return_pct`
- Best/worst performers and relevant stats.
- A human-readable “Batch summary” line on stdout.

- **Tests & documentation**
- Pytest coverage for:
- Single-run CLI behavior.
- Batch CLI behavior and manifest validation.
- JSON output formats and aggregates.
- README updates documenting:
- How to run single and batch backtests.
- JSON schemas for outputs.

This phase creates the **engine** that everything else (API, UI, live trading) will depend on.

---

## Phase 2 – Strategy & Data Abstractions (Week 2)

Goal: Make it easy to plug in **SMC strategies** and feed data from multiple sources.

### Deliverables

- **Strategy interface**
- A clear abstraction for “strategy” (e.g., a class or set of functions that:
- Receives price/volume time series and context.
- Emits trading decisions/signals over time.
- Initial strategies:
- Baseline (buy-and-hold).
- A simple technical/SMC-adjacent strategy (e.g., moving average, basic structure-based entries/exits).

- **Data loading layer**
- Standardized OHLCV data structure.
- Ability to plug in:
- Local CSV files.
- Later: API feeds (e.g., Polygon/Alpaca/other).

- **CLI extension**
- Backtest CLIs accept:
- Strategy selection parameter.
- Strategy-specific configuration (hyperparameters).

- **Tests & docs**
- Unit tests for strategies and data loaders.
- README docs for:
- How to add a new strategy.
- How to select strategies via CLI.

This phase prepares the engine for **real SMC strategies** and multiple data sources.

---

## Phase 3 – API / Service Layer

Goal: Turn the backtesting engine into a **service** that a UI and other tools can talk to.

### Deliverables

- **HTTP API** (e.g., FastAPI/Flask)
- Endpoints (examples):
- `POST /backtest` – single run, JSON input, JSON output.
- `POST /backtest-batch` – batch manifest in JSON, JSON summary output.
- `GET /strategies` – list available strategies and parameters.
- Internally call the same engine used by the CLI.

- **Configuration & persistence**
- Simple persistence for:
- Saved configurations.
- Recent backtest results.
- Could be:
- Files on disk, or
- A lightweight DB (e.g., SQLite) depending on complexity.

- **Tests & docs**
- API integration tests.
- Docs:
- API endpoints and example requests/responses.
- How to run the API server locally.

This phase creates the **bridge** from engine to UI, and also lays foundation for live services later.

---

## Phase 4 – UI (Web App) for Backtesting & Analysis

Goal: Build a **user-friendly UI** for configuring/running backtests and inspecting results.

### Deliverables

- **UI stack**
- Likely React / Next.js (aligned with Stanley’s experience).
- Frontend talking to the backend API via HTTP.

- **Core flows**
- Select/upload data (ticker/CSV or preset universes).
- Configure strategy + parameters.
- Run single or batch backtests.
- View results:
- Summary stats cards.
- Tables of runs (for batch).
- Visuals: equity curve, drawdown, comparison charts.

- **UX goals**
- Make the system usable without touching CLI or raw JSON.
- Preserve the ability for power users to still use CLIs directly.

- **Tests & docs**
- Basic frontend tests (where appropriate).
- Documentation on how to run the UI and how it connects to the API.

This phase delivers the **“easy to use” UI** on top of the existing engine.

---

## Phase 5 – SMC Strategies (Smart Money Concepts)

Goal: Introduce **real SMC trading logic** atop the engine.

### Deliverables

- **SMC building blocks**
- Market structure (HH/HL/LH/LL).
- Liquidity zones (equal highs/lows, liquidity pools).
- Order blocks, fair value gaps (FVGs).
- Session/time-of-day filters.

- **SMC strategies**
- Codify 1–2 concrete SMC strategies using these building blocks:
- Entry/exit rules.
- Risk management (stop loss, TP, partials).
- Expose their configuration via:
- Strategy parameters in the API/CLI.
- UI controls (dropdowns, sliders, fields).

- **Backtests & visualization**
- Extend backtest outputs to include:
- SMC-specific annotations (e.g., where entries/exits were triggered).
- Optional: UI overlays on charts for SMC structures.

This phase differentiates the system as an **SMC-focused** trading tool, not just a generic backtester.

---

## Phase 6 – Live Trading (Paper → Live)

Goal: Turn the system into an **AI-assisted live trading setup**.

### Deliverables

- **Broker integration**
- Initial integration with a broker API (e.g., Alpaca, IBKR, etc.).
- Start with **paper trading** mode:
- Translate strategy signals into real orders.
- Track positions, P&L, and risk.

- **Live trading engine**
- A process/service that:
- Subscribes to live data.
- Uses SMC strategies to generate signals.
- Sends orders to the broker (respecting rate limits and risk caps).
- Logging and metrics:
- Every decision and order is logged.
- Monitoring dashboards (or at least logs + simple UI views).

- **UI extensions**
- Monitor:
- Live positions.
- Open orders.
- Recent trades & performance.
- Controls to:
- Start/stop strategies.
- Adjust risk parameters.

- **AI assistance**
- Where appropriate, add AI/ML components:
- Regime classification (risk on/off).
- Volatility-aware position sizing.
- Model-based filters for SMC signals.

This phase completes the arc: from backtesting to **real-time, automated SMC trading**.

---

## Guiding Principles

- **Engine first, UI second, automation third.**
- **Always keep `develop` runnable and documented.**
- **SMC is the core edge.** Everything (data, engine, UI, live trading) is built to serve robust SMC strategies.
- Start with **paper trading** and thorough backtests before risking real capital.
