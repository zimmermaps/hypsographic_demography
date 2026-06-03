"""Build country-level Dataset S2 robustness decomposition tables.

This additive script uses the enriched static_2025 release tables when they
are available locally. It does not overwrite Dataset S1 or the existing
Dataset S2 robustness CSV.

Run from the repository root:

    .venv/bin/python processing/build_dataset_s2_country_decomposition.py
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = ROOT.parent / "hypsographic_demography_download_data"
TABLE_DIR = ROOT / "outputs" / "tables"

LOWLAND_BANDS = list(range(1, 9))
HIGHLAND_BANDS = [11, 12, 13, 14]

CSV_OUTPUTS = {
    "country_highland_lowland": TABLE_DIR / "dataset_s2_country_highland_lowland.csv",
    "concentration_summary": TABLE_DIR / "dataset_s2_concentration_summary.csv",
    "leave_one_country_out": TABLE_DIR / "dataset_s2_leave_one_country_out.csv",
    "leave_one_country_out_summary": TABLE_DIR / "dataset_s2_leave_one_country_out_summary.csv",
    "leave_one_region_out": TABLE_DIR / "dataset_s2_leave_one_region_out.csv",
    "country_standardized_comparison": TABLE_DIR / "dataset_s2_country_standardized_comparison.csv",
    "quality_checks": TABLE_DIR / "dataset_s2_country_decomposition_quality_checks.csv",
}


def safe_divide(num: float, den: float) -> float:
    if pd.isna(num) or pd.isna(den) or den == 0:
        return math.nan
    return num / den


def percent_change(end: float, start: float) -> float:
    return 100 * safe_divide(end - start, start)


def required_path(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")
    return path


def load_source_tables(source_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, bool]:
    metrics_path = required_path(source_root / "data" / "static_2025" / "fact_enriched_demographic_metrics.parquet")
    country_path = required_path(source_root / "lookups" / "dim_country.parquet")
    metrics = pd.read_parquet(
        metrics_path,
        columns=[
            "iso3",
            "country_name",
            "continent",
            "band_id",
            "year",
            "population_total",
            "youth_population",
        ],
    )
    countries = pd.read_parquet(country_path)
    region_available = "continent" in metrics.columns and metrics["continent"].notna().any()
    return metrics, countries, region_available


def aggregate_zone(metrics: pd.DataFrame, bands: list[int], prefix: str) -> pd.DataFrame:
    sub = metrics[metrics["band_id"].isin(bands) & metrics["year"].isin([2015, 2025])].copy()
    grouped = (
        sub.groupby(["iso3", "country_name", "continent", "year"], dropna=False)
        .agg(population_total=("population_total", "sum"), youth_population=("youth_population", "sum"))
        .reset_index()
    )
    wide = grouped.pivot_table(
        index=["iso3", "country_name", "continent"],
        columns="year",
        values=["population_total", "youth_population"],
        aggfunc="sum",
        fill_value=0,
    )
    wide.columns = [f"{prefix}_{metric}_{int(year)}" for metric, year in wide.columns]
    wide = wide.reset_index()
    for col in [
        f"{prefix}_population_total_2015",
        f"{prefix}_population_total_2025",
        f"{prefix}_youth_population_2025",
    ]:
        if col not in wide.columns:
            wide[col] = 0.0
    wide[f"{prefix}_absolute_change_2015_2025"] = (
        wide[f"{prefix}_population_total_2025"] - wide[f"{prefix}_population_total_2015"]
    )
    wide[f"{prefix}_percent_change_2015_2025"] = wide.apply(
        lambda row: percent_change(row[f"{prefix}_population_total_2025"], row[f"{prefix}_population_total_2015"]),
        axis=1,
    )
    wide[f"{prefix}_youth_share_2025_percent"] = 100 * wide.apply(
        lambda row: safe_divide(row[f"{prefix}_youth_population_2025"], row[f"{prefix}_population_total_2025"]),
        axis=1,
    )
    return wide


def build_country_decomposition(metrics: pd.DataFrame, countries: pd.DataFrame) -> pd.DataFrame:
    high = aggregate_zone(metrics, HIGHLAND_BANDS, "highland")
    low = aggregate_zone(metrics, LOWLAND_BANDS, "lowland")
    merged = high.merge(low, on=["iso3", "country_name", "continent"], how="outer").fillna(0)

    country_cols = ["country_id", "GENC_3", "DOS_Short", "DOS_Long", "WP_Name_ND"]
    lookup_cols = [col for col in country_cols if col in countries.columns]
    country_lookup = countries[lookup_cols].drop_duplicates("GENC_3") if "GENC_3" in lookup_cols else pd.DataFrame()
    if not country_lookup.empty:
        merged = merged.merge(country_lookup, left_on="iso3", right_on="GENC_3", how="left")
    else:
        merged["country_id"] = pd.NA
        merged["DOS_Short"] = pd.NA
        merged["DOS_Long"] = pd.NA
        merged["WP_Name_ND"] = pd.NA

    global_highland_2025 = merged["highland_population_total_2025"].sum()
    global_highland_growth = merged["highland_absolute_change_2015_2025"].sum()
    merged["highland_minus_lowland_growth_difference_pp"] = (
        merged["highland_percent_change_2015_2025"] - merged["lowland_percent_change_2015_2025"]
    )
    merged["country_share_global_highland_2025_population_percent"] = (
        100 * merged["highland_population_total_2025"] / global_highland_2025
    )
    merged["country_share_global_highland_absolute_growth_percent"] = (
        100 * merged["highland_absolute_change_2015_2025"] / global_highland_growth
    )

    out = merged.rename(
        columns={
            "continent": "region",
            "DOS_Short": "country_name_dos_short",
            "DOS_Long": "country_name_dos_long",
            "WP_Name_ND": "worldpop_country_name",
        }
    )
    ordered = [
        "iso3",
        "country_id",
        "country_name",
        "worldpop_country_name",
        "country_name_dos_short",
        "country_name_dos_long",
        "region",
        "highland_population_total_2015",
        "highland_population_total_2025",
        "highland_absolute_change_2015_2025",
        "highland_percent_change_2015_2025",
        "lowland_population_total_2015",
        "lowland_population_total_2025",
        "lowland_absolute_change_2015_2025",
        "lowland_percent_change_2015_2025",
        "highland_minus_lowland_growth_difference_pp",
        "highland_youth_share_2025_percent",
        "lowland_youth_share_2025_percent",
        "country_share_global_highland_2025_population_percent",
        "country_share_global_highland_absolute_growth_percent",
    ]
    return out[ordered].sort_values("highland_population_total_2025", ascending=False).reset_index(drop=True)


def build_concentration(country: pd.DataFrame) -> pd.DataFrame:
    global_highland_pop = country["highland_population_total_2025"].sum()
    global_highland_growth = country["highland_absolute_change_2015_2025"].sum()
    rows: list[dict[str, object]] = []
    for metric, label in [
        ("highland_population_total_2025", "2025 highland population"),
        ("highland_absolute_change_2015_2025", "absolute highland growth, 2015-2025"),
    ]:
        ranked = country.sort_values(metric, ascending=False).reset_index(drop=True)
        for top_n in [10, 20]:
            top = ranked.head(top_n)
            rows.append(
                {
                    "ranking_metric": label,
                    "top_n": top_n,
                    "countries": "; ".join(f"{row.iso3} ({row.country_name})" for row in top.itertuples()),
                    "cumulative_highland_population_2025": top["highland_population_total_2025"].sum(),
                    "cumulative_highland_population_2025_share_percent": 100
                    * safe_divide(top["highland_population_total_2025"].sum(), global_highland_pop),
                    "cumulative_highland_absolute_growth_2015_2025": top[
                        "highland_absolute_change_2015_2025"
                    ].sum(),
                    "cumulative_highland_absolute_growth_2015_2025_share_percent": 100
                    * safe_divide(top["highland_absolute_change_2015_2025"].sum(), global_highland_growth),
                }
            )
    return pd.DataFrame(rows)


def compute_removed_row(base: pd.Series, removed: pd.Series, id_cols: Mapping[str, object]) -> dict[str, object]:
    high_start = base["highland_population_total_2015"] - removed["highland_population_total_2015"]
    high_end = base["highland_population_total_2025"] - removed["highland_population_total_2025"]
    low_start = base["lowland_population_total_2015"] - removed["lowland_population_total_2015"]
    low_end = base["lowland_population_total_2025"] - removed["lowland_population_total_2025"]
    high_growth = percent_change(high_end, high_start)
    low_growth = percent_change(low_end, low_start)
    row = dict(id_cols)
    row.update(
        {
            "remaining_highland_population_2015": high_start,
            "remaining_highland_population_2025": high_end,
            "remaining_highland_absolute_change_2015_2025": high_end - high_start,
            "remaining_highland_growth_percent": high_growth,
            "remaining_lowland_population_2015": low_start,
            "remaining_lowland_population_2025": low_end,
            "remaining_lowland_absolute_change_2015_2025": low_end - low_start,
            "remaining_lowland_growth_percent": low_growth,
            "remaining_highland_minus_lowland_growth_difference_pp": high_growth - low_growth,
            "contrast_reverses_highland_not_greater_than_lowland": bool(high_growth <= low_growth),
        }
    )
    return row


def build_leave_one_country(country: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = country[
        [
            "highland_population_total_2015",
            "highland_population_total_2025",
            "lowland_population_total_2015",
            "lowland_population_total_2025",
        ]
    ].sum()
    rows = []
    for row in country.itertuples(index=False):
        removed = pd.Series(
            {
                "highland_population_total_2015": row.highland_population_total_2015,
                "highland_population_total_2025": row.highland_population_total_2025,
                "lowland_population_total_2015": row.lowland_population_total_2015,
                "lowland_population_total_2025": row.lowland_population_total_2025,
            }
        )
        rows.append(
            compute_removed_row(
                base,
                removed,
                {
                    "removed_iso3": row.iso3,
                    "removed_country_name": row.country_name,
                    "removed_region": row.region,
                    "removed_highland_population_2025": row.highland_population_total_2025,
                    "removed_highland_absolute_growth_2015_2025": row.highland_absolute_change_2015_2025,
                },
            )
        )
    loo = pd.DataFrame(rows).sort_values("remaining_highland_minus_lowland_growth_difference_pp")
    summary = summarize_leave_one(loo, "country")
    return loo, summary


def summarize_leave_one(loo: pd.DataFrame, unit: str) -> pd.DataFrame:
    id_col = f"removed_{unit}_name" if f"removed_{unit}_name" in loo.columns else f"removed_{unit}"
    min_diff = loo.loc[loo["remaining_highland_minus_lowland_growth_difference_pp"].idxmin()]
    max_diff = loo.loc[loo["remaining_highland_minus_lowland_growth_difference_pp"].idxmax()]
    min_high = loo.loc[loo["remaining_highland_growth_percent"].idxmin()]
    max_high = loo.loc[loo["remaining_highland_growth_percent"].idxmax()]
    min_low = loo.loc[loo["remaining_lowland_growth_percent"].idxmin()]
    max_low = loo.loc[loo["remaining_lowland_growth_percent"].idxmax()]
    return pd.DataFrame(
        [
            {
                "leave_one_unit": unit,
                "n_units_tested": len(loo),
                "min_highland_growth_percent": min_high["remaining_highland_growth_percent"],
                "min_highland_growth_removed_unit": min_high[id_col],
                "max_highland_growth_percent": max_high["remaining_highland_growth_percent"],
                "max_highland_growth_removed_unit": max_high[id_col],
                "min_lowland_growth_percent": min_low["remaining_lowland_growth_percent"],
                "min_lowland_growth_removed_unit": min_low[id_col],
                "max_lowland_growth_percent": max_low["remaining_lowland_growth_percent"],
                "max_lowland_growth_removed_unit": max_low[id_col],
                "min_highland_minus_lowland_difference_pp": min_diff[
                    "remaining_highland_minus_lowland_growth_difference_pp"
                ],
                "min_difference_removed_unit": min_diff[id_col],
                "max_highland_minus_lowland_difference_pp": max_diff[
                    "remaining_highland_minus_lowland_growth_difference_pp"
                ],
                "max_difference_removed_unit": max_diff[id_col],
                "contrast_ever_reverses": bool(
                    loo["contrast_reverses_highland_not_greater_than_lowland"].any()
                ),
            }
        ]
    )


def build_leave_one_region(country: pd.DataFrame, region_available: bool) -> pd.DataFrame:
    if not region_available:
        return pd.DataFrame(
            [
                {
                    "status": "region unavailable",
                    "notes": "Region/continent fields were not available in local source tables.",
                }
            ]
        )
    region = (
        country.groupby("region", dropna=False)
        .agg(
            highland_population_total_2015=("highland_population_total_2015", "sum"),
            highland_population_total_2025=("highland_population_total_2025", "sum"),
            highland_absolute_change_2015_2025=("highland_absolute_change_2015_2025", "sum"),
            lowland_population_total_2015=("lowland_population_total_2015", "sum"),
            lowland_population_total_2025=("lowland_population_total_2025", "sum"),
        )
        .reset_index()
    )
    base = region[
        [
            "highland_population_total_2015",
            "highland_population_total_2025",
            "lowland_population_total_2015",
            "lowland_population_total_2025",
        ]
    ].sum()
    rows = []
    for row in region.itertuples(index=False):
        removed = pd.Series(
            {
                "highland_population_total_2015": row.highland_population_total_2015,
                "highland_population_total_2025": row.highland_population_total_2025,
                "lowland_population_total_2015": row.lowland_population_total_2015,
                "lowland_population_total_2025": row.lowland_population_total_2025,
            }
        )
        rows.append(
            compute_removed_row(
                base,
                removed,
                {
                    "removed_region": row.region,
                    "removed_highland_population_2025": row.highland_population_total_2025,
                    "removed_highland_absolute_growth_2015_2025": row.highland_absolute_change_2015_2025,
                },
            )
        )
    return pd.DataFrame(rows).sort_values("remaining_highland_minus_lowland_growth_difference_pp")


def build_country_standardized(country: pd.DataFrame, threshold: float) -> pd.DataFrame:
    eligible = country[
        (country["highland_population_total_2025"] >= threshold)
        & (country["lowland_population_total_2025"] >= threshold)
        & country["highland_minus_lowland_growth_difference_pp"].notna()
    ].copy()
    if eligible.empty:
        weighted = math.nan
    else:
        weighted = (
            eligible["highland_minus_lowland_growth_difference_pp"] * eligible["highland_population_total_2025"]
        ).sum() / eligible["highland_population_total_2025"].sum()
    return pd.DataFrame(
        [
            {
                "minimum_population_2025_threshold": threshold,
                "n_countries_with_meaningful_population_in_both_zones": len(eligible),
                "n_countries_highland_growth_exceeds_lowland_growth": int(
                    (eligible["highland_minus_lowland_growth_difference_pp"] > 0).sum()
                ),
                "share_countries_highland_growth_exceeds_lowland_growth_percent": 100
                * safe_divide((eligible["highland_minus_lowland_growth_difference_pp"] > 0).sum(), len(eligible)),
                "unweighted_mean_highland_minus_lowland_difference_pp": eligible[
                    "highland_minus_lowland_growth_difference_pp"
                ].mean(),
                "median_highland_minus_lowland_difference_pp": eligible[
                    "highland_minus_lowland_growth_difference_pp"
                ].median(),
                "highland_population_weighted_mean_difference_pp": weighted,
                "included_iso3": "; ".join(eligible.sort_values("iso3")["iso3"].astype(str).tolist()),
            }
        ]
    )


def build_quality_checks(country: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    totals = {
        "<500 m 2025 population": country["lowland_population_total_2025"].sum(),
        "<100 m 2025 population": metrics[
            metrics["band_id"].isin([1, 2, 3, 4]) & metrics["year"].eq(2025)
        ]["population_total"].sum(),
        "1500-3500 m 2025 population": country["highland_population_total_2025"].sum(),
        "highland growth": percent_change(
            country["highland_population_total_2025"].sum(), country["highland_population_total_2015"].sum()
        ),
        "lowland growth": percent_change(
            country["lowland_population_total_2025"].sum(), country["lowland_population_total_2015"].sum()
        ),
    }
    targets = {
        "<500 m 2025 population": 6.24e9,
        "<100 m 2025 population": 3.51e9,
        "1500-3500 m 2025 population": 522e6,
        "highland growth": 17.5,
        "lowland growth": 9.0,
    }
    rows = []
    for metric, value in totals.items():
        target = targets[metric]
        rows.append(
            {
                "metric": metric,
                "computed_value": value,
                "target_approximate_value": target,
                "absolute_difference": value - target,
                "relative_difference_percent": 100 * safe_divide(value - target, target),
            }
        )
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--min-population-threshold", type=float, default=100_000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    metrics, countries, region_available = load_source_tables(args.source_root)
    country = build_country_decomposition(metrics, countries)
    concentration = build_concentration(country)
    leave_one_country, leave_one_country_summary = build_leave_one_country(country)
    leave_one_region = build_leave_one_region(country, region_available)
    standardized = build_country_standardized(country, args.min_population_threshold)
    quality_checks = build_quality_checks(country, metrics)

    outputs = {
        "country_highland_lowland": country,
        "concentration_summary": concentration,
        "leave_one_country_out": leave_one_country,
        "leave_one_country_out_summary": leave_one_country_summary,
        "leave_one_region_out": leave_one_region,
        "country_standardized_comparison": standardized,
        "quality_checks": quality_checks,
    }
    for name, df in outputs.items():
        df.to_csv(CSV_OUTPUTS[name], index=False)

    for name, path in CSV_OUTPUTS.items():
        print(f"Wrote {name}: {path}")
    print("Quality checks:")
    print(quality_checks.to_string(index=False))


if __name__ == "__main__":
    main()
