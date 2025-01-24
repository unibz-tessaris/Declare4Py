from contextlib import contextmanager
import logging
import math
import random
from string import Template
import typing

import clingo
import pandas as pd

from Declare4Py.D4PyEventLog import D4PyEventLog
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedModel import PositionalBasedModel
from Declare4Py.ProcessMiningTasks.LogGenerator.PositionalBased.PositionalBasedUtils.ASPUtils import ASPFunctions
from Declare4Py.ProcessModels.AbstractModel import ProcessModel

from .PositionalBasedLogGenerator import PositionalBasedLogGenerator

class PBLGwrapper(PositionalBasedLogGenerator):
    """Helper class wrapping the private methods and property of the PositionalBasedLogGenerator class."""
    def __init__(self, total_traces: int, min_events: int, max_events: int, pb_model: PositionalBasedModel, verbose: bool = False):
        super().__init__(total_traces, min_events, max_events, pb_model, verbose)

    # Accessing the base implementation from PositionalBasedLogGenerator
    #   this hack is needed because most of the implementation is based on private methods/properties
    #   that doesn't allow specialisation

    def __get_PBLG(self, name: str) -> typing.Any:
        return getattr(self, '_PositionalBasedLogGenerator' + name)

    def __set_PBLG(self, name: str, value: typing.Any) -> None:
        setattr(self, '_PositionalBasedLogGenerator' + name, value)

    ### Wrap private methods

    def __parse_results(self, results: dict, label: str, noise_percentage: int = 0) -> None:
        self.__get_PBLG('__parse_results')(results, label, noise_percentage)

    def __prepare_clingo_configuration(self) -> typing.List[str]:
        return self.__get_PBLG('__prepare_clingo_configuration')()

    def __prepare_asp_models(self, equal_rule_split: bool, generate_negatives: bool = False) -> tuple[list[str], bool]:
        return self.__get_PBLG('__prepare_asp_models')(equal_rule_split, generate_negatives)

    def __handle_clingo_result(self, output: clingo.solving.Model) -> None:
        self.__get_PBLG('__handle_clingo_result')(output)

    def __get_clingo_time_limit(self) -> int:
        return self.__get_PBLG('__get_clingo_time_limit')()

    ### Wrap private attributes

    ## PositionalBasedLogGenerator.__case_index
    @property
    def __case_index(self) -> int:
        return self.__get_PBLG('__case_index')
    @__case_index.setter
    def __case_index(self, value: int):
        self.__set_PBLG('__case_index', value)

    ## PositionalBasedLogGenerator.__current_asp_rule
    @property
    def __current_asp_rule(self) -> str:
        return self.__get_PBLG('__current_asp_rule')
    @__current_asp_rule.setter
    def __current_asp_rule(self, value: str):
        self.__set_PBLG('__current_asp_rule', value)

    ## PositionalBasedLogGenerator.__generate_positives
    @property
    def __generate_positives(self) -> bool:
        return self.__get_PBLG('__generate_positives')
    @__generate_positives.setter
    def __generate_positives(self, value: bool):
        self.__set_PBLG('__generate_positives', value)

    ## PositionalBasedLogGenerator.__negatives_results
    @property
    def __negatives_results(self) -> dict:
        return self.__get_PBLG('__negatives_results')
    @__negatives_results.setter
    def __negatives_results(self, value: dict):
        self.__set_PBLG('__negatives_results', value)

    ## PositionalBasedLogGenerator.__pd_cols
    @property
    def __pd_cols(self) -> typing.List[str]:
        return self.__get_PBLG('__pd_cols')
    @__pd_cols.setter
    def __pd_cols(self, value: typing.List[str]):
        self.__set_PBLG('__pd_cols', value)

    ## PositionalBasedLogGenerator.__pd_results
    @property
    def __pd_results(self) -> pd.DataFrame:
        return self.__get_PBLG('__pd_results')
    @__pd_results.setter
    def __pd_results(self, value: pd.DataFrame):
        self.__set_PBLG('__pd_results', value)

    ## PositionalBasedLogGenerator.__positive_results
    @property
    def __positive_results(self) -> dict:
        return self.__get_PBLG('__positive_results')
    @__positive_results.setter
    def __positive_results(self, value: dict):
        self.__set_PBLG('__positive_results', value)

    ### 
    # for the following methods see code PositionalBasedLogGenerator.run

    def _initialise_datastore(self, append_results: bool) -> None:
        # Checks if the result must be appended, otherwise resets the dataframe
        if not append_results:
            self.__pd_results = pd.DataFrame(columns=self.__pd_cols)
            self.__case_index = 0

        # Resets the results dicts
        self.__positive_results = {}
        self.__negatives_results = {}

    def _get_clingo_configuration(self) -> typing.Sequence[str]:
        return self.__prepare_clingo_configuration()

    def _get_ASP_code(self, equal_rule_split: bool, generate_negatives: bool) -> typing.Iterable[str]:
        self.__generate_positives = not generate_negatives
        asp_list, _ = self.__prepare_asp_models(equal_rule_split, generate_negatives=generate_negatives)
        # Inserts the function for the range in ASP
        # see PositionalBasedLogGenerator.__run_clingo
        return (asp + "\n" + ASPFunctions.ASP_PYTHON_RANGE_SCRIPT for asp in asp_list)

    def _parse_results(self, negative_results: bool, noise_percentage: int) -> None:
        if negative_results:
            self.__parse_results(self.__negatives_results, "Negative", noise_percentage=noise_percentage)
        else:
            self.__parse_results(self.__positive_results, "Positive", noise_percentage=noise_percentage)

    def _update_asp_current_rule(self, index: int, equal_rule_split: bool, generate_negatives: bool) -> None:
        # see PositionalBasedLogGenerator.__run_clingo_per_trace_set
        if generate_negatives:
            self.__current_asp_rule = "Not_Rule_"
        else:
            self.__current_asp_rule = "Rule_"
        if equal_rule_split:
            self.__current_asp_rule += str(index + 1)
        else:
            self.__current_asp_rule += "?"

    def _clingo_model_handler(self, index: int, model: clingo.Model) -> None:
        self.__handle_clingo_result(model)

    def _get_timed_events(self, model: clingo.Model) -> typing.Iterable[tuple[str, int, int]]:
        # see `PositionalBasedLogGenerator.__handle_clingo_result`
        # and `PositionalBasedLogGenerator.__parse_results`
        for function in model.symbols(shown=True):
            if function.name == ASPFunctions.ASP_TIMED_EVENT:
                    args_ = function.arguments
                    yield (args_[0].name, args_[1].number, args_[2].number)

    @property
    def _clingo_time_limit(self) -> int:
        return self.__get_clingo_time_limit()

    @property
    def _current_asp_rule(self) -> str:
        return self.__current_asp_rule


