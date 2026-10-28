# Financial Data Processing

**A Python and Pandas data engineering project for financial
data ingestion, validation, cleaning, transformation,
analytics, and export.**

This repository demonstrates practical Python engineering
skills through a reproducible financial data pipeline
using fully synthetic datasets.

## Project Overview

The application processes customer, product, and
transaction datasets through a modular pipeline.

It validates data integrity, enriches transactions
using controlled joins, calculates analytical metrics,
and optionally exports results in CSV, Parquet, and JSON.

The project is designed for technical learning and
portfolio demonstration. It does not process real
banking or customer information.

## Technology Stack

- Python 3.12+
- Pandas
- NumPy
- PyArrow
- pytest
- JupyterLab
- GitHub Actions

## Architecture

```mermaid
flowchart TD
    A["CSV datasets"] --> B["Ingestion"]
    B --> C["Cleaning"]
    C --> D["Validation"]
    D --> E["Transformations"]
    E --> F["Analytics"]
    F --> G["Optional Export"]
    G --> H["CSV / Parquet / JSON"]
```

For technical details, see [Architecture](docs/architecture.md).

## Features

### Data Ingestion
- CSV loading with Pandas.
- Explicit data type conversion.
- Required-column checks.

### Data Cleaning
- Text normalization.
- Blank value handling.
- Optional exact duplicate removal.
- Cleaning reports.

### Data Validation
- Primary key integrity.
- Required field validation.
- Foreign key validation.
- Transaction amount checks.
- Optional date validation.

### Data Transformation
- Customer and product enrichment.
- Controlled many-to-one joins.
- Merge cardinality checks.
- Unmatched reference detection.

### Financial Analytics
- Customer activity metrics.
- Product aggregation.
- Segment aggregation.
- Overall transaction indicators.

### Data Export
- CSV reports.
- Apache Parquet datasets.
- JSON summary metrics.

## Repository Structure

```text
data/          Synthetic datasets
docs/          Technical documentation
notebooks/     Reproducible Pandas examples
scripts/       Supporting utilities
src/           Application source code
tests/         Automated tests
.github/       Continuous integration
```

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/financial-data-processing.git
cd financial-data-processing
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

Or on Linux/macOS:

```bash
source .venv/bin/activate
```

Install the project with development and notebook dependencies:

```bash
python -m pip install -e ".[dev,notebooks]"
```

## Running the Pipeline

Run the complete processing pipeline:

```bash
python -m financial_processing.main --raw-dir data/raw
```

Run with output generation:

```bash
python -m financial_processing.main --raw-dir data/raw --output-dir data/processed
```

You can also use the installed CLI command:

```bash
financial-process --raw-dir data/raw --output-dir data/processed
```

## Generated Outputs

When export is enabled, the pipeline generates:

- enriched_transactions.csv
- enriched_transactions.parquet
- customer_metrics.csv
- customer_metrics.parquet
- product_metrics.csv
- product_metrics.parquet
- segment_metrics.csv
- segment_metrics.parquet
- overall_metrics.json

Generated data is excluded from version control.

## Automated Testing

Run the complete suite:

```bash
python -m pytest -v
```

The suite covers:
- Ingestion failures.
- Invalid schemas.
- Duplicate identifiers.
- Referential integrity.
- Numeric validation.
- Cleaning behavior.
- Merge cardinality.
- Analytical calculations.
- Export round trips.
- End-to-end integration.

Before repository professionalization, 117 tests passed
in the local development environment.

GitHub Actions is configured to run tests automatically
on pushes and pull requests.

## Jupyter Notebooks

The notebooks provide practical examples of Pandas:

1. Pandas fundamentals.
2. Data cleaning.
3. Dataset merging.
4. Financial analytics.

Generate notebooks:

```bash
python scripts/create_notebooks.py
```

Launch JupyterLab:

```bash
jupyter lab
```

## Documentation

- [Architecture](docs/architecture.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Engineering Development Log](docs/learning_log.md)

## Engineering Principles

