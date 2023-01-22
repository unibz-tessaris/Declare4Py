from __future__ import annotations

import collections
import logging
import re
import typing
import warnings
from datetime import datetime, timedelta, timezone
from random import randrange

import copy
import clingo
from pm4py.objects.log import obj as lg
from pm4py.objects.log.exporter.xes import exporter

from src.declare4py.pm_tasks.log_generation.log_generator import LogGenerator
from src.declare4py.process_models.decl_model import DeclModel, DeclareParsedDataModel, DeclareModelAttributeType, \
    DeclareModelTemplateDataModel
from src.declare4py.pm_tasks.log_generation.asp.asp_translator.asp_translator import TranslatedASPModel, ASPTranslator
from src.declare4py.pm_tasks.log_generation.asp.asp_utils.asp_encoding import ASPEncoding
from src.declare4py.pm_tasks.log_generation.asp.asp_utils.asp_result_parser import ASPResultTraceModel
from src.declare4py.pm_tasks.log_generation.asp.asp_utils.asp_template import ASPTemplate
from src.declare4py.process_models.process_model import ProcessModel


class LogTracesType(typing.TypedDict):
    positive: typing.List
    negative: typing.List


class AspGenerator(LogGenerator):

    def __init__(self, decl_model: DeclModel, num_traces: int, min_event: int, max_event: int,
                 encode_decl_model: bool = True, activation: dict | None = None):
        """
        ASPGenerator generates the log from declare model which translate declare model
        into ASP, and then it passes to the clingo, which generates the traces

        Parameters
        ----------
        decl_model: DeclModel
        num_traces: int an integer representing the number of traces to generate
        min_event: int an integer representing the minimum number of events that a trace can have
        max_event: int an integer representing the maximum number of events that a trace can have
        distributor_type: "uniform" | "gaussian" | "custom"
        custom_probabilities: list of floats which represents the probabilities and the total sum of values must be 1
        loc: mu:float in case gaussian distribution is used, You must provide mu and sigma
        scale sigma:float in case gaussian distribution is used, You must provide mu and sigma
        """
        super().__init__(num_traces, min_event, max_event, decl_model)
        self.py_logger = logging.getLogger("ASP generator")
        self.clingo_output = []
        # self.asp_generated_traces: typing.List[ASPResultTraceModel] | None = None
        self.asp_generated_traces: LogTracesType | None = None
        self.asp_encoding = ASPEncoding().get_alp_encoding()
        self.asp_template = ASPTemplate().value

        self.lp_model: TranslatedASPModel = None
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
        self.lp_model = ASPTranslator().from_decl_model(process_model, encode, violation)
        self.__handle_activations_condition_asp_generation()
        lp = self.lp_model.to_str()
        if save_file:
            with open(save_file, 'w+') as f:
                f.write(lp)
        self.py_logger.debug(f"Declare model translated to ASP. Total Facts {len(self.lp_model.fact_names)}")
        self.asp_encoding = ASPEncoding().get_alp_encoding(self.lp_model.fact_names)
        self.py_logger.debug("ASP encoding generated")
        return lp

    def __handle_activations_condition_asp_generation(self):
        if self.activation_conditions is None:
            return
        decl_model: DeclareParsedDataModel = self.process_model.parsed_model
        # decl_model.templates[0].template_line
        for template_def, cond_num_list in self.activation_conditions.items():
            template_def = template_def.strip()
            decl_template_parsed: DeclareModelTemplateDataModel = [d for d in decl_model.templates if d.template_line == template_def]
            decl_template_parsed = decl_template_parsed[0]
            asp_template_idx = decl_template_parsed.template_index_id
            if decl_template_parsed is None or len(decl_template_parsed) == 0 or len(decl_template_parsed) > 1:
                warnings.warn("Unexpected found. Same constraint templates are defined multiple times.")
            if len(cond_num_list) >= 1:
                self.lp_model.add_asp_line(f":- #count{{T:trace(A,T), activation_condition({asp_template_idx},T)}} < {cond_num_list[0]}.")
                if decl_template_parsed.template.both_activation_condition:
                    self.lp_model.add_asp_line(f":- #count{{T:trace(A,T), correlation_condition({asp_template_idx},T)}} < {cond_num_list[0]}.")
            if len(cond_num_list) == 2:
                self.lp_model.add_asp_line(
                    f":- #count{{T:trace(A,T), activation_condition({asp_template_idx},T)}} > {cond_num_list[1]}.")
                if decl_template_parsed.template.both_activation_condition:
                    self.lp_model.add_asp_line(
                        f":- #count{{T:trace(A,T), correlation_condition({asp_template_idx},T)}} > {cond_num_list[1]}.")

    def run(self, generated_asp_file_path: str | None = None):
        """
            Runs Clingo on the ASP translated, encoding and templates of the Declare model to generate the traces.
        """
        if self.negative_traces > self.log_length:
            warnings.warn("Negative traces can not be greater than total traces asked to generate. Nothing Generating")
            return

        pos_traces = self.log_length - self.negative_traces
        neg_traces = self.negative_traces
        pos_traces_dist = self.compute_distribution(pos_traces)
        neg_traces_dist = self.compute_distribution(neg_traces)
        result: LogTracesType = LogTracesType(negative=[], positive=[])
        if self.negative_traces > 0:
            self.py_logger.debug("Generating negative traces")
            violation = {'constraint_violation': True, 'violate_all_constraints': self.violate_all_constraints}
            dupl_decl_model = self.__get_decl_model_with_violate_constraint()
            if generated_asp_file_path is not None:
                lp = self.generate_asp_from_decl_model(self.encode_decl_model, generated_asp_file_path + '.neg.lp',
                                                       dupl_decl_model, violation)
            else:
                lp = self.generate_asp_from_decl_model(self.encode_decl_model, None, dupl_decl_model, violation)
            self.__generate_log(lp, neg_traces_dist)
            result['negative'] = self.clingo_output

        self.py_logger.debug("Generating traces")
        lp = self.generate_asp_from_decl_model(self.encode_decl_model, generated_asp_file_path)
        self.__generate_log(lp, pos_traces_dist)
        result['positive'] = self.clingo_output

        self.py_logger.debug(f"Traces generated. Positive: {len(result['positive'])}"
                             f" Neg: {len(result['negative'])}. Parsing Trace results.")
        self.__format_to_custom_asp_structure(result)
        self.py_logger.debug(f"Trace results parsed")
        self.__pm4py_log()

    def __generate_log(self, lp_model: str, traces_to_generate: collections.Counter):
        """
            Runs Clingo on the ASP translated, encoding and templates of the Declare model to generate the traces.
        """
        self.clingo_output = []
        self.py_logger.debug("Start generating traces")
        # traces_to_generate = {2: 3, 4: 1}
        # for events, traces in self.traces_length.items():
        for events, traces in traces_to_generate.items():
            self.py_logger.debug(f" Total trace to generate and events: Traces:{traces}, Events: {events},"
                                 f" RandFrequency: 0.9")
            self.__generate_asp_trace(lp_model, events, traces)

    def __generate_asp_trace(self, asp: str, num_events: int, num_traces: int, freq: float = 0.9):
        # "--project --sign-def=3 --rand-freq=0.9 --restart-on-model --seed=" + seed
        for i in range(num_traces):
            seed = randrange(0, 2 ** 32 - 1)
            self.py_logger.debug(f" Generating trace:{i + 1}/{num_traces} with events:{num_events}, seed:{seed}")
            ctl = clingo.Control([f"-c t={int(num_events)}", "--project",
                                  # f"{int(num_traces)}",
                                  f"1",
                                  f"--seed={seed}",
                                  f"--sign-def=rnd",
                                  f"--restart-on-model",
                                  f"--rand-freq={freq}"])
            ctl.add(asp)
            ctl.add(self.asp_encoding)
            ctl.add(self.asp_template)
            ctl.ground([("base", [])], context=self)
            result = ctl.solve(on_model=self.__handle_clingo_result)
            self.py_logger.debug(f" Clingo Result :{str(result)}")
            if result.unsatisfiable:
                warnings.warn(f'WARNING: Cannot generate traces with {num_events} events with this model.')
                # self.py_logger.warning(f" Unsatisfied result produced by clingo. It will retry with"
                #                        f" increasing the number of events.")
                # self.__generate_asp_trace(asp, num_events + 1, 1, freq)

    def __format_to_custom_asp_structure(self, results: LogTracesType):
        self.asp_generated_traces = LogTracesType(positive=[], negative=[])
        i = 0
        for result in results:  # result value can be 'negative' or 'positive'
            asp_model = []
            for clingo_trace in results[result]:
                trace_model = ASPResultTraceModel(f"trace_{i}", clingo_trace)
                asp_model.append(trace_model)
                i = i + 1
            self.asp_generated_traces[result] = asp_model

    def __handle_clingo_result(self, output: clingo.solving.Model):
        symbols = output.symbols(shown=True)
        self.py_logger.debug(f" Traces generated :{symbols}")
        self.clingo_output.append(symbols)

    def __pm4py_log(self):
        self.py_logger.debug(f"Generating Pm4py log")
        self.log_analyzer.log = lg.EventLog()
        decl_encoded_model: DeclareParsedDataModel = self.process_model.parsed_model
        attr_list = decl_encoded_model.attributes_list
        tot_traces_generated = 0

        # current_time = datetime(tzinfo=timezone(timedelta(hours=1))).now()
        dt = datetime.now()
        current_time = datetime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second,
                                tzinfo=timezone(timedelta(hours=1)))
        formatted_time = current_time.isoformat()

        for result in self.asp_generated_traces:
            tot_traces_generated = tot_traces_generated + len(self.asp_generated_traces[result])
            for trace in self.asp_generated_traces[result]:
                trace_gen = lg.Trace()
                trace_gen.attributes["concept:name"] = trace.name
                trace_gen.attributes["label"] = result
                for asp_event in trace.events:
                    event = lg.Event()
                    event["lifecycle:transition"] = "complete"  # NOTE: I don't know why but need
                    event["concept:name"] = decl_encoded_model.decode_value(asp_event.name)
                    for res_name, res_value in asp_event.resource.items():
                        res_name_decoded = decl_encoded_model.decode_value(res_name)
                        res_value_decoded = decl_encoded_model.decode_value(res_value)
                        res_value_decoded = str(res_value_decoded)
                        is_number = re.match(r"[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", res_value_decoded)
                        if is_number:
                            if res_name_decoded in attr_list:
                                attr = attr_list[res_name_decoded]
                                if attr["value_type"] != DeclareModelAttributeType.ENUMERATION:
                                    # num = int(res_value_decoded) / attr["range_precision"]
                                    num = res_value_decoded
                                    dmat = DeclareModelAttributeType
                                    if attr["value_type"] in [dmat.FLOAT]:
                                        num = int(res_value_decoded) / attr["range_precision"]
                                    if attr["value_type"] in [dmat.FLOAT_RANGE]:
                                        num = int(res_value_decoded) / attr["range_precision"]
                                    res_value_decoded = str(num)
                        event[res_name_decoded] = str(res_value_decoded).strip()
                        # event["time:timestamp"] = datetime.now().timestamp()  # + timedelta(hours=c).datetime
                        # event["time:timestamp"] = datetime.now().isoformat()  # + timedelta(hours=c).datetime
                        # event["time:timestamp"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+%z%Z")  # + timedelta(hours=c).datetime
                        event["time:timestamp"] = formatted_time
                    trace_gen.append(event)
                self.log_analyzer.log.append(trace_gen)
        if tot_traces_generated != self.log_length:
            self.py_logger.warning(f'PM4PY log generated: {tot_traces_generated}/{self.log_length} only.')
        self.py_logger.debug(f"Pm4py generated but not saved yet")

    def to_xes(self, output_fn: str):
        if self.log_analyzer.log is None:
            self.__pm4py_log()
        exporter.apply(self.log_analyzer.log, output_fn)

    def add_constraints_subset_to_violate(self, constraints_list: list[str]):
        """
        Add constraints to violate

        Parameters
        ----------
        constraints_list

        Returns
        -------

        """
        self.declare_model_violate_constraints = constraints_list

    def __get_decl_model_with_violate_constraint(self) -> DeclModel | ProcessModel:
        """
        Creates a duplicate process model with change in template list, assigning a boolean value to `violate` property

        Returns
        -------
        DeclModel
        """
        dpm = copy.deepcopy(self.process_model)
        parsed_tmpl = dpm.parsed_model.templates
        for cv in self.declare_model_violate_constraints:
            for tmpl in parsed_tmpl:
                if tmpl.template_line == cv:
                    tmpl.violate = True
        return dpm
