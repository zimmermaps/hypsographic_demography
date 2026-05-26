# Hypsographic Demography: Age and Change in Population by Altitude

[![License](https://img.shields.io/badge/license-MIT%20%2B%20CC%20BY%204.0-blue.svg)](LICENSE.md)
[![Citation](https://img.shields.io/badge/citation-CITATION.cff-green.svg)](CITATION.cff)

This repository supports the manuscript **"Hypsographic Demography: Age and Change in Population by Altitude."**

It contains the analysis-ready data used to generate the two main figures, a notebook to reproduce those figures, and lightweight processing scripts documenting how the analysis tables were created from public gridded population, elevation, and settlement datasets.

<p align="center">
  <img src="outputs/figures/fig1_hypsographic_summary.png" alt="Hypsographic demographic summary" width="100%">
</p>

<p align="center">
  <img src="outputs/figures/fig2_elevation_settlement_stats.png" alt="Elevation and settlement summaries" width="100%">
</p>


## Repository contents

- `data/dataset_s1_hypsographic_demography.csv`: Dataset S1 for the two main figures and attribution diagnostic, including the age-class contribution values used for Figure 1C.
- `data/dataset_s2_robustness_checks.csv`: Computed robustness summaries for the main elevation-gradient findings, including exact alternative highland thresholds available from Dataset S1 and settlement-class stratification. Checks requiring unavailable columns or years are reported by the builder script but omitted from the submitted CSV.
- `notebooks/01_reproduce_figures.ipynb`: figure reproduction notebook.
- `outputs/figures/`: final main figures as PNG and PDF.
- `outputs/tables/`: figure tables and manuscript values. These are regenerated from Dataset S1 by the notebook.
- `processing/`: short scripts and notes documenting the upstream preparation workflow.

## Data sources

The analysis uses:

- WorldPop Global 2 annual age-sex population estimates, 2015–2030.
- GMTED2010 mean elevation, 30 arc-second.
- GHS-SMOD R2023A settlement classification.

The full gridded source products are not included in this repository. Processing notes document the expected inputs and alignment logic.

## Main analysis choices

- Elevation groups: `<100 m`, `100–499 m`, `500–1499 m`, `1500–2499 m`, `2500–3499 m`, and `>=3500 m`.
- Inhabited highlands are summarized as `1500–3500 m`.
- Broad age groups: `0–14`, `15–64`, and `65+`.
- Figure 1C decomposes modeled population growth from 2015 to 2025 by broad age-class contribution. Segment widths show each age class's contribution, in percentage points, to total population growth within each elevation group; labels show total modeled growth. These values are included in Dataset S1 under `table_name = figure1_age_contribution`.
- `static_2025` attribution is used for the main 2015–2025 growth summaries: 2025 elevation and settlement classes are held fixed across the interval.
- Dynamic attribution is kept only as a robustness diagnostic for the settlement-growth matrix.
- 2015–2025 differences are modeled gridded population change, not direct observations of births, deaths, or migration.

## Reproduce figures

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab notebooks/01_reproduce_figures.ipynb
```


## Build Dataset S2

Dataset S2 is generated from Dataset S1 and contains computed robustness-check summaries only. Checks requiring unavailable years or columns, including 2015-2030 windows, geography-exclusion checks, and thresholds that split an aggregated elevation band, are printed by the script and omitted from the submitted CSV. The script does not create additional figures or reprocess source rasters.

```bash
python processing/build_dataset_s2_robustness_checks.py
```