class PBLogGeneratorOrig(PBLGwrapper):
    """reimplementation of the PositionalBasedLogGenerator class using the wrapper PBLGwrapper"""
    def __init__(
        self,
        total_traces: int,
        min_event: int,
        max_event: int,
        process_model: ProcessModel,
        log: typing.Union[D4PyEventLog, None] = None,
        verbose: bool = False,
        seed: typing.Union[int, float, str, bytes, bytearray, None, random.Random] = None
    ):
        super().__init__(total_traces, min_event, max_event, process_model, verbose=verbose)

        logger_name = type(self).__name__
        self._logger: logging.Logger = logging.getLogger(logger_name)
        self._logger.setLevel(logging.DEBUG if verbose else logging.INFO)

        self._random: random.Random = seed if isinstance(seed, random.Random) else random.Random(seed)

        self._monitor_predicates: set[str] = set([ASPFunctions.ASP_TIMED_EVENT])

        self._clingo_prog: list[list[tuple[tuple, str]]] = [[]]
        self.__clingo_stats: typing.Sequence[dict] = []

    def run(self, equal_rule_split: bool = True, high_variability: bool = False, generate_negatives_traces: bool = False, positive_noise_percentage: int = 0, negative_noise_percentage: int = 0, append_results: bool = False):
        """
        Method that generates positional based logs:

        Parameters
            equal_rule_split: bool = If True the generation will not be random and each rule will appear in a uniform manner
            high_variability: bool = Unused, kept for API compatibility
            generate_negatives_traces: bool = If True generates also the negative logs
            append_results: bool = If True appends the new log results to the existing logs
            positive_noise_percentage: int = Indicates the noise in the positive traces
            negative_noise_percentage: int = Indicates the noise in the negative traces
        """

        self._initialise_datastore(append_results)

        # Runs clingo and parses the results for the positive traces
        self._generate_trace_set(equal_rule_split, False, positive_noise_percentage)

        # If the generator must solve also the negative traces
        if generate_negatives_traces:
            self._generate_trace_set(equal_rule_split, True, negative_noise_percentage)

    def _generate_trace_set(self, equal_rule_split: bool, generate_negatives: bool, noise_percentage: int) -> None:
        asp_list = list(self._get_ASP_code(equal_rule_split, generate_negatives))
        distribution = self.compute_distribution(math.ceil(self.log_length / len(asp_list)))

        # see PositionalBasedLogGenerator.__run_clingo_per_trace_set
        for i, asp in enumerate(asp_list):
            # Set the current ASP rule
            self._update_asp_current_rule(i, equal_rule_split, generate_negatives)

            # For every number of events in the number of traces generates a uniform set of trace
            for num_events, num_traces in distribution.items():
                self._logger.info(f"Generating {num_traces} {'negative' if generate_negatives else 'positive'} traces with {num_events} events, {noise_percentage} noise (current rule: {self._current_asp_rule})")
                self._clingo_generate_traces(asp, num_traces, num_events)

        # parses ASP generated models
        self._parse_results(generate_negatives, noise_percentage)

    def _clingo_model_handler(self, index: int, model: clingo.Model) -> None:
        super()._clingo_model_handler(index, model)
        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug('clingo model %(index)s: %(model)s', {'index': index, 'model': list(str(p) for p in self._clingo_get_model_atoms(model, self._monitor_predicates))})

    def _clingo_control(self, arguments: typing.Sequence[str], *programs: str) -> clingo.Control:
        """Create a new [`clingo.Control`](https://potassco.org/clingo/python-api/current/clingo/control.html#clingo.control.Control) using the given arguments, and add the provided programs

        Args:
            arguments (Sequence[str]): clingo arguments
            programs (Sequence[str]): clingo ASP programs

        Returns:
            clingo.Control: a new clingo controller
        """
        self._logger.debug('New clingo control: %(clingo_args)s', {'clingo_args': arguments})
        self._clingo_prog.append([])
        ctl = clingo.Control(arguments, logger=self._logger)
        asp = "\n".join(programs)

        self._clingo_add(ctl, 'base', [], asp)
        return ctl
    
    def _clingo_add(self, ctl: clingo.Control, name: str, parameters: typing.Sequence[str], program: str) -> None:
        self._logger.debug('clingo: adding %(part)s: %(asp)s', {'part': (name, parameters), 'asp': program})
        self._clingo_prog[-1].append(((name, parameters), program))
        ctl.add(name, parameters, program)

    def _clingo_ground(self, ctl: clingo.Control, parts: typing.Sequence[tuple[str, typing.Sequence[clingo.Symbol]]] = (("base", ()), ), context: typing.Any = None):
        self._logger.debug('clingo: grounding %(parts)s', {'parts': parts, 'context': context})
        ctl.ground(parts=parts, context=context)

    @property
    def clingo_statistics(self) -> typing.Sequence[dict]:
        """The clingo statistics of each [`Control.solve`](https://potassco.org/clingo/python-api/current/clingo/control.html#clingo.control.Control.solve) call
        """
        return self.__clingo_stats
    
    def clingo_statistics_reset(self) -> None:
        """resets clingo statistics
        """
        self.__clingo_stats = []

    def _clingo_stat_add(self, stat: dict) -> None:
        self.__clingo_stats.append(stat)

    def get_running_stats(self) -> dict:
        """return the cumulative running statistics of the solving time"""
        glob_stat = {
            'times': {},
            'timeout': self._clingo_time_limit,
            'timedout': False,
            'models': 0
        }
        for stat in self.clingo_statistics:
            times_ = stat.get('solver', {}).get('times', {})
            for a in times_.keys():
                glob_stat['times'][a] = times_[a] + glob_stat['times'].get(a, 0)
            if not glob_stat['timedout'] and stat['timedout']:
                glob_stat['timedout'] = True
            glob_stat['models'] += stat['call']['models']
        return glob_stat

    def _clingo_solve(self, ctl: clingo.Control, models: int=0, timeout: typing.Optional[int]=None) -> typing.Iterable[clingo.Model]:
        ctl.configuration.solve.models = models
        timedout: bool = False
        generates_models: int = 0
        with ctl.solve(yield_=True, async_=True) as hnd:
            for i in range(models):
                hnd.resume()
                if not hnd.wait(timeout):
                    # terminated within the time limit
                    self._logger.info(f'clingo timeout on model {i}')
                    hnd.cancel()
                    timedout = True
                    break
                m = hnd.model()
                if m is None:
                    # no more models
                    self._logger.info(f'not enough ASP models, generated {i} instead of {models}')
                    break
                generates_models += 1
                yield m
            solve_result = hnd.get()
        stat = {
            'solver': dict(**ctl.statistics.get('summary', {})),
            'solveresult': {a: getattr(solve_result, a, None) for a in ('exhausted', 'interrupted', 'satisfiable', 'unknown', 'unsatisfiable')},
            'timedout': timedout,
            'call': {'models': models, 'timeout': timeout},
            'models': generates_models
        }
        self._logger.debug('clingo statistics: %(stats)s', {'stats': stat})
        self._clingo_stat_add(stat)

    def _clingo_get_model_atoms(self, model: clingo.Model, names: typing.Iterable[str]=[]) -> typing.Iterable[clingo.Symbol]:
        return (t for t in model.symbols(atoms=True) if t.name in set(names))

    def _clingo_generate_traces(self, program: str, traces: int, events: int):
        """use clingo to generate the given number of traces of a specific length using the provided ASP program

        Args:
            program (str): ASP program encoding generation and model based filtering
            traces (int): number of traces to generate
            events (int): length of each trace
        """

        self._logger.info(f'Using clingo to generate {traces} traces of length {events}')
        clingo_args = [
                    "-c",
                    f"p={int(events)}",
                    f"--seed={self._random.randrange(0, 2 ** 30 - 1)}",
                    "--project"
                ] + self._get_clingo_configuration()

        ctl = self._clingo_control(clingo_args, program)
        self._clingo_ground(ctl)

        for i, m in enumerate(self._clingo_solve(ctl, models=traces, timeout=self._clingo_time_limit)):
            self._clingo_model_handler(i, m)

