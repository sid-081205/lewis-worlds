"""
Phase 2b — Transitivity graph
Reads phase2_results.json, outputs one clean chart.
"""

import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


def load_results():
    with open("phase2/results/results.json", "r") as f:
        return json.load(f)


def compute_cumulative_cls(results):
    valid = sorted([r for r in results if r['answer'] in (0, 1)], key=lambda r: r['distance'])
    cum_yes, cum_total = 0, 0
    distances, cls_vals = [], []
    for r in valid:
        cum_total += 1
        cum_yes += r['answer']
        distances.append(r['distance'])
        cls_vals.append(cum_yes / cum_total)
    return distances, cls_vals


data = load_results()

d1, c1 = compute_cumulative_cls(data['2b']['run1'])
d2, c2 = compute_cumulative_cls(data['2b']['run2'])
d3, c3 = compute_cumulative_cls(data['2b']['run3'])

fig, ax = plt.subplots(figsize=(12, 6))

ax.plot(d1, c1, color='#457B9D', linewidth=2.5, label=f'A→B: destruction → rationing (CLS = {data["2b"]["cls_ab"]:.2f})')
ax.plot(d2, c2, color='#2A9D8F', linewidth=2.5, label=f'B→C: rationing → resentment (CLS = {data["2b"]["cls_bc"]:.2f})')
ax.plot(d3, c3, color='#E63946', linewidth=2.5, label=f'A→C: destruction → resentment (CLS = {data["2b"]["cls_ac"]:.2f})')

ax.axhline(y=0.5, color='#999', linestyle=':', alpha=0.4)
ax.set_xlabel('sphere radius r', fontsize=11)
ax.set_ylabel('cumulative CLS within sphere S(r)', fontsize=11)
ax.set_title('test 2b: transitivity', fontsize=13, fontweight='bold')
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.05, 1.05)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.2)

plt.tight_layout()
plt.savefig('phase2/plots/phase2b_transitivity.png', dpi=150)
print('saved: phase2b_transitivity.png')