"""Entry point for the financial data processing pipeline."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from financial_processing.analytics import calculate_all_metrics
from financial_processing.cleaning import clean_datasets
from financial_processing.export import export_pipeline_results
from financial_processing.ingestion import load_datasets
from financial_processing.transformations import enrich_transactions
from financial_processing.validation import validate_datasets


def run_pipeline(
    raw_dir: str | Path,
    *,
    drop_exact_duplicates: bool = False,
    output_dir: str | Path | None = None,
) -> dict[str, int]:
    """
    Execute the financial data processing pipeline.

    Stages:
        1. CSV ingestion
        2. Data cleaning
        3. Data validation
        4. Transaction enrichment
        5. Financial analytics
        6. Optional CSV, Parquet and JSON export

    Args:
        raw_dir: Directory containing input datasets.
        drop_exact_duplicates: Remove fully identical rows.
        output_dir: Optional export destination.

    Returns:
        Row counts for the processed datasets.
    """
    # PFD-02: Ingestion
    raw_datasets = load_datasets(raw_dir)

    # PFD-04: Cleaning
    cleaned_datasets, cleaning_reports = clean_datasets(
        raw_datasets,
        drop_exact_duplicates=drop_exact_duplicates,
    )

    # PFD-03: Validation
    validate_datasets(cleaned_datasets)

    # PFD-05: Transformations
    enriched_transactions = enrich_transactions(
        cleaned_datasets
    )

    # PFD-06: Analytics
    analytics_reports = calculate_all_metrics(
        enriched_transactions
    )

    overall = analytics_reports["overall"]

    # PFD-07: Optional export
    export_report = None

    if output_dir is not None:
        export_report = export_pipeline_results(
            enriched_transactions,
            analytics_reports,
            output_dir,
        )

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

    if export_report is not None:
        print(
            f"Export completed: {len(export_report.files)} files"
        )
        print(
            f"Output directory: {export_report.output_directory}"
        )

        for file_path in export_report.files:
            print(f"  {file_path.name}")

    return {
        **{
            name: len(dataframe)
            for name, dataframe in cleaned_datasets.items()
        },
        "enriched_transactions": len(enriched_transactions),
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and execute the pipeline."""
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
        help="Remove identical rows before validation.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for CSV, Parquet and JSON exports.",
    )

    args = parser.parse_args(argv)

    run_pipeline(
        args.raw_dir,
        drop_exact_duplicates=args.drop_exact_duplicates,
        output_dir=args.output_dir,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())