"""Extract WorldPop age-sex population by aligned grid attributes.

The paper uses WorldPop Global 2 annual age-sex estimates. Age codes are kept
native during extraction, then summarized to broad manuscript age groups:
0-14, 15-64, and 65+.
"""


AGE_GROUPS = {
    "0-14": range(0, 15),
    "15-64": range(15, 65),
    "65+": range(65, 121),
}


def main() -> None:
    notes = """
    Production step:
    1. Read WorldPop annual age-sex rasters on the master grid.
    2. Join aligned elevation, country, and settlement attributes by cell.
    3. Sum population by year, age, sex, elevation band, and settlement class.
    4. Aggregate native age codes to 0-14, 15-64, and 65+ for the paper figures.

    The full gridded extraction requires source rasters that are not included here.
    """
    print(notes.strip())


if __name__ == "__main__":
    main()
