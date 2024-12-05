from contextlib import contextmanager
import dataclasses
from dataclasses import dataclass
import itertools
import json
import logging
import logging.handlers
import os
from pathlib import Path
import random
import statistics
from typing import Any, Callable, Hashable, Iterable, Optional, Sequence, Union
import warnings

import Levenshtein
import numpy as np
import pandas as pd

from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedLogGenerator import PositionalBasedLogGenerator
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedModel import PositionalBasedModel


@dataclass
class Experiment(object):
    """Docstring for Experiment."""
    id_: str
    class_: PositionalBasedLogGenerator
    args: dict[str, dict[str, Any]]
    model: PositionalBasedModel
    parameters: Optional[dict[str, Any]]=None
    description: Optional[str]=None

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)

    def new_generator(self) -> PositionalBasedLogGenerator:
        return self.class_(**self.args.get('init',{}))

    def run_generator(self, gen: Optional[PositionalBasedLogGenerator]=None) -> PositionalBasedLogGenerator:
        if gen is None:
            gen = self.new_generator()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gen.run(**self.args.get('run',{}))
        return gen
    
    def get_results(self, gen: Optional[PositionalBasedLogGenerator]=None, normalise: bool=True, columns: Sequence[str]=[]) -> dict:
        if gen is None:
            gen = self.run_generator()
        num_cases = gen.get_results_as_dataframe()['case:concept:name'].nunique()
        results = {
            'id': self.id_,
            'generator': type(gen).__name__,
            'cases': num_cases,
            'control_flow': average_distance(gen, normalise=normalise).asdict(),
            'params': self.parameters if self.parameters is not None else {}
        }
        try:
            results['stats'] = gen.get_running_stats()
        except:
            pass
        if len(columns) > 0:
            results['data_flow'] = average_distance(gen, columns=['concept:name', *columns], normalise=normalise).asdict()
        return results
    
    def check_reproducibility(self, seed=None, ignore: list[str]=['time:timestamp', 'concept:name:time'], only: list[str] = []) -> pd.DataFrame:
        if seed is not None:
            with random_seed(seed):
                g1 = self.run_generator()
            with random_seed(seed):
                g2 = self.run_generator()
        else:
            g1 = self.run_generator()
            g2 = self.run_generator()
        
        return compare_results(g1, g2, ignore=ignore, only=only)


def experiments_dump(experiments: dict[str, Experiment], fp,**kwargs) -> None:
    def custom_json(obj):
        if isinstance(obj, type):
            return obj.__name__
        elif isinstance(obj, object):
            return f'obj({type(obj).__name__})'
        raise TypeError(f'Cannot serialize object of {type(obj)}')

    json.dump([e.as_dict() for e in experiments.values()], fp, default=custom_json, **kwargs)

###############################################################
## Trace distances

def results_to_seq(generator: PositionalBasedLogGenerator, columns: Sequence[str] = ["concept:name"]) -> Iterable[Sequence[Hashable]]:
    def case_key(key: pd.Series) -> pd.Series:
        return key.str.removeprefix('event_').astype('int64')

    for case, frame in generator.get_results_as_dataframe().groupby('case:concept:name'):
        case_df = frame.sort_values(by='concept:name:order', key=case_key)
        if len(columns) > 1:
            yield [tuple(r) for r in case_df[columns].to_numpy()]
        else:
            yield case_df[columns[0]].values.tolist()

@dataclass
class Distances(object):
    """Docstring for ClassName."""
    levenshtein: int
    hamming: int

    def asdict(self) -> dict:
        return dataclasses.asdict(self)

def average_distances_seq(traces: Iterable[Sequence[Hashable]], aggr: Callable=statistics.mean, normalise: Optional[int]=None) -> Distances:
    t1, t2 = itertools.tee(itertools.combinations(traces,2))
    try:
        levenshtein = aggr(Levenshtein.distance(s1,s2) for s1,s2 in t1)
    except statistics.StatisticsError as e:
        logging.warning(f'error averaging distance: {e}')
        levenshtein = float('nan')
    try:
        hamming = aggr(Levenshtein.hamming(s1,s2) for s1,s2 in t2)
    except statistics.StatisticsError as e:
        logging.warning(f'error averaging distance: {e}')
        hamming = float('nan')
    if normalise is not None and normalise > 0:
        return Distances(levenshtein=levenshtein/normalise, hamming=hamming/normalise)
    else:
        return Distances(levenshtein=levenshtein, hamming=hamming)

