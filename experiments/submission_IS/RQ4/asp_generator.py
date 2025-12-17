#! /usr/bin/env python

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    import itertools
    import json
    import os
    import sys
    from pathlib import Path
    from typing import Iterable, Sequence, Hashable, Optional
    from numbers import Number
    import time

    from Declare4Py.ProcessModels.DeclareModel import DeclareModel
    from Declare4Py.ProcessMiningTasks.LogGenerator.ASP.ASPLogGenerator import AspGenerator
    from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedLogGeneratorNG import PBLogGeneratorBaseline, PBLogGeneratorRandom

    import Levenshtein as Lev
    import pm4py
    import polars as pl
    return (
        AspGenerator,
        DeclareModel,
        Hashable,
        Iterable,
        Lev,
        Number,
        Optional,
        Path,
        Sequence,
        itertools,
        json,
        mo,
        pl,
        pm4py,
        time,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Clingo Configurations for Log Generation

    This document compares different configurations for the [`clingo`](https://potassco.org/clingo/) solver, used in the ASP based log generator of [`Declare4Py`](https://github.com/ivanDonadello/Declare4Py/tree/main) package (more details on [`9.1.ASP_Log_Generation.ipynb`](https://github.com/ivanDonadello/Declare4Py/blob/main/docs/source/tutorials/9.1.ASP_Log_Generation.ipynb) tutorial).

    For the test it uses Declare models extracted from real logs, below the set of data for the experiments in JSON format. Each element include:
    - **xes**: the original log
    - **declare**: the Declare model extracted
    - **targets**: list of pairs with the number of traces and lenght of each trace to be generated
    - **clingo_config**: the clingo configuration to be used, each `id` corresponds to a different configuration:
        - `default`: uses `clingo` defaults
        - `ASPlog`: the default configuration of [`Declare4Py`](https://github.com/ivanDonadello/Declare4Py/blob/main/docs/source/tutorials/9.1.ASP_Log_Generation.ipynb)

    The output (including generated XES log files) is written in a directory with a timestamp in the `results` directory:
    - `datasets.json` the datasets below
    - `asp_log_generation_results.parquet` the summary table in [Parquet](https://parquet.apache.org/) format
    - one XES file for each test id with all generated traces
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Notebook parameters:
    """)
    return


@app.cell
def _():
    from dataclasses import dataclass, asdict
    from datetime import datetime
    from simple_parsing import ArgumentParser

    parser = ArgumentParser()

    @dataclass
    class Parameters:
        """Notebook parameters."""

        nb_name: str = 'asp_generator' # name of the notebook
        result_dir: str|None = None         # name to use for the output directory, default to name + timestamp
        export: bool = True                 # True to write the logs and summary table in the results directory

        def __post_init__(self):
            if self.result_dir is None:
                self.result_dir = (self.nb_name + '_' + datetime.now().strftime('%Y-%m-%dT%H%M%S'))


    parser.add_arguments(Parameters, dest="parameters")

    nb_parameters = parser.parse_args().parameters

    asdict(nb_parameters)
    return (nb_parameters,)


@app.cell
def _(Path, json, mo, nb_parameters):

    # True to write the logs and summary table in the results directory
    EXPORT_RESULTS = nb_parameters.export

    NOTEBOOK_DIR = mo.notebook_dir()
    mo.stop(NOTEBOOK_DIR is None, mo.md("**Cannot determine the running directory**"))

    DATASETS_PATH = NOTEBOOK_DIR / 'Datasets'
    DECLARE_MODELS_PATH = DATASETS_PATH / "declare"
    OUTPUT_DIR = NOTEBOOK_DIR / nb_parameters.result_dir

    mo.stop(not DATASETS_PATH.exists(), mo.md(f"**Datasets path missing:** `{DATASETS_PATH.as_posix()}`"))
    mo.stop(not DECLARE_MODELS_PATH.exists(), mo.md(f"**Declare models path missing:** `{DECLARE_MODELS_PATH.as_posix()}`"))

    if EXPORT_RESULTS:
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    CLINGO_CONFIGURATIONS = {
        # clingo defaults
        'default': {"CONFIG": None, "THREADS": None, "FREQUENCY": None, "SIGN-DEF": None, "MODE": None, "STRATEGY": None, "HEURISTIC": None},
        # default configuration, see <https://github.com/unibz-tessaris/Declare4Py/blob/99b7a8146359d104ec32bb2af3d3401dc25ea8f4/Declare4Py/ProcessMiningTasks/LogGenerator/ASP/ASPLogGenerator.py#L84>
        # 'ASPlog': {"CONFIG": "trendy", "THREADS": str(os.cpu_count()), "FREQUENCY": "0.3", "SIGN-DEF": "asp", "MODE": "optN", "STRATEGY": None, "HEURISTIC": None},
        'ASPlog': {}
    }

    DATASETS = {
        'bpic15_municipality_1': {
            'xes': DATASETS_PATH / 'BPIC15_Municipality_1.xes',
            'declare': DECLARE_MODELS_PATH / 'BPIC15_Municipality_1.decl',
            'targets': [(72, 40), (28, 51), (30,13), (17,62)], # (size, length)
            'clingo_config': CLINGO_CONFIGURATIONS
        },
        'bpi_challenge_2012': {
            'xes': DATASETS_PATH / 'BPI_Challenge_2012.xes.gz',
            'declare': DECLARE_MODELS_PATH / 'BPI_Challenge_2012.xes.decl',
            'targets': [(361,10), (222,20), (207,30), (116,40), (82,50), (46,60)], # (size, length)
            'clingo_config': CLINGO_CONFIGURATIONS
        },
        'sepsis_cases': {
            'xes': DATASETS_PATH / 'Sepsis Cases - Event Log.xes.gz',
            'declare': DECLARE_MODELS_PATH / 'Sepsis Cases - Event Log.xes.decl',
            'targets': [(50,10), (19,20)], # (size, length)
            'clingo_config': CLINGO_CONFIGURATIONS
        },
        'bpic15_municipality_1_abs3choice': {
            'xes': DATASETS_PATH / 'BPIC15_Municipality_1.xes',
            'declare': DECLARE_MODELS_PATH / 'BPIC15_Municipality_1_ABS3CHOICE.decl',
            'targets': [(72, 40), (28, 51), (30,13), (17,62)], # (size, length)
            'clingo_config': CLINGO_CONFIGURATIONS
        },
        'bpi_challenge_2012_abs3choice': {
            'xes': DATASETS_PATH / 'BPI_Challenge_2012.xes.gz',
            'declare': DECLARE_MODELS_PATH / 'BPI_Challenge_2012_ABS3CHOICE.xes.decl',
            'targets': [(361,10), (222,20), (207,30), (116,40), (82,50), (46,60)], # (size, length)
            'clingo_config': CLINGO_CONFIGURATIONS
        },
        'sepsis_cases_abs3choice': {
            'xes': DECLARE_MODELS_PATH / 'Sepsis Cases - Event Log.xes.gz',
            'declare': DECLARE_MODELS_PATH / 'Sepsis Cases - Event Log.xesABS3CHOICE.decl',
            'targets': [(50,10), (19,20)], # (size, length)
            'clingo_config': CLINGO_CONFIGURATIONS
        }
    }

    def custom_json_serializer(obj):
        if isinstance(obj, Path):
            return obj.relative_to(NOTEBOOK_DIR, walk_up=True).as_posix()
        raise TypeError(f"Type {type(obj)} not serializable")

    DATASETS_JSON = json.dumps(DATASETS, default=custom_json_serializer)
    if EXPORT_RESULTS:
        with open(OUTPUT_DIR / 'datasets.json', 'w') as f:
            f.write(DATASETS_JSON)
    mo.json(DATASETS_JSON)
    return DATASETS, EXPORT_RESULTS, NOTEBOOK_DIR, OUTPUT_DIR


@app.cell(hide_code=True)
def _(NOTEBOOK_DIR, OUTPUT_DIR, mo):
    mo.md(f"""
    Results files written in [`{OUTPUT_DIR.relative_to(NOTEBOOK_DIR, walk_up=True).as_posix()}`](`{OUTPUT_DIR.relative_to(NOTEBOOK_DIR, walk_up=True).as_posix()}`)
    """)
    return


@app.cell
def _(AspGenerator, DeclareModel, Iterable, Path, pm4py, time):
    def generate_log(model: DeclareModel|Path, traces: int, length: int, clingo_conf: dict[str] = {}) -> tuple[pm4py.objects.log.obj.EventLog, int, dict[str,str]]:
        decl_mdl = model if isinstance(model, DeclareModel) else DeclareModel().parse_from_file(filename=model.as_posix())
        asp_gen = AspGenerator(decl_model=decl_mdl,num_traces=traces,min_event=length,max_event=length,verbose=False)
        current_config = asp_gen.get_current_clingo_configuration()
        for k, v in clingo_conf.items():
            if k in current_config:
                current_config[k] = v
            asp_gen.custom_configuration = current_config
            asp_gen.use_custom_clingo_config = True
        start_time = time.perf_counter_ns()
        asp_gen.run()
        elapsed = time.perf_counter_ns() - start_time
        # consider only positive traces
        data = {'positive': asp_gen.traces_generated_events['positive']}
        return asp_gen.toEventLog(data=data), elapsed, asp_gen.get_current_clingo_configuration()

    def logToTraces(log: pm4py.objects.log.obj.EventLog) -> Iterable[tuple[str]]:
        for trace in log:
            yield tuple(e['concept:name'] for e in trace)
    return generate_log, logToTraces


@app.cell
def _(Hashable, Iterable, Lev, Number, Optional, Sequence, itertools, pl):
    DEFAULT_DIST = Lev.distance

    def  pairwise_distances(traces: Iterable[Sequence[Hashable]],
                            distance: Optional[callable]=None,
                            norm_value: int = 1) -> pl.Series:
        distance = distance or DEFAULT_DIST
        return pl.Series(distance(t1, t2)/norm_value for t1,t2 in itertools.combinations(traces, 2))

    def series_stats(series: pl.Series, prefix: str = '') -> dict[str, Number]:
        return {
            prefix + 'mean': series.mean(),
            prefix + 'median': series.median(),
            prefix + 'std': series.std(),
            prefix + 'max': series.max(),
            prefix + 'min': series.min(),
            prefix + 'size': series.count()
        }
    return pairwise_distances, series_stats


@app.cell
def _(
    DeclareModel,
    Iterable,
    Optional,
    Path,
    generate_log,
    logToTraces,
    pairwise_distances,
    pl,
    pm4py,
    series_stats,
):
    def generate_full_log(log_id: str, model: DeclareModel, target_sizes: Iterable[tuple[int, int]], conf_id: str, clingo_conf: dict[str] = {}) -> tuple[pm4py.objects.log.obj.EventLog, list[dict[str]]]:
        results: list[dict] = []
        full_log = pm4py.objects.log.obj.EventLog()
        elapsed_total = 0
        for i, (size, length) in enumerate(target_sizes):
            log, elapsed, configuration = generate_log(model,traces=size, length=length, clingo_conf=clingo_conf)
            elapsed_total += elapsed
            for j, trace in enumerate(log):
                # make sure each trace has a unique id
                trace.attributes['concept:name'] = f'case_{i}_{j}'
                full_log.append(trace)
            distances = pairwise_distances(logToTraces(log),norm_value=length)
            results.append({
                'id': log_id,
                'clingo': conf_id,
                'size': len(log),
                'length': length,
                'time_ns': elapsed,
                **series_stats(distances, prefix='distance_'),
                'clingo_configuration': configuration
            })
        if len(results) > 1:
            distances = pairwise_distances(logToTraces(full_log), norm_value=max(t[1] for t in target_sizes))
            results.append({
                'id': log_id,
                'clingo': conf_id,
                'size': len(full_log),
                'time_ns': elapsed,
                **series_stats(distances, prefix='distance_'),
                'clingo_configuration': configuration
            })
        return full_log, results


    def asp_logs(datasets: dict[str, dict], output_path: Optional[Path]=None) -> pl.DataFrame:
        results: list[dict] = []
        for id, data in datasets.items():
            model = DeclareModel().parse_from_file(data['declare'].as_posix())
            elapsed_total = 0
            for conf_name, clingo_conf in data.get('clingo_config', {'default': {}}).items():
                full_log, results_partial = generate_full_log(id, model, data['targets'], conf_name, clingo_conf)
                results.extend(results_partial)
                if output_path is not None:
                    pm4py.write_xes(full_log, file_path=output_path / f'{id}_{conf_name}.xes')
        summarized_results = pl.DataFrame(results)
        if output_path:
            summarized_results.write_parquet(output_path / 'results.parquet')
            summarized_results.write_json(output_path / 'results.json')
        return summarized_results
    return (asp_logs,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The summary table includes the data:
    - `id`: the test id
    - `clingo`: the id of the clingo configuration
    - `size`: the number of traces in the dataset
    - `length`: the length of each trace, if null includes traces of different length
    - `time_ns`: the generation time in nanoseconds
    - `distance_mean`: average (normalised) Levenshtein distance
    - `distance_median`: median (normalised) Levenshtein distance
    - `distance_std`: standard deviation of (normalised) Levenshtein distances
    - `distance_max`: maximum among (normalised) Levenshtein distances
    - `distance_min`: minimum among (normalised) Levenshtein distances
    - `distance_size`: number of pairs of different traces
    - `clingo_configuration`: detailed `clingo` configuration used for the generation
    """)
    return


@app.cell
def _(DATASETS, EXPORT_RESULTS, OUTPUT_DIR, asp_logs, mo):
    summary_df = asp_logs(DATASETS, output_path=OUTPUT_DIR if EXPORT_RESULTS else None)
    mo.ui.table(summary_df, pagination=False)
    return


if __name__ == "__main__":
    app.run()
