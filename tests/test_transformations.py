"""Tests for financial transaction transformations."""

import pandas as pd
import pytest

from pandas.testing import assert_frame_equal

from financial_processing.transformations import (
    DataTransformationError,
    merge_customers,
    merge_products,
    enrich_transactions,
)


@pytest.fixture
def sample_datasets() -> dict[str, pd.DataFrame]:
    """Create valid synthetic datasets."""
    return {
        "customers": pd.DataFrame({
            "customer_id": ["C001", "C002", "C003"],
            "segment": ["Premium", "Retail", "Premium"],
            "region": ["North", "Center", "South"],
        }),
        "products": pd.DataFrame({
            "product_id": ["P001", "P002"],
            "product_type": ["Investment", "Credit"],
        }),
        "transactions": pd.DataFrame({
            "transaction_id": ["T001", "T002", "T003"],
            "customer_id": ["C001", "C002", "C001"],
            "product_id": ["P001", "P002", "P002"],
            "amount": [12500.50, 7800.00, 3200.00],
        }),
    }


def test_merge_customers(sample_datasets):
    result = merge_customers(
        sample_datasets["transactions"],
        sample_datasets["customers"],
    )

    assert len(result) == 3
    assert "segment" in result.columns
    assert "region" in result.columns

    assert result.loc[0, "segment"] == "Premium"
    assert result.loc[1, "region"] == "Center"


def test_merge_products(sample_datasets):
    result = merge_products(
        sample_datasets["transactions"],
        sample_datasets["products"],
    )

    assert len(result) == 3

    assert result["product_type"].tolist() == [
        "Investment",
        "Credit",
        "Credit",
    ]


def test_enrich_transactions(sample_datasets):
    result = enrich_transactions(sample_datasets)

    expected_columns = {
        "transaction_id",
        "customer_id",
        "product_id",
        "amount",
        "segment",
        "region",
        "product_type",
    }

    assert expected_columns.issubset(result.columns)
    assert len(result) == 3

    assert result.loc[0, "segment"] == "Premium"
    assert result.loc[0, "product_type"] == "Investment"


def test_transaction_order_is_preserved(sample_datasets):
    result = enrich_transactions(sample_datasets)

    assert result["transaction_id"].tolist() == [
        "T001",
        "T002",
        "T003",
    ]


def test_transaction_amounts_are_preserved(sample_datasets):
    result = enrich_transactions(sample_datasets)

    assert result["amount"].tolist() == [
        12500.50,
        7800.00,
        3200.00,
    ]


def test_inputs_are_not_modified(sample_datasets):
    originals = {
        name: dataframe.copy(deep=True)
        for name, dataframe in sample_datasets.items()
    }

    enrich_transactions(sample_datasets)

    for name, dataframe in sample_datasets.items():
        assert_frame_equal(
            dataframe,
            originals[name],
        )


def test_unknown_customer_is_rejected(sample_datasets):
    sample_datasets["transactions"].loc[
        0, "customer_id"
    ] = "C999"

    with pytest.raises(
        DataTransformationError,
        match="Unmatched keys in customers",
    ):
        enrich_transactions(sample_datasets)


def test_unknown_product_is_rejected(sample_datasets):
    sample_datasets["transactions"].loc[
        0, "product_id"
    ] = "P999"

    with pytest.raises(
        DataTransformationError,
        match="Unmatched keys in products",
    ):
        enrich_transactions(sample_datasets)


def test_duplicate_customer_key_is_rejected(sample_datasets):
    customers = sample_datasets["customers"]

    sample_datasets["customers"] = pd.concat(
        [customers, customers.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(
        DataTransformationError,
        match="duplicate merge key 'customer_id'",
    ):
        enrich_transactions(sample_datasets)


def test_duplicate_product_key_is_rejected(sample_datasets):
    products = sample_datasets["products"]

    sample_datasets["products"] = pd.concat(
        [products, products.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(
        DataTransformationError,
        match="duplicate merge key 'product_id'",
    ):
        enrich_transactions(sample_datasets)


def test_null_merge_key_is_rejected(sample_datasets):
    sample_datasets["transactions"].loc[
        0, "customer_id"
    ] = None

    with pytest.raises(
        DataTransformationError,
        match="Null merge key",
    ):
        enrich_transactions(sample_datasets)


def test_missing_dataset_is_rejected(sample_datasets):
    del sample_datasets["products"]

    with pytest.raises(
        DataTransformationError,
        match="Missing datasets",
    ):
        enrich_transactions(sample_datasets)


def test_missing_customer_column_is_rejected(sample_datasets):
    sample_datasets["customers"] = (
        sample_datasets["customers"].drop(
            columns=["segment"]
        )
    )

    with pytest.raises(
        DataTransformationError,
        match="missing columns",
    ):
        enrich_transactions(sample_datasets)


def test_existing_column_collision_is_rejected(sample_datasets):
    sample_datasets["transactions"]["segment"] = "Existing"

    with pytest.raises(
        DataTransformationError,
        match="Column collision",
    ):
        enrich_transactions(sample_datasets)


def test_empty_transactions_are_supported(sample_datasets):
    sample_datasets["transactions"] = (
        sample_datasets["transactions"].iloc[0:0].copy()
    )

    result = enrich_transactions(sample_datasets)

    assert result.empty
    assert "segment" in result.columns
    assert "product_type" in result.columns


def test_enrichment_preserves_optional_date(sample_datasets):
    sample_datasets["transactions"]["transaction_date"] = (
        pd.to_datetime([
            "2026-01-15",
            "2026-01-16",
            "2026-01-17",
        ])
    )

    result = enrich_transactions(sample_datasets)

    assert "transaction_date" in result.columns
    assert pd.api.types.is_datetime64_any_dtype(
        result["transaction_date"]
    )