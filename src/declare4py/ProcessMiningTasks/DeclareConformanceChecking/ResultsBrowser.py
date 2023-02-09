from __future__ import annotations

import pdb
from typing import List, Union

from src.declare4py.Utils.Declare.Checkers import CheckerResult

"""
Initializes class ConformanceCheckingResults

Attributes
-------
    dict_results : dict
        dictionary of conformance checking results
"""


class ResultsBrowser:

    def __init__(self, matrix_results: List[List[CheckerResult]]):
        self.model_check_res: List[List[CheckerResult]] = matrix_results

    def get_metric(self, metric: str, trace_id: int = None, constr_id: int = None) -> Union[List, int]:
        if metric is None:
            raise RuntimeError("You must specify a metric among num_activations, num_violations, num_fulfillments, "
                               "num_pendings, state.")
        results = None
        if trace_id is None and constr_id is None:
            results = []
            for trace_res in self.model_check_res:
                tmp_list = []
                for result_checker in trace_res:
                    try:
                        tmp_list.append(getattr(result_checker, metric))
                    except AttributeError:
                        print("You must specify a metric among num_activations, num_violations, num_fulfillments, "
                               "num_pendings, state.")
                results.append(tmp_list)
        if trace_id is not None:
            pass
        return results

    def get_activations(self, trace_id: int, constr_id: int) -> int:
        if trace_id is None and constr_id is None:
            print("ERROR: at least one parameter is expected.")
        elif trace_id is None:
            return self.model_check_res[constr_id].num_activations
        elif constr_id is None:
            return self.model_check_res[trace_id].num_activations
        else:
            return self.model_check_res[trace_id][constr_id].num_activations

    def get_violations(self, trace_id: int, constr_id: int) -> int:
        if trace_id is None and constr_id is None:
            print("ERROR: at least one parameter is expected.")
        elif trace_id is None:
            return self.model_check_res[constr_id].num_violations
        elif constr_id is None:
            return self.model_check_res[trace_id].num_violations
        else:
            return self.model_check_res[trace_id][constr_id].num_violations

    def get_fulfillments(self, trace_id: int, constr_id: int) -> int:
        if trace_id is None and constr_id is None:
            print("ERROR: at least one parameter is expected.")
        elif trace_id is None:
            return self.model_check_res[constr_id].num_fulfillments
        elif constr_id is None:
            return self.model_check_res[trace_id].num_fulfillments
        else:
            return self.model_check_res[trace_id][constr_id].num_fulfillments

    def get_states(self, trace_id: int, constr_id: int) -> bool:
        if trace_id is None and constr_id is None:
            print("ERROR: at least one parameter is expected.")
        elif trace_id is None:
            return self.model_check_res[constr_id].state
        elif constr_id is None:
            return self.model_check_res[trace_id].state
        else:
            return self.model_check_res[trace_id][constr_id].state
