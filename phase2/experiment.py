"""
PHASE 2 — Testing Lewis's Three Fallacies
==========================================
Tests whether strengthening the antecedent, transitivity,
and contraposition fail for counterfactuals, as Lewis predicts.

Uses the same 81 island worlds from Phase 1 (population 30 to 270, step 3).
"""

import json
import re
import time
from pathlib import Path

from anthropic import Anthropic

PHASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = PHASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# --- CONFIGURATION ---

API_BASE_URL = "http://localhost:8001"
API_KEY = "anything"
MODEL = "claude-haiku-4-5-20251001"

# --- SYSTEM PROMPT (same as Phase 1) ---

def make_system_prompt(population: int) -> str:
    return f"""You exist in the following world. This is the complete and total description of your reality. Reason only from what is described below.

THE ISLAND

A remote island with no contact with the outside world. No one can leave. No outside help is possible.

There are {population} people living on the island. They are ordinary people with the full range of human behaviour — capable of kindness and selfishness, cooperation and competition, trust and suspicion, generosity and hoarding. They are neither unusually virtuous nor unusually cruel. They behave as typical humans do under the circumstances they face.

There is no formal government or legal system on the island. There is no single leader. People organise themselves however they see fit. In recent months, as the island's population has settled into its current size, people have naturally formed smaller circles of trust — families, close friends, people who fish together or farm together.

The island has one rice field. It was originally designed to feed about 30 people. The island also has fishing waters, but the catch is limited — enough to supplement meals, not to replace the rice field.

There is a storage hut with dried rice, but it holds only enough to feed about 30 people for several months.

The island has no weapons beyond basic farming and fishing tools.

You always respond with extreme brevity. One short phrase maximum. No essays. No analysis. No paragraphs. Just a gut judgment and the final verdict."""


# --- WORLD GENERATION (same as Phase 1) ---

def generate_worlds():
    """Generate 81 worlds: population 30 to 270 in steps of 3."""
    worlds = []
    for i in range(81):
        pop = 30 + (i * 3)
        distance = (pop - 30) / 240
        worlds.append({
            "id": f"W{i}",
            "population": pop,
            "distance": round(distance, 4),
            "system_prompt": make_system_prompt(pop),
        })
    return worlds


# --- PARSING ---

def parse_binary(text: str, yes_word: str, no_word: str) -> int:
    """Parse a binary answer from the response. Returns 1 for yes_word, 0 for no_word, -1 for unclear."""
    lines = text.strip().split("\n")

    # Check last few lines
    for line in reversed(lines):
        stripped = line.strip().upper()
        if stripped == no_word.upper():
            return 0
        elif stripped == yes_word.upper():
            return 1

    # Fallback: find last occurrence
    upper = text.upper()
    last_no = upper.rfind(no_word.upper())
    last_yes = upper.rfind(yes_word.upper())

    if last_no == -1 and last_yes == -1:
        return -1
    elif last_no == -1:
        return 1
    elif last_yes == -1:
        return 0
    # If no_word contains yes_word (like "NO CONFLICT" contains "CONFLICT")
    elif no_word.upper() in yes_word.upper() or yes_word.upper() in no_word.upper():
        # Check if the last yes is part of the last no
        if last_yes >= last_no and last_yes <= last_no + len(no_word):
            return 0
        elif last_yes > last_no:
            return 1
        else:
            return 0
    elif last_yes > last_no:
        return 1
    else:
        return 0


def extract_reasoning(text: str) -> str:
    lines = text.strip().split("\n")
    reasoning_lines = [l.strip() for l in lines[:-1] if l.strip()]
    return " ".join(reasoning_lines)[:200]


# --- QUERY FUNCTION ---

def query(client: Anthropic, system_prompt: str, user_msg: str) -> str:
    """Send a query and return raw response text."""
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=200,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"ERROR: {e}"


# ============================================================
# TEST 2a — STRENGTHENING THE ANTECEDENT
# ============================================================
# Lewis: from (φ □→ ψ) it does NOT follow that (φ & χ) □→ ψ
#
# Run 1: "If the rice field is destroyed, does conflict break out?"
# Run 2: "If the rice field is destroyed AND a respected elder steps up to lead, does conflict break out?"
#
# Prediction: CLS should DROP in Run 2. The added condition (elder leads)
# should reduce conflict, even though we strengthened the antecedent.
# ============================================================

