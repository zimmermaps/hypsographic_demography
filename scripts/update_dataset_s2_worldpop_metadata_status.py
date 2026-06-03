#!/usr/bin/env python3
"""Update Dataset S2 WorldPop Global 2 country metadata status table.

The script downloads the official WorldPop Global 2 R2025A v1 census/source
metadata workbook and extracts selected countries used in Dataset S2
provenance checks.
"""

from __future__ import annotations

import csv
import re
import tempfile
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


TARGET_ISO3 = ("ETH", "MEX", "KEN", "YEM", "AFG")
WORKBOOK_URL = (
    "https://data.worldpop.org/repo/prj/Global_2015_2030/R2025A/doc/census/"
    "global2_census_data_sources_R2025A_v1.xlsx"
)
RELEASE_STATEMENT_URL = (
    "https://data.worldpop.org/repo/prj/Global_2015_2030/R2025A/doc/"
    "Global2_Release_Statement_R2025A_v1.pdf"
)
OUTPUT_TABLES = Path("outputs/tables")
OUTPUT_DIR = Path("outputs/supplementary/dataset_s2")
STATUS_CSV = OUTPUT_DIR / "dataset_s2_worldpop_metadata_status.csv"
TABLES_STATUS_CSV = OUTPUT_TABLES / "dataset_s2_worldpop_metadata_status.csv"
README = OUTPUT_DIR / "README.txt"


def col_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    value = 0
    for letter in letters:
        value = value * 26 + ord(letter.upper()) - 64
    return value - 1


def read_xlsx_first_sheet(path: Path) -> list[list[str]]:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        ss_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        for si in ss_root.findall("a:si", ns):
            shared_strings.append(
                "".join((t.text or "") for t in si.findall(".//a:t", ns))
            )

        sheet_root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows: list[list[str]] = []
        for row in sheet_root.findall(".//a:sheetData/a:row", ns):
            values: dict[int, str] = {}
            for cell in row.findall("a:c", ns):
                value_node = cell.find("a:v", ns)
                value = "" if value_node is None else value_node.text or ""
                if cell.attrib.get("t") == "s" and value:
                    value = shared_strings[int(value)]
                values[col_index(cell.attrib.get("r", ""))] = value
            if values:
                rows.append([values.get(i, "") for i in range(max(values) + 1)])
    return rows


def clean(value: str) -> str:
    value = (value or "").strip()
    return value if value else "not_available"


def year_if_census(source_type: str, year: str) -> str | None:
    if "census" in (source_type or "").lower() and year:
        return year
    return None


def latest_census_year(row: dict[str, str]) -> str:
    years = [
        year_if_census(row["first_population_source_type"], row["first_population_year"]),
        year_if_census(row["second_population_source_type"], row["second_population_year"]),
    ]
    numeric = [int(year) for year in years if year and re.fullmatch(r"\d{4}", year)]
    return str(max(numeric)) if numeric else "not_available"


def combined_source_type(row: dict[str, str]) -> str:
    source_types = [
        clean(row["first_population_source_type"]),
        clean(row["second_population_source_type"]),
    ]
    source_types = [source for source in source_types if source != "not_available"]
    if not source_types:
        return "not_available"
    return "; ".join(dict.fromkeys(source_types))


def input_constraint_type(row: dict[str, str]) -> str:
    second_admin = row["second_highest_admin_level_used"].strip().lower()
    second_year = row["second_population_year"].strip()
    second_only = row["modelled_with_second_timepoint_only"].strip()
    if second_admin == "single time-point" or not second_year:
        return "single_timepoint_input"
    if second_only:
        return "modelled_with_second_timepoint_only"
    return "two_timepoint_input"


def input_year(row: dict[str, str]) -> str:
    years = [
        clean(row["first_population_year"]),
        clean(row["second_population_year"]),
    ]
    years = [year for year in years if year != "not_available"]
    return "; ".join(dict.fromkeys(years)) if years else "not_available"


def notes(row: dict[str, str]) -> str:
    parts = []
    first_year = clean(row["first_population_year"])
    first_type = clean(row["first_population_source_type"])
    second_year = clean(row["second_population_year"])
    second_type = clean(row["second_population_source_type"])
    if first_year != "not_available" or first_type != "not_available":
        parts.append(f"first_timepoint={first_year} {first_type}")
    if second_year != "not_available" or second_type != "not_available":
        parts.append(f"second_timepoint={second_year} {second_type}")
    nested_units = clean(row["nested_number_of_units"])
    if nested_units != "not_available":
        parts.append(f"nested_units={nested_units}")
    return "; ".join(parts) if parts else "not_available"


