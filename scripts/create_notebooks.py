"""Generate reproducible educational Pandas notebooks."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"


def markdown(text: str):
    return nbf.v4.new_markdown_cell(text)


def code(source: str):
    return nbf.v4.new_code_cell(source)


def save_notebook(name: str, cells: list) -> None:
    notebook = nbf.v4.new_notebook()
    notebook.cells = cells
    notebook.metadata.kernelspec = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }

    nbf.write(notebook, NOTEBOOK_DIR / name)


def main() -> None:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)

    setup = """
from pathlib import Path
import pandas as pd

from financial_processing import load_datasets

RAW_DIR = Path("../data/raw")
datasets = load_datasets(RAW_DIR)

customers = datasets["customers"]
products = datasets["products"]
transactions = datasets["transactions"]
"""

    save_notebook(
        "01_pandas_fundamentals.ipynb",
        [
            markdown(
                "# 01 — Pandas Fundamentals\n\n"
                "Explore synthetic financial datasets using "
                "DataFrames and Series."
            ),
            code(setup),
            markdown("## Dataset dimensions"),
            code("""
for name, df in datasets.items():
    print(name, df.shape)
"""),
            markdown("## Inspect customers"),
            code("""
display(customers.head())
display(customers.dtypes)
"""),
            markdown("## Explore transaction amounts"),
            code("""
display(transactions["amount"].describe())
print("Total amount:", transactions["amount"].sum())
"""),
            markdown(
                "## Learning outcome\n\n"
                "Understand DataFrame structure, Series, "
                "data types and descriptive statistics."
            ),
        ],
    )

    save_notebook(
        "02_data_cleaning.ipynb",
        [
            markdown(
                "# 02 — Data Cleaning\n\n"
                "Explore data quality and conservative "
                "normalization using Pandas."
            ),
            code(setup),
            markdown("## Missing values"),
            code("""
for name, df in datasets.items():
    print(name)
    display(df.isna().sum())
"""),
            markdown("## Duplicate records"),
            code("""
for name, df in datasets.items():
    print(name, "duplicates:", df.duplicated().sum())
"""),
            markdown("## Controlled cleaning"),
            code("""
from financial_processing.cleaning import clean_datasets
from financial_processing.validation import validate_datasets

cleaned, reports = clean_datasets(datasets)
validate_datasets(cleaned)

for name, report in reports.items():
    print(name, report)
"""),
            markdown(
                "## Learning outcome\n\n"
                "Differentiate cleaning from validation "
                "and inspect missing or duplicate values."
            ),
        ],
    )

    save_notebook(
        "03_merging_datasets.ipynb",
        [
            markdown(
                "# 03 — Merging Datasets\n\n"
                "Combine transactions with customer and "
                "product information using controlled joins."
            ),
            code(setup),
            markdown("## Validate and enrich transactions"),
            code("""
from financial_processing.cleaning import clean_datasets
from financial_processing.validation import validate_datasets
from financial_processing.transformations import enrich_transactions

cleaned, _ = clean_datasets(datasets)
validate_datasets(cleaned)

enriched = enrich_transactions(cleaned)
display(enriched.head())
"""),
            markdown("## Verify transaction cardinality"),
            code("""
print("Source rows:", len(transactions))
print("Enriched rows:", len(enriched))

assert len(transactions) == len(enriched)
"""),
            markdown("## Inspect product classifications"),
            code("""
display(
    enriched.groupby("product_type", observed=True)
    .size()
    .reset_index(name="transaction_count")
)
"""),
            markdown(
                "## Learning outcome\n\n"
                "Apply joins and understand why many-to-one "
                "cardinality validation is important."
            ),
        ],
    )

    save_notebook(
        "04_financial_analysis.ipynb",
        [
            markdown(
                "# 04 — Financial Analysis\n\n"
                "Calculate reproducible indicators using "
                "Pandas groupby and aggregation operations."
            ),
            code(setup),
            markdown("## Prepare enriched data"),
            code("""
from financial_processing.cleaning import clean_datasets
from financial_processing.validation import validate_datasets
from financial_processing.transformations import enrich_transactions
from financial_processing.analytics import calculate_all_metrics

cleaned, _ = clean_datasets(datasets)
validate_datasets(cleaned)

enriched = enrich_transactions(cleaned)
reports = calculate_all_metrics(enriched)
"""),
            markdown("## Customer metrics"),
            code("""
display(reports["customers"])
"""),
            markdown("## Product and segment metrics"),
            code("""
display(reports["products"])
display(reports["segments"])
"""),
            markdown("## Overall metrics"),
            code("""
print(reports["overall"])
"""),
            markdown("## Independent aggregation example"),
            code("""
summary = (
    enriched.groupby("segment", observed=True)
    .agg(
        transaction_count=("transaction_id", "count"),
        total_amount=("amount", "sum"),
        average_amount=("amount", "mean"),
    )
    .reset_index()
)

display(summary)
"""),
            markdown(
                "## Learning outcome\n\n"
                "Build analytical indicators using groupby, "
                "agg and vectorized Pandas operations."
            ),
        ],
    )

    print("Four notebooks generated successfully.")


if __name__ == "__main__":
    main()