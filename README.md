# Hypsographic Demography: Age and Change in Population by Altitude

[![License](https://img.shields.io/badge/license-MIT%20%2B%20CC%20BY%204.0-blue.svg)](LICENSE.md)
[![Citation](https://img.shields.io/badge/citation-CITATION.cff-green.svg)](CITATION.cff)

This repository supports the paper **"Hypsographic Demography: Age and Change in Population by Altitude."** It contains compact analysis-ready data, figure reproduction code, final figure outputs, and supplementary CSV tables.

<p align="center">
  <img src="outputs/figures/fig1_hypsographic_summary.png" alt="Figure 1. Hypsographic demographic summary" width="95%">
</p>

<p align="center">
  <img src="outputs/figures/fig2_elevation_settlement_stats.png" alt="Figure 2. Elevation and settlement summaries" width="95%">
</p>

## Contents

- `data/`: compact analysis-ready Dataset S1 and primary Dataset S2 robustness table.
- `notebooks/01_reproduce_figures.ipynb`: notebook that reproduces the two main figures from Dataset S1.
- `outputs/figures/`: final main figures as PNG and PDF.
- `outputs/supplementary/dataset_s1/`: clean CSV source data for the main figures and headline values.
- `outputs/supplementary/dataset_s2/`: clean CSV robustness, sensitivity, country-decomposition, and metadata-provenance tables.
- `processing/`: lightweight provenance scripts documenting the upstream data-preparation workflow.
- `scripts/`: packaging and metadata utilities for the supplementary CSV folders.

## Data Sources

The analysis is based on public gridded datasets:

- WorldPop Global 2 annual age-sex population estimates, 2015-2030.
- GMTED2010 mean elevation, 30 arc-second.
- GHS-SMOD R2023A settlement classification.

The full gridded source products are not included because of size. The repository includes compact derived tables used for figure reproduction and supplementary checks.

## Reproduce Figures

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab notebooks/01_reproduce_figures.ipynb
```

For a noninteractive run:

```bash
MPLBACKEND=Agg .venv/bin/python -m jupyter nbconvert --to notebook --execute notebooks/01_reproduce_figures.ipynb --output /tmp/01_reproduce_figures.executed.ipynb --ExecutePreprocessor.timeout=1200
```

## Build Supplementary Tables

Build the primary robustness checks:

```bash
.venv/bin/python processing/build_dataset_s2_robustness_checks.py
```

Build the country-decomposition robustness tables:

```bash
.venv/bin/python processing/build_dataset_s2_country_decomposition.py
```

Update the WorldPop metadata-provenance table:

```bash
.venv/bin/python scripts/update_dataset_s2_worldpop_metadata_status.py
```

Package the public supplementary Dataset S1 and Dataset S2 folders:

```bash
.venv/bin/python scripts/package_supplementary_datasets.py
```

## Outputs

Public supplementary files are under:

- `outputs/supplementary/dataset_s1/`
- `outputs/supplementary/dataset_s2/`

Intermediate figure tables are under `outputs/tables/`. Final figures are under `outputs/figures/`.

## Citation And License

Please cite the paper and repository metadata in `CITATION.cff`. Code is released under the MIT License and derived data/documentation are released under CC BY 4.0; see `LICENSE.md`.
