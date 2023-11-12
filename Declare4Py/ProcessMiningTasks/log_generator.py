from __future__ import annotations

import collections
import logging
import typing
from abc import ABC

from Declare4Py.ProcessMiningTasks.AbstractPMTask import AbstractPMTask
from Declare4Py.ProcessModels.AbstractModel import ProcessModel


"""

An abstract class for log generators.


Parameters
-------
log_length object of type int
PMTask inheriting from PMTask
"""


class LogGenerator(AbstractPMTask, ABC):

    def __init__(self,
                 num_traces: int,
                 min_event: int,
                 max_event: int,
                 p_model: ProcessModel
                 ):

        super().__init__(None, p_model)

        """INIT Conditions"""
        if min_event > max_event:
            raise ValueError(f"min_events({min_event}) > max_events({max_event})! "
                             f"Min events should no be greater than max events")
        if min_event < 0 and max_event < 0:
            raise ValueError(f"min and max events should be greater than 0!")
        if min_event < 0:
            raise ValueError(f"min_events({min_event}) should be greater than 0!")
        if max_event < 0:
            raise ValueError(f"max_events({max_event}) should be greater than 0!")
        if not isinstance(min_event, int) or not isinstance(max_event, int):
            raise ValueError(f"min_events or/and max_events are not valid!")

        """DEF"""
        self.__py_logger = logging.getLogger("Log generator")
        self.log_length: int = num_traces
        self.max_events: int = max_event
        self.min_events: int = min_event

        # Distributions Setting
        self.traces_length: typing.Union[collections.Counter, typing.Dict] = {}
        self.distributor_type: typing.Literal["uniform", "gaussian", "custom"] = "uniform"
        self.custom_probabilities: None = None
        self.scale: typing.Union[float, None] = None
        self.loc: typing.Union[float, None] = None

        # Constraint violations
        """
        A trace is positive if it satisfies all three constraints that are defined in this model. Whereas it is
        negative if at least one of them is not satisfied. In the generated log you sent me, in all traces the 
        constraint " Response[Driving_Test, Resit] |A.Grade<=2 | " is not satisfied, i.e. it is violated!
        """
        self.violate_all_constraints: bool = False  # if false: clingo will decide itself the constraints to violate
        self.violable_constraints: [str] = []  # constraint list which should be violated
        self.negative_traces = 0

        # constraint template conditions
        self.activation_conditions: dict = None

    def add_constraints_to_violate(self, constrains_to_violate: typing.Union[str, list[str]] = True):
        if isinstance(constrains_to_violate, str):
            self.violable_constraints.append(constrains_to_violate)
        else:
            self.violable_constraints = constrains_to_violate
        return self

