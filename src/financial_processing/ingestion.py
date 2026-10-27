from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class DatasetPaths:
    customers: Path
    products: Path
    transactions: Path

    @classmethod
    def from_directory(cls, raw_dir: str | Path) -> "DatasetPaths":
        directory = Path(raw_dir)

        return cls(
            customers=directory / "customers.csv",
            products=directory / "products.csv",
            transactions=directory / "transactions.csv",
        )


def load_csv(
    file_path: str | Path,
    required_columns: set[str],
    string_columns: list[str],
    date_columns: list[str] | None = None,
    numeric_columns: list[str] | None = None,
) -> pd.DataFrame:
    """
    Read a CSV file into a DataFrame with explicit type conversion.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns or convertible values are invalid.
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    dataframe = pd.read_csv(
        path,
        dtype={column: "string" for column in string_columns},
    )

    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns in {path.name}: "
            f"{sorted(missing_columns)}"
        )

    for column in date_columns or []:
        dataframe[column] = pd.to_datetime(
            dataframe[column],
            errors="raise",
        )

    for column in numeric_columns or []:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="raise",
        )

    return dataframe


def load_customers(file_path: str | Path) -> pd.DataFrame:
    return load_csv(
        file_path=file_path,
        required_columns={
            "customer_id",
            "segment",
            "region",
        },
        string_columns=[
            "customer_id",
            "segment",
            "region",
        ],
    )


def load_products(file_path: str | Path) -> pd.DataFrame:
    return load_csv(
        file_path=file_path,
        required_columns={
            "product_id",
            "product_type",
        },
        string_columns=[
            "product_id",
            "product_type",
        ],
    )


def load_transactions(file_path: str | Path) -> pd.DataFrame:
    return load_csv(
        file_path=file_path,
        required_columns={
            "transaction_id",
            "customer_id",
            "product_id",
            "amount",
        },
        string_columns=[
            "transaction_id",
            "customer_id",
            "product_id",
        ],
        numeric_columns=[
            "amount",
        ],
    )


def load_datasets(raw_dir: str | Path) -> dict[str, pd.DataFrame]:
    """
    Load all three financial datasets from the raw data directory.
    """
    paths = DatasetPaths.from_directory(raw_dir)

    return {
        "customers": load_customers(paths.customers),
        "products": load_products(paths.products),
        "transactions": load_transactions(paths.transactions),
    }