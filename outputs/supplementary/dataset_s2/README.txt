Supplementary Dataset S2
========================

Dataset S2 contains sample robustness and sensitivity tables supporting the elevation-gradient results.

Files:
- `dataset_s2_primary_robustness_checks.csv`: Primary robustness, highland threshold, and settlement-class sensitivity checks.
- `dataset_s2_dynamic_vs_static2025_settlement.csv`: Dynamic versus static-2025 settlement attribution comparison.
- `dataset_s2_country_highland_lowland.csv`: Country-level highland and lowland decomposition.
- `dataset_s2_concentration_summary.csv`: Top-10 and top-20 country concentration summaries.
- `dataset_s2_leave_one_country_out.csv`: Leave-one-country-out robustness table.
- `dataset_s2_leave_one_country_out_summary.csv`: Leave-one-country-out min/max summary.
- `dataset_s2_leave_one_region_out.csv`: Leave-one-region-out robustness table.
- `dataset_s2_country_standardized_comparison.csv`: Country-standardized highland-minus-lowland growth comparison.
- `dataset_s2_worldpop_metadata_status.csv`: WorldPop country source/census metadata provenance for selected highland-growth countries.
- `dataset_s2_country_decomposition_quality_checks.csv`: Quality checks for the country decomposition outputs.

Column and unit notes:
- `population_*` columns are counts of people unless otherwise stated.
- `*_pct` columns are percentages.
- `*_pp` columns are percentage-point differences.
- `iso3`, `country_name`, and `region` identify countries and regions where available.
- Elevation, age-group, and settlement-class labels follow Dataset S1 conventions.

Table notes:
- The country decomposition compares <500 m lowlands with 1,500-3,500 m inhabited highlands by country.
- Concentration summaries report top-10 and top-20 cumulative shares by highland population and highland growth.
- Leave-one-country-out and leave-one-region-out tables recompute the global highland-lowland contrast after removing each unit.
- The country-standardized comparison includes countries with at least 100,000 people in both zones in 2025 by default.
- The WorldPop metadata-status table reports fields extracted from the official Global 2 R2025A v1 census/source workbook and uses `not_available` where values are not listed.
- These tables support robustness and sensitivity checks; they do not provide pixel-level uncertainty intervals.

Quality checks:
- top 10 highland growth concentration: 75.71740032464037 (target 75.7; passed=True)
- top 20 highland growth concentration: 93.0095431918768 (target 93.0; passed=True)
- leave-one-country-out highland-minus-lowland remains positive: 5.548414708552908 (target >0 and no reversal; passed=True)
- country-standardized default country count: 48 (target 48; passed=True)

This dataset is provided as sample supplementary robustness and sensitivity tables, not as main figure source data.
