from contextlib import contextmanager, nullcontext
import dataclasses
from dataclasses import dataclass
import importlib
import inspect
import itertools
import json
import logging
import logging.handlers
import os
from pathlib import Path
import random
import re
import statistics
import sys
from typing import Any, Callable, Hashable, Iterable, Optional, Sequence, Union
import warnings
from typing_extensions import deprecated

import Levenshtein
import numpy as np
import pandas as pd

from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedLogGenerator import PositionalBasedLogGenerator
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedModel import PositionalBasedModel


@dataclass
class Experiment(object):
    """Docstring for Experiment."""
    id_: str
    class_: type[PositionalBasedLogGenerator]
    args: dict[str, dict[str, Any]]
    model: PositionalBasedModel
    parameters: Optional[dict[str, Any]]=None
    description: Optional[str]=None

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)

    def runner(self, id_: Optional[str]=None) -> 'Runner':
        init_args = self.args.get('init',{})
        gen = self.class_(**init_args)
        gen_args = self.args.get('run',{})
        return Runner(id=self.id_ if id_ is None else id_, experiment=self, generator=gen, args=gen_args)

    @staticmethod
    def new(id_: str, class_: Union[str, type[PositionalBasedLogGenerator]], model: Union[str, Path, PositionalBasedModel], parameters: dict[str, Any], args: dict[str, dict[str, Any]], description: Optional[str]=None) -> 'Experiment':
        if isinstance(class_, str):
            class_ = import_string(class_)
            if not issubclass(class_, PositionalBasedLogGenerator):
                raise RuntimeError(f'{class_} is not a subclass of PositionalBasedLogGenerator')
        if isinstance(model, str):
            model = PositionalBasedModel().parse_from_string(model)
        elif isinstance(model, Path):
            model = PositionalBasedModel().parse_from_file(model.as_posix())
        for m in ('init', 'run'):
            if m not in args:
                args[m] = {}
        # dirty hack to handle different argument names
        for k, p in inspect.signature(getattr(class_, '__init__')).parameters.items():
            # skip arguments with defaults
            if p.default != inspect._empty:
                continue
            if k in ('pb_model', 'process_model'):
                args['init'][k] = model
        return Experiment(id_=id_, class_=class_, args=args, model=model, parameters=parameters, description=description)

    def check_reproducibility(self, seed=None, ignore: list[str]=['time:timestamp', 'concept:name:time'], only: list[str] = []) -> pd.DataFrame:
        g1 = self.runner(id_= self.id_ + '_1').run(seed=seed)
        g2 = self.runner(id_= self.id_ + '_2').run(seed=seed)
        return compare_results(g1, g2, ignore=ignore, only=only)

@dataclass
class Runner(object):
    """Docstring for ClassName."""
    id: str
    experiment: Experiment
    generator: PositionalBasedLogGenerator
    args: dict[str, Any]

    def run(self, seed: Union[int, float, str, bytes, bytearray, None]=None) -> PositionalBasedLogGenerator:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with random_seed(seed) if seed is not None else nullcontext():
                self.generator.run(**self.args)
        return self.generator

    def stats(self,  normalise: bool=True, columns: Sequence[str]=[]) -> dict[str, Any]:
        num_cases = self.generator.get_results_as_dataframe()['case:concept:name'].nunique()
        results = {
            'id': self.id,
            'generator': type(self.generator).__name__,
            'cases': num_cases,
            'control_flow': self.average_distance(normalise=normalise).asdict(),
            'params': self.experiment.parameters if self.experiment.parameters is not None else {}
        }
        try:
            results['stats'] = self.generator.get_running_stats()
        except:
            pass
        if len(columns) > 0:
            results['data_flow'] = self.average_distance(columns=['concept:name', *columns], normalise=normalise).asdict()
        return results

    def results_as_seq(self, columns: Sequence[str] = ["concept:name"]) -> Iterable[Sequence[Hashable]]:
        def case_key(key: pd.Series) -> pd.Series:
            return key.str.removeprefix('event_').astype('int64')

        for case, frame in self.generator.get_results_as_dataframe().groupby('case:concept:name'):
            case_df = frame.sort_values(by='concept:name:order', key=case_key)
            if len(columns) > 1:
                yield [tuple(r) for r in case_df[columns].to_numpy()]
            else:
                yield case_df[columns[0]].values.tolist()


    def average_distance(self, columns: Sequence[str] = ["concept:name"], normalise: bool=True, aggr: Callable=statistics.mean) -> 'Distances':
        norm_val = self.generator.get_results_as_dataframe()['concept:name:order'].nunique() if normalise else None
        return average_distances_seq(self.results_as_seq(columns=columns), normalise=norm_val, aggr=aggr)


def import_string(dotted_path: str) -> Any:
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    if not re.match(r'(\w+\.)*\w+$', dotted_path):
        raise RuntimeError(f'invalid object spec {dotted_path}')
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError:
        # not a dotted spec, look into current module
        return globals()[dotted_path]

    return getattr(importlib.import_module(module_path), class_name)

###############################################################
## Trace distances

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
        levenshtein = None
    try:
        hamming = aggr(Levenshtein.hamming(s1,s2) for s1,s2 in t2)
    except statistics.StatisticsError as e:
        logging.warning(f'error averaging distance: {e}')
        hamming = None
    if normalise is not None and normalise > 0:
        return Distances(levenshtein=levenshtein/normalise, hamming=hamming/normalise)
    else:
        return Distances(levenshtein=levenshtein, hamming=hamming)

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

###############################################################
## Dealing with logging

class JsonFormatter(logging.Formatter):
    """Formatter to dump error message into JSON"""

    @staticmethod
    def _custom_json(obj: Any) -> Any:
        if isinstance(obj, type):
            return obj.__name__
        elif isinstance(obj, object):
            return repr(obj)
        raise TypeError(f'Cannot serialize object of {type(obj)}')

    def format(self, record: logging.LogRecord) -> str:
        record_dict = {
            "name": record.name,
            "level": record.levelname,
            "date": self.formatTime(record),
            "message": record.getMessage(),
            "msg": record.msg,
            "args": record.args,
            "module": record.module,
            "file": record.filename,
            "function": record.funcName,
            "lineno": record.lineno,
        }
        return json.dumps(record_dict, default=self._custom_json)

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
