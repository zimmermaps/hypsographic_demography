"""Shared Robinson-projection utilities for manuscript Figure 3."""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("/tmp") / "matplotlib-hypso-fig3-map"))

import matplotlib as mpl

mpl.use("Agg")

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from matplotlib.path import Path as MplPath


ROOT = Path(__file__).resolve().parents[1]
INPUT_COUNTRY_ELEVATION = (
    ROOT / "data" / "figure_data" / "fig3_country_elevation_groups.geoparquet"
)
NATURAL_EARTH_ADMIN0 = (
    ROOT / "data" / "figure_data" / "fig3_natural_earth_admin0_110m.geojson"
)
GRID_COLOR = (0.35, 0.48, 0.55, 0.17)


@dataclass(frozen=True)
class Projection:
    name: str
    fn: callable
    frame_fn: callable
    lon_min: float = -180
    lon_max: float = 180
    lat_min: float = -60
    lat_max: float = 85

def configure_style() -> None:
    from matplotlib import font_manager

    available_fonts = {f.name for f in font_manager.fontManager.ttflist}
    if "Helvetica" in available_fonts:
        figure_font = "Helvetica"
    elif "Arial" in available_fonts:
        figure_font = "Arial"
    else:
        figure_font = "DejaVu Sans"

    mpl.rcParams.update(
        {
            "font.family": figure_font,
            "font.size": 6.6,
            "axes.titlesize": 7.4,
            "axes.labelsize": 6.8,
            "xtick.labelsize": 6.0,
            "ytick.labelsize": 6.0,
            "legend.fontsize": 6.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.dpi": 600,
            "savefig.facecolor": "white",
        }
    )

def parse_wkb_exterior_rings(wkb: bytes) -> list[np.ndarray]:
    data = memoryview(wkb)

    def read(offset: int, fmt: str, endian: str):
        size = struct.calcsize(fmt)
        return struct.unpack(endian + fmt, data[offset : offset + size])[0], offset + size

    def parse(offset: int):
        byte_order = data[offset]
        endian = "<" if byte_order == 1 else ">"
        offset += 1
        type_code, offset = read(offset, "I", endian)
        base_type = type_code if type_code in {3, 6} else type_code % 1000

        if base_type == 3:
            nrings, offset = read(offset, "I", endian)
            exterior = None
            for ring_i in range(nrings):
                npoints, offset = read(offset, "I", endian)
                nvals = npoints * 2
                size = nvals * 8
                vals = struct.unpack(endian + "d" * nvals, data[offset : offset + size])
                offset += size
                if ring_i == 0 and npoints >= 3:
                    exterior = np.asarray(vals, dtype=float).reshape(npoints, 2)
            return ([exterior] if exterior is not None else []), offset

        if base_type == 6:
            ngeom, offset = read(offset, "I", endian)
            rings = []
            for _ in range(ngeom):
                subrings, offset = parse(offset)
                rings.extend(subrings)
            return rings, offset

        raise ValueError(f"Unsupported WKB geometry type: {type_code}")

    rings, _ = parse(0)
    return rings

ROBINSON_X = np.array(
    [
        1.0000,
        0.9986,
        0.9954,
        0.9900,
        0.9822,
        0.9730,
        0.9600,
        0.9427,
        0.9216,
        0.8962,
        0.8679,
        0.8350,
        0.7986,
        0.7597,
        0.7186,
        0.6732,
        0.6213,
        0.5722,
        0.5322,
    ]
)

ROBINSON_Y = np.array(
    [
        0.0000,
        0.0620,
        0.1240,
        0.1860,
        0.2480,
        0.3100,
        0.3720,
        0.4340,
        0.4958,
        0.5571,
        0.6176,
        0.6769,
        0.7346,
        0.7903,
        0.8435,
        0.8936,
        0.9394,
        0.9761,
        1.0000,
    ]
)

def robinson(lon_deg, lat_deg):
    lon = np.asarray(lon_deg, dtype=float)
    lat = np.asarray(lat_deg, dtype=float)
    abs_lat = np.clip(np.abs(lat), 0, 90)
    idx = np.floor(abs_lat / 5).astype(int)
    idx = np.clip(idx, 0, len(ROBINSON_X) - 2)
    frac = (abs_lat - idx * 5) / 5
    xcoef = ROBINSON_X[idx] + frac * (ROBINSON_X[idx + 1] - ROBINSON_X[idx])
    ycoef = ROBINSON_Y[idx] + frac * (ROBINSON_Y[idx + 1] - ROBINSON_Y[idx])
    x = 0.8487 * xcoef * np.deg2rad(lon)
    y = 1.3523 * np.sign(lat) * ycoef
    return x, y

