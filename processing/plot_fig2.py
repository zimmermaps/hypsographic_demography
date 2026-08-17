"""Plot manuscript Figure 2 from the retained publication table."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path("/tmp") / "matplotlib-hypso-fig2-5")
)

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "figure_data" / "fig2_elevation_settlement_age_shares.csv"
FIGURE_DIR = ROOT / "figures"
OUTPUT_STEM = "fig2"

ELEVATION_ORDER = [
    "<100 m",
    "100-499 m",
    "500-1499 m",
    "1500-2499 m",
    "2500-3499 m",
    ">=3500 m",
]
ELEVATION_LABELS = {
    "<100 m": "<100 m",
    "100-499 m": "100-499 m",
    "500-1499 m": "500-1,499 m",
    "1500-2499 m": "1,500-2,499 m",
    "2500-3499 m": "2,500-3,499 m",
    ">=3500 m": "≥3,500 m",
}
SETTLEMENT_ORDER = [
    "Low-density rural",
    "Rural cluster",
    "Peri-urban",
    "Semi-dense urban",
    "Dense urban",
    "Urban centre",
]
def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 6.4,
            "axes.titlesize": 7.4,
            "axes.labelsize": 6.8,
            "xtick.labelsize": 5.4,
            "ytick.labelsize": 5.8,
            "axes.linewidth": 0.55,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def load_data() -> pd.DataFrame:
    if not INPUT.exists():
        raise FileNotFoundError(f"Required Figure 2 table not found: {INPUT}")

    summary = pd.read_csv(INPUT)

    expected_cells = len(ELEVATION_ORDER) * len(SETTLEMENT_ORDER)
    if len(summary) != expected_cells:
        raise ValueError(
            f"Expected {expected_cells} elevation-settlement cells; "
            f"found {len(summary)}."
        )
    if summary.isna().any().any():
        missing = summary.columns[summary.isna().any()].tolist()
        raise ValueError(f"Missing values in Figure 2.5 data: {missing}")

    summary["elevation_group"] = pd.Categorical(
        summary["elevation_group"], ELEVATION_ORDER, ordered=True
    )
    summary["settlement_class"] = pd.Categorical(
        summary["settlement_class"], SETTLEMENT_ORDER, ordered=True
    )
    summary = summary.sort_values(
        ["elevation_group", "settlement_class"]
    ).reset_index(drop=True)

    return summary


def matrix(data: pd.DataFrame, value: str) -> pd.DataFrame:
    return (
        data.pivot(
            index="elevation_group",
            columns="settlement_class",
            values=value,
        )
        .reindex(
            index=list(reversed(ELEVATION_ORDER)),
            columns=SETTLEMENT_ORDER,
        )
        .astype(float)
    )


def text_color(cmap, norm, value: float) -> str:
    red, green, blue, _alpha = cmap(norm(value))
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return "white" if luminance < 0.50 else "0.12"


def annotate_matrix(ax, values, cmap, norm, *, population=False) -> None:
    for row in range(values.shape[0]):
        for column in range(values.shape[1]):
            value = float(values[row, column])
            label = (
                f"{value:.0f}" if population and value >= 10 else f"{value:.1f}"
            )
            ax.text(
                column,
                row,
                label,
                ha="center",
                va="center",
                fontsize=4.7,
                color=text_color(cmap, norm, value),
            )


def draw_panel(
    fig,
    ax,
    *,
    data,
    title,
    cmap,
    norm,
    colorbar_label,
    ticks,
    panel,
    column,
    population=False,
    add_colorbar=True,
    extend="neither",
    colorbar_ax=None,
    colorbar_limits=None,
    show_xlabels=True,
) -> mpl.image.AxesImage:
    cmap = mpl.colormaps[cmap] if isinstance(cmap, str) else cmap
    values = data.to_numpy(dtype=float)
    image = ax.imshow(values, cmap=cmap, norm=norm, aspect="equal")
    annotate_matrix(ax, values, cmap, norm, population=population)

    ax.set_title(title, pad=6)
    ax.text(
        0.0,
        1.025,
        panel,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.8,
        fontweight="bold",
    )
    ax.set_xticks(np.arange(len(SETTLEMENT_ORDER)))
    if show_xlabels:
        ax.set_xticklabels(
            SETTLEMENT_ORDER,
            rotation=38,
            ha="right",
            rotation_mode="anchor",
        )
    else:
        ax.set_xticklabels([])
    matrix_elevation_order = list(reversed(ELEVATION_ORDER))
    ax.set_yticks(
        np.arange(len(matrix_elevation_order)),
        [ELEVATION_LABELS[value] for value in matrix_elevation_order],
    )
    ax.tick_params(axis="x", length=0, pad=2)
    ax.tick_params(
        axis="y",
        length=0,
        labelleft=(column == 0),
        pad=3,
    )
    ax.set_xticks(
        np.arange(-0.5, len(SETTLEMENT_ORDER), 1),
        minor=True,
    )
    ax.set_yticks(
        np.arange(-0.5, len(matrix_elevation_order), 1),
        minor=True,
    )
    ax.grid(which="minor", color="white", linewidth=0.45)
    ax.tick_params(which="minor", bottom=False, left=False)
    for spine in ax.spines.values():
        spine.set_linewidth(0.55)
        spine.set_color("0.38")
    if add_colorbar:
        colorbar_mappable = image
        if colorbar_limits is not None:
            lower, upper = colorbar_limits
            sampled_colors = cmap(
                np.linspace(norm(lower), norm(upper), 256)
            )
            display_cmap = mpl.colors.ListedColormap(
                sampled_colors,
                name=f"{cmap.name}_cropped_colorbar",
            )
            display_cmap.set_under(cmap(0.0))
            display_cmap.set_over(cmap(1.0))
            colorbar_mappable = mpl.cm.ScalarMappable(
                norm=mpl.colors.Normalize(vmin=lower, vmax=upper),
                cmap=display_cmap,
            )
        colorbar = fig.colorbar(
            colorbar_mappable,
            cax=colorbar_ax,
            ticks=ticks,
            extend=extend,
            aspect=28,
        )
        colorbar.ax.tick_params(labelsize=5.0, length=2, width=0.5, pad=2)
        colorbar.outline.set_linewidth(0.45)
        colorbar.set_label(colorbar_label, fontsize=5.5, labelpad=3)
    return image


def draw_figure(data: pd.DataFrame) -> plt.Figure:
    configure_style()
    population_cmap = mpl.colors.LinearSegmentedColormap.from_list(
        "population_lavender_purple",
        ["#F1EEF6", "#D7D4EA", "#A6A1CF", "#756BB1", "#54278F"],
    )
    change_cmap = mpl.colors.LinearSegmentedColormap.from_list(
        "blue_teal_orange_red_purple_change",
        [
            (0.000, "#253494"),
            (0.200, "#2C7FB8"),
            (0.380, "#26A6A1"),
            (0.500, "#F3F1EC"),
            (0.600, "#FDAE6B"),
            (0.720, "#F16913"),
            (0.840, "#E31A1C"),
            (0.920, "#D01C6B"),
            (1.000, "#762A83"),
        ],
    )
    change_norm = mpl.colors.Normalize(vmin=-50, vmax=50, clip=False)

    panels = [
        {
            "value": "population_2025_millions",
            "title": "Population,\n2025",
            "cmap": population_cmap,
            "norm": mpl.colors.PowerNorm(gamma=0.45, vmin=0, vmax=2000),
            "label": "Population (millions)",
            "ticks": [1, 10, 100, 1000, 2000],
        },
        {
            "value": "population_change_percent",
            "title": "Population change,\n2015–2025",
            "cmap": change_cmap,
            "norm": change_norm,
            "label": "Change, 2015–2025 (%)",
            "ticks": [-15, 0, 10, 20, 30, 40, 50],
            "change": True,
        },
        {
            "value": "youth_share_2025_percent",
            "title": "Youth share,\n2025",
            "cmap": "YlGn",
            "norm": mpl.colors.Normalize(vmin=20, vmax=35),
            "label": "Youth share (%)",
            "ticks": [20, 25, 30, 35],
        },
        {
            "value": "youth_share_change_percent",
            "title": "Youth share change,\n2015–2025",
            "cmap": change_cmap,
            "norm": change_norm,
            "label": "Change, 2015–2025 (%)",
            "ticks": [-15, 0, 10, 20, 30, 40, 50],
            "change": True,
        },
        {
            "value": "old_age_share_2025_percent",
            "title": "Older-age share,\n2025",
            "cmap": "YlOrRd",
            "norm": mpl.colors.Normalize(vmin=4, vmax=14),
            "label": "Older-age share (%)",
            "ticks": [4, 6, 8, 10, 12, 14],
        },
        {
            "value": "old_age_share_change_percent",
            "title": "Older-age share change,\n2015–2025",
            "cmap": change_cmap,
            "norm": change_norm,
            "label": "Change, 2015–2025 (%)",
            "ticks": [-15, 0, 10, 20, 30, 40, 50],
            "change": True,
        },
    ]

    fig, axes = plt.subplots(
        3,
        2,
        figsize=(7.65, 6.60),
        sharey=True,
    )
    fig.subplots_adjust(
        left=0.105,
        right=0.950,
        top=0.955,
        bottom=0.105,
    hspace=0.25,
        wspace=0.24,
    )

    colorbar_axes = []
    for index, (ax, panel) in enumerate(zip(axes.ravel(), panels)):
        column = index % 2
        ax.set_anchor("E" if column == 0 else "W")
        colorbar_ax = fig.add_axes([0, 0, 0.01, 0.10])
        draw_panel(
            fig,
            ax,
            data=matrix(data, panel["value"]),
            title=panel["title"],
            cmap=panel["cmap"],
            norm=panel["norm"],
            colorbar_label=panel["label"],
            ticks=panel["ticks"],
            panel=chr(ord("A") + index),
            column=column,
            population=(index == 0),
            add_colorbar=True,
            extend=(
                "both" if panel.get("change", False)
                else panel.get("extend", "neither")
            ),
            colorbar_ax=colorbar_ax,
            colorbar_limits=(-15, 50) if panel.get("change", False) else None,
            show_xlabels=(index >= 4),
        )
        colorbar_axes.append((ax, colorbar_ax))

    fig.canvas.draw()
    for ax, colorbar_ax in colorbar_axes:
        position = ax.get_position()
        colorbar_ax.set_position(
            [position.x1 + 0.008, position.y0, 0.012, position.height]
        )
    return fig


def save_figure(fig: plt.Figure) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        FIGURE_DIR / f"{OUTPUT_STEM}.pdf",
        bbox_inches="tight",
        facecolor="white",
    )


def main() -> None:
    data = load_data()
    figure = draw_figure(data)
    save_figure(figure)
    plt.close(figure)
    print(f"Saved {(FIGURE_DIR / f'{OUTPUT_STEM}.pdf').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
