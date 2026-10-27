"""Unit tests for financial data cleaning."""

import pandas as pd
import pytest

from pandas.testing import assert_frame_equal

from financial_processing.cleaning import (
    CleaningReport,
    DataCleaningError,
    clean_dataset,
    clean_datasets,
    normalize_text_columns,
    remove_exact_duplicates,
)


@pytest.fixture
def sample_datasets() -> dict[str, pd.DataFrame]:
    return {
        "customers": pd.DataFrame({
            "customer_id": [" C001 ", "C002"],
            "segment": [" Premium ", "Retail"],
            "region": [" North ", "South"],
        }),
        "products": pd.DataFrame({
            "product_id": [" P001 ", "P002"],
            "product_type": [" Investment ", "Credit"],
        }),
        "transactions": pd.DataFrame({
            "transaction_id": [" T001 ", "T002"],
            "customer_id": [" C001 ", "C002"],
            "product_id": [" P001 ", "P002"],
            "amount": [12500.50, 7800.00],
        }),
    }


def test_strip_surrounding_whitespace():
    dataframe = pd.DataFrame({
        "customer_id": [" C001 ", " C002  "],
    })

    result = normalize_text_columns(
        dataframe,
        ["customer_id"],
    )

    assert result["customer_id"].tolist() == [
        "C001",
        "C002",
    ]


def test_blank_strings_become_null():
    dataframe = pd.DataFrame({
        "region": ["  ", "", "North"],
    })

    result = normalize_text_columns(
        dataframe,
        ["region"],
    )

    assert pd.isna(result.loc[0, "region"])
    assert pd.isna(result.loc[1, "region"])
    assert result.loc[2, "region"] == "North"


def test_existing_null_is_preserved():
    dataframe = pd.DataFrame({
        "region": [None, "South"],
    })

    result = normalize_text_columns(
        dataframe,
        ["region"],
    )

    assert pd.isna(result.loc[0, "region"])
    assert result.loc[1, "region"] == "South"


def test_original_dataframe_is_not_modified():
    dataframe = pd.DataFrame({
        "customer_id": [" C001 "],
    })

    original = dataframe.copy(deep=True)

    result = normalize_text_columns(
        dataframe,
        ["customer_id"],
    )

    assert_frame_equal(dataframe, original)
    assert result.loc[0, "customer_id"] == "C001"


def test_missing_text_column():
    dataframe = pd.DataFrame({
        "customer_id": ["C001"],
    })

    with pytest.raises(
        DataCleaningError,
        match="Missing text columns",
    ):
        normalize_text_columns(
            dataframe,
            ["region"],
        )


def test_non_string_value_is_rejected():
    dataframe = pd.DataFrame({
        "customer_id": ["C001", 123],
    })

    with pytest.raises(
        DataCleaningError,
        match="non-string values",
    ):
        normalize_text_columns(
            dataframe,
            ["customer_id"],
        )


def test_exact_duplicates_are_removed():
    dataframe = pd.DataFrame({
        "transaction_id": ["T001", "T001", "T002"],
        "amount": [100.0, 100.0, 200.0],
    })

    result, removed = remove_exact_duplicates(
        dataframe
    )

    assert len(result) == 2
    assert removed == 1
    assert result["transaction_id"].tolist() == [
        "T001",
        "T002",
    ]


def test_conflicting_duplicates_are_preserved():
    dataframe = pd.DataFrame({
        "transaction_id": ["T001", "T001"],
        "amount": [100.0, 200.0],
    })

    result, removed = remove_exact_duplicates(
        dataframe
    )

    assert len(result) == 2
    assert removed == 0


def test_duplicates_are_preserved_by_default():
    dataframe = pd.DataFrame({
        "customer_id": ["C001", "C001"],
        "segment": ["Premium", "Premium"],
        "region": ["North", "North"],
    })

    result, report = clean_dataset(
        dataframe,
        "customers",
    )

    assert len(result) == 2
    assert report.duplicates_removed == 0


def test_explicit_duplicate_removal():
    dataframe = pd.DataFrame({
        "customer_id": [" C001 ", "C001"],
        "segment": ["Premium", "Premium"],
        "region": ["North", "North"],
    })

    result, report = clean_dataset(
        dataframe,
        "customers",
        drop_exact_duplicates=True,
    )

    assert len(result) == 1
    assert report.input_rows == 2
    assert report.output_rows == 1
    assert report.duplicates_removed == 1


def test_unknown_dataset():
    dataframe = pd.DataFrame({
        "customer_id": ["C001"],
    })

    with pytest.raises(
        DataCleaningError,
        match="Unknown dataset",
    ):
        clean_dataset(
            dataframe,
            "unknown",
        )


def test_invalid_dataset_type():
    with pytest.raises(
        DataCleaningError,
        match="expected a pandas DataFrame",
    ):
        clean_dataset(
            ["C001"],
            "customers",
        )


def test_clean_datasets(sample_datasets):
    cleaned, reports = clean_datasets(
        sample_datasets
    )

    assert set(cleaned) == {
        "customers",
        "products",
        "transactions",
    }

    assert cleaned["customers"].loc[
        0, "customer_id"
    ] == "C001"

    assert cleaned["products"].loc[
        0, "product_id"
    ] == "P001"

    assert cleaned["transactions"].loc[
        0, "transaction_id"
    ] == "T001"

    assert isinstance(
        reports["customers"],
        CleaningReport,
    )


def test_clean_datasets_missing_dataset(sample_datasets):
    del sample_datasets["products"]

    with pytest.raises(
        DataCleaningError,
        match="Missing datasets",
    ):
        clean_datasets(sample_datasets)


def test_numeric_columns_are_not_modified(sample_datasets):
    original_amounts = (
        sample_datasets["transactions"]["amount"].copy()
    )

    cleaned, _ = clean_datasets(sample_datasets)

    pd.testing.assert_series_equal(
        cleaned["transactions"]["amount"],
        original_amounts,
    )


def test_clean_datasets_preserves_originals(sample_datasets):
    originals = {
        name: dataframe.copy(deep=True)
        for name, dataframe in sample_datasets.items()
    }

    clean_datasets(sample_datasets)

    for name in sample_datasets:
        assert_frame_equal(
            sample_datasets[name],
            originals[name],
        )