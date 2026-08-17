"""Plot Figure 3, the global inhabited-highland population change map."""

from __future__ import annotations

import os
import json
import struct
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("/tmp") / "matplotlib-hypso-fig3-map"))

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from matplotlib.collections import LineCollection
from matplotlib.collections import PolyCollection
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath


ROOT = Path(__file__).resolve().parents[1]
INPUT_COUNTRY_CHANGE = ROOT / "data" / "fig3_highland_change_polygons.geoparquet"
INPUT_COUNTRY_ELEVATION = (
    ROOT / "data" / "figure_data" / "fig3_country_elevation_groups.geoparquet"
)
FIG_DIR = ROOT / "figures"
TAB_DIR = ROOT / "data" / "figure_data"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TAB_DIR.mkdir(parents=True, exist_ok=True)
NATURAL_EARTH_ADMIN0 = (
    ROOT / "data" / "figure_data" / "fig3_natural_earth_admin0_110m.geojson"
)

HIGHLAND_BANDS = ["1500-2499m", "2500-3499m"]
GROWTH_FIELD = "pop_total_pct_change_2015_2025"
POP_FIELD = "pop_total_2025"
POP_THRESHOLD = 100_000

GROWTH_VMIN = 0
GROWTH_VMAX = 40
GROWTH_CMAP = mpl.colormaps["YlOrRd"].copy()
GROWTH_CMAP.set_under("#fff7bc")
GROWTH_CMAP.set_over("#7f0000")

BASE_LAND_COLOR = "#ebe9e4"
SMALL_HIGHLAND_COLOR = "#d4d2cb"
OCEAN_COLOR = "#e8f6fa"
GRID_COLOR = (0.35, 0.48, 0.55, 0.17)
FRAME_COLOR = (0.22, 0.22, 0.22, 0.62)
HIGHLAND_OUTLINE_COLOR = (0.25, 0.20, 0.15, 0.48)
COUNTRY_BOUNDARY_COLOR = (0.32, 0.30, 0.27, 0.48)

ELEVATION_LABELS = {
    "1500-2499m": "1,500-2,499 m",
    "2500-3499m": "2,500-3,499 m",
}



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


def color_for_growth(value: float | None, norm: mpl.colors.Normalize) -> str:
    if pd.isna(value):
        return SMALL_HIGHLAND_COLOR
    return mpl.colors.to_hex(GROWTH_CMAP(norm(float(value))))


def load_country_change() -> pd.DataFrame:
    if not INPUT_COUNTRY_CHANGE.exists():
        raise FileNotFoundError(f"Primary analytical GeoParquet not found: {INPUT_COUNTRY_CHANGE}")
    return pq.read_table(INPUT_COUNTRY_CHANGE).to_pandas()


def load_base_context() -> pd.DataFrame:
    if INPUT_COUNTRY_ELEVATION.exists():
        return pq.read_table(INPUT_COUNTRY_ELEVATION, columns=["iso3", "country_name", "elevation_group", "geometry"]).to_pandas()
    return load_country_change()[["iso3", "country_name", "elevation_group", "geometry"]].copy()


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


def project_line_rows(rows: pd.DataFrame, project_fn) -> list[np.ndarray]:
    lines: list[np.ndarray] = []
    for row in rows.itertuples(index=False):
        for ring in parse_wkb_exterior_rings(row.geometry):
            if len(ring) < 2:
                continue
            x, y = project_fn(ring[:, 0], ring[:, 1])
            lines.append(np.column_stack([x, y]))
    return lines


def sample_segment_keys(p0: np.ndarray, p1: np.ndarray, *, step_deg: float = 0.03, round_decimals: int = 3) -> list[tuple[float, float]]:
    distance = max(abs(float(p1[0] - p0[0])), abs(float(p1[1] - p0[1])))
    n = max(1, int(np.ceil(distance / step_deg)))
    # Use midpoints so adjacent non-overlapping segments do not collide at shared vertices.
    t = (np.arange(n) + 0.5) / n
    points = p0[None, :2] + (p1[None, :2] - p0[None, :2]) * t[:, None]
    rounded = np.round(points, round_decimals)
    return [(float(lon), float(lat)) for lon, lat in rounded]