- Separation of concerns.
- Explicit data validation.
- Reproducible synthetic datasets.
- Controlled transformations.
- Automated testing.
- Modular and maintainable Python code.

## Limitations

This is an educational project.

It does not include:
- Production banking integrations.
- AWS infrastructure.
- Distributed processing.
- Streaming ingestion.
- Strict accounting-grade monetary precision.
- Transactional or atomic export guarantees.

## License

See the LICENSE file for the applicable license.

## Author

Alejandro de Jesús Zepeda Flores

Python Engineering | Backend Development | Data Engineering
```

Sustituye `<your-username>` por `Alejandrozf23` si esa es la cuenta donde creaste este repositorio. Verifica también que el archivo `LICENSE` exista y contenga la licencia que realmente elegiste; si aún no has escogido una, elimina temporalmente esa sección.

## 8. Verificación final

Antes de hacer el commit, sigue este orden:

**Primero, instala las dependencias.**

```bash
python -m pip install -e ".[dev,notebooks]"
```

**Segundo, genera los notebooks.**

```bash
python scripts/create_notebooks.py
```

**Tercero, verifica la suite completa.**

```bash
python -m pytest -q
```

La referencia inicial es de 117 pruebas aprobadas. Como no hemos cambiado la lógica funcional ni añadido nuevas pruebas, el total debería mantenerse.

**Cuarto, comprueba la exportación.**

```bash
python -m financial_processing.main --raw-dir data/raw --output-dir data/processed
```

**Quinto, abre los notebooks y ejecuta todas sus celdas.** Comprueba que los cuatro terminan sin excepciones.

Finalmente, después del push, entra en la pestaña **Actions** de GitHub y comprueba que las pruebas terminan correctamente tanto en Python 3.12 como en 3.13. No consideraremos la integración continua verificada hasta que ambas ejecuciones finalicen con éxito.

## 9. Commit PFD-08

Cuando hayas creado todos los archivos y completado las comprobaciones:

```bash
git add .github/workflows/python-tests.yml
git add docs/
git add notebooks/
git add scripts/create_notebooks.py
git add pyproject.toml
git add README.md

git diff --cached --stat
```

Y después:

```bash
git commit -m "docs: professionalize financial data pipeline with notebooks and CI"
git push
```

## 10. Resultado para tu portafolio

<box border radius="lg" padding={3} gap={2}>
  <row align="center" justify="between">
    **Financial Data Processing**
    <text color="secondary" size="xs">PFD-08</text>
  </row>
  <grid columns={2} gap={3}>
    <grid-item>
      <title size="xl" tabularNums>117</title>
      <caption>Pruebas aprobadas antes de PFD-08</caption>
    </grid-item>
    <grid-item>
      <title size="xl" tabularNums>4</title>
      <caption>Notebooks definidos para generar</caption>
    </grid-item>
    <grid-item>
      <title size="lg">3 formatos</title>
      <caption>CSV, Parquet y JSON</caption>
    </grid-item>
    <grid-item>
      <title size="lg">6 etapas</title>
      <caption>Pipeline de extremo a extremo</caption>
    </grid-item>
  </grid>
</box>

Cuando PFD-08 esté verificado y publicado, podremos reflejarlo en tu CV de manera concreta:

<WritingBlock id="86412" variant="standard">**Financial Data Processing | Python, Pandas, pytest, PyArrow**

Desarrollo de un pipeline modular de ingeniería de datos financieros sintéticos, implementando ingesta CSV, validación de integridad referencial, limpieza controlada, enriquecimiento mediante joins many-to-one y cálculo de indicadores con Pandas (`groupby`, `agg`). Generación de resultados CSV, Parquet y JSON, con pruebas automatizadas, documentación técnica, notebooks reproducibles e integración continua.</WritingBlock>

Esta descripción quedaría respaldada por el repositorio una vez que confirmes la ejecución de los notebooks y la integración continua.

**Con esto cerramos el alcance de profesionalización.** No necesitamos introducir AWS ni más frameworks para demostrar Pandas: lo importante es que el código, las pruebas y la documentación cuenten una historia técnica coherente y verificable.