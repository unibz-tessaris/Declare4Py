
from __future__ import annotations

from abc import ABC

from src.declare4py.pm_tasks.pm_task import PMTask
from src.declare4py.process_models.process_model import ProcessModel

# from src.declare4py.process_models.ltl_model import LTLModel

"""

An abstract class for log generators.


Parameters
-------
log_length object of type int
PMTask inheriting from PMTask
"""


class LogGenerator(PMTask, ABC):

    def __init__(self, num_traces: int, min_event: int, max_event: int, p_model: ProcessModel):
        super().__init__(None, p_model)
        self.log_length: int = num_traces
        self.max_events: int = max_event
        self.min_events: int = min_event
