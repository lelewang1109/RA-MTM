#!/usr/bin/env python3
"""Draw four paper-ready theoretical schematics for RA-MTM.

All coordinates and values in these figures are illustrative.  The script does
not load experimental outputs and does not execute the RA-MTM optimizer.
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, Rectangle


OUT = Path(__file__).resolve().parent

# Feature identities use exactly the same colors in all four figures.
FEATURE = {
    1: "#3B77B6",  # blue
    2: "#E68632",  # orange
    3: "#2A9D8F",  # teal
    4: "#8064A2",  # purple
}
INK = "#20242A"
MID = "#626A73"
LIGHT = "#D8DDE3"
PALE = "#F3F5F7"
RED = "#C83E4D"
GREEN = "#4F8A5B"

mpl.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9.0,
        "axes.titlesize": 10.5,
        "axes.titleweight": "semibold",
        "axes.linewidth": 0.8,
        "lines.linewidth": 1.5,
        "patch.linewidth": 1.2,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    }
)


def clean(ax, xlim=(0, 1), ylim=(0, 1)):
    ax.set(xlim=xlim, ylim=ylim)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def panel(ax, letter, title):
    ax.text(0.01, 1.04, f"({letter})", transform=ax.transAxes, ha="left", va="bottom",
            fontsize=11, fontweight="bold", color=INK)
    ax.text(0.18, 1.04, title, transform=ax.transAxes, ha="left", va="bottom",
            fontsize=10.2, fontweight="semibold", color=INK)


def arrow_between(fig, left_ax, right_ax, label=None, y=0.52):
    p0, p1 = left_ax.get_position(), right_ax.get_position()
    a = FancyArrowPatch(
        (p0.x1 + 0.006, p0.y0 + y * p0.height),
        (p1.x0 - 0.006, p1.y0 + y * p1.height),
        transform=fig.transFigure,
        arrowstyle="-|>", mutation_scale=12, lw=1.2, color=MID,
    )
    fig.add_artist(a)
    if label:
        fig.text((p0.x1 + p1.x0) / 2, p0.y0 + y * p0.height + 0.035,
                 label, ha="center", va="bottom", fontsize=8, color=MID)


def save(fig, stem):
    svg = OUT / f"{stem}.svg"
    fig.savefig(svg, bbox_inches="tight")
    # Matplotlib leaves spaces at line endings in path data; normalize them so
    # generated SVG files remain clean and reviewable in Git.
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def draw_tree(ax, leaves=(1, 2, 3), y_leaf=0.82, y_merge=(0.51, 0.25)):
    """Draw a small augmented merge-tree schematic."""
    xs = np.linspace(0.18, 0.82, len(leaves))
    if len(leaves) == 3:
        # Leaves 1 and 2 merge, then merge with leaf 3.
        m1 = ((xs[0] + xs[1]) / 2, y_merge[0])
        root = (0.50, y_merge[1])
        for x in xs[:2]:
            ax.plot([x, m1[0]], [y_leaf, m1[1]], color=INK, lw=1.6)
        ax.plot([m1[0], root[0]], [m1[1], root[1]], color=INK, lw=1.6)
        ax.plot([xs[2], root[0]], [y_leaf, root[1]], color=INK, lw=1.6)
        for x, f in zip(xs, leaves):
            ax.add_patch(Circle((x, y_leaf), 0.034, fc=FEATURE[f], ec="white", lw=1.0, zorder=4))
        ax.add_patch(Circle(m1, 0.018, fc="white", ec=INK, zorder=4))
        ax.add_patch(Circle(root, 0.020, fc=INK, ec=INK, zorder=4))
    else:
        # Balanced four-leaf tree.
        m1, m2 = (0.30, 0.53), (0.70, 0.53)
        root = (0.50, 0.24)
        for x, m in zip(xs, (m1, m1, m2, m2)):
            ax.plot([x, m[0]], [y_leaf, m[1]], color=INK, lw=1.5)
        ax.plot([m1[0], root[0]], [m1[1], root[1]], color=INK, lw=1.5)
        ax.plot([m2[0], root[0]], [m2[1], root[1]], color=INK, lw=1.5)
        for x, f in zip(xs, leaves):
            ax.add_patch(Circle((x, y_leaf), 0.030, fc=FEATURE[f], ec="white", lw=1.0, zorder=4))
        for m in (m1, m2):
            ax.add_patch(Circle(m, 0.016, fc="white", ec=INK, zorder=4))
        ax.add_patch(Circle(root, 0.019, fc=INK, ec=INK, zorder=4))


def draw_interval(ax, z, w, y, feature, height=0.10, anchor=None, reference=None,
                  edge=None, alpha=0.90, label=None):
    edge = edge or FEATURE[feature]
    ax.add_patch(Rectangle((z - w / 2, y - height / 2), w, height,
                           fc=FEATURE[feature], ec=edge, alpha=alpha, lw=1.2))
    if reference is not None:
        ax.plot([reference, reference], [y - height * 0.85, y + height * 0.85],
                ls=(0, (3, 2)), color="#8A9098", lw=1.2, zorder=3)
    if anchor is not None:
        ax.plot(anchor, y, "o", ms=4.8, color=INK, zorder=5)
    if label:
        ax.text(z, y, label, ha="center", va="center", color="white",
                fontsize=8, fontweight="bold")


def feature_blob(ax, xy, size, feature, label=None, alpha=0.88, edge="white"):
    ax.add_patch(Ellipse(xy, size[0], size[1], fc=FEATURE[feature], ec=edge,
                         lw=1.1, alpha=alpha))
    if label:
        ax.text(*xy, label, ha="center", va="center", color="white",
                fontweight="bold", fontsize=8)


def theory_1():
    fig, axs = plt.subplots(1, 4, figsize=(14.2, 3.45), gridspec_kw={"wspace": 0.36})
    for ax in axs:
        clean(ax)

    # (a) Smooth, newly drawn illustrative scalar field.
    ax = axs[0]
    panel(ax, "a", "2D scalar field")
    x = np.linspace(-2.7, 2.7, 180)
    y = np.linspace(-2.0, 2.0, 140)
    X, Y = np.meshgrid(x, y)
    peaks = [(-1.25, 0.55, 0.72), (0.35, -0.55, 0.62), (1.35, 0.55, 0.55)]
    Z = sum(a * np.exp(-((X-cx)**2 + (Y-cy)**2) / (2 * 0.55**2)) for cx, cy, a in peaks)
    ax.contourf(X, Y, Z, levels=12, cmap="Greys", alpha=0.42)
    ax.contour(X, Y, Z, levels=7, colors="#8A9098", linewidths=0.45, alpha=0.55)
    for f, (cx, cy, _) in enumerate(peaks, 1):
        ax.add_patch(Ellipse((cx, cy), 0.95, 0.70, fc=FEATURE[f], ec="white", alpha=0.82))
        ax.text(cx, cy, f"F{f}", ha="center", va="center", color="white", fontweight="bold")
    ax.set(xlim=(-2.7, 2.7), ylim=(-2.0, 2.0))
    ax.text(0.5, -0.08, "spatial domain", transform=ax.transAxes, ha="center", color=MID)

    ax = axs[1]
    panel(ax, "b", "Augmented merge tree")
    draw_tree(ax)
    ax.text(0.50, 0.10, "topology + arc samples", ha="center", color=MID)

    ax = axs[2]
    panel(ax, "c", "Tree-guided 1D linearization")
    ax.annotate("", (0.92, 0.30), (0.08, 0.30), arrowprops=dict(arrowstyle="->", color=INK, lw=1.2))
    widths = [0.20, 0.26, 0.18]
    centers = [0.20, 0.48, 0.76]
    for f, z, w in zip((1, 2, 3), centers, widths):
        draw_interval(ax, z, w, 0.52, f, height=0.24, label=f"F{f}")
    ax.text(0.5, 0.72, "each feature remains contiguous", ha="center", color=INK)
    ax.text(0.5, 0.13, "1D sample order", ha="center", color=MID)

    ax = axs[3]
    panel(ax, "d", "Static temporal map")
    times = np.linspace(0.16, 0.88, 6)
    for j, t in enumerate(times):
        y0 = 0.75 - j * 0.105
        centers_t = [0.20 + 0.015*j, 0.48 + 0.010*j, 0.76 + 0.012*j]
        widths_t = [0.18, 0.24 + 0.008*j, 0.16]
        for f, z, w in zip((1, 2, 3), centers_t, widths_t):
            draw_interval(ax, z, w, y0, f, height=0.082, alpha=0.88)
    ax.annotate("time", (0.94, 0.13), (0.10, 0.13),
                arrowprops=dict(arrowstyle="->", color=INK, lw=1.2), ha="center", va="bottom")
    ax.text(0.50, 0.91, "time steps stacked in one view", ha="center", color=MID)

    arrow_between(fig, axs[0], axs[1])
    arrow_between(fig, axs[1], axs[2])
    arrow_between(fig, axs[2], axs[3])
    fig.suptitle("Merge Tree Map: from a spatial scalar field to a static temporal view",
                 y=1.04, fontsize=13, fontweight="semibold", color=INK)
    fig.text(0.5, -0.015, "Schematic only — coordinates and values are illustrative.",
             ha="center", fontsize=8, color=MID)
    save(fig, "theory_1_merge_tree_map_pipeline")


def theory_2():
    fig, axs = plt.subplots(1, 3, figsize=(14.4, 4.75), gridspec_kw={"wspace": 0.26})
    for ax in axs:
        clean(ax)

    # (a) Common translation.
    ax = axs[0]
    panel(ax, "a", "Common translation")
    x0 = [0.18, 0.43, 0.68]
    x1 = [v + 0.16 for v in x0]
    for row, xs, t in [(0.78, x0, "t₀"), (0.55, x1, "t₁")]:
        ax.text(0.05, row, t, ha="center", va="center", fontweight="bold", color=INK)
        for f, x in enumerate(xs, 1):
            feature_blob(ax, (x, row), (0.13, 0.115), f, f"F{f}")
    ax.annotate("common shift", (0.87, 0.66), (0.70, 0.66),
                arrowprops=dict(arrowstyle="-|>", color=INK), ha="center", va="bottom", color=INK)
    ax.annotate("d₁₂", (x0[1], 0.91), (x0[0], 0.91),
                arrowprops=dict(arrowstyle="<->", color=MID), ha="center", color=MID)
    ax.annotate("d₁₂", (x1[1], 0.42), (x1[0], 0.42),
                arrowprops=dict(arrowstyle="<->", color=MID), ha="center", color=MID)
    ax.text(0.50, 0.35, "dᵢⱼ(t₀) = dᵢⱼ(t₁)", ha="center", fontweight="semibold", color=INK)
    for f, z in zip((1, 2, 3), (0.25, 0.50, 0.75)):
        draw_interval(ax, z, 0.17, 0.19, f, height=0.09)
    ax.text(0.50, 0.07, "distance-based 1D layout may remain unchanged",
            ha="center", color=RED, fontweight="semibold", fontsize=8.5)

    # (b) Common growth.
    ax = axs[1]
    panel(ax, "b", "Common growth")
    xs = [0.20, 0.50, 0.80]
    for f, x in enumerate(xs, 1):
        feature_blob(ax, (x, 0.80), (0.115, 0.095), f, f"F{f}")
        feature_blob(ax, (x, 0.58), (0.175, 0.145), f, f"F{f}")
        ax.annotate("", (x, 0.66), (x, 0.72), arrowprops=dict(arrowstyle="-|>", color=MID, lw=1.0))
    ax.text(0.06, 0.80, "t₀", ha="center", fontweight="bold")
    ax.text(0.06, 0.58, "t₁", ha="center", fontweight="bold")
    ax.text(0.50, 0.45, "Aᵢ(t₁) > Aᵢ(t₀)  for all i", ha="center", color=INK, fontweight="semibold")
    ax.text(0.50, 0.36, "ŵᵢ = K Aᵢ / Σⱼ Aⱼ", ha="center", color=MID)
    for y, lab in [(0.27, "t₀"), (0.16, "t₁")]:
        ax.text(0.06, y, lab, ha="center", va="center", fontsize=8)
        for f, z in zip((1, 2, 3), (0.25, 0.50, 0.75)):
            draw_interval(ax, z, 0.19, y, f, height=0.075)
    ax.plot([0.145, 0.855], [0.10, 0.10], color=INK, lw=1.1)
    ax.annotate("K", (0.855, 0.10), (0.145, 0.10),
                arrowprops=dict(arrowstyle="<->", color=INK), ha="center", va="bottom")
    ax.text(0.50, 0.02, "relative-size encoding cannot reveal global growth",
            ha="center", color=RED, fontweight="semibold", fontsize=8.5)

    # (c) Hierarchy conflict.
    ax = axs[2]
    panel(ax, "c", "Hierarchy conflict")
    qs = [0.20, 0.50, 0.80]
    ax.annotate("world-x", (0.92, 0.70), (0.08, 0.70), arrowprops=dict(arrowstyle="->", color=INK))
    for i, q in enumerate(qs, 1):
        ax.plot([q, q], [0.66, 0.77], ls=(0, (3, 2)), color="#8A9098")
        ax.text(q, 0.79, f"q{i}", ha="center", color=MID)
    ax.text(0.50, 0.88, "reference order:  q₁ < q₂ < q₃", ha="center", color=INK)
    for f, q, w in zip((1, 2, 3), qs, (0.23, 0.22, 0.24)):
        draw_interval(ax, q, w, 0.57, f, height=0.11, anchor=q)
    ax.text(0.50, 0.46, "xᵢ = qᵢ", ha="center", color=MID)
    # Tree requires F1 and F3 to form one contiguous subtree.
    leaf_x = [0.20, 0.50, 0.80]
    for f, x in zip((1, 3, 2), leaf_x):
        ax.add_patch(Circle((x, 0.27), 0.028, fc=FEATURE[f], ec="white"))
        ax.text(x, 0.34, f"F{f}", ha="center", fontsize=8, color=FEATURE[f], fontweight="bold")
    ax.plot([leaf_x[0], 0.35, leaf_x[1]], [0.27, 0.16, 0.27], color=INK, lw=1.4)
    ax.plot([0.35, 0.50, leaf_x[2]], [0.16, 0.08, 0.27], color=INK, lw=1.4)
    ax.text(0.52, 0.16, "legal grouping: {F1,F3}", ha="center", color=INK, fontsize=8.5)
    ax.text(0.50, 0.535, "×", ha="center", va="center", color=RED, fontsize=26, fontweight="bold")
    ax.text(0.50, 0.01, "reference + absolute width + hierarchy may conflict",
            ha="center", color=RED, fontweight="semibold", fontsize=8.5)

    fig.suptitle("Three information gaps motivating RA-MTM", y=1.03,
                 fontsize=13, fontweight="semibold", color=INK)
    fig.text(0.5, -0.005, "Schematic only — sizes, positions, and distances are not experimental results.",
             ha="center", fontsize=8, color=MID)
    save(fig, "theory_2_missing_information")


def theory_3():
    fig, axs = plt.subplots(1, 6, figsize=(17.4, 3.8), gridspec_kw={"wspace": 0.34})
    for ax in axs:
        clean(ax)

    ax = axs[0]
    panel(ax, "a", "Original features")
    specs = [(1, (0.32, 0.65), (0.31, 0.23)), (2, (0.65, 0.43), (0.40, 0.29)), (3, (0.38, 0.22), (0.24, 0.18))]
    for f, xy, size in specs:
        feature_blob(ax, xy, size, f, f"F{f}")
        ax.plot(*xy, marker="+", ms=8, mew=1.4, color=INK)
        ax.text(xy[0]+0.03, xy[1]+size[1]/2+0.025, f"C{f},  A{f}", fontsize=8, color=INK)
    ax.text(0.5, 0.04, "centroid Cᵢ  +  measure Aᵢ", ha="center", color=MID)

    ax = axs[1]
    panel(ax, "b", "Fixed reference")
    ax.annotate("world-x", (0.93, 0.24), (0.08, 0.24), arrowprops=dict(arrowstyle="->", color=INK))
    qs = [0.24, 0.52, 0.78]
    for f, q, y in zip((1, 2, 3), qs, (0.78, 0.62, 0.47)):
        ax.plot(q, y, "+", ms=8, mew=1.4, color=FEATURE[f])
        ax.plot([q, q], [0.24, y], ls=(0, (3, 2)), color="#8A9098", lw=1.0)
        ax.text(q, 0.17, f"q{f}", ha="center", color=FEATURE[f], fontweight="semibold")
    ax.text(0.50, 0.90, "qᵢ = Cᵢ,ₓ", ha="center", fontweight="semibold")

    ax = axs[2]
    panel(ax, "c", "Absolute width")
    ws = [0.22, 0.34, 0.16]
    for f, w, y in zip((1, 2, 3), ws, (0.74, 0.50, 0.27)):
        draw_interval(ax, 0.5, w, y, f, height=0.115)
        ax.annotate(f"w{f}", (0.5+w/2, y-0.09), (0.5-w/2, y-0.09),
                    arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9), ha="center", va="top", fontsize=8)
    ax.text(0.50, 0.92, "wᵢ = c Aᵢ", ha="center", fontweight="semibold")
    ax.text(0.50, 0.07, "one shared scale c", ha="center", color=MID)

    ax = axs[3]
    panel(ax, "d", "Layout variables")
    y0 = 0.55
    layout = [(1, 0.18, 0.22, 0.20, 0.20), (2, 0.48, 0.52, 0.30, 0.56), (3, 0.82, 0.78, 0.16, 0.77)]
    ax.annotate("world-x", (0.95, 0.29), (0.05, 0.29), arrowprops=dict(arrowstyle="->", color=INK))
    for f, q, z, w, x in layout:
        draw_interval(ax, z, w, y0, f, height=0.14, anchor=x, reference=q)
        ax.text(q, 0.76, f"q{f}", ha="center", color=MID, fontsize=8)
        ax.text(x, 0.42, f"x{f}", ha="center", color=INK, fontsize=8)
        ax.text(z, 0.65, f"z{f}", ha="center", color="white", fontsize=8, fontweight="bold")
    ax.plot([0.48, 0.56], [0.80, 0.80], color=RED, lw=1.1)
    ax.plot([0.48, 0.48], [0.78, 0.82], color=RED, lw=1.1)
    ax.plot([0.56, 0.56], [0.78, 0.82], color=RED, lw=1.1)
    ax.text(0.52, 0.85, "|xᵢ−qᵢ|", ha="center", color=RED, fontsize=8)
    ax.plot([0.52, 0.56], [0.37, 0.37], color=INK, lw=1.0)
    ax.plot([0.52, 0.52], [0.35, 0.39], color=INK, lw=1.0)
    ax.plot([0.56, 0.56], [0.35, 0.39], color=INK, lw=1.0)
    ax.text(0.54, 0.31, "|xᵢ−zᵢ|", ha="center", va="top", fontsize=8)

    ax = axs[4]
    panel(ax, "e", "Joint constraints")
    ax.text(0.10, 0.86, "✓  legal leaf order", color=GREEN, fontweight="semibold")
    ax.text(0.10, 0.72, "✓  non-overlap", color=GREEN, fontweight="semibold")
    ax.text(0.10, 0.58, "✓  minimum gap  g", color=GREEN, fontweight="semibold")
    ax.text(0.10, 0.44, "✓  canvas bounds", color=GREEN, fontweight="semibold")
    ax.text(0.10, 0.28, "|xᵢ−zᵢ| ≤ ρ wᵢ / 2", color=INK, fontweight="semibold")
    ax.text(0.50, 0.09, "hierarchy and intervals\nconstrain the reference fit",
            ha="center", color=MID, fontsize=8.5)

    ax = axs[5]
    panel(ax, "f", "Fixed-world rasterization")
    ax.text(0.50, 0.89, "continuous intervals", ha="center", color=MID)
    for f, z, w in [(1, 0.24, 0.22), (2, 0.56, 0.34), (3, 0.82, 0.16)]:
        draw_interval(ax, z, w, 0.73, f, height=0.11)
    ax.annotate("same world → pixel map", (0.50, 0.48), (0.50, 0.62),
                arrowprops=dict(arrowstyle="-|>", color=INK), ha="center", va="center", fontsize=8)
    n = 30
    for k in range(n):
        u = (k + 0.5) / n
        if u < 0.35:
            c = FEATURE[1]
        elif u < 0.73:
            c = FEATURE[2]
        else:
            c = FEATURE[3]
        ax.add_patch(Rectangle((0.08 + k*0.028, 0.28), 0.028, 0.15, fc=c, ec="white", lw=0.25))
    ax.text(0.50, 0.18, "final RA-MTM slice", ha="center", color=INK, fontweight="semibold")
    ax.text(0.50, 0.07, "no per-frame normalization", ha="center", color=MID, fontsize=8)

    for a, b in zip(axs[:-1], axs[1:]):
        arrow_between(fig, a, b, y=0.50)
    fig.suptitle("RA-MTM jointly represents reference position, absolute measure, and hierarchy legality",
                 y=1.04, fontsize=13, fontweight="semibold", color=INK)
    fig.text(0.5, -0.01, "Schematic only — the displayed coordinates and widths are illustrative.",
             ha="center", fontsize=8, color=MID)
    save(fig, "theory_3_ramtm_variables_constraints")


def budget_panel(ax, letter, title, tau_label, windows, layout=None, feasible=False, delta=False):
    clean(ax)
    panel(ax, letter, title)
    qs = [0.20, 0.50, 0.80]
    y = 0.55
    ax.annotate("world-x", (0.94, 0.27), (0.06, 0.27), arrowprops=dict(arrowstyle="->", color=INK))
    for f, q in zip((1, 2, 3), qs):
        ax.plot([q, q], [0.25, 0.86], ls=(0, (3, 2)), color="#8A9098", lw=1.0)
        ax.text(q, 0.89, f"q{f}", ha="center", color=MID)
        if windows > 0:
            ax.add_patch(Rectangle((q-windows, 0.34), 2*windows, 0.42,
                                   fc="#CED4DA", ec="none", alpha=0.32))
            ax.plot([q-windows, q-windows], [0.34, 0.76], color="#A2A9B1", lw=0.8)
            ax.plot([q+windows, q+windows], [0.34, 0.76], color="#A2A9B1", lw=0.8)
    if layout is None:
        for f, q, w in zip((1, 2, 3), qs, (0.23, 0.22, 0.24)):
            draw_interval(ax, q, w, y, f, height=0.13, anchor=q)
        ax.text(0.50, 0.55, "×", ha="center", va="center", color=RED,
                fontsize=27, fontweight="bold", zorder=9)
    else:
        for f, z, w in zip((1, 3, 2), layout, (0.22, 0.20, 0.23)):
            draw_interval(ax, z, w, y, f, height=0.13, anchor=z)
        ax.text(0.50, 0.70, "legal order: F1 – F3 – F2", ha="center", color=GREEN,
                fontsize=8.5, fontweight="semibold")
    ax.text(0.50, 0.16, tau_label, ha="center", fontweight="semibold",
            color=GREEN if feasible else RED)
    if feasible:
        ax.text(0.50, 0.06, "feasible", ha="center", color=GREEN, fontweight="bold")
    else:
        ax.text(0.50, 0.06, "infeasible", ha="center", color=RED, fontweight="bold")
    if delta:
        ax.text(0.50, 0.81, "larger feasible region", ha="center", color=MID, fontsize=8)


def theory_4():
    fig, axs = plt.subplots(1, 4, figsize=(15.2, 4.25), gridspec_kw={"wspace": 0.28})
    budget_panel(axs[0], "a", "Exact reference", "τ = 0", 0.0, None, False)
    budget_panel(axs[1], "b", "Insufficient tolerance", "0 < τ < τ*", 0.12, None, False)
    budget_panel(axs[2], "c", "First feasible layout", "τ = τ*", 0.27,
                 [0.20, 0.55, 0.77], True)
    budget_panel(axs[3], "d", "Optimization budget", "τ* + Δ", 0.32,
                 [0.23, 0.54, 0.79], True, True)
    axs[2].text(0.50, 0.95, "minimum feasible deviation τ*", ha="center",
                color=GREEN, fontweight="semibold", fontsize=8.5)
    axs[3].text(0.50, 0.95, "select the best feasible layout", ha="center",
                color=INK, fontweight="semibold", fontsize=8.5)
    axs[3].text(0.50, -0.02,
                "geometry preservation\n+ motion residual\n+ anchor–band consistency",
                ha="center", va="top", color=INK, fontsize=8.3,
                bbox=dict(boxstyle="round,pad=0.30", fc=PALE, ec=LIGHT))
    for a, b in zip(axs[:-1], axs[1:]):
        arrow_between(fig, a, b, y=0.50)
    fig.suptitle("τ* and the RA-MTM error budget", y=1.03,
                 fontsize=13, fontweight="semibold", color=INK)
    fig.text(0.5, -0.055,
             "τ* = the minimum unavoidable reference-position distortion required by hierarchy and interval constraints.",
             ha="center", fontsize=9.2, color=INK, fontweight="semibold")
    fig.text(0.5, -0.105, "Schematic only — τ, τ*, and Δ are not experimental values.",
             ha="center", fontsize=8, color=MID)
    save(fig, "theory_4_tau_error_budget")


def contact_sheet():
    stems = [
        "theory_1_merge_tree_map_pipeline",
        "theory_2_missing_information",
        "theory_3_ramtm_variables_constraints",
        "theory_4_tau_error_budget",
    ]
    titles = ["Theory-1 · Basic pipeline", "Theory-2 · Motivation",
              "Theory-3 · Variables and constraints", "Theory-4 · τ* and error budget"]
    fig, axs = plt.subplots(2, 2, figsize=(16, 9.3), facecolor="#ECEFF2")
    for ax, stem, title in zip(axs.flat, stems, titles):
        img = plt.imread(OUT / f"{stem}.png")
        ax.imshow(img)
        ax.set_title(title, loc="left", fontsize=11, pad=8, fontweight="semibold", color=INK)
        ax.axis("off")
    fig.suptitle("RA-MTM theoretical figures — contact sheet", fontsize=15,
                 fontweight="semibold", color=INK, y=0.985)
    fig.tight_layout(rect=(0.015, 0.015, 0.985, 0.96), h_pad=1.8, w_pad=1.4)
    fig.savefig(OUT / "overview_contact_sheet.png", dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    theory_1()
    theory_2()
    theory_3()
    theory_4()
    contact_sheet()
    print(f"Wrote theory figures to {OUT}")


if __name__ == "__main__":
    main()
