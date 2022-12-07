from __future__ import annotations

from src.declare4py.process_mining.log_analyzer import LogAnalyzer
from src.declare4py.process_models.decl_model import DeclModel
from src.declare4py.process_models.ltl_model import LTLModel
from src.declare4py.process_models.process_model import ProcessModel
from src.declare4py.utility.template_checkers.template_checker import TemplateCheckers


class ConstraintCheck:

    def __init__(self, consider_vacuity: bool | None):
        """
        Checks whether the constraints are fulfillment, violation, pendings, activations etc

        Parameters
        ----------
        :param bool consider_vacuity: True means that vacuously satisfied traces are considered as satisfied, violated
         otherwise
        :param LogAnalyzer log: log
        :param LTLModel ltl_model: Process mining model

        """
        self.consider_vacuity: bool = consider_vacuity | False

    def check_trace_conformance(self, trace: dict, p_model: ProcessModel, consider_vacuity: bool = None) -> dict:
        # Set containing all constraints that raised SyntaxError in checker functions
        rules = {"vacuous_satisfaction": consider_vacuity | self.consider_vacuity}
        error_constraint_set = set()
        model: DeclModel = p_model
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
                # TODO: use python logger
                if constraint_str not in error_constraint_set:
                    error_constraint_set.add(constraint_str)
                    print('Condition not properly formatted for constraint "' + constraint_str + '".')
        return trace_results
