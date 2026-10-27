"""Conservative cleaning utilities for financial datasets."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import pandas as pd


TEXT_COLUMNS = {
    "customers": ("customer_id", "segment", "region"),
    "products": ("product_id", "product_type"),
    "transactions": (
        "transaction_id",
        "customer_id",
        "product_id",
    ),
}


class DataCleaningError(ValueError):
    """Raised when a cleaning operation cannot be performed safely."""


@dataclass(frozen=True)
class CleaningReport:
    """Summary of cleaning changes for one dataset."""

    dataset_name: str
    input_rows: int
    output_rows: int
    duplicates_removed: int


def normalize_text_columns(
    dataframe: pd.DataFrame,
    columns: Sequence[str],
) -> pd.DataFrame:
    """
    Strip surrounding whitespace and convert blank strings to null.

    The original DataFrame is never modified.
    """
    missing = set(columns) - set(dataframe.columns)

    if missing:
        raise DataCleaningError(
            f"Missing text columns: {sorted(missing)}"
        )

    result = dataframe.copy()

    for column in columns:
        values = result[column]

        # Reject structured or numeric values rather than
        # silently converting them to arbitrary strings.
        invalid_types = values.map(
            lambda value: (
                not pd.isna(value)
                and not isinstance(value, str)
            )
        )

        if invalid_types.any():
            raise DataCleaningError(
                f"Column '{column}' contains non-string values"
            )

        normalized = values.astype("string").str.strip()

        result[column] = normalized.mask(
            normalized.eq(""),
            pd.NA,
        )

    return result


def remove_exact_duplicates(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    """
    Remove fully identical rows.

    This operation must be explicitly requested by the caller.
    It does not remove rows merely because they share an ID.
    """
    result = dataframe.drop_duplicates(
        keep="first"
    ).copy()

    removed = len(dataframe) - len(result)

    return result.reset_index(drop=True), removed


def clean_dataset(
    dataframe: pd.DataFrame,
    dataset_name: str,
    *,
    drop_exact_duplicates: bool = False,
) -> tuple[pd.DataFrame, CleaningReport]:
    """
    Clean a known financial dataset and return an audit report.

    By default, no rows are removed.
    """
    if dataset_name not in TEXT_COLUMNS:
        raise DataCleaningError(
            f"Unknown dataset: {dataset_name}"
        )

    if not isinstance(dataframe, pd.DataFrame):
        raise DataCleaningError(
            f"{dataset_name}: expected a pandas DataFrame"
        )

    result = normalize_text_columns(
        dataframe,
        TEXT_COLUMNS[dataset_name],
    )

    removed = 0

    if drop_exact_duplicates:
        result, removed = remove_exact_duplicates(
            result
        )

    report = CleaningReport(
        dataset_name=dataset_name,
        input_rows=len(dataframe),
        output_rows=len(result),
        duplicates_removed=removed,
    )

    return result, report


def clean_datasets(
    datasets: Mapping[str, pd.DataFrame],
    *,
    drop_exact_duplicates: bool = False,
) -> tuple[
    dict[str, pd.DataFrame],
    dict[str, CleaningReport],
]:
    """
    Clean customers, products and transactions independently.

    Returns cleaned copies and a report for every dataset.
    """
    missing = TEXT_COLUMNS.keys() - datasets.keys()

    if missing:
        raise DataCleaningError(
            f"Missing datasets: {sorted(missing)}"
        )

    cleaned = {}
    reports = {}

    for name in TEXT_COLUMNS:
        dataframe, report = clean_dataset(
            datasets[name],
            name,
            drop_exact_duplicates=drop_exact_duplicates,
        )

        cleaned[name] = dataframe
        reports[name] = report

    return cleaned, reports