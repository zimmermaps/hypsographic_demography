Supplementary Dataset S1
========================

Dataset S1 contains analysis-ready source data for the main paper figures and headline manuscript values.

Files:
- `dataset_s1_fig01_population_age_growth.csv`: Fig. 1 population, age composition, and 2015-2025 growth by elevation group.
- `dataset_s1_fig01_age_contributions.csv`: Fig. 1 age-class contributions to total growth by elevation group.
- `dataset_s1_fig02_settlement_static2025.csv`: Fig. 2 static-2025 settlement source data by elevation group and settlement class.
- `dataset_s1_key_manuscript_values.csv`: Headline manuscript values and companion threshold values used in the paper.

Column and unit notes:
- `population_*` columns are counts of people unless the column name includes `_billions` or `_millions`.
- `*_pct` columns are percentages.
- `*_pp` columns are percentage-point differences or contributions.
- `elevation_group` uses the manuscript elevation groups: <100 m, 100-499 m, 500-1,499 m, 1,500-2,499 m, 2,500-3,499 m, and >=3,500 m.
- `age_group` uses 0-14, 15-64, and 65+.
- `settlement_class` uses Low-density rural, Rural cluster, Peri-urban, Semi-dense urban, Dense urban, and Urban centre.
- Figure 2 settlement fields use static 2025 settlement classification, meaning 2025 settlement classes are held fixed for the 2015-2025 comparison.

Quality checks:
- <500 m 2025 population: 6.24236e+09 (target 6240000000.0; passed=True)
- <100 m 2025 population: 3.5136e+09 (target 3510000000.0; passed=True)
- 1,500-3,500 m 2025 population: 5.21971e+08 (target 522000000.0; passed=True)
- highland growth: 17.5291 (target 17.5; passed=True)
- lowland growth: 8.97416 (target 9.0; passed=True)
- highland youth share: 30.7125 (target 30.7; passed=True)
- lowland youth share: 23.2306 (target 23.2; passed=True)
- >=3,500 m 2025 population: 1.20968e+07 (target 12100000.0; passed=True)

This dataset supports main figures, headline manuscript values, and companion threshold values only.
