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
    """Verify the complete pipeline executes successfully."""
    result = run_pipeline(sample_raw_dir)

    assert result == {
        "customers": 2,
        "products": 2,
        "transactions": 2,
    }

    captured = capsys.readouterr()

    assert (
        "Financial data pipeline completed successfully."
        in captured.out
    )

    assert "customers: input=2, output=2" in captured.out


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