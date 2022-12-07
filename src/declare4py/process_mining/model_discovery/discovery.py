from __future__ import annotations

from abc import ABC

from src.declare4py.pm_tasks.pm_task import PMTask
from src.declare4py.process_mining.log_analyzer import LogAnalyzer
from src.declare4py.process_models.process_model import ProcessModel

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


class Discovery(PMTask, ABC):

    def __init__(self, consider_vacuity: bool, log: LogAnalyzer | None, model: ProcessModel):
        self.consider_vacuity = consider_vacuity
        super().__init__(log, model)

