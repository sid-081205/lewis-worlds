"""
PHASE 1 — Testing Lewis's Core Hypothesis (Conflict Version)
=============================================================
Does the counterfactual "if the rice field is destroyed, conflict breaks out"
depend on world-distance (population difference from base world)?

81 worlds: population from 30 to 270 in steps of 3.
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

# --- BASE WORLD PROMPT ---

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


# --- THE COUNTERFACTUAL QUESTION ---

USER_MESSAGE_TEMPLATE = """The rice field has just been completely destroyed. It cannot be replanted or recovered.

The islanders still have the stored rice and the fishing waters. These resources can sustain a significant number of people but the long-term situation is now precarious.

There are exactly {population} people on this island. Not {alt_population}, not {alt_population_low} — exactly {population}. This exact number determines everything: how food is split, whether strangers exist in the group, whether anyone can hide, whether one conversation can include everyone, whether trust holds or fractures.

Do not describe the group as being in any "zone" or "threshold." Do not use academic framing. Simply imagine you are watching these exact {population} people from above as the weeks unfold. Watch what they actually do — the specific conversations, the specific moments where someone takes more than their share or doesn't, the specific point where a fight starts or doesn't.

Does violent conflict break out among the islanders within 8 weeks?

Answer in one short phrase of reasoning, then on a new line write exactly CONFLICT or NO CONFLICT."""


# --- GENERATE ALL WORLDS ---

def generate_worlds():
    """Generate 81 worlds: population 30 to 270 in steps of 3."""
    worlds = []
    for i in range(81):
        pop = 30 + (i * 3)
        distance = (pop - 30) / 240  # normalised 0 to 1
        worlds.append({
            "id": f"W{i}",
            "population": pop,
            "distance": round(distance, 4),
            "system_prompt": make_system_prompt(pop),
        })
    return worlds


# --- QUERY A SINGLE WORLD ---

def parse_conflict(text: str) -> int:
    """Extract CONFLICT or NO CONFLICT from the response."""
    lines = text.strip().split("\n")

    # Check last few lines (model might add trailing whitespace or empty lines)
    for line in reversed(lines):
        stripped = line.strip().upper()
        if stripped == "NO CONFLICT":
            return 0
        elif stripped == "CONFLICT":
            return 1

    # Fallback: scan whole response
    upper = text.upper()
    # Check for "NO CONFLICT" first (to avoid matching "CONFLICT" inside it)
    last_no = upper.rfind("NO CONFLICT")
    last_yes = upper.rfind("CONFLICT")

    if last_no == -1 and last_yes == -1:
        return -1
    elif last_no == -1:
        return 1
    elif last_yes == last_no + 3:
        # "NO CONFLICT" contains "CONFLICT" at offset +3
        return 0
    elif last_yes > last_no:
        return 1
    else:
        return 0


def query_world(client: Anthropic, world: dict) -> dict:
    """Send the counterfactual question to one world and parse the response."""
    user_msg = USER_MESSAGE_TEMPLATE.format(
        population=world["population"],
        alt_population=world["population"] + 3,
        alt_population_low=world["population"] - 3
    )

    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=200,
            system=world["system_prompt"],
            messages=[{"role": "user", "content": user_msg}],
        )
        response_text = msg.content[0].text.strip()
        answer = parse_conflict(response_text)

        # Extract reasoning (everything before the last line)
        lines = response_text.strip().split("\n")
        reasoning_lines = [l.strip() for l in lines[:-1] if l.strip()]
        reasoning = " ".join(reasoning_lines)[:250]

        return {
            "world_id": world["id"],
            "population": world["population"],
            "distance": world["distance"],
            "answer": answer,
            "reasoning": reasoning,
            "full_response": response_text,
        }

    except Exception as e:
        return {
            "world_id": world["id"],
            "population": world["population"],
            "distance": world["distance"],
            "answer": -1,
            "reasoning": str(e),
            "full_response": str(e),
        }


# --- RUN THE EXPERIMENT ---

def run_phase1():
    client = Anthropic(base_url=API_BASE_URL, api_key=API_KEY)
    worlds = generate_worlds()
    results = []

    print("=" * 70)
    print("PHASE 1 — Lewis's Core Hypothesis (Conflict Version)")
    print(f"Testing {len(worlds)} worlds (population 30 to 270, step 3)")
    print("Antecedent: Rice field destroyed")
    print("Consequent: Does violent conflict break out?")
    print("=" * 70)
    print()

    for i, world in enumerate(worlds):
        print(f"[{i+1:>2}/{len(worlds)}] {world['id']:<4} "
              f"pop: {world['population']:>3}  "
              f"dist: {world['distance']:.3f}", end="  →  ")

        result = query_world(client, world)
        results.append(result)

        if result["answer"] == 1:
            label = "⚔️  CONFLICT"
        elif result["answer"] == 0:
            label = "🕊️  NO CONFLICT"
        else:
            label = "❓  UNCLEAR"
        print(label)

        if result.get("reasoning"):
            # Print reasoning wrapped to reasonable width
            r = result["reasoning"][:200]
            print(f"    ↳ {r}")
        print()

        time.sleep(0.5)

    # --- SAVE RAW RESULTS ---
    results_path = RESULTS_DIR / "results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Raw results saved to {results_path}")

    # --- COMPUTE AND DISPLAY CLS ---
    print("\n" + "=" * 70)
    print("RESULTS — Cumulative CLS (conflict rate) as sphere expands")
    print("=" * 70)

    valid = [r for r in results if r["answer"] in (0, 1)]
    valid.sort(key=lambda r: r["distance"])

    print(f"\n{'Population':<15} {'Distance':<10} {'Answer':<15} {'CLS so far':<12}")
    print("-" * 55)

    cumulative_yes = 0
    cumulative_total = 0

    for r in valid:
        cumulative_total += 1
        cumulative_yes += r["answer"]
        cls = cumulative_yes / cumulative_total
        label = "CONFLICT" if r["answer"] == 1 else "NO CONFLICT"
        print(f"{r['population']:<15} {r['distance']:<10.3f} {label:<15} {cls:<12.4f}")

    # --- SUMMARY ---
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")

    closest_5 = valid[:5]
    farthest_5 = valid[-5:]

    c5_yes = sum(r["answer"] for r in closest_5)
    f5_yes = sum(r["answer"] for r in farthest_5)

    print(f"Closest 5 worlds (pop 30-50):")
    print(f"  Conflict rate: {c5_yes}/{len(closest_5)} = {c5_yes/len(closest_5):.2f}")
    print(f"Farthest 5 worlds (pop 258-270):")
    print(f"  Conflict rate: {f5_yes}/{len(farthest_5)} = {f5_yes/len(farthest_5):.2f}")

    diff = (f5_yes/len(farthest_5)) - (c5_yes/len(closest_5))
    print(f"\nDifference: {diff:+.2f}")

    if diff > 0.3:
        print("→ Strong gradient. Distance matters. Lewis supported.")
    elif diff > 0.1:
        print("→ Moderate gradient. Some support for Lewis.")
    else:
        print("→ Weak gradient. Distance may not matter here.")

    # Find flip point
    print()
    for r in valid:
        if r["answer"] == 1:
            print(f"First CONFLICT at: population {r['population']} "
                  f"(distance {r['distance']:.3f})")
            break

    overall_cls = cumulative_yes / cumulative_total
    print(f"\nOverall conflict rate: {cumulative_yes}/{cumulative_total} = {overall_cls:.2f}")

    # Lewis's verdict
    if len(closest_5) > 0:
        inner_cls = c5_yes / len(closest_5)
        if inner_cls < 0.3:
            print(f"\nLEWIS'S VERDICT: The counterfactual 'rice field destroyed → conflict' is FALSE.")
            print(f"The closest worlds (inner sphere CLS = {inner_cls:.2f}) reject conflict.")
        elif inner_cls > 0.7:
            print(f"\nLEWIS'S VERDICT: The counterfactual 'rice field destroyed → conflict' is TRUE.")
            print(f"The closest worlds (inner sphere CLS = {inner_cls:.2f}) affirm conflict.")
        else:
            print(f"\nLEWIS'S VERDICT: The counterfactual is INDETERMINATE.")
            print(f"The closest worlds (inner sphere CLS = {inner_cls:.2f}) are split.")

    # Save summary
    summary = {
        "experiment": "Phase 1 — Conflict Version",
        "antecedent": "Rice field destroyed",
        "consequent": "Violent conflict breaks out",
        "total_worlds": len(worlds),
        "valid_responses": len(valid),
        "all_results": results,
    }
    summary_path = RESULTS_DIR / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved to {summary_path}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run_phase1()