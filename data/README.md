# Data

`dataset_s1_hypsographic_demography.csv` is the analysis-ready dataset used to reproduce the two main manuscript figures. It is a compact, tidy CSV derived from the analysis-ready release tables.

Rows with `table_name = figure1_elevation_summary` support Figure 1: population by elevation, 2025 age composition, and 2015-2025 population growth.

Rows with `table_name = figure2_elevation_settlement` support Figure 2: 2025 population, 2025 youth share, and 2015-2025 population growth by elevation group and GHS-SMOD settlement class.

Rows with `table_name = dynamic_static_growth_comparison` support the attribution sensitivity diagnostic. Dynamic attribution allows classes to vary by year. Static_2025 attribution holds 2025 elevation and settlement classes fixed across the 2015-2025 interval and is the main specification for the manuscript figures.

The 2015-2025 values are modeled gridded population change from the input population products. They are not direct observations of births, deaths, or migration.
