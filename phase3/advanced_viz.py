"""
PHASE 3 — Advanced Visualizations
===================================
Sphere-based analysis: for each consequent, show CLS at expanding sphere sizes.
Network graph: connect consequents that co-occur in the same worlds.
3D surface: consequent × distance × CLS.
"""

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

matplotlib.use("Agg")

PHASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = PHASE_DIR / "results"
PLOTS_DIR = PHASE_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_results():
    with open(RESULTS_DIR / "results.json", "r") as f:
        return json.load(f)


# ============================================================
# 1. SPHERE EXPANSION PLOT
# For each consequent, plot CLS as you expand the sphere outward
# This is the Lewis plot — closest worlds on the left, all worlds on the right
# ============================================================

def plot_sphere_expansion(data):
    all_results = data["all_results"]
    consequents = data["summary"]

    # Sort consequents by overall CLS for consistent ordering
    consequents = sorted(consequents, key=lambda x: x["cls_overall"], reverse=True)

    # Only plot consequents that actually vary (not stuck at 0 or 1)
    interesting = [c for c in consequents if 0.05 < c["cls_overall"] < 0.95]
    saturated_high = [c for c in consequents if c["cls_overall"] >= 0.95]
    saturated_low = [c for c in consequents if c["cls_overall"] <= 0.05]

    colors = ["#E63946", "#457B9D", "#2A9D8F", "#E9C46A", "#F4A261",
              "#6C4AB6", "#1D3557", "#264653", "#D4A373", "#9B2226"]

    fig, ax = plt.subplots(figsize=(16, 9))

    for i, c in enumerate(interesting):
        cid = c["id"]
        responses = all_results[cid]["responses"]
        valid = [r for r in responses if r["answer"] in (0, 1)]
        valid.sort(key=lambda r: r["distance"])

        # Compute cumulative CLS as sphere expands
        distances = []
        cls_values = []
        cumsum = 0
        for j, r in enumerate(valid):
            cumsum += r["answer"]
            distances.append(r["distance"])
            cls_values.append(cumsum / (j + 1))

        color = colors[i % len(colors)]
        ax.plot(distances, cls_values, linewidth=2.5, color=color,
                label=f"{c['id']}: {c['name']} ({c['cls_overall']:.2f})", alpha=0.85)

    ax.axhline(y=0.5, color="#999", linestyle=":", alpha=0.5)
    ax.set_xlabel("Sphere radius r (distance from base world)", fontsize=12)
    ax.set_ylabel("CLS within sphere S(r)", fontsize=12)
    ax.set_title("Phase 3 — CLS as Sphere Expands (Lewis Plot)\n"
                 "Closest worlds on the left determine the counterfactual",
                 fontsize=14, fontweight="bold")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=9)
    ax.grid(True, alpha=0.3)

    # Top axis
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ticks = [0, 0.25, 0.5, 0.75, 1.0]
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([f"{int(30 + t * 240)} ppl" for t in ticks])
    ax2.set_xlabel("Population at that distance", fontsize=10)

    # Annotate saturated consequents
    if saturated_high or saturated_low:
        note = "Always YES: " + ", ".join(f"{c['id']}" for c in saturated_high)
        note += "\nAlways NO: " + ", ".join(f"{c['id']}" for c in saturated_low)
        ax.text(0.02, 0.02, note, transform=ax.transAxes, fontsize=8,
                color="#666", verticalalignment="bottom",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))

    plt.tight_layout()
    out = PLOTS_DIR / "sphere_expansion.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Saved: {out}")
    plt.close()


# ============================================================
# 2. CO-OCCURRENCE NETWORK
# Which consequents tend to be YES together in the same world?
# Edge thickness = correlation strength
# ============================================================

