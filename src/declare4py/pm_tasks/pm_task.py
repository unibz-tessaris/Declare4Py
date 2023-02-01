from __future__ import annotations

import typing
from abc import abstractmethod

from src.declare4py.pm_tasks.log_analyzer import d4pyEventLog
from src.declare4py.process_models.process_model import ProcessModel

"""

An abstract class for process tasking
    
"""


class PMTask:

    def __init__(self, log: d4pyEventLog | None, p_model: ProcessModel):
        super().__init__()
        if log is None:
            log = d4pyEventLog()
        self.log_analyzer: d4pyEventLog = log
        self.process_model: ProcessModel = p_model

    @abstractmethod
    def run(self, *args, **kwargs) -> typing.Any:
        pass
