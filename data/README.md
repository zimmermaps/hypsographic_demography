# Publication data

This directory contains compact, derived data for the manuscript. Large WorldPop, GMTED2010, and GHS-SMOD source rasters are not redistributed.

## Figure data

- `figure_data/fig1_elevation_summary.csv`: population totals, changes, and 2025 broad-age composition for the six manuscript elevation groups.
- `figure_data/fig1_age_contributions.csv`: broad-age contributions to 2015–2025 total population growth. Contributions sum to total elevation-group growth.
- `figure_data/fig1_elevation_profile_2025.csv`: global 2025 population counts by integer elevation and broad age group for Figure 1D.
- `figure_data/fig2_elevation_settlement_age_shares.csv`: the 36 elevation-by-settlement cells used in Figure 2.
- `figure_data/fig3_region_elevation_growth.csv`: the 36 continent-by-elevation cells used in Figure 3B–C.
- `figure_data/fig3_country_elevation_groups.geoparquet`: elevation-zone polygons used in Figure 3A.
- `figure_data/fig3_natural_earth_admin0_110m.geojson`: Natural Earth boundary context used in Figure 3A.
- `figure_data/headline_manuscript_values.csv`: lookup table for reported headline values.

`dataset_s1_hypsographic_demography.csv` is the retained master tidy table from which the earlier figure summaries were assembled. `global_integer_elevation_age_sex_2015_2025.parquet` is the compact global integer-elevation table retained for provenance and optional threshold calculations.

## Country comparisons

- `country_comparisons/within_country_growth.csv`: one row per country for the lowland/highland 2015–2025 growth comparison.
- `country_comparisons/within_country_age_structure_2025.csv`: one row per country with youth and older-age counts, shares, and highland-minus-lowland differences.
- `country_comparisons/country_zone_counts_2015_2025.csv`: compact country-zone counts retained to document and reconcile the growth sample.

Both headline comparisons use lowlands `<500 m`, highlands `1,500–3,499 m`, and the same 48 countries with at least 100,000 people in both zones in 2025. Age shares are calculated from population counts aggregated within each country-zone before division; grid-cell percentages are never averaged.

## Sensitivity data

- `sensitivity/settlement_class_sensitivity.csv`: dynamic versus static-2025 settlement attribution by elevation and settlement class.
- `sensitivity/robustness_checks.csv`: global alternative-threshold and settlement-stratified checks.

## Conventions

- Intervals use `2015–2025` in labels and prose; machine-readable column names retain ASCII underscores.
- Elevation display labels use en dashes and `≥3,500 m`; internal category values retain their original ASCII encoding where required by plotting code.
- Population values are modeled people; shares and changes identify their units in column names (`percent` or `pp`).
