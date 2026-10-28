"""Entry point for the financial data processing pipeline."""

import argparse
from collections.abc import Sequence
from pathlib import Path

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
    Execute ingestion, cleaning, validation and enrichment.

    Args:
        raw_dir: Directory containing input CSV files.
        drop_exact_duplicates: Whether to remove identical rows.

    Returns:
        Row counts of the validated input datasets and enriched
        transactions.

    Raises:
        FileNotFoundError: If a source file does not exist.
        ValueError: If a dataset fails loading, cleaning,
            validation or transformation.
    """
    # PFD-02: Ingestion
    raw_datasets = load_datasets(raw_dir)

    # PFD-04: Cleaning
    cleaned_datasets, reports = clean_datasets(
        raw_datasets,
        drop_exact_duplicates=drop_exact_duplicates,
    )

    # PFD-03: Data quality validation
    validate_datasets(cleaned_datasets)

    # PFD-05: Data enrichment
    enriched_transactions = enrich_transactions(
        cleaned_datasets
    )

    print("Financial data pipeline completed successfully.")

    for name, report in reports.items():
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

    return {
        **{
            name: len(dataframe)
            for name, dataframe in cleaned_datasets.items()
        },
        "enriched_transactions": len(enriched_transactions),
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI arguments and run the financial pipeline."""
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