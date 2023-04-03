from __future__ import annotations

import collections
import logging
import math
import re
import typing
import warnings
from datetime import datetime, timedelta, timezone
from random import randrange

import copy
import clingo
import pm4py
from clingo import Symbol
from pm4py.objects.log import obj as lg

from src.Declare4Py.D4PyEventLog import D4PyEventLog
from src.Declare4Py.ProcessMiningTasks.ASPLogGeneration.ASPTranslator.asp_translator import ASPModel
from src.Declare4Py.ProcessMiningTasks.ASPLogGeneration.ASPUtils.asp_encoding import ASPEncoding
from src.Declare4Py.ProcessMiningTasks.ASPLogGeneration.ASPUtils.asp_result_parser import ASPResultTraceModel
from src.Declare4Py.ProcessMiningTasks.ASPLogGeneration.ASPUtils.asp_template import ASPTemplate
from src.Declare4Py.ProcessMiningTasks.ASPLogGeneration.ASPUtils.distribution import Distributor
from src.Declare4Py.ProcessMiningTasks.log_generator import LogGenerator
from src.Declare4Py.ProcessModels.AbstractModel import ProcessModel
from src.Declare4Py.ProcessModels.DeclareModel import DeclareModel, DeclareParsedDataModel, \
    DeclareModelConstraintTemplate, DeclareModelAttributeType, DeclareModelAttr


class LogTracesType(typing.TypedDict):
    positive: typing.List
    negative: typing.List


def custom_sort_trace_key(x):
    # Extract the numeric parts of the string
    parts = re.findall(r'\d+', x.name)
    # Convert the numeric parts to integers
    parts = [int(p) for p in parts]
    return parts


