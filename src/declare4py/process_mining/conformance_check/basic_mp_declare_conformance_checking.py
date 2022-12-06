from __future__ import annotations

from src.declare4py.models.ltl_model import LTLModel
from src.declare4py.process_mining.conformance_check.api_functions import check_trace_conformance
from src.declare4py.process_mining.conformance_check.conf_checking import ConformanceChecking
from src.declare4py.process_mining.conformance_check.basic_conformance_checking_results \
    import BasicConformanceCheckingResults
from src.declare4py.process_mining.log_analyzer import LogAnalyzer

"""
Provides basic conformance checking functionalities

Parameters
--------
    conformance_checking_results : dict
        return type for this class
        
    ConformanceChecking
        inheriting init function
"""


class BasicMPDeclareConformanceChecking(ConformanceChecking):

    def __init__(self, consider_vacuity, log: LogAnalyzer, ltl_model: LTLModel):
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
        if self.ltl_model is None:
            raise RuntimeError("You must load the DECLARE model before checking the model.")

        self.basic_conformance_checking_results = BasicConformanceCheckingResults({})
        for i, trace in enumerate(self.log_analyzer):  # TODO: why enumerate log analyzer? it isn't even iteratable object
            trc_res = check_trace_conformance(trace, self.ltl_model, consider_vacuity)
            self.basic_conformance_checking_results[(i, trace.attributes["concept:name"])] = trc_res
        return self.basic_conformance_checking_results
