"""
C12 Deep Analysis — Someone Dies of Starvation
================================================
The closest worlds say NO. The distant worlds say YES.
This is Lewis's core insight: the counterfactual verdict depends on
which worlds you look at.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


def load_results():
    with open("phase3/results/results.json", "r") as f:
        return json.load(f)


def main():
    data = load_results()
    responses = data["all_results"]["C12"]["responses"]
    valid = [r for r in responses if r["answer"] in (0, 1)]
    valid.sort(key=lambda r: r["distance"])

    distances = [r["distance"] for r in valid]
    populations = [r["population"] for r in valid]
    answers = [r["answer"] for r in valid]

    # --- PLOT 1: Cumulative CLS as sphere expands ---
    fig, ax = plt.subplots(figsize=(16, 7))

    cum_yes = 0
    cum_total = 0
    cum_distances = []
    cum_cls = []
    cum_pops = []

    for r in valid:
        cum_total += 1
        cum_yes += r["answer"]
        cum_distances.append(r["distance"])
        cum_cls.append(cum_yes / cum_total)
        cum_pops.append(r["population"])

    ax.plot(cum_distances, cum_cls, color="#e63946", linewidth=3, label="CLS(S(r)) — starvation rate within sphere")
    ax.fill_between(cum_distances, cum_cls, alpha=0.15, color="#e63946")

    # Mark the inner sphere
    ax.axvline(x=0.125, color="#f4a261", linestyle="--", linewidth=2, alpha=0.8)
    ax.text(0.13, 0.95, "lewis's inner\nsphere", color="#f4a261", fontsize=10,
            fontweight="bold", va="top", transform=ax.get_xaxis_transform())

    # Mark key CLS values
    inner_cls = cum_cls[9] if len(cum_cls) > 9 else cum_cls[-1]
    full_cls = cum_cls[-1]
    ax.annotate(f"inner sphere\nCLS = {inner_cls:.2f}", xy=(0.125, inner_cls),
                xytext=(0.2, inner_cls - 0.15), fontsize=11, fontweight="bold",
                color="#1d3557", arrowprops=dict(arrowstyle="->", color="#1d3557"))
    ax.annotate(f"all worlds\nCLS = {full_cls:.2f}", xy=(1.0, full_cls),
                xytext=(0.85, full_cls + 0.12), fontsize=11, fontweight="bold",
                color="#e63946", arrowprops=dict(arrowstyle="->", color="#e63946"))

    ax.axhline(y=0.5, color="#999", linestyle=":", alpha=0.5)
    ax.axhline(y=0.8, color="#e63946", linestyle=":", alpha=0.3, label="T=0.8 threshold")

    ax.set_xlabel("sphere radius r (distance from base world)", fontsize=12)
    ax.set_ylabel("CLS — proportion saying YES (someone starves)", fontsize=12)
    ax.set_title("C12: someone dies of starvation — CLS as sphere expands\n"
                 "closest worlds say NO, distant worlds say YES — lewis says trust the closest",
                 fontsize=14, fontweight="bold")
    ax.set_xlim(-0.02, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="center right", fontsize=10)
    ax.grid(True, alpha=0.2)

    # Top axis
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ticks = [0, 0.25, 0.5, 0.75, 1.0]
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([f"{int(30 + t * 240)} ppl" for t in ticks])
    ax2.set_xlabel("population at that distance", fontsize=10)

    plt.tight_layout()
    plt.savefig("phase3/plots/c12_sphere_expansion.png", dpi=150)
    print("Saved: c12_sphere_expansion.png")
    plt.close()

    # --- PLOT 2: Individual responses as colored dots ---
    fig, ax = plt.subplots(figsize=(16, 4))

    colors = ["#2a9d8f" if a == 0 else "#e63946" for a in answers]
    ax.scatter(populations, [0.5] * len(populations), c=colors, s=80, alpha=0.85,
              edgecolors="white", linewidth=0.8, zorder=3)

    # Add jitter for overlapping points
    for i, (pop, ans) in enumerate(zip(populations, answers)):
        y = 0.7 if ans == 1 else 0.3
        ax.scatter(pop, y, c=colors[i], s=60, alpha=0.7, edgecolors="white", linewidth=0.5)

    # Inner sphere shading
    ax.axvspan(30, 30 + 0.125 * 240, alpha=0.08, color="#f4a261", label="inner sphere")
    ax.axvline(x=30 + 0.125 * 240, color="#f4a261", linestyle="--", linewidth=1.5, alpha=0.6)

    ax.set_xlabel("population", fontsize=12)
    ax.set_yticks([0.3, 0.7])
    ax.set_yticklabels(["NO\n(no starvation)", "YES\n(starvation)"], fontsize=10)
    ax.set_title("C12: individual world responses — does anyone starve?",
                 fontsize=13, fontweight="bold")
    ax.set_xlim(25, 275)
    ax.set_ylim(0, 1)
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.15, axis="x")

    plt.tight_layout()
    plt.savefig("phase3/plots/c12_individual_responses.png", dpi=150)
    print("Saved: c12_individual_responses.png")
    plt.close()

    # --- PLOT 3: Sliding window showing local YES rate ---
    window = 8
    fig, ax = plt.subplots(figsize=(16, 6))

    midpoints = []
    mid_pops = []
    local_cls = []

    for i in range(len(valid) - window + 1):
        chunk = valid[i:i + window]
        yes_count = sum(r["answer"] for r in chunk)
        cls = yes_count / len(chunk)
        mid_d = (chunk[0]["distance"] + chunk[-1]["distance"]) / 2
        mid_p = (chunk[0]["population"] + chunk[-1]["population"]) / 2
        midpoints.append(mid_d)
        mid_pops.append(mid_p)
        local_cls.append(cls)

    ax.plot(midpoints, local_cls, color="#e63946", linewidth=2.5, label=f"local CLS (window={window})")
    ax.fill_between(midpoints, local_cls, alpha=0.15, color="#e63946")

    ax.axvline(x=0.125, color="#f4a261", linestyle="--", linewidth=2, alpha=0.8, label="inner sphere boundary")
    ax.axhline(y=0.5, color="#999", linestyle=":", alpha=0.5)

    ax.set_xlabel("distance from base world", fontsize=12)
    ax.set_ylabel("local starvation rate (in sliding window)", fontsize=12)
    ax.set_title("C12: where does starvation become likely?\n"
                 "the flip point shows where the counterfactual changes",
                 fontsize=14, fontweight="bold")
    ax.set_xlim(-0.02, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc="best", fontsize=10)
    ax.grid(True, alpha=0.2)

    # Top axis
    ax2 = ax.twiny()
    ax2.set_xlim(ax.get_xlim())
    ax2.set_xticks(ticks)
    ax2.set_xticklabels([f"{int(30 + t * 240)} ppl" for t in ticks])
    ax2.set_xlabel("population", fontsize=10)

    plt.tight_layout()
    plt.savefig("phase3/plots/c12_sliding_window.png", dpi=150)
    print("Saved: c12_sliding_window.png")
    plt.close()

    # --- PLOT 4: The Lewis verdict diagram ---
    fig, ax = plt.subplots(figsize=(12, 6))

    # Three bars: inner sphere, mid sphere, outer sphere
    inner = valid[:10]
    mid = valid[20:40]
    outer = valid[-10:]

    inner_cls_val = sum(r["answer"] for r in inner) / len(inner)
    mid_cls_val = sum(r["answer"] for r in mid) / len(mid)
    outer_cls_val = sum(r["answer"] for r in outer) / len(outer)
    all_cls_val = sum(r["answer"] for r in valid) / len(valid)

    labels = [
        f"inner sphere\npop 30–57\n(closest 10 worlds)",
        f"middle sphere\npop 90–147\n(worlds 20–40)",
        f"outer sphere\npop 240–270\n(farthest 10 worlds)",
        f"all worlds\npop 30–270\n(all 81 worlds)",
    ]
    values = [inner_cls_val, mid_cls_val, outer_cls_val, all_cls_val]
    colors = ["#1d3557", "#457b9d", "#e63946", "#888"]

    bars = ax.bar(range(4), values, color=colors, width=0.6, edgecolor="white", linewidth=2)

    ax.axhline(y=0.8, color="#f4a261", linestyle="--", linewidth=2, alpha=0.6, label="T=0.8")
    ax.axhline(y=0.5, color="#999", linestyle=":", alpha=0.5, label="T=0.5")

    for bar, val in zip(bars, values):
        verdict = "WOULD" if val >= 0.8 else "MIGHT" if val > 0 else "WOULD NOT"
        color = "#e63946" if verdict == "WOULD" else "#e9c46a" if verdict == "MIGHT" else "#2a9d8f"
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.03, f"CLS={val:.2f}\n{verdict}",
                ha="center", fontsize=11, fontweight="bold", color=color)

    ax.set_xticks(range(4))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("CLS (starvation rate)", fontsize=12)
    ax.set_title("C12: lewis's verdict vs naive verdict\n"
                 "the inner sphere (lewis) and all worlds (naive) give DIFFERENT answers",
                 fontsize=14, fontweight="bold")
    ax.set_ylim(0, 1.15)
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(True, alpha=0.15, axis="y")

    plt.tight_layout()
    plt.savefig("phase3/plots/c12_lewis_verdict.png", dpi=150)
    print("Saved: c12_lewis_verdict.png")
    plt.close()

    # --- PRINT SUMMARY ---
    print(f"\n{'=' * 60}")
    print("C12: SOMEONE DIES OF STARVATION — SUMMARY")
    print(f"{'=' * 60}")
    print(f"\nInner sphere (10 closest, pop 30–57): CLS = {inner_cls_val:.3f}")
    print(f"Middle sphere (worlds 20–40, pop 90–147): CLS = {mid_cls_val:.3f}")
    print(f"Outer sphere (10 farthest, pop 240–270): CLS = {outer_cls_val:.3f}")
    print(f"All worlds: CLS = {all_cls_val:.3f}")
    print(f"\nAt T=0.8:")
    print(f"  Inner sphere says: {'WOULD' if inner_cls_val >= 0.8 else 'MIGHT' if inner_cls_val > 0 else 'WOULD NOT'}")
    print(f"  All worlds says:   {'WOULD' if all_cls_val >= 0.8 else 'MIGHT' if all_cls_val > 0 else 'WOULD NOT'}")
    print(f"\nLewis's verdict: {'starvation WOULD happen' if inner_cls_val >= 0.8 else 'starvation MIGHT happen (but would not be certain)' if inner_cls_val > 0 else 'starvation WOULD NOT happen'}")
    print(f"Naive verdict:   {'starvation WOULD happen' if all_cls_val >= 0.8 else 'starvation MIGHT happen' if all_cls_val > 0 else 'starvation WOULD NOT happen'}")
    if (inner_cls_val >= 0.8) != (all_cls_val >= 0.8):
        print(f"\n→ THE VERDICTS DISAGREE. This is Lewis's contribution.")
        print(f"  The naive approach includes distant worlds with very different")
        print(f"  conditions and gets a different answer. Lewis says: trust")
        print(f"  the closest worlds. They are most similar to reality.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()