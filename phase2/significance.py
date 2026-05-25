"""
PHASE 2 — Statistical Significance Tests
==========================================
Runs chi-squared tests and Fisher's exact tests on Phase 2 results
to determine whether the observed differences are statistically significant.
"""

import json
from pathlib import Path

from scipy import stats

PHASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = PHASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_results():
    with open(RESULTS_DIR / "results.json", "r") as f:
        return json.load(f)


def count_answers(results):
    """Count YES (1) and NO (0) from a list of results."""
    yes = sum(1 for r in results if r["answer"] == 1)
    no = sum(1 for r in results if r["answer"] == 0)
    return yes, no


def run_test(name, run1_results, run2_results, run1_label, run2_label):
    """Run chi-squared and Fisher's exact test comparing two runs."""
    yes1, no1 = count_answers(run1_results)
    yes2, no2 = count_answers(run2_results)
    
    total1 = yes1 + no1
    total2 = yes2 + no2
    
    cls1 = yes1 / total1 if total1 > 0 else 0
    cls2 = yes2 / total2 if total2 > 0 else 0
    
    print(f"\n{'=' * 60}")
    print(f"{name}")
    print(f"{'=' * 60}")
    print(f"  {run1_label}: {yes1}/{total1} = {cls1:.3f}")
    print(f"  {run2_label}: {yes2}/{total2} = {cls2:.3f}")
    print(f"  Δ = {abs(cls1 - cls2):.3f}")
    
    # Contingency table
    #              YES    NO
    # Run 1        yes1   no1
    # Run 2        yes2   no2
    table = [[yes1, no1], [yes2, no2]]
    
    print(f"\n  Contingency table:")
    print(f"  {'':>20} {'YES':>8} {'NO':>8} {'Total':>8}")
    print(f"  {run1_label:>20} {yes1:>8} {no1:>8} {total1:>8}")
    print(f"  {run2_label:>20} {yes2:>8} {no2:>8} {total2:>8}")
    
    # Chi-squared test
    if min(yes1, no1, yes2, no2) >= 5:
        chi2, p_chi2, dof, expected = stats.chi2_contingency(table)
        print(f"\n  Chi-squared test:")
        print(f"    χ² = {chi2:.4f}")
        print(f"    df = {dof}")
        print(f"    p  = {p_chi2:.6f}")
        if p_chi2 < 0.001:
            print(f"    → Highly significant (p < 0.001)")
        elif p_chi2 < 0.01:
            print(f"    → Very significant (p < 0.01)")
        elif p_chi2 < 0.05:
            print(f"    → Significant (p < 0.05)")
        else:
            print(f"    → Not significant (p ≥ 0.05)")
    else:
        print(f"\n  Chi-squared: skipped (cell count < 5)")
    
    # Fisher's exact test (works for all sample sizes)
    odds_ratio, p_fisher = stats.fisher_exact(table)
    print(f"\n  Fisher's exact test:")
    print(f"    Odds ratio = {odds_ratio:.4f}")
    print(f"    p = {p_fisher:.6f}")
    if p_fisher < 0.001:
        print(f"    → Highly significant (p < 0.001)")
    elif p_fisher < 0.01:
        print(f"    → Very significant (p < 0.01)")
    elif p_fisher < 0.05:
        print(f"    → Significant (p < 0.05)")
    else:
        print(f"    → Not significant (p ≥ 0.05)")
    
    return {
        "name": name,
        "cls1": cls1,
        "cls2": cls2,
        "delta": abs(cls1 - cls2),
        "chi2_p": p_chi2 if min(yes1, no1, yes2, no2) >= 5 else None,
        "fisher_p": p_fisher,
        "fisher_odds": odds_ratio,
    }


def main():
    data = load_results()
    
    print("=" * 60)
    print("PHASE 2 — STATISTICAL SIGNIFICANCE TESTS")
    print("=" * 60)
    
    results = []
    
    # Test 2a: Strengthening the Antecedent
    r = run_test(
        "Test 2a — Strengthening the Antecedent",
        data["2a"]["run1"], data["2a"]["run2"],
        "Destroyed", "Destroyed + Elder"
    )
    results.append(r)
    
    # Test 2b: Transitivity
    # Compare chain prediction vs direct
    # The chain is A→B × B→C. We compare A→B (rationing) vs A→C (resentment direct)
    r = run_test(
        "Test 2b — Transitivity (A→B vs A→C)",
        data["2b"]["run1"], data["2b"]["run3"],
        "A→B (rationing)", "A→C (resentment)"
    )
    results.append(r)
    
    # Also compare B→C vs A→C
    r = run_test(
        "Test 2b — Transitivity (B→C vs A→C)",
        data["2b"]["run2"], data["2b"]["run3"],
        "B→C (resentment|ration)", "A→C (resentment|destroy)"
    )
    results.append(r)
    
    # Test 2c: Contraposition
    r = run_test(
        "Test 2c — Contraposition",
        data["2c"]["run1"], data["2c"]["run2"],
        "Forward (destroy→conflict)", "Contra (peace→intact)"
    )
    results.append(r)
    
    # Summary
    print(f"\n\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"\n{'Test':<45} {'Δ':>6} {'Fisher p':>12} {'Sig?':>8}")
    print("-" * 75)
    for r in results:
        sig = "YES" if r["fisher_p"] < 0.05 else "NO"
        star = "***" if r["fisher_p"] < 0.001 else "**" if r["fisher_p"] < 0.01 else "*" if r["fisher_p"] < 0.05 else ""
        print(f"{r['name']:<45} {r['delta']:>6.3f} {r['fisher_p']:>12.6f} {sig:>5} {star}")
    
    # Save
    out_path = RESULTS_DIR / "significance.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()