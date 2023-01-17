from __future__ import annotations

import collections
import logging
import re
import typing
import warnings
from datetime import datetime
from random import randrange

import copy
import clingo
from pm4py.objects.log import obj as lg
from pm4py.objects.log.exporter.xes import exporter

from src.declare4py.pm_tasks.log_generation.log_generator import LogGenerator
from src.declare4py.process_models.decl_model import DeclModel, DeclareParsedDataModel, DeclareModelAttributeType
from src.declare4py.pm_tasks.log_generation.asp.asp_translator.asp_translator import TranslatedASPModel, ASPTranslator
from src.declare4py.pm_tasks.log_generation.asp.asp_utils.asp_encoding import ASPEncoding
from src.declare4py.pm_tasks.log_generation.asp.asp_utils.asp_result_parser import ASPResultTraceModel
from src.declare4py.pm_tasks.log_generation.asp.asp_utils.asp_template import ASPTemplate
from src.declare4py.pm_tasks.log_generation.asp.asp_utils.distribution import Distributor
from src.declare4py.process_models.process_model import ProcessModel


class AspGenerator(LogGenerator):

    def __init__(self, decl_model: DeclModel, num_traces: int, min_event: int, max_event: int,
                 distributor_type: typing.Literal["uniform", "gaussian", "custom"] = "uniform",
                 custom_probabilities: typing.Optional[typing.List[float]] = None,
                 loc: float = None, scale: float = None, encode_decl_model: bool = True,
                 activation: dict | None = None
                 ):
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
        self.asp_generated_traces: typing.List[ASPResultTraceModel] | None = None
        self.asp_encoding = ASPEncoding().get_alp_encoding()
        self.asp_template = ASPTemplate().value
        self.distributor_type = distributor_type
        self.custom_probabilities = custom_probabilities
        self.scale = scale
        self.loc = loc
        self.violate_all_constraints_in_subset: bool = False  # IF false: clingo will decide itself the constraints to violate
        self.declare_model_violate_constraints: [str] = []  # constraint list which should be violated
        self.traces_length = {}
        self.distributor_instance: Distributor = Distributor()
        self.lp_model: TranslatedASPModel = None
        self.encode_decl_model = encode_decl_model
        self.py_logger.debug(f"Distribution for traces {self.distributor_type}")
        self.py_logger.debug(f"traces length: {num_traces}, events can have a trace min({self.min_events})"
                             f" max({self.max_events})")
        self.compute_distribution()

    def compute_distribution(self):
        """
         The compute_distribution method computes the distribution of the number of events in a trace based on
         the distributor_type parameter. If the distributor_type is "gaussian", it uses the loc and scale parameters
         to compute a Gaussian distribution. Otherwise, it uses a uniform or custom distribution.
        """
        self.py_logger.info("Start computing distribution")
        d = self.distributor_instance
        if self.distributor_type == "gaussian":
            self.py_logger.info(f"Computing gaussian distribution with mu={self.loc} and sigma={self.scale}")
            assert self.loc > 1  # Mu atleast should be 2
            assert self.scale >= 0  # standard deviation must be a positive value
            result: collections.Counter | None = d.distribution(
                self.loc, self.scale, self.log_length, self.distributor_type, self.custom_probabilities)
            self.py_logger.info(f"Gaussian distribution result {result}")
            if result is None or len(result) == 0:
                raise ValueError("Unable to found the number of traces with events to produce in log.")
            for k, v in result.items():
                if self.min_events <= k <= self.max_events:  # TODO: ask whether the boundaries should be included
                    self.traces_length[k] = v
            self.py_logger.info(f"Gaussian distribution after refinement {self.traces_length}")
        else:
            self.traces_length: collections.Counter | None = d.distribution(
                self.min_events, self.max_events, self.log_length, self.distributor_type, self.custom_probabilities)
        self.py_logger.info(f"Distribution result {self.traces_length}")

    def generate_asp_from_decl_model(self, encode: bool = True, save_file: str = None) -> str:
        """
            Generates an ASP translation of the Declare model. It takes an optional encode parameter, which is a boolean
             indicating whether to encode the model or not. The default value is True.
        """
        self.py_logger.debug("Starting translate declare model to ASP")
        self.lp_model = ASPTranslator().from_decl_model(self.process_model, encode)
        lp = self.lp_model.to_str()
        if save_file:
            with open(save_file, 'w+') as f:
                f.write(lp)
        self.py_logger.debug(f"Declare model translated to ASP. Total Facts {len(self.lp_model.fact_names)}")
        self.asp_encoding = ASPEncoding().get_alp_encoding(self.lp_model.fact_names)
        self.py_logger.debug("ASP encoding generated")
        return lp

    def run(self, generated_asp_file_path: str | None = None, negative_traces: int = 0):
        """
            Runs Clingo on the ASP translated, encoding and templates of the Declare model to generate the traces.
        """
        if negative_traces > self.log_length:
            warnings.warn("Negative traces can not be greater than total traces asked to generate. Nothing Generating")
            return

        if negative_traces > 0:
            nDeclModel = self.__get_decl_model_with_violate_constraint()
            lp = self.generate_asp_from_decl_model(self.encode_decl_model, generated_asp_file_path)

        # self.__generate_log(generated_asp_file_path, 89565)  ### TODO: how to handle distribution for neg and pos traces

    def __generate_log(self, lp_model: str, traces_to_generate: int):
        """
            Runs Clingo on the ASP translated, encoding and templates of the Declare model to generate the traces.
        """
        self.py_logger.debug("Starting RUN method")
        self.clingo_output = []
        self.py_logger.debug("Start generating traces")
        # traces_length = {2: 3, 4: 1}
        for events, traces in self.traces_length.items():
            self.py_logger.debug(f" Total trace to generate and events: Traces:{traces}, Events: {events},"
                                 f" RandFrequency: 0.9")
            self.__generate_asp_trace(lp_model, events, traces)
        self.py_logger.debug(f"Traces generated. Parsing Trace results")
        self.__format_to_custom_asp_structure()
        self.py_logger.debug(f"Trace results parsed")
        self.__pm4py_log()

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

    def __format_to_custom_asp_structure(self):
        self.asp_generated_traces = []
        asp_model = self.asp_generated_traces
        i = 0
        for clingo_trace in self.clingo_output:
            trace_model = ASPResultTraceModel(f"trace_{i}", clingo_trace)
            asp_model.append(trace_model)
            i = i + 1

    def __handle_clingo_result(self, output: clingo.solving.Model):
        symbols = output.symbols(shown=True)
        print('symbols', symbols)
        self.py_logger.debug(f" Traces generated :{symbols}")
        self.clingo_output.append(symbols)

    def __pm4py_log(self):
        self.py_logger.debug(f"Generating Pm4py log")
        self.log_analyzer.log = lg.EventLog()
        decl_encoded_model: DeclareParsedDataModel = self.process_model.parsed_model
        attr_list = decl_encoded_model.attributes_list
        for trace in self.asp_generated_traces:
            trace_gen = lg.Trace()
            trace_gen.attributes["concept:name"] = trace.name
            for asp_event in trace.events:
                event = lg.Event()
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
                event["time:timestamp"] = datetime.now().timestamp()  # + timedelta(hours=c).datetime
                trace_gen.append(event)
            self.log_analyzer.log.append(trace_gen)
        l = len(self.asp_generated_traces)
        if l != self.log_length:
            self.py_logger.warning(f'PM4PY log generated: {l}/{self.log_length} only.')
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
        parsed_tmpl = dpm.templates
        for cv in self.declare_model_violate_constraints:
            for tmpl in parsed_tmpl:
                if tmpl.template_line == cv:
                    tmpl.violate = True
        return dpm
