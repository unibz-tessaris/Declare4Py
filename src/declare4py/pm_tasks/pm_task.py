from __future__ import annotations

from typing import Union, Any
from abc import abstractmethod

from src.declare4py.d4py_event_log import D4PyEventLog
from src.declare4py.process_models.process_model import ProcessModel

"""

An abstract class for process tasking
    
"""


class PMTask:

    def __init__(self, log: Union[D4PyEventLog], p_model: ProcessModel):
        super().__init__()
        if log is None:
            log = D4PyEventLog()
        self.log_analyzer: D4PyEventLog = log
        self.process_model: ProcessModel = p_model

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        pass
