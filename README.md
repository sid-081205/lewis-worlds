# lewis counterfactual experiment

tests whether counterfactuals track closest possible worlds (phase 1), then lewis's three fallacies: strengthening, transitivity, contraposition (phase 2).

## setup

```bash
pip install -r requirements.txt
```

local api proxy at http://localhost:8001

## phase 1

```bash
python phase1/experiment.py
python phase1/visualize.py
```

81 worlds, conflict rate vs distance from the actual world.

## phase 2

```bash
python phase2/experiment.py
python phase2/visualize.py
python phase2/significance.py
```

results go to each phase's `results/` and `plots/` folders.