def average_distance(generator: PositionalBasedLogGenerator, columns: Sequence[str] = ["concept:name"], normalise: bool=True) -> Distances:
    norm_val = generator.get_results_as_dataframe()['concept:name:order'].nunique() if normalise else None
    return average_distances_seq(results_to_seq(generator, columns=columns), normalise=norm_val)


###############################################################
## Evaluation of reproducibility

@contextmanager
def random_seed(seed: Union[int, float, str, bytes, bytearray, None]):
    """context manager to change the seed of the default random generators of python and numpy and restore their state at exit

    Args:
        seed (int | float | str | bytes | bytearray | None): see `random.seed` function
    """
    current_state = random.getstate()
    current_np_state = np.random.get_state()
    random.seed(seed)
    np.random.seed(random.randint(2, 2^32))
    try:
        yield
    finally:
        random.setstate(current_state)
        np.random.set_state(current_np_state)

def compare_results(g1: PositionalBasedLogGenerator, g2: PositionalBasedLogGenerator, ignore: list[str]=['time:timestamp', 'concept:name:time'], only: list[str] = []) -> pd.DataFrame:
    if only is not None and len(only) > 0:
        g1_df = g1.get_results_as_dataframe()[only]
        g2_df = g2.get_results_as_dataframe()[only]
    else:
        g1_df = g1.get_results_as_dataframe().drop(columns=ignore)
        g2_df = g2.get_results_as_dataframe().drop(columns=ignore)

    return g1_df.compare(g2_df)

def check_reproducibility(exp: dict, seed=None, ignore: list[str]=['time:timestamp', 'concept:name:time'], only: list[str] = []) -> pd.DataFrame:
    if seed is not None:
        with random_seed(seed):
            g1 = run_generator(exp)
        with random_seed(seed):
            g2 = run_generator(exp)
    else:
        g1 = run_generator(exp)
        g2 = run_generator(exp)
    
    return compare_results(g1, g2, ignore=ignore, only=only)

###############################################################
## Dealing with logging

class JsonFormatter(logging.Formatter):
    """Formatter to dump error message into JSON"""

    def format(self, record: logging.LogRecord) -> str:
        if isinstance(record.args, tuple):
            args = [str(a) for a in record.args]
        elif isinstance(record.args, dict):
            args = {k: str(v) for k, v in record.args.items()}
        else:
            args = str(record.args)
        record_dict = {
            "level": record.levelname,
            "date": self.formatTime(record),
            "message": record.getMessage(),
            "msg": record.msg,
            "args": args,
            "module": record.module,
            "file": record.filename,
            "function": record.funcName,
            "lineno": record.lineno,
        }
        return json.dumps(record_dict)

@contextmanager
def log_to_file(filename: Union[str, bytes, os.PathLike, Path], level: Optional[int]=None, fmt: Union[str, logging.Formatter, None]=None, logger: Optional[logging.Logger]=None):
    if fmt is None:
        fmt = JsonFormatter()
        # fmt = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
    elif isinstance(fmt, str):
        fmt = logging.Formatter(fmt)
    assert isinstance(fmt, logging.Formatter)
    if logger is None:
        logger = logging.getLogger()
    hdlr = logging.FileHandler(filename)
    hdlr.setFormatter(fmt)
    with changelogger([hdlr], level=level, logger_=logger):
        yield

@contextmanager
def changelogger(hdlrs: Iterable[logging.Handler], level: Optional[int]=None, logger_: Optional[logging.Logger]=None):
    if logger_ is None:
        logger_ = logging.getLogger()
    current_hdlrs = list(logger_.handlers)
    current_lvl = logger_.level
    if level is None:
        level = current_lvl
    for hdlr in logger_.handlers:
        logger_.removeHandler(hdlr)
    for hdlr in hdlrs:
        logger_.addHandler(hdlr)
    logger_.setLevel(level)
    try:
        yield
    finally:
        for hdlr in logger_.handlers:
            logger_.removeHandler(hdlr)
        for hdlr in current_hdlrs:
            logger_.addHandler(hdlr)
        logger_.setLevel(current_lvl)
