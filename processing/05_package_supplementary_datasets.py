"""Package supplementary Dataset S1 and Dataset S2 CSV folders.

The script copies, cleans, and harmonizes selected analysis outputs into
CSV-only supplementary folders with README files. It does not modify Dataset S1,
Dataset S2, figures, or intermediate source outputs in place.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_TABLES = ROOT / "outputs" / "tables"
DATA_DIR = ROOT / "data"
SUPPLEMENTARY_DIR = ROOT / "outputs" / "supplementary"
S1_DIR = SUPPLEMENTARY_DIR / "dataset_s1"
S2_DIR = SUPPLEMENTARY_DIR / "dataset_s2"

FLOAT_FORMAT = "%.17g"


S1_SOURCES = [
    (
        OUTPUT_TABLES / "main_fig01_data.csv",
        S1_DIR / "dataset_s1_fig01_population_age_growth.csv",
        "Fig. 1 population, age composition, and 2015-2025 growth by elevation group.",
    ),
    (
        OUTPUT_TABLES / "fig01_age_contribution_values.csv",
        S1_DIR / "dataset_s1_fig01_age_contributions.csv",
        "Fig. 1 age-class contributions to total growth by elevation group.",
    ),
    (
        OUTPUT_TABLES / "main_fig02_static2025_data.csv",
        S1_DIR / "dataset_s1_fig02_settlement_static2025.csv",
        "Fig. 2 static-2025 settlement source data by elevation group and settlement class.",
    ),
    (
        OUTPUT_TABLES / "key_values_for_manuscript.csv",
        S1_DIR / "dataset_s1_key_manuscript_values.csv",
        "Headline manuscript values and companion threshold values used in the paper.",
    ),
]


S2_SOURCES = [
    (
        DATA_DIR / "dataset_s2_robustness_checks.csv",
        S2_DIR / "dataset_s2_primary_robustness_checks.csv",
        "Primary robustness, highland threshold, and settlement-class sensitivity checks.",
    ),
    (
        OUTPUT_TABLES / "dynamic_vs_static2025_fig02_comparison.csv",
        S2_DIR / "dataset_s2_dynamic_vs_static2025_settlement.csv",
        "Dynamic versus static-2025 settlement attribution comparison.",
    ),
    (
        OUTPUT_TABLES / "dataset_s2_country_highland_lowland.csv",
        S2_DIR / "dataset_s2_country_highland_lowland.csv",
        "Country-level highland and lowland decomposition.",
    ),
    (
        OUTPUT_TABLES / "dataset_s2_concentration_summary.csv",
        S2_DIR / "dataset_s2_concentration_summary.csv",
        "Top-10 and top-20 country concentration summaries.",
    ),
    (
        OUTPUT_TABLES / "dataset_s2_leave_one_country_out.csv",
        S2_DIR / "dataset_s2_leave_one_country_out.csv",
        "Leave-one-country-out robustness table.",
    ),
    (
        OUTPUT_TABLES / "dataset_s2_leave_one_country_out_summary.csv",
        S2_DIR / "dataset_s2_leave_one_country_out_summary.csv",
        "Leave-one-country-out min/max summary.",
    ),
    (
        OUTPUT_TABLES / "dataset_s2_country_exclusion_sensitivity.csv",
        S2_DIR / "dataset_s2_country_exclusion_sensitivity.csv",
        "Targeted full-sample and selected country-exclusion sensitivity table.",
    ),
    (
        OUTPUT_TABLES / "dataset_s2_country_exclusion_ingredients.csv",
        S2_DIR / "dataset_s2_country_exclusion_ingredients.csv",
        "Compact country/elevation/year ingredients for regenerating the selected country-exclusion sensitivity table.",
    ),
    (
        OUTPUT_TABLES / "dataset_s2_leave_one_region_out.csv",
        S2_DIR / "dataset_s2_leave_one_region_out.csv",
        "Leave-one-region-out robustness table.",
    ),
    (
        OUTPUT_TABLES / "dataset_s2_country_standardized_comparison.csv",
        S2_DIR / "dataset_s2_country_standardized_comparison.csv",
        "Country-standardized highland-minus-lowland growth comparison.",
    ),
    (
        OUTPUT_TABLES / "dataset_s2_worldpop_metadata_status.csv",
        S2_DIR / "dataset_s2_worldpop_metadata_status.csv",
        "WorldPop country source/census metadata provenance for selected highland-growth countries.",
    ),
    (
        OUTPUT_TABLES / "dataset_s2_country_decomposition_quality_checks.csv",
        S2_DIR / "dataset_s2_country_decomposition_quality_checks.csv",
        "Quality checks for the country decomposition outputs.",
    ),
]


RENAME_BY_FILE = {
    "dataset_s1_fig01_population_age_growth.csv": {
        "population_total_start": "population_2015",
        "population_total": "population_2025",
        "absolute_change": "absolute_change_2015_2025",
        "growth_2015_2025_percent": "growth_2015_2025_pct",
        "0-14_population": "age_0_14_population_2025",
        "0-14_share_percent": "age_0_14_share_2025_pct",
        "15-64_population": "age_15_64_population_2025",
        "15-64_share_percent": "age_15_64_share_2025_pct",
        "65+_population": "age_65_plus_population_2025",
        "65+_share_percent": "age_65_plus_share_2025_pct",
        "youth_population": "age_0_14_population_2025_duplicate",
        "working_age_population": "age_15_64_population_2025_duplicate",
        "old_age_population": "age_65_plus_population_2025_duplicate",
        "youth_share_percent": "age_0_14_share_2025_pct_duplicate",
        "working_age_share_percent": "age_15_64_share_2025_pct_duplicate",
        "old_age_share_percent": "age_65_plus_share_2025_pct_duplicate",
    },
    "dataset_s1_fig01_age_contributions.csv": {
        "population_2015_ageclass": "age_group_population_2015",
        "population_2025_ageclass": "age_group_population_2025",
        "absolute_change_ageclass": "age_group_absolute_change_2015_2025",
        "population_2015_total": "elevation_group_population_2015_total",
        "total_growth_percent": "total_growth_pct",
    },
    "dataset_s1_fig02_settlement_static2025.csv": {
        "pop_2015_static2025": "population_2015_static2025",
        "pop_2025_static2025": "population_2025_static2025",
        "youth_population": "age_0_14_population_2025",
        "youth_share_percent": "age_0_14_share_2025_pct",
        "male_share_percent": "male_share_2025_pct",
        "growth_static2025_percent": "growth_static2025_pct",
        "pop_2025_change_static2025": "population_2025_change_static2025",
    },
    "dataset_s2_primary_robustness_checks.csv": {
        "percent_change": "percent_change_pct",
        "share_under_15_start": "share_under_15_start_pct",
        "share_under_15_end": "share_under_15_end_pct",
        "share_65plus_start": "share_65plus_start_pct",
        "share_65plus_end": "share_65plus_end_pct",
        "male_share_start": "male_share_start_pct",
        "male_share_end": "male_share_end_pct",
    },
    "dataset_s2_dynamic_vs_static2025_settlement.csv": {
        "pop_2015_static2025": "population_2015_static2025",
        "pop_2025_static2025": "population_2025_static2025",
        "growth_static2025": "growth_static2025_pct",
        "growth_dynamic": "growth_dynamic_pct",
    },
}


DROP_DUPLICATE_COLUMNS_BY_FILE = {
    "dataset_s1_fig01_population_age_growth.csv": [
        "age_0_14_population_2025_duplicate",
        "age_15_64_population_2025_duplicate",
        "age_65_plus_population_2025_duplicate",
        "age_0_14_share_2025_pct_duplicate",
        "age_15_64_share_2025_pct_duplicate",
        "age_65_plus_share_2025_pct_duplicate",
    ],
}


FAR_RIGHT_COLUMNS = [
    "notes",
    "note",
    "source_table",
    "included_iso3",
    "candidate_files",
    "searched_locations",
    "countries",
]


def snake_case(name: str) -> str:
    name = str(name).strip()
    name = re.sub(r"^unnamed:.*$", "", name, flags=re.IGNORECASE)
    name = name.replace("%", " pct ")
    name = name.replace("+", " plus ")
    name = re.sub(r"[^0-9A-Za-z]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_").lower()
    if name and name[0].isdigit():
        name = f"col_{name}"
    return name


def normalize_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    replacements = {
        "1500-3500 m": "1,500-3,500 m",
        "1500–3500 m": "1,500-3,500 m",
        ">=3500 m": ">=3,500 m",
        "≥3500 m": ">=3,500 m",
        "65 plus": "65+",
        "65_plus": "65+",
    }
    for col in out.columns:
        if not (pd.api.types.is_object_dtype(out[col]) or pd.api.types.is_string_dtype(out[col])):
            continue
        out[col] = out[col].replace(replacements)
    return out


def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    preferred = [
        "iso3",
        "country_id",
        "country_name",
        "region",
        "elevation_group",
        "age_group",
        "settlement_class",
        "check_id",
        "check_name",
        "comparison",
        "elevation_definition",
        "geography_filter",
        "time_window",
        "year_start",
        "year_end",
        "metric",
        "value",
        "unit",
    ]
    front = [col for col in preferred if col in df.columns]
    far_right = [col for col in FAR_RIGHT_COLUMNS if col in df.columns and col not in front]
    middle = [col for col in df.columns if col not in front and col not in far_right]
    return df[front + middle + far_right]


def clean_table(path: Path, dest_name: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.loc[:, ~df.columns.astype(str).str.match(r"^Unnamed", case=False)]
    df = df.drop_duplicates().copy()
    df = df.rename(columns=RENAME_BY_FILE.get(dest_name, {}))
    df.columns = [snake_case(col) for col in df.columns]
    for col in DROP_DUPLICATE_COLUMNS_BY_FILE.get(dest_name, []):
        if col in df.columns:
            df = df.drop(columns=col)
    df = normalize_labels(df)
    return reorder_columns(df)


def write_cleaned_tables(
    sources: list[tuple[Path, Path, str]],
    output_dir: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    for source, dest, description in sources:
        if not source.exists():
            excluded.append({"source": str(source), "reason": "source file not found"})
            continue
        df = clean_table(source, dest.name)
        df.to_csv(dest, index=False, float_format=FLOAT_FORMAT)
        written.append(
            {
                "source": str(source),
                "dest": str(dest),
                "description": description,
                "rows": str(len(df)),
                "columns": str(len(df.columns)),
            }
        )
    return written, excluded


def read_packaged(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def qc_status(name: str, value: float, target: float, tolerance_pct: float) -> dict[str, object]:
    rel = abs(value - target) / abs(target) * 100 if target else 0
    return {
        "check": name,
        "value": value,
        "target": target,
        "relative_difference_pct": rel,
        "passed": rel <= tolerance_pct,
    }


def run_s1_qc() -> list[dict[str, object]]:
    fig1 = read_packaged(S1_DIR / "dataset_s1_fig01_population_age_growth.csv")
    high = fig1[fig1["elevation_group"].isin(["1500-2499 m", "2500-3499 m"])]
    low = fig1[fig1["elevation_group"].isin(["<100 m", "100-499 m"])]
    below100 = fig1.loc[fig1["elevation_group"].eq("<100 m"), "population_2025"].sum()
    above3500 = fig1.loc[fig1["elevation_group"].eq(">=3,500 m"), "population_2025"].sum()
    high_2015 = high["population_2015"].sum()
    high_2025 = high["population_2025"].sum()
    low_2015 = low["population_2015"].sum()
    low_2025 = low["population_2025"].sum()
    high_growth = 100 * (high_2025 - high_2015) / high_2015
    low_growth = 100 * (low_2025 - low_2015) / low_2015
    high_youth = 100 * high["age_0_14_population_2025"].sum() / high_2025
    low_youth = 100 * low["age_0_14_population_2025"].sum() / low_2025
    return [
        qc_status("<500 m 2025 population", low_2025, 6.24e9, 0.5),
        qc_status("<100 m 2025 population", below100, 3.51e9, 0.5),
        qc_status("1,500-3,500 m 2025 population", high_2025, 522e6, 0.5),
        qc_status("highland growth", high_growth, 17.5, 1.0),
        qc_status("lowland growth", low_growth, 9.0, 1.0),
        qc_status("highland youth share", high_youth, 30.7, 1.0),
        qc_status("lowland youth share", low_youth, 23.2, 1.0),
        qc_status(">=3,500 m 2025 population", above3500, 12.1e6, 0.5),
    ]


def run_s2_qc() -> list[dict[str, object]]:
    concentration = read_packaged(S2_DIR / "dataset_s2_concentration_summary.csv")
    loo = read_packaged(S2_DIR / "dataset_s2_leave_one_country_out_summary.csv")
    standardized = read_packaged(S2_DIR / "dataset_s2_country_standardized_comparison.csv")
    top_growth = concentration[concentration["ranking_metric"].eq("absolute highland growth, 2015-2025")]
    top10 = float(
        top_growth.loc[
            top_growth["top_n"].eq(10),
            "cumulative_highland_absolute_growth_2015_2025_share_percent",
        ].iloc[0]
    )
    top20 = float(
        top_growth.loc[
            top_growth["top_n"].eq(20),
            "cumulative_highland_absolute_growth_2015_2025_share_percent",
        ].iloc[0]
    )
    min_diff = float(loo["min_highland_minus_lowland_difference_pp"].iloc[0])
    contrast_reverses = bool(loo["contrast_ever_reverses"].iloc[0])
    n_countries = int(standardized["n_countries_with_meaningful_population_in_both_zones"].iloc[0])
    return [
        qc_status("top 10 highland growth concentration", top10, 75.7, 1.0),
        qc_status("top 20 highland growth concentration", top20, 93.0, 1.0),
        {
            "check": "leave-one-country-out highland-minus-lowland remains positive",
            "value": min_diff,
            "target": ">0 and no reversal",
            "relative_difference_pct": None,
            "passed": (min_diff > 0) and (not contrast_reverses),
        },
        {
            "check": "country-standardized default country count",
            "value": n_countries,
            "target": 48,
            "relative_difference_pct": 0 if n_countries == 48 else None,
            "passed": n_countries == 48,
        },
    ]


def write_readme(path: Path, title: str, lines: list[str]) -> None:
    path.write_text(title + "\n" + "=" * len(title) + "\n\n" + "\n".join(lines) + "\n")


def s1_readme_lines(written: list[dict[str, str]], qc: list[dict[str, object]]) -> list[str]:
    files = "\n".join(f"- `{Path(item['dest']).name}`: {item['description']}" for item in written)
    qc_lines = "\n".join(
        f"- {item['check']}: {item['value']:.6g} (target {item['target']}; passed={item['passed']})"
        for item in qc
    )
    return [
        "Dataset S1 contains analysis-ready source data for the main paper figures and headline manuscript values.",
        "",
        "Files:",
        files,
        "",
        "Column and unit notes:",
        "- `population_*` columns are counts of people unless the column name includes `_billions` or `_millions`.",
        "- `*_pct` columns are percentages.",
        "- `*_pp` columns are percentage-point differences or contributions.",
        "- `elevation_group` uses the manuscript elevation groups: <100 m, 100-499 m, 500-1,499 m, 1,500-2,499 m, 2,500-3,499 m, and >=3,500 m.",
        "- `age_group` uses 0-14, 15-64, and 65+.",
        "- `settlement_class` uses Low-density rural, Rural cluster, Peri-urban, Semi-dense urban, Dense urban, and Urban centre.",
        "- Figure 2 settlement fields use static 2025 settlement classification, meaning 2025 settlement classes are held fixed for the 2015-2025 comparison.",
        "",
        "Quality checks:",
        qc_lines,
        "",
        "This dataset supports main figures, headline manuscript values, and companion threshold values only.",
    ]


def s2_readme_lines(written: list[dict[str, str]], qc: list[dict[str, object]]) -> list[str]:
    files = "\n".join(f"- `{Path(item['dest']).name}`: {item['description']}" for item in written)
    qc_lines = "\n".join(
        f"- {item['check']}: {item['value']} (target {item['target']}; passed={item['passed']})"
        for item in qc
    )
    return [
        "Dataset S2 contains sample robustness and sensitivity tables supporting the elevation-gradient results.",
        "",
        "Files:",
        files,
        "",
        "Column and unit notes:",
        "- `population_*` columns are counts of people unless otherwise stated.",
        "- `*_pct` columns are percentages.",
        "- `*_pp` columns are percentage-point differences.",
        "- `iso3`, `country_name`, and `region` identify countries and regions where available.",
        "- Elevation, age-group, and settlement-class labels follow Dataset S1 conventions.",
        "",
        "Table notes:",
        "- The country decomposition compares <500 m lowlands with 1,500-3,500 m inhabited highlands by country.",
        "- Concentration summaries report top-10 and top-20 cumulative shares by highland population and highland growth.",
        "- Leave-one-country-out and leave-one-region-out tables recompute the global highland-lowland contrast after removing each unit.",
        "- The country-exclusion sensitivity table reports the full sample and selected exclusions (ETH, MEX, KEN, YEM, AFG); its compact ingredients table stores the full-sample and selected-country elevation-year totals needed to regenerate those rows without bundling the large analysis-ready parquet source.",
        "- The country-standardized comparison includes countries with at least 100,000 people in both zones in 2025 by default.",
        "- The WorldPop metadata-status table reports fields extracted from the official Global 2 R2025A v1 census/source workbook and uses `not_available` where values are not listed.",
        "- These tables support robustness and sensitivity checks; they do not provide pixel-level uncertainty intervals.",
        "",
        "Rebuild note:",
        "- Run `python processing/build_dataset_s2_country_exclusion_sensitivity.py` from the repository root to regenerate `dataset_s2_country_exclusion_sensitivity.csv` from the compact ingredients table. If the larger static-2025 analysis-ready parquet is available one directory above the repository, the script refreshes the ingredients from that source first.",
        "",
        "Quality checks:",
        qc_lines,
        "",
        "This dataset is provided as sample supplementary robustness and sensitivity tables, not as main figure source data.",
    ]


def main() -> None:
    written_s1, excluded_s1 = write_cleaned_tables(S1_SOURCES, S1_DIR)
    written_s2, excluded_s2 = write_cleaned_tables(S2_SOURCES, S2_DIR)
    s1_qc = run_s1_qc()
    s2_qc = run_s2_qc()
    write_readme(S1_DIR / "README.txt", "Supplementary Dataset S1", s1_readme_lines(written_s1, s1_qc))
    write_readme(S2_DIR / "README.txt", "Supplementary Dataset S2", s2_readme_lines(written_s2, s2_qc))

    print("Supplementary Dataset S1 files written:")
    for item in written_s1:
        print(f"- {item['dest']} ({item['rows']} rows, {item['columns']} columns)")
    print("Supplementary Dataset S2 files written:")
    for item in written_s2:
        print(f"- {item['dest']} ({item['rows']} rows, {item['columns']} columns)")
    print("Excluded files:")
    for item in excluded_s1 + excluded_s2:
        print(f"- {item['source']}: {item['reason']}")
    if not excluded_s1 and not excluded_s2:
        print("- None")
    print("QC checks:")
    for item in s1_qc + s2_qc:
        print(f"- {item['check']}: passed={item['passed']} value={item['value']} target={item['target']}")

    failed = [item for item in s1_qc + s2_qc if not item["passed"]]
    if failed:
        raise SystemExit(f"{len(failed)} QC check(s) failed")


if __name__ == "__main__":
    main()
