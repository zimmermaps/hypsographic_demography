# Data

`dataset_s1_hypsographic_demography.csv` is the analysis-ready dataset used to reproduce the two main manuscript figures. It is a compact, tidy CSV derived from the analysis-ready release tables.

Rows with `table_name = figure1_elevation_summary` support Figure 1A and 1B: population by elevation and 2025 age composition.

Rows with `table_name = figure1_age_contribution` support Figure 1C: modeled population growth from 2015 to 2025 decomposed by broad age-class contribution. The key metric is `contribution_to_total_growth`, defined as age-class modeled population change divided by total 2015 population in the elevation group, expressed in percentage points. The notebook writes these rows back out as `outputs/tables/fig01_age_contribution_values.csv`.

Rows with `table_name = figure2_elevation_settlement` support Figure 2: 2025 population, 2025 youth share, 2025 male share, and 2015-2025 population growth by elevation group and GHS-SMOD settlement class.

Rows with `table_name = dynamic_static_growth_comparison` support the attribution sensitivity diagnostic. Dynamic attribution allows classes to vary by year. Static_2025 attribution holds 2025 elevation and settlement classes fixed across the 2015-2025 interval and is the main specification for the manuscript figures.

The 2015-2025 values are modeled gridded population change from the input population products. They are not direct observations of births, deaths, or migration.


`dataset_s2_robustness_checks.csv` contains computed robustness summaries derived from Dataset S1. It reports the primary lowland/highland comparison, exact alternative thresholds that can be assembled from the six manuscript elevation groups, and settlement-class stratified summaries. Checks that require unavailable columns or years are documented in the builder script output and omitted from the CSV.

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