def project_country_boundary_segments(rows: pd.DataFrame, project_fn) -> list[np.ndarray]:
    lines: list[np.ndarray] = []
    for _, country_rows in rows.groupby("iso3", sort=False):
        raw_segments: list[tuple[np.ndarray, np.ndarray, list[tuple[float, float]]]] = []
        sample_counts: dict[tuple[float, float], int] = {}
        for row in country_rows.itertuples(index=False):
            for ring in parse_wkb_exterior_rings(row.geometry):
                if len(ring) < 2:
                    continue
                for raw0, raw1 in zip(ring[:-1], ring[1:]):
                    if np.allclose(raw0[:2], raw1[:2]):
                        continue
                    keys = sample_segment_keys(raw0[:2], raw1[:2])
                    raw_segments.append((raw0[:2], raw1[:2], keys))
                    for key in set(keys):
                        sample_counts[key] = sample_counts.get(key, 0) + 1

        for raw0, raw1, keys in raw_segments:
            if not keys:
                continue
            unique_fraction = sum(sample_counts.get(key, 0) == 1 for key in keys) / len(keys)
            if unique_fraction < 0.55:
                continue
            x, y = project_fn(np.array([raw0[0], raw1[0]]), np.array([raw0[1], raw1[1]]))
            lines.append(np.column_stack([x, y]))
    return lines


def natural_earth_boundary_lines(project_fn) -> list[np.ndarray] | None:
    if not NATURAL_EARTH_ADMIN0.exists():
        print(f"Natural Earth boundary file not found: {NATURAL_EARTH_ADMIN0.relative_to(ROOT)}")
        return None

    with NATURAL_EARTH_ADMIN0.open("r", encoding="utf-8") as f:
        geojson = json.load(f)

    lines: list[np.ndarray] = []
    for feature in geojson.get("features", []):
        geometry = feature.get("geometry") or {}
        geom_type = geometry.get("type")
        coordinates = geometry.get("coordinates")
        if not coordinates:
            continue

        if geom_type == "Polygon":
            polygons = [coordinates]
        elif geom_type == "MultiPolygon":
            polygons = coordinates
        else:
            continue

        for polygon in polygons:
            if not polygon:
                continue
            exterior = np.asarray(polygon[0], dtype=float)
            if len(exterior) < 2:
                continue
            x, y = project_fn(exterior[:, 0], exterior[:, 1])
            lines.append(np.column_stack([x, y]))

    return lines


def continuous_norm(values: pd.Series) -> mpl.colors.Normalize:
    return mpl.colors.Normalize(vmin=GROWTH_VMIN, vmax=GROWTH_VMAX, clip=False)


def add_continuous_colorbar(
    fig,
    norm: mpl.colors.Normalize,
    *,
    left: float,
    bottom: float,
    width: float,
    height: float,
    fontsize: float = 8.0,
    title_y: float | None = None,
    show_low_high: bool = True,
):
    ax = fig.add_axes([left, bottom, width, height])
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=GROWTH_CMAP)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=ax, orientation="horizontal", extend="both", extendfrac=0.075)
    ticks = [0, 10, 20, 30, 40]
    cbar.set_ticks(ticks)
    cbar.set_ticklabels(["0%", "10%", "20%", "30%", "40%"])
    cbar.ax.tick_params(labelsize=fontsize, length=3.0, width=0.65, pad=1.8)
    cbar.outline.set_visible(True)
    cbar.outline.set_linewidth(0.45)
    cbar.outline.set_edgecolor("0.35")
    if title_y is None:
        cbar.ax.set_title(
            "Highland population change, 2015–2025",
            fontsize=fontsize + 0.25,
            pad=2.0,
        )
    else:
        fig.text(
            left + width / 2,
            title_y,
            "Highland population change, 2015–2025",
            ha="center",
            va="bottom",
            fontsize=fontsize + 0.25,
        )
    if show_low_high:
        cbar.ax.text(0, -1.55, "Low", transform=cbar.ax.transAxes, ha="left", va="top", fontsize=fontsize, color="0.30")
        cbar.ax.text(1, -1.55, "High", transform=cbar.ax.transAxes, ha="right", va="top", fontsize=fontsize, color="0.30")


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


