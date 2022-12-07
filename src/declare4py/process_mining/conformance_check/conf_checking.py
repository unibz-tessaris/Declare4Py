from __future__ import annotations

from abc import ABC

from src.declare4py.models.ltl_model import LTLModel
from src.declare4py.process_mining.checkers.constraint_checker import ConstraintCheck
from src.declare4py.process_mining.log_analyzer import LogAnalyzer

"""

An abstract class for verifying whether the behavior of a given process model, as recorded in a log,
 is in line with some expected behaviors provided in the form of a process model ()

Parameters
-------
    consider_vacuity : bool
        True means that vacuously satisfied traces are considered as satisfied, violated otherwise.
        
"""


class ConformanceChecking(ConstraintCheck, ABC):

    def __init__(self, consider_vacuity: bool, log: LogAnalyzer, ltl_model: LTLModel):
        super().__init__(consider_vacuity, log, ltl_model)

