"""Inspect the packaged Dataset S1 analysis table."""

from pathlib import Path

import pandas as pd


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    dataset = root / "data" / "dataset_s1_hypsographic_demography.csv"
    if dataset.exists():
        df = pd.read_csv(dataset)
        print(f"Dataset S1 exists: {dataset.relative_to(root)}")
        print(df.groupby("table_name").size())
    else:
        print("Dataset S1 is not present.")


if __name__ == "__main__":
    main()
