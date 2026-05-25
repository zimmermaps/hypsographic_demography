# Repository Cleanup Log

This repository was reduced to the materials needed for the PNAS-style hypsographic demography paper.

Kept:

- Dataset S1 in `data/`, with column definitions documented in `data/README.md`.
- The final figure reproduction notebook in `notebooks/01_reproduce_figures.ipynb`.
- Final PNG/PDF figures in `outputs/figures/`.
- Final figure and manuscript-value tables in `outputs/tables/`.
- Lightweight processing notes/scripts in `processing/`.

Excluded from the final paper repository:

- Raw and analysis-ready release data, because they are large and not needed for figure reproduction from Dataset S1.
- Exploratory figures, old figure variants, and old notebook outputs.
- Country archetype, natural/residual change, vital-event, land-area/IPD, and age-sex pyramid outputs.
- Local virtual environments and operating-system metadata.

Large or deprecated local materials, if still needed, should be kept outside this repository or in an ignored local archive.
