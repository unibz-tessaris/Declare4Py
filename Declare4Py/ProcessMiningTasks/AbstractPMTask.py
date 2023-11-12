from __future__ import annotations

import typing
from typing import Any
from abc import abstractmethod

from Declare4Py.D4PyEventLog import D4PyEventLog
from Declare4Py.ProcessModels.AbstractModel import ProcessModel


class AbstractPMTask:
    """
    An abstract class for representing process mining tasks

    ...

    Attributes
    ----------
    event_log : D4PyEventLog
        the event log
    process_model : ProcessModel
        the process model
    """

    def __init__(self, log: typing.Union[D4PyEventLog, None], process_model: ProcessModel):
        self.event_log: typing.Union[D4PyEventLog, None] = log
        self.process_model: ProcessModel = process_model

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        pass

    def get_event_log(self):
        return self.event_log

    def get_process_model(self):
        return self.process_model
