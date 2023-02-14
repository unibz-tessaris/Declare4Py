from __future__ import annotations

from abc import ABC
from typing import Union

from src.declare4py.ProcessMiningTasks.AbstractPMTask import AbstractPMTask
from src.declare4py.D4PyEventLog import D4PyEventLog
from src.declare4py.ProcessModels.AbstractModel import ProcessModel

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


class AbstractDiscovery(AbstractPMTask, ABC):

    def __init__(self, consider_vacuity: bool, log: Union[D4PyEventLog, None], model: ProcessModel):
        self.consider_vacuity = consider_vacuity
        super().__init__(log, model)