class PBLogGeneratorBatch(PBLogGeneratorOrig):
    """Generates positional based logs given a positional based model using clingo.
    Runs clingo solver several times, generating logs in batches of models instead of a single run."""
    def __init__(
        self,
        total_traces: int,
        min_event: int,
        max_event: int,
        process_model: ProcessModel,
        log: typing.Union[D4PyEventLog, None] = None,
        verbose: bool = False,
        seed: typing.Union[int, float, str, bytes, bytearray, None, random.Random] = None,
        batches: int = 5
    ):
        super().__init__(total_traces, min_event, max_event, process_model, log=log, verbose=verbose, seed=seed)
        self._batches = batches

    def _clingo_generate_traces(self, program: str, traces: int, events: int):
        """use clingo to generate the given number of traces of a specific length using the provided ASP program

        Args:
            program (str): ASP program encoding generation and model based filtering
            traces (int): number of traces to generate
            events (int): length of each trace
        """
        for i, b_traces in enumerate([traces // self._batches] * self._batches + [traces % self._batches], start=1):
            if b_traces < 1:
                continue
            self._logger.info(f'Generating batch {i} of {b_traces} traces of length {events}')
            super()._clingo_generate_traces(program, b_traces, events)

class PBLogGeneratorBaseline(PBLogGeneratorOrig):
    """Generates positional based logs given a positional based model using clingo.
    The baseline implementation doesn't attempt to introduce variability in the models generated by the solver."""
    def __init__(
        self,
        total_traces: int,
        min_event: int,
        max_event: int,
        process_model: ProcessModel,
        log: typing.Union[D4PyEventLog, None] = None,
        verbose: bool = False,
        seed: typing.Union[int, float, str, bytes, bytearray, None, random.Random] = None
    ):
        super().__init__(total_traces, min_event, max_event, process_model, log=log, verbose=verbose, seed=seed)

    def _clingo_generate_traces(self, program: str, traces: int, events: int):
        """use clingo to generate the given number of traces of a specific length using the provided ASP program

        Args:
            program (str): ASP program encoding generation and model based filtering
            traces (int): number of traces to generate
            events (int): length of each trace
        """

        self._logger.info(f'Using clingo to generate {traces} traces of length {events}')
        clingo_args = ["-c", f"p={int(events)}"]

        ctl = self._clingo_control(clingo_args, program)
        self._clingo_ground(ctl)

        for i, m in enumerate(self._clingo_solve(ctl, models=traces, timeout=self._clingo_time_limit)):
            self._clingo_model_handler(i, m)

class PBLogGeneratorRandom(PBLogGeneratorOrig):
    """Generates positional based logs given a positional based model using clingo.
    This implementation uses clingo randomisation to introduce variability in the models generated by the solver."""
    def __init__(
        self,
        total_traces: int,
        min_event: int,
        max_event: int,
        process_model: ProcessModel,
        log: typing.Union[D4PyEventLog, None] = None,
        verbose: bool = False,
        seed: typing.Union[int, float, str, bytes, bytearray, None, random.Random] = None
    ):
        super().__init__(total_traces, min_event, max_event, process_model, log=log, verbose=verbose, seed=seed)

    def _clingo_generate_traces(self, program: str, traces: int, events: int):
        """use clingo to generate the given number of traces of a specific length using the provided ASP program

        Args:
            program (str): ASP program encoding generation and model based filtering
            traces (int): number of traces to generate
            events (int): length of each trace
        """

        self._logger.info(f'Using clingo to generate {traces} traces of length {events}')
        clingo_args = ["-c", f"p={int(events)}"]

        ctl = self._clingo_control(clingo_args, program)
        self._clingo_ground(ctl)

        # configure solver for randomisation
        ctl.configuration.solver.sign_def = 'rnd'
        ctl.configuration.solver.rand_freq = 1
        ctl.configuration.solve.models = 1

        for i in range(traces):
            model_found: bool = False
            # set a new seed before each `Control.solve` call
            ctl.configuration.solver.seed = self._random.randint(2, 2^32)
            for m in self._clingo_solve(ctl, models=1, timeout=self._clingo_time_limit):
                self._clingo_model_handler(i, m)
                model_found = True
            if not model_found:
                self._logger.info(f'clingo cannot find more models, stopped at {i}')
                break

class PBLogGeneratorHamming(PBLogGeneratorOrig):
    """Generates positional based logs given a positional based model using clingo.
    This implementation uses...
    """

    _prog_name = 'hamming'
    _prog_argnames = ['tid', 'threshold']
    _tabu_pred = 'tabu'
    _tabu_program_tmpl: Template = Template(r'''
hamm_dist(${tid_arg}, D) :- D = #count { ${timed_event_pred}(A,P,T) : ${timed_event_pred}(A,P,T), ${tabu_pred}(${tid_arg}, A1, P), A != A1 }, D <= ${max_distance}.

:- hamm_dist(${tid_arg}, D), D < ${threshold_arg}.
''')

    def __init__(
        self,
        total_traces: int,
        min_event: int,
        max_event: int,
        process_model: ProcessModel,
        log: typing.Union[D4PyEventLog, None] = None,
        verbose: bool = False,
        seed: typing.Union[int, float, str, bytes, bytearray, None, random.Random] = None,
        threshold: float = .3,
        randomise: bool = False
    ):
        super().__init__(total_traces, min_event, max_event, process_model, log=log, verbose=verbose, seed=seed)

        self._threshold = threshold
        self._randomise_clingo = randomise

    def _clingo_generate_traces(self, program: str, traces: int, events: int):
        """use clingo to generate the given number of traces of a specific length using the provided ASP program

        Args:
            program (str): ASP program encoding generation and model based filtering
            traces (int): number of traces to generate
            events (int): length of each trace
        """

        self._logger.info(f'Using clingo to generate {traces} traces of length {events}')
        clingo_args = ["-c", f"p={int(events)}"]

        ctl = self._clingo_control(clingo_args, program)
        self._clingo_ground(ctl)

        self._add_tabu_asp_program(ctl)

        if self._randomise_clingo:
            # configure solver for randomisation
            ctl.configuration.solver.sign_def = 'rnd'
            ctl.configuration.solver.rand_freq = 1
            ctl.configuration.solve.models = 1

        last_tabu_trace: list[tuple[str, int, int]] = []

        for i in range(traces):
            model_found: bool = False
            if self._randomise_clingo:
                # set a new seed before each `Control.solve` call
                ctl.configuration.solver.seed = self._random.randint(2, 2^32)
            if len(last_tabu_trace) > 0:
                self._ground_tabu_asp_program(ctl, i, last_tabu_trace)
                last_tabu_trace = []
            for m in self._clingo_solve(ctl, models=1, timeout=self._clingo_time_limit):
                self._clingo_model_handler(i, m)
                last_tabu_trace = list(self._get_timed_events(m))
                model_found = True
            if not model_found:
                self._logger.info(f'clingo cannot find more models, stopped at {i}')
                break

    def _tabu_asp_program(self) -> str:
        asp = self._tabu_program_tmpl.substitute(
            prog_name=self._prog_name,
            prog_args=','.join(self._prog_argnames),
            tid_arg=self._prog_argnames[0],
            threshold_arg=self._prog_argnames[1],
            timed_event_pred=ASPFunctions.ASP_TIMED_EVENT,
            tabu_pred=self._tabu_pred,
            max_distance='p',
        )
        return asp
    
    def _add_tabu_asp_program(self, ctl: clingo.Control) -> None:
        self._clingo_add(ctl, self._prog_name, self._prog_argnames, self._tabu_asp_program())

    def _ground_tabu_asp_program(self, ctl: clingo.Control, tid: int, tabu_case: list[tuple[str, int, int]]) -> None:
        asp_prog_args = (clingo.Number(tid), clingo.Number(int(len(tabu_case) * self._threshold)))

        tabu_assertions = ' '.join(f'{self._tabu_pred}({tid}, {a}, {p}).' for a,p,_ in tabu_case) + "\n"
        self._clingo_add(ctl, self._prog_name, self._prog_argnames, tabu_assertions)
        self._clingo_ground(ctl, parts=((self._prog_name, asp_prog_args),))

class PBLogGeneratorLevenshtein(PBLogGeneratorHamming):
    """Generates positional based logs given a positional based model using clingo.
    This implementation uses...
    """

    _prog_name = 'levenshtein'
    _prog_argnames = ['tid', 'threshold']
    _tabu_pred = 'tabu'
    _tabu_program_tmpl: Template = Template(r'''
lev(${tid_arg},0,0,0).
lev(${tid_arg},0,D,D) :- D = 1..${max_distance}.
lev(${tid_arg},D,0,D) :- D = 1..${max_distance}.

lev(${tid_arg}, I, J, D) :- ${timed_event_pred}(A,I,_), ${tabu_pred}(${tid_arg},A,J), D = #min { D1 : lev(${tid_arg}, I-1, J-1, D1); D2+1 : lev(${tid_arg}, I-1, J, D2); D3+1 : lev(${tid_arg}, I, J-1, D3) }, I = 1..${max_distance}, J = 1..${max_distance}, D <= ${max_distance}.%, |I - J| <= ${threshold_arg}.
lev(${tid_arg}, I, J, D) :- ${timed_event_pred}(A,I,_), ${tabu_pred}(${tid_arg}, A1, J), A != A1, D = #min { D1+1 : lev(${tid_arg}, I-1, J-1, D1); D2+1 : lev(${tid_arg}, I-1, J, D2); D3+1 : lev(${tid_arg}, I, J-1, D3) }, I = 1..${max_distance}+1, J = 1..${max_distance}+1, D <= ${max_distance}.%, |I - J| <= ${threshold_arg}.

lev_dist(${tid_arg}, D) :- lev(${tid_arg}, ${max_distance}, ${max_distance}, D).
hamm_dist(${tid_arg}, D) :- D = #count { (A,P) : ${timed_event_pred}(A,P,_), ${tabu_pred}(${tid_arg}, A1, P), A != A1 }, D <= ${max_distance}.

:- hamm_dist(${tid_arg}, D), D < ${threshold_arg}.
:- lev_dist(${tid_arg}, D), D < ${threshold_arg}.
''')

    def __init__(
        self,
        total_traces: int,
        min_event: int,
        max_event: int,
        process_model: ProcessModel,
        log: typing.Union[D4PyEventLog, None] = None,
        verbose: bool = False,
        seed: typing.Union[int, float, str, bytes, bytearray, None, random.Random] = None,
        threshold: float = .3,
        randomise: bool = False
    ):
        super().__init__(total_traces, min_event, max_event, process_model, log=log, verbose=verbose, seed=seed, threshold=threshold, randomise=randomise)
