"""
PHASE 3 — Visualization
========================
Reads phase3_results.json and produces the counterfactual likelihood landscape.
"""

import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
matplotlib.use('Agg')


def load_results():
    with open("phase3_results.json", "r") as f:
        return json.load(f)


def compute_cls_curve(responses, n_bins=12):
    """Compute CLS in distance bins."""
    valid = [r for r in responses if r["answer"] in (0, 1)]
    valid.sort(key=lambda r: r["distance"])

    bin_size = max(1, len(valid) // n_bins)
    midpoints = []
    cls_values = []
    pops = []

    for i in range(0, len(valid), bin_size):
        chunk = valid[i:i + bin_size]
        if not chunk:
            continue
        mid = sum(r["distance"] for r in chunk) / len(chunk)
        pop = sum(r["population"] for r in chunk) / len(chunk)
        cls = sum(r["answer"] for r in chunk) / len(chunk)
        midpoints.append(mid)
        cls_values.append(cls)
        pops.append(pop)

    return midpoints, cls_values, pops


def plot_all_curves(data):
    """Plot all consequent CLS curves on one graph."""
    all_results = data["all_results"]
    summary = data["summary"]

    colors = [
        "#E63946", "#457B9D", "#2A9D8F", "#E9C46A", "#F4A261",
        "#6C4AB6", "#1D3557", "#264653", "#A8DADC", "#D4A373",
        "#2D6A4F", "#9B2226", "#BB3E03", "#005F73", "#CA6702",
    ]

    fig, ax = plt.subplots(figsize=(16, 9))

    for i, s in enumerate(summary):
        cid = s["id"]
        responses = all_results[cid]["responses"]
        midpoints, cls_values, _ = compute_cls_curve(responses)
        color = colors[i % len(colors)]
        ax.plot(midpoints, cls_values, linewidth=2, color=color,
                marker="o", markersize=4, label=f"{cid}: {s['name']} ({s['cls_overall']:.2f})")

    ax.axhline(y=0.5, color="#999", linestyle=":", alpha=0.5, label="50% threshold")
    ax.set_xlabel("Distance from base world (normalised)", fontsize=12)
    ax.set_ylabel("CLS — proportion saying YES", fontsize=12)
    ax.set_title("Phase 3 — Counterfactual Likelihood Landscape\n"
                 "All consequents across the similarity gradient",
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
    ax2.set_xlabel("Population", fontsize=10)

    plt.tight_layout()
    plt.savefig("phase3_all_curves.png", dpi=150, bbox_inches="tight")
    print("Saved: phase3_all_curves.png")
    plt.close()


def plot_ranking_bar(data):
    """Bar chart ranking all consequents by overall CLS."""
    summary = sorted(data["summary"], key=lambda x: x["cls_overall"], reverse=True)

    names = [f"{s['id']}: {s['name']}" for s in summary]
    values = [s["cls_overall"] for s in summary]

    colors = []
    for v in values:
        if v >= 0.7:
            colors.append("#2D6A4F")
        elif v >= 0.3:
            colors.append("#E9C46A")
        else:
            colors.append("#E63946")

    fig, ax = plt.subplots(figsize=(14, 8))
    bars = ax.barh(range(len(names)), values, color=colors, edgecolor="white", linewidth=1)

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=10)
    ax.set_xlabel("CLS (proportion of worlds saying YES)", fontsize=12)
    ax.set_title("Phase 3 — Ranked Counterfactual Consequents\n"
                 "If the rice field is destroyed, what happens?",
                 fontsize=14, fontweight="bold")
    ax.set_xlim(0, 1.05)
    ax.invert_yaxis()

    ax.axvline(x=0.7, color="#2D6A4F", linestyle="--", alpha=0.5, label="'Would' threshold (0.7)")
    ax.axvline(x=0.3, color="#E63946", linestyle="--", alpha=0.5, label="'Might' threshold (0.3)")

    for bar, val in zip(bars, values):
        ax.text(val + 0.01, bar.get_y() + bar.get_height()/2, f"{val:.2f}",
                va="center", fontsize=10, fontweight="bold")

    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.2, axis="x")

    plt.tight_layout()
    plt.savefig("phase3_ranking.png", dpi=150)
    print("Saved: phase3_ranking.png")
    plt.close()


