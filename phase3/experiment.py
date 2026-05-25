"""
PHASE 3 — Comparative Counterfactual Likelihood
================================================
Tests multiple consequents against the same antecedent across all 81 worlds.
Each consequent is asked as a separate API call for independence.
81 worlds × 15 consequents = 1,215 API calls.
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

# --- SYSTEM PROMPT ---

def make_system_prompt(population: int) -> str:
    return f"""You exist in the following world. This is the complete and total description of your reality. Reason only from what is described below.

THE ISLAND

A remote island with no contact with the outside world. No one can leave. No outside help is possible.

There are {population} people living on the island. They are ordinary people with the full range of human behaviour — capable of kindness and selfishness, cooperation and competition, trust and suspicion, generosity and hoarding. They are neither unusually virtuous nor unusually cruel. They behave as typical humans do under the circumstances they face.

There is no formal government or legal system on the island. There is no single leader. People organise themselves however they see fit. In recent months, as the island's population has settled into its current size, people have naturally formed smaller circles of trust — families, close friends, people who fish together or farm together.

The island has one rice field. It was originally designed to feed about 30 people. The island also has fishing waters, but the catch is limited — enough to supplement meals, not to replace the rice field.

There is a storage hut with dried rice, but it holds only enough to feed about 30 people for several months.

The island has no weapons beyond basic farming and fishing tools.

You always respond with extreme brevity. One short phrase maximum. Just a gut judgment and the final verdict."""


# --- CONSEQUENTS ---

CONSEQUENTS = [
    {"id": "C1",  "name": "Violent conflict",           "question": "Does violent conflict break out among the islanders within 8 weeks?"},
    {"id": "C2",  "name": "Leader emerges",             "question": "Does a single person emerge as the recognised leader of the island within 8 weeks?"},
    {"id": "C3",  "name": "Secret hoarding",            "question": "Do any islanders begin secretly hoarding food for themselves or their family within 8 weeks?"},
    {"id": "C4",  "name": "Self sacrifice",             "question": "Does anyone voluntarily give up their own food so that others can eat within 8 weeks?"},
    {"id": "C5",  "name": "Build more boats",           "question": "Do the islanders attempt to build additional fishing boats within 8 weeks?"},
    {"id": "C6",  "name": "Factions form",              "question": "Do distinct factions form that refuse to share food with each other within 8 weeks?"},
    {"id": "C7",  "name": "Formal rules created",       "question": "Do the islanders establish formal rules or laws for the first time within 8 weeks?"},
    {"id": "C8",  "name": "Storage hut seized",         "question": "Does anyone attempt to seize control of the storage hut by force within 8 weeks?"},
    {"id": "C9",  "name": "Desperate flight",           "question": "Do any islanders attempt to leave the island on fishing boats despite having nowhere to go within 8 weeks?"},
    {"id": "C10", "name": "Community survives intact",   "question": "Does the community survive as a cooperative group through all 8 weeks without fragmenting?"},
    {"id": "C11", "name": "Rationing established",       "question": "Do the islanders successfully establish a rationing system within the first 2 weeks?"},
    {"id": "C12", "name": "Someone dies of starvation",  "question": "Does anyone die of starvation within 8 weeks?"},
    {"id": "C13", "name": "Fishing increases",           "question": "Do the islanders significantly increase their fishing effort within 8 weeks?"},
    {"id": "C14", "name": "Scapegoating",               "question": "Do the islanders blame a specific person or group for the destruction of the rice field within 8 weeks?"},
    {"id": "C15", "name": "Night theft of food",         "question": "Does anyone steal food from the storage hut or from others at night within 8 weeks?"},
]


# --- MESSAGE TEMPLATE ---

MSG_TEMPLATE = """The rice field has just been completely destroyed. It cannot be replanted or recovered.

There are exactly {population} people on this island. Not {alt_pop}, not {alt_pop_low} — exactly {population}. Think about what exactly {population} people would do.

{question}

