"""
PHASE 2 — Visualization
========================
Reads phase2_results.json and produces comparison plots
for each of Lewis's three fallacies.
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


def compute_cls(results):
    valid = [r for r in results if r["answer"] in (0, 1)]
    if not valid:
        return 0.0
    return sum(r["answer"] for r in valid) / len(valid)


def compute_cls_by_distance(results, n_bins=10):
    """Compute CLS in distance bins for plotting curves."""
    valid = [r for r in results if r["answer"] in (0, 1)]
    valid.sort(key=lambda r: r["distance"])
    
    bin_size = max(1, len(valid) // n_bins)
    midpoints = []
    cls_values = []
    
    for i in range(0, len(valid), bin_size):
        chunk = valid[i:i + bin_size]
        if not chunk:
            continue
        mid = sum(r["distance"] for r in chunk) / len(chunk)
        cls = sum(r["answer"] for r in chunk) / len(chunk)
        midpoints.append(mid)
        cls_values.append(cls)
    
    return midpoints, cls_values


def plot_2a_strengthening(data):
    """Plot Test 2a — Strengthening the Antecedent."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Bar chart comparing overall CLS
    labels = ["Rice field\ndestroyed", "Rice field destroyed\n+ Elder leads"]
    values = [data["cls_run1"], data["cls_run2"]]
    colors = ["#E63946", "#2D6A4F"]
    
    bars = ax1.bar(labels, values, color=colors, width=0.5, edgecolor="white", linewidth=2)
    ax1.set_ylabel("CLS (conflict rate)", fontsize=12)
    ax1.set_title("Test 2a — Strengthening the Antecedent\n"
                   "Adding a condition should REDUCE conflict",
                   fontsize=13, fontweight="bold")
    ax1.set_ylim(0, 1)
    ax1.axhline(y=0.5, color="#999", linestyle=":", alpha=0.5)
    
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 0.02, f"{val:.3f}",
                ha="center", fontsize=12, fontweight="bold")
    
    delta = data["cls_run1"] - data["cls_run2"]
    ax1.text(0.5, 0.92, f"Δ = {delta:+.3f}", transform=ax1.transAxes,
             ha="center", fontsize=14, fontweight="bold",
             color="#2D6A4F" if delta > 0 else "#E63946")
    
    # CLS curves by distance
    mid1, cls1 = compute_cls_by_distance(data["run1"])
    mid2, cls2 = compute_cls_by_distance(data["run2"])
    
    ax2.plot(mid1, cls1, color="#E63946", linewidth=2, marker="o", markersize=5,
             label="Destroyed only")
    ax2.plot(mid2, cls2, color="#2D6A4F", linewidth=2, marker="s", markersize=5,
             label="Destroyed + Elder")
    ax2.set_xlabel("Distance from base world", fontsize=11)
    ax2.set_ylabel("Local CLS (conflict rate)", fontsize=11)
    ax2.set_title("Conflict rate across similarity gradient", fontsize=12)
    ax2.set_xlim(-0.02, 1.02)
    ax2.set_ylim(-0.05, 1.05)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    out = PLOTS_DIR / "test2a.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()


