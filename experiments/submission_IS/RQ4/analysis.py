#!/usr/bin/env python

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium", auto_download=["html", "ipynb"])


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Analysis of variability in process logs

    This document presents the varability analysis of process logs. See the `DATASETS` variable for the details on the datasets.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pm4py
    import Levenshtein
    import pandas as pd
    import polars as pl
    import altair as alt

    from dataclasses import dataclass
    import itertools
    import json
    from numbers import Number
    from pathlib import Path
    from typing import Any, NamedTuple, Iterable, Sequence, Hashable, Callable, Optional, TypeAlias
    return (
        Any,
        Callable,
        Hashable,
        Iterable,
        Levenshtein,
        Number,
        Optional,
        Path,
        Sequence,
        TypeAlias,
        alt,
        dataclass,
        itertools,
        json,
        mo,
        pd,
        pl,
        pm4py,
    )


@app.cell
def _(dataclass):
    from dataclasses import fields
    from datetime import datetime
    from simple_parsing import ArgumentParser

    _parser = ArgumentParser()

    @dataclass
    class Parameters:
        """Notebook parameters."""

        result_dir: str = 'results/asp_generator_2025-12'  # directory with the results to analyse

    _parser.add_arguments(Parameters, dest="parameters")

    nb_parameters = _parser.parse_args().parameters

    {field.name: getattr(nb_parameters, field.name) for field in fields(nb_parameters)}
    return (nb_parameters,)


@app.cell
def _(Any, Iterable, Number, dataclass, pd, pl):
    @dataclass
    class Stats:
        datapoints: int
        mean: float
        median: float
        std: float
        min: float
        max: float

        def row(self, **kwargs) -> dict[str, Any]:
            return kwargs | {
                'mean': self.mean,
                'median': self.median,
                'std': self.std,
                'min': self.min,
                'max': self.max,
                'datapoints': self.datapoints
            }

    def sequence_stats(data: Iterable[Number] | pl.Series | pd.Series) -> Stats:
        if isinstance(data, (pl.Series, pd.Series)) :
            series = data
        else:
            series = pl.Series(data)
        return Stats(
            datapoints=series.len(),
            mean=series.mean(),
            median=series.median(),
            std=series.std(),
            min=series.min(),
            max=series.max(),
        )
    return (sequence_stats,)