def extract_targets(rows: list[list[str]]) -> list[dict[str, str]]:
    if len(rows) < 4:
        raise ValueError("Workbook did not contain the expected metadata rows.")

    # Row 3 in Excel has the detailed headers; duplicate labels are disambiguated
    # according to the workbook's first/second-timepoint column groups.
    extracted: list[dict[str, str]] = []
    for raw in rows[3:]:
        iso3 = raw[2] if len(raw) > 2 else ""
        if iso3 not in TARGET_ISO3:
            continue

        def get(index: int) -> str:
            return raw[index].strip() if index < len(raw) else ""

        row = {
            "iso3": iso3,
            "country_name": get(0),
            "continent": get(1),
            "first_highest_admin_level_used": get(4),
            "first_number_of_units": get(5),
            "first_population_year": get(6),
            "first_population_source_type": get(7),
            "first_population_source_citation": get(8),
            "first_sex_variable_year": get(9),
            "first_sex_variable_type": get(10),
            "first_age_variable_year": get(11),
            "first_age_variable_type": get(12),
            "second_highest_admin_level_used": get(13),
            "second_number_of_units": get(14),
            "second_population_year": get(15),
            "second_population_source_type": get(16),
            "second_population_source_citation": get(17),
            "second_sex_variable_year": get(18),
            "second_sex_variable_type": get(19),
            "second_age_variable_year": get(20),
            "second_age_variable_type": get(21),
            "nested_number_of_units": get(22),
            "modelled_with_second_timepoint_only": get(23),
        }
        extracted.append(row)

    by_iso = {row["iso3"]: row for row in extracted}
    missing = sorted(set(TARGET_ISO3) - set(by_iso))
    if missing:
        raise ValueError(f"Target ISO3 code(s) missing from workbook: {missing}")
    return [by_iso[iso3] for iso3 in TARGET_ISO3]


def status_rows(target_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    output_rows: list[dict[str, str]] = []
    for row in target_rows:
        output_rows.append(
            {
                "iso3": row["iso3"],
                "country_name": row["country_name"],
                "source_type": combined_source_type(row),
                "input_year": input_year(row),
                "most_recent_census_year": latest_census_year(row),
                "input_constraint_type": input_constraint_type(row),
                "metadata_source": WORKBOOK_URL,
                "notes": notes(row),
            }
        )
    return output_rows


def write_status_csv(rows: list[dict[str, str]]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_TABLES.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    for path in (STATUS_CSV, TABLES_STATUS_CSV):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def update_readme() -> None:
    if not README.exists():
        return
    text = README.read_text(encoding="utf-8")
    old = (
        "- WorldPop country source/census metadata were not available locally; the "
        "metadata-status table preserves that note and does not invent metadata."
    )
    new = (
        "- WorldPop Global 2 R2025A v1 country source/census metadata were not "
        "available locally, so the metadata-status table is extracted from the "
        "official WorldPop census/source workbook. It reports only fields present "
        "in that workbook and does not infer unavailable census/source details."
    )
    if old in text:
        text = text.replace(old, new)
    elif new not in text:
        text = text.rstrip() + "\n" + new + "\n"
    if "dataset_s2_worldpop_metadata_summary.md" not in text:
        text = text.replace(
            "- `dataset_s2_worldpop_metadata_status.csv`: WorldPop country source/census metadata availability status.",
            "- `dataset_s2_worldpop_metadata_status.csv`: WorldPop country source/census metadata provenance for selected highland-growth countries.",
        )
    README.write_text(text, encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        workbook = Path(tmpdir) / "global2_census_data_sources_R2025A_v1.xlsx"
        urllib.request.urlretrieve(WORKBOOK_URL, workbook)
        rows = read_xlsx_first_sheet(workbook)

    targets = extract_targets(rows)
    output_rows = status_rows(targets)
    write_status_csv(output_rows)
    update_readme()

    with STATUS_CSV.open(newline="", encoding="utf-8") as handle:
        count = sum(1 for _ in csv.DictReader(handle))
    if count != len(TARGET_ISO3):
        raise RuntimeError(f"Expected {len(TARGET_ISO3)} rows, found {count}.")
    print(f"Wrote {STATUS_CSV} with {count} target-country rows.")
    print(f"Wrote {TABLES_STATUS_CSV}.")


if __name__ == "__main__":
    main()
