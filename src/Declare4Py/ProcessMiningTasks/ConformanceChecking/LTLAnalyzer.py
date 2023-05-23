from __future__ import annotations

import pdb

import numba
import numpy
import pm4py

from src.Declare4Py.D4PyEventLog import D4PyEventLog
from src.Declare4Py.ProcessMiningTasks.AbstractConformanceChecking import AbstractConformanceChecking
from pythomata.core import DFA
from src.Declare4Py.ProcessModels.LTLModel import LTLModel, LTLModelTemplate
from src.Declare4Py.Utils.utils import Utils
from logaut import ltl2dfa
from functools import reduce
import pandas
import time
from joblib import Parallel, delayed
import multiprocessing
import swifter
from numba import njit

"""
Provides basic conformance checking functionalities
"""


# AbstractConformanceChecking
class LTLAnalyzer():
    # def __init__(self, log: pandas.DataFrame, ltl_model: LTLModel):
    # super().__init__(log, ltl_model)
    def __int__(self, ltl_model: LTLModel, data_frame: pandas.DataFrame):
        self.ltl_model: LTLModel = ltl_model
        self.data_frame = data_frame


    dfa: DFA = None

    def ltl_conf_check(self, df: pandas.DataFrame) -> bool:
        current_states = {self.dfa.initial_state}
        for event in df:
            symbol = Utils.parse_activity(event)
            symbol = symbol.lower()
            temp = dict()
            temp[symbol] = True
            current_states = reduce(
                set.union,
                map(lambda x: self.dfa.get_successors(x, temp), current_states),
                set(),
            )
        # outcome = any(self.dfa.is_accepting(state) for state in current_states)
        outcome = [bool(state) if self.dfa.is_accepting(state) == True else False for state in current_states]
        return outcome[0]

    # Not working
    def parallel_conf(self, dfgroup, function):
        retLst = Parallel(n_jobs=multiprocessing.cpu_count())(delayed(function)(group) for name, group in dfgroup)
        return pandas.concat(retLst)

    def run(self) -> pandas.DataFrame:
        """
        Performs conformance checking for the provided log Dataframe and an input LTL model.
        The Dataframe contains a 'conformance' column, which is boolean.
        The returned Dataframe is also sorted by trace id.

        Returns:
            A sorted, by trace id, Pandas Dataframe and also contains an additional column 'conformance'.
        """

        if self.data_frame is None:
            raise RuntimeError("You must load the log before checking the model.")
        if self.ltl_model is None:
            raise RuntimeError("You must load the LTL model before checking the model.")
        dfa = ltl2dfa(self.ltl_model.parsed_formula, backend="lydia")
        self.dfa = dfa.minimize()
        group = self.data_frame.groupby('case:concept:name', group_keys=True)

        result = group['concept:name'].apply(self.ltl_conf_check)

        result = result.to_frame()
        print(result)
        # result = group['concept:name'].transform(self.ltl_conf_check, engine='numba', engine_kwargs = {'nopython': True, 'nogil': False, 'parallel': True})


        # Not working
        # self.data_frame['conformance'] = self.parallel_conf(group, self.ltl_conf_check)
        # print(result_df)
        # for i in range(len(result_df)):
        #    print(result_df.loc[i, 'case:concept:name'], result_df.loc[i, 'conformance'])
        return result


#df = pm4py.read_xes("/home/xhedj/Desktop/test_logs/InternationalDeclarations.xes")
#template = LTLModelTemplate("eventually_a_next_b_next_c")
#model = template.get_templ_model(["Start trip", "End Trip", "Permit SUBMITTED by EMPLOYEE"])
#analyzer = LTLAnalyzer()
#analyzer.ltl_model = model
#analyzer.data_frame = df
#s = time.time()
#res = analyzer.run()
#e = time.time()
#print(f"Elapsed time: {e - s}")
