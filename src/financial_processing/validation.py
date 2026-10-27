"""Data quality and integrity validation for financial datasets."""

from collections.abc import Mapping
from datetime import datetime

import numpy as np
import pandas as pd


class DataValidationError(ValueError):
    """Raised when a dataset violates a data quality rule."""


REQUIRED_COLUMNS = {
    "customers": {"customer_id", "segment", "region"},
    "products": {"product_id", "product_type"},
    "transactions": {
        "transaction_id",
        "customer_id",
        "product_id",
        "amount",
    },
}


def validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: set[str],
    dataset_name: str,
) -> None:
    """Verify that the dataset contains its mandatory columns."""
    missing = required_columns - set(dataframe.columns)

    if missing:
        raise DataValidationError(
            f"{dataset_name}: missing required columns: {sorted(missing)}"
        )


def validate_primary_key(
    dataframe: pd.DataFrame,
    column: str,
    dataset_name: str,
) -> None:
    """Reject null, blank and duplicate primary key values."""
    validate_required_columns(dataframe, {column}, dataset_name)

    values = dataframe[column]

    null_mask = values.isna()
    if null_mask.any():
        raise DataValidationError(
            f"{dataset_name}: '{column}' contains "
            f"{int(null_mask.sum())} null values"
        )

    blank_mask = values.astype("string").str.strip().eq("").fillna(False)
    if blank_mask.any():
        raise DataValidationError(
            f"{dataset_name}: '{column}' contains blank values"
        )

    duplicate_mask = values.duplicated(keep=False)

    if duplicate_mask.any():
        duplicates = values[duplicate_mask].unique().tolist()
        raise DataValidationError(
            f"{dataset_name}: duplicate '{column}' values: {duplicates}"
        )


def validate_not_null(
    dataframe: pd.DataFrame,
    columns: set[str],
    dataset_name: str,
) -> None:
    """Reject missing values in mandatory fields."""
    validate_required_columns(dataframe, columns, dataset_name)

    for column in sorted(columns):
        null_count = int(dataframe[column].isna().sum())

        if null_count:
            raise DataValidationError(
                f"{dataset_name}: '{column}' contains "
                f"{null_count} null values"
            )


def validate_foreign_key(
    child: pd.DataFrame,
    parent: pd.DataFrame,
    column: str,
    child_name: str,
    parent_name: str,
) -> None:
    """Verify that every child key exists in its parent dataset."""
    validate_required_columns(child, {column}, child_name)
    validate_required_columns(parent, {column}, parent_name)

    invalid_mask = (
        child[column].notna()
        & ~child[column].isin(parent[column])
    )

    if invalid_mask.any():
        invalid_values = (
            child.loc[invalid_mask, column]
            .drop_duplicates()
            .tolist()
        )

        raise DataValidationError(
            f"{child_name}: unknown '{column}' values "
            f"not found in {parent_name}: {invalid_values}"
        )


def validate_positive_amounts(
    dataframe: pd.DataFrame,
    column: str = "amount",
) -> None:
    """Require finite, strictly positive numeric amounts."""
    validate_required_columns(
        dataframe, {column}, "transactions"
    )

    values = dataframe[column]

    # Reject missing values and non-numeric content.
    try:
        numeric = pd.to_numeric(values, errors="raise")
    except (ValueError, TypeError) as exc:
        raise DataValidationError(
            f"transactions: '{column}' contains non-numeric values"
        ) from exc

    if numeric.isna().any():
        raise DataValidationError(
            f"transactions: '{column}' contains null values"
        )

    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise DataValidationError(
            f"transactions: '{column}' contains infinite values"
        )

    if (numeric <= 0).any():
        raise DataValidationError(
            f"transactions: '{column}' must be greater than zero"
        )


def validate_dates(
    dataframe: pd.DataFrame,
    column: str = "transaction_date",
) -> None:
    """Validate an optional transaction date column."""
    if column not in dataframe.columns:
        return

    try:
        parsed = pd.to_datetime(
            dataframe[column],
            errors="raise",
            format="mixed",
        )
    except (ValueError, TypeError, OverflowError) as exc:
        raise DataValidationError(
            f"transactions: '{column}' contains invalid dates"
        ) from exc

    if parsed.isna().any():
        raise DataValidationError(
            f"transactions: '{column}' contains null dates"
        )


def validate_datasets(
    datasets: Mapping[str, pd.DataFrame],
) -> None:
    """
    Validate schema, primary keys, amounts and referential integrity.

    Raises:
        DataValidationError: On the first detected quality violation.
    """
    missing_datasets = REQUIRED_COLUMNS.keys() - datasets.keys()

    if missing_datasets:
        raise DataValidationError(
            f"Missing datasets: {sorted(missing_datasets)}"
        )

    for name, required_columns in REQUIRED_COLUMNS.items():
        dataframe = datasets[name]

        if not isinstance(dataframe, pd.DataFrame):
            raise DataValidationError(
                f"{name}: expected a pandas DataFrame"
            )

        validate_required_columns(
            dataframe,
            required_columns,
            name,
        )

    customers = datasets["customers"]
    products = datasets["products"]
    transactions = datasets["transactions"]

    validate_primary_key(
        customers, "customer_id", "customers"
    )
    validate_primary_key(
        products, "product_id", "products"
    )
    validate_primary_key(
        transactions, "transaction_id", "transactions"
    )

    validate_not_null(
        customers, {"segment", "region"}, "customers"
    )
    validate_not_null(
        products, {"product_type"}, "products"
    )
    validate_not_null(
        transactions,
        {"customer_id", "product_id"},
        "transactions",
    )

    validate_positive_amounts(transactions)
    validate_dates(transactions)

    validate_foreign_key(
        transactions,
        customers,
        "customer_id",
        "transactions",
        "customers",
    )
    validate_foreign_key(
        transactions,
        products,
        "product_id",
        "transactions",
        "products",
    )