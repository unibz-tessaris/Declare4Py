
from __future__ import annotations

from abc import ABC

from src.declare4py.models.pm_task import PMTask
from src.declare4py.models.ltl_model import LTLModel

"""
Initializes class LogGenerator, inheriting from class PMTask

Parameters
-------
log_length
    object of type int
PMTask
    inheriting from PMTask
"""


class LogGenerator(PMTask, ABC):

    def __init__(self, num_traces: int, min_event: int, max_event: int, ltl_model: LTLModel):
        super().__init__(None, ltl_model)
        self.log_length: int = num_traces
        self.max_events: int = max_event
        self.min_events: int = min_event
