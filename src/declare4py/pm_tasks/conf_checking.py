from __future__ import annotations

from abc import ABC

from src.declare4py.pm_tasks.pm_task import PMTask
from src.declare4py.pm_tasks.log_analyzer import LogAnalyzer
from src.declare4py.process_models.process_model import ProcessModel

"""

An abstract class for verifying whether the behavior of a given process model, as recorded in a log,
 is in line with some expected behaviors provided in the form of a process model ()

Parameters
-------
    consider_vacuity : bool
        True means that vacuously satisfied traces are considered as satisfied, violated otherwise.

"""


class ConformanceChecking(PMTask, ABC):

    def __init__(self, consider_vacuity: bool, log: LogAnalyzer, process_model: ProcessModel):
        self.consider_vacuity = consider_vacuity
        super().__init__(log, process_model)

