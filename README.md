# Hypsographic Demography Revisited

[![License](https://img.shields.io/badge/license-MIT%20%2B%20CC%20BY%204.0-blue.svg)](LICENSE.md)
[![Citation](https://img.shields.io/badge/citation-CITATION.cff-green.svg)](CITATION.cff)

<p align="center">
  <img src="outputs/figures/population_by_elevation_continents/population_by_elevation_pyramid_continents_6panel.gif" alt="Animated 2025 population pyramids by descending elevation threshold for six continents" width="100%">
</p>

This repository supports the submiited manuscript **“Hypsographic Demography Revisited: Age Structure and Population Change by Elevation.”**. It contains compact derived data and figure-reproduction notebooks for the manuscript.

## Repository Contents

- `data/Dataset_S1.xlsx`: Dataset S1 included with manuscript
- `data/Dataset_S2.xlsx`: Dataset S2 included with manuscript
- `notebooks/01_reproduce_figures.ipynb`: reproduces the three main manuscript figures and writes the main figure source tables.
- `notebooks/02_population_by_elevation_table_and_gif.ipynb`: writes the elevation-threshold summary tables and calls the production GIF renderer.
- `outputs/figures/`: final manuscript figures and the companion GIF.
- `outputs/tables/`: intermediate and manuscript-value tables produced by the notebooks.
- `outputs/supplementary/dataset_s1/`: CSV source data for the main figures and headline manuscript values.
- `outputs/supplementary/dataset_s2/`: robustness and sensitivity tables supporting the manuscript.
- `data/`: compact derived inputs needed to reproduce figures, threshold summaries, and the GIF.
- `processing/`: lightweight provenance scripts documenting the derived-table workflow.

## Key Outputs

- Figure 1: `outputs/figures/fig1_hypsographic_summary.{png,pdf}`
- Figure 2: `outputs/figures/fig2_elevation_settlement_stats.{png,pdf}`
- Figure 3: `outputs/figures/fig3_highland_change_map.{png,pdf,svg}`
- Companion GIF: `outputs/figures/population_by_elevation_pyramid.gif`
- Continent companion GIFs, including the six-panel figure: `outputs/figures/population_by_elevation_continents/`
- Threshold table: `outputs/tables/population_by_elevation_threshold_summary.csv`
- Threshold-by-age table: `outputs/tables/population_by_elevation_threshold_age_summary.csv`
- Regional threshold table: `outputs/tables/population_by_elevation_threshold_region_summary.csv`
- Manuscript value lookup: `outputs/tables/key_values_for_manuscript.csv`

## Data Sources

The analysis uses public gridded datasets:

- WorldPop Global 2 annual age-sex population estimates.
- GMTED2010 mean elevation.
- GHS-SMOD R2023A settlement classification.
- Natural Earth 110 m admin-0 country boundaries for Figure 3.

The full gridded source products are not included because of file size. This repository provides the compact derived tables and geospatial inputs needed to reproduce the manuscript figures, reported values, and companion animation.

## Reproduce

Create a Python environment and run the notebooks:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```