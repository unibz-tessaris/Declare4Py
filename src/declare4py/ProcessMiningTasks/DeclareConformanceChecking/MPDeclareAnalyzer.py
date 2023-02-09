from __future__ import annotations

import pdb

from src.declare4py.D4PyEventLog import D4PyEventLog
from src.declare4py.ProcessMiningTasks.ConformanceChecking import ConformanceChecking
from src.declare4py.ProcessMiningTasks.DeclareConformanceChecking.ResultsBrowser import ResultsBrowser
from src.declare4py.ProcessModels.DeclareModel import DeclareModel
from src.declare4py.Utils.Declare.Checkers import ConstraintChecker

"""
Provides basic conformance checking functionalities
"""


class MPDeclareAnalyzer(ConformanceChecking):

    def __init__(self, consider_vacuity: bool, log: D4PyEventLog, declare_model: DeclareModel):
        super().__init__(log, declare_model)
        self.consider_vacuity = consider_vacuity
        self.basic_conformance_checking_results: ResultsBrowser = None

    def run(self) -> ResultsBrowser:
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

        log_checkers_results = []
        for trace in self.event_log.log:
            log_checkers_results.append(ConstraintChecker().check_trace_conformance(trace, self.process_model,
                                                                                    self.consider_vacuity))

        self.basic_conformance_checking_results = ResultsBrowser(log_checkers_results)
        return self.basic_conformance_checking_results
