from __future__ import annotations

from src.Declare4Py.D4PyEventLog import D4PyEventLog
from src.Declare4Py.ProcessMiningTasks.AbstractConformanceChecking import AbstractConformanceChecking
from src.Declare4Py.ProcessModels.LTLModel import LTLModel, LTLModelTemplate
from src.Declare4Py.Utils.utils import Utils
from logaut import ltl2dfa
from functools import reduce
import pandas

"""
Provides basic conformance checking functionalities
"""


class LTLAnalyzer(AbstractConformanceChecking):

    def __init__(self, log: D4PyEventLog, ltl_model: LTLModel):
        super().__init__(log, ltl_model)


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
        parameters = self.process_model.parameters

        df = pandas.DataFrame()

        temp_id: int = 0
        for trace in g_log:
            current_states = {dfa.initial_state}
            for event in trace:
                symbol = event[self.event_log.activity_key]
                symbol = Utils.parse_activity(symbol)
                symbol = symbol.lower()
                temp = dict()
                if symbol in parameters:
                    temp[symbol] = True
                else:
                    temp[symbol] = False
                current_states = reduce(
                    set.union,
                    map(lambda x: dfa.get_successors(x, temp), current_states),
                    set(),
                )
            result = any(dfa.is_accepting(state) for state in current_states)
            to_append = pandas.DataFrame([{'case id': temp_id, 'accepting': result}])
            df = pandas.concat([df, to_append])
            temp_id += 1

        return df


