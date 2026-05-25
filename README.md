# lewis counterfactual experiment

tests whether counterfactuals track closest possible worlds (phase 1), then lewis's three fallacies: strengthening, transitivity, contraposition (phase 2).

## setup

```bash
pip install -r requirements.txt
```

i set up my local api proxy at http://localhost:8001, you can set your anthropic api key instead in the code instead.

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

## phase 3

```bash
python phase3/experiment.py
python phase3/visualize.py
python phase3/advanced_viz.py
python phase3/lewis_difference.py
```

15 consequents × 81 worlds. live explorer: https://lewis-worlds.vercel.app

redeploy: `vercel deploy --prod`
