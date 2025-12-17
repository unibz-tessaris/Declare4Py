# INFSYS 2025 submission experiments - RQ4

This directory includes the code for the experiments for the evaluation of RQ 4 of the INFSYS 2025 submission.

## Prerequisites

Install [Pixi](https://pixi.sh/latest/) package management tool. It's a single executable tool for managing [`conda` based](https://pixi.sh/latest/switching_from/conda/) environments (similar to `micromamba`). It can also be installed using different package managers, see [pixi package versions on Repology.org](https://repology.org/project/pixi/versions) for the available packages.

## Reproducing the Experiments

The code for the experiments is included in [Marimo](https://docs.marimo.io/) notebooks located in this directory. The output of the experiments is written in the [`results`](results/) directory.

To reproduce the experiments, run the following command:

```sh
pixi run experiment
```

which will execute the [`asp_generator.py`](asp_generator.py) notebook, writing the results of the generative process in the [`results/asp_generator_test_2025-IS`](results/asp_generator_test_2025-IS/) directory and the notebook output in [`results/asp_generator_test_2025-ISt.html`](results/asp_generator_test_2025-ISt.html). To test with a smaller set of parameters for a quicker run, you can use the command:

```sh
pixi run test_experiment
```

To run the analysis notebook, use the command:

```sh
pixi run analysis
```

which will open a notebook in a browser window.

The output of the experiment results included in the paper are in the [`results/asp_generator_2025-12`](results/asp_generator_2025-12/) directory, while the notebook output in the files ['results/asp_generator_2025-12.html'](results/asp_generator_2025-12.html) and [`results/asp_generator_2025-12_analysis.html`](results/asp_generator_2025-12_analysis.html).
