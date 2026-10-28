"""Integration tests for the financial data pipeline."""

from pathlib import Path

import pytest

from financial_processing.main import main, run_pipeline
from financial_processing.validation import DataValidationError


@pytest.fixture
def sample_raw_dir(tmp_path: Path) -> Path:
    """Create valid synthetic CSV files for integration tests."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    (raw_dir / "customers.csv").write_text(
        "customer_id,segment,region\n"
        " C001 , Premium , North \n"
        "C002,Retail,South\n",
        encoding="utf-8",
    )

    (raw_dir / "products.csv").write_text(
        "product_id,product_type\n"
        " P001 , Investment \n"
        "P002,Credit\n",
        encoding="utf-8",
    )

    (raw_dir / "transactions.csv").write_text(
        "transaction_id,customer_id,product_id,amount\n"
        "T001, C001 , P001 ,12500.50\n"
        "T002,C002,P002,7800.00\n",
        encoding="utf-8",
    )

    return raw_dir


def test_run_pipeline_success(sample_raw_dir, capsys):
    """Verify the pipeline includes transaction enrichment."""
    result = run_pipeline(sample_raw_dir)

    assert result == {
        "customers": 2,
        "products": 2,
        "transactions": 2,
        "enriched_transactions": 2,
    }

    captured = capsys.readouterr()

    assert (
        "Financial data pipeline completed successfully."
        in captured.out
    )

    assert "customers: input=2, output=2" in captured.out
    assert "enriched_transactions: rows=2" in captured.out

def test_run_pipeline_missing_file(tmp_path):
    """Verify missing input files stop pipeline execution."""
    with pytest.raises(FileNotFoundError):
        run_pipeline(tmp_path)


def test_run_pipeline_invalid_reference(sample_raw_dir):
    """Verify unknown customers are rejected."""
    transactions = sample_raw_dir / "transactions.csv"

    transactions.write_text(
        "transaction_id,customer_id,product_id,amount\n"
        "T001,C999,P001,100.00\n",
        encoding="utf-8",
    )

    with pytest.raises(
        DataValidationError,
        match="unknown 'customer_id'",
    ):
        run_pipeline(sample_raw_dir)


def test_run_pipeline_rejects_duplicate_transaction(
    sample_raw_dir,
):
    """Verify duplicate IDs are rejected by default."""
    transactions = sample_raw_dir / "transactions.csv"

    transactions.write_text(
        "transaction_id,customer_id,product_id,amount\n"
        "T001,C001,P001,100.00\n"
        "T001,C001,P001,100.00\n",
        encoding="utf-8",
    )

    with pytest.raises(
        DataValidationError,
        match="duplicate 'transaction_id'",
    ):
        run_pipeline(sample_raw_dir)


def test_run_pipeline_removes_exact_duplicates(
    sample_raw_dir,
    capsys,
):
    """Verify optional duplicate removal."""
    transactions = sample_raw_dir / "transactions.csv"

    transactions.write_text(
        "transaction_id,customer_id,product_id,amount\n"
        "T001,C001,P001,100.00\n"
        "T001,C001,P001,100.00\n",
        encoding="utf-8",
    )

    result = run_pipeline(
        sample_raw_dir,
        drop_exact_duplicates=True,
    )

    assert result["transactions"] == 1

    output = capsys.readouterr().out
    assert "duplicates_removed=1" in output


def test_main_with_custom_directory(sample_raw_dir):
    """Verify the CLI accepts a custom data directory."""
    exit_code = main([
        "--raw-dir",
        str(sample_raw_dir),
    ])

    assert exit_code == 0


def test_main_with_duplicate_removal(sample_raw_dir):
    """Verify the CLI accepts the duplicate removal flag."""
    exit_code = main([
        "--raw-dir",
        str(sample_raw_dir),
        "--drop-exact-duplicates",
    ])

    assert exit_code == 0

def test_pipeline_fails_when_customer_catalog_has_duplicates(
    sample_raw_dir,
):
    """Reject duplicate customer keys before data enrichment."""
    customers = sample_raw_dir / "customers.csv"

    customers.write_text(
        "customer_id,segment,region\n"
        "C001,Premium,North\n"
        "C001,Retail,South\n",
        encoding="utf-8",
    )

    with pytest.raises(
        DataValidationError,
        match="duplicate 'customer_id'",
    ):
        run_pipeline(sample_raw_dir)

def test_pipeline_calculates_financial_analytics(
    sample_raw_dir,
    capsys,
):
    """Verify that the pipeline computes and prints analytics."""
    result = run_pipeline(sample_raw_dir)

    output = capsys.readouterr().out

    assert result["enriched_transactions"] == 2

    assert "Financial analytics:" in output
    assert "transaction_count=2" in output
    assert "unique_customers=2" in output

    # 12500.50 + 7800.00 = 20300.50
    assert "total_amount=20300.50" in output
    assert "average_amount=10150.25" in output

def test_pipeline_exports_nine_files(
    sample_raw_dir,
    tmp_path,
    capsys,
):
    """Verify the complete pipeline generates nine artifacts."""
    output_dir = tmp_path / "processed"

    result = run_pipeline(
        sample_raw_dir,
        output_dir=output_dir,
    )

    assert result["enriched_transactions"] == 2

    expected_files = {
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

    actual_files = {
        path.name
        for path in output_dir.iterdir()
        if path.is_file()
    }

    assert actual_files == expected_files

    output = capsys.readouterr().out
    assert "Export completed: 9 files" in output


def test_pipeline_without_output_does_not_export(
    sample_raw_dir,
    tmp_path,
):
    """Verify export is optional."""
    output_dir = tmp_path / "processed"

    result = run_pipeline(sample_raw_dir)

    assert result["enriched_transactions"] == 2
    assert not output_dir.exists()


def test_cli_supports_export(
    sample_raw_dir,
    tmp_path,
):
    """Verify the command-line export argument."""
    output_dir = tmp_path / "results"

    exit_code = main([
        "--raw-dir",
        str(sample_raw_dir),
        "--output-dir",
        str(output_dir),
    ])

    assert exit_code == 0
    assert (output_dir / "overall_metrics.json").exists()
    assert (output_dir / "enriched_transactions.parquet").exists()