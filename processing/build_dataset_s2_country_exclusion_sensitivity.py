"""Build Dataset S2 country-exclusion sensitivity table and ingredients.

This adds a targeted robustness table for the main lowland/highland headline
metrics without modifying Dataset S1, manuscript text, or figure outputs.

The compact ingredients table stores only the full-sample and selected-country
population totals needed to regenerate the sensitivity table. If the larger
static-2025 demographic metrics parquet is available one directory above this
repo, ingredients are rebuilt from it; otherwise the script regenerates the
sensitivity table from the compact ingredients already included in Dataset S2.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_TABLES = ROOT / "outputs" / "tables"
SUPPLEMENTARY_S2 = ROOT / "outputs" / "supplementary" / "dataset_s2"

SOURCE_CANDIDATES = [
    ROOT.parent
    / "hypsographic_demography_download_data"
    / "data"
    / "static_2025"
    / "fact_enriched_demographic_metrics.parquet",
    ROOT.parent
    / "hypsographic_demography_public_release_v1"
    / "data"
    / "static_2025"
    / "fact_enriched_demographic_metrics.parquet",
]

OUT_TABLE = OUTPUT_TABLES / "dataset_s2_country_exclusion_sensitivity.csv"
OUT_SUPPLEMENTARY = SUPPLEMENTARY_S2 / "dataset_s2_country_exclusion_sensitivity.csv"
INGREDIENT_TABLE = OUTPUT_TABLES / "dataset_s2_country_exclusion_ingredients.csv"
INGREDIENT_SUPPLEMENTARY = SUPPLEMENTARY_S2 / "dataset_s2_country_exclusion_ingredients.csv"

EXCLUDED_COUNTRIES = {
    "ETH": "Ethiopia",
    "MEX": "Mexico",
    "KEN": "Kenya",
    "YEM": "Yemen",
    "AFG": "Afghanistan",
}

ELEVATION_BIN_TO_GROUP = {
    "<0": "<100 m",
    "0-9": "<100 m",
    "10-49": "<100 m",
    "50-99": "<100 m",
    "100-199": "100-499 m",
    "200-299": "100-499 m",
    "300-399": "100-499 m",
    "400-499": "100-499 m",
    "500-999": "500-1499 m",
    "1000-1499": "500-1499 m",
    "1500-1999": "1500-2499 m",
    "2000-2499": "1500-2499 m",
    "2500-2999": "2500-3499 m",
    "3000-3499": "2500-3499 m",
    "3500-3999": ">=3500 m",
    "4000-4499": ">=3500 m",
    "4500-4999": ">=3500 m",
    "5000-5499": ">=3500 m",
    "5500-5999": ">=3500 m",
    "6000-6499": ">=3500 m",
    "6500-6999": ">=3500 m",
    "7000-7499": ">=3500 m",
    "7500-7999": ">=3500 m",
    "8000+": ">=3500 m",
}

LOWLAND_GROUPS = ["<100 m", "100-499 m"]
HIGHLAND_GROUPS = ["1500-2499 m", "2500-3499 m"]
VERY_HIGH_GROUPS = [">=3500 m"]
INGREDIENT_COLUMNS = [
    "ingredient_scope",
    "iso3",
    "country_name",
    "year",
    "elevation_group",
    "population_total",
    "youth_population",
]


def find_source() -> Path | None:
    for path in SOURCE_CANDIDATES:
        if path.exists():
            return path
    return None


def percent_growth(pop_2015: float, pop_2025: float) -> float:
    return (pop_2025 - pop_2015) / pop_2015 * 100


def youth_share_percent(youth_2025: float, pop_2025: float) -> float:
    return youth_2025 / pop_2025 * 100


def zone_totals(df: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    return (
        df[df["elevation_group"].isin(groups)]
        .groupby("year", as_index=False)[["population_total", "youth_population"]]
        .sum()
    )


def value_for_year(totals: pd.DataFrame, year: int, column: str) -> float:
    return float(totals.loc[totals["year"].eq(year), column].sum())


def summarize_scenario(df: pd.DataFrame, scenario: str, excluded_iso3: str | None) -> dict[str, object]:
    low = zone_totals(df, LOWLAND_GROUPS)
    high = zone_totals(df, HIGHLAND_GROUPS)
    very_high = zone_totals(df, VERY_HIGH_GROUPS)

    low_2015 = value_for_year(low, 2015, "population_total")
    low_2025 = value_for_year(low, 2025, "population_total")
    high_2015 = value_for_year(high, 2015, "population_total")
    high_2025 = value_for_year(high, 2025, "population_total")
    very_high_2025 = value_for_year(very_high, 2025, "population_total")

    low_youth_2025 = value_for_year(low, 2025, "youth_population")
    high_youth_2025 = value_for_year(high, 2025, "youth_population")

    low_growth = percent_growth(low_2015, low_2025)
    high_growth = percent_growth(high_2015, high_2025)
    low_youth_share = youth_share_percent(low_youth_2025, low_2025)
    high_youth_share = youth_share_percent(high_youth_2025, high_2025)

    return {
        "table_name": "country_exclusion_sensitivity",
        "scenario": scenario,
        "excluded_iso3": excluded_iso3 or "",
        "excluded_country": EXCLUDED_COUNTRIES.get(excluded_iso3 or "", ""),
        "population_below_500m_2015": low_2015,
        "population_below_500m_2025": low_2025,
        "population_1500_3500m_2015": high_2015,
        "population_1500_3500m_2025": high_2025,
        "population_above_3500m_2025": very_high_2025,
        "growth_below_500m_2015_2025_percent": low_growth,
        "growth_1500_3500m_2015_2025_percent": high_growth,
        "youth_share_below_500m_2025_percent": low_youth_share,
        "youth_share_1500_3500m_2025_percent": high_youth_share,
        "highland_minus_lowland_growth_difference_pp": high_growth - low_growth,
        "highland_minus_lowland_youth_share_difference_pp": high_youth_share - low_youth_share,
    }


def load_metrics(path: Path) -> pd.DataFrame:
    cols = [
        "iso3",
        "country_name",
        "year",
        "elevation_bin",
        "population_total",
        "youth_population",
    ]
    df = pd.read_parquet(path, columns=cols)
    df = df[df["year"].isin([2015, 2025])].copy()
    df["elevation_group"] = df["elevation_bin"].map(ELEVATION_BIN_TO_GROUP)
    if df["elevation_group"].isna().any():
        missing = df.loc[df["elevation_group"].isna(), "elevation_bin"].drop_duplicates()
        raise ValueError(f"Unmapped elevation bins: {missing.tolist()}")
    return df


def build_ingredients(metrics: pd.DataFrame) -> pd.DataFrame:
    full_sample = (
        metrics.groupby(["year", "elevation_group"], as_index=False)[["population_total", "youth_population"]]
        .sum()
        .assign(ingredient_scope="full_sample", iso3="", country_name="")
    )
    country = (
        metrics[metrics["iso3"].isin(EXCLUDED_COUNTRIES)]
        .groupby(["iso3", "country_name", "year", "elevation_group"], as_index=False)[
            ["population_total", "youth_population"]
        ]
        .sum()
        .assign(ingredient_scope="excluded_country")
    )
    ingredients = pd.concat([full_sample, country], ignore_index=True)
    ingredients = ingredients[INGREDIENT_COLUMNS].sort_values(
        ["ingredient_scope", "iso3", "year", "elevation_group"],
        kind="stable",
    )
    return ingredients


def load_ingredients(path: Path) -> pd.DataFrame:
    if not path.exists():
        searched = "\n".join(str(candidate) for candidate in SOURCE_CANDIDATES)
        raise FileNotFoundError(
            "Could not find either compact ingredients or static-2025 demographic metrics source.\n"
            f"Missing ingredients: {path}\n"
            f"Searched source candidates:\n{searched}"
        )
    ingredients = pd.read_csv(path)
    missing = [col for col in INGREDIENT_COLUMNS if col not in ingredients.columns]
    if missing:
        raise ValueError(f"Ingredient table is missing required columns: {missing}")
    ingredients["iso3"] = ingredients["iso3"].fillna("")
    ingredients["country_name"] = ingredients["country_name"].fillna("")
    return ingredients[INGREDIENT_COLUMNS].copy()


def scenario_elevation_table(ingredients: pd.DataFrame, excluded_iso3: str | None) -> pd.DataFrame:
    full = ingredients[ingredients["ingredient_scope"].eq("full_sample")][
        ["year", "elevation_group", "population_total", "youth_population"]
    ].copy()
    if excluded_iso3 is None:
        return full

    country = ingredients[
        ingredients["ingredient_scope"].eq("excluded_country")
        & ingredients["iso3"].eq(excluded_iso3)
    ][["year", "elevation_group", "population_total", "youth_population"]].copy()
    if country.empty:
        raise ValueError(f"No ingredient rows found for excluded country {excluded_iso3}")

    scenario = full.merge(
        country,
        on=["year", "elevation_group"],
        how="left",
        suffixes=("", "_excluded"),
    )
    scenario[["population_total_excluded", "youth_population_excluded"]] = scenario[
        ["population_total_excluded", "youth_population_excluded"]
    ].fillna(0)
    scenario["population_total"] = scenario["population_total"] - scenario["population_total_excluded"]
    scenario["youth_population"] = scenario["youth_population"] - scenario["youth_population_excluded"]
    return scenario[["year", "elevation_group", "population_total", "youth_population"]]


def write_csv_pair(df: pd.DataFrame, table_path: Path, supplementary_path: Path) -> None:
    table_path.parent.mkdir(parents=True, exist_ok=True)
    supplementary_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(table_path, index=False)
    df.to_csv(supplementary_path, index=False)


def manuscript_reference() -> dict[str, float]:
    fig1 = pd.read_csv(OUTPUT_TABLES / "main_fig01_data.csv")
    low = fig1[fig1["elevation_group"].isin(LOWLAND_GROUPS)]
    high = fig1[fig1["elevation_group"].isin(HIGHLAND_GROUPS)]
    very_high = fig1[fig1["elevation_group"].isin(VERY_HIGH_GROUPS)]
    return {
        "population_below_500m_2015": low["population_total_start"].sum(),
        "population_below_500m_2025": low["population_total"].sum(),
        "population_1500_3500m_2015": high["population_total_start"].sum(),
        "population_1500_3500m_2025": high["population_total"].sum(),
        "population_above_3500m_2025": very_high["population_total"].sum(),
        "growth_below_500m_2015_2025_percent": percent_growth(
            low["population_total_start"].sum(), low["population_total"].sum()
        ),
        "growth_1500_3500m_2015_2025_percent": percent_growth(
            high["population_total_start"].sum(), high["population_total"].sum()
        ),
        "youth_share_below_500m_2025_percent": youth_share_percent(
            low["youth_population"].sum(), low["population_total"].sum()
        ),
        "youth_share_1500_3500m_2025_percent": youth_share_percent(
            high["youth_population"].sum(), high["population_total"].sum()
        ),
    }


def print_full_sample_check(full_sample: dict[str, object]) -> None:
    reference = manuscript_reference()
    print("Full-sample check against current manuscript values:")
    for key, expected in reference.items():
        observed = float(full_sample[key])
        diff = observed - expected
        print(f"- {key}: observed={observed:.12g}; expected={expected:.12g}; diff={diff:.6g}")


def print_interpretation_summary(table: pd.DataFrame) -> None:
    reversals = table[
        (table["highland_minus_lowland_growth_difference_pp"] <= 0)
        | (table["highland_minus_lowland_youth_share_difference_pp"] <= 0)
    ].copy()
    min_growth = table["highland_minus_lowland_growth_difference_pp"].min()
    min_youth = table["highland_minus_lowland_youth_share_difference_pp"].min()
    if reversals.empty:
        print(
            "Interpretation summary: no exclusion changes the main pattern; "
            "1,500-3,500 m remains higher than <500 m for both 2015-2025 growth "
            f"(minimum difference {min_growth:.2f} pp) and 2025 youth share "
            f"(minimum difference {min_youth:.2f} pp)."
        )
    else:
        scenarios = ", ".join(reversals["scenario"].tolist())
        print(
            "Interpretation summary: at least one exclusion changes a headline contrast "
            f"or makes it non-positive: {scenarios}."
        )


def main() -> None:
    source = find_source()
    if source is not None:
        metrics = load_metrics(source)
        ingredients = build_ingredients(metrics)
        source_note = f"rebuilt ingredients from {source}"
    else:
        ingredients = load_ingredients(INGREDIENT_TABLE)
        source_note = f"loaded compact ingredients from {INGREDIENT_TABLE}"

    write_csv_pair(ingredients, INGREDIENT_TABLE, INGREDIENT_SUPPLEMENTARY)

    rows: list[dict[str, object]] = [
        summarize_scenario(scenario_elevation_table(ingredients, None), "full_sample", None)
    ]
    for iso3 in EXCLUDED_COUNTRIES:
        scenario_df = scenario_elevation_table(ingredients, iso3)
        rows.append(summarize_scenario(scenario_df, f"exclude_{iso3}", iso3))

    out = pd.DataFrame(rows)
    write_csv_pair(out, OUT_TABLE, OUT_SUPPLEMENTARY)

    print(f"Wrote {OUT_TABLE}")
    print(f"Wrote {OUT_SUPPLEMENTARY}")
    print(f"Wrote {INGREDIENT_TABLE}")
    print(f"Wrote {INGREDIENT_SUPPLEMENTARY}")
    print(f"Source: {source_note}")
    print_full_sample_check(rows[0])
    print_interpretation_summary(out)


if __name__ == "__main__":
    main()
