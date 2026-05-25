"""
PHASE 1 — Visualization (Conflict Version)
============================================
Reads phase1_results.json and produces plots.
"""

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")

PHASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = PHASE_DIR / "results"
PLOTS_DIR = PHASE_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_results():
    with open(RESULTS_DIR / "results.json", "r") as f:
        return json.load(f)


def plot_responses(results):
    """Plot each world's CONFLICT/NO CONFLICT answer against population."""
    valid = [r for r in results if r["answer"] in (0, 1)]
    valid.sort(key=lambda r: r["population"])

    pops = [r["population"] for r in valid]
    answers = [r["answer"] for r in valid]

    fig, ax = plt.subplots(figsize=(14, 5))

    colors = ["#2D6A4F" if a == 0 else "#E63946" for a in answers]
    ax.scatter(pops, answers, c=colors, s=120, alpha=0.8, zorder=3,
              edgecolors="white", linewidth=1)

    ax.set_xlabel("Population", fontsize=12)
    ax.set_ylabel("Outcome", fontsize=12)
    ax.set_title("Phase 1 — Conflict Outcome by Population\n"
                 "Green = No Conflict, Red = Conflict",
                 fontsize=14, fontweight="bold")
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["NO CONFLICT", "CONFLICT"])
    ax.set_xlim(25, 435)
    ax.set_ylim(-0.2, 1.2)
    ax.grid(True, alpha=0.3)

    # Mark the actual world
    ax.axvline(x=30, color="#1D3557", linestyle="--", alpha=0.5, label="Actual world (pop=30)")
    ax.legend(fontsize=10)

    plt.tight_layout()
    out = PLOTS_DIR / "conflict_scatter.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()


def plot_cls_curve(results):
    """Plot cumulative CLS as sphere expands from actual world outward."""
    valid = [r for r in results if r["answer"] in (0, 1)]
    valid.sort(key=lambda r: r["distance"])

    distances = []
    populations = []
    cls_values = []
    cumulative_yes = 0
    cumulative_total = 0

    for r in valid:
        cumulative_total += 1
        cumulative_yes += r["answer"]
        distances.append(r["distance"])
        populations.append(r["population"])
        cls_values.append(cumulative_yes / cumulative_total)

    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(distances, cls_values, color="#1D3557", linewidth=2.5, marker="o",
            markersize=6, label="CLS(S(r)) — conflict rate within sphere")
    ax.fill_between(distances, cls_values, alpha=0.1, color="#1D3557")

    # Threshold lines
    ax.axhline(y=0.5, color="#E9C46A", linestyle="--", alpha=0.6, label="50% threshold")

    ax.set_xlabel("Distance from actual world (normalised)", fontsize=12)
    ax.set_ylabel("CLS — proportion saying CONFLICT", fontsize=12)
    ax.set_title("Phase 1 — Conflict Rate vs Sphere Size\n"
                 "Lewis: the counterfactual is determined by the closest worlds (left side)",
                 fontsize=13, fontweight="bold")
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="best", fontsize=10)
    ax.grid(True, alpha=0.3)

    # Top axis: population
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    tick_dists = [0, 0.25, 0.5, 0.75, 1.0]
    tick_labels = [f"{int(30 + d * 400)} ppl" for d in tick_dists]
    ax2.set_xticks(tick_dists)
    ax2.set_xticklabels(tick_labels)
    ax2.set_xlabel("Population at that distance", fontsize=10)

    plt.tight_layout()
    out = PLOTS_DIR / "cls_curve.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()


def plot_bar_chart(results):
    """Simple bar chart showing CONFLICT vs NO CONFLICT at each population."""
    valid = [r for r in results if r["answer"] in (0, 1)]
    valid.sort(key=lambda r: r["population"])

    pops = [r["population"] for r in valid]
    answers = [r["answer"] for r in valid]
    colors = ["#E63946" if a == 1 else "#2D6A4F" for a in answers]

    fig, ax = plt.subplots(figsize=(14, 5))

    bars = ax.bar(range(len(pops)), answers, color=colors, width=0.8,
                  edgecolor="white", linewidth=0.5)

    ax.set_xticks(range(len(pops)))
    ax.set_xticklabels([str(p) for p in pops], rotation=45, fontsize=9)
    ax.set_xlabel("Population", fontsize=12)
    ax.set_ylabel("Conflict (1) / No Conflict (0)", fontsize=12)
    ax.set_title("Phase 1 — Conflict at Each Population Level\n"
                 "Red = Conflict, Green = No Conflict",
                 fontsize=14, fontweight="bold")
    ax.set_ylim(-0.1, 1.3)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["NO CONFLICT", "CONFLICT"])

    # Add population labels on bars
    for i, (p, a) in enumerate(zip(pops, answers)):
        label = "⚔️" if a == 1 else "🕊️"
        ax.text(i, a + 0.05, label, ha="center", fontsize=12)

    plt.tight_layout()
    out = PLOTS_DIR / "conflict_bars.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()


def print_summary(results):
    """Print text summary."""
    valid = [r for r in results if r["answer"] in (0, 1)]
    valid.sort(key=lambda r: r["distance"])

    print("\n" + "=" * 60)
    print("PHASE 1 SUMMARY — Conflict Version")
    print("=" * 60)

    total_conflict = sum(r["answer"] for r in valid)
    total_peace = len(valid) - total_conflict

    print(f"Total: {total_conflict} CONFLICT, {total_peace} NO CONFLICT")
    print(f"Overall conflict rate: {total_conflict/len(valid):.2f}")
    print()

    # Print each world
    for r in valid:
        label = "CONFLICT" if r["answer"] == 1 else "NO CONFLICT"
        print(f"  Pop {r['population']:>3}  dist {r['distance']:.3f}  → {label}")

    # Find the transition zone
    print()
    prev = None
    for r in valid:
        if prev is not None and r["answer"] != prev["answer"]:
            print(f"Transition: {prev['population']} ({['NO CONFLICT','CONFLICT'][prev['answer']]}) "
                  f"→ {r['population']} ({['NO CONFLICT','CONFLICT'][r['answer']]})")
        prev = r

    print("=" * 60)


if __name__ == "__main__":
    results = load_results()
    print_summary(results)
    plot_responses(results)
    plot_cls_curve(results)
    plot_bar_chart(results)
    print("\nAll plots saved.")