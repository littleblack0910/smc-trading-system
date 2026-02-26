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

2. **Data Ingestion (Weeks 1–2)**
   - Implement market data ingestion (historical + live) from chosen provider.
   - Store data in local DB or files; define canonical data schema.

3. **Strategy & Backtesting (Weeks 2–3)**
   - Implement a simple baseline strategy (e.g., momentum + volatility filters).
   - Build a small backtesting harness.

4. **Execution Engine (Weeks 3–4)**
   - Integrate with broker paper-trading API.
   - Implement risk checks and position sizing.

5. **24/7 Orchestration & Monitoring (Weeks 4–6)**
   - Build a scheduler/daemon to run the loop.
   - Add logging, metrics, and basic monitoring dashboard.

This file will evolve as we refine requirements and the product direction.
