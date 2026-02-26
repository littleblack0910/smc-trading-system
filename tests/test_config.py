from pathlib import Path

from smc_trading.config.settings import BacktestConfig, backtest_config_from_args


class DummyArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_backtest_config_from_args_minimal(tmp_path: Path) -> None:
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text("date,close\n2024-01-01,100.0\n", encoding="utf-8")

    args = DummyArgs(ticker="AAPL", csv_path=str(csv_path), initial_cash=5000.0)

    cfg = backtest_config_from_args(args)

    assert isinstance(cfg, BacktestConfig)
    assert cfg.ticker == "AAPL"
    assert cfg.csv_path == csv_path
    assert cfg.initial_cash == 5000.0
    assert cfg.start_date is None
    assert cfg.end_date is None
    assert cfg.output_path is None


def test_backtest_config_from_args_with_dates(tmp_path: Path) -> None:
    csv_path = tmp_path / "prices.csv"
    csv_path.write_text("date,close\n2024-01-01,100.0\n", encoding="utf-8")

    args = DummyArgs(
        ticker="MSFT",
        csv_path=str(csv_path),
        initial_cash=10_000.0,
        start_date="2024-01-01",
        end_date="2024-02-01",
        output_path=str(tmp_path / "summary.json"),
    )

    cfg = backtest_config_from_args(args)

    assert cfg.ticker == "MSFT"
    assert cfg.csv_path == csv_path
    assert cfg.initial_cash == 10_000.0
    assert cfg.start_date == "2024-01-01"
    assert cfg.end_date == "2024-02-01"
    assert cfg.output_path == tmp_path / "summary.json"
