# Variability experiments

This directory includes the code for the experiments for the evaluation of the ASP based techniques to generate diverse logs.

## Prerequisites

Install [Pixi](https://pixi.sh/latest/) package management tool. It's a single executable tool for managing [`conda` based](https://pixi.sh/latest/switching_from/conda/) environments (similar to `micromamba`). It can also be installed using different package managers, see [pixi package versions on Repology.org](https://repology.org/project/pixi/versions) for the available packages.

## Experiments

The experiments can be run by evaluating the included Jypyter notebooks. Results are written in the [`output`](output/) directory (see the notebooks for details).

To execute and convert a notebook to html use the command `pixi run experiments`; the output will be written in the `./output` directory. The `analysis.ipynb` notebook summarises and aggregates the results of the experiments.
