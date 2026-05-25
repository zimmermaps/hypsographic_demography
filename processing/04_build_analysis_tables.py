"""Build the analysis tables used in Dataset S1.

This script documents the final aggregation layer for the paper. The figure
notebook reads the already materialized Dataset S1 CSV in `data/`.
"""

from pathlib import Path

import pandas as pd


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    dataset = root / "data" / "dataset_s1_hypsographic_demography.csv"
    if dataset.exists():
        df = pd.read_csv(dataset)
        print(f"Dataset S1 exists: {dataset}")
        print(df.groupby("table_name").size())
    else:
        print("Dataset S1 is not present. Build it from the analysis-ready release tables.")


if __name__ == "__main__":
    main()
