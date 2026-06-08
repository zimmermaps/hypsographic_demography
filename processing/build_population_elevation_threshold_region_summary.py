"""Build regional population-by-elevation threshold summary table.

This companion output extends the global threshold summary by reporting the
same population counts and percentages for each broad region/continent.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT_TABLES = ROOT / "outputs" / "tables"

INPUT_FACT = DATA / "fact_population_by_integer_elevation_age_sex_2015_2025.parquet"
OUT_TABLE = OUTPUT_TABLES / "population_by_elevation_threshold_region_summary.csv"
GLOBAL_REFERENCE = OUTPUT_TABLES / "population_by_elevation_threshold_summary.csv"

YEARS = [2015, 2025]
THRESHOLDS_M = [100, 150, 200, 500, 1000, 1500, 3500]
REGION_ORDER = ["Global", "Africa", "Asia", "Europe", "North America", "Oceania", "South America"]

YEAR_COL = "year"
GEOGRAPHY_COL = "geography_level"
REGION_COL = "continent"
ELEV_COL = "elevation_m"
POP_COL = "population_count"


def load_fact() -> pd.DataFrame:
    if not INPUT_FACT.exists():
        raise FileNotFoundError(f"Missing input: {INPUT_FACT}")
    df = pd.read_parquet(
        INPUT_FACT,
        columns=[YEAR_COL, GEOGRAPHY_COL, REGION_COL, ELEV_COL, POP_COL],
    )
    df = df[df[YEAR_COL].isin(YEARS)].copy()
    df = df[
        df[GEOGRAPHY_COL].isin(["global", "continent"])
        & df[REGION_COL].isin(REGION_ORDER)
    ].copy()
    df[ELEV_COL] = pd.to_numeric(df[ELEV_COL], errors="coerce")
    df[POP_COL] = pd.to_numeric(df[POP_COL], errors="coerce").fillna(0)
    df = df.dropna(subset=[ELEV_COL])
    if df.empty:
        raise ValueError("No global or regional integer-elevation rows found.")
    return df


def build_threshold_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    grouped = df.groupby([YEAR_COL, GEOGRAPHY_COL, REGION_COL], sort=False)
    for (year, geography_level, region), sub in grouped:
        total_pop = float(sub[POP_COL].sum())
        for threshold in THRESHOLDS_M:
            pop_below = float(sub.loc[sub[ELEV_COL] <= threshold, POP_COL].sum())
            pop_above = total_pop - pop_below
            rows.append(
                {
                    "year": int(year),
                    "threshold_m": int(threshold),
                    "geography_level": geography_level,
                    "region": region,
                    "population_total": total_pop,
                    "population_below_or_equal": pop_below,
                    "percent_below_or_equal": pop_below / total_pop * 100,
                    "population_above": pop_above,
                    "percent_above": pop_above / total_pop * 100,
                }
            )
    out = pd.DataFrame(rows)
    out["region_sort"] = out["region"].map({region: i for i, region in enumerate(REGION_ORDER)})
    out = (
        out.sort_values(["year", "threshold_m", "region_sort"], kind="stable")
        .drop(columns="region_sort")
        .reset_index(drop=True)
    )
    return out


def print_global_check(out: pd.DataFrame) -> None:
    if not GLOBAL_REFERENCE.exists():
        print(f"Skipped global check; missing {GLOBAL_REFERENCE}")
        return
    reference = pd.read_csv(GLOBAL_REFERENCE)
    merged = out[out["region"].eq("Global")].merge(
        reference,
        on=["year", "threshold_m"],
        suffixes=("_regional", "_global_reference"),
    )
    checks = [
        "population_below_or_equal",
        "percent_below_or_equal",
        "population_above",
        "percent_above",
    ]
    print("Global-row check against existing threshold summary:")
    for col in checks:
        diff = merged[f"{col}_regional"] - merged[f"{col}_global_reference"]
        print(f"- {col}: max_abs_diff={diff.abs().max():.6g}")


def print_2025_150m_summary(out: pd.DataFrame) -> None:
    focus = out[out["year"].eq(2025) & out["threshold_m"].eq(150)].copy()
    print("2025 population share at or below 150 m:")
    for row in focus.itertuples(index=False):
        print(f"- {row.region}: {row.percent_below_or_equal:.1f}%")


def main() -> None:
    df = load_fact()
    out = build_threshold_summary(df)
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_TABLE, index=False)
    print(f"Wrote {OUT_TABLE}")
    print_global_check(out)
    print_2025_150m_summary(out)


if __name__ == "__main__":
    main()
