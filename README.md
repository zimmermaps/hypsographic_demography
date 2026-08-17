# Hypsographic Demography Revisited

[![License](https://img.shields.io/badge/license-MIT%20%2B%20CC%20BY%204.0-blue.svg)](LICENSE.md)
[![Citation](https://img.shields.io/badge/citation-CITATION.cff-green.svg)](CITATION.cff)

<p align="center">
  <img src="assets/population_by_elevation_continents/population_by_elevation_pyramid_continents_6panel.gif" alt="Animated 2025 population pyramids by descending elevation threshold for six continents" width="100%">
</p>

This repository supports the manuscript **“Hypsographic Demography Revisited: Age Structure and Population Change by Elevation.”** It contains the compact derived data, analysis checks, and plotting code needed to reproduce the three final manuscript figures and headline results. The large source rasters are intentionally not redistributed.

## Repository structure

```text
README.md
LICENSE.md
CITATION.cff
requirements.txt
assets/                         companion GIFs
data/
├── figure_data/                tables and map layers for Figures 1–3
├── country_comparisons/        within-country growth and age structure
└── sensitivity/                settlement and threshold checks
figures/
├── fig1.pdf
├── fig2.pdf
└── fig3.pdf
notebooks/
├── 01_reproduce_figures.ipynb  main reproducible workflow
└── 02_population_by_elevation_table_and_gif.ipynb
processing/                     figure scripts and provenance code
```

## Data sources

The analysis combines four public data products:

- **WorldPop Global 2**, annual age-sex population estimates for 2015 and 2025 ([data catalogue](https://www.worldpop.org/datacatalog/); [Global2 release statement](https://data.worldpop.org/repo/prj/Global_2015_2030/R2025A/doc/Global2_Release_Statement_R2025A_v1.pdf)).
- **GMTED2010**, mean elevation at 30 arc-seconds, U.S. Geological Survey ([dataset DOI](https://doi.org/10.5066/F7J38R2N); [documentation](https://doi.org/10.3133/ofr20111073)).
- **GHS-SMOD R2023A**, Degree of Urbanisation settlement classes, European Commission Joint Research Centre ([dataset DOI](https://doi.org/10.2905/A0DF7A6F-49DE-46EA-9BDE-563437A6E2BA)).
- **Natural Earth 1:110m admin-0 boundaries**, used only for map outlines in Figure 3 ([Natural Earth](https://www.naturalearthdata.com/)).

The retained CSV and GeoParquet files are aggregated publication data. They do not contain or replace the original WorldPop, GMTED2010, or GHS-SMOD grids. Population changes are modeled changes in the gridded population products, not direct observations of births, deaths, or migration.

## Files behind the results

| Result | Retained source data | Plot or analysis code |
|---|---|---|
| Figure 1 | `data/figure_data/fig1_elevation_summary.csv`, `fig1_age_contributions.csv`, `fig1_elevation_profile_2025.csv` | `notebooks/01_reproduce_figures.ipynb` |
| Figure 2 | `data/figure_data/fig2_elevation_settlement_age_shares.csv` | `processing/plot_fig2.py` |
| Figure 3 | `data/figure_data/fig3_region_elevation_growth.csv` and the two `fig3_*` map layers | `processing/plot_fig3.py` |
| Headline manuscript values | `data/figure_data/headline_manuscript_values.csv` | main notebook checks |
| Within-country growth | `data/country_comparisons/within_country_growth.csv` | main notebook checks |
| Within-country age structure, 2025 | `data/country_comparisons/within_country_age_structure_2025.csv` | `processing/build_within_country_age_structure_2025.py` and main notebook checks |
| Settlement sensitivity | `data/sensitivity/settlement_class_sensitivity.csv` | retained analysis output |
| Other robustness checks | `data/sensitivity/robustness_checks.csv` | retained analysis output |

Lowlands are `<500 m`; inhabited highlands are `1,500–3,499 m`. The within-country comparisons include the same 48 countries with at least 100,000 people in both zones in 2025. Age shares are ratios calculated after aggregating population counts within country-zone combinations, not averages of grid-cell percentages.

## Companion animation

The GIFs in `assets/` are intentional communication products and are not part of the three-figure manuscript workflow. `notebooks/02_population_by_elevation_table_and_gif.ipynb` and `processing/07_plot_population_elevation_pyramid_gif.py` regenerate them from the optional local input `data/fact_population_by_integer_elevation_age_sex_2015_2025.parquet`, which is excluded from version control. The notebook writes its diagnostic threshold tables to the ignored directory `outputs/population_by_elevation/`; all GIFs are written under `assets/`.

Please use [CITATION.cff](CITATION.cff) when citing the repository. Code is released under the MIT License; derived data are released under CC BY 4.0 as described in [LICENSE.md](LICENSE.md).
