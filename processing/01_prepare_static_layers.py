"""Prepare elevation classes for the hypsographic demography analysis.

This script documents the static-layer step used upstream of Dataset S1.
It expects raw GMTED2010 elevation and a WorldPop template grid. The large
source rasters are not included in this paper repository.
"""

from pathlib import Path


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
    Production step:
    1. Reproject/resample GMTED2010 mean elevation to the WorldPop grid.
    2. Use bilinear resampling for elevation.
    3. Round aligned elevation to integer meters.
    4. Assign native elevation bands and the six manuscript groups.

    See the full source repository for raster execution details.
    """
    print(notes.strip())


if __name__ == "__main__":
    main()