def plot_2b_transitivity(data):
    """Plot Test 2b — Transitivity."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Bar chart comparing CLS values
    labels = ["A→B\nDestruction\n→Rationing", "B→C\nRationing\n→Resentment",
              "Chain\nA→B × B→C", "A→C direct\nDestruction\n→Resentment"]
    values = [data["cls_ab"], data["cls_bc"], data["cls_chain"], data["cls_ac"]]
    colors = ["#457B9D", "#457B9D", "#E9C46A", "#E63946"]
    
    bars = ax1.bar(labels, values, color=colors, width=0.6, edgecolor="white", linewidth=2)
    ax1.set_ylabel("CLS", fontsize=12)
    ax1.set_title("Test 2b — Transitivity\n"
                   "Chain prediction vs direct counterfactual",
                   fontsize=13, fontweight="bold")
    ax1.set_ylim(0, 1)
    
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 0.02, f"{val:.3f}",
                ha="center", fontsize=11, fontweight="bold")
    
    delta = data["cls_chain"] - data["cls_ac"]
    ax1.text(0.5, 0.92, f"Δ (chain − direct) = {delta:+.3f}", transform=ax1.transAxes,
             ha="center", fontsize=13, fontweight="bold",
             color="#E63946" if abs(delta) > 0.1 else "#999")
    
    # CLS curves for all three runs
    mid1, cls1 = compute_cls_by_distance(data["run1"])
    mid2, cls2 = compute_cls_by_distance(data["run2"])
    mid3, cls3 = compute_cls_by_distance(data["run3"])
    
    ax2.plot(mid1, cls1, color="#457B9D", linewidth=2, marker="o", markersize=5,
             label="A→B (destruction→rationing)")
    ax2.plot(mid2, cls2, color="#2A9D8F", linewidth=2, marker="s", markersize=5,
             label="B→C (rationing→resentment)")
    ax2.plot(mid3, cls3, color="#E63946", linewidth=2, marker="^", markersize=5,
             label="A→C (destruction→resentment)")
    ax2.set_xlabel("Distance from base world", fontsize=11)
    ax2.set_ylabel("Local CLS", fontsize=11)
    ax2.set_title("Each link across the gradient", fontsize=12)
    ax2.set_xlim(-0.02, 1.02)
    ax2.set_ylim(-0.05, 1.05)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    out = PLOTS_DIR / "test2b.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()


def plot_2c_contraposition(data):
    """Plot Test 2c — Contraposition."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Bar chart
    labels = ["Forward\nDestruction\n→Conflict", "Contrapositive\nNo conflict\n→Field intact"]
    values = [data["cls_forward"], data["cls_contra"]]
    colors = ["#E63946", "#6C4AB6"]
    
    bars = ax1.bar(labels, values, color=colors, width=0.5, edgecolor="white", linewidth=2)
    ax1.set_ylabel("CLS", fontsize=12)
    ax1.set_title("Test 2c — Contraposition\n"
                   "Forward vs contrapositive should be ASYMMETRIC",
                   fontsize=13, fontweight="bold")
    ax1.set_ylim(0, 1)
    ax1.axhline(y=0.5, color="#999", linestyle=":", alpha=0.5)
    
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 0.02, f"{val:.3f}",
                ha="center", fontsize=12, fontweight="bold")
    
    delta = abs(data["cls_forward"] - data["cls_contra"])
    ax1.text(0.5, 0.92, f"|Δ| = {delta:.3f}", transform=ax1.transAxes,
             ha="center", fontsize=14, fontweight="bold",
             color="#E63946" if delta > 0.15 else "#999")
    
    # CLS curves
    mid1, cls1 = compute_cls_by_distance(data["run1"])
    mid2, cls2 = compute_cls_by_distance(data["run2"])
    
    ax2.plot(mid1, cls1, color="#E63946", linewidth=2, marker="o", markersize=5,
             label="Forward (destruction→conflict)")
    ax2.plot(mid2, cls2, color="#6C4AB6", linewidth=2, marker="s", markersize=5,
             label="Contra (no conflict→intact)")
    ax2.set_xlabel("Distance from base world", fontsize=11)
    ax2.set_ylabel("Local CLS", fontsize=11)
    ax2.set_title("Forward vs contrapositive across gradient", fontsize=12)
    ax2.set_xlim(-0.02, 1.02)
    ax2.set_ylim(-0.05, 1.05)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    out = PLOTS_DIR / "test2c.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()


