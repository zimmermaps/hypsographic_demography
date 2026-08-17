# Configuration Notes

Expected raw inputs for a full rebuild:

- `worldpop_dir`: directory of WorldPop Global 2 age-sex rasters by year, sex, and age code.
- `elevation_raster`: GMTED2010 mean elevation, 30 arc-second.
- `ghs_smod_dir`: GHS-SMOD R2023A settlement-class rasters for relevant years.
- `worldpop_template`: raster grid used as the alignment target.
- `output_dir`: destination for intermediate aligned tables.

Main conventions:

- Elevation is aligned to the WorldPop grid and rounded to integer meters before band assignment.
- Continuous elevation is resampled bilinearly.
- Categorical settlement classes are resampled by nearest neighbor.
- Static_2025 attribution holds 2025 classes fixed for 2015–2025 change summaries.
- Dynamic attribution allows classes to vary by year and is used only as a diagnostic in this paper.