@app.cell
def _(Path, Sequence, json, nb_parameters):
    def results_to_datasets(results_path: Path, datasets_groups: Sequence[str] = []) -> dict[str]:
        datasets = {}
        datasets_file = results_path / 'datasets.json'
        if datasets_file.exists():
            with datasets_file.open() as fd:
                dataset_results: dict[str] = json.load(fd)
            for id, data in dataset_results.items():
                filter_length = [t[1] for t in data['targets']]
                for clingo_conf in data.get('clingo_config', {}).keys():
                    dataset_id = f'{id}_{clingo_conf}'
                    datasets[dataset_id] = {
                        'path': results_path.as_posix(),
                        'xes': f'{id}_{clingo_conf}.xes',
                        'generator': f'asp_{clingo_conf}'
                        # 'filter_length': filter_length
                    }
                    for dataset_group in datasets_groups:
                        if id.startswith(dataset_group):
                            datasets[dataset_id]['dataset'] = dataset_group
                            break
        return datasets

    DATASETS_GROUPS = {
        '2025-11-10_flexible_log_gen' : {
            "bpic15_municipality_1": {
                "path": "Datasets",
                "xes": "BPIC15_Municipality_1.xes",
                "dataset": "bpic15_municipality_1",
                "generator": "real"
            },
            "bpi_challenge_2012": {
                "path": "Datasets",
                "xes": "BPI_Challenge_2012.xes.gz",
                "dataset": "bpi_challenge_2012",
                "generator": "real"
            },
            "hospital": {
                "path": "Datasets",
                "xes": "Hospital_log.xes.gz",
                "dataset": "hospital",
                "generator": "real"
            },
            "sepsis_cases": {
                "path": "Datasets",
                "xes": "Sepsis Cases - Event Log.xes.gz",
                "dataset": "sepsis_cases",
                "generator": "real"
            }
        },
        'experiments_2025-12': {
            "bpic15_municipality_1_real": {
                "path": "Datasets",
                "xes": "BPIC15_Municipality_1.xes",
                "dataset": "bpic15_municipality_1",
                "generator": "real",
                "filter_length": [40, 51, 13, 62]
            },
            "bpi_challenge_2012_real": {
                "path": "Datasets",
                "xes": "BPI_Challenge_2012.xes.gz",
                "dataset": "bpi_challenge_2012",
                "generator": "real",
                "filter_length": [10, 20, 30, 40, 50, 60]
            },
            "sepsis_cases_real": {
                "path": "Datasets",
                "xes": "Sepsis Cases - Event Log.xes.gz",
                "dataset": "sepsis_cases",
                "generator": "real",
                "filter_length": [10, 20]
            }
        },
        "generators": {
            "bpic15_municipality_1_abs3choice_alloy": {
                "path": "Datasets/generators/BPIC15_Municipality_1_ABS3CHOICE 1",
                "xes": "BPIC15_Municipality_1_ABS3CHOICE 1_ALLOY.xes",
                "dataset": "bpic15_municipality_1",
                "generator": "alloy",
            },
            "bpi_challenge_2012_abs3choice_alloy": {
                "path": "Datasets/generators/BPI_Challenge_2012_ABS3CHOICE",
                "xes": "BPI_Challenge_2012_ABS3CHOICE_ALLOY.xes",
                "generator": "alloy",
                "dataset": "bpi_challenge_2012"
            },
            "bpi_challenge_2012_abs3choice_minerful": {
                "path": "Datasets/generators/BPI_Challenge_2012_ABS3CHOICE",
                "xes": "BPI_Challenge_2012_ABS3CHOICE_MINERFUL.xes",
                "generator": "minerful",
                "dataset": "bpi_challenge_2012"
            },
            "sepsis_cases_abs3choice_alloy": {
                "path": "Datasets/generators/Sepsis Cases - Event Log.xesABS3CHOICE",
                "xes": "Sepsis Cases - Event Log.xesABS3CHOICE_ALLOY.xes",
                "generator": "alloy",
                "dataset": "sepsis_cases"
            },
            "sepsis_cases_abs3choice_minerful": {
                "path": "Datasets/generators/Sepsis Cases - Event Log.xesABS3CHOICE",
                "xes": "Sepsis Cases - Event Log.xesABS3CHOICE_MINERFUL.xes",
                "generator": "minerful",
                "dataset": "sepsis_cases"
            }
        }
    }

    DATASETS = results_to_datasets(Path(nb_parameters.result_dir), datasets_groups=["bpic15_municipality_1", "bpi_challenge_2012", "sepsis_cases"]) | DATASETS_GROUPS['experiments_2025-12'] | DATASETS_GROUPS['generators']
    return (DATASETS,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The list of datasets:
    """)
    return


@app.cell
def _(DATASETS, mo, pl):
    DATASETS_DF = pl.DataFrame(data=[{'id': id} | data for id, data in DATASETS.items()])

    mo.ui.tabs({
        dataset[0]: data.
            select(pl.exclude('dataset')).
            sort(by='id')
        for dataset, data in DATASETS_DF.group_by('dataset')
    })
    return (DATASETS_DF,)


@app.cell
def _(DATASETS, Iterable, Optional, Path, TypeAlias, pd, pm4py):
    PLogs: TypeAlias = Iterable[tuple[str]]

    def read_log(xes: Path|str) -> pd.DataFrame:
        if isinstance(xes, Path):
            xes_path = xes
        else:
            assert xes in DATASETS
            xes_path = Path() / DATASETS[xes]['path'] / DATASETS[xes]['xes']
        return pm4py.read_xes(xes_path.as_posix())

    def log_to_traces(log: pd.DataFrame, filter_length: Optional[int] = None) -> PLogs:
        for trace in pm4py.convert_to_event_log(log):
            if filter_length is None or len(trace) in filter_length:
                yield tuple(e['concept:name'] for e in trace)

    def read_traces(xes: Path|str, filter_length: Optional[int] = None) -> PLogs:
        return log_to_traces(read_log(xes), filter_length=filter_length)
    return PLogs, read_traces


@app.cell
def _(DATASETS, Path, read_traces):
    TRACES = {lid: list(read_traces(Path() / data['path'] / data['xes'], filter_length=data.get('filter_length', None))) for lid, data in DATASETS.items() if Path(data['path']).joinpath(data['xes']).exists()}
    return (TRACES,)


@app.cell
def _(PLogs: "TypeAlias"):
    def trace_variants(traces: PLogs) -> dict[tuple[str], int]:
        variant_counts = {}
        for trace in traces:
            if trace in variant_counts:
                variant_counts[trace] += 1
            else:
                variant_counts[trace] = 1
        return variant_counts

    def traces_by_length(traces: PLogs) -> dict[int, list[tuple[str]]]:
        trace_buckets = {}
        for trace in traces:
            length = len(trace)
            if length in trace_buckets:
                trace_buckets[length].append(trace)
            else:
                trace_buckets[length] = [trace]
        return trace_buckets

    def padded_traces(traces: PLogs, size: int, pad_symbol: str = '<PAD>', skip_long: bool = True) -> PLogs:
        for trace in traces:
            if len(trace) > size and not skip_long:
                yield trace[:size]
            else:
                yield trace + (pad_symbol,) * (size - len(trace))
    return padded_traces, trace_variants, traces_by_length


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Show the statistics about the length of traces in each log.
    """)
    return


