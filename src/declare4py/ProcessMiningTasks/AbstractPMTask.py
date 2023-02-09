from __future__ import annotations

from typing import Union, Any
from abc import abstractmethod

from src.declare4py.D4PyEventLog import D4PyEventLog
from src.declare4py.ProcessModels.AbstractModel import ProcessModel

"""

An abstract class for process tasking
    
"""


class AbstractPMTask:

    def __init__(self, log: Union[D4PyEventLog], process_model: ProcessModel):
        super().__init__()
        if log is None:
            log = D4PyEventLog()
        self.event_log: D4PyEventLog = log
        self.process_model: ProcessModel = process_model

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        pass
