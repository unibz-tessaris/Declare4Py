from __future__ import annotations

from abc import ABC

from src.declare4py.ProcessMiningTasks.AbstractPMTask import AbstractPMTask
from src.declare4py.D4PyEventLog import D4PyEventLog
from src.declare4py.ProcessModels.AbstractModel import ProcessModel
from typing import Union

"""
Initializes class Monitoring, inheriting from class PMTask

Parameters
-------
    PMTask
        inheriting from PMTask
"""


class Monitoring(AbstractPMTask, ABC):

    def __init__(self, log: Union[D4PyEventLog, None], p_model: ProcessModel):
        super().__init__(log, p_model)

