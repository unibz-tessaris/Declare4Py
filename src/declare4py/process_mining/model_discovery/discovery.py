from __future__ import annotations

from abc import ABC

from src.declare4py.models.ltl_model import LTLModel
from src.declare4py.process_mining.checkers.constraint_checker import ConstraintCheck
from src.declare4py.process_mining.log_analyzer import LogAnalyzer
from src.declare4py.process_mining.model_discovery.basic_mp_declare_discovery import BasicDiscoveryResults

"""
Initializes class Discovery, inheriting from class PMTask

Parameters
-------
    PMTask
        inheriting from PMTask
Attributes
-------
    consider_vacuity : bool
        True means that vacuously satisfied traces are considered as satisfied, violated otherwise.
        
    support : float
        the support that a discovered constraint needs to have to be included in the filtered result.

    max_declare_cardinality : int, optional
        the maximum cardinality that the algorithm checks for DECLARE templates supporting it (default 3).
"""


class Discovery(ConstraintCheck, ABC):

    def __init__(self, consider_vacuity: bool, support: float, max_declare_cardinality: int,
                 log: LogAnalyzer | None, ltl_model: LTLModel):
        super().__init__(consider_vacuity, log, ltl_model)
        self.support: float = support
        self.max_declare_cardinality: int | None = max_declare_cardinality
        self.basic_discovery_results: BasicDiscoveryResults | None = None
        self.init_discovery_result_instance()

    def init_discovery_result_instance(self):
        self.basic_discovery_results: BasicDiscoveryResults = BasicDiscoveryResults()

