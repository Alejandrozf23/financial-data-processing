from pathlib import Path

import pandas as pd
import pytest

from financial_processing.ingestion import (
    DatasetPaths,
    load_csv,
    load_customers,
    load_products,
    load_transactions,
    load_datasets,
)


@pytest.fixture
def sample_raw_dir(tmp_path: Path) -> Path:
    """
    Create temporary synthetic CSV files for testing.
    """
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    (raw_dir / "customers.csv").write_text(
        "customer_id,segment,region\n"
        "C001,Premium,North\n"
        "C002,Retail,Center\n",
        encoding="utf-8",
    )

    (raw_dir / "products.csv").write_text(
        "product_id,product_type\n"
        "P001,Investment\n"
        "P002,Credit\n",
        encoding="utf-8",
    )

    (raw_dir / "transactions.csv").write_text(
        "transaction_id,customer_id,product_id,amount\n"
        "T001,C001,P001,12500.50\n"
        "T002,C002,P002,7800.00\n",
        encoding="utf-8",
    )

    return raw_dir


def test_dataset_paths_from_directory(tmp_path: Path):
    paths = DatasetPaths.from_directory(tmp_path)

    assert paths.customers == tmp_path / "customers.csv"
    assert paths.products == tmp_path / "products.csv"
    assert paths.transactions == tmp_path / "transactions.csv"


def test_load_customers(sample_raw_dir: Path):
    dataframe = load_customers(
        sample_raw_dir / "customers.csv"
    )

    assert isinstance(dataframe, pd.DataFrame)
    assert len(dataframe) == 2

    assert dataframe["customer_id"].tolist() == [
        "C001",
        "C002",
    ]

    assert pd.api.types.is_string_dtype(
        dataframe["customer_id"]
    )


def test_load_products(sample_raw_dir: Path):
    dataframe = load_products(
        sample_raw_dir / "products.csv"
    )

    assert len(dataframe) == 2

    assert dataframe["product_id"].tolist() == [
        "P001",
        "P002",
    ]

    assert "product_type" in dataframe.columns


def test_load_transactions(sample_raw_dir: Path):
    dataframe = load_transactions(
        sample_raw_dir / "transactions.csv"
    )

    assert len(dataframe) == 2

    assert dataframe["transaction_id"].tolist() == [
        "T001",
        "T002",
    ]

    assert pd.api.types.is_numeric_dtype(
        dataframe["amount"]
    )

    assert dataframe["amount"].sum() == pytest.approx(
        20300.50
    )


def test_load_datasets(sample_raw_dir: Path):
    datasets = load_datasets(sample_raw_dir)

    assert set(datasets.keys()) == {
        "customers",
        "products",
        "transactions",
    }

    assert len(datasets["customers"]) == 2
    assert len(datasets["products"]) == 2
    assert len(datasets["transactions"]) == 2


def test_missing_csv_file(tmp_path: Path):
    missing_file = tmp_path / "missing.csv"

    with pytest.raises(
        FileNotFoundError,
        match="Dataset not found",
    ):
        load_customers(missing_file)


def test_missing_required_columns(tmp_path: Path):
    invalid_file = tmp_path / "customers.csv"

    invalid_file.write_text(
        "customer_id,segment\n"
        "C001,Premium\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Missing required columns",
    ):
        load_customers(invalid_file)


def test_invalid_numeric_amount(tmp_path: Path):
    invalid_file = tmp_path / "transactions.csv"

    invalid_file.write_text(
        "transaction_id,customer_id,product_id,amount\n"
        "T001,C001,P001,INVALID\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_transactions(invalid_file)


def test_date_conversion(tmp_path: Path):
    file_path = tmp_path / "dated_transactions.csv"

    file_path.write_text(
        "transaction_id,transaction_date\n"
        "T001,2026-01-15\n",
        encoding="utf-8",
    )

    dataframe = load_csv(
        file_path=file_path,
        required_columns={
            "transaction_id",
            "transaction_date",
        },
        string_columns=["transaction_id"],
        date_columns=["transaction_date"],
    )

    assert pd.api.types.is_datetime64_any_dtype(
        dataframe["transaction_date"]
    )


def test_invalid_date(tmp_path: Path):
    file_path = tmp_path / "invalid_dates.csv"

    file_path.write_text(
        "transaction_id,transaction_date\n"
        "T001,not-a-date\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_csv(
            file_path=file_path,
            required_columns={
                "transaction_id",
                "transaction_date",
            },
            string_columns=["transaction_id"],
            date_columns=["transaction_date"],
        )