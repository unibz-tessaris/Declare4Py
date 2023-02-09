from __future__ import annotations

from src.declare4py.utility.Declare.checker_result import CheckerResult

"""
Initializes class ConformanceCheckingResults

Attributes
-------
    dict_results : dict
        dictionary of conformance checking results
"""


class BasicConformanceCheckingResults(dict):

    def __init__(self, dict_results: dict, **kwargs):
        super().__init__(kwargs)
        self.basic_conformance_checking_results: dict = dict_results
        self.model_check_res: [CheckerResult] = []

    def activations(self, trace_id: int, constr_id: int) -> int:
        if trace_id is None and constr_id is None:
            print("ERROR: at least one parameter is expected.")
        elif trace_id is None:
            return self.model_check_res[constr_id].num_activations
        elif constr_id is None:
            return self.model_check_res[trace_id].num_activations
        else:
            return self.model_check_res[trace_id][constr_id].num_activations

    def violations(self, trace_id: int, constr_id: int) -> int:
        if trace_id is None and constr_id is None:
            print("ERROR: at least one parameter is expected.")
        elif trace_id is None:
            return self.model_check_res[constr_id].num_violations
        elif constr_id is None:
            return self.model_check_res[trace_id].num_violations
        else:
            return self.model_check_res[trace_id][constr_id].num_violations

    def fulfillments(self, trace_id: int, constr_id: int) -> int:
        if trace_id is None and constr_id is None:
            print("ERROR: at least one parameter is expected.")
        elif trace_id is None:
            return self.model_check_res[constr_id].num_fulfillments
        elif constr_id is None:
            return self.model_check_res[trace_id].num_fulfillments
        else:
            return self.model_check_res[trace_id][constr_id].num_fulfillments

    def state(self, trace_id: int, constr_id: int) -> bool:
        if trace_id is None and constr_id is None:
            print("ERROR: at least one parameter is expected.")
        elif trace_id is None:
            return self.model_check_res[constr_id].state
        elif constr_id is None:
            return self.model_check_res[trace_id].state
        else:
            return self.model_check_res[trace_id][constr_id].state

    def clean(self):
        return self.basic_conformance_checking_results