def plot_summary(data):
    """Plot overall Phase 2 summary — all three deltas."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    labels = ["2a: Strengthening\nthe Antecedent", "2b: Transitivity", "2c: Contraposition"]
    deltas = [
        data["2a"]["cls_run1"] - data["2a"]["cls_run2"],
        abs(data["2b"]["cls_chain"] - data["2b"]["cls_ac"]),
        abs(data["2c"]["cls_forward"] - data["2c"]["cls_contra"]),
    ]
    thresholds = [0.1, 0.1, 0.15]
    confirmed = [d > t for d, t in zip(deltas, thresholds)]
    colors = ["#2D6A4F" if c else "#E63946" for c in confirmed]
    
    bars = ax.bar(labels, deltas, color=colors, width=0.5, edgecolor="white", linewidth=2)
    
    for i, (bar, val, conf) in enumerate(zip(bars, deltas, confirmed)):
        symbol = "✓" if conf else "✗"
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.01, f"{symbol} Δ={val:.3f}",
                ha="center", fontsize=12, fontweight="bold")
    
    # Threshold line
    ax.axhline(y=0.1, color="#E9C46A", linestyle="--", alpha=0.6, label="Confirmation threshold")
    
    ax.set_ylabel("Delta (effect size)", fontsize=12)
    ax.set_title("Phase 2 Summary — Lewis's Three Fallacies\n"
                 "Green = confirmed, Red = not confirmed",
                 fontsize=14, fontweight="bold")
    ax.set_ylim(0, max(deltas) * 1.3 + 0.05)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis="y")
    
    n_confirmed = sum(confirmed)
    ax.text(0.5, 0.02, f"{n_confirmed}/3 fallacies confirmed",
            transform=ax.transAxes, ha="center", fontsize=13,
            fontweight="bold", color="#1D3557")
    
    plt.tight_layout()
    out = PLOTS_DIR / "summary.png"
    plt.savefig(out, dpi=150)
    print(f"Saved: {out}")
    plt.close()


def print_summary(data):
    print("\n" + "=" * 60)
    print("PHASE 2 — FALLACY TEST RESULTS")
    print("=" * 60)
    
    d2a = data["2a"]["cls_run1"] - data["2a"]["cls_run2"]
    d2b = abs(data["2b"]["cls_chain"] - data["2b"]["cls_ac"])
    d2c = abs(data["2c"]["cls_forward"] - data["2c"]["cls_contra"])
    
    print(f"\n2a Strengthening:")
    print(f"  CLS(destroyed):          {data['2a']['cls_run1']:.3f}")
    print(f"  CLS(destroyed + elder):  {data['2a']['cls_run2']:.3f}")
    print(f"  Δ = {d2a:+.3f}  {'✓ CONFIRMED' if d2a > 0.1 else '✗ NOT CONFIRMED'}")
    
    print(f"\n2b Transitivity:")
    print(f"  CLS(A→B):    {data['2b']['cls_ab']:.3f}")
    print(f"  CLS(B→C):    {data['2b']['cls_bc']:.3f}")
    print(f"  Chain:        {data['2b']['cls_chain']:.3f}")
    print(f"  CLS(A→C):    {data['2b']['cls_ac']:.3f}")
    print(f"  Δ = {d2b:.3f}   {'✓ CONFIRMED' if d2b > 0.1 else '✗ NOT CONFIRMED'}")
    
    print(f"\n2c Contraposition:")
    print(f"  CLS(forward):  {data['2c']['cls_forward']:.3f}")
    print(f"  CLS(contra):   {data['2c']['cls_contra']:.3f}")
    print(f"  |Δ| = {d2c:.3f}  {'✓ CONFIRMED' if d2c > 0.15 else '✗ NOT CONFIRMED'}")
    
    print("=" * 60)


if __name__ == "__main__":
    data = load_results()
    print_summary(data)
    plot_2a_strengthening(data["2a"])
    plot_2b_transitivity(data["2b"])
    plot_2c_contraposition(data["2c"])
    plot_summary(data)
    print("\nAll plots saved.")