import typing
import collections
import logging

from clingo import Symbol

from Declare4Py.ProcessMiningTasks.AbstractLogGenerator import AbstractLogGenerator
from Declare4Py.ProcessModels.Declare4PyModel import DeclareModel
from Declare4Py.ProcessMiningTasks.LogGenerator.ASP.ASPUtils.Distribution import Distribution
from Declare4Py.ProcessMiningTasks.LogGenerator.ASP.ASPUtils import ASPTemplate
from Declare4Py.ProcessMiningTasks.LogGenerator.ASP.ASPUtils.ASPEncoding import ASPEncoder
from Declare4Py.ProcessMiningTasks.LogGenerator.ASP.ASPTranslator.ASPModel import ASPModel


class LogTracesType(typing.TypedDict):
    positive: typing.List
    negative: typing.List


class AspGenerator(AbstractLogGenerator):

    def __init__(self,
                 decl_model: DeclareModel,
                 num_traces: int,
                 min_event: int,
                 max_event: int,
                 encode_decl_model: bool = True,
                 include_boundaries: bool = True
                 ):
        """
        ASP generates the log from declare model which translate declare model
        into ASP, and then it passes to the clingo, which generates the traces

        Parameters
        ----------
        decl_model: DeclModel
            Declare model object
        num_traces: int
            an integer representing the number of traces to generate
        min_event: int
            an integer representing the minimum number of events that a trace can have
        max_event: int
            an integer representing the maximum number of events that a trace can have
        encode_decl_model: boolean
            indicating whether the declare model should be encoded or not.

        Because, clingo doesn't accept some names such as a name starting with capital letter.
        """
        """Super class LogGenerator"""
        super().__init__(num_traces, min_event, max_event, decl_model)

        """DEF Logger"""
        self.py_logger: logging.Logger = logging.getLogger("ASP generator")

        """DEF clingo outputs"""
        # self.clingo_output: typing.List = []
        # self.clingo_current_output: typing.Sequence[Symbol]
        # self.clingo_output_traces_variation: typing.List = []

        """DEF ASP outputs"""
        # self.asp_generated_traces: typing.List[ASPResultTraceModel] | None = None
        # self.asp_generated_traces: typing.Union[LogTracesType, None] = None
        # self.asp_encoding = ASPEncoder.get_asp_encoding()
        # self.asp_template: str = ASPTemplate.value

        """DEF specs and counters"""
        # self.num_repetition_per_trace: int = 0
        # self.trace_counter: int = 0
        # self.trace_variations_key_id: int = 0
        # self.parallel_workers: int = 10
        # self.trace_counter_id: int = 0
        # self.run_parallel: bool = False
        # self.parallel_futures: typing.List = []
        # self._custom_counter: typing.Dict[str, typing.Union[collections.Counter, None]] = {
        #    "positive": None,
        #    "negative": None
        # }
        # self.include_boundaries: bool = include_boundaries

        """DEF Model"""
        # self.lp_model: typing.Union[ASPModel, None] = None
        # self.traces_generated_events: typing.Union[typing.List, None] = None
        # self.encode_decl_model: bool = encode_decl_model

        """Logger opt"""
        self.py_logger.debug(f"Distribution for traces {self.distributor_type}")
        self.py_logger.debug(f"traces: {num_traces}, "
                             f"events can have a trace min({self.min_events}) max({self.max_events})")

        # Constraint violations
        """
        A trace is positive if it satisfies all three constraints that are defined in this model. Whereas it is
        negative if at least one of them is not satisfied. In the generated log you sent me, in all traces the 
        constraint " Response[Driving_Test, Resit] |A.Grade<=2 | " is not satisfied, i.e. it is violated!
        """
        # self.violate_all_constraints: bool = False  # if false: clingo will decide itself the constraints to violate
        # self.violable_constraints: [str] = []  # constraint list which should be violated
        # self.negative_traces = 0

        # constraint template conditions
        # self.activation_conditions: typing.Union[dict, None] = None

    def run(self, *args, **kwargs) -> typing.Any:
        """
        modello declare -> tradotto in modello ASP -> Dare il modello ASP ad un ASP solver.
        ASO Solver si chiama Clingo, Clingo restituisce un output -> Che sono le tracce (con formaztazione loro)
        Ritradurre la traccia in un event log
        Declare Model-> ASP Model -> Clingo -> Tracce formattate -> Log

        """
        self.compute_distribution()
        pass

    """
    def add_constraints_to_violate(self, constrains_to_violate: typing.Union[str, list[str]] = True):
        if isinstance(constrains_to_violate, str):
            self.violable_constraints.append(constrains_to_violate)
        else:
            self.violable_constraints = constrains_to_violate
        return self
    """