MSG_2A_RUN1 = """The rice field has just been completely destroyed. It cannot be replanted or recovered.

There are exactly {population} people on this island. Think about what these {population} people actually do in the weeks that follow.

Does violent conflict break out among the islanders within 8 weeks?

One short phrase of reasoning, then on a new line write exactly CONFLICT or NO CONFLICT."""

MSG_2A_RUN2 = """The rice field has just been completely destroyed. It cannot be replanted or recovered. At the same time, a widely respected elder among the islanders immediately steps forward and proposes a rationing plan that everyone hears.

There are exactly {population} people on this island. Think about what these {population} people actually do in the weeks that follow.

Does violent conflict break out among the islanders within 8 weeks?

One short phrase of reasoning, then on a new line write exactly CONFLICT or NO CONFLICT."""


# ============================================================
# TEST 2b — TRANSITIVITY
# ============================================================
# Lewis: from (φ □→ ψ) and (ψ □→ χ) it does NOT follow that (φ □→ χ)
#
# Run 1: "If the rice field is destroyed, do the islanders start rationing?"
# Run 2: "If the islanders start rationing, does resentment build up?"
# Run 3: "If the rice field is destroyed, does resentment build up?"
#
# Prediction: Run 1 and Run 2 may both have high YES rates,
# but Run 3 may have a LOWER YES rate than chaining would predict.
# ============================================================

MSG_2B_RUN1 = """The rice field has just been completely destroyed. It cannot be replanted or recovered.

There are exactly {population} people on this island. Think about what these {population} people actually do.

Do the islanders begin strictly rationing food within the first 2 weeks?

One short phrase of reasoning, then on a new line write exactly RATIONING or NO RATIONING."""

MSG_2B_RUN2 = """The islanders have been strictly rationing food for 4 weeks now. Portions are small and everyone is hungry. Some people feel others are getting more than their fair share.

There are exactly {population} people on this island. Think about what these {population} people actually do.

Does widespread resentment and anger build up among the islanders?

One short phrase of reasoning, then on a new line write exactly RESENTMENT or NO RESENTMENT."""

MSG_2B_RUN3 = """The rice field has just been completely destroyed. It cannot be replanted or recovered.

There are exactly {population} people on this island. Think about what these {population} people actually do over the following 6 weeks.

Does widespread resentment and anger build up among the islanders?

One short phrase of reasoning, then on a new line write exactly RESENTMENT or NO RESENTMENT."""


# ============================================================
# TEST 2c — CONTRAPOSITION
# ============================================================
# Lewis: from (φ □→ ψ) it does NOT follow that (~ψ □→ ~φ)
#
# Run 1 (forward): "If the rice field is destroyed, does conflict break out?"
# Run 2 (contrapositive): "If there is no conflict, is it the case that the rice field was not destroyed?"
#
# Prediction: The rates should be ASYMMETRIC.
# ============================================================

MSG_2C_RUN1 = """The rice field has just been completely destroyed. It cannot be replanted or recovered.

There are exactly {population} people on this island. Think about what these {population} people actually do.

Does violent conflict break out among the islanders within 8 weeks?

One short phrase of reasoning, then on a new line write exactly CONFLICT or NO CONFLICT."""

MSG_2C_RUN2 = """The island has been peaceful for the past 8 weeks. There has been no violent conflict at all among the islanders. Everyone has remained calm.

There are exactly {population} people on this island. Given this peace, think about the state of the island.

Is the rice field still intact and producing food?

One short phrase of reasoning, then on a new line write exactly INTACT or NOT INTACT."""


# ============================================================
# RUN ALL TESTS
# ============================================================

