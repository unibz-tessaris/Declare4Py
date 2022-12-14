from __future__ import annotations

import collections
import logging
import re
import typing
from datetime import datetime
from random import randrange

import clingo
from pm4py.objects.log import obj as lg
from pm4py.objects.log.exporter.xes import exporter

from src.declare4py.pm_tasks.log_generation.log_generator import LogGenerator
from src.declare4py.process_models.decl_model import DeclModel, DeclareParsedDataModel, DeclareModelAttributeType
from src.declare4py.pm_tasks.log_generation.asp.asp_translator.asp_translator import TranslatedASPModel, ASPTranslator
from src.declare4py.pm_tasks.log_generation.asp.asp_utils.asp_encoding import ASPEncoding
from src.declare4py.pm_tasks.log_generation.asp.asp_utils.asp_result_parser import AspResultLogModel
from src.declare4py.pm_tasks.log_generation.asp.asp_utils.asp_result_parser import ASPResultTraceModel
from src.declare4py.pm_tasks.log_generation.asp.asp_utils.asp_template import ASPTemplate
from src.declare4py.pm_tasks.log_generation.asp.asp_utils.distribution import Distributor


class AspGenerator(LogGenerator):

    def __init__(self, decl_model: DeclModel, num_traces: int, min_event: int, max_event: int,
                 distributor_type: typing.Literal["uniform", "gaussian", "custom"] = "uniform",
                 custom_probabilities: typing.Optional[typing.List[float]] = None,
                 loc: float = None, scale: float = None, encode_decl_model: bool = True):
        """
        ASPGenerator generates the log from declare model which translate declare model
        into ASP, and then it passes to the clingo, which generates the traces

        Parameters
        ----------
        decl_model: DeclModel
        num_traces: int
        min_event: int
        max_event: int
        distributor_type: "uniform" | "gaussian" | "custom"
        custom_probabilities: list of floats which represents the probabilities and the total sum of values must be 1
        loc: mu:float in case gaussian distribution is used, You must provide mu and sigma
        scale sigma:float in case gaussian distribution is used, You must provide mu and sigma
        """
        super().__init__(num_traces, min_event, max_event, decl_model)
        self.py_logger = logging.getLogger("ASP generator")
        self.clingo_output = []
        self.asp_custom_structure: AspResultLogModel | None = None
        self.asp_encoding = ASPEncoding().get_alp_encoding()
        self.asp_template = ASPTemplate().value
        self.distributor_type = distributor_type
        self.custom_probabilities = custom_probabilities
        self.scale = scale
        self.loc = loc
        self.traces_length = {}
        self.distributor_instance: Distributor = Distributor()
        self.lp_model: TranslatedASPModel = None
        self.encode_decl_model = encode_decl_model
        self.py_logger.debug(f"Distribution for traces {self.distributor_type}")
        self.py_logger.debug(f"traces length: {num_traces}, events can have a trace min({self.min_events})"
                             f" max({self.max_events})")
        self.compute_distribution()

    def compute_distribution(self):
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

    def generate_asp_from_decl_model(self, encode: bool = True) -> str:
        self.py_logger.debug("Starting translate declare model to ASP")
        self.lp_model = ASPTranslator().from_decl_model(self.process_model, encode)
        lp = self.lp_model.to_str()
        with open('../generated.asp', 'w+') as f:
            f.write(lp)
        self.py_logger.debug(f"Declare model translated to ASP. Total Facts {len(self.lp_model.fact_names)}")
        self.asp_encoding = ASPEncoding().get_alp_encoding(self.lp_model.fact_names)
        self.py_logger.debug("ASP encoding generated")
        return lp

    def run(self):
        self.py_logger.debug("Starting RUN method")
        lp = self.generate_asp_from_decl_model(self.encode_decl_model)
        self.clingo_output = []
        self.py_logger.debug("Start generating traces")
        for events, traces in self.traces_length.items():
            random_seed = randrange(0, 2 ** 32 - 1)
            self.py_logger.debug(f"Total trace to generate and events: Traces:{traces}, Events: {events},"
                                 f" RandomSeed:{random_seed}, RandFrequency: 0.9")
            self.__generate_asp_trace(lp, events, traces, random_seed)
        self.py_logger.debug(f"Traces generated")
        self.py_logger.debug(f"Parsing Trace results")
        self.__format_to_custom_asp_structure()
        self.py_logger.debug(f"Trace results parsed")
        self.__pm4py_log()

    def __generate_asp_trace(self, asp: str, num_events: int, num_traces: int,
                             seed: int, freq: float = 0.9):
        ctl = clingo.Control([f"-c t={int(num_events)}", f"{int(num_traces)}", f"--seed={seed}", f"--rand-freq={freq}"])
        ctl.add(asp)
        ctl.add(self.asp_encoding)
        ctl.add(self.asp_template)
        ctl.ground([("base", [])], context=self)
        ctl.solve(on_model=self.__handle_clingo_result)

    def __format_to_custom_asp_structure(self):
        self.asp_custom_structure = AspResultLogModel()
        asp_model = self.asp_custom_structure
        i = 0
        for clingo_trace in self.clingo_output:
            trace_model = ASPResultTraceModel(f"trace_{i}", clingo_trace, self.lp_model.scale_number)
            asp_model.traces.append(trace_model)
            i = i + 1

    def __handle_clingo_result(self, output: clingo.solving.Model):
        symbols = output.symbols(shown=True)
        print("output", output)
        self.clingo_output.append(symbols)

    def __pm4py_log(self):
        self.py_logger.debug(f"Generating Pm4py log")
        self.log_analyzer.log = lg.EventLog()
        decl_encoded_model: DeclareParsedDataModel = self.process_model.parsed_model
        attr_list = decl_encoded_model.attributes_list
        for trace in self.asp_custom_structure.traces:
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
                                num = int(res_value_decoded) / self.lp_model.scale_number
                                dmat = DeclareModelAttributeType
                                if attr["value_type"] in [dmat.INTEGER_RANGE, dmat.INTEGER]:
                                    if isinstance(num, float):
                                        # age: integer between 1 to 10
                                        # but after scaled up this for example with 100, this would have become value
                                        # from 100 to 1000 and log/cling might have generated the generated the value
                                        # for example 485 but scaling down back, it would become 4.85, which is not an
                                        # integer but float. I don't know what to do in this case, right now, i am
                                        # scaling down and round to nearst integer
                                        self.py_logger.info(f"Unsafe: attribute \"{res_name_decoded}\" =>"
                                                            f" \"{attr['value']}\" is type"
                                                            f" of integer but scaling down from a float."
                                                            f" Value: {res_value_decoded}"
                                                            f" precision: {self.lp_model.scale_number}"
                                                            f" num: {num}")
                                    num = round(num)
                                res_value_decoded = str(num)
                    event[res_name_decoded] = str(res_value_decoded).strip()
                event["time:timestamp"] = datetime.now().timestamp()  # + timedelta(hours=c).datetime
                trace_gen.append(event)
            self.log_analyzer.log.append(trace_gen)
        self.py_logger.debug(f"Pm4py generated but not saved yet")

    def to_xes(self, output_fn: str):
        if self.log_analyzer.log is None:
            self.__pm4py_log()
        exporter.apply(self.log_analyzer.log, output_fn)
