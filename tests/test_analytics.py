"""Unit tests for Pandas financial analytics."""

import numpy as np
import pandas as pd
import pytest

from pandas.testing import assert_frame_equal

from financial_processing.analytics import (
    DataAnalyticsError,
    OverallMetrics,
    validate_analytics_input,
    calculate_customer_metrics,
    calculate_product_metrics,
    calculate_segment_metrics,
    calculate_overall_metrics,
    calculate_all_metrics,
)


@pytest.fixture
def transactions() -> pd.DataFrame:
    """Create a deterministic enriched transaction dataset."""
    return pd.DataFrame({
        "transaction_id": ["T001", "T002", "T003"],
        "customer_id": ["C001", "C001", "C002"],
        "product_id": ["P001", "P002", "P002"],
        "amount": [100.0, 200.0, 300.0],
        "segment": ["Premium", "Premium", "Retail"],
        "region": ["North", "North", "South"],
        "product_type": [
            "Investment",
            "Credit",
            "Credit",
        ],
    })


def test_valid_analytics_input(transactions):
    assert validate_analytics_input(transactions) is None


def test_customer_metrics(transactions):
    result = calculate_customer_metrics(transactions)

    assert len(result) == 2

    customer = result.set_index("customer_id")

    assert customer.loc["C001", "transaction_count"] == 2
    assert customer.loc["C001", "total_amount"] == pytest.approx(
        300.0
    )
    assert customer.loc["C001", "average_amount"] == pytest.approx(
        150.0
    )

    assert customer.loc["C002", "transaction_count"] == 1
    assert customer.loc["C002", "total_amount"] == pytest.approx(
        300.0
    )


def test_customer_metrics_include_dimensions(transactions):
    result = calculate_customer_metrics(transactions)

    customer = result.set_index("customer_id")

    assert customer.loc["C001", "segment"] == "Premium"
    assert customer.loc["C001", "region"] == "North"


def test_product_metrics(transactions):
    result = calculate_product_metrics(transactions)

    products = result.set_index("product_type")

    assert products.loc["Credit", "transaction_count"] == 2
    assert products.loc["Credit", "total_amount"] == pytest.approx(
        500.0
    )
    assert products.loc["Credit", "average_amount"] == pytest.approx(
        250.0
    )

    assert products.loc[
        "Investment", "total_amount"
    ] == pytest.approx(100.0)


def test_segment_metrics(transactions):
    result = calculate_segment_metrics(transactions)

    segments = result.set_index("segment")

    assert segments.loc["Premium", "transaction_count"] == 2
    assert segments.loc["Premium", "total_amount"] == pytest.approx(
        300.0
    )

    assert segments.loc["Retail", "transaction_count"] == 1
    assert segments.loc["Retail", "total_amount"] == pytest.approx(
        300.0
    )


def test_metrics_are_sorted_by_total_amount(transactions):
    result = calculate_product_metrics(transactions)

    assert result["product_type"].tolist() == [
        "Credit",
        "Investment",
    ]

    assert result["total_amount"].tolist() == [
        500.0,
        100.0,
    ]


def test_overall_metrics(transactions):
    result = calculate_overall_metrics(transactions)

    assert isinstance(result, OverallMetrics)
    assert result.transaction_count == 3
    assert result.unique_customers == 2
    assert result.total_amount == pytest.approx(600.0)
    assert result.average_amount == pytest.approx(200.0)


def test_calculate_all_metrics(transactions):
    reports = calculate_all_metrics(transactions)

    assert set(reports) == {
        "customers",
        "products",
        "segments",
        "overall",
    }

    assert isinstance(reports["customers"], pd.DataFrame)
    assert isinstance(reports["products"], pd.DataFrame)
    assert isinstance(reports["segments"], pd.DataFrame)
    assert isinstance(reports["overall"], OverallMetrics)

    assert reports["overall"].transaction_count == 3


def test_empty_transactions(transactions):
    empty = transactions.iloc[0:0].copy()

    result = calculate_overall_metrics(empty)

    assert result.transaction_count == 0
    assert result.unique_customers == 0
    assert result.total_amount == 0.0
    assert result.average_amount == 0.0


def test_empty_grouped_reports(transactions):
    empty = transactions.iloc[0:0].copy()

    reports = calculate_all_metrics(empty)

    assert reports["customers"].empty
    assert reports["products"].empty
    assert reports["segments"].empty


def test_missing_required_column(transactions):
    invalid = transactions.drop(columns=["segment"])

    with pytest.raises(
        DataAnalyticsError,
        match="Missing analytics columns",
    ):
        calculate_all_metrics(invalid)


def test_non_dataframe_input():
    with pytest.raises(
        DataAnalyticsError,
        match="Expected a pandas DataFrame",
    ):
        validate_analytics_input(["T001", "T002"])


def test_null_dimension_is_rejected(transactions):
    transactions.loc[0, "segment"] = None

    with pytest.raises(
        DataAnalyticsError,
        match="dimensions contain null values",
    ):
        calculate_segment_metrics(transactions)


def test_non_numeric_amount_is_rejected(transactions):
    transactions["amount"] = ["100", "INVALID", "300"]

    with pytest.raises(
        DataAnalyticsError,
        match="non-numeric values",
    ):
        calculate_overall_metrics(transactions)


@pytest.mark.parametrize(
    "invalid_amount",
    [None, np.nan, np.inf, -np.inf, 0, -100],
)
def test_invalid_amounts(transactions, invalid_amount):
    transactions["amount"] = transactions["amount"].astype(object)
    transactions.loc[0, "amount"] = invalid_amount

    with pytest.raises(DataAnalyticsError):
        calculate_overall_metrics(transactions)


def test_analytics_does_not_modify_input(transactions):
    original = transactions.copy(deep=True)

    calculate_all_metrics(transactions)

    assert_frame_equal(transactions, original)


def test_customer_metrics_include_only_active_customers(transactions):
    result = calculate_customer_metrics(transactions)

    assert set(result["customer_id"]) == {
        "C001",
        "C002",
    }


def test_average_amount_is_weighted_by_transactions(transactions):
    result = calculate_overall_metrics(transactions)

    # The global mean is based on all transactions,
    # not on an unweighted mean of customer averages.
    expected = (100.0 + 200.0 + 300.0) / 3

    assert result.average_amount == pytest.approx(expected)