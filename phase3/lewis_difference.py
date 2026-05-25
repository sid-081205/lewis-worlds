"""
PHASE 3 — Sphere Expansion Verdict Map
========================================
Shows how counterfactual verdicts change as the sphere expands.
Fixed threshold T. Sweep r from closest worlds to all worlds.
The difference between left edge and right edge IS Lewis's contribution.
"""

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")

PHASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = PHASE_DIR / "results"
PLOTS_DIR = PHASE_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_results():
    with open(RESULTS_DIR / "results.json", "r") as f:
        return json.load(f)


def compute_cls_at_r(responses, r):
    valid = [resp for resp in responses if resp["answer"] in (0, 1)]
    valid.sort(key=lambda x: x["distance"])
    in_sphere = [resp for resp in valid if resp["distance"] <= r]
    if not in_sphere:
        return None
    return sum(resp["answer"] for resp in in_sphere) / len(in_sphere)


def plot_verdict_map(data, threshold=0.8):
    all_results = data["all_results"]
    
    # Sort consequents by CLS at inner sphere
    cids = list(all_results.keys())
    inner_cls = {}
    for cid in cids:
        cls = compute_cls_at_r(all_results[cid]["responses"], 0.125)
        inner_cls[cid] = cls if cls is not None else 0
    cids.sort(key=lambda c: inner_cls[c], reverse=True)
    
    names = [f"{cid}: {all_results[cid]['name']}" for cid in cids]
    
    # Sweep r
    r_values = np.arange(0.01, 1.01, 0.0125)
    n_cons = len(cids)
    n_r = len(r_values)
    
    # Build matrix: consequent × r → CLS
    cls_matrix = np.zeros((n_cons, n_r))
    for ci, cid in enumerate(cids):
        responses = all_results[cid]["responses"]
        for ri, r in enumerate(r_values):
            cls = compute_cls_at_r(responses, r)
            cls_matrix[ci, ri] = cls if cls is not None else 0
    
    # Build verdict matrix: 1 = would (CLS >= T), 0 = would not / might
    verdict_matrix = (cls_matrix >= threshold).astype(float)
    
    # --- PLOT 1: Verdict map (binary: would vs not) ---
    fig, ax = plt.subplots(figsize=(18, 10))
    
    cmap = matplotlib.colors.ListedColormap(["#1a2a1a", "#e63946"])
    im = ax.imshow(verdict_matrix, cmap=cmap, aspect="auto", vmin=0, vmax=1,
                   interpolation="nearest")
    
    # X axis: sphere radius
    n_ticks = 10
    tick_positions = np.linspace(0, n_r - 1, n_ticks).astype(int)
    tick_labels = [f"r={r_values[i]:.2f}\npop≤{int(30 + r_values[i] * 240)}" for i in tick_positions]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, fontsize=8)
    ax.set_xlabel("sphere radius r (→ expanding outward from actual world)", fontsize=12)
    
    # Y axis: consequents
    ax.set_yticks(range(n_cons))
    ax.set_yticklabels(names, fontsize=9)
    
    ax.set_title(f"phase 3 — verdict map as sphere expands (T = {threshold})\n"
                 f"red = WOULD happen (CLS ≥ {threshold})   |   dark = would NOT / might\n"
                 f"lewis says: trust the LEFT edge (closest worlds)",
                 fontsize=14, fontweight="bold")
    
    # Add vertical line marking inner sphere
    inner_r_idx = np.argmin(np.abs(r_values - 0.125))
    ax.axvline(x=inner_r_idx, color="#f4a261", linestyle="--", linewidth=2, alpha=0.8)
    ax.text(inner_r_idx + 1, -0.8, "← lewis's\n    inner sphere", color="#f4a261",
            fontsize=9, fontweight="bold", va="bottom")
    
    plt.tight_layout()
    out = PLOTS_DIR / "verdict_map.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()
    
    # --- PLOT 2: CLS heatmap (continuous values) ---
    fig, ax = plt.subplots(figsize=(18, 10))
    
    im = ax.imshow(cls_matrix, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=1,
                   interpolation="bilinear")
    
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, fontsize=8)
    ax.set_xlabel("sphere radius r (→ expanding outward from actual world)", fontsize=12)
    
    ax.set_yticks(range(n_cons))
    ax.set_yticklabels(names, fontsize=9)
    
    ax.set_title(f"phase 3 — CLS heatmap as sphere expands\n"
                 f"red = high CLS (likely)   |   green = low CLS (unlikely)\n"
                 f"threshold T = {threshold} shown as contour",
                 fontsize=14, fontweight="bold")
    
    # Draw threshold contour
    for ci in range(n_cons):
        # Find where CLS crosses threshold
        crossings = []
        for ri in range(1, n_r):
            if (cls_matrix[ci, ri-1] < threshold and cls_matrix[ci, ri] >= threshold) or \
               (cls_matrix[ci, ri-1] >= threshold and cls_matrix[ci, ri] < threshold):
                crossings.append(ri)
        for cx in crossings:
            ax.plot(cx, ci, marker="|", color="white", markersize=15, markeredgewidth=2)
    
    ax.axvline(x=inner_r_idx, color="#f4a261", linestyle="--", linewidth=2, alpha=0.8)
    ax.text(inner_r_idx + 1, -0.8, "← inner sphere", color="#f4a261",
            fontsize=9, fontweight="bold", va="bottom")
    
    plt.colorbar(im, ax=ax, label="CLS", shrink=0.8)
    plt.tight_layout()
    out = PLOTS_DIR / "cls_heatmap_sweep.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()
    
    # --- PLOT 3: The key comparison — inner vs full ---
    fig, ax = plt.subplots(figsize=(14, 9))
    
    inner_r = 0.125
    full_r = 1.0
    
    inner_vals = []
    full_vals = []
    for cid in cids:
        responses = all_results[cid]["responses"]
        ic = compute_cls_at_r(responses, inner_r)
        fc = compute_cls_at_r(responses, full_r)
        inner_vals.append(ic if ic is not None else 0)
        full_vals.append(fc if fc is not None else 0)
    
    y = np.arange(n_cons)
    height = 0.35
    
    bars1 = ax.barh(y - height/2, inner_vals, height, label=f"inner sphere (r≤{inner_r}, pop≤{int(30 + inner_r * 240)})",
                    color="#1d3557", edgecolor="white", linewidth=0.5)
    bars2 = ax.barh(y + height/2, full_vals, height, label=f"all worlds (r≤{full_r}, pop≤270)",
                    color="#e63946", alpha=0.6, edgecolor="white", linewidth=0.5)
    
    # Threshold line
    ax.axvline(x=threshold, color="#f4a261", linestyle="--", linewidth=2, label=f"threshold T={threshold}")
    
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("CLS", fontsize=12)
    ax.set_title(f"phase 3 — the lewis difference\n"
                 f"blue = closest worlds only (lewis says trust this)\n"
                 f"red = all worlds equally (naive approach)",
                 fontsize=14, fontweight="bold")
    ax.set_xlim(0, 1.05)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.15, axis="x")
    
    # Annotate differences
    for i in range(n_cons):
        diff = full_vals[i] - inner_vals[i]
        if abs(diff) > 0.1:
            direction = "↑" if diff > 0 else "↓"
            ax.text(max(inner_vals[i], full_vals[i]) + 0.02, i,
                    f"{direction}{abs(diff):.2f}", fontsize=8, va="center",
                    color="#f4a261", fontweight="bold")
    
    # Count verdict changes
    inner_would = sum(1 for v in inner_vals if v >= threshold)
    full_would = sum(1 for v in full_vals if v >= threshold)
    ax.text(0.5, n_cons + 0.5,
            f"inner sphere: {inner_would} consequents 'would'   |   all worlds: {full_would} consequents 'would'   |   difference: {full_would - inner_would}",
            fontsize=11, fontweight="bold", color="#f4a261", ha="center")
    
    plt.tight_layout()
    out = PLOTS_DIR / "lewis_difference.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()
    
    # --- PRINT SUMMARY ---
    print(f"\n{'=' * 70}")
    print(f"THE LEWIS DIFFERENCE (T = {threshold})")
    print(f"{'=' * 70}")
    print(f"\n{'Consequent':<35} {'Inner CLS':>10} {'Full CLS':>10} {'Inner':>8} {'Full':>8} {'Changed?':>10}")
    print("-" * 85)
    for i, cid in enumerate(cids):
        name = all_results[cid]["name"]
        iv = inner_vals[i]
        fv = full_vals[i]
        inner_v = "WOULD" if iv >= threshold else "might" if iv > 0 else "no"
        full_v = "WOULD" if fv >= threshold else "might" if fv > 0 else "no"
        changed = "← FLIPPED" if inner_v != full_v else ""
        print(f"{cid}: {name:<30} {iv:>10.3f} {fv:>10.3f} {inner_v:>8} {full_v:>8} {changed:>10}")
    
    print(f"\nInner sphere: {inner_would} 'would' out of {n_cons}")
    print(f"All worlds:   {full_would} 'would' out of {n_cons}")
    print(f"Flipped:      {abs(full_would - inner_would)} consequents changed verdict")
    print(f"\nLewis's claim: the {inner_would} consequents identified by the inner sphere")
    print(f"are the correct counterfactual verdicts. The additional {abs(full_would - inner_would)}")
    print(f"that appear when including distant worlds are artefacts of including")
    print(f"irrelevant worlds with very different conditions.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    data = load_results()
    
    # Run at multiple thresholds
    for t in [0.8, 0.7, 0.5]:
        print(f"\n\n{'#' * 70}")
        print(f"THRESHOLD T = {t}")
        print(f"{'#' * 70}")
        plot_verdict_map(data, threshold=t)
    
    print("\nAll plots saved.")
