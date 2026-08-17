"""Build the 2025 within-country lowland/highland age-structure comparison.

This analysis deliberately reuses the elevation-bin mapping and zone definitions
from the existing country-level sensitivity pipeline. Countries are retained only
when both their <500 m and 1,500-3,499 m populations reach 100,000 in 2025.
Age shares are ratios of population counts summed within each country-zone; no
grid-cell percentages are calculated or averaged.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "v1" / "data" / "static_2025" / "fact_enriched_population_age_sex.parquet"
EXISTING_SAMPLE = ROOT / "data" / "country_comparisons" / "within_country_growth.csv"
EXISTING_COUNTRY_COMPARISON = (
    ROOT / "data" / "country_comparisons" / "country_zone_counts_2015_2025.csv"
)
OUTPUT = ROOT / "data" / "country_comparisons" / "within_country_age_structure_2025.csv"

YEAR = 2025
MINIMUM_ZONE_POPULATION = 100_000
EXPECTED_COUNTRY_COUNT = 48
YOUTH_AGE_GROUPS = {"0-4", "5-9", "10-14"}
OLDER_AGE_GROUPS = {"65-69", "70-74", "75-79", "80-84", "85-89", "90+"}

# Exact bin mapping used by the existing within-country growth comparison.
ELEVATION_BIN_TO_GROUP = {
    "<0": "<100 m", "0-9": "<100 m", "10-49": "<100 m", "50-99": "<100 m",
    "100-199": "100-499 m", "200-299": "100-499 m", "300-399": "100-499 m",
    "400-499": "100-499 m", "500-999": "500-1499 m", "1000-1499": "500-1499 m",
    "1500-1999": "1500-2499 m", "2000-2499": "1500-2499 m",
    "2500-2999": "2500-3499 m", "3000-3499": "2500-3499 m",
    "3500-3999": ">=3500 m", "4000-4499": ">=3500 m", "4500-4999": ">=3500 m",
    "5000-5499": ">=3500 m", "5500-5999": ">=3500 m", "6000-6499": ">=3500 m",
    "6500-6999": ">=3500 m", "7000-7499": ">=3500 m", "7500-7999": ">=3500 m",
    "8000+": ">=3500 m",
}
LOWLAND_GROUPS = ["<100 m", "100-499 m"]
HIGHLAND_GROUPS = ["1500-2499 m", "2500-3499 m"]


def bins_for_groups(groups: list[str]) -> list[str]:
    """Return source elevation bins assigned to the requested existing groups."""
    return [
        elevation_bin
        for elevation_bin, elevation_group in ELEVATION_BIN_TO_GROUP.items()
        if elevation_group in groups
    ]


def load_expected_sample() -> set[str]:
    """Load the exact ISO3 cohort recorded by the existing growth comparison."""
    comparison = pd.read_csv(EXISTING_SAMPLE)
    iso3 = set(comparison["iso3"])
    if len(iso3) != EXPECTED_COUNTRY_COUNT:
        raise AssertionError(
            f"Existing comparison contains {len(iso3)} countries, expected {EXPECTED_COUNTRY_COUNT}"
        )
    return iso3


def load_population_counts() -> pd.DataFrame:
    """Read only 2025 age-population counts in the two comparison zones."""
    if not SOURCE.exists():
        raise FileNotFoundError(f"Missing processed age-sex source: {SOURCE}")

    lowland_bins = bins_for_groups(LOWLAND_GROUPS)
    highland_bins = bins_for_groups(HIGHLAND_GROUPS)
    selected_bins = lowland_bins + highland_bins
    dataset = ds.dataset(SOURCE, format="parquet")
    required = {
        "iso3",
        "country_name",
        "year",
        "elevation_bin",
        "analysis_age_group",
        "population_value",
    }
    missing = required.difference(dataset.schema.names)
    if missing:
        raise ValueError(f"Processed source is missing columns: {sorted(missing)}")

    table = dataset.to_table(
        columns=sorted(required),
        filter=(ds.field("year") == YEAR) & ds.field("elevation_bin").isin(selected_bins),
    )
    counts = table.to_pandas()
    if counts.empty:
        raise AssertionError("No 2025 population counts found in the selected elevation zones")
    if counts["population_value"].isna().any() or (counts["population_value"] < 0).any():
        raise AssertionError("Population counts must be non-missing and non-negative")

    zone_by_bin = {
        **{value: "lowland" for value in lowland_bins},
        **{value: "highland" for value in highland_bins},
    }
    counts["zone"] = counts["elevation_bin"].map(zone_by_bin)
    if counts["zone"].isna().any():
        raise AssertionError("At least one selected elevation bin was not assigned to a zone")
    return counts


def aggregate_country_zones(counts: pd.DataFrame) -> pd.DataFrame:
    """Aggregate counts first, then calculate country-zone age shares."""
    working = counts.copy()
    working["youth_population_2025"] = working["population_value"].where(
        working["analysis_age_group"].isin(YOUTH_AGE_GROUPS), 0.0
    )
    working["older_population_2025"] = working["population_value"].where(
        working["analysis_age_group"].isin(OLDER_AGE_GROUPS), 0.0
    )

    # Select one stable display name per ISO3, weighted toward the name carrying
    # the most population in case the processed source contains name variants.
    country_names = (
        working.groupby(["iso3", "country_name"], as_index=False)["population_value"]
        .sum()
        .sort_values(["iso3", "population_value", "country_name"], ascending=[True, False, True])
        .drop_duplicates("iso3")[["iso3", "country_name"]]
    )
    aggregated = (
        working.groupby(["iso3", "zone"], as_index=False)[
            ["population_value", "youth_population_2025", "older_population_2025"]
        ]
        .sum()
        .rename(columns={"population_value": "population_2025"})
    )
    wide = aggregated.pivot(
        index="iso3",
        columns="zone",
        values=["population_2025", "youth_population_2025", "older_population_2025"],
    )
    wide.columns = [f"{zone}_{metric}" for metric, zone in wide.columns]
    wide = wide.reset_index().fillna(0).merge(country_names, on="iso3", how="left", validate="one_to_one")

    expected_columns = [
        "lowland_population_2025",
        "highland_population_2025",
        "lowland_youth_population_2025",
        "highland_youth_population_2025",
        "lowland_older_population_2025",
        "highland_older_population_2025",
    ]
    missing = [column for column in expected_columns if column not in wide.columns]
    if missing:
        raise AssertionError(f"Country-zone aggregation is missing columns: {missing}")

    included = wide[
        (wide["lowland_population_2025"] >= MINIMUM_ZONE_POPULATION)
        & (wide["highland_population_2025"] >= MINIMUM_ZONE_POPULATION)
    ].copy()
    expected_iso3 = load_expected_sample()
    observed_iso3 = set(included["iso3"])
    if observed_iso3 != expected_iso3:
        raise AssertionError(
            "Threshold-derived sample differs from the existing growth-comparison sample; "
            f"only expected={sorted(expected_iso3 - observed_iso3)}, "
            f"only observed={sorted(observed_iso3 - expected_iso3)}"
        )
    if len(included) != EXPECTED_COUNTRY_COUNT:
        raise AssertionError(f"Expected {EXPECTED_COUNTRY_COUNT} countries, found {len(included)}")

    included["lowland_youth_share_2025_percent"] = (
        100 * included["lowland_youth_population_2025"] / included["lowland_population_2025"]
    )
    included["highland_youth_share_2025_percent"] = (
        100 * included["highland_youth_population_2025"] / included["highland_population_2025"]
    )
    included["highland_minus_lowland_youth_share_difference_pp"] = (
        included["highland_youth_share_2025_percent"]
        - included["lowland_youth_share_2025_percent"]
    )
    included["lowland_older_age_share_2025_percent"] = (
        100 * included["lowland_older_population_2025"] / included["lowland_population_2025"]
    )
    included["highland_older_age_share_2025_percent"] = (
        100 * included["highland_older_population_2025"] / included["highland_population_2025"]
    )
    included["highland_minus_lowland_older_age_share_difference_pp"] = (
        included["highland_older_age_share_2025_percent"]
        - included["lowland_older_age_share_2025_percent"]
    )

    columns = [
        "iso3",
        "country_name",
        "lowland_population_2025",
        "highland_population_2025",
        "lowland_youth_population_2025",
        "highland_youth_population_2025",
        "lowland_youth_share_2025_percent",
        "highland_youth_share_2025_percent",
        "highland_minus_lowland_youth_share_difference_pp",
        "lowland_older_population_2025",
        "highland_older_population_2025",
        "lowland_older_age_share_2025_percent",
        "highland_older_age_share_2025_percent",
        "highland_minus_lowland_older_age_share_difference_pp",
    ]
    return included[columns].sort_values(["country_name", "iso3"], kind="stable").reset_index(drop=True)


def qa_checks(result: pd.DataFrame) -> None:
    """Confirm sample identity, aggregation-first shares, and source reconciliation."""
    if len(result) != EXPECTED_COUNTRY_COUNT or result["iso3"].nunique() != EXPECTED_COUNTRY_COUNT:
        raise AssertionError("QA failed: output is not one row for each of 48 countries")

    share_specs = [
        ("lowland_youth_share_2025_percent", "lowland_youth_population_2025", "lowland_population_2025"),
        ("highland_youth_share_2025_percent", "highland_youth_population_2025", "highland_population_2025"),
        ("lowland_older_age_share_2025_percent", "lowland_older_population_2025", "lowland_population_2025"),
        ("highland_older_age_share_2025_percent", "highland_older_population_2025", "highland_population_2025"),
    ]
    for share_column, numerator_column, denominator_column in share_specs:
        expected = 100 * result[numerator_column] / result[denominator_column]
        if not np.allclose(result[share_column], expected, rtol=0, atol=1e-12):
            raise AssertionError(f"QA failed: {share_column} is not derived from aggregated counts")
        if not result[share_column].between(0, 100).all():
            raise AssertionError(f"QA failed: {share_column} falls outside 0-100%")

    existing = pd.read_csv(EXISTING_COUNTRY_COMPARISON)
    existing["lowland_youth_population_2025"] = (
        existing["lowland_population_total_2025"]
        * existing["lowland_youth_share_2025_percent"]
        / 100
    )
    existing["highland_youth_population_2025"] = (
        existing["highland_population_total_2025"]
        * existing["highland_youth_share_2025_percent"]
        / 100
    )
    reference = existing.groupby("iso3", as_index=False)[
        [
            "lowland_population_total_2025",
            "highland_population_total_2025",
            "lowland_youth_population_2025",
            "highland_youth_population_2025",
        ]
    ].sum()
    check = result.merge(reference, on="iso3", how="left", validate="one_to_one")
    comparisons = [
        ("lowland_population_2025", "lowland_population_total_2025"),
        ("highland_population_2025", "highland_population_total_2025"),
        ("lowland_youth_population_2025_x", "lowland_youth_population_2025_y"),
        ("highland_youth_population_2025_x", "highland_youth_population_2025_y"),
    ]
    for observed_column, reference_column in comparisons:
        if not np.allclose(check[observed_column], check[reference_column], rtol=1e-10, atol=1e-5):
            raise AssertionError(
                f"QA failed: {observed_column} does not reconcile with the existing country comparison"
            )

    combined_share = (
        result["lowland_youth_share_2025_percent"]
        + result["lowland_older_age_share_2025_percent"]
    )
    if (combined_share > 100 + 1e-10).any():
        raise AssertionError("QA failed: lowland youth and older-age shares exceed 100%")
    combined_share = (
        result["highland_youth_share_2025_percent"]
        + result["highland_older_age_share_2025_percent"]
    )
    if (combined_share > 100 + 1e-10).any():
        raise AssertionError("QA failed: highland youth and older-age shares exceed 100%")


def summarize(result: pd.DataFrame) -> dict[str, float | int]:
    youth_difference = result["highland_minus_lowland_youth_share_difference_pp"]
    older_difference = result["highland_minus_lowland_older_age_share_difference_pp"]
    youth_count = int((youth_difference > 0).sum())
    older_count = int((older_difference > 0).sum())
    n = len(result)
    return {
        "n_countries": n,
        "n_highland_youth_share_greater": youth_count,
        "percent_highland_youth_share_greater": 100 * youth_count / n,
        "mean_youth_difference_pp": float(youth_difference.mean()),
        "median_youth_difference_pp": float(youth_difference.median()),
        "n_highland_older_share_greater": older_count,
        "percent_highland_older_share_greater": 100 * older_count / n,
        "mean_older_difference_pp": float(older_difference.mean()),
        "median_older_difference_pp": float(older_difference.median()),
    }


def print_results_summary(summary: dict[str, float | int]) -> None:
    print("QA checks: PASS")
    print(
        f"- Sample contains {summary['n_countries']} countries, matching the existing "
        "within-country growth comparison."
    )
    print(
        "- Age shares were calculated after summing 2025 age-specific population counts "
        "within each country-zone; no grid-cell percentages were averaged."
    )
    print("Results-ready summary:")
    print(
        f"Among the {summary['n_countries']} countries with at least 100,000 residents in "
        "both lowlands (<500 m) and highlands (1,500-3,499 m) in 2025, highland youth "
        f"shares exceeded lowland youth shares in {summary['n_highland_youth_share_greater']} "
        f"countries ({summary['percent_highland_youth_share_greater']:.1f}%). The unweighted "
        "highland-minus-lowland youth-share difference averaged "
        f"{summary['mean_youth_difference_pp']:+.2f} percentage points (median "
        f"{summary['median_youth_difference_pp']:+.2f}). Highland older-age shares exceeded "
        f"lowland older-age shares in {summary['n_highland_older_share_greater']} countries "
        f"({summary['percent_highland_older_share_greater']:.1f}%), with an unweighted mean "
        f"difference of {summary['mean_older_difference_pp']:+.2f} percentage points "
        f"(median {summary['median_older_difference_pp']:+.2f})."
    )


def main() -> None:
    counts = load_population_counts()
    result = aggregate_country_zones(counts)
    qa_checks(result)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT, index=False, float_format="%.10f")
    print(f"Wrote {OUTPUT}")
    print_results_summary(summarize(result))


if __name__ == "__main__":
    main()
