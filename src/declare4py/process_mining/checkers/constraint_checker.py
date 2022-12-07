from __future__ import annotations

from abc import ABC, abstractmethod

from src.declare4py.models.decl_model import DeclModel
from src.declare4py.models.ltl_model import LTLModel
from src.declare4py.models.pm_task import PMTask
from src.declare4py.process_mining.checkers.template_checker import TemplateCheckers
from src.declare4py.process_mining.log_analyzer import LogAnalyzer


class ConstraintCheck(PMTask, ABC):

    def __init__(self, consider_vacuity: bool, log: LogAnalyzer, ltl_model: LTLModel):
        """
        Checks whether the constraints are fulfillment, violation, pendings, activations etc

        Parameters
        ----------
        :param bool consider_vacuity: True means that vacuously satisfied traces are considered as satisfied, violated
         otherwise
        :param LogAnalyzer log: log
        :param LTLModel ltl_model: Process mining model

        """
        super().__init__(log, ltl_model)
        self.consider_vacuity: bool = consider_vacuity

    def check_trace_conformance(self, trace: dict, model: DeclModel | LTLModel = None, consider_vacuity: bool = None) -> dict:
        # Set containing all constraints that raised SyntaxError in checker functions
        rules = {"vacuous_satisfaction": consider_vacuity | self.consider_vacuity}
        model |= self.ltl_model
        error_constraint_set = set()
        trace_results = {}
        for idx, constraint in enumerate(model.constraints):
            constraint_str = model.serialized_constraints[idx]
            rules["activation"] = constraint['condition'][0]
            if constraint['template'].supports_cardinality:
                rules["n"] = constraint['n']
            if constraint['template'].is_binary:
                rules["correlation"] = constraint['condition'][1]
            rules["time"] = constraint['condition'][-1]  # time condition is always at last position
            try:
                constraint_template_cls = TemplateCheckers().get_template(constraint['template'], trace, True,
                                                                          constraint['activities'], rules)
                trace_results[constraint_str] = constraint_template_cls.get_check_result()
            except SyntaxError:
                # TODO: use logger
                if constraint_str not in error_constraint_set:
                    error_constraint_set.add(constraint_str)
                    print('Condition not properly formatted for constraint "' + constraint_str + '".')
        return trace_results
