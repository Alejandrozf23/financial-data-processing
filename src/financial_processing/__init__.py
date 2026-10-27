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

from financial_processing.cleaning import (
    CleaningReport,
    DataCleaningError,
    normalize_text_columns,
    remove_exact_duplicates,
    clean_dataset,
    clean_datasets,
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
    "CleaningReport",
    "DataCleaningError",
    "normalize_text_columns",
    "remove_exact_duplicates",
    "clean_dataset",
    "clean_datasets",
]