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

from financial_processing.transformations import (
    DataTransformationError,
    merge_customers,
    merge_products,
    enrich_transactions,
)

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
    "DataAnalyticsError",
    "OverallMetrics",
    "validate_analytics_input",
    "calculate_customer_metrics",
    "calculate_product_metrics",
    "calculate_segment_metrics",
    "calculate_overall_metrics",
    "calculate_all_metrics",
]