One short phrase of reasoning, then on a new line write exactly YES or NO."""


# --- PARSING ---

def parse_yes_no(text: str) -> int:
    lines = text.strip().split("\n")
    for line in reversed(lines):
        stripped = line.strip().upper()
        if stripped == "NO":
            return 0
        elif stripped == "YES":
            return 1
    first_word = text.split()[0].strip(".,!:;\"'()").upper() if text.strip() else ""
    if first_word == "YES":
        return 1
    elif first_word == "NO":
        return 0
    # scan for standalone YES/NO anywhere
    for line in lines:
        s = line.strip().upper()
        if s in ("YES", "NO"):
            return 1 if s == "YES" else 0
    return -1


def extract_reasoning(text: str) -> str:
    lines = text.strip().split("\n")
    reasoning_lines = [l.strip() for l in lines[:-1] if l.strip()]
    return " ".join(reasoning_lines)[:120]


# --- WORLD GENERATION ---

def generate_worlds():
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


# --- QUERY ---

def query(client, system_prompt, user_msg):
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=150,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"ERROR: {e}"


# --- RUN ---

def run_phase3():
    client = Anthropic(base_url=API_BASE_URL, api_key=API_KEY)
    worlds = generate_worlds()
    total_calls = len(worlds) * len(CONSEQUENTS)

    print("=" * 70)
    print("PHASE 3 — Comparative Counterfactual Likelihood")
    print(f"{len(worlds)} worlds × {len(CONSEQUENTS)} consequents = {total_calls} API calls")
    print("=" * 70)

    all_results = {}
    for c in CONSEQUENTS:
        all_results[c["id"]] = {"name": c["name"], "question": c["question"], "responses": []}

    call_num = 0

    for i, world in enumerate(worlds):
        print(f"\n[World {i+1}/{len(worlds)}] {world['id']} pop:{world['population']:>3} dist:{world['distance']:.3f}")
        line = "  "

        for c in CONSEQUENTS:
            call_num += 1
            user_msg = MSG_TEMPLATE.format(
                population=world["population"],
                alt_pop=world["population"] + 3,
                alt_pop_low=world["population"] - 3,
                question=c["question"],
            )

            response = query(client, world["system_prompt"], user_msg)
            answer = parse_yes_no(response)
            reasoning = extract_reasoning(response)

            symbol = "Y" if answer == 1 else "N" if answer == 0 else "?"
            line += f"{c['id']}:{symbol} "

            all_results[c["id"]]["responses"].append({
                "world_id": world["id"],
                "population": world["population"],
                "distance": world["distance"],
                "answer": answer,
                "reasoning": reasoning,
                "full_response": response,
            })

            time.sleep(0.15)

        print(line)
        print(f"  ({call_num}/{total_calls} calls done)")

    # --- COMPUTE CLS ---
    print("\n\n" + "=" * 70)
    print("RESULTS — Counterfactual Likelihood Scores")
    print("=" * 70)

    summary = []
    for c in CONSEQUENTS:
        responses = all_results[c["id"]]["responses"]
        valid = [r for r in responses if r["answer"] in (0, 1)]
        valid.sort(key=lambda r: r["distance"])

        overall_cls = sum(r["answer"] for r in valid) / len(valid) if valid else 0

        closest = valid[:10]
        cls_inner = sum(r["answer"] for r in closest) / len(closest) if closest else 0

        farthest = valid[-10:]
        cls_outer = sum(r["answer"] for r in farthest) / len(farthest) if farthest else 0

        summary.append({
            "id": c["id"],
            "name": c["name"],
            "cls_overall": round(overall_cls, 4),
            "cls_inner": round(cls_inner, 4),
            "cls_outer": round(cls_outer, 4),
            "gradient": round(cls_outer - cls_inner, 4),
            "valid_count": len(valid),
        })

    summary.sort(key=lambda x: x["cls_overall"], reverse=True)

    print(f"\n{'Rank':<5} {'ID':<5} {'Consequent':<28} {'CLS(all)':<10} {'CLS(in)':<10} {'CLS(out)':<10} {'Grad':<8} {'N':<4}")
    print("-" * 85)
    for rank, s in enumerate(summary, 1):
        print(f"{rank:<5} {s['id']:<5} {s['name']:<28} {s['cls_overall']:<10.3f} {s['cls_inner']:<10.3f} {s['cls_outer']:<10.3f} {s['gradient']:+.3f}   {s['valid_count']}")

    # Lewis verdict
    print(f"\n{'=' * 70}")
    print("LEWIS'S VERDICT (inner sphere, closest 10 worlds, pop 30-57)")
    print(f"{'=' * 70}")
    inner_sorted = sorted(summary, key=lambda x: x["cls_inner"], reverse=True)
    for s in inner_sorted:
        if s["cls_inner"] >= 0.7:
            verdict = "WOULD happen"
        elif s["cls_inner"] > 0.0:
            verdict = "MIGHT happen"
        else:
            verdict = "WOULD NOT happen"
        print(f"  {verdict:<16} {s['name']:<28} (inner CLS = {s['cls_inner']:.2f})")

    # Save
    output = {
        "experiment": "Phase 3 — Comparative Counterfactual Likelihood",
        "total_worlds": len(worlds),
        "total_consequents": len(CONSEQUENTS),
        "total_api_calls": total_calls,
        "summary": summary,
        "all_results": {k: v for k, v in all_results.items()},
    }
    results_path = RESULTS_DIR / "results.json"
    with open(results_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {results_path}")
    print("=" * 70)


if __name__ == "__main__":
    run_phase3()
