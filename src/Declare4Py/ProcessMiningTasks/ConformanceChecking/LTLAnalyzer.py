from __future__ import annotations

import multiprocessing
import pdb

from src.Declare4Py.D4PyEventLog import D4PyEventLog
from src.Declare4Py.ProcessMiningTasks.AbstractConformanceChecking import AbstractConformanceChecking
from src.Declare4Py.ProcessModels.LTLModel import LTLModel, LTLModelTemplate
from src.Declare4Py.Utils.utils import Utils
from logaut import ltl2dfa
from functools import reduce
import pandas
from numba import jit

"""
Provides basic conformance checking functionalities
"""


class LTLAnalyzer(AbstractConformanceChecking):

    def __init__(self, log: D4PyEventLog, ltl_model: LTLModel):
        super().__init__(log, ltl_model)

    def run_single_trace(self, trace, dfa):
        current_states = {dfa.initial_state}
        for event in trace:
            symbol = event[self.event_log.activity_key]
            symbol = Utils.parse_activity(symbol)
            symbol = symbol.lower()
            temp = dict()
            temp[symbol] = True
            current_states = reduce(
                set.union,
                map(lambda x: dfa.get_successors(x, temp), current_states),
                set(),
            )
        is_accepted = any(dfa.is_accepting(state) for state in current_states)
        return is_accepted


# Add parameters?
    def run(self) -> pandas.DataFrame:
        """
        Performs conformance checking for the provided event log and an input LTL model.

        Returns:
            A pandas Dataframe containing the id of the traces and the result of the conformance check
        """

        if self.event_log is None:
            raise RuntimeError("You must load the log before checking the model.")
        if self.process_model is None:
            raise RuntimeError("You must load the LTL model before checking the model.")
        dfa = ltl2dfa(self.process_model.parsed_formula, backend="lydia")
        dfa = dfa.minimize()
        g_log = self.event_log.get_log()
        #parameters = self.process_model.parameters

        results = []
        """
        for trace in g_log:
            is_accepted = self.run_single_trace(trace, dfa)
            results.append([trace.attributes['concept:name'], is_accepted])
        """
        jobs=4
        #with multiprocessing.get_context("spawn").Pool(processes=jobs) as pool:
        #    tmp_list_results = pool.map(self.run_single_trace, g_log)

        pool = multiprocessing.Pool(processes=jobs)
        tmp_list_results = pool.map(self.run_single_trace, g_log)
        pool.close()
        return "ciao"
        #return pandas.DataFrame(results, columns=[self.event_log.case_id_key, "accepted"])
