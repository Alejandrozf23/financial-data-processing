"""Financial transaction enrichment using Pandas."""

from collections.abc import Mapping

import pandas as pd
from pandas.errors import MergeError


class DataTransformationError(ValueError):
    """Raised when a financial data transformation fails."""


CUSTOMER_COLUMNS = (
    "customer_id",
    "segment",
    "region",
)

PRODUCT_COLUMNS = (
    "product_id",
    "product_type",
)

TRANSACTION_COLUMNS = (
    "transaction_id",
    "customer_id",
    "product_id",
    "amount",
)


def _require_columns(
    dataframe: pd.DataFrame,
    columns: tuple[str, ...],
    dataset_name: str,
) -> None:
    """Verify the presence of required columns."""
    if not isinstance(dataframe, pd.DataFrame):
        raise DataTransformationError(
            f"{dataset_name}: expected a pandas DataFrame"
        )

    missing = set(columns) - set(dataframe.columns)

    if missing:
        raise DataTransformationError(
            f"{dataset_name}: missing columns: {sorted(missing)}"
        )


def _merge_many_to_one(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    key: str,
    right_columns: tuple[str, ...],
    right_name: str,
) -> pd.DataFrame:
    """Perform a controlled many-to-one enrichment."""
    _require_columns(left, (key,), "transactions")
    _require_columns(right, right_columns, right_name)

    # Avoid silent column collisions before merging.
    additional_columns = set(right_columns) - {key}
    collisions = additional_columns & set(left.columns)

    if collisions:
        raise DataTransformationError(
            f"Column collision with {right_name}: "
            f"{sorted(collisions)}"
        )

    # Prevent Pandas from matching null keys together.
    if left[key].isna().any() or right[key].isna().any():
        raise DataTransformationError(
            f"Null merge key detected: '{key}'"
        )

    if right[key].duplicated().any():
        raise DataTransformationError(
            f"{right_name}: duplicate merge key '{key}'"
        )

    try:
        merged = left.merge(
            right.loc[:, list(right_columns)],
            on=key,
            how="left",
            validate="many_to_one",
            indicator=True,
            sort=False,
        )
    except (MergeError, ValueError) as exc:
        raise DataTransformationError(
            f"Failed to merge {right_name}: {exc}"
        ) from exc

    unmatched = merged["_merge"].ne("both")

    if unmatched.any():
        missing_keys = (
            merged.loc[unmatched, key]
            .drop_duplicates()
            .tolist()
        )

        raise DataTransformationError(
            f"Unmatched keys in {right_name}: {missing_keys}"
        )

    merged = merged.drop(columns=["_merge"])

    if len(merged) != len(left):
        raise DataTransformationError(
            f"Unexpected row count after merging {right_name}"
        )

    return merged.reset_index(drop=True)


def merge_customers(
    transactions: pd.DataFrame,
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """Add customer segment and region to transactions."""
    _require_columns(
        transactions,
        TRANSACTION_COLUMNS,
        "transactions",
    )

    return _merge_many_to_one(
        transactions,
        customers,
        key="customer_id",
        right_columns=CUSTOMER_COLUMNS,
        right_name="customers",
    )


def merge_products(
    transactions: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Add product classification to transactions."""
    _require_columns(
        transactions,
        TRANSACTION_COLUMNS,
        "transactions",
    )

    return _merge_many_to_one(
        transactions,
        products,
        key="product_id",
        right_columns=PRODUCT_COLUMNS,
        right_name="products",
    )


def enrich_transactions(
    datasets: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Enrich validated transactions with customer and product data.

    The input DataFrames are never mutated.
    """
    required_datasets = {
        "customers",
        "products",
        "transactions",
    }

    missing = required_datasets - set(datasets)

    if missing:
        raise DataTransformationError(
            f"Missing datasets: {sorted(missing)}"
        )

    transactions = datasets["transactions"]
    customers = datasets["customers"]
    products = datasets["products"]

    with_customers = merge_customers(
        transactions,
        customers,
    )

    enriched = merge_products(
        with_customers,
        products,
    )

    return enriched