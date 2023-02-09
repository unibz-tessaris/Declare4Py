from __future__ import annotations

import pdb

from src.declare4py.pm_tasks.basic_conformance_checking.basic_conformance_checking_results import \
    BasicConformanceCheckingResults
from src.declare4py.pm_tasks.conf_checking import ConformanceChecking
from src.declare4py.d4py_event_log import D4PyEventLog
from src.declare4py.process_models.decl_model import DeclModel
from src.declare4py.utility.Declare.constraint_checker import ConstraintCheck

"""
Provides basic conformance checking functionalities
"""


class BasicMPDeclareConformanceChecking(ConformanceChecking):
    """
    def __init__(self, template_str: str, max_declare_cardinality: int, activation: str, target: str,
                 act_cond: str, trg_cond: str, time_cond: str, min_support: float,
                 consider_vacuity: bool, log: D4PyEventLog, ltl_model: LTLModel):
        self.template_str: Optional[str] = template_str
        self.activation: Optional[str] = activation
        self.target: Optional[str] = target
        self.act_cond: Optional[str] = act_cond
        self.trg_cond: Optional[str] = trg_cond
        self.time_cond: Optional[str] = time_cond
        self.min_support: float = min_support  # or 1.0
        self.max_declare_cardinality: int = max_declare_cardinality
        self.constraint_checker = ConstraintCheck(consider_vacuity)
        super().__init__(consider_vacuity, log, ltl_model)
        self.basic_conformance_checking_results: BasicConformanceCheckingResults = BasicConformanceCheckingResults()
    """
    def __init__(self, consider_vacuity: bool, log: D4PyEventLog, declare_model: DeclModel):
        super().__init__(consider_vacuity, log, declare_model)
        #self.template_str: Optional[str] = template_str
        #self.activation: Optional[str] = activation
        #self.target: Optional[str] = target
        #self.act_cond: Optional[str] = act_cond
        #self.trg_cond: Optional[str] = trg_cond
        #self.time_cond: Optional[str] = time_cond
        #self.min_support: float = min_support  # or 1.0
        #self.max_declare_cardinality: int = max_declare_cardinality
        #self.constraint_checker = ConstraintCheck()
        self.basic_conformance_checking_results: BasicConformanceCheckingResults = BasicConformanceCheckingResults({})

    def run(self) -> BasicConformanceCheckingResults:
        """
        Performs conformance checking for the provided event log and DECLARE model.

        Parameters
        ----------
        consider_vacuity : bool
            True means that vacuously satisfied traces are considered as satisfied, violated otherwise.

        Returns
        -------
        conformance_checking_results
            dictionary where the key is a list containing trace position inside the log and the trace name, the value is
            a dictionary with keys the names of the constraints and values a CheckerResult object containing
            the number of pendings, activations, violations, fulfillments and the truth value of the trace for that
            constraint.
        """
        if self.event_log is None:
            raise RuntimeError("You must load the log before checking the model.")
        if self.process_model is None:
            raise RuntimeError("You must load the DECLARE model before checking the model.")

        for i, trace in enumerate(self.event_log.log):
            trc_res = ConstraintCheck().check_trace_conformance(trace, self.process_model, self.consider_vacuity)
            import pdb
            pdb.set_trace()
            self.basic_conformance_checking_results[(i, trace.attributes["concept:name"])] = trc_res
        return self.basic_conformance_checking_results
