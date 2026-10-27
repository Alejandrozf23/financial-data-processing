"""Entry point for the financial data processing pipeline."""

import argparse
from collections.abc import Sequence
from pathlib import Path

from financial_processing.cleaning import clean_datasets
from financial_processing.ingestion import load_datasets
from financial_processing.validation import validate_datasets


def run_pipeline(
    raw_dir: str | Path,
    *,
    drop_exact_duplicates: bool = False,
) -> dict[str, int]:
    """
    Execute the ingestion, cleaning and validation pipeline.

    Args:
        raw_dir: Directory containing the input CSV files.
        drop_exact_duplicates: Remove identical rows when True.

    Returns:
        Dictionary containing the validated row count per dataset.

    Raises:
        FileNotFoundError: If an input CSV file is missing.
        ValueError: If ingestion, cleaning or validation fails.
    """
    # PFD-02: Read input CSV files.
    datasets = load_datasets(raw_dir)

    # PFD-04: Clean data without mutating the original frames.
    cleaned_datasets, reports = clean_datasets(
        datasets,
        drop_exact_duplicates=drop_exact_duplicates,
    )

    # PFD-03: Check business rules and referential integrity.
    validate_datasets(cleaned_datasets)

    # Report successful results only after validation.
    print("Financial data pipeline completed successfully.")

    for name, report in reports.items():
        print(
            f"{name}: "
            f"input={report.input_rows}, "
            f"output={report.output_rows}, "
            f"duplicates_removed={report.duplicates_removed}"
        )

    return {
        name: len(dataframe)
        for name, dataframe in cleaned_datasets.items()
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Parse command-line arguments and execute the pipeline."""
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