def frame_path(project_fn, lon_min=-180, lon_max=180, lat_min=-60, lat_max=85) -> MplPath:
    lat_right = np.linspace(lat_min, lat_max, 300)
    x_right, y_right = project_fn(np.full_like(lat_right, lon_max), lat_right)
    lon_top = np.linspace(lon_max, lon_min, 500)
    x_top, y_top = project_fn(lon_top, np.full_like(lon_top, lat_max))
    lat_left = np.linspace(lat_max, lat_min, 300)
    x_left, y_left = project_fn(np.full_like(lat_left, lon_min), lat_left)
    lon_bottom = np.linspace(lon_min, lon_max, 500)
    x_bottom, y_bottom = project_fn(lon_bottom, np.full_like(lon_bottom, lat_min))
    vertices = np.column_stack([np.r_[x_right, x_top, x_left, x_bottom], np.r_[y_right, y_top, y_left, y_bottom]])
    vertices = np.vstack([vertices, vertices[0]])
    codes = np.full(len(vertices), MplPath.LINETO, dtype=np.uint8)
    codes[0] = MplPath.MOVETO
    codes[-1] = MplPath.CLOSEPOLY
    return MplPath(vertices, codes)

ROBINSON_PROJECTION = Projection(
    "Robinson",
    robinson,
    lambda: frame_path(robinson, lon_min=-135, lon_max=160, lat_min=-60, lat_max=60),
    lon_min=-135,
    lon_max=160,
    lat_min=-60,
    lat_max=60,
)

def load_base_context() -> pd.DataFrame:
    """Load the retained country-by-elevation polygons used in Figure 3."""
    if not INPUT_COUNTRY_ELEVATION.exists():
        raise FileNotFoundError(
            f"Figure 3 polygon input not found: {INPUT_COUNTRY_ELEVATION.relative_to(ROOT)}"
        )
    return pq.read_table(
        INPUT_COUNTRY_ELEVATION,
        columns=["iso3", "country_name", "elevation_group", "geometry"],
    ).to_pandas()

def project_rows(rows: pd.DataFrame, project_fn, color: str | None = None, color_field: str | None = None):
    polygons: list[np.ndarray] = []
    colors: list[str] = []
    for row in rows.itertuples(index=False):
        row_color = getattr(row, color_field) if color_field else color
        for ring in parse_wkb_exterior_rings(row.geometry):
            x, y = project_fn(ring[:, 0], ring[:, 1])
            polygons.append(np.column_stack([x, y]))
            colors.append(row_color)
    return polygons, colors

def sample_segment_keys(p0: np.ndarray, p1: np.ndarray, *, step_deg: float = 0.03, round_decimals: int = 3) -> list[tuple[float, float]]:
    distance = max(abs(float(p1[0] - p0[0])), abs(float(p1[1] - p0[1])))
    n = max(1, int(np.ceil(distance / step_deg)))
    # Use midpoints so adjacent non-overlapping segments do not collide at shared vertices.
    t = (np.arange(n) + 0.5) / n
    points = p0[None, :2] + (p1[None, :2] - p0[None, :2]) * t[:, None]
    rounded = np.round(points, round_decimals)
    return [(float(lon), float(lat)) for lon, lat in rounded]

def add_graticule(ax, projection: Projection, clip_patch):
    lon_start = np.ceil(projection.lon_min / 30) * 30
    lon_stop = np.floor(projection.lon_max / 30) * 30
    lat_start = np.ceil(projection.lat_min / 15) * 15
    lat_stop = np.floor(projection.lat_max / 15) * 15

    for lon in np.arange(lon_start, lon_stop + 1, 30):
        lat_vals = np.linspace(projection.lat_min, projection.lat_max, 400)
        lon_vals = np.full_like(lat_vals, lon, dtype=float)
        x, y = projection.fn(lon_vals, lat_vals)
        line, = ax.plot(x, y, color=GRID_COLOR, linewidth=0.18, zorder=1)
        line.set_clip_path(clip_patch)

    for lat in np.arange(lat_start, lat_stop + 1, 15):
        lon_vals = np.linspace(projection.lon_min, projection.lon_max, 600)
        lat_vals = np.full_like(lon_vals, lat, dtype=float)
        x, y = projection.fn(lon_vals, lat_vals)
        line, = ax.plot(x, y, color=GRID_COLOR, linewidth=0.18, zorder=1)
        line.set_clip_path(clip_patch)