def plot_cooccurrence_network(data):
    all_results = data["all_results"]
    consequents = data["summary"]
    cids = [c["id"] for c in sorted(consequents, key=lambda x: x["cls_overall"], reverse=True)]
    names = {c["id"]: c["name"] for c in consequents}

    n = len(cids)
    n_worlds = len(all_results[cids[0]]["responses"])

    # Build answer matrix: worlds × consequents
    matrix = np.zeros((n_worlds, n))
    for j, cid in enumerate(cids):
        for w, r in enumerate(all_results[cid]["responses"]):
            matrix[w, j] = r["answer"] if r["answer"] in (0, 1) else np.nan

    # Compute correlation matrix
    # Only use rows where all values are valid
    valid_mask = ~np.isnan(matrix).any(axis=1)
    clean = matrix[valid_mask]

    if clean.shape[0] < 10:
        print("Not enough valid data for co-occurrence network")
        return

    corr = np.corrcoef(clean.T)

    # Plot as a circular network
    fig, ax = plt.subplots(figsize=(14, 14))

    # Position nodes in a circle
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    radius = 4
    positions = {cids[i]: (radius * np.cos(a), radius * np.sin(a)) for i, a in enumerate(angles)}

    # Draw edges (only for |corr| > 0.15)
    for i in range(n):
        for j in range(i + 1, n):
            c = corr[i, j]
            if abs(c) > 0.15 and not np.isnan(c):
                x = [positions[cids[i]][0], positions[cids[j]][0]]
                y = [positions[cids[i]][1], positions[cids[j]][1]]
                color = "#2D6A4F" if c > 0 else "#E63946"
                alpha = min(abs(c) * 1.5, 0.9)
                width = abs(c) * 4
                ax.plot(x, y, color=color, alpha=alpha, linewidth=width, zorder=1)

    # Draw nodes
    for cid in cids:
        x, y = positions[cid]
        cls_val = next(c["cls_overall"] for c in consequents if c["id"] == cid)

        # Color by CLS
        if cls_val >= 0.7:
            node_color = "#E63946"
        elif cls_val >= 0.3:
            node_color = "#E9C46A"
        else:
            node_color = "#2D6A4F"

        circle = plt.Circle((x, y), 0.4, color=node_color, zorder=3, ec="white", linewidth=2)
        ax.add_patch(circle)

        # Label
        label = f"{cid}\n{names[cid]}\n({cls_val:.2f})"
        label_x = x * 1.35
        label_y = y * 1.35
        ha = "left" if x > 0 else "right" if x < 0 else "center"
        ax.annotate(label, (x, y), (label_x, label_y),
                    fontsize=8, ha=ha, va="center", fontweight="bold",
                    arrowprops=dict(arrowstyle="-", color="#999", lw=0.5))

    ax.set_xlim(-7, 7)
    ax.set_ylim(-7, 7)
    ax.set_aspect("equal")
    ax.set_title("Phase 3 — Co-occurrence Network\n"
                 "Green edges = positive correlation (happen together)\n"
                 "Red edges = negative correlation (one happens, other doesn't)",
                 fontsize=13, fontweight="bold")
    ax.axis("off")

    # Legend
    ax.plot([], [], color="#2D6A4F", linewidth=3, label="Positive correlation")
    ax.plot([], [], color="#E63946", linewidth=3, label="Negative correlation")
    ax.legend(loc="lower right", fontsize=10)

    plt.tight_layout()
    out = PLOTS_DIR / "network.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()


# ============================================================
# 3. 3D SURFACE PLOT
# X = population distance, Y = consequent, Z = CLS
# ============================================================

