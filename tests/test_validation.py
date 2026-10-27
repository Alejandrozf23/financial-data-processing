"""Unit tests for financial dataset validation."""

import numpy as np
import pandas as pd
import pytest

from financial_processing.validation import (
    DataValidationError,
    validate_required_columns,
    validate_primary_key,
    validate_not_null,
    validate_foreign_key,
    validate_positive_amounts,
    validate_dates,
    validate_datasets,
)


@pytest.fixture
def valid_datasets() -> dict[str, pd.DataFrame]:
    """Return valid synthetic financial datasets."""
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
            "transaction_date": [
                "2026-01-15",
                "2026-01-16",
                "2026-01-17",
            ],
        }),
    }


def test_valid_datasets_pass_validation(valid_datasets):
    assert validate_datasets(valid_datasets) is None


def test_missing_dataset(valid_datasets):
    del valid_datasets["products"]

    with pytest.raises(
        DataValidationError,
        match="Missing datasets",
    ):
        validate_datasets(valid_datasets)


def test_missing_required_column(valid_datasets):
    customers = valid_datasets["customers"].drop(
        columns=["region"]
    )

    with pytest.raises(
        DataValidationError,
        match="missing required columns",
    ):
        validate_required_columns(
            customers,
            {"customer_id", "segment", "region"},
            "customers",
        )


def test_null_primary_key(valid_datasets):
    valid_datasets["customers"].loc[0, "customer_id"] = None

    with pytest.raises(
        DataValidationError,
        match="null values",
    ):
        validate_datasets(valid_datasets)


def test_blank_primary_key(valid_datasets):
    valid_datasets["customers"].loc[0, "customer_id"] = "   "

    with pytest.raises(
        DataValidationError,
        match="blank values",
    ):
        validate_datasets(valid_datasets)


def test_duplicate_customer_id(valid_datasets):
    valid_datasets["customers"].loc[1, "customer_id"] = "C001"

    with pytest.raises(
        DataValidationError,
        match="duplicate 'customer_id'",
    ):
        validate_datasets(valid_datasets)


def test_duplicate_transaction_id(valid_datasets):
    valid_datasets["transactions"].loc[
        1, "transaction_id"
    ] = "T001"

    with pytest.raises(
        DataValidationError,
        match="duplicate 'transaction_id'",
    ):
        validate_datasets(valid_datasets)


def test_null_mandatory_field(valid_datasets):
    valid_datasets["customers"].loc[0, "region"] = None

    with pytest.raises(
        DataValidationError,
        match="'region' contains 1 null values",
    ):
        validate_datasets(valid_datasets)


def test_unknown_customer(valid_datasets):
    valid_datasets["transactions"].loc[
        0, "customer_id"
    ] = "C999"

    with pytest.raises(
        DataValidationError,
        match="unknown 'customer_id'",
    ):
        validate_datasets(valid_datasets)


def test_unknown_product(valid_datasets):
    valid_datasets["transactions"].loc[
        0, "product_id"
    ] = "P999"

    with pytest.raises(
        DataValidationError,
        match="unknown 'product_id'",
    ):
        validate_datasets(valid_datasets)


@pytest.mark.parametrize(
    "invalid_amount",
    [0, -100, None, np.inf, -np.inf],
)
def test_invalid_amounts(valid_datasets, invalid_amount):
    valid_datasets["transactions"].loc[
        0, "amount"
    ] = invalid_amount

    with pytest.raises(DataValidationError):
        validate_datasets(valid_datasets)


def test_non_numeric_amount(valid_datasets):
    valid_datasets["transactions"]["amount"] = [
        "12500",
        "INVALID",
        "3200",
    ]

    with pytest.raises(
        DataValidationError,
        match="non-numeric values",
    ):
        validate_datasets(valid_datasets)


def test_valid_transaction_dates(valid_datasets):
    assert validate_dates(
        valid_datasets["transactions"]
    ) is None


def test_invalid_transaction_date(valid_datasets):
    valid_datasets["transactions"].loc[
        0, "transaction_date"
    ] = "not-a-date"

    with pytest.raises(
        DataValidationError,
        match="invalid dates",
    ):
        validate_datasets(valid_datasets)


def test_optional_transaction_date(valid_datasets):
    valid_datasets["transactions"].drop(
        columns=["transaction_date"],
        inplace=True,
    )

    assert validate_datasets(valid_datasets) is None


def test_empty_valid_datasets():
    datasets = {
        "customers": pd.DataFrame(
            columns=["customer_id", "segment", "region"]
        ),
        "products": pd.DataFrame(
            columns=["product_id", "product_type"]
        ),
        "transactions": pd.DataFrame(
            columns=[
                "transaction_id",
                "customer_id",
                "product_id",
                "amount",
            ]
        ),
    }

    assert validate_datasets(datasets) is None


def test_non_dataframe_dataset(valid_datasets):
    valid_datasets["products"] = ["P001", "P002"]

    with pytest.raises(
        DataValidationError,
        match="expected a pandas DataFrame",
    ):
        validate_datasets(valid_datasets)