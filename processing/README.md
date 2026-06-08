# Processing Workflow

The files in this directory are provenance scripts for the paper, not a complete production pipeline. They record the data-preparation steps used to make Dataset S1 and keep the manuscript repository understandable without carrying the large gridded workflow.

The full extraction was developed in the archived/source processing repository and requires large public source datasets that are not included here:

- WorldPop Global 2 annual age-sex population rasters.
- GMTED2010 mean elevation at 30 arc-second resolution.
- GHS-SMOD R2023A settlement-class rasters.
- Country boundary layers used in the full source workflow.

The figure notebook does not need those files. It reads the compact manuscript data products in `data/` and reproduces the three manuscript figures directly.

## What the scripts are

These scripts are deliberately minimal. They are meant to document the sequence of operations, key definitions, and analysis choices for this paper. They should be read as executable notes or pseudocode-style provenance, not as a turnkey geospatial processing system.

## Workflow order

1. `01_prepare_static_layers.py`: documents alignment of GMTED2010 elevation to the WorldPop grid, meter rounding, native elevation bands, and the six manuscript elevation groups.
2. `02_extract_population_by_grid.py`: documents extraction of WorldPop annual age-sex population by aligned grid attributes and aggregation to `0-14`, `15-64`, and `65+`.
3. `03_prepare_settlement_attribution.py`: documents GHS-SMOD alignment, the six settlement classes, static_2025 attribution for the main figures, and dynamic attribution for the diagnostic comparison.
4. `04_build_analysis_tables.py`: checks the materialized Dataset S1 and summarizes the logical tables used by the reproduction notebook.
5. `05_package_supplementary_datasets.py`: packages the public Dataset S1 and sample Dataset S2 CSV folders from the derived table outputs.
6. `build_dataset_s2_country_exclusion_sensitivity.py`: builds the compact Dataset S2 selected country-exclusion sensitivity table and its small release ingredients table.
7. `build_population_elevation_threshold_region_summary.py`: extends the companion threshold summary to Global plus broad regions/continents.
8. `06_plot_fig3_highland_change_map.py`: plots the production Figure 3 inhabited-highland population-change map from country elevation-zone GeoParquet inputs.
9. `07_plot_population_elevation_pyramid_gif.py`: generates the production population-by-elevation companion GIF embedded in the README plus the per-continent and six-panel continent GIFs in `outputs/figures/population_by_elevation_continents/`.

## Why this is lightweight

The manuscript figures use already aggregated analysis tables. Re-running the full raster workflow would require hundreds of source rasters, grid templates, and intermediate files that are too large for this repository. Keeping only the compact Dataset S1 plus these provenance scripts makes figure reproduction simple while still documenting how the analysis-ready tables were built.

For full production reruns, start from the archived/source processing repository and the raw WorldPop, GMTED2010, and GHS-SMOD inputs listed in `config_notes.md`.
