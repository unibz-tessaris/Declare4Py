# CAiSE 2025 experiments

This directory includes the code for the experiments for the CAiSE 2025 submission.

## Prerequisites

Install [Pixi](https://pixi.sh/latest/) package management tool. It's a single executable tool for managing [`conda` based](https://pixi.sh/latest/switching_from/conda/) environments (similar to `micromamba`). It can also be installed using different package managers, see [pixi package versions on Repology.org](https://repology.org/project/pixi/versions) for the available packages.

## Experiments

The experiments can be run by evaluating the included Jypyter notebooks. Results are written in the [`output`](output/) directory (see the notebooks for details).

To execute and convert a notebook to html use the command `pixi run notebook_file_name.ipynb`; alternatively, you can use the JupyterLab interface with the `pixi run lab` command.

- [`caise2025 experiment original.ipynb`](caise2025%20experiment%20original.ipynb): generates a set of positive logs using the original code as available on [commit 481fcbf](https://github.com/ivanDonadello/Declare4Py/commit/481fcbff26130c5442dea7f12296aa0e7947ca9c) (branch [`v1.0.1/refactor-architecture-zorzi`](https://github.com/pandamarty/declare4py-v2.0/compare/main...ivanDonadello:Declare4Py:v1.0.1/refactor-architecture-zorzi)).