@app.cell
def _(DATASETS, TRACES, mo, pl, sequence_stats, trace_variants):

    mo.ui.tabs({
        dataset[0]: data.
            select(pl.exclude('dataset')).
            sort(by='id')
        for dataset, data in pl.DataFrame(sequence_stats(len(trace) for trace in traces).row(id=lid, dataset=DATASETS[lid].get('dataset', None), size=len(traces), variants=len(trace_variants(traces))) for lid, traces in TRACES.items()).group_by('dataset')
    })
    return


@app.cell
def _(PLogs: "TypeAlias", alt, pl):
    def length_frequency_chart(traces: PLogs, binned: bool = False) -> alt.Chart:
        data = pl.DataFrame({'length': [len(t) for t in traces]})
        base = alt.Chart(data)
        return (
            base.mark_bar()
                .encode(
                    alt.X('length:Q', bin=binned, title='Lenght of trace'),
                    alt.Y('count():Q', title='Frequency'),
                ) +
            # base.mark_rule().encode(
            #     x='mean(length)'
            # ) +
            base.mark_rule().encode(
                x='median(length)'
            )
        )

    def dataset_length_chart(traces: PLogs, title: str) -> alt.Chart:
        return alt.hconcat(
            length_frequency_chart(traces).properties(name=f'{title}_freq'),
            length_frequency_chart(traces, binned=True).properties(name=f'{title}_freq_bin')
        ).properties(title=title)
    return (dataset_length_chart,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The following charts show the lengths distribution for the different datasets.
    """)
    return


@app.cell
def _(DATASETS_DF, TRACES, alt, dataset_length_chart, mo):
    mo.ui.tabs({
        dataset: alt.vconcat(*(dataset_length_chart(TRACES[id], id) for id in sorted(df['id']) if id in TRACES))
        for (dataset,), df in DATASETS_DF.group_by('dataset')
    })
    return


@app.cell
def _(
    Callable,
    Hashable,
    Iterable,
    Levenshtein,
    Optional,
    PLogs: "TypeAlias",
    Sequence,
    TypeAlias,
    itertools,
    padded_traces,
    pl,
    traces_by_length,
):
    DistanceFN: TypeAlias = Callable[[Sequence[Hashable], Sequence[Hashable]], int]
    DEFAULT_DIST: DistanceFN = Levenshtein.distance

    def pairwise_distances(traces: Iterable[Sequence[Hashable]], distance: Optional[DistanceFN]=None, norm_value: int = 1) -> pl.Series:
        distance = distance or DEFAULT_DIST
        traces_seq = traces if isinstance(traces, Sequence) else list(traces)
        return pl.Series(distance(traces_seq[i], traces_seq[j])/norm_value
                         for i,j in itertools.combinations(range(len(traces_seq)), 2))

    def log_distances(traces: PLogs, distance: Optional[DistanceFN]=None, normalise: bool=False) -> pl.Series:
        if normalise:
            traces = traces if isinstance(traces, Sequence) else list(traces)
            norm_value = max(len(t) for t in traces)
        else:
            norm_value = 1
        return pairwise_distances(traces, distance=distance, norm_value=norm_value)

    def simple_distances(traces: PLogs, normalise: bool = True, distance: Optional[DistanceFN]=None) -> pl.Series:
        """
        Computes the distances for each pair of traces using the given distance function. For normalisation, it uses the maximum length among the traces.

        Parameters:
        -----------
        traces : PLogs
            A sequence of traces.

        normalise : bool, optional
            A boolean flag indicating whether to normalize the distance values. Defaults to True.

        distance : DistanceFN, optional
            A function that compute the distance between two sequences as an integer. The function should be able to compare sequences of different length. Uses `pairwise_distances` default unless specified.

        Returns:
        --------
        Series
            A Polar Series with all the distances between traces.

        Notes:
        ------
        This function utilizes the `pairwise_distances` function to calculate pairwise distances among log traces and then derives statistical metrics from those distances.
        """
        return log_distances(traces, distance=distance, normalise=normalise)

    def padded_distances(traces: PLogs, padding: Optional[int] = None, distance: Optional[DistanceFN]=None, normalise: bool = True) -> pl.Series:
        """
        Computes the distances for each pair of padded traces using the given distance function. For normalization, it uses the padded length.

        Parameters:
        -----------
        traces : PLogs
            A sequence of traces.

        padding : int, optional
            The length of each padded trace. Traces longer than the value are skipped (see `padded_traces` function). Defaults to the maximun length of the original traces.

        normalise : bool, optional
            A boolean flag indicating whether to normalize the distance values. Defaults to True.

        distance : DistanceFN, optional
            A function that computes the distance between two sequences as an integer. The function should be able to compare sequences of different lengths. Uses `pairwise_distances` default unless specified.

        Returns:
        --------
        Series
            A Polar Series with all the distances between padded traces.

        Notes:
        ------
        This function utilizes the `pairwise_distances` function to calculate pairwise distances among padded log traces and then derives statistical metrics from those distances.
        """
        if padding is None:
            traces = traces if isinstance(traces, Sequence) else list(traces)
            padding = max(len(t) for t in traces)
        return log_distances(padded_traces(traces, padding), distance=distance, normalise=normalise)

    def bylength_distances(traces: PLogs, distance: Optional[DistanceFN]=None, normalise: bool=False) -> Iterable[tuple[int,int, pl.Series]]:
        traces_buckets = traces_by_length(traces)
        for length, traces_group in traces_by_length(traces).items():
            norm_value = length if normalise else 1
            yield (length, len(traces_group), pairwise_distances(traces_group, distance=distance, norm_value=norm_value))
    return bylength_distances, log_distances, padded_distances


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Simple Levenshtein Distance

    Compare the pairwise distance between traces in each log using the Levenshtein distance. The values are normalised by the maximum length of traces in each dataset.
    """)
    return


