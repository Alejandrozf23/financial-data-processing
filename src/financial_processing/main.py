"""Entry point for the financial data processing pipeline."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from financial_processing.analytics import calculate_all_metrics
from financial_processing.cleaning import clean_datasets
from financial_processing.ingestion import load_datasets
from financial_processing.transformations import enrich_transactions
from financial_processing.validation import validate_datasets


def run_pipeline(
    raw_dir: str | Path,
    *,
    drop_exact_duplicates: bool = False,
) -> dict[str, int]:
    """
    Run ingestion, cleaning, validation, enrichment and analytics.

    Args:
        raw_dir: Directory containing input CSV files.
        drop_exact_duplicates: Remove fully identical records
            before validation when explicitly enabled.

    Returns:
        Row counts for validated datasets and enriched transactions.

    Raises:
        FileNotFoundError: When an input CSV is missing.
        ValueError: When an operation rejects invalid data.
    """
    # PFD-02: Read source CSV files.
    raw_datasets = load_datasets(raw_dir)

    # PFD-04: Normalize text and optionally remove exact duplicates.
    cleaned_datasets, cleaning_reports = clean_datasets(
        raw_datasets,
        drop_exact_duplicates=drop_exact_duplicates,
    )

    # PFD-03: Validate schemas, keys, amounts and relationships.
    validate_datasets(cleaned_datasets)

    # PFD-05: Enrich transactions using controlled Pandas joins.
    enriched_transactions = enrich_transactions(
        cleaned_datasets
    )

    # PFD-06: Calculate financial metrics.
    analytics_reports = calculate_all_metrics(
        enriched_transactions
    )

    overall = analytics_reports["overall"]

    print("Financial data pipeline completed successfully.")

    for name, report in cleaning_reports.items():
        print(
            f"{name}: "
            f"input={report.input_rows}, "
            f"output={report.output_rows}, "
            f"duplicates_removed={report.duplicates_removed}"
        )

    print(
        "enriched_transactions: "
        f"rows={len(enriched_transactions)}, "
        f"columns={len(enriched_transactions.columns)}"
    )

    print("Financial analytics:")
    print(f"  transaction_count={overall.transaction_count}")
    print(f"  unique_customers={overall.unique_customers}")
    print(f"  total_amount={overall.total_amount:.2f}")
    print(f"  average_amount={overall.average_amount:.2f}")

    return {
        **{
            name: len(dataframe)
            for name, dataframe in cleaned_datasets.items()
        },
        "enriched_transactions": len(enriched_transactions),
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI arguments and execute the pipeline."""
    parser = argparse.ArgumentParser(
        description="Financial data processing pipeline"
    )

    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory containing input CSV datasets.",
    )

    parser.add_argument(
        "--drop-exact-duplicates",
        action="store_true",
        help="Remove fully identical rows before validation.",
    )

    args = parser.parse_args(argv)

    run_pipeline(
        args.raw_dir,
        drop_exact_duplicates=args.drop_exact_duplicates,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())