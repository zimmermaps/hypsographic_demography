# Processing Workflow

These scripts document the upstream workflow used to build Dataset S1. They are intentionally lightweight and are not a packaged processing system.

Full processing requires large public source datasets that are not included in this repository:

- WorldPop Global 2 annual age-sex population rasters.
- GMTED2010 mean elevation at 30 arc-second resolution.
- GHS-SMOD R2023A settlement-class rasters.
- Country boundary layers used in the full source workflow.

The figure notebook does not need these inputs. It reads `data/dataset_s1_hypsographic_demography.csv`.

## Order

1. `01_prepare_static_layers.py`: align elevation to the WorldPop grid and assign elevation bands.
2. `02_extract_population_by_grid.py`: summarize WorldPop age-sex population by aligned grid attributes.
3. `03_prepare_settlement_attribution.py`: prepare GHS-SMOD settlement classes for static_2025 and dynamic attribution.
4. `04_build_analysis_tables.py`: aggregate the aligned grid summaries into Dataset S1.

The complete production pipeline lives in the full processing source repository. These scripts are a readable record of the parts used for this paper only.