@app.cell
def _(DATASETS, TRACES, log_distances, pl, sequence_stats):
    levDistances_simple = pl.DataFrame(sequence_stats(log_distances(traces,normalise=True)).row(id=lid, dataset=DATASETS[lid].get('dataset', None), generator=DATASETS[lid].get('generator', None), size=len(traces)) for lid, traces in TRACES.items())
    return (levDistances_simple,)


@app.cell
def _(levDistances_simple, mo, pl):
    mo.ui.tabs({
        dataset[0]: data.
            select(pl.exclude('dataset')).
            sort(by='mean', descending=True)
        for dataset, data in levDistances_simple.group_by('dataset')
    })
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Padded Levenshtein Distance

    Compare the pairwise distance between traces in each log using the Levenshtein distance. Traces in each are padded to ensure the same length, taking the maximum length of the traces in the dataset. The values are normalised by the length of (padded) traces in each dataset.
    """)
    return


@app.cell
def _(DATASETS, TRACES, padded_distances, pl, sequence_stats):
    levDistances_padded = pl.DataFrame(sequence_stats(padded_distances(traces,normalise=True)).row(id=lid, dataset=DATASETS[lid].get('dataset', None), generator=DATASETS[lid].get('generator', None), size=len(traces)) for lid, traces in TRACES.items())
    return (levDistances_padded,)


@app.cell
def _(levDistances_padded, mo, pl):
    mo.ui.tabs({
        dataset[0]: data.
            select(pl.exclude('dataset')).
            sort(by='mean', descending=True)
        for dataset, data in levDistances_padded.group_by('dataset')
    })
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Aggregation of Levenshtein Distance

    For each dataset, traces are grouped by length and for each group is calculated the pairwise Levenshtein distance between traces. The result for the entire dataset is obtained by averaging the results for each group weighted by the number of traces in each group. Only groups larger than 2 traces are taken into account.
    """)
    return


@app.cell
def _(
    DATASETS,
    PLogs: "TypeAlias",
    TRACES,
    bylength_distances,
    pl,
    sequence_stats,
):
    def grouped_stats(id: str, dataset: str, traces: PLogs) -> pl.DataFrame:
        """Calculate the distances between traces grouped by length, returning a dataframe with the statistics (using `sequence_stats`) for each group. Traces smaller than three events are dropped"""
        data = bylength_distances(traces, normalise=True)
        return pl.DataFrame(sequence_stats(series).row(id=id, dataset=dataset, length=length, size=size) for length, size, series in data if size > 2)

    def _grouped_stats(traces: PLogs) -> pl.DataFrame:
        return pl.DataFrame(sequence_stats(series).row(length=length, size=size)
                            for length, size, series in bylength_distances(traces, normalise=True) if size > 2)

    # levDistances_byLength_full = pl.concat(grouped_stats(id, DATASETS[id].get('dataset', None), traces) for id,traces in TRACES.items())
    levDistances_byLength_full = pl.concat(
        _grouped_stats(traces).with_columns(
            id=pl.lit(id), dataset=pl.lit(DATASETS[id].get('dataset', None)), generator=pl.lit(DATASETS[id].get('generator', None)))
        for id,traces in TRACES.items()).pipe(lambda tdf: tdf.select(list(dict.fromkeys(['id', 'dataset', 'generator'] + tdf.columns))))
    levDistances_byLength = (levDistances_byLength_full.lazy()
        .group_by('id')
        .agg(
            pl.first('dataset'),
            pl.len().alias('groups'),
            pl.sum('size'),
            pl.mean('size').alias('group_size_mean'),
            pl.median('size').alias('group_size_median'),
            pl.mean('mean').alias('dist_mean_avg'),
            pl.mean('median').alias('dist_median_avg')
        )
    ).collect()
    return levDistances_byLength, levDistances_byLength_full