def run_test(client, worlds, test_name, msg_template, yes_word, no_word):
    """Run a single test across all worlds. Returns list of results."""
    results = []
    for i, world in enumerate(worlds):
        user_msg = msg_template.format(population=world["population"])
        print(f"  [{i+1:>2}/{len(worlds)}] pop:{world['population']:>3}", end="  →  ")

        response = query(client, world["system_prompt"], user_msg)
        answer = parse_binary(response, yes_word, no_word)
        reasoning = extract_reasoning(response)

        label = yes_word if answer == 1 else no_word if answer == 0 else "???"
        print(f"{label:<15} {reasoning[:100]}")

        results.append({
            "world_id": world["id"],
            "population": world["population"],
            "distance": world["distance"],
            "answer": answer,
            "reasoning": reasoning,
            "full_response": response,
        })
        time.sleep(0.3)

    return results


def compute_cls(results):
    """Compute overall CLS from a list of results."""
    valid = [r for r in results if r["answer"] in (0, 1)]
    if not valid:
        return 0.0
    return sum(r["answer"] for r in valid) / len(valid)


def compute_cls_by_sphere(results, sphere_sizes=[10, 20, 40, 81]):
    """Compute CLS at various sphere sizes."""
    valid = [r for r in results if r["answer"] in (0, 1)]
    valid.sort(key=lambda r: r["distance"])
    stats = []
    for n in sphere_sizes:
        subset = valid[:n]
        if not subset:
            continue
        cls = sum(r["answer"] for r in subset) / len(subset)
        stats.append({"n": n, "cls": round(cls, 4)})
    return stats


