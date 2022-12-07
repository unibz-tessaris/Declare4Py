from __future__ import annotations

from abc import ABC

from src.declare4py.pm_tasks.pm_task import PMTask
from src.declare4py.process_mining.log_analyzer import LogAnalyzer
from src.declare4py.process_models.process_model import ProcessModel

"""
Initializes class Monitoring, inheriting from class PMTask

Parameters
-------
    PMTask
        inheriting from PMTask
"""


class Monitoring(PMTask, ABC):

    def __init__(self, log: LogAnalyzer | None, p_model: ProcessModel):
        super().__init__(log, p_model)

