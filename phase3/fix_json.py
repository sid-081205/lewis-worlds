"""
Fix results.json — re-parse any answer=-1 entries
by stripping punctuation from YES/NO responses.
"""

import json
from pathlib import Path

PHASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = PHASE_DIR / "results"
RESULTS_PATH = RESULTS_DIR / "results.json"


def parse_yes_no(text: str) -> int:
    lines = text.strip().split("\n")
    for line in reversed(lines):
        stripped = line.strip().strip(".,!;:\"'()").upper()
        if stripped == "NO":
            return 0
        elif stripped == "YES":
            return 1
    first_word = text.split()[0].strip(".,!:;\"'()").upper() if text.strip() else ""
    if first_word == "YES":
        return 1
    elif first_word == "NO":
        return 0
    for line in lines:
        s = line.strip().strip(".,!;:\"'()").upper()
        if s in ("YES", "NO"):
            return 1 if s == "YES" else 0
    return -1


def main():
    with open(RESULTS_PATH, "r") as f:
        data = json.load(f)

    fixed_count = 0
    still_broken = 0

    for cid, cdata in data["all_results"].items():
        for r in cdata["responses"]:
            if r["answer"] == -1 and r.get("full_response"):
                new_answer = parse_yes_no(r["full_response"])
                if new_answer in (0, 1):
                    r["answer"] = new_answer
                    fixed_count += 1
                else:
                    still_broken += 1
                    print(f"  still broken: {cid} {r['world_id']} pop={r['population']}: {r['full_response'][:100]}")

    # Recompute summary
    for s in data["summary"]:
        cid = s["id"]
        responses = data["all_results"][cid]["responses"]
        valid = [r for r in responses if r["answer"] in (0, 1)]
        valid.sort(key=lambda r: r["distance"])

        overall_cls = sum(r["answer"] for r in valid) / len(valid) if valid else 0

        closest = valid[:10]
        cls_inner = sum(r["answer"] for r in closest) / len(closest) if closest else 0

        farthest = valid[-10:]
        cls_outer = sum(r["answer"] for r in farthest) / len(farthest) if farthest else 0

        s["cls_overall"] = round(overall_cls, 4)
        s["cls_inner"] = round(cls_inner, 4)
        s["cls_outer"] = round(cls_outer, 4)
        s["gradient"] = round(cls_outer - cls_inner, 4)
        s["valid_count"] = len(valid)

    # Save
    with open(RESULTS_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nFixed {fixed_count} answers.")
    print(f"Still broken: {still_broken}")
    print(f"Saved updated {RESULTS_PATH}")


if __name__ == "__main__":
    main()
