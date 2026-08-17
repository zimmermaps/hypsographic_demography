# Processing and figure code

The public workflow is intentionally lightweight. The main notebook reads the retained publication tables and writes the three final PDFs; it does not rerun the large raster extraction.

## Manuscript workflow

- `plot_fig2.py`: plots `figures/fig2.pdf` from `data/figure_data/fig2_elevation_settlement_age_shares.csv`.
- `plot_fig3.py`: plots `figures/fig3.pdf` from the retained regional table and map layers.
- `06_plot_fig3_highland_change_map.py`: shared Robinson-projection and GeoParquet utilities used by `plot_fig3.py`.
- `build_within_country_age_structure_2025.py`: optional provenance rebuild of the 48-country 2025 age-structure table when the large local processed age-sex parquet is available.

Figure 1 remains in `notebooks/01_reproduce_figures.ipynb` because its four coordinated panels share notebook-level layout code. The same notebook invokes the Figure 2 and Figure 3 scripts and verifies headline country comparisons.

## Provenance

Scripts `01_prepare_static_layers.py` through `04_build_analysis_tables.py` document the original sequence: align elevation and settlement layers, extract age-sex population, apply static-2025 settlement attribution, and assemble analysis tables. They require public source data that are not bundled here and are not part of the simple figure-reproduction command.

`07_plot_population_elevation_pyramid_gif.py` is the optional renderer for the preserved communication assets in `assets/`. It requires the larger local global-and-continent integer-elevation table excluded from version control.

The exact source-product choices and category definitions are recorded in `config_notes.md` and `data/README.md`.