def draw_map(
    base: pd.DataFrame,
    highland: pd.DataFrame,
    width: float,
    height: float,
    output_stem: str = "fig3_highland_change_map",
) -> None:
    projection = ROBINSON_PROJECTION
    highland_main = highland[highland[POP_FIELD] >= POP_THRESHOLD].copy()
    highland_small = highland[highland[POP_FIELD] < POP_THRESHOLD].copy()

    norm = continuous_norm(highland_main[GROWTH_FIELD])
    highland_main["fill_color"] = highland_main[GROWTH_FIELD].map(lambda value: color_for_growth(value, norm))
    context = base[~base["elevation_group"].isin(HIGHLAND_BANDS)].copy()

    context_polys, context_colors = project_rows(context, projection.fn, color=BASE_LAND_COLOR)
    small_polys, small_colors = project_rows(highland_small, projection.fn, color=SMALL_HIGHLAND_COLOR)
    main_polys, main_colors = project_rows(highland_main, projection.fn, color_field="fill_color")
    country_lines = natural_earth_boundary_lines(projection.fn)
    boundary_source = "Natural Earth"
    if country_lines is None:
        country_lines = project_country_boundary_segments(base, projection.fn)
        boundary_source = "GeoParquet-derived"
    print(f"Boundary source for {output_stem}: {boundary_source}")

    frame = projection.frame_fn()
    frame_patch = PathPatch(frame, facecolor=OCEAN_COLOR, edgecolor="none", zorder=0)
    frame_vertices = frame.vertices[:-1]
    extent = (
        float(frame_vertices[:, 0].min()),
        float(frame_vertices[:, 0].max()),
        float(frame_vertices[:, 1].min()),
        float(frame_vertices[:, 1].max()),
    )

    fig = plt.figure(figsize=(width, height))
    if width <= 3.6:
        ax = fig.add_axes([0.015, 0.315, 0.97, 0.670])
    else:
        ax = fig.add_axes([0.02, 0.195, 0.96, 0.785])

    ax.add_patch(frame_patch)
    add_graticule(ax, projection, frame_patch)

    for polys, colors, edgecolor, zorder, lw in [
        (context_polys, context_colors, None, 2, 0.0),
        (small_polys, small_colors, None, 3, 0.0),
        (main_polys, main_colors, HIGHLAND_OUTLINE_COLOR, 4, 0.040 if width <= 3.6 else 0.035),
    ]:
        if polys:
            collection = PolyCollection(
                polys,
                facecolors=colors,
                edgecolors="none" if edgecolor is None else [edgecolor],
                linewidths=lw,
                antialiaseds=True,
                rasterized=True,
                zorder=zorder,
            )
            collection.set_clip_path(frame_patch)
            ax.add_collection(collection)

    if country_lines:
        country_collection = LineCollection(
            country_lines,
            colors=[COUNTRY_BOUNDARY_COLOR],
            linewidths=0.125 if width <= 3.6 else 0.105,
            antialiaseds=True,
            rasterized=True,
            zorder=5,
        )
        country_collection.set_clip_path(frame_patch)
        ax.add_collection(country_collection)

    ax.add_patch(PathPatch(frame, facecolor="none", edgecolor=FRAME_COLOR, linewidth=0.70, zorder=6))
    pad_x = (extent[1] - extent[0]) * 0.004
    pad_y = (extent[3] - extent[2]) * 0.006
    ax.set_xlim(extent[0] - pad_x, extent[1] + pad_x)
    ax.set_ylim(extent[2] - pad_y, extent[3] + pad_y)
    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()

    legend_left = 0.130 if width <= 3.6 else 0.220
    legend_width = 0.740 if width <= 3.6 else 0.560
    add_continuous_colorbar(
        fig,
        norm,
        left=legend_left,
        bottom=0.218 if width <= 3.6 else 0.115,
        width=legend_width,
        height=0.036 if width <= 3.6 else 0.038,
        fontsize=8.3,
        title_y=0.278 if width <= 3.6 else 0.158,
        show_low_high=False,
    )

    for ext in ["png", "pdf", "svg"]:
        path = FIG_DIR / f"{output_stem}.{ext}"
        if ext == "png":
            fig.savefig(path, bbox_inches="tight", pad_inches=0.015, facecolor="white", dpi=600)
        else:
            fig.savefig(path, bbox_inches="tight", pad_inches=0.015, facecolor="white")
        print(f"Saved {path.relative_to(ROOT)}")
    plt.close(fig)


def print_diagnostics(highland: pd.DataFrame, retained: pd.DataFrame) -> None:
    mapped_pop = highland[POP_FIELD].sum()
    mapped_change = highland["pop_total_change_2015_2025"].sum()
    weighted_growth = 100 * mapped_change / highland["pop_total_2015"].sum()
    print("\nDiagnostics")
    print(f"- Inhabited-highland country-elevation strata: {len(highland):,}")
    print(f"- Shown above POP_THRESHOLD={POP_THRESHOLD:,}: {len(retained):,}")
    print(f"- Total 2025 population in mapped inhabited-highland strata: {mapped_pop:,.0f}")
    print(f"- Total absolute change 2015–2025: {mapped_change:,.0f}")
    print(f"- Weighted mean percent growth: {weighted_growth:.2f}%")

    growth = highland[GROWTH_FIELD].dropna()
    if not growth.empty:
        print(
            "- Growth among inhabited-highland strata "
            f"min/median/max: {growth.min():.2f}% / {growth.median():.2f}% / {growth.max():.2f}%"
        )
    retained_growth = retained[GROWTH_FIELD].dropna()
    if not retained_growth.empty:
        print(
            "- Growth among shown strata "
            f"min/median/max: {retained_growth.min():.2f}% / {retained_growth.median():.2f}% / {retained_growth.max():.2f}%"
        )

    top_change = retained.nlargest(10, "pop_total_change_2015_2025")[
        ["iso3", "country_name", "elevation_group", POP_FIELD, "pop_total_change_2015_2025", GROWTH_FIELD]
    ]
    top_pct = retained.nlargest(10, GROWTH_FIELD)[
        ["iso3", "country_name", "elevation_group", POP_FIELD, "pop_total_change_2015_2025", GROWTH_FIELD]
    ]
    print("\nTop 10 retained strata by absolute population change")
    print(top_change.to_string(index=False))
    print("\nTop 10 retained strata by percent growth")
    print(top_pct.to_string(index=False))


def main() -> None:
    configure_style()
    country_change = load_country_change()
    base = load_base_context()

    print(f"Primary input: {INPUT_COUNTRY_CHANGE}")
    print(f"Base/context input: {INPUT_COUNTRY_ELEVATION if INPUT_COUNTRY_ELEVATION.exists() else INPUT_COUNTRY_CHANGE}")
    print(f"Elevation groups found: {sorted(country_change['elevation_group'].dropna().unique().tolist())}")

    highland = country_change[country_change["elevation_group"].isin(HIGHLAND_BANDS)].copy()
    highland["growth_percent"] = highland[GROWTH_FIELD]
    highland["elevation_label"] = highland["elevation_group"].map(ELEVATION_LABELS)
    retained = highland[highland[POP_FIELD] >= POP_THRESHOLD].copy()

    data_csv = TAB_DIR / "fig3_highland_change_map_data.csv"
    highland.drop(columns=["geometry"]).to_csv(data_csv, index=False)
    print(f"Saved {data_csv.relative_to(ROOT)}")

    draw_map(
        base,
        highland,
        width=3.4,
        height=2.42,
    )

    print_diagnostics(highland, retained)


if __name__ == "__main__":
    main()
