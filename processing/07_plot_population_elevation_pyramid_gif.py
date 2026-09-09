"""Generate the production elevation-threshold population-pyramid GIF.

This writes assets/population_by_elevation_pyramid.gif, which is
embedded at the top of the public README.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path("/tmp") / "matplotlib-hypso-gif"))

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter, FixedLocator, MaxNLocator


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "assets"

INPUT_POPULATION_BY_ELEVATION = DATA / "fact_population_by_integer_elevation_age_sex_2015_2025.parquet"
OUT_GIF = FIG / "population_by_elevation_pyramid.gif"
OUT_CONTINENT_DIR = FIG / "population_by_elevation_continents"
OUT_CONTINENT_PANEL_GIF = OUT_CONTINENT_DIR / "population_by_elevation_pyramid_continents_6panel.gif"

YEAR = 2025
YEAR_COL = "year"
GEOGRAPHY_COL = "geography_level"
CONTINENT_COL = "continent"
ELEV_COL = "elevation_m"
SEX_COL = "sex"
AGE_LABEL_COL = "age_label"
POP_COL = "population_count"

MIN_ELEV_M = 0
MAX_ELEV_M = 8000
FPS = 12
DPI = 120
SYMLINTHRESH_M = 10
Y_TICKS_M = [0, 20, 50, 100, 150, 500, 1500, 2500, 3500, 8000]
# Inspired by wesanderson::wes_palette("Zissou1").
ZISSOU_BLUE = "#3B9AB2"
ZISSOU_TEAL = "#78B7C5"
ZISSOU_YELLOW = "#EBCC2A"
ZISSOU_GOLD = "#E1AF00"
ZISSOU_RED = "#F21A00"
ELEVATION_BINS = [
    ("<100 m", 0, 100, "#E8F4F7"),
    ("100-499 m", 100, 500, "#D7EBF0"),
    ("500-1,499 m", 500, 1500, "#F8EFC5"),
    ("1,500-2,499 m", 1500, 2500, "#F2D985"),
    ("2,500-3,499 m", 2500, 3500, "#EDB860"),
    ("≥3,500 m", 3500, MAX_ELEV_M, "#F3A08A"),
]
ELEVATION_BOUNDARIES_M = [100, 500, 1500, 2500, 3500]
UPPER_TAIL_FRAMES = 18
BELOW_3500_FRAMES = 320
BELOW_3500_EASING_POWER = 3.1

MALE_COLOR = ZISSOU_BLUE
FEMALE_COLOR = ZISSOU_RED
DOT_COLOR = ZISSOU_YELLOW
GRID_COLOR = "#D9D9D9"
AXIS_COLOR = "#111111"
TEXT_COLOR = "#111111"
LINE_COLOR = "#2F3A3D"
SHADE_COLOR = ZISSOU_TEAL
CONTINENT_ORDER = ["Africa", "Asia", "Europe", "North America", "Oceania", "South America"]
CONTINENT_COLORS = {
    "Africa": "#FF6B35",
    "Asia": "#00A6D6",
    "Europe": "#9B7CFF",
    "North America": "#FF2D95",
    "Oceania": "#39B54A",
    "South America": "#F5B700",
}


mpl.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.labelsize": 10,
        "axes.titlesize": 12,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


def load_population_year(year: int, geography_level: str, continent: str | None = None) -> pd.DataFrame:
    if not INPUT_POPULATION_BY_ELEVATION.exists():
        raise FileNotFoundError(f"Missing input: {INPUT_POPULATION_BY_ELEVATION.relative_to(ROOT)}")

    filters = [(YEAR_COL, "=", year), (GEOGRAPHY_COL, "=", geography_level)]
    if continent is not None:
        filters.append((CONTINENT_COL, "=", continent))

    df = pd.read_parquet(
        INPUT_POPULATION_BY_ELEVATION,
        columns=[YEAR_COL, GEOGRAPHY_COL, CONTINENT_COL, ELEV_COL, SEX_COL, AGE_LABEL_COL, POP_COL],
        filters=filters,
    )

    df[ELEV_COL] = pd.to_numeric(df[ELEV_COL], errors="coerce")
    df[POP_COL] = pd.to_numeric(df[POP_COL], errors="coerce").fillna(0)
    df = df.dropna(subset=[ELEV_COL])
    if df.empty:
        label = f"{geography_level}" if continent is None else f"{geography_level}/{continent}"
        raise ValueError(f"No integer-elevation rows found for {label}, {year}.")
    return df


def load_continents_year(year: int) -> pd.DataFrame:
    return load_population_year(year=year, geography_level="continent")


def make_5yr_age_bin(age_label) -> str:
    s = str(age_label).strip().lower()
    nums = re.findall(r"\d+", s)
    if not nums:
        return s
    lo = int(nums[0])
    if lo < 5:
        return "0-4"
    if "+" in s:
        return f"{(lo // 5) * 5}+"
    lo5 = (lo // 5) * 5
    return f"{lo5}-{lo5 + 4}"


def age_bin_sort_value(age_bin) -> int:
    nums = re.findall(r"\d+", str(age_bin))
    return int(nums[0]) if nums else 999


def clean_sex(x) -> str:
    s = str(x).strip().lower()
    if s in {"m", "male", "men", "1"}:
        return "Male"
    if s in {"f", "female", "women", "2"}:
        return "Female"
    return str(x)


def fmt_population(x, pos=None) -> str:
    x = abs(x)
    def scaled_label(value: float, scale: float, suffix: str) -> str:
        scaled = value / scale
        if scaled >= 10:
            label = f"{scaled:.0f}"
        else:
            label = f"{scaled:.1f}".rstrip("0").rstrip(".")
        return f"{label}{suffix}"

    if x >= 1e9:
        return scaled_label(x, 1e9, "B")
    if x >= 1e6:
        return scaled_label(x, 1e6, "M")
    if x >= 1e3:
        return scaled_label(x, 1e3, "K")
    return f"{x:.0f}"


def fmt_elevation(x, pos=None) -> str:
    return f"{x:,.0f}"


def tidy_axes(ax):
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(AXIS_COLOR)
        spine.set_linewidth(0.8)
    ax.tick_params(axis="both", colors=AXIS_COLOR, width=0.8, length=3.5, direction="out")


def make_descending_thresholds() -> np.ndarray:
    """Move quickly through the sparse upper tail, then ease toward sea level."""
    upper_tail = np.expm1(np.linspace(np.log1p(MAX_ELEV_M), np.log1p(3500), UPPER_TAIL_FRAMES))
    upper_tail = np.round(upper_tail).astype(int)
    t = np.linspace(0, 1, BELOW_3500_FRAMES)
    below_highlands = np.round(3500 * (1 - t) ** BELOW_3500_EASING_POWER).astype(int)

    thresholds = np.array(
        sorted(
            set(np.concatenate([upper_tail, below_highlands[1:]]).astype(int)),
            reverse=True,
        )
    )
    thresholds = thresholds[(thresholds >= MIN_ELEV_M) & (thresholds <= MAX_ELEV_M)]
    if thresholds[0] != MAX_ELEV_M:
        thresholds = np.insert(thresholds, 0, MAX_ELEV_M)
    if thresholds[-1] != MIN_ELEV_M:
        thresholds = np.append(thresholds, MIN_ELEV_M)
    return thresholds


def draw_elevation_bands(ax):
    for _label, lo, hi, color in ELEVATION_BINS:
        visible_hi = ax.get_ylim()[1] if hi >= MAX_ELEV_M else hi
        ax.axhspan(lo, visible_hi, facecolor=color, alpha=0.34, edgecolor="none", zorder=0)

    for boundary in ELEVATION_BOUNDARIES_M:
        ax.axhline(boundary, color="#6A6A6A", linewidth=0.75, alpha=0.55, zorder=2)


def build_animation_data(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["sex_clean"] = df[SEX_COL].apply(clean_sex)
    df = df[df["sex_clean"].isin(["Male", "Female"])].copy()
    df["age_bin"] = df[AGE_LABEL_COL].apply(make_5yr_age_bin)
    df["elevation_capped_m"] = df[ELEV_COL].clip(lower=MIN_ELEV_M, upper=MAX_ELEV_M).round().astype(int)

    grouped = (
        df.groupby(["elevation_capped_m", "age_bin", "sex_clean"], as_index=False)[POP_COL]
        .sum()
        .rename(columns={"elevation_capped_m": "elevation_m", POP_COL: "population"})
    )

    age_order = sorted(grouped["age_bin"].unique(), key=age_bin_sort_value)
    sex_order = ["Male", "Female"]
    elevations = np.arange(MIN_ELEV_M, MAX_ELEV_M + 1)
    full_index = pd.MultiIndex.from_product(
        [elevations, age_order, sex_order],
        names=["elevation_m", "age_bin", "sex_clean"],
    )

    wide = (
        grouped.set_index(["elevation_m", "age_bin", "sex_clean"])["population"]
        .reindex(full_index, fill_value=0)
        .reset_index()
    )
    wide["cum_below"] = (
        wide.sort_values("elevation_m").groupby(["age_bin", "sex_clean"])["population"].cumsum()
    )

    cum = (
        wide.pivot_table(
            index="elevation_m",
            columns=["age_bin", "sex_clean"],
            values="cum_below",
            fill_value=0,
        )
        .sort_index()
    )

    cdf = wide.groupby("elevation_m", as_index=False)["population"].sum().sort_values("elevation_m")
    cdf["cum_below"] = cdf["population"].cumsum()
    cdf["cum_frac"] = cdf["cum_below"] / cdf["cum_below"].iloc[-1]

    full_ref = cum.loc[MAX_ELEV_M]
    full_male = np.array([full_ref.get((age, "Male"), 0) for age in age_order], dtype=float)
    full_female = np.array([full_ref.get((age, "Female"), 0) for age in age_order], dtype=float)

    return {
        "cum": cum,
        "cdf": cdf,
        "age_order": age_order,
        "full_male": full_male,
        "full_female": full_female,
        "xmax": max(full_male.max(), full_female.max()) * 1.12,
        "ypos": np.arange(len(age_order)),
    }


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def render_gif(data: dict, out_gif: Path, title: str, x_max: float | None = None) -> None:
    thresholds = make_descending_thresholds()
    out_gif.parent.mkdir(parents=True, exist_ok=True)

    print(f"GIF: {out_gif.relative_to(ROOT)}")
    print(f"Frames: {len(thresholds):,}; duration: {len(thresholds) / FPS:.1f} s")

    fig = plt.figure(figsize=(10.0, 6.2))
    gs = GridSpec(1, 2, width_ratios=[1.08, 0.92], wspace=0.24, figure=fig)
    ax_pyr = fig.add_subplot(gs[0, 0])
    ax_cdf = fig.add_subplot(gs[0, 1])
    fig.subplots_adjust(top=0.88, left=0.078, right=0.965, bottom=0.13)
    fig.suptitle(
        title,
        y=0.955,
        fontsize=13.5,
        color=TEXT_COLOR,
    )

    cum = data["cum"]
    cdf = data["cdf"]
    age_order = data["age_order"]
    ypos = data["ypos"]

    def get_pyramid_values(threshold: int):
        row = cum.loc[int(threshold)]
        male = np.array([row.get((age, "Male"), 0) for age in age_order], dtype=float)
        female = np.array([row.get((age, "Female"), 0) for age in age_order], dtype=float)
        return male, female

    def draw_frame(i):
        threshold = int(thresholds[i])
        male, female = get_pyramid_values(threshold)
        cdf_row = cdf.loc[cdf["elevation_m"].eq(threshold)]
        cum_pop = float(cdf_row["cum_below"].iloc[0])
        cum_frac = float(cdf_row["cum_frac"].iloc[0]) * 100.0

        ax_pyr.clear()
        ax_cdf.clear()
        ax_pyr.set_axisbelow(True)
        ax_cdf.set_axisbelow(True)

        ax_pyr.grid(
            True,
            which="major",
            axis="x",
            linestyle="--",
            linewidth=0.55,
            color=GRID_COLOR,
            alpha=0.85,
            zorder=0,
        )
        ax_pyr.barh(ypos, -data["full_male"], height=0.84, color=MALE_COLOR, alpha=0.13, edgecolor="none", zorder=2)
        ax_pyr.barh(ypos, data["full_female"], height=0.84, color=FEMALE_COLOR, alpha=0.13, edgecolor="none", zorder=2)
        ax_pyr.barh(ypos, -male, height=0.60, color=MALE_COLOR, alpha=0.96, edgecolor=AXIS_COLOR, linewidth=0.25, zorder=3)
        ax_pyr.barh(ypos, female, height=0.60, color=FEMALE_COLOR, alpha=0.96, edgecolor=AXIS_COLOR, linewidth=0.25, zorder=3)
        ax_pyr.axvline(0, color=AXIS_COLOR, linewidth=0.8, zorder=4)
        ax_pyr.set_yticks(ypos)
        ax_pyr.set_yticklabels(age_order)
        plot_xmax = data["xmax"] if x_max is None else x_max
        ax_pyr.set_xlim(-plot_xmax, plot_xmax)
        ax_pyr.xaxis.set_major_locator(MaxNLocator(nbins=7, steps=[1, 2, 2.5, 5, 10], symmetric=True))
        ax_pyr.xaxis.set_major_formatter(FuncFormatter(fmt_population))
        ax_pyr.set_xlabel("Population")
        ax_pyr.set_ylabel("Age group")
        ax_pyr.text(
            0.02,
            0.985,
            f"Population below {threshold:,.0f} m\n{cum_pop / 1e9:.2f}B ({cum_frac:.1f}%)",
            transform=ax_pyr.transAxes,
            ha="left",
            va="top",
            fontsize=9.2,
            color=TEXT_COLOR,
            bbox={"facecolor": "white", "alpha": 0.82, "edgecolor": "none", "pad": 1.6},
        )
        ax_pyr.text(0.25, -0.085, "Male", transform=ax_pyr.transAxes, ha="center", va="top", fontsize=9.5, color=TEXT_COLOR)
        ax_pyr.text(0.75, -0.085, "Female", transform=ax_pyr.transAxes, ha="center", va="top", fontsize=9.5, color=TEXT_COLOR)
        tidy_axes(ax_pyr)

        ax_cdf.set_xlim(0, 100)
        ax_cdf.set_ylim(MIN_ELEV_M, MAX_ELEV_M * 1.04)
        ax_cdf.set_yscale("symlog", linthresh=SYMLINTHRESH_M)
        ax_cdf.yaxis.set_major_locator(FixedLocator(Y_TICKS_M))
        ax_cdf.yaxis.set_major_formatter(FuncFormatter(fmt_elevation))
        draw_elevation_bands(ax_cdf)
        ax_cdf.grid(True, which="major", linestyle="--", linewidth=0.55, color=GRID_COLOR, alpha=0.72, zorder=1)
        ax_cdf.fill_betweenx(cdf["elevation_m"], 0, cdf["cum_frac"] * 100, color=SHADE_COLOR, alpha=0.08, zorder=1)
        ax_cdf.plot(cdf["cum_frac"] * 100, cdf["elevation_m"], color=LINE_COLOR, linewidth=2.0, alpha=0.98, zorder=3)
        ax_cdf.scatter([cum_frac], [threshold], s=55, color=DOT_COLOR, edgecolor=AXIS_COLOR, linewidth=0.9, zorder=5)
        ax_cdf.axhline(threshold, color=AXIS_COLOR, linewidth=0.8, alpha=0.45, linestyle="--", zorder=4)
        ax_cdf.set_xlabel("Cumulative population\nbelow threshold (%)")
        ax_cdf.set_ylabel("Elevation threshold (m, log scale)")
        ax_cdf.text(
            0.04,
            0.985,
            f"{threshold:,.0f} m",
            transform=ax_cdf.transAxes,
            ha="left",
            va="top",
            fontsize=9.5,
            color=TEXT_COLOR,
        )
        tidy_axes(ax_cdf)
        return []

    anim = FuncAnimation(fig, draw_frame, frames=len(thresholds), interval=1000 / FPS, blit=False)
    anim.save(out_gif, writer=PillowWriter(fps=FPS), dpi=DPI)
    plt.close(fig)

    print(f"Saved {out_gif.relative_to(ROOT)}")


def get_pyramid_values(data: dict, threshold: int) -> tuple[np.ndarray, np.ndarray]:
    row = data["cum"].loc[int(threshold)]
    age_order = data["age_order"]
    male = np.array([row.get((age, "Male"), 0) for age in age_order], dtype=float)
    female = np.array([row.get((age, "Female"), 0) for age in age_order], dtype=float)
    return male, female


def render_continent_panel_gif(continent_data: dict[str, dict], out_gif: Path) -> None:
    """Render the continent companion animation as one six-panel figure."""
    thresholds = make_descending_thresholds()
    out_gif.parent.mkdir(parents=True, exist_ok=True)

    print(f"GIF: {out_gif.relative_to(ROOT)}")
    print(f"Frames: {len(thresholds):,}; duration: {len(thresholds) / FPS:.1f} s")

    continents = [continent for continent in CONTINENT_ORDER if continent in continent_data]
    continents.extend(sorted(set(continent_data) - set(continents)))
    if len(continents) != 6:
        raise ValueError(f"Expected six continents for the panel GIF, found {len(continents)}: {continents}")

    fig = plt.figure(figsize=(17.2, 8.4))
    gs = GridSpec(2, 4, width_ratios=[1, 1, 1, 1.32], wspace=0.24, hspace=0.34, figure=fig)
    axes = [fig.add_subplot(gs[row, col]) for row in range(2) for col in range(3)]
    ax_cdf = fig.add_subplot(gs[:, 3])
    fig.subplots_adjust(top=0.84, left=0.055, right=0.985, bottom=0.11)
    fig.text(
        0.5,
        0.975,
        "Hypsographic Demography: Population by Elevation (2025)",
        ha="center",
        va="top",
        fontsize=18,
        fontweight="bold",
        color=TEXT_COLOR,
    )
    threshold_title = fig.text(0.5, 0.932, "", ha="center", va="top", fontsize=15, color=TEXT_COLOR)

    def draw_frame(i):
        threshold = int(thresholds[i])
        threshold_title.set_text(f"Population below {threshold:,.0f} m")

        for ax_i, (ax, continent) in enumerate(zip(axes, continents)):
            data = continent_data[continent]
            continent_color = CONTINENT_COLORS.get(continent, LINE_COLOR)
            male, female = get_pyramid_values(data, threshold)
            cdf = data["cdf"]
            cdf_row = cdf.loc[cdf["elevation_m"].eq(threshold)]
            cum_pop = float(cdf_row["cum_below"].iloc[0])
            cum_frac = float(cdf_row["cum_frac"].iloc[0]) * 100.0

            ax.clear()
            ax.set_axisbelow(True)
            ax.grid(
                True,
                which="major",
                axis="x",
                linestyle="--",
                linewidth=0.48,
                color=GRID_COLOR,
                alpha=0.75,
                zorder=0,
            )
            ax.barh(
                data["ypos"],
                -data["full_male"],
                height=0.82,
                color=MALE_COLOR,
                alpha=0.12,
                edgecolor="none",
                zorder=2,
            )
            ax.barh(
                data["ypos"],
                data["full_female"],
                height=0.82,
                color=FEMALE_COLOR,
                alpha=0.12,
                edgecolor="none",
                zorder=2,
            )
            ax.barh(
                data["ypos"],
                -male,
                height=0.58,
                color=MALE_COLOR,
                alpha=0.96,
                edgecolor=AXIS_COLOR,
                linewidth=0.18,
                zorder=3,
            )
            ax.barh(
                data["ypos"],
                female,
                height=0.58,
                color=FEMALE_COLOR,
                alpha=0.96,
                edgecolor=AXIS_COLOR,
                linewidth=0.18,
                zorder=3,
            )
            ax.axvline(0, color=AXIS_COLOR, linewidth=0.72, zorder=4)
            ax.set_title(continent, fontsize=13, color=continent_color, fontweight="bold", pad=7)
            ax.set_yticks(data["ypos"])
            if ax_i % 3 == 0:
                ax.set_yticklabels(data["age_order"])
                ax.set_ylabel("Age group", fontsize=11.5)
            else:
                ax.tick_params(axis="y", labelleft=False)
            if ax_i >= 3:
                ax.set_xlabel("Population", fontsize=11.5)
            plot_xmax = data["xmax"]
            ax.set_xlim(-plot_xmax, plot_xmax)
            ax.xaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 2.5, 5, 10], symmetric=True))
            ax.xaxis.set_major_formatter(FuncFormatter(fmt_population))
            ax.tick_params(axis="both", labelsize=9.8)
            ax.text(
                0.02,
                0.965,
                f"{fmt_population(cum_pop)} ({cum_frac:.1f}%)",
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=10.2,
                color=TEXT_COLOR,
                bbox={"facecolor": "white", "alpha": 0.82, "edgecolor": "none", "pad": 1.4},
            )
            if ax_i == 0:
                ax.text(
                    0.965,
                    0.965,
                    "Female",
                    transform=ax.transAxes,
                    ha="right",
                    va="top",
                    fontsize=9.4,
                    fontweight="bold",
                    color="white",
                    bbox={"facecolor": FEMALE_COLOR, "edgecolor": "none", "pad": 2.2},
                )
                ax.text(
                    0.965,
                    0.875,
                    "Male",
                    transform=ax.transAxes,
                    ha="right",
                    va="top",
                    fontsize=9.4,
                    fontweight="bold",
                    color="white",
                    bbox={"facecolor": MALE_COLOR, "edgecolor": "none", "pad": 2.2},
                )
            tidy_axes(ax)
            for spine in ax.spines.values():
                spine.set_color(continent_color)
                spine.set_linewidth(1.65)

        ax_cdf.clear()
        ax_cdf.set_axisbelow(True)
        ax_cdf.set_xlim(0, 100)
        ax_cdf.set_ylim(MIN_ELEV_M, MAX_ELEV_M * 1.04)
        ax_cdf.set_yscale("symlog", linthresh=SYMLINTHRESH_M)
        ax_cdf.yaxis.set_major_locator(FixedLocator(Y_TICKS_M))
        ax_cdf.yaxis.set_major_formatter(FuncFormatter(fmt_elevation))
        draw_elevation_bands(ax_cdf)
        ax_cdf.grid(True, which="major", linestyle="--", linewidth=0.55, color=GRID_COLOR, alpha=0.72, zorder=1)
        for continent in continents:
            data = continent_data[continent]
            cdf = data["cdf"]
            continent_color = CONTINENT_COLORS.get(continent, LINE_COLOR)
            cdf_row = cdf.loc[cdf["elevation_m"].eq(threshold)]
            cum_frac = float(cdf_row["cum_frac"].iloc[0]) * 100.0
            ax_cdf.plot(
                cdf["cum_frac"] * 100,
                cdf["elevation_m"],
                color=continent_color,
                linewidth=2.35,
                alpha=0.95,
                label=continent,
                zorder=3,
            )
            ax_cdf.scatter(
                [cum_frac],
                [threshold],
                s=56,
                color=continent_color,
                edgecolor=AXIS_COLOR,
                linewidth=0.75,
                zorder=5,
            )
        ax_cdf.axhline(threshold, color=AXIS_COLOR, linewidth=0.85, alpha=0.5, linestyle="--", zorder=4)
        ax_cdf.set_title("Elevation profile", fontsize=13, color=TEXT_COLOR, fontweight="bold", pad=7)
        ax_cdf.set_xlabel("Cumulative population\nbelow threshold (%)", fontsize=11.5)
        ax_cdf.set_ylabel("Elevation threshold (m, log scale)", fontsize=11.5)
        ax_cdf.tick_params(axis="both", labelsize=9.8)
        ax_cdf.text(
            0.04,
            0.985,
            f"{threshold:,.0f} m",
            transform=ax_cdf.transAxes,
            ha="left",
            va="top",
            fontsize=10.5,
            color=TEXT_COLOR,
            bbox={"facecolor": "white", "alpha": 0.82, "edgecolor": "none", "pad": 1.4},
        )
        ax_cdf.legend(loc="lower right", fontsize=9, frameon=True, framealpha=0.9, edgecolor="#CCCCCC")
        tidy_axes(ax_cdf)

        return []

    anim = FuncAnimation(fig, draw_frame, frames=len(thresholds), interval=1000 / FPS, blit=False)
    anim.save(out_gif, writer=PillowWriter(fps=FPS), dpi=DPI)
    plt.close(fig)

    print(f"Saved {out_gif.relative_to(ROOT)}")


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)

    global_df = load_population_year(year=YEAR, geography_level="global", continent="Global")
    global_data = build_animation_data(global_df)
    render_gif(
        global_data,
        OUT_GIF,
        title=f"Hypsographic demography: population by elevation ({YEAR})",
    )

    continent_df = load_continents_year(YEAR)
    continent_names = [name for name in CONTINENT_ORDER if name in set(continent_df[CONTINENT_COL])]
    extra_names = sorted(set(continent_df[CONTINENT_COL]) - set(continent_names))
    continent_names.extend(extra_names)
    print("Continents:", ", ".join(continent_names))

    continent_data = {
        continent: build_animation_data(continent_df[continent_df[CONTINENT_COL].eq(continent)].copy())
        for continent in continent_names
    }
    for continent, data in continent_data.items():
        render_gif(
            data,
            OUT_CONTINENT_DIR / f"population_by_elevation_pyramid_{slugify(continent)}.gif",
            title=f"{continent}, {YEAR}",
        )
    render_continent_panel_gif(continent_data, OUT_CONTINENT_PANEL_GIF)


if __name__ == "__main__":
    main()
