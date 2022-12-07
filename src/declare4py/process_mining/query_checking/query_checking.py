from __future__ import annotations

from abc import abstractmethod, ABC

from src.declare4py.models.ltl_model import LTLModel
from src.declare4py.models.pm_task import PMTask
from src.declare4py.process_mining.checkers.constraint_checker import ConstraintCheck
from src.declare4py.process_mining.log_analyzer import LogAnalyzer

"""
Initializes class QueryChecking, inheriting from class PMTask


Attributes
-------
    consider_vacuity : bool
        True means that vacuously satisfied traces are considered as satisfied, violated otherwise.

    template_str : str, optional
        if specified, the query checking is restricted on this DECLARE template. If not, the query checking is
        performed over the whole set of supported templates.

    max_declare_cardinality : int, optional
        the maximum cardinality that the algorithm checks for DECLARE templates supporting it (default 1).

    activation : str, optional
        if specified, the query checking is restricted on this activation activity. If not, the query checking
        considers in turn each activity of the log as activation.

    target : str, optional
        if specified, the query checking is restricted on this target activity. If not, the query checking
        considers in turn each activity of the log as target.

    act_cond : str, optional
        activation condition to evaluate. It has to be written by following the DECLARE standard format.

    trg_cond : str, optional
        target condition to evaluate. It has to be written by following the DECLARE standard format.

    time_cond : str, optional
        time condition to evaluate. It has to be written by following the DECLARE standard format.

    min_support : float, optional
        the minimum support that a constraint needs to have to be included in the result (default 1).
"""


class QueryChecking(ConstraintCheck, ABC):

    def __init__(self, template_str: str, activation: str, target: str,
                 act_cond: str, trg_cond: str, time_cond: str, min_support: float,
                 max_declare_cardinality: int, consider_vacuity: bool,
                 log: LogAnalyzer, ltl_model: LTLModel):
        self.template_str: str | None = template_str
        self.activation: str | None = activation
        self.target: str | None = target
        self.act_cond: str | None = act_cond
        self.trg_cond: str | None = trg_cond
        self.time_cond: str | None = time_cond
        self.min_support: float = min_support  # or 1.0
        self.max_declare_cardinality: int = max_declare_cardinality
        super().__init__(consider_vacuity, log, ltl_model)

