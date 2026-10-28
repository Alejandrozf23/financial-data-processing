"""Unit tests for CSV, Parquet and JSON export."""

import json
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from financial_processing.analytics import OverallMetrics
from financial_processing.export import (
    DataExportError,
    ExportReport,
    export_dataframe,
    export_overall_metrics,
    export_pipeline_results,
    prepare_output_directory,
)


@pytest.fixture
def sample_results():
    """Build deterministic synthetic analytics results."""
    enriched = pd.DataFrame({
        "transaction_id": ["T001", "T002"],
        "customer_id": ["C001", "C002"],
        "product_id": ["P001", "P002"],
        "amount": [100.0, 200.0],
        "segment": ["Premium", "Retail"],
        "region": ["North", "South"],
        "product_type": ["Investment", "Credit"],
    })

    customers = pd.DataFrame({
        "customer_id": ["C001", "C002"],
        "transaction_count": [1, 1],
        "total_amount": [100.0, 200.0],
        "average_amount": [100.0, 200.0],
    })

    products = pd.DataFrame({
        "product_type": ["Investment", "Credit"],
        "transaction_count": [1, 1],
        "total_amount": [100.0, 200.0],
        "average_amount": [100.0, 200.0],
    })

    segments = pd.DataFrame({
        "segment": ["Premium", "Retail"],
        "transaction_count": [1, 1],
        "total_amount": [100.0, 200.0],
        "average_amount": [100.0, 200.0],
    })

    overall = OverallMetrics(
        transaction_count=2,
        unique_customers=2,
        total_amount=300.0,
        average_amount=150.0,
    )

    reports = {
        "customers": customers,
        "products": products,
        "segments": segments,
        "overall": overall,
    }

    return enriched, reports


def test_prepare_output_directory(tmp_path):
    directory = tmp_path / "nested" / "processed"

    result = prepare_output_directory(directory)

    assert result == directory
    assert directory.is_dir()


def test_existing_output_directory(tmp_path):
    assert prepare_output_directory(tmp_path) == tmp_path


def test_invalid_output_directory(tmp_path):
    file_path = tmp_path / "already_a_file"
    file_path.write_text("content", encoding="utf-8")

    with pytest.raises(DataExportError):
        prepare_output_directory(file_path)


def test_export_dataframe_creates_both_formats(tmp_path):
    dataframe = pd.DataFrame({
        "customer_id": ["C001"],
        "amount": [125.5],
    })

    csv_path, parquet_path = export_dataframe(
        dataframe,
        tmp_path,
        "transactions",
    )

    assert csv_path.exists()
    assert parquet_path.exists()
    assert csv_path.suffix == ".csv"
    assert parquet_path.suffix == ".parquet"


def test_csv_round_trip(tmp_path):
    dataframe = pd.DataFrame({
        "customer_id": ["C001", "C002"],
        "amount": [100.5, 200.0],
    })

    csv_path, _ = export_dataframe(
        dataframe,
        tmp_path,
        "transactions",
    )

    restored = pd.read_csv(
        csv_path,
        dtype={"customer_id": "object"},
    )

    assert restored["customer_id"].tolist() == [
        "C001", "C002"
    ]
    assert restored["amount"].sum() == pytest.approx(300.5)


def test_parquet_round_trip(tmp_path):
    dataframe = pd.DataFrame({
        "customer_id": ["C001", "C002"],
        "amount": [100.5, 200.0],
    })

    _, parquet_path = export_dataframe(
        dataframe,
        tmp_path,
        "transactions",
    )

    restored = pd.read_parquet(parquet_path)

    assert_frame_equal(restored, dataframe)


def test_export_does_not_include_index(tmp_path):
    dataframe = pd.DataFrame({
        "customer_id": ["C001"],
        "amount": [100.0],
    })

    csv_path, parquet_path = export_dataframe(
        dataframe,
        tmp_path,
        "transactions",
    )

    csv_result = pd.read_csv(csv_path)
    parquet_result = pd.read_parquet(parquet_path)

    assert "Unnamed: 0" not in csv_result.columns
    assert "index" not in parquet_result.columns


@pytest.mark.parametrize(
    "filename",
    ["", "../output", "folder/output", r"folder\output"],
)
def test_invalid_filename(tmp_path, filename):
    dataframe = pd.DataFrame({"amount": [100.0]})

    with pytest.raises(
        DataExportError,
        match="Filename",
    ):
        export_dataframe(
            dataframe,
            tmp_path,
            filename,
        )


def test_invalid_dataframe(tmp_path):
    with pytest.raises(
        DataExportError,
        match="Expected a pandas DataFrame",
    ):
        export_dataframe(
            [100, 200],
            tmp_path,
            "invalid",
        )


def test_export_overall_metrics(tmp_path):
    metrics = OverallMetrics(
        transaction_count=3,
        unique_customers=2,
        total_amount=600.0,
        average_amount=200.0,
    )

    output_path = export_overall_metrics(
        metrics,
        tmp_path,
    )

    with output_path.open(encoding="utf-8") as file:
        result = json.load(file)

    assert result == {
        "transaction_count": 3,
        "unique_customers": 2,
        "total_amount": 600.0,
        "average_amount": 200.0,
    }


def test_export_overall_rejects_wrong_type(tmp_path):
    with pytest.raises(
        DataExportError,
        match="OverallMetrics",
    ):
        export_overall_metrics(
            {"total_amount": 100},
            tmp_path,
        )


def test_export_pipeline_creates_nine_files(
    tmp_path,
    sample_results,
):
    enriched, reports = sample_results

    result = export_pipeline_results(
        enriched,
        reports,
        tmp_path,
    )

    assert isinstance(result, ExportReport)
    assert len(result.files) == 9
    assert all(path.is_file() for path in result.files)

    expected = {
        "enriched_transactions.csv",
        "enriched_transactions.parquet",
        "customer_metrics.csv",
        "customer_metrics.parquet",
        "product_metrics.csv",
        "product_metrics.parquet",
        "segment_metrics.csv",
        "segment_metrics.parquet",
        "overall_metrics.json",
    }

    assert {path.name for path in result.files} == expected


def test_export_pipeline_preserves_inputs(
    tmp_path,
    sample_results,
):
    enriched, reports = sample_results

    original = enriched.copy(deep=True)

    export_pipeline_results(
        enriched,
        reports,
        tmp_path,
    )

    assert_frame_equal(enriched, original)


def test_export_pipeline_missing_report(
    tmp_path,
    sample_results,
):
    enriched, reports = sample_results
    del reports["products"]

    with pytest.raises(
        DataExportError,
        match="Missing analytics reports",
    ):
        export_pipeline_results(
            enriched,
            reports,
            tmp_path,
        )


def test_export_pipeline_invalid_report(
    tmp_path,
    sample_results,
):
    enriched, reports = sample_results
    reports["segments"] = ["Premium", "Retail"]

    with pytest.raises(
        DataExportError,
        match="must be a DataFrame",
    ):
        export_pipeline_results(
            enriched,
            reports,
            tmp_path,
        )

    assert list(tmp_path.iterdir()) == []


def test_export_pipeline_invalid_overall(
    tmp_path,
    sample_results,
):
    enriched, reports = sample_results
    reports["overall"] = {"total_amount": 300}

    with pytest.raises(
        DataExportError,
        match="must be OverallMetrics",
    ):
        export_pipeline_results(
            enriched,
            reports,
            tmp_path,
        )