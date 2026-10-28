"""Export financial processing results to CSV, Parquet and JSON."""

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from financial_processing.analytics import OverallMetrics


class DataExportError(ValueError):
    """Raised when financial data export cannot be completed."""


@dataclass(frozen=True)
class ExportReport:
    """Summary of generated output artifacts."""

    output_directory: Path
    files: tuple[Path, ...]


REPORT_NAMES = (
    "customer_metrics",
    "product_metrics",
    "segment_metrics",
)

REPORT_KEYS = {
    "customer_metrics": "customers",
    "product_metrics": "products",
    "segment_metrics": "segments",
}


def prepare_output_directory(
    output_dir: str | Path,
) -> Path:
    """Create the destination directory when necessary."""
    directory = Path(output_dir)

    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DataExportError(
            f"Cannot create output directory: {directory}"
        ) from exc

    if not directory.is_dir():
        raise DataExportError(
            f"Output path is not a directory: {directory}"
        )

    return directory


def export_dataframe(
    dataframe: pd.DataFrame,
    output_dir: str | Path,
    filename: str,
) -> tuple[Path, Path]:
    """
    Export a DataFrame to CSV and Parquet.

    DataFrame indexes are excluded from both formats.
    """
    if not isinstance(dataframe, pd.DataFrame):
        raise DataExportError(
            "Expected a pandas DataFrame"
        )

    if (
        not filename
        or filename in {".", ".."}
        or Path(filename).name != filename
        or "/" in filename
        or "\\" in filename
    ):
        raise DataExportError(
            "Filename must be a simple non-empty name"
        )

    directory = prepare_output_directory(output_dir)

    csv_path = directory / f"{filename}.csv"
    parquet_path = directory / f"{filename}.parquet"

    try:
        dataframe.to_csv(
            csv_path,
            index=False,
            encoding="utf-8",
        )

        dataframe.to_parquet(
            parquet_path,
            engine="pyarrow",
            index=False,
        )
    except (OSError, ValueError, ImportError, TypeError) as exc:
        raise DataExportError(
            f"Failed to export DataFrame '{filename}': {exc}"
        ) from exc

    return csv_path, parquet_path


def export_overall_metrics(
    metrics: OverallMetrics,
    output_dir: str | Path,
) -> Path:
    """Serialize overall financial indicators to JSON."""
    if not isinstance(metrics, OverallMetrics):
        raise DataExportError(
            "Expected an OverallMetrics instance"
        )

    directory = prepare_output_directory(output_dir)
    output_path = directory / "overall_metrics.json"

    try:
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(
                asdict(metrics),
                file,
                indent=2,
                allow_nan=False,
            )
            file.write("\n")
    except (OSError, ValueError, TypeError) as exc:
        raise DataExportError(
            f"Failed to export overall metrics: {exc}"
        ) from exc

    return output_path


def export_pipeline_results(
    enriched_transactions: pd.DataFrame,
    analytics_reports: Mapping[
        str, pd.DataFrame | OverallMetrics
    ],
    output_dir: str | Path,
) -> ExportReport:
    """
    Export enriched data and financial analytics.

    Expected analytics keys:
        customers, products, segments, overall
    """
    expected_keys = {
        "customers",
        "products",
        "segments",
        "overall",
    }

    missing = expected_keys - set(analytics_reports)

    if missing:
        raise DataExportError(
            f"Missing analytics reports: {sorted(missing)}"
        )

    if not isinstance(enriched_transactions, pd.DataFrame):
        raise DataExportError(
            "Enriched transactions must be a DataFrame"
        )

    # Validate report types before writing any files.
    for name in REPORT_NAMES:
        report_key = REPORT_KEYS[name]

        if not isinstance(
            analytics_reports[report_key], pd.DataFrame
        ):
            raise DataExportError(
                f"Report '{report_key}' must be a DataFrame"
            )

    overall = analytics_reports["overall"]

    if not isinstance(overall, OverallMetrics):
        raise DataExportError(
            "Report 'overall' must be OverallMetrics"
        )

    directory = prepare_output_directory(output_dir)
    generated_files: list[Path] = []

    generated_files.extend(
        export_dataframe(
            enriched_transactions,
            directory,
            "enriched_transactions",
        )
    )

    for filename in REPORT_NAMES:
        report_key = REPORT_KEYS[filename]

        generated_files.extend(
            export_dataframe(
                analytics_reports[report_key],
                directory,
                filename,
            )
        )

    generated_files.append(
        export_overall_metrics(overall, directory)
    )

    return ExportReport(
        output_directory=directory,
        files=tuple(generated_files),
    )