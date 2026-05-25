# Hypsographic Demography: Age and Change in Population by Altitude

This repository supports the manuscript "Hypsographic Demography: Age and Change in Population by Altitude." It contains the analysis-ready data used to generate the two main figures, a notebook to reproduce those figures, and lightweight processing scripts documenting how the analysis tables were created from public gridded population, elevation, and settlement datasets.

The repository is intentionally narrow. It covers population by elevation, broad age structure by elevation, modeled population change from 2015 to 2025, and elevation-by-settlement summaries using GHS-SMOD classes.

## What This Repository Contains

- `data/dataset_s1_hypsographic_demography.csv`: Dataset S1 for the two main figures and attribution diagnostic.
- `notebooks/01_reproduce_figures.ipynb`: figure reproduction notebook.
- `outputs/figures/`: final main figures as PNG and PDF.
- `outputs/tables/`: figure tables and manuscript values.
- `processing/`: short scripts and notes documenting the upstream preparation workflow.

## Data Sources

- WorldPop Global 2 annual age-sex population estimates, 2015-2030.
- GMTED2010 mean elevation, 30 arc-second.
- GHS-SMOD R2023A settlement classification.

The full gridded source products are not included here. The processing notes explain the expected inputs and the alignment logic.

## Main Analysis Choices

- Elevation groups: `<100 m`, `100-499 m`, `500-1499 m`, `1500-2499 m`, `2500-3499 m`, `>=3500 m`.
- Inhabited highlands are summarized as `1500-3500 m`.
- Broad age groups: `0-14`, `15-64`, and `65+`.
- Static_2025 attribution is used for the main 2015-2025 growth summaries: 2025 elevation and settlement classes are held fixed across the interval.
- Dynamic attribution is kept only as a robustness diagnostic for the settlement-growth matrix.
- 2015-2025 differences are modeled gridded population change, not direct observations of births, deaths, or migration.

## Reproduce Figures

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab notebooks/01_reproduce_figures.ipynb
```

The notebook reads Dataset S1 and writes:

- `outputs/figures/main_fig01_hypsographic_summary_final.png`
- `outputs/figures/main_fig01_hypsographic_summary_final.pdf`
- `outputs/figures/main_fig02_elevation_settlement_static2025_final.png`
- `outputs/figures/main_fig02_elevation_settlement_static2025_final.pdf`

## Limitations

- The analysis is descriptive and does not estimate causal effects of elevation.
- Results inherit uncertainty and modeling choices from the gridded input products.
- The main figures do not reproduce land-area-normalized integrated population density.
- The full extraction workflow requires large public source datasets that are not stored in this repository.

## Citation

If using this repository, cite the manuscript and Dataset S1. A placeholder citation file is included and should be updated after publication.
