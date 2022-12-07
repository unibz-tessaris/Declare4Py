from __future__ import annotations

from src.declare4py.process_models.ltl_model import LTLModel
from src.declare4py.process_mining.conformance_check.conf_checking import ConformanceChecking
from src.declare4py.process_mining.conformance_check.basic_conformance_checking_results \
    import BasicConformanceCheckingResults
from src.declare4py.process_mining.log_analyzer import LogAnalyzer


"""
Provides basic conformance checking functionalities
"""


class BasicMPDeclareConformanceChecking(ConformanceChecking):

    def __init__(self, template_str: str, max_declare_cardinality: int, activation: str, target: str,
                 act_cond: str, trg_cond: str, time_cond: str, min_support: float,
                 consider_vacuity: bool, log: LogAnalyzer, ltl_model: LTLModel):
        self.template_str: str | None = template_str
        self.activation: str | None = activation
        self.target: str | None = target
        self.act_cond: str | None = act_cond
        self.trg_cond: str | None = trg_cond
        self.time_cond: str | None = time_cond
        self.min_support: float = min_support  # or 1.0
        self.max_declare_cardinality: int = max_declare_cardinality
        super().__init__(consider_vacuity, log, ltl_model)
        self.basic_conformance_checking_results: BasicConformanceCheckingResults | None = None

    def run(self, consider_vacuity: bool) -> BasicConformanceCheckingResults:
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
        if self.log_analyzer is None:
            raise RuntimeError("You must load the log before checking the model.")
        if self.process_model is None:
            raise RuntimeError("You must load the DECLARE model before checking the model.")

        self.basic_conformance_checking_results = BasicConformanceCheckingResults({})
        for i, trace in enumerate(self.log_analyzer.log):
            trc_res = self.constraint_checker.check_trace_conformance(trace, self.process_model, consider_vacuity)
            self.basic_conformance_checking_results[(i, trace.attributes["concept:name"])] = trc_res
        return self.basic_conformance_checking_results