@app.cell
def _(levDistances_byLength, mo, pl):
    mo.ui.tabs({
        dataset[0]: data.
            select(pl.exclude('dataset')).
            sort(by='dist_mean_avg', descending=True)
        for dataset, data in levDistances_byLength.group_by('dataset')
    })
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Below the details of the datasets grouped by trace length:
    """)
    return


@app.cell
def _(levDistances_byLength_full, mo, pl):
    mo.ui.tabs({
        dataset[0]: data.
            select(pl.exclude('dataset')).
            sort(['length', 'id'])
        for dataset, data in levDistances_byLength_full.group_by('dataset')
    })
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Data for pubblication
    """)
    return


@app.cell
def _():
    import great_tables as gt
    return (gt,)


@app.cell
def _(levDistances_byLength_full, pl):
    _table = (levDistances_byLength_full
        .filter(pl.col('id').str.contains(pattern=r'_real$'))
        .group_by('dataset')
        .agg(
            pl.col('size').sum(),
        ))
    _table
    return


@app.cell
def _(gt, levDistances_byLength_full, pl):
    _table = pl.concat(
        [_df.select(pl.col('length').alias(f'{_dataset}/length'), pl.col('size').alias(f'{_dataset}/size'))
         for (_dataset,), _df in (levDistances_byLength_full
             .filter(pl.col('id').str.contains(pattern=r'_real$'))
             .sort('dataset', 'length')
             .group_by('dataset'))
        ], how='horizontal')

    _gt_table = (gt.GT(_table)
     .tab_header(title='Size by case lengths of real and generated logs.')
     .tab_spanner(label='bpi_challenge_2012', columns=pl.selectors.starts_with('bpi_challenge_2012'))
     .tab_spanner(label='bpic15_municipality_1', columns=pl.selectors.starts_with('bpic15_municipality_1'))
     .tab_spanner(label='sepsis_cases', columns=pl.selectors.starts_with('sepsis_cases'))
     .cols_label({cname: cname.split('/')[1] for cname in filter(lambda c: '/' in c, _table.columns)})
     .sub_missing(missing_text='')

    )

    print(_gt_table.as_latex())
    # Summary rows are not yet supported by latex output
    _gt_table.grand_summary_rows(fns={
         'total': pl.sum(r'^.*/size$')
     })
    return


@app.cell
def _(mo):
    mo.md(r"""
    Summarisation table for RQ4
    """)
    return


@app.cell
def _(gt, levDistances_simple, pl):
    _table = (levDistances_simple
        .filter(
            pl.col("id").str.contains(r'abs3choice') | (pl.col("generator") == 'real')
        ).pivot(
            on='dataset', index='generator', values=['mean', 'median', 'std'], separator='/'
        ).with_columns(pl.selectors.float().round(2))
    ).pipe(lambda tdf: tdf.select(
        ['generator'] + sorted(filter(lambda c: '/' in c, tdf.columns), key=lambda c: tuple(reversed(c.split('/'))))
    ))

    _gt_table = (gt.GT(_table)
     .tab_header(title='Comparison of real and generated logs')
     .tab_spanner(label='bpi_challenge_2012', columns=pl.selectors.ends_with('bpi_challenge_2012'))
     .tab_spanner(label='bpic15_municipality_1', columns=pl.selectors.ends_with('bpic15_municipality_1'))
     .tab_spanner(label='sepsis_cases', columns=pl.selectors.ends_with('sepsis_cases'))
     .cols_label({cname: cname.split('/')[0] for cname in filter(lambda c: '/' in c, _table.columns)})
     .sub_missing(missing_text='N/A')
    )

    print(_gt_table.as_latex())
    _gt_table
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