def run_phase2():
    client = Anthropic(base_url=API_BASE_URL, api_key=API_KEY)
    worlds = generate_worlds()

    print("=" * 70)
    print("PHASE 2 — Testing Lewis's Three Fallacies")
    print(f"Using {len(worlds)} worlds (population 30 to 270, step 3)")
    print("=" * 70)

    all_results = {}

    # --- TEST 2a: STRENGTHENING THE ANTECEDENT ---
    print("\n" + "=" * 70)
    print("TEST 2a — STRENGTHENING THE ANTECEDENT")
    print("Lewis: adding a condition to the antecedent can FLIP the result")
    print("=" * 70)

    print("\nRun 1: Rice field destroyed → conflict?")
    r2a_run1 = run_test(client, worlds, "2a_run1", MSG_2A_RUN1, "CONFLICT", "NO CONFLICT")

    print("\nRun 2: Rice field destroyed AND elder leads → conflict?")
    r2a_run2 = run_test(client, worlds, "2a_run2", MSG_2A_RUN2, "CONFLICT", "NO CONFLICT")

    cls_2a_1 = compute_cls(r2a_run1)
    cls_2a_2 = compute_cls(r2a_run2)
    delta_strengthen = cls_2a_1 - cls_2a_2

    print(f"\n  CLS (rice destroyed):              {cls_2a_1:.4f}")
    print(f"  CLS (rice destroyed + elder leads): {cls_2a_2:.4f}")
    print(f"  Δ_strengthen = {delta_strengthen:+.4f}")
    if delta_strengthen > 0.1:
        print(f"  ✓ FALLACY CONFIRMED: Strengthening the antecedent reduced conflict rate.")
    else:
        print(f"  ✗ Fallacy not clearly demonstrated (Δ too small).")

    all_results["2a"] = {
        "run1": r2a_run1, "run2": r2a_run2,
        "cls_run1": cls_2a_1, "cls_run2": cls_2a_2,
        "delta": delta_strengthen,
    }

    # --- TEST 2b: TRANSITIVITY ---
    print("\n" + "=" * 70)
    print("TEST 2b — TRANSITIVITY")
    print("Lewis: (A→B) and (B→C) does NOT imply (A→C)")
    print("=" * 70)

    print("\nRun 1: Rice field destroyed → rationing?")
    r2b_run1 = run_test(client, worlds, "2b_run1", MSG_2B_RUN1, "RATIONING", "NO RATIONING")

    print("\nRun 2: Rationing happening → resentment?")
    r2b_run2 = run_test(client, worlds, "2b_run2", MSG_2B_RUN2, "RESENTMENT", "NO RESENTMENT")

    print("\nRun 3: Rice field destroyed → resentment? (direct)")
    r2b_run3 = run_test(client, worlds, "2b_run3", MSG_2B_RUN3, "RESENTMENT", "NO RESENTMENT")

    cls_2b_ab = compute_cls(r2b_run1)
    cls_2b_bc = compute_cls(r2b_run2)
    cls_2b_ac = compute_cls(r2b_run3)
    cls_chain = cls_2b_ab * cls_2b_bc
    delta_transit = cls_chain - cls_2b_ac

    print(f"\n  CLS (A→B, destruction→rationing):  {cls_2b_ab:.4f}")
    print(f"  CLS (B→C, rationing→resentment):   {cls_2b_bc:.4f}")
    print(f"  CLS_chain = A→B × B→C:             {cls_chain:.4f}")
    print(f"  CLS (A→C, destruction→resentment):  {cls_2b_ac:.4f}")
    print(f"  Δ_transit = chain - direct = {delta_transit:+.4f}")
    if abs(delta_transit) > 0.1:
        print(f"  ✓ FALLACY CONFIRMED: Direct counterfactual differs from chained prediction.")
    else:
        print(f"  ✗ Fallacy not clearly demonstrated (Δ too small).")

    all_results["2b"] = {
        "run1": r2b_run1, "run2": r2b_run2, "run3": r2b_run3,
        "cls_ab": cls_2b_ab, "cls_bc": cls_2b_bc, "cls_ac": cls_2b_ac,
        "cls_chain": cls_chain, "delta": delta_transit,
    }

    # --- TEST 2c: CONTRAPOSITION ---
    print("\n" + "=" * 70)
    print("TEST 2c — CONTRAPOSITION")
    print("Lewis: (φ→ψ) does NOT imply (~ψ→~φ)")
    print("=" * 70)

    print("\nRun 1 (forward): Rice field destroyed → conflict?")
    r2c_run1 = run_test(client, worlds, "2c_run1", MSG_2C_RUN1, "CONFLICT", "NO CONFLICT")

    print("\nRun 2 (contrapositive): No conflict → rice field intact?")
    r2c_run2 = run_test(client, worlds, "2c_run2", MSG_2C_RUN2, "INTACT", "NOT INTACT")

    cls_forward = compute_cls(r2c_run1)
    cls_contra = compute_cls(r2c_run2)
    delta_contra = abs(cls_forward - cls_contra)

    print(f"\n  CLS (forward: destruction→conflict):     {cls_forward:.4f}")
    print(f"  CLS (contra: no conflict→field intact):  {cls_contra:.4f}")
    print(f"  Δ_contra = |forward - contra| = {delta_contra:.4f}")
    if delta_contra > 0.15:
        print(f"  ✓ FALLACY CONFIRMED: Forward and contrapositive give different rates.")
    else:
        print(f"  ✗ Fallacy not clearly demonstrated (rates too similar).")

    all_results["2c"] = {
        "run1": r2c_run1, "run2": r2c_run2,
        "cls_forward": cls_forward, "cls_contra": cls_contra,
        "delta": delta_contra,
    }

    # --- FINAL SUMMARY ---
    print("\n" + "=" * 70)
    print("PHASE 2 — FINAL SUMMARY")
    print("=" * 70)
    print(f"\n  2a Strengthening: Δ = {delta_strengthen:+.4f}  {'✓ CONFIRMED' if delta_strengthen > 0.1 else '✗ NOT CONFIRMED'}")
    print(f"  2b Transitivity:  Δ = {delta_transit:+.4f}  {'✓ CONFIRMED' if abs(delta_transit) > 0.1 else '✗ NOT CONFIRMED'}")
    print(f"  2c Contraposition: Δ = {delta_contra:.4f}   {'✓ CONFIRMED' if delta_contra > 0.15 else '✗ NOT CONFIRMED'}")

    confirmed = sum([
        delta_strengthen > 0.1,
        abs(delta_transit) > 0.1,
        delta_contra > 0.15,
    ])
    print(f"\n  {confirmed}/3 fallacies confirmed.")
    if confirmed == 3:
        print("  All three fallacies demonstrated. Strong support for Lewis's variably strict analysis.")
    elif confirmed >= 2:
        print("  Majority confirmed. Good support for Lewis.")
    else:
        print("  Weak support. The model may not differentiate these cases well.")

    # Save everything
    results_path = RESULTS_DIR / "results.json"
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Results saved to {results_path}")
    print("=" * 70)


if __name__ == "__main__":
    run_phase2()