def plot_3d_surface(data):
    all_results = data["all_results"]
    consequents = sorted(data["summary"], key=lambda x: x["cls_overall"], reverse=True)
    cids = [c["id"] for c in consequents]
    cnames = [c["name"] for c in consequents]

    n_bins = 12
    n_cons = len(cids)

    # Build the surface data
    Z = np.zeros((n_cons, n_bins))
    X_labels = []

    for ci, cid in enumerate(cids):
        responses = all_results[cid]["responses"]
        valid = [r for r in responses if r["answer"] in (0, 1)]
        valid.sort(key=lambda r: r["distance"])

        bin_size = max(1, len(valid) // n_bins)
        for bi in range(n_bins):
            chunk = valid[bi * bin_size: (bi + 1) * bin_size]
            if chunk:
                Z[ci, bi] = sum(r["answer"] for r in chunk) / len(chunk)
                if ci == 0:
                    mid_pop = int(sum(r["population"] for r in chunk) / len(chunk))
                    X_labels.append(str(mid_pop))

    # Pad X_labels if needed
    while len(X_labels) < n_bins:
        X_labels.append("")

    X, Y = np.meshgrid(range(n_bins), range(n_cons))

    fig = plt.figure(figsize=(18, 12))
    ax = fig.add_subplot(111, projection='3d')

    # Plot surface
    surf = ax.plot_surface(X, Y, Z, cmap="RdYlGn_r", alpha=0.85,
                           edgecolor="white", linewidth=0.3)

    ax.set_xlabel("\nPopulation →", fontsize=11, labelpad=15)
    ax.set_ylabel("\nConsequent", fontsize=11, labelpad=15)
    ax.set_zlabel("\nCLS", fontsize=11, labelpad=10)
    ax.set_title("Phase 3 — 3D Counterfactual Landscape\n"
                 "Height = likelihood of each outcome at each population level",
                 fontsize=14, fontweight="bold", pad=20)

    ax.set_xticks(range(n_bins))
    ax.set_xticklabels(X_labels, fontsize=7, rotation=45)
    ax.set_yticks(range(n_cons))
    ax.set_yticklabels([f"{cid}" for cid in cids], fontsize=7)
    ax.set_zlim(0, 1)

    ax.view_init(elev=25, azim=135)

    fig.colorbar(surf, ax=ax, shrink=0.5, label="CLS")

    plt.tight_layout()
    out = PLOTS_DIR / "3d_surface.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()


# ============================================================
# 4. CLOSEST WORLDS DETAIL
# For the 10 closest worlds, show exactly which consequents are YES/NO
# This is Lewis's inner sphere — what actually determines the counterfactual
# ============================================================

def plot_closest_worlds_detail(data):
    all_results = data["all_results"]
    consequents = sorted(data["summary"], key=lambda x: x["cls_inner"], reverse=True)
    cids = [c["id"] for c in consequents]
    cnames = [c["name"] for c in consequents]

    # Get the 10 closest worlds
    sample_responses = all_results[cids[0]]["responses"]
    sorted_worlds = sorted(sample_responses, key=lambda r: r["distance"])[:10]
    world_ids = [w["world_id"] for w in sorted_worlds]
    world_pops = [w["population"] for w in sorted_worlds]

    n_worlds = len(world_ids)
    n_cons = len(cids)

    # Build matrix
    matrix = np.zeros((n_cons, n_worlds))
    for ci, cid in enumerate(cids):
        responses = {r["world_id"]: r["answer"] for r in all_results[cid]["responses"]}
        for wi, wid in enumerate(world_ids):
            ans = responses.get(wid, -1)
            matrix[ci, wi] = ans if ans in (0, 1) else np.nan

    fig, ax = plt.subplots(figsize=(14, 10))

    # Custom colormap: green=NO, red=YES, grey=unknown
    cmap = matplotlib.colors.ListedColormap(["#2D6A4F", "#E63946"])
    im = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(range(n_worlds))
    ax.set_xticklabels([f"{wid}\npop={p}" for wid, p in zip(world_ids, world_pops)],
                       fontsize=9, rotation=45, ha="right")
    ax.set_yticks(range(n_cons))
    ax.set_yticklabels([f"{cid}: {name}" for cid, name in zip(cids, cnames)], fontsize=9)

    ax.set_xlabel("Closest worlds (inner sphere)", fontsize=12)
    ax.set_title("Phase 3 — Lewis's Inner Sphere Detail\n"
                 "These 10 closest worlds determine the counterfactual verdict\n"
                 "Red = YES, Green = NO",
                 fontsize=13, fontweight="bold")

    # Add YES/NO text
    for ci in range(n_cons):
        for wi in range(n_worlds):
            val = matrix[ci, wi]
            if not np.isnan(val):
                text = "Y" if val == 1 else "N"
                color = "white"
                ax.text(wi, ci, text, ha="center", va="center", fontsize=10,
                        fontweight="bold", color=color)

    # Add CLS column on the right
    for ci, c in enumerate(consequents):
        ax.text(n_worlds + 0.3, ci, f"CLS={c['cls_inner']:.2f}",
                ha="left", va="center", fontsize=9, fontweight="bold",
                color="#1D3557")

    plt.tight_layout()
    out = PLOTS_DIR / "inner_sphere_detail.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()


# ============================================================
# 5. THRESHOLD SWEEP
# For each consequent, at what threshold T does it transition
# from "would" to "might" to "would not"?
# ============================================================

def plot_threshold_sweep(data):
    consequents = sorted(data["summary"], key=lambda x: x["cls_inner"], reverse=True)

    # Filter to interesting ones
    interesting = [c for c in consequents if 0.05 < c["cls_inner"] < 0.95]

    if not interesting:
        interesting = consequents[:8]

    fig, ax = plt.subplots(figsize=(14, 8))

    thresholds = np.arange(0, 1.01, 0.05)

    for c in interesting:
        cls_inner = c["cls_inner"]
        # At each threshold, is this consequent "would" (above T) or not?
        above = [1 if cls_inner >= t else 0 for t in thresholds]
        ax.plot(thresholds, [cls_inner] * len(thresholds),
                linewidth=0, marker="", label=f"{c['id']}: {c['name']}")

    # Simpler: just show where each consequent sits as a horizontal line
    y_positions = range(len(interesting))
    cls_values = [c["cls_inner"] for c in interesting]
    names = [f"{c['id']}: {c['name']}" for c in interesting]

    ax.barh(y_positions, cls_values, color=["#2D6A4F" if v < 0.3 else "#E9C46A" if v < 0.7 else "#E63946" for v in cls_values],
            edgecolor="white", linewidth=1, height=0.6)

    # Threshold lines
    ax.axvline(x=0.7, color="#E63946", linestyle="--", alpha=0.6, linewidth=2, label='"Would" threshold')
    ax.axvline(x=0.3, color="#E9C46A", linestyle="--", alpha=0.6, linewidth=2, label='"Might" threshold')

    ax.set_yticks(y_positions)
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("CLS (inner sphere)", fontsize=12)
    ax.set_title("Phase 3 — Threshold Analysis (Inner Sphere)\n"
                 "Where does each consequent fall on the would/might/would-not spectrum?",
                 fontsize=13, fontweight="bold")
    ax.set_xlim(0, 1.05)
    ax.invert_yaxis()
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.2, axis="x")

    # Add value labels
    for yi, val in zip(y_positions, cls_values):
        ax.text(val + 0.02, yi, f"{val:.2f}", va="center", fontsize=10, fontweight="bold")

    # Add zone labels
    ax.text(0.15, -0.8, "WOULD NOT", ha="center", fontsize=11, color="#2D6A4F", fontweight="bold")
    ax.text(0.5, -0.8, "MIGHT", ha="center", fontsize=11, color="#E9C46A", fontweight="bold")
    ax.text(0.85, -0.8, "WOULD", ha="center", fontsize=11, color="#E63946", fontweight="bold")

    plt.tight_layout()
    out = PLOTS_DIR / "threshold_analysis.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()


if __name__ == "__main__":
    data = load_results()
    plot_sphere_expansion(data)
    plot_cooccurrence_network(data)
    plot_3d_surface(data)
    plot_closest_worlds_detail(data)
    plot_threshold_sweep(data)
    print("\nAll advanced plots saved.")
