"""Build Dataset S2 robustness summaries from Dataset S1.

Dataset S2 is intentionally small. It uses only the aggregated
analysis-ready CSV in this repository and does not touch the original
WorldPop rasters or other large source products.

Run from the repository root:

    python processing/build_dataset_s2_robustness_checks.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "dataset_s1_hypsographic_demography.csv"
OUTPUT = ROOT / "data" / "dataset_s2_robustness_checks.csv"

ELEVATION_ORDER = [
    "<100 m",
    "100-499 m",
    "500-1499 m",
    "1500-2499 m",
    "2500-3499 m",
    ">=3500 m",
]
LOWLAND_LT_500 = ["<100 m", "100-499 m"]
HIGHLAND_1500_3500 = ["1500-2499 m", "2500-3499 m"]
SETTLEMENT_ORDER = [
    "Low-density rural",
    "Rural cluster",
    "Peri-urban",
    "Semi-dense urban",
    "Dense urban",
    "Urban centre",
]

OUTPUT_COLUMNS = [
    "check_id",
    "check_name",
    "comparison",
    "elevation_definition",
    "settlement_class",
    "geography_filter",
    "time_window",
    "year_start",
    "year_end",
    "population_start",
    "population_end",
    "absolute_change",
    "percent_change",
    "share_under_15_start",
    "share_under_15_end",
    "share_65plus_start",
    "share_65plus_end",
    "dependency_ratio_start",
    "dependency_ratio_end",
    "male_share_start",
    "male_share_end",
    "notes",
]


def require_columns(df: pd.DataFrame, columns: list[str]) -> None:
    missing = [col for col in columns if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset S1 is missing required columns: {missing}")


def blank_row(
    check_id: str,
    check_name: str,
    comparison: str,
    elevation_definition: str,
    notes: str,
    settlement_class: str = "",
    geography_filter: str = "global",
    time_window: str = "",
    year_start: float | int | None = None,
    year_end: float | int | None = None,
) -> dict[str, object]:
    row = {col: pd.NA for col in OUTPUT_COLUMNS}
    row.update(
        {
            "check_id": check_id,
            "check_name": check_name,
            "comparison": comparison,
            "elevation_definition": elevation_definition,
            "settlement_class": settlement_class,
            "geography_filter": geography_filter,
            "time_window": time_window,
            "year_start": year_start,
            "year_end": year_end,
            "notes": notes,
        }
    )
    return row


def safe_divide(num: float, den: float) -> float:
    if pd.isna(num) or pd.isna(den) or den == 0:
        return pd.NA
    return num / den


def clean_s1(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["year_num"] = pd.to_numeric(out["year"], errors="coerce")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out


def is_blank(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype(str).str.strip().eq("")


def aggregate_sex_share_end(f2: pd.DataFrame, elevation_groups: list[str], settlement_class: str | None = None) -> float:
    """Aggregate 2025 male share from weighted settlement-cell male shares."""
    sub = f2[f2["elevation_group"].isin(elevation_groups)].copy()
    if settlement_class:
        sub = sub[sub["settlement_class"].eq(settlement_class)]

    pop = sub[
        sub["metric"].eq("population")
        & sub["year_num"].eq(2025)
        & is_blank(sub["age_group"])
    ][["elevation_group", "settlement_class", "value"]].rename(columns={"value": "population_end"})
    male = sub[sub["metric"].eq("male_share")][
        ["elevation_group", "settlement_class", "value"]
    ].rename(columns={"value": "male_share_percent"})
    merged = pop.merge(male, on=["elevation_group", "settlement_class"], how="inner")
    if merged.empty or merged["population_end"].sum() == 0:
        return pd.NA
    male_pop = (merged["population_end"] * merged["male_share_percent"] / 100).sum()
    return 100 * male_pop / merged["population_end"].sum()


def aggregate_figure1_group(
    f1: pd.DataFrame,
    f2: pd.DataFrame,
    check_id: str,
    check_name: str,
    comparison: str,
    elevation_definition: str,
    elevation_groups: list[str],
) -> dict[str, object]:
    """Summarize an elevation-only group using Figure 1 rows in S1."""
    sub = f1[f1["elevation_group"].isin(elevation_groups)].copy()
    pop_start = sub[
        sub["metric"].eq("population")
        & sub["year_num"].eq(2015)
        & is_blank(sub["age_group"])
    ]["value"].sum()
    pop_end = sub[
        sub["metric"].eq("population")
        & sub["year_num"].eq(2025)
        & is_blank(sub["age_group"])
    ]["value"].sum()
    youth_end = sub[
        sub["metric"].eq("population")
        & sub["year_num"].eq(2025)
        & sub["age_group"].eq("0-14")
    ]["value"].sum()
    working_end = sub[
        sub["metric"].eq("population")
        & sub["year_num"].eq(2025)
        & sub["age_group"].eq("15-64")
    ]["value"].sum()
    old_end = sub[
        sub["metric"].eq("population")
        & sub["year_num"].eq(2025)
        & sub["age_group"].eq("65+")
    ]["value"].sum()
    abs_change = pop_end - pop_start

    row = blank_row(
        check_id=check_id,
        check_name=check_name,
        comparison=comparison,
        elevation_definition=elevation_definition,
        time_window="2015-2025",
        year_start=2015,
        year_end=2025,
        notes="Age-structure metrics are available for 2025 only in Dataset S1.",
    )
    row.update(
        {
            "population_start": pop_start,
            "population_end": pop_end,
            "absolute_change": abs_change,
            "percent_change": 100 * safe_divide(abs_change, pop_start),
            "share_under_15_end": 100 * safe_divide(youth_end, pop_end),
            "share_65plus_end": 100 * safe_divide(old_end, pop_end),
            "dependency_ratio_end": 100 * safe_divide(youth_end + old_end, working_end),
            "male_share_end": aggregate_sex_share_end(f2, elevation_groups),
        }
    )
    return row


def aggregate_settlement_group(
    f2: pd.DataFrame,
    check_id: str,
    comparison: str,
    elevation_definition: str,
    elevation_groups: list[str],
    settlement_class: str,
) -> dict[str, object]:
    """Summarize a lowland/highland group within one settlement class."""
    sub = f2[
        f2["elevation_group"].isin(elevation_groups)
        & f2["settlement_class"].eq(settlement_class)
    ].copy()
    pop_start = sub[
        sub["metric"].eq("population")
        & sub["year_num"].eq(2015)
        & is_blank(sub["age_group"])
    ]["value"].sum()
    pop_end = sub[
        sub["metric"].eq("population")
        & sub["year_num"].eq(2025)
        & is_blank(sub["age_group"])
    ]["value"].sum()
    youth_end = sub[
        sub["metric"].eq("population")
        & sub["year_num"].eq(2025)
        & sub["age_group"].eq("0-14")
    ]["value"].sum()
    abs_change = pop_end - pop_start
    row = blank_row(
        check_id=check_id,
        check_name="Settlement-class sensitivity",
        comparison=comparison,
        elevation_definition=elevation_definition,
        settlement_class=settlement_class,
        time_window="2015-2025",
        year_start=2015,
        year_end=2025,
        notes="Settlement-specific age and sex metrics are available for 2025 only in Dataset S1.",
    )
    row.update(
        {
            "population_start": pop_start,
            "population_end": pop_end,
            "absolute_change": abs_change,
            "percent_change": 100 * safe_divide(abs_change, pop_start),
            "share_under_15_end": 100 * safe_divide(youth_end, pop_end),
            "male_share_end": aggregate_sex_share_end(f2, elevation_groups, settlement_class),
        }
    )
    return row


def build_dataset_s2(s1: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    require_columns(
        s1,
        [
            "table_name",
            "attribution_scenario",
            "year",
            "interval",
            "elevation_group",
            "settlement_class",
            "age_group",
            "metric",
            "value",
            "unit",
            "notes",
        ],
    )
    s1 = clean_s1(s1)
    f1 = s1[s1["table_name"].eq("figure1_elevation_summary")].copy()
    f2 = s1[
        s1["table_name"].eq("figure2_elevation_settlement")
        & s1["attribution_scenario"].eq("static_2025")
    ].copy()

    rows: list[dict[str, object]] = []
    computed: list[str] = []
    skipped: list[str] = []

    rows.append(
        aggregate_figure1_group(
            f1,
            f2,
            "A1",
            "Primary comparison",
            "Lowland reference",
            "<500 m",
            LOWLAND_LT_500,
        )
    )
    rows.append(
        aggregate_figure1_group(
            f1,
            f2,
            "A2",
            "Primary comparison",
            "Primary inhabited highlands",
            "1500-3500 m",
            HIGHLAND_1500_3500,
        )
    )
    computed.append("primary lowland and 1500-3500 m highland comparison")

    threshold_defs = {
        ">=1500 m": ["1500-2499 m", "2500-3499 m", ">=3500 m"],
        ">=2500 m": ["2500-3499 m", ">=3500 m"],
        ">=3500 m": [">=3500 m"],
    }
    for i, (label, groups) in enumerate(threshold_defs.items(), start=1):
        rows.append(
            aggregate_figure1_group(
                f1,
                f2,
                f"B{i}",
                "Alternative highland threshold",
                label,
                label,
                groups,
            )
        )
    computed.append("alternative exact thresholds available from six manuscript elevation groups: >=1500 m, >=2500 m, >=3500 m")

    skipped.append(
        "alternative threshold >=1000 m: Dataset S1 uses 500-1499 m as one band, so an exact threshold cannot be computed"
    )
    skipped.append(
        "alternative threshold >=2000 m: Dataset S1 uses 1500-2499 m as one band, so an exact threshold cannot be computed"
    )
    skipped.append("temporal window 2015-2030: 2030 not available in Dataset S1")

    for settlement in SETTLEMENT_ORDER:
        rows.append(
            aggregate_settlement_group(
                f2,
                f"D_lowland_{settlement.lower().replace(' ', '_').replace('-', '_')}",
                "Lowland reference",
                "<500 m",
                LOWLAND_LT_500,
                settlement,
            )
        )
        rows.append(
            aggregate_settlement_group(
                f2,
                f"D_highland_{settlement.lower().replace(' ', '_').replace('-', '_')}",
                "Primary inhabited highlands",
                "1500-3500 m",
                HIGHLAND_1500_3500,
                settlement,
            )
        )
    computed.append("primary lowland/highland comparison within six GHS-SMOD settlement classes")

    skipped.append("geographic dominance checks: country/continent fields unavailable in Dataset S1")
    skipped.append("Tremblay/Ainslie near-2019 or 2020 comparison: reference year unavailable in Dataset S1")

    out = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    for col in ["year_start", "year_end"]:
        out[col] = pd.array(out[col], dtype="Int64")
    return out, computed, skipped


def main() -> None:
    if not INPUT.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT}")
    s1 = pd.read_csv(INPUT)
    out, computed, skipped = build_dataset_s2(s1)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT, index=False)

    print(f"Input file used: {INPUT}")
    print(f"Output file written: {OUTPUT}")
    print(f"Rows written: {len(out):,}")
    print("Checks successfully computed:")
    for item in computed:
        print(f"- {item}")
    print("Checks skipped and why:")
    for item in skipped:
        print(f"- {item}")


if __name__ == "__main__":
    main()
