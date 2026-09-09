# Processing and figure code

The main notebook reads the derived publication tables and writes the three final PDFs. It does not rerun the large raster extraction.

## Manuscript workflow

- `plot_fig2.py`: plots `figures/fig2.pdf` from `data/figure_data/fig2_elevation_settlement_age_shares.csv`.
- `plot_fig3.py`: plots `figures/fig3.pdf` from the retained regional table and map layers.
- `06_plot_fig3_highland_change_map.py`: shared Robinson-projection and GeoParquet utilities used by `plot_fig3.py`.
- `build_within_country_age_structure_2025.py`: optional provenance rebuild of the 48-country 2025 age-structure table when the large local processed age-sex parquet is available.

Figure 1 is generated in `notebooks/01_reproduce_figures.ipynb`, where its four panels share layout code. The notebook also invokes the Figure 2 and Figure 3 scripts, verifies the country comparisons, and calculates the sensitivity summaries.

## Provenance

Files `01_prepare_static_layers.py` through `04_build_analysis_tables.py` record the upstream sequence: align elevation and settlement layers, extract age-sex population, apply static-2025 settlement attribution, and assemble analysis tables. The source rasters are not bundled here, and these steps are not part of the figure-reproduction command.

`07_plot_population_elevation_pyramid_gif.py` renders the companion GIFs in `assets/`. It reads the excluded local table `data/fact_population_by_integer_elevation_age_sex_2015_2025.parquet`; the companion notebook writes threshold tables to the ignored directory `outputs/population_by_elevation/`.

The exact source-product choices and category definitions are recorded in `config_notes.md` and `data/README.md`.
