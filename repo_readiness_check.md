# Repository Readiness Check

Date: 2026-05-25

## 1. Final Tree

```text
hypso_demog/
├── README.md
├── LICENSE.md
├── CITATION.cff
├── requirements.txt
├── processing_requirements.txt
├── .gitignore
├── data/
│   ├── README.md
│   ├── dataset_s1_hypsographic_demography.csv
│   └── dataset_s1_dictionary.csv
├── notebooks/
│   └── 01_reproduce_figures.ipynb
├── processing/
│   ├── README.md
│   ├── config_notes.md
│   ├── 01_prepare_static_layers.py
│   ├── 02_extract_population_by_grid.py
│   ├── 03_prepare_settlement_attribution.py
│   └── 04_build_analysis_tables.py
├── outputs/
│   ├── repo_cleanup_log.md
│   ├── figures/
│   │   ├── main_fig01_hypsographic_summary_final.png
│   │   ├── main_fig01_hypsographic_summary_final.pdf
│   │   ├── main_fig02_elevation_settlement_static2025_final.png
│   │   └── main_fig02_elevation_settlement_static2025_final.pdf
│   └── tables/
│       ├── main_fig01_data.csv
│       ├── main_fig02_static2025_data.csv
│       ├── dynamic_vs_static2025_fig02_comparison.csv
│       └── key_values_for_manuscript.csv
└── manuscript/
    ├── README.md
    ├── figure_captions.md
    └── optional_final_latex_or_notes.md
```

## 2. Figure Notebook

`notebooks/01_reproduce_figures.ipynb` runs from Dataset S1 and reproduced the final figures and tables. It was executed successfully, then cleared of embedded outputs so the repository stays lightweight.

## 3. Final Figures

Both main figures exist as PNG and PDF:

- `outputs/figures/main_fig01_hypsographic_summary_final.png`
- `outputs/figures/main_fig01_hypsographic_summary_final.pdf`
- `outputs/figures/main_fig02_elevation_settlement_static2025_final.png`
- `outputs/figures/main_fig02_elevation_settlement_static2025_final.pdf`

The executed notebook selected Helvetica as the figure font. Font sizes are within the PNAS range specified for reduced figures.

## 4. Dataset S1

Dataset S1 and the dictionary exist:

- `data/dataset_s1_hypsographic_demography.csv`
- `data/dataset_s1_dictionary.csv`

Dataset S1 contains rows for Figure 1, Figure 2, and the dynamic-vs-static attribution diagnostic.

## 5. README

`README.md` matches the current repository contents and distinguishes figure reproduction from full upstream processing provenance.

## 6. Raw Data

Raw and large analysis-ready release files are excluded from the repository. The full downloaded release is outside this repo at the project level and is ignored if placed back under this folder.

## 7. Removed Analyses

The final repo excludes old exploratory outputs, country archetype analyses, age-sex pyramid figures, land-area/IPD tests, vital-event allocation outputs, and natural/residual change decompositions.

## 8. TODOs

- Replace placeholder author/repository fields in `CITATION.cff`.
- Replace `LICENSE.md` placeholder with the selected license before public release.

## 9. GitHub Readiness

The repository is safe to initialize and push after updating the license and citation placeholders. The `.gitignore` excludes virtual environments, raw data, large raster formats, scratch folders, and release bundles while keeping Dataset S1, notebooks, final figures, and final tables trackable.
