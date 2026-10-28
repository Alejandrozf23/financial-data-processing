"""Financial analytics using Pandas aggregations."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


class DataAnalyticsError(ValueError):
    """Raised when financial analytics cannot be calculated safely."""


@dataclass(frozen=True)
class OverallMetrics:
    """Summary metrics for a collection of transactions."""

    transaction_count: int
    unique_customers: int
    total_amount: float
    average_amount: float


REQUIRED_COLUMNS = {
    "transaction_id",
    "customer_id",
    "product_id",
    "amount",
    "segment",
    "region",
    "product_type",
}


def validate_analytics_input(
    dataframe: pd.DataFrame,
) -> None:
    """Check the enriched dataset before computing analytics."""
    if not isinstance(dataframe, pd.DataFrame):
        raise DataAnalyticsError(
            "Expected a pandas DataFrame"
        )

    missing = REQUIRED_COLUMNS - set(dataframe.columns)

    if missing:
        raise DataAnalyticsError(
            f"Missing analytics columns: {sorted(missing)}"
        )

    if dataframe.empty:
        return

    required_dimensions = REQUIRED_COLUMNS - {"amount"}

    if dataframe[list(required_dimensions)].isna().any().any():
        raise DataAnalyticsError(
            "Analytics dimensions contain null values"
        )

    try:
        numeric = pd.to_numeric(
            dataframe["amount"],
            errors="raise",
        )
    except (ValueError, TypeError) as exc:
        raise DataAnalyticsError(
            "Amount contains non-numeric values"
        ) from exc

    if numeric.isna().any():
        raise DataAnalyticsError(
            "Amount contains null values"
        )

    if not np.isfinite(
        numeric.to_numpy(dtype=float)
    ).all():
        raise DataAnalyticsError(
            "Amount contains non-finite values"
        )

    if (numeric <= 0).any():
        raise DataAnalyticsError(
            "Amount must be greater than zero"
        )


def _aggregate_by(
    dataframe: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:
    """Calculate transaction metrics for selected dimensions."""
    grouped = (
        dataframe.groupby(
            group_columns,
            dropna=False,
            sort=True,
            observed=True,
        )
        .agg(
            transaction_count=(
                "transaction_id",
                "count",
            ),
            total_amount=(
                "amount",
                "sum",
            ),
            average_amount=(
                "amount",
                "mean",
            ),
        )
        .reset_index()
    )

    return grouped.sort_values(
        by=["total_amount", *group_columns],
        ascending=[False] + [True] * len(group_columns),
        kind="stable",
    ).reset_index(drop=True)


def calculate_customer_metrics(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate activity and amounts by customer.

    Returns:
        customer_id, segment, region, transaction_count,
        total_amount and average_amount.
    """
    validate_analytics_input(dataframe)

    return _aggregate_by(
        dataframe,
        ["customer_id", "segment", "region"],
    )


def calculate_product_metrics(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate transaction metrics by product type."""
    validate_analytics_input(dataframe)

    return _aggregate_by(
        dataframe,
        ["product_type"],
    )


def calculate_segment_metrics(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate transaction metrics by customer segment."""
    validate_analytics_input(dataframe)

    return _aggregate_by(
        dataframe,
        ["segment"],
    )


def calculate_overall_metrics(
    dataframe: pd.DataFrame,
) -> OverallMetrics:
    """Calculate overall indicators without modifying the input."""
    validate_analytics_input(dataframe)

    if dataframe.empty:
        return OverallMetrics(
            transaction_count=0,
            unique_customers=0,
            total_amount=0.0,
            average_amount=0.0,
        )

    return OverallMetrics(
        transaction_count=len(dataframe),
        unique_customers=int(
            dataframe["customer_id"].nunique()
        ),
        total_amount=float(
            dataframe["amount"].sum()
        ),
        average_amount=float(
            dataframe["amount"].mean()
        ),
    )


def calculate_all_metrics(
    dataframe: pd.DataFrame,
) -> dict[str, pd.DataFrame | OverallMetrics]:
    """Build all financial analytics reports."""
    validate_analytics_input(dataframe)

    return {
        "customers": calculate_customer_metrics(dataframe),
        "products": calculate_product_metrics(dataframe),
        "segments": calculate_segment_metrics(dataframe),
        "overall": calculate_overall_metrics(dataframe),
    }