def plot_inner_vs_outer(data):
    """Compare inner sphere CLS vs outer sphere CLS for each consequent."""
    summary = sorted(data["summary"], key=lambda x: x["cls_inner"], reverse=True)

    names = [f"{s['id']}: {s['name']}" for s in summary]
    inner = [s["cls_inner"] for s in summary]
    outer = [s["cls_outer"] for s in summary]

    x = np.arange(len(names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(16, 8))
    bars1 = ax.bar(x - width/2, inner, width, label="Inner sphere (closest 10)", color="#1D3557", edgecolor="white")
    bars2 = ax.bar(x + width/2, outer, width, label="Outer sphere (farthest 10)", color="#E63946", alpha=0.7, edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel("CLS", fontsize=12)
    ax.set_title("Phase 3 — Inner vs Outer Sphere\n"
                 "Lewis: the inner sphere (blue) determines the counterfactual",
                 fontsize=13, fontweight="bold")
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.2, axis="y")

    plt.tight_layout()
    plt.savefig("phase3_inner_vs_outer.png", dpi=150)
    print("Saved: phase3_inner_vs_outer.png")
    plt.close()


def plot_gradient_heatmap(data):
    """Heatmap showing CLS at each distance for each consequent."""
    all_results = data["all_results"]
    summary = sorted(data["summary"], key=lambda x: x["cls_overall"], reverse=True)

    n_bins = 10
    matrix = []
    labels = []

    for s in summary:
        cid = s["id"]
        responses = all_results[cid]["responses"]
        _, cls_values, _ = compute_cls_curve(responses, n_bins=n_bins)
        matrix.append(cls_values[:n_bins])
        labels.append(f"{s['id']}: {s['name']}")

    # Pad if needed
    max_len = max(len(row) for row in matrix)
    matrix = [row + [0] * (max_len - len(row)) for row in matrix]

    fig, ax = plt.subplots(figsize=(14, 8))
    im = ax.imshow(matrix, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=1)

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)

    bin_labels = [f"{int(30 + (i/n_bins) * 240)}–{int(30 + ((i+1)/n_bins) * 240)}" for i in range(max_len)]
    ax.set_xticks(range(max_len))
    ax.set_xticklabels(bin_labels, rotation=45, ha="right", fontsize=8)
    ax.set_xlabel("Population range", fontsize=11)

    ax.set_title("Phase 3 — Counterfactual Heatmap\n"
                 "Green = low CLS (unlikely), Red = high CLS (likely)",
                 fontsize=13, fontweight="bold")

    # Add text annotations
    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            val = matrix[i][j]
            color = "white" if val > 0.6 or val < 0.2 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8, color=color)

    plt.colorbar(im, ax=ax, label="CLS", shrink=0.8)
    plt.tight_layout()
    plt.savefig("phase3_heatmap.png", dpi=150)
    print("Saved: phase3_heatmap.png")
    plt.close()


def print_summary(data):
    summary = data["summary"]
    print("\n" + "=" * 70)
    print("PHASE 3 — COUNTERFACTUAL LIKELIHOOD RANKING")
    print("=" * 70)

    sorted_s = sorted(summary, key=lambda x: x["cls_overall"], reverse=True)
    print(f"\n{'Rank':<5} {'Consequent':<28} {'CLS':<8} {'Inner':<8} {'Outer':<8} {'Gradient':<8}")
    print("-" * 70)
    for rank, s in enumerate(sorted_s, 1):
        print(f"{rank:<5} {s['name']:<28} {s['cls_overall']:.3f}  {s['cls_inner']:.3f}   {s['cls_outer']:.3f}   {s['gradient']:+.3f}")

    print(f"\n{'=' * 70}")
    print("LEWIS'S VERDICT (inner sphere)")
    print(f"{'=' * 70}")
    inner_sorted = sorted(summary, key=lambda x: x["cls_inner"], reverse=True)
    for s in inner_sorted:
        if s["cls_inner"] >= 0.7:
            v = "WOULD"
        elif s["cls_inner"] > 0.0:
            v = "MIGHT"
        else:
            v = "WOULD NOT"
        print(f"  {v:<10} {s['name']:<28} (CLS inner = {s['cls_inner']:.2f})")


if __name__ == "__main__":
    data = load_results()
    print_summary(data)
    plot_all_curves(data)
    plot_ranking_bar(data)
    plot_inner_vs_outer(data)
    plot_gradient_heatmap(data)
    print("\nAll plots saved.")
