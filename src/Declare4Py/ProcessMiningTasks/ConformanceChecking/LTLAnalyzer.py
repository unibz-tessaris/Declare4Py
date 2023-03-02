from __future__ import annotations

from typing import Any
from src.Declare4Py.D4PyEventLog import D4PyEventLog
from src.Declare4Py.ProcessMiningTasks.AbstractConformanceChecking import AbstractConformanceChecking
from src.Declare4Py.ProcessModels.LTLModel import LTLModel
from logaut import ltl2dfa

import pm4py.algo.filtering.log.ltl

"""
Provides basic conformance checking functionalities
"""


class LTLAnalyzer(AbstractConformanceChecking):

    def __init__(self, log: D4PyEventLog, ltl_model: LTLModel):
        super().__init__(log, ltl_model)

    def run(self) -> Any:
        """
        Performs conformance checking for the provided event log and an input LTL model.

        Parameters
        ----------

        Returns
        -------
        """

        if self.event_log is None:
            raise RuntimeError("You must load the log before checking the model.")
        if self.process_model is None:
            raise RuntimeError("You must load the LTL model before checking the model.")
        dfa = ltl2dfa(self.process_model.parsed_formula, backend="lydia")
        dfa = dfa.minimize()
        # fare il for del event log
        pass