class AspGenerator(LogGenerator):

    def __init__(self, decl_model: DeclareModel, num_traces: int, min_event: int, max_event: int,
                 encode_decl_model: bool = True):
        """
        ASPGenerator generates the log from declare model which translate declare model
        into ASP, and then it passes to the clingo, which generates the traces

        Parameters
        ----------
        decl_model: DeclModel
        num_traces: int an integer representing the number of traces to generate
        min_event: int an integer representing the minimum number of events that a trace can have
        max_event: int an integer representing the maximum number of events that a trace can have
        encode_decl_model: boolean value, indicating whether the declare model should be encoded or not.
        Because, clingo doesn't accept some names such as a name starting with capital letter.
        """
        super().__init__(num_traces, min_event, max_event, decl_model)
        self.py_logger = logging.getLogger("ASP generator")
        self.clingo_output = []
        self.clingo_current_output: typing.Sequence[Symbol]
        self.clingo_output_traces_variation = []
        # self.asp_generated_traces: typing.List[ASPResultTraceModel] | None = None
        self.asp_generated_traces: typing.Union[LogTracesType, None] = None
        self.asp_encoding = ASPEncoding().get_ASP_encoding()
        self.asp_template = ASPTemplate().value
        self.num_repetition_per_trace = 0
        self.trace_counter = 0
        self.trace_variations_key_id = 0  #

        self.lp_model: ASPModel = None
        self.encode_decl_model = encode_decl_model
        self.py_logger.debug(f"Distribution for traces {self.distributor_type}")
        self.py_logger.debug(
            f"traces: {num_traces}, events can have a trace min({self.min_events}) max({self.max_events})")
        self.compute_distribution()

    def generate_asp_from_decl_model(self, encode: bool = True, save_file: str = None,
                                     process_model: ProcessModel = None, violation: dict = None) -> str:
        """
            Generates an ASP translation of the Declare model. It takes an optional encode parameter, which is a boolean
             indicating whether to encode the model or not. The default value is True.
        """
        if process_model is None:
            process_model = self.process_model
        self.py_logger.debug("Translate declare model to ASP")
        self.lp_model = ASPModel(encode).from_decl_model(process_model, violation)
        self.__handle_activations_condition_asp_generation()
        lp = self.lp_model.to_str()
        if save_file:
            with open(save_file, 'w+') as f:
                f.write(lp)
        self.py_logger.debug(f"Declare model translated to ASP. Total Facts {len(self.lp_model.fact_names)}")

        if self.negative_traces > 0:
            self.asp_encoding = ASPEncoding(True).get_ASP_encoding(self.lp_model.fact_names)
        else:
            self.asp_encoding = ASPEncoding(False).get_ASP_encoding(self.lp_model.fact_names)
        self.py_logger.debug("ASP encoding generated")
        return lp

    def __handle_activations_condition_asp_generation(self):
        """ Handles the logic for the activations condition """
        if self.activation_conditions is None:
            return
        decl_model: DeclareParsedDataModel = self.process_model.parsed_model
        # decl_model.templates[0].template_line
        for template_def, cond_num_list in self.activation_conditions.items():
            template_def = template_def.strip()
            decl_template_parsed: [DeclareModelConstraintTemplate] = [val for key, val in decl_model.templates.items() if val.line == template_def]
            decl_template_parsed: DeclareModelConstraintTemplate = decl_template_parsed[0]
            asp_template_idx = decl_template_parsed.template_index
            if decl_template_parsed is None:
                warnings.warn("Unexpected found. Same constraint templates are defined multiple times.")
            if len(cond_num_list) == 2:
                if cond_num_list[0] <= 0:
                    # left side tends to -inf or 0 starting from cond_num_list[1]. cond_num_list = [0, 2]
                    # means it can have only at most 2 activations
                    self.lp_model.add_asp_line(f":- #count{{T:trace(A,T), activation_condition({asp_template_idx},T)}} < {cond_num_list[1]}.")
                    if decl_template_parsed.template.both_activation_condition:  # some templates's both conditions are activation conditions
                        self.lp_model.add_asp_line(f":- #count{{T:trace(A,T), correlation_condition({asp_template_idx},T)}} < {cond_num_list[1]}.")
                elif cond_num_list[1] == math.inf:
                    # right side tends to inf from cond_num_list[0] to +inf. cond_num_list = [2, math.inf]
                    # means it can have it should at least 2 activations and can go to infinite
                    self.lp_model.add_asp_line(f":- #count{{T:trace(A,T), activation_condition({asp_template_idx},T)}} > {cond_num_list[0]}.")
                    if decl_template_parsed.template.both_activation_condition:
                        self.lp_model.add_asp_line(f":- #count{{T:trace(A,T), correlation_condition({asp_template_idx},T)}} > {cond_num_list[0]}.")
                else:
                    # ie cond_num_list = [2, 4]
                    self.lp_model.add_asp_line(f":- #count{{T:trace(A,T), activation_condition({asp_template_idx},T)}} > {cond_num_list[0]}.")
                    self.lp_model.add_asp_line(f":- #count{{T:trace(A,T), activation_condition({asp_template_idx},T)}} < {cond_num_list[1]}.")
                    if decl_template_parsed.template.both_activation_condition:
                        self.lp_model.add_asp_line(f":- #count{{T:trace(A,T), correlation_condition({asp_template_idx},T)}} > {cond_num_list[0]}.")
                        self.lp_model.add_asp_line(f":- #count{{T:trace(A,T), correlation_condition({asp_template_idx},T)}} < {cond_num_list[1]}.")
            else:
                raise ValueError("Interval values are wrong. It must have only 2 values, represents, left and right interval")

    def run(self, generated_asp_file_path: typing.Union[str, None] = None):
        """
            Runs Clingo on the ASP translated, encoding and templates of the Declare model to generate the traces.
        """
        if self.negative_traces > self.log_length:
            warnings.warn("Negative traces can not be greater than total traces asked to generate. Nothing Generating")
            return
        self.trace_counter = 0
        pos_traces = self.log_length - self.negative_traces
        neg_traces = self.negative_traces
        pos_traces_dist = self.compute_distribution(pos_traces)
        neg_traces_dist = self.compute_distribution(neg_traces)
        result: LogTracesType = LogTracesType(negative=[], positive=[])
        result_variation: LogTracesType = LogTracesType(negative=[], positive=[])
        if self.negative_traces > 0:
            self.py_logger.debug("Generating negative traces")
            violation = {'constraint_violation': True, 'violate_all_constraints': self.violate_all_constraints}
            dupl_decl_model = self.__get_decl_model_with_violate_constraint()
            if generated_asp_file_path is not None:
                lp = self.generate_asp_from_decl_model(self.encode_decl_model, generated_asp_file_path + '.neg.lp',
                                                       dupl_decl_model, violation)
            else:
                lp = self.generate_asp_from_decl_model(self.encode_decl_model, None, dupl_decl_model, violation)
            self.__generate_traces(lp, neg_traces_dist, "negative")
            result['negative'] = self.clingo_output
            result_variation['negative'] = self.clingo_output_traces_variation

        self.py_logger.debug("Generating traces")
        lp = self.generate_asp_from_decl_model(self.encode_decl_model, generated_asp_file_path)
        # print(lp)
        self.__generate_traces(lp, pos_traces_dist, "positive")
        result['positive'] = self.clingo_output
        result_variation['positive'] = self.clingo_output_traces_variation

        self.py_logger.debug(f"Traces generated. Positive: {len(result['positive'])}"
                             f" Neg: {len(result['negative'])}. Parsing Trace results.")
        self.__resolve_clingo_results(result)
        self.__resolve_clingo_results_variation(result_variation)
        self.py_logger.debug(f"Trace results parsed")
        self.__pm4py_log()

    def __generate_traces(self, lp_model: str, traces_to_generate: collections.Counter, trace_type: str):
        """
            Runs Clingo on the ASP translated, encoding and templates of the Declare model to generate the traces.
        """
        self.clingo_output = []
        self.clingo_output_traces_variation = {}
        self.py_logger.debug("Start generating traces")
        # traces_to_generate = {2: 3, 4: 1}
        # for events, traces in self.traces_length.items():
        for events, traces in traces_to_generate.items():
            self.py_logger.debug(f" Total trace to generate and events: Traces:{traces}, Events: {events}, RandFrequency: 0.9")
            self.__generate_asp_trace(lp_model, events, traces, trace_type)

    def __generate_asp_trace(self, asp: str, num_events: int, num_traces: int, trace_type: str, freq: float = 0.9):
        """Generate ASP trace using Clingo based on the given paramenters and then generate also the variation"""
        # "--project --sign-def=3 --rand-freq=0.9 --restart-on-model --seed=" + seed
        for i in range(num_traces):
            self.clingo_current_output = None
            seed = randrange(0, 2 ** 32 - 1)
            self.py_logger.debug(f" Generating trace:{i + 1}/{num_traces} with events:{num_events}, seed:{seed}")
            ctl = clingo.Control([
                "-c",
                f"t={int(num_events)}",
                f"1",
                "--project",
                "--sign-def=rnd",
                f"--rand-freq={freq}",
                f"--restart-on-model",
                # f"--seed=8794",
                f"--seed={seed}",
            ])
            ctl.add(asp)
            ctl.add(self.asp_encoding)
            ctl.add(self.asp_template)
            ctl.ground([("base", [])], context=self)  # ctl.ground()
            result = ctl.solve(on_model=self.__handle_clingo_result)
            self.py_logger.debug(f" Clingo Result: {str(result)}")

            # ctl.ground([("base", [])], context=self)
            # # ctl.ground()
            # # result = ctl.solve(on_model=self.__handle_clingo_result, yield_=True)
            # result = ctl.solve(on_model=self.__handle_clingo_result)

            if result.unsatisfiable:
                """
                    Clingo was not able to generate trace events with exactly num_events, thus it returns
                    unsatisfiable.
                """
                warnings.warn(f'WARNING: Cannot generate {num_traces} {trace_type} trace/s exactly with {num_events} events with this Declare model.')
                break  # we exit because we cannot generate more traces with same params.
            elif self.num_repetition_per_trace > 0:
                self.trace_counter = self.trace_counter + 1
                self.clingo_output_traces_variation[len(self.clingo_output_traces_variation)] = []  # to generate the name of variation trace
                num = self.num_repetition_per_trace - 1
                if num > 0 and self.clingo_current_output is not None:
                    c = ASPResultTraceModel(f"variation_{i}_trace_{self.trace_counter}", self.clingo_current_output)
                    asp_variation = asp + "\n"
                    for ev in c.events:
                        asp_variation = asp_variation + f"trace({ev.name}, {ev.pos}).\n"
                    for nm in range(0, num):
                        self.__generate_asp_trace_variation(asp_variation, num_events, 1, freq)

    def __generate_asp_trace_variation(self, asp: str, num_events: int, num_traces: int, freq: float = 0.9):
        """ Generate variation traces based on the parameters"""
        # "--project --sign-def=3 --rand-freq=0.9 --restart-on-model --seed=" + seed
        seed = randrange(0, 2 ** 30 - 1)
        self.py_logger.debug(f" Generating variation trace: {num_traces}, events{num_events}, seed:{seed}")
        ctl = clingo.Control([f"-c t={int(num_events)}", "--project", f"1", # f"{int(num_traces)}",
                              f"--seed={seed}", f"--sign-def=rnd", f"--restart-on-model", f"--rand-freq={freq}"])
        ctl.add(asp)
        ctl.add(self.asp_encoding)
        ctl.add(self.asp_template)
        ctl.ground([("base", [])], context=self)
        result = ctl.solve(on_model=self.__handle_clingo_variation_result)
        self.py_logger.debug(f" Clingo variation Result :{str(result)}")
        if result.unsatisfiable:
            warnings.warn(f'WARNING: Failed to generate trace variation/case.')

    def __handle_clingo_result(self, output: clingo.solving.Model):
        """Saves clingo produced result in an array """
        symbols = output.symbols(shown=True)
        self.clingo_current_output = symbols
        self.py_logger.debug(f" Traces generated :{symbols}")
        self.clingo_output.append(symbols)

    def __resolve_clingo_results(self, results: LogTracesType):
        """Resolve clingo produced result in particular structured """
        self.asp_generated_traces = LogTracesType(positive=[], negative=[])
        i = 0
        for result in results:  # result value can be 'negative' or 'positive'
            asp_model = []
            for clingo_trace in results[result]:
                trace_model = ASPResultTraceModel(f"trace_{i}", clingo_trace)
                asp_model.append(trace_model)
                i = i + 1
            self.asp_generated_traces[result] = asp_model

    def __resolve_clingo_results_variation(self, variations_result: LogTracesType):
        """Resolve clingo produced variations result in particular structured """
        if self.asp_generated_traces is None:
            self.asp_generated_traces = LogTracesType(positive=[], negative=[])
        for result in variations_result:  # result value can be 'negative' or 'positive'
            asp_model = []
            for traces_key_id in variations_result[result]:
                i = 0
                for clingo_trace in variations_result[result][traces_key_id]:
                    trace_model = ASPResultTraceModel(f"trace_{traces_key_id}_variation_{i}", clingo_trace)
                    asp_model.append(trace_model)
                    i = i + 1
            self.asp_generated_traces[result] = self.asp_generated_traces[result] + asp_model

    def __handle_clingo_variation_result(self, output: clingo.solving.Model):
        symbols = output.symbols(shown=True)
        self.py_logger.debug(f" Variation traces generated :{symbols}")
        self.clingo_output_traces_variation[len(self.clingo_output_traces_variation) - 1].append(symbols)

    def __pm4py_log(self):
        """ Generate pm4py log """
        self.py_logger.debug(f"Generating Pm4py log")
        if self.event_log is None:
            self.event_log = D4PyEventLog()
        self.event_log.log = lg.EventLog()
        decl_model: DeclareParsedDataModel = self.process_model.parsed_model
        attr_list: dict[str, DeclareModelAttr] = decl_model.attributes_list
        tot_traces_generated = 0
        for result in self.asp_generated_traces:
            tot_traces_generated = tot_traces_generated + len(self.asp_generated_traces[result])
            traces_generated = self.asp_generated_traces[result]
            # traces_generated.sort(key=lambda x: x.name)
            traces_generated = sorted(traces_generated, key=custom_sort_trace_key)
            for trace in traces_generated:  # Positive, Negative...
                trace_gen = lg.Trace()
                trace_gen.attributes["concept:name"] = trace.name
                trace_gen.attributes["label"] = result
                for asp_event in trace.parsed_result:
                    event = lg.Event()
                    event["lifecycle:transition"] = "complete"  # NOTE: I don't know why we need it
                    event["concept:name"] = decl_model.decode_value(asp_event['name'], self.encode_decl_model)
                    for res_name, res_value in asp_event['resources'].items():
                        if res_name == '__position':  # private property
                            continue
                        res_name_decoded = decl_model.decode_value(res_name, self.encode_decl_model)
                        res_value_decoded = decl_model.decode_value(res_value, self.encode_decl_model)
                        res_value_decoded = str(res_value_decoded)
                        is_number = re.match(r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", res_value_decoded)
                        if is_number:
                            if res_name_decoded in attr_list:
                                attr = attr_list[res_name_decoded]
                                if attr.value_type != DeclareModelAttributeType.ENUMERATION:
                                    num = res_value_decoded
                                    if attr.value_type == DeclareModelAttributeType.FLOAT_RANGE:
                                        num = int(res_value_decoded) / attr.attr_value.precision
                                    elif attr.value_type == DeclareModelAttributeType.INTEGER_RANGE:
                                        num = int(res_value_decoded)
                                    res_value_decoded = num
                        if isinstance(res_value_decoded, str):
                            event[res_name_decoded] = res_value_decoded.strip()
                        else:
                            event[res_name_decoded] = res_value_decoded
                        event["time:timestamp"] = datetime.now()
                    trace_gen.append(event)
                self.event_log.log.append(trace_gen)
        if tot_traces_generated != self.log_length:
            num = self.num_repetition_per_trace
            if num <= 0:
                num = 1
            self.py_logger.warning(f'PM4PY log generated: {tot_traces_generated}/{self.log_length * num} only.')
        self.py_logger.debug(f"Pm4py generated but not saved yet")

    def to_xes(self, output_fn: str):
        """Save log in xes file"""
        if self.event_log.log is None:
            self.__pm4py_log()
        pm4py.write_xes(self.event_log.log, output_fn)

    def set_constraints_to_violate(self, tot_negative_trace: int, violate_all: bool, constraints_list: list[str]):
        """
        Add constraints to violate

        Parameters
        ----------
        tot_negative_trace
        violate_all
        constraints_list

        Returns
        -------
            declare_model_violate_constraints
        """
        assert tot_negative_trace >= 0
        self.negative_traces = tot_negative_trace
        self.violate_all_constraints = violate_all
        self.add_constraints_to_violate(constraints_list)

    def set_constraints_to_violate_by_template_index(self, tot_negative_trace: int, violate_all: bool, constraints_idx_list: list[int]):
        """
        Add constraints to violate

        Parameters
        ----------
        tot_negative_trace: the number of total negative traces to generate. Cannot be greater than the Total traces len
        violate_all: whether all constraints should be violated or some of them (decided by clingo using && op)
        constraints_idx_list: an integer list indicating the indexing of constraint templates

        Returns
        -------
        """
        templates: dict[int, DeclareModelConstraintTemplate] = self.process_model.parsed_model.templates
        constraints_list = []
        for idx in constraints_idx_list:
            constraints_list.append(templates[idx].line)
        self.set_constraints_to_violate(tot_negative_trace, violate_all, constraints_list)

    def set_number_of_repetition_per_trace(self, repetition: int):
        """
        Example: 4(number of traces) Traces with 8(repetition) repetition. Suppose we have generated 4 traces as following:
        - A B E D
        - C D A F
        - E D C A
        - B A C E
        and then for each of these trace we generate other 7 traces
        """
        self.num_repetition_per_trace = repetition

    def __get_decl_model_with_violate_constraint(self) -> DeclareModel:
        """
        Creates a duplicate process model with change in template list, assigning a boolean value to `violate` property

        Returns
        -------
        DeclModel
        """
        parsed_tmpl: dict[int, DeclareModelConstraintTemplate] = self.process_model.parsed_model.templates
        for cv in self.violatable_constraints:
            for tmpl_idx, tmpl in parsed_tmpl.items():
                if tmpl.line == cv:
                    tmpl.violate = True
        return self.process_model

    def set_activation_conditions(self, activations_list: dict[str, list[int]]):
        """
        the activation conditions are used TODO: add more info about it.
        TODO: this method should be in the ASPLogGeneration generator rather than abstract class and also self.activation_conditions.

        Parameters
        ----------
        : param activations_list dict: accepts a dictionary with key as a string which represent a declare model
            constraint template, and value as an list with number values.
            i.e 'Response[A,B] | A.attribute is value1 | |': [3, 5].
            Here key represents a constraint template and the number list represents how many times activation key of
            that constraint template should be occurred. In this example we are saying, that it should at least 3 times
            and at most 5 times.
            the value must be a list of 2 integer which represents the bounding limits of activation. You can add math.inf
            as the 2 second element. First element should be greater or equal than 0.

        Returns
        -------

        """
        self.activation_conditions = activations_list
        return self

    def set_activation_conditions_by_template_index(self, activations_list: dict[int, list[int]]):
        """
        the activation conditions are used TODO: add more info about it.
        TODO: this method should be in the ASPLogGeneration generator rather than abstract class and also self.activation_conditions.

        Parameters
        ----------
        : param activations_list dict: accepts a dictionary with key as a string which represent a declare model
            constraint template, and value as an list with number values.
            i.e 'Response[A,B] | A.attribute is value1 | |': [3, 5].
            Here key represents a constraint template and the number list represents how many times activation key of
            that constraint template should be occurred. In this example we are saying, that it should at least 3 times
            and at most 5 times.

        Returns
        -------

        """
        # indexes = activations_list.keys()  # indexes of constraint templates
        templates = self.process_model.parsed_model.templates
        n_dict = {}
        for m, n in activations_list.items():
            n_dict[templates[m].line] = n
        self.activation_conditions = n_dict
        return self

    def compute_distribution(self, total_traces: typing.Union[int, None] = None):
        """
         The compute_distribution method computes the distribution of the number of events in a trace based on
         the distributor_type parameter. If the distributor_type is "gaussian", it uses the loc and scale parameters
         to compute a Gaussian distribution. Otherwise, it uses a uniform or custom distribution.
        """
        self.py_logger.info("Computing distribution")
        d = Distributor()
        if total_traces is None:
            total_traces = self.log_length
        traces_len = {}
        if self.distributor_type == "gaussian":
            self.py_logger.info(f"Computing gaussian distribution with mu={self.loc} and sigma={self.scale}")
            assert self.loc > 1  # Mu atleast should be 2
            assert self.scale >= 0  # standard deviation must be a positive value
            result: typing.Union[collections.Counter, None] = d.distribution(
                self.loc, self.scale, total_traces, self.distributor_type, self.custom_probabilities)
            self.py_logger.info(f"Gaussian distribution result {result}")
            if result is None or len(result) == 0:
                raise ValueError("Unable to found the number of traces with events to produce in log.")
            for k, v in result.items():
                if self.min_events <= k <= self.max_events:  # TODO: ask whether the boundaries should be included
                    traces_len[k] = v
            self.py_logger.info(f"Gaussian distribution after refinement {traces_len}")
        else:
            traces_len: typing.Union[collections.Counter, None] = d.distribution(self.min_events, self.max_events, total_traces,
                                                                    self.distributor_type, self.custom_probabilities)
        self.py_logger.info(f"Distribution result {traces_len}")
        self.traces_length = traces_len
        return traces_len

    def set_distribution(self, distributor_type: typing.Literal["uniform", "gaussian", "custom"] = "uniform",
                         custom_probabilities: typing.Optional[typing.List[float]] = None,
                         loc: float = None, scale: float = None):
        self.distributor_type = distributor_type
        self.custom_probabilities = custom_probabilities
        self.scale = scale
        self.loc = loc
        return self