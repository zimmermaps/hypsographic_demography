"""Plot manuscript Figure 3 from retained map and regional publication data."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("/tmp") / "matplotlib-hypso-fig3-map"))

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, PathPatch


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"
TAB_DIR = ROOT / "data" / "figure_data"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TAB_DIR.mkdir(parents=True, exist_ok=True)

FIG3_SCRIPT = ROOT / "processing" / "06_plot_fig3_highland_change_map.py"
FIG3_SPEC = importlib.util.spec_from_file_location("fig3_map_utils", FIG3_SCRIPT)
if FIG3_SPEC is None or FIG3_SPEC.loader is None:
    raise ImportError(f"Could not load shared map utilities from {FIG3_SCRIPT}")
fig3 = importlib.util.module_from_spec(FIG3_SPEC)
sys.modules[FIG3_SPEC.name] = fig3
FIG3_SPEC.loader.exec_module(fig3)

OUTPUT_STEM = "fig3"
INPUT_REGIONAL_GROWTH = TAB_DIR / "fig3_region_elevation_growth.csv"
FIGURE_WIDTH_IN = 7.50
FIGURE_HEIGHT_IN = 7.30
NORTH_CLIP_LAT = 90
REGION_ORDER = ["Africa", "Asia", "Europe", "North America", "Oceania", "South America"]
CONTINENT_OUTLINE_COLORS = {
    "Africa": "#6A3D9A",
    "Asia": "#009E73",
    "Europe": "#FF1493",
    "North America": "#0066CC",
    "Oceania": "#D99A00",
    "South America": "#C51B1D",
}

ELEVATION_ORDER = [
    "<100m",
    "100-499m",
    "500-1499m",
    "1500-2499m",
    "2500-3499m",
    ">=3500m",
]
ELEVATION_LABELS = {
    "<100m": "<100 m",
    "100-499m": "100–499 m",
    "500-1499m": "500–1,499 m",
    "1500-2499m": "1,500–2,499 m",
    "2500-3499m": "2,500–3,499 m",
    ">=3500m": "≥3,500 m",
}
# A hypsometric palette: soft greens for lowlands, warm earth tones for
# uplands, and a muted plum for the highest terrain.
ELEVATION_COLORS = {
    "<100m": "#DCECB5",
    "100-499m": "#A9D18E",
    "500-1499m": "#E3D378",
    "1500-2499m": "#D6A25F",
    "2500-3499m": "#B86F50",
    ">=3500m": "#745064",
}

OCEAN_COLOR = "#E8F6FA"
FRAME_COLOR = (0.22, 0.22, 0.22, 0.58)
GROWTH_VMIN = 0
GROWTH_VMAX = 30
NEGATIVE_GROWTH_COLOR = "#D9D9D9"
FRAME_OUTLINE_PATH_FACTORY = None
MAP_AX_POSITION = (0.030, 0.585, 0.690, 0.365)
ABSOLUTE_AX_POSITION = (0.045, 0.145, 0.455, 0.360)
GROWTH_AX_POSITION = (0.515, 0.145, 0.455, 0.360)
ELEVATION_LEGEND_Y = 0.528
CONTINENT_LEGEND_Y = 0.491
LOWER_PANEL_LABEL_Y = 0.560
LOWER_PANEL_TITLE_Y = 0.533
LOWER_COLORBAR_ORIENTATION = "vertical"
MAP_LEGEND_LAYOUT = "right"
MAP_TITLE_X = 0.375
CONTINENT_HALO_WIDTH = 1.65
CONTINENT_OUTLINE_WIDTH = 1.00
SHARED_BORDER_SEPARATOR_WIDTH = 2.20
CONTINENT_LEGEND_LINEWIDTH = 1.50


def load_continent_boundary_lines(project_fn) -> dict[str, list[np.ndarray]]:
    """Return dissolved Natural Earth outlines grouped by panel continent."""
    source = fig3.NATURAL_EARTH_ADMIN0
    if not source.exists():
        raise FileNotFoundError(
            f"Natural Earth boundary file not found: {source.relative_to(ROOT)}"
        )

    with source.open("r", encoding="utf-8") as stream:
        geojson = json.load(stream)

    rings_by_continent: dict[str, list[np.ndarray]] = {
        continent: [] for continent in REGION_ORDER
    }
    interior_rings_by_continent: dict[str, list[np.ndarray]] = {
        continent: [] for continent in REGION_ORDER
    }
    for feature in geojson.get("features", []):
        continent = (feature.get("properties") or {}).get("CONTINENT")
        if continent not in rings_by_continent:
            continue
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates")
        if not coordinates:
            continue
        if geometry.get("type") == "Polygon":
            polygons = [coordinates]
        elif geometry.get("type") == "MultiPolygon":
            polygons = coordinates
        else:
            continue
        for polygon in polygons:
            if polygon and len(polygon[0]) >= 2:
                rings_by_continent[continent].append(
                    np.asarray(polygon[0], dtype=float)
                )
                interior_rings_by_continent[continent].extend(
                    np.asarray(ring, dtype=float)
                    for ring in polygon[1:]
                    if len(ring) >= 2
                )

    projected_by_continent: dict[str, list[np.ndarray]] = {}
    for continent, rings in rings_by_continent.items():
        ring_segments: list[list[tuple[np.ndarray, np.ndarray, list[tuple[float, float]]]]] = []
        sample_counts: dict[tuple[float, float], int] = {}
        for ring in interior_rings_by_continent[continent]:
            for raw0, raw1 in zip(ring[:-1], ring[1:]):
                if np.allclose(raw0[:2], raw1[:2]):
                    continue
                if abs(float(raw1[0] - raw0[0])) > 180:
                    continue
                keys = fig3.sample_segment_keys(
                    raw0[:2], raw1[:2], step_deg=0.04, round_decimals=3
                )
                for key in set(keys):
                    sample_counts[key] = sample_counts.get(key, 0) + 1
        for ring in rings:
            raw_segments = []
            for raw0, raw1 in zip(ring[:-1], ring[1:]):
                if np.allclose(raw0[:2], raw1[:2]):
                    continue
                if abs(float(raw1[0] - raw0[0])) > 180:
                    raw_segments.append((raw0[:2], raw1[:2], []))
                    continue
                keys = fig3.sample_segment_keys(
                    raw0[:2], raw1[:2], step_deg=0.04, round_decimals=3
                )
                raw_segments.append((raw0[:2], raw1[:2], keys))
                for key in set(keys):
                    sample_counts[key] = sample_counts.get(key, 0) + 1
            ring_segments.append(raw_segments)

        retained_paths: list[np.ndarray] = []
        for raw_segments in ring_segments:
            current_path: list[np.ndarray] = []

            def finish_path() -> None:
                if len(current_path) < 2:
                    current_path.clear()
                    return
                lon_lat = np.asarray(current_path)
                x, y = project_fn(lon_lat[:, 0], lon_lat[:, 1])
                retained_paths.append(np.column_stack([x, y]))
                current_path.clear()

            for raw0, raw1, keys in raw_segments:
                unique_fraction = (
                    sum(sample_counts.get(key, 0) == 1 for key in keys) / len(keys)
                    if keys
                    else 0
                )
                if unique_fraction < 0.55:
                    finish_path()
                    continue
                if not current_path:
                    current_path.extend([raw0, raw1])
                elif np.allclose(current_path[-1], raw0):
                    current_path.append(raw1)
                else:
                    finish_path()
                    current_path.extend([raw0, raw1])
            finish_path()
        projected_by_continent[continent] = retained_paths

    return projected_by_continent


def load_shared_continent_boundaries(
    project_fn,
) -> dict[tuple[str, str], list[np.ndarray]]:
    """Return one projected path for each boundary shared by two continents."""
    with fig3.NATURAL_EARTH_ADMIN0.open("r", encoding="utf-8") as stream:
        geojson = json.load(stream)

    ring_segments: dict[
        str,
        list[list[tuple[np.ndarray, np.ndarray, list[tuple[float, float]]]]],
    ] = {continent: [] for continent in REGION_ORDER}
    key_continents: dict[tuple[float, float], set[str]] = {}

    for feature in geojson.get("features", []):
        continent = (feature.get("properties") or {}).get("CONTINENT")
        if continent not in ring_segments:
            continue
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates")
        if not coordinates:
            continue
        if geometry.get("type") == "Polygon":
            polygons = [coordinates]
        elif geometry.get("type") == "MultiPolygon":
            polygons = coordinates
        else:
            continue
        for polygon in polygons:
            if not polygon or len(polygon[0]) < 2:
                continue
            segments = []
            ring = np.asarray(polygon[0], dtype=float)
            for raw0, raw1 in zip(ring[:-1], ring[1:]):
                if np.allclose(raw0[:2], raw1[:2]):
                    continue
                if abs(float(raw1[0] - raw0[0])) > 180:
                    segments.append((raw0[:2], raw1[:2], []))
                    continue
                keys = fig3.sample_segment_keys(
                    raw0[:2], raw1[:2], step_deg=0.04, round_decimals=3
                )
                segments.append((raw0[:2], raw1[:2], keys))
                for key in set(keys):
                    key_continents.setdefault(key, set()).add(continent)
            ring_segments[continent].append(segments)

    region_rank = {continent: rank for rank, continent in enumerate(REGION_ORDER)}
    shared_paths: dict[tuple[str, str], list[np.ndarray]] = {}
    for continent, rings in ring_segments.items():
        for segments in rings:
            current_pair: tuple[str, str] | None = None
            current_path: list[np.ndarray] = []

            def finish_path() -> None:
                if current_pair is not None and len(current_path) >= 2:
                    lon_lat = np.asarray(current_path)
                    x, y = project_fn(lon_lat[:, 0], lon_lat[:, 1])
                    shared_paths.setdefault(current_pair, []).append(
                        np.column_stack([x, y])
                    )
                current_path.clear()

            for raw0, raw1, keys in segments:
                neighbor_votes: dict[str, int] = {}
                for key in keys:
                    for neighbor in key_continents.get(key, set()) - {continent}:
                        neighbor_votes[neighbor] = neighbor_votes.get(neighbor, 0) + 1
                if neighbor_votes:
                    neighbor, votes = max(neighbor_votes.items(), key=lambda item: item[1])
                else:
                    neighbor, votes = None, 0
                is_shared = bool(keys) and votes / len(keys) >= 0.55
                if not is_shared or neighbor is None:
                    finish_path()
                    current_pair = None
                    continue
                pair = tuple(
                    sorted((continent, neighbor), key=lambda name: region_rank[name])
                )
                if pair[0] != continent:
                    finish_path()
                    current_pair = None
                    continue
                if pair != current_pair:
                    finish_path()
                    current_pair = pair
                    current_path.extend([raw0, raw1])
                elif np.allclose(current_path[-1], raw0):
                    current_path.append(raw1)
                else:
                    finish_path()
                    current_pair = pair
                    current_path.extend([raw0, raw1])
            finish_path()

    return shared_paths


def offset_polyline(points: np.ndarray, distance: float) -> np.ndarray:
    """Offset a projected polyline perpendicular to its local direction."""
    if len(points) < 2:
        return points.copy()
    tangent = np.gradient(points, axis=0)
    lengths = np.hypot(tangent[:, 0], tangent[:, 1])
    lengths[lengths == 0] = 1.0
    normals = np.column_stack([-tangent[:, 1] / lengths, tangent[:, 0] / lengths])
    return points + distance * normals


def load_regional_growth() -> pd.DataFrame:
    if not INPUT_REGIONAL_GROWTH.exists():
        raise FileNotFoundError(
            f"Regional Figure 3 table not found: {INPUT_REGIONAL_GROWTH}"
        )
    regional = pd.read_csv(INPUT_REGIONAL_GROWTH)
    expected = len(REGION_ORDER) * len(ELEVATION_ORDER)
    if len(regional) != expected or regional[["continent", "elevation_group"]].duplicated().any():
        raise ValueError(f"Expected {expected} unique continent-elevation rows")
    if regional.isna().any().any():
        raise ValueError("Figure 3 regional table contains missing values")
    return regional


def annotation_text_color(color) -> str:
    red, green, blue, _alpha = mpl.colors.to_rgba(color)
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return "white" if luminance < 0.52 else "0.12"


def draw_growth_matrix(
    fig,
    ax,
    regional_growth: pd.DataFrame,
) -> None:
    matrix_elevation_order = list(reversed(ELEVATION_ORDER))
    matrix = (
        regional_growth.pivot(
            index="elevation_group",
            columns="continent",
            values="percent_change_2015_2025",
        )
        .reindex(index=matrix_elevation_order, columns=REGION_ORDER)
        .astype(float)
    )
    growth_cmap = mpl.colormaps["YlGnBu"].copy()
    growth_cmap.set_under(NEGATIVE_GROWTH_COLOR)
    growth_cmap.set_over("#081D58")
    norm = mpl.colors.Normalize(vmin=GROWTH_VMIN, vmax=GROWTH_VMAX, clip=False)
    image = ax.imshow(matrix.to_numpy(), cmap=growth_cmap, norm=norm, aspect="equal")

    ax.set_xticks(np.arange(len(REGION_ORDER)))
    ax.set_xticklabels(
        REGION_ORDER,
        rotation=36,
        ha="right",
        rotation_mode="anchor",
        fontsize=6.2,
    )
    ax.tick_params(axis="x", top=False, labeltop=False, bottom=True, labelbottom=True, length=0, pad=2)
    ax.set_yticks(np.arange(len(matrix_elevation_order)))
    ax.set_yticklabels([ELEVATION_LABELS[band] for band in matrix_elevation_order], fontsize=6.7)
    ax.tick_params(axis="y", length=0, pad=3)

    ax.set_xticks(np.arange(-0.5, len(REGION_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(matrix_elevation_order), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.7)
    ax.tick_params(which="minor", bottom=False, left=False)
    for spine in ax.spines.values():
        spine.set_color("0.45")
        spine.set_linewidth(0.55)

    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value = matrix.iat[row, col]
            color = growth_cmap(norm(value))
            ax.text(
                col,
                row,
                f"{value:+.1f}",
                ha="center",
                va="center",
                fontsize=6.3,
                color=annotation_text_color(color),
            )

    panel_position = ax.get_position()
    if LOWER_COLORBAR_ORIENTATION == "vertical":
        colorbar_ax = fig.add_axes(
            [panel_position.x1 + 0.010, panel_position.y0, 0.014, panel_position.height]
        )
        colorbar = fig.colorbar(
            image,
            cax=colorbar_ax,
            orientation="vertical",
            extend="both",
            extendfrac=0.045,
        )
    else:
        colorbar_left = panel_position.x0 + (panel_position.width - 0.255) / 2
        colorbar_ax = fig.add_axes([colorbar_left, 0.010, 0.255, 0.014])
        colorbar = fig.colorbar(
            image,
            cax=colorbar_ax,
            orientation="horizontal",
            extend="both",
            extendfrac=0.065,
        )
    colorbar.set_ticks([0, 10, 20, 30])
    colorbar.set_ticklabels(["0%", "10%", "20%", "30%"])
    colorbar.ax.tick_params(labelsize=6.7, length=2.5, width=0.55, pad=1.5)
    colorbar.outline.set_linewidth(0.45)
    colorbar.outline.set_edgecolor("0.4")
    if LOWER_COLORBAR_ORIENTATION == "vertical":
        colorbar.ax.set_ylabel("Change (%)", fontsize=7.2, labelpad=4.0)
    else:
        colorbar.ax.set_title("Change (%)", fontsize=7.2, pad=2.0)


def format_absolute_change(value_people: float) -> str:
    value_millions = value_people / 1e6
    if abs(value_millions) < 0.05:
        return "<0.1M"
    sign = "−" if value_millions < 0 else "+"
    if abs(value_millions) >= 100:
        magnitude = f"{abs(value_millions):.0f}"
    else:
        magnitude = f"{abs(value_millions):.1f}".rstrip("0").rstrip(".")
    return f"{sign}{magnitude}M"


def draw_absolute_change_matrix(
    fig,
    ax,
    regional_growth: pd.DataFrame,
) -> None:
    matrix_elevation_order = list(reversed(ELEVATION_ORDER))
    matrix = (
        regional_growth.pivot(
            index="elevation_group",
            columns="continent",
            values="absolute_change_2015_2025",
        )
        .reindex(index=matrix_elevation_order, columns=REGION_ORDER)
        .astype(float)
    )
    matrix_millions = matrix / 1e6
    absolute_cmap = mpl.colormaps["YlOrRd"].copy()
    absolute_cmap.set_under(NEGATIVE_GROWTH_COLOR)
    absolute_cmap.set_over("#800026")
    norm = mpl.colors.SymLogNorm(
        linthresh=0.1,
        linscale=0.55,
        vmin=0,
        vmax=160,
        base=10,
        clip=False,
    )
    image = ax.imshow(matrix_millions.to_numpy(), cmap=absolute_cmap, norm=norm, aspect="equal")

    ax.set_xticks(np.arange(len(REGION_ORDER)))
    ax.set_xticklabels(
        REGION_ORDER,
        rotation=36,
        ha="right",
        rotation_mode="anchor",
        fontsize=6.2,
    )
    ax.tick_params(axis="x", top=False, labeltop=False, bottom=True, labelbottom=True, length=0, pad=2)
    ax.set_yticks(np.arange(len(matrix_elevation_order)))
    ax.set_yticklabels([ELEVATION_LABELS[band] for band in matrix_elevation_order], fontsize=6.7)
    ax.tick_params(axis="y", length=0, pad=3)

    ax.set_xticks(np.arange(-0.5, len(REGION_ORDER), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(matrix_elevation_order), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.7)
    ax.tick_params(which="minor", bottom=False, left=False)
    for spine in ax.spines.values():
        spine.set_color("0.45")
        spine.set_linewidth(0.55)

    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            value_people = matrix.iat[row, col]
            value_millions = matrix_millions.iat[row, col]
            color = absolute_cmap(norm(value_millions))
            ax.text(
                col,
                row,
                format_absolute_change(value_people),
                ha="center",
                va="center",
                fontsize=5.9,
                color=annotation_text_color(color),
            )

    panel_position = ax.get_position()
    if LOWER_COLORBAR_ORIENTATION == "vertical":
        colorbar_ax = fig.add_axes(
            [panel_position.x1 + 0.010, panel_position.y0, 0.014, panel_position.height]
        )
        colorbar = fig.colorbar(
            image,
            cax=colorbar_ax,
            orientation="vertical",
            extend="both",
            extendfrac=0.045,
        )
    else:
        colorbar_left = panel_position.x0 + (panel_position.width - 0.255) / 2
        colorbar_ax = fig.add_axes([colorbar_left, 0.010, 0.255, 0.014])
        colorbar = fig.colorbar(
            image,
            cax=colorbar_ax,
            orientation="horizontal",
            extend="both",
            extendfrac=0.065,
        )
    colorbar.set_ticks([0, 1, 10, 160])
    colorbar.set_ticklabels(["0", "1M", "10M", "160M"])
    colorbar.ax.minorticks_off()
    colorbar.ax.tick_params(labelsize=6.1, length=2.5, width=0.55, pad=1.5)
    colorbar.outline.set_linewidth(0.45)
    colorbar.outline.set_edgecolor("0.4")
    if LOWER_COLORBAR_ORIENTATION == "vertical":
        colorbar.ax.set_ylabel("Absolute change", fontsize=7.0, labelpad=4.0)
    else:
        colorbar.ax.set_title(
            "Absolute change",
            fontsize=7.0,
            pad=2.0,
        )


def draw_map() -> None:
    fig3.configure_style()
    regional_growth = load_regional_growth()
    source_projection = fig3.ROBINSON_PROJECTION
    projection = fig3.Projection(
        source_projection.name,
        source_projection.fn,
        lambda: fig3.frame_path(
            source_projection.fn,
            lon_min=-180,
            lon_max=180,
            lat_min=source_projection.lat_min,
            lat_max=NORTH_CLIP_LAT,
        ),
        lon_min=-180,
        lon_max=180,
        lat_min=source_projection.lat_min,
        lat_max=NORTH_CLIP_LAT,
    )
    elevation_zones = fig3.load_base_context()
    continent_lines = load_continent_boundary_lines(projection.fn)
    shared_continent_lines = load_shared_continent_boundaries(projection.fn)
    found = set(elevation_zones["elevation_group"].dropna().astype(str))
    missing = [band for band in ELEVATION_ORDER if band not in found]
    if missing:
        raise ValueError(f"Missing elevation bands in map input: {missing}")

    frame = projection.frame_fn()
    frame_patch = PathPatch(frame, facecolor=OCEAN_COLOR, edgecolor="none", zorder=0)
    frame_vertices = frame.vertices[:-1]
    extent = (
        float(frame_vertices[:, 0].min()),
        float(frame_vertices[:, 0].max()),
        float(frame_vertices[:, 1].min()),
        float(frame_vertices[:, 1].max()),
    )

    fig = plt.figure(figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN))
    map_ax = fig.add_axes(MAP_AX_POSITION)
    absolute_ax = fig.add_axes(ABSOLUTE_AX_POSITION)
    growth_ax = fig.add_axes(GROWTH_AX_POSITION)
    map_ax.add_patch(frame_patch)
    fig3.add_graticule(map_ax, projection, frame_patch)

    polygon_count = 0
    for zorder, band in enumerate(ELEVATION_ORDER, start=2):
        rows = elevation_zones[elevation_zones["elevation_group"].astype(str).eq(band)]
        polygons, colors = fig3.project_rows(rows, projection.fn, color=ELEVATION_COLORS[band])
        polygon_count += len(polygons)
        if not polygons:
            continue
        collection = PolyCollection(
            polygons,
            facecolors=colors,
            edgecolors="none",
            linewidths=0,
            antialiaseds=False,
            rasterized=True,
            zorder=zorder,
        )
        collection.set_clip_path(frame_patch)
        map_ax.add_collection(collection)

    outline_style = "solid"
    for continent in REGION_ORDER:
        lines = continent_lines[continent]
        if not lines:
            continue
        halo = LineCollection(
            lines,
            colors=[(1.0, 1.0, 1.0, 0.92)],
            linewidths=CONTINENT_HALO_WIDTH,
            linestyles=outline_style,
            antialiaseds=True,
            rasterized=False,
            zorder=8.2,
        )
        halo.set_clip_path(frame_patch)
        map_ax.add_collection(halo)
        outline = LineCollection(
            lines,
            colors=[CONTINENT_OUTLINE_COLORS[continent]],
            linewidths=CONTINENT_OUTLINE_WIDTH,
            linestyles=outline_style,
            antialiaseds=True,
            rasterized=False,
            zorder=8.4,
        )
        outline.set_clip_path(frame_patch)
        map_ax.add_collection(outline)

    map_width_points = FIGURE_WIDTH_IN * 72 * 0.976
    pair_offset = 0.55 * (extent[1] - extent[0]) / map_width_points
    for pair, paths in shared_continent_lines.items():
        if not paths:
            continue
        separator = LineCollection(
            paths,
            colors=[(1.0, 1.0, 1.0, 0.96)],
            linewidths=SHARED_BORDER_SEPARATOR_WIDTH,
            linestyles=outline_style,
            antialiaseds=True,
            rasterized=False,
            zorder=8.5,
        )
        separator.set_clip_path(frame_patch)
        map_ax.add_collection(separator)
        for direction, continent in zip((-1, 1), pair):
            paired_paths = [
                offset_polyline(path, direction * pair_offset) for path in paths
            ]
            paired_outline = LineCollection(
                paired_paths,
                colors=[CONTINENT_OUTLINE_COLORS[continent]],
                linewidths=CONTINENT_OUTLINE_WIDTH,
                linestyles=outline_style,
                antialiaseds=True,
                rasterized=False,
                zorder=8.6,
            )
            paired_outline.set_clip_path(frame_patch)
            map_ax.add_collection(paired_outline)

    equator_lon = np.linspace(projection.lon_min, projection.lon_max, 800)
    equator_x, equator_y = projection.fn(equator_lon, np.zeros_like(equator_lon))
    (equator_line,) = map_ax.plot(
        equator_x,
        equator_y,
        color=(0.26, 0.37, 0.42, 0.34),
        linewidth=0.36,
        linestyle=(0, (3.0, 2.4)),
        dash_capstyle="butt",
        zorder=8,
    )
    equator_line.set_clip_path(frame_patch)

    frame_outline = (
        FRAME_OUTLINE_PATH_FACTORY()
        if FRAME_OUTLINE_PATH_FACTORY is not None
        else frame
    )
    map_ax.add_patch(PathPatch(frame_outline, facecolor="none", edgecolor=FRAME_COLOR, linewidth=0.65, zorder=9))
    pad_x = (extent[1] - extent[0]) * 0.003
    pad_y = (extent[3] - extent[2]) * 0.005
    map_ax.set_xlim(extent[0] - pad_x, extent[1] + pad_x)
    map_ax.set_ylim(extent[2] - pad_y, extent[3] + pad_y)
    map_ax.set_aspect("equal", adjustable="box")
    map_ax.set_axis_off()

    draw_absolute_change_matrix(fig, absolute_ax, regional_growth)
    draw_growth_matrix(fig, growth_ax, regional_growth)
    growth_ax.tick_params(axis="y", labelleft=False)
    absolute_center_x = (
        absolute_ax.get_position().x0 + absolute_ax.get_position().x1
    ) / 2
    growth_center_x = (
        growth_ax.get_position().x0 + growth_ax.get_position().x1
    ) / 2
    fig.text(MAP_TITLE_X, 0.985, "A", ha="center", va="top", fontsize=10.2, fontweight="bold")
    fig.text(MAP_TITLE_X, 0.958, "Global elevation bands", ha="center", va="top", fontsize=8.9)
    fig.text(absolute_center_x, LOWER_PANEL_LABEL_Y, "B", ha="center", va="top", fontsize=10.2, fontweight="bold")
    fig.text(absolute_center_x, LOWER_PANEL_TITLE_Y, "Absolute population change, 2015–2025", ha="center", va="top", fontsize=8.6)
    fig.text(growth_center_x, LOWER_PANEL_LABEL_Y, "C", ha="center", va="top", fontsize=10.2, fontweight="bold")
    fig.text(growth_center_x, LOWER_PANEL_TITLE_Y, "Percent population change, 2015–2025", ha="center", va="top", fontsize=8.6)

    handles = [
        Patch(facecolor=ELEVATION_COLORS[band], edgecolor="none", label=ELEVATION_LABELS[band])
        for band in ELEVATION_ORDER
    ]
    if MAP_LEGEND_LAYOUT == "right":
        elevation_legend = fig.legend(
            handles=list(reversed(handles)),
            loc="upper left",
            bbox_to_anchor=(0.735, 0.915),
            ncol=1,
            frameon=False,
            fontsize=6.8,
            handlelength=1.65,
            handleheight=1.10,
            labelspacing=0.42,
            handletextpad=0.45,
            borderaxespad=0.0,
            title="Elevation band",
            title_fontsize=7.5,
        )
    else:
        elevation_legend = fig.legend(
            handles=handles,
            loc="lower center",
            bbox_to_anchor=(0.500, ELEVATION_LEGEND_Y),
            ncol=6,
            frameon=False,
            fontsize=7.0,
            handlelength=1.70,
            handleheight=1.25,
            columnspacing=0.72,
            handletextpad=0.40,
            title="Elevation band",
            title_fontsize=7.5,
        )
    elevation_legend._legend_box.align = "center"

    continent_handles = [
        Line2D(
            [0],
            [0],
            color=CONTINENT_OUTLINE_COLORS[continent],
            linewidth=CONTINENT_LEGEND_LINEWIDTH,
            linestyle=outline_style,
            label=continent,
        )
        for continent in REGION_ORDER
    ]
    if MAP_LEGEND_LAYOUT == "right":
        continent_legend = fig.legend(
            handles=continent_handles,
            loc="upper left",
            bbox_to_anchor=(0.735, 0.765),
            ncol=1,
            frameon=False,
            fontsize=6.8,
            handlelength=2.15,
            labelspacing=0.38,
            handletextpad=0.45,
            borderaxespad=0.0,
            title="Continent",
            title_fontsize=7.5,
        )
    else:
        continent_legend = fig.legend(
            handles=continent_handles,
            loc="lower center",
            bbox_to_anchor=(0.500, CONTINENT_LEGEND_Y),
            ncol=6,
            frameon=False,
            fontsize=6.8,
            handlelength=2.15,
            columnspacing=0.80,
            handletextpad=0.38,
        )
    continent_legend._legend_box.align = "center"

    path = FIG_DIR / f"{OUTPUT_STEM}.pdf"
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02, facecolor="white")

    plt.close(fig)
    print(f"Saved {path.relative_to(ROOT)}")


def main() -> None:
    draw_map()


if __name__ == "__main__":
    main()
