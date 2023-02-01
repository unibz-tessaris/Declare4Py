from __future__ import annotations

from abc import ABC

from src.declare4py.pm_tasks.log_analyzer import d4pyEventLog
from src.declare4py.pm_tasks.discovery import Discovery
from src.declare4py.process_models.decl_model import DeclModel, DeclareModelTemplate, TraceState
from src.declare4py.process_models.ltl_model import LTLModel
from src.declare4py.utility.template_checkers.checker_result import CheckerResult
from src.declare4py.utility.template_checkers.constraint_checker import ConstraintCheck

"""

Dictionary type object to save some value

"""


class BasicDiscoveryResults(dict):

    def __init__(self, **kwargs):
        super().__init__(kwargs)


"""
Provides basic discovery functionalities

Parameters
--------
    Discovery
        inherit class init

Attributes
--------
    super()
        inheriting from class Discovery
    output_path : str
        if specified, save the discovered constraints in a DECLARE model to the provided path.

"""


class BasicMPDeclareDiscovery(Discovery, ABC):

    def __init__(self, consider_vacuity: bool, support: float, max_declare_cardinality: int,
                 log: d4pyEventLog | None, ltl_model: LTLModel):
        super().__init__(consider_vacuity, support, max_declare_cardinality, log, ltl_model)
        self.init_discovery_result_instance()
        self.constraint_checker = ConstraintCheck(consider_vacuity)
        self.support: float = support
        self.max_declare_cardinality: int | None = max_declare_cardinality
        self.basic_discovery_results: BasicDiscoveryResults | None = None

    def init_discovery_result_instance(self):
        self.basic_discovery_results: BasicDiscoveryResults = BasicDiscoveryResults()

    def run(self, consider_vacuity: bool, max_declare_cardinality: int = 3, output_path: str = None) \
            -> BasicDiscoveryResults:
        """
        Performs discovery of the supported DECLARE templates for the provided log by using the computed frequent item
        sets.

        Parameters
        ----------
        consider_vacuity : bool
            True means that vacuously satisfied traces are considered as satisfied, violated otherwise.

        max_declare_cardinality : int, optional
            the maximum cardinality that the algorithm checks for DECLARE templates supporting it (default 3).

        output_path : str, optional
            if specified, save the discovered constraints in a DECLARE model to the provided path.

        Returns
        -------
        basic_discovery_results
            dictionary containing the results indexed by discovered constraints. The value is a dictionary with keys
            the tuples containing id and name of traces that satisfy the constraint. The values of this inner dictionary
            is a CheckerResult object containing the number of pendings, activations, violations, fulfilments.
        """
        print("Computing discovery ...")
        if self.log_analyzer is None:
            raise RuntimeError("You must load a log before.")
        if self.log_analyzer.frequent_item_sets is None:
            raise RuntimeError("You must discover frequent itemsets before.")
        if max_declare_cardinality <= 0:
            raise RuntimeError("Cardinality must be greater than 0.")
        self.init_discovery_result_instance()

        for item_set in self.log_analyzer.frequent_item_sets['itemsets']:  # TODO: improve this key name?
            length = len(item_set)
            if length == 1:
                for templ in DeclareModelTemplate.get_unary_templates():
                    constraint = {"template": templ, "activities": ', '.join(item_set), "condition": ("", "")}
                    if not templ.supports_cardinality:
                        self.basic_discovery_results |= self.discover_constraint(self.log_analyzer, constraint,
                                                                                 consider_vacuity)
                    else:
                        for i in range(max_declare_cardinality):
                            constraint['n'] = i + 1
                            self.basic_discovery_results |= self.discover_constraint(self.log_analyzer, constraint,
                                                                                     consider_vacuity)
            elif length == 2:
                for templ in DeclareModelTemplate.get_binary_templates():
                    constraint = {"template": templ, "activities": ', '.join(item_set), "condition": ("", "", "")}
                    self.basic_discovery_results |= self.discover_constraint(self.log_analyzer, constraint,
                                                                             consider_vacuity)
                    constraint['activities'] = ', '.join(reversed(list(item_set)))
                    self.basic_discovery_results |= self.discover_constraint(self.log_analyzer, constraint,
                                                                             consider_vacuity)
        activities_decl_format = "activity " + "\nactivity ".join(self.log_analyzer.get_log_alphabet_activities()) + "\n"
        if output_path is not None:
            with open(output_path, 'w+') as f:
                f.write(activities_decl_format)
                f.write('\n'.join(self.basic_discovery_results.keys()))
        return self.basic_discovery_results

    def filter_discovery(self, min_support: float = 0, output_path: str = None) \
            -> dict[str: dict[tuple[int, str]: CheckerResult]]:
        """
        Filters discovery results by means of minimum support.

        Parameters
        ----------
        min_support : float, optional
            the minimum support that a discovered constraint needs to have to be included in the filtered result.

        output_path : str, optional
            if specified, save the filtered constraints in a DECLARE model to the provided path.

        Returns
        -------
        result
            dictionary containing the results indexed by discovered constraints. The value is a dictionary with keys
            the tuples containing id and name of traces that satisfy the constraint. The values of this inner dictionary
            is a CheckerResult object containing the number of pendings, activations, violations, fulfilments.
        """
        if self.log_analyzer is None:
            raise RuntimeError("You must load a log before.")
        if self.basic_discovery_results is None:
            raise RuntimeError("You must run a Discovery task before.")
        if not 0 <= min_support <= 1:
            raise RuntimeError("Min. support must be in range [0, 1].")
        result = {}

        for key, val in self.basic_discovery_results.items():
            support = len(val) / len(self.log_analyzer.log)
            if support >= min_support:
                result[key] = support

        if output_path is not None:
            with open(output_path, 'w') as f:
                f.write("activity " + "\nactivity ".join(self.log_analyzer.get_log_alphabet_activities()) + "\n")
                f.write('\n'.join(result.keys()))
        return result

    def discover_constraint(self, log: d4pyEventLog, constraint: dict, consider_vacuity: bool):
        # Fake model composed by a single constraint
        model = DeclModel()
        model.constraints.append(constraint)
        discovery_res: BasicDiscoveryResults = {}
        for i, trace in enumerate(log.log):
            trc_res = self.constraint_checker.check_trace_conformance(trace, model, consider_vacuity)
            if not trc_res:  # Occurring when constraint data conditions are formatted bad
                break
            constraint_str, checker_res = next(iter(trc_res.items()))  # trc_res will always have only one element
            # inside
            if checker_res.state == TraceState.SATISFIED:
                new_val = {(i, trace.attributes['concept:name']): checker_res}
                if constraint_str in discovery_res:
                    discovery_res[constraint_str] |= new_val
                else:
                    discovery_res[constraint_str] = new_val
        return discovery_res

