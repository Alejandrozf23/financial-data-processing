"""Financial data processing package."""

from financial_processing.ingestion import (
    DatasetPaths,
    load_csv,
    load_customers,
    load_products,
    load_transactions,
    load_datasets,
)

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

__all__ = [
    "DatasetPaths",
    "load_csv",
    "load_customers",
    "load_products",
    "load_transactions",
    "load_datasets",
    "DataValidationError",
    "validate_required_columns",
    "validate_primary_key",
    "validate_not_null",
    "validate_foreign_key",
    "validate_positive_amounts",
    "validate_dates",
    "validate_datasets",
]