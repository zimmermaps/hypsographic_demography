# Data

`dataset_s1_hypsographic_demography.csv` is the analysis-ready dataset used to reproduce the first two main manuscript figures. It is a compact, tidy CSV derived from the analysis-ready release tables.

Rows with `table_name = figure1_elevation_summary` support Figure 1A and 1B: population by elevation and 2025 age composition.

Rows with `table_name = figure1_age_contribution` support Figure 1C: modeled population growth from 2015 to 2025 decomposed by broad age-class contribution. The key metric is `contribution_to_total_growth`, defined as age-class modeled population change divided by total 2015 population in the elevation group, expressed in percentage points. The notebook writes these rows back out as `outputs/tables/fig01_age_contribution_values.csv`.

Rows with `table_name = figure2_elevation_settlement` support Figure 2: 2025 population, 2025 youth share, 2025 male share, and 2015-2025 population growth by elevation group and GHS-SMOD settlement class.

Rows with `table_name = dynamic_static_growth_comparison` support the attribution sensitivity diagnostic. Dynamic attribution allows classes to vary by year. Static_2025 attribution holds 2025 elevation and settlement classes fixed across the 2015-2025 interval and is the main specification for the manuscript figures.

The 2015-2025 values are modeled gridded population change from the input population products. They are not direct observations of births, deaths, or migration.


`dataset_s2_robustness_checks.csv` contains computed robustness summaries derived from Dataset S1. It reports the primary lowland/highland comparison, exact alternative thresholds that can be assembled from the six manuscript elevation groups, and settlement-class stratified summaries. Checks that require unavailable columns or years are documented in the builder script output and omitted from the CSV.

Additional Dataset S2 robustness outputs in `outputs/tables/` include the selected country-exclusion sensitivity table and its compact ingredients table. Run `python processing/build_dataset_s2_country_exclusion_sensitivity.py` from the repository root to rebuild the sensitivity table from those ingredients without bundling the larger analysis-ready release parquet.

Additional compact geospatial and integer-elevation inputs support the production Figure 3 map, threshold summaries, and companion animation:

- `country_elevation_group_polygons.geoparquet`: country elevation-zone polygons used as map context.
- `fig3_highland_change_polygons.geoparquet`: inhabited-highland country elevation-zone polygons with the total 2015-2025 population-change values used for Figure 3.
- `natural_earth_admin0_110m.geojson`: Natural Earth country boundaries used for Figure 3 borders.
- `global_integer_elevation_age_sex_2015_2025.parquet`: compact global-only population by year, integer elevation, age, sex, and broad age group.
- `fact_population_by_integer_elevation_age_sex_2015_2025.parquet`: global and continent population by year, integer elevation, age, sex, and broad age group. The companion notebook filters this file to `geography_level == "global"` for the threshold tables; `processing/build_population_elevation_threshold_region_summary.py` uses its `continent` rows for regional threshold summaries; `processing/07_plot_population_elevation_pyramid_gif.py` uses it to produce the global README GIF and per-continent GIFs.

The integer-elevation parquet file includes `broad_age_group` values for `young_0_14`, `working_age_15_64`, and `old_age_65_plus`; these support reported threshold shares by broad age group.

## Columns

| Column | Description | Units | Allowed values / notes |
|---|---|---|---|
| `table_name` | Logical table within Dataset S1. | text | `figure1_elevation_summary`; `figure1_age_contribution`; `figure2_elevation_settlement`; `dynamic_static_growth_comparison` |
| `attribution_scenario` | Spatial attribution used for the row. | text | `static_2025`, `dynamic`, or `dynamic_minus_static_2025` |
| `year` | Calendar year for annual quantities. | year | Blank for interval metrics. |
| `interval` | Change interval for change metrics. | text | `2015-2025` where applicable. |
| `elevation_group` | Broad elevation group used in the manuscript figures. | text | `<100 m`; `100-499 m`; `500-1499 m`; `1500-2499 m`; `2500-3499 m`; `>=3500 m` |
| `elevation_group_order` | Plot order for elevation groups, low to high. | integer | 1 to 6 |
| `settlement_class` | GHS-SMOD settlement class after light grouping. | text | Blank for elevation-only rows; otherwise final six settlement classes. |
| `settlement_class_order` | Plot order for settlement classes. | integer | 1 to 6; blank for elevation-only rows. |
| `age_group` | Broad age group. | text | `0-14`, `15-64`, `65+`, or blank. |
| `metric` | Measured quantity. | text | `population`, `population_share`, `population_growth`, `absolute_change`, `contribution_to_total_growth`, `male_share`, `mean_age_approx`, `growth_difference`, `population_denominator` |
| `value` | Metric value. | numeric | Interpret using `unit`. |
| `unit` | Unit for value. | text | `people`, `percent`, `years`, `percentage points` |
| `notes` | Interpretive or provenance notes. | text | `static_2025` means 2025 classes held fixed for change summaries. |
