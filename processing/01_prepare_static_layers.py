"""Record the elevation classes and alignment used upstream of Dataset S1."""


ELEVATION_GROUPS = [
    ("<100 m", -500, 100),
    ("100-499 m", 100, 500),
    ("500-1499 m", 500, 1500),
    ("1500-2499 m", 1500, 2500),
    ("2500-3499 m", 2500, 3500),
    (">=3500 m", 3500, None),
]


def assign_elevation_group(elevation_m: float) -> str:
    """Return the broad manuscript elevation group for a meter value."""
    for label, lo, hi in ELEVATION_GROUPS:
        if elevation_m >= lo and (hi is None or elevation_m < hi):
            return label
    return "<100 m"


def main() -> None:
    notes = """
    Upstream workflow:
    1. Reproject/resample GMTED2010 mean elevation to the WorldPop grid.
    2. Use bilinear resampling for elevation.
    3. Round aligned elevation to integer meters.
    4. Assign native elevation bands and the six manuscript groups.

    The required source rasters are not distributed with this repository.
    """
    print(notes.strip())


if __name__ == "__main__":
    main()
