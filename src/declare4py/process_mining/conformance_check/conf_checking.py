from __future__ import annotations

from abc import ABC

from src.declare4py.models.ltl_model import LTLModel
from src.declare4py.models.pm_task import PMTask
from src.declare4py.process_mining.log_analyzer import LogAnalyzer

"""
Initializes class ConformanceChecking, inheriting from class PMTask
checkers.
Parameters
-------
    PMTask
        inheriting from PMTask
Attributes
----------
    consider_vacuity : bool
        True means that vacuously satisfied traces are considered as satisfied, violated otherwise.
        
"""


class ConformanceChecking(PMTask, ABC):

    def __init__(self, consider_vacuity: bool, log: LogAnalyzer, ltl_model: LTLModel):
        self.consider_vacuity: bool = consider_vacuity
        super().__init__(log, ltl_model)
