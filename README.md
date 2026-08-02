# lewis counterfactual experiment

this codebase accompanies my blog post on testing david lewis's theory of counterfactuals with claude:

**[counterfactuals and claude](https://sid081205.substack.com/p/counterfactuals-and-claude)**

## what this is

i build a fake island world and 81 "possible worlds" that differ only in population (30 to 270). in each world i put the same language model behind a system prompt that fully describes that world, then ask counterfactual questions: *if the rice field were destroyed, would X happen?*

the goal is to operationalise lewis's idea that counterfactuals are fixed by what happens in the **closest** possible worlds — and to see where that breaks down.

each phase writes results to its own `results/` folder. phase 1 and 2 also have `visualize.py` scripts that save plots to `plots/`. phase 3 analysis lives in the notebook. paths are relative to the script, so run from the repo root.

## phases

**phase 1 — closest worlds.** one consequent (violent conflict) across all 81 worlds. measures whether the conflict rate changes as you expand the similarity sphere outward from the actual world (pop 30).

**phase 2 — lewis's three fallacies.** tests strengthening the antecedent, transitivity, and contraposition. if the model behaves lewisianly, these inference patterns should fail in predictable ways.

**phase 3 — comparative likelihood.** 15 consequents × 81 worlds (1,215 api calls). `experiment.py` collects responses into `results/results.json`. analysis and figures are in `phase3_notebook.ipynb`. `explorer.html` is an interactive viewer for the results (serve locally from `phase3/`).

## setup

```bash
pip install -r requirements.txt
```

## phase 1

```bash
python phase1/experiment.py
python phase1/visualize.py
```

## phase 2

```bash
python phase2/experiment.py
python phase2/visualize.py
python phase2/significance.py
```

## phase 3

```bash
python phase3/experiment.py          # 1,215 api calls → results/results.json
```

then open `phase3/phase3_notebook.ipynb` and run all cells for plots and analysis.

interactive explorer:

```bash
cd phase3 && python -m http.server
# then open http://localhost:8000/explorer.html
```
