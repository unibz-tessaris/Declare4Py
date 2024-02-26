from __future__ import annotations

import collections
import logging
import typing
from abc import ABC

from Declare4Py.ProcessMiningTasks.AbstractPMTask import AbstractPMTask
from Declare4Py.ProcessModels.AbstractModel import ProcessModel
from Declare4Py.ProcessMiningTasks.LogGenerator.ASP.ASPUtils.Distribution import Distribution

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
                 p_model: ProcessModel,
                 distributor_type: str = "uniform"
                 ):

        super().__init__(None, p_model)

        """INIT Conditions"""
        if not isinstance(min_event, int):
            raise ValueError(f"min_events is not of type int!")
        if not isinstance(max_event, int):
            raise ValueError(f"max_event is not of type int!")
        if not isinstance(num_traces, int):
            raise ValueError(f"num_traces is not of type int!")

        if min_event > max_event:
            raise ValueError(f"min_events({min_event}) > max_events({max_event})! "
                             f"Min events should not be greater than max events")
        if min_event < 0 and max_event < 0:
            raise ValueError(f"min and max events should be greater than 0!")
        if min_event < 0:
            raise ValueError(f"min_events({min_event}) should be greater than 0!")
        if max_event < 0:
            raise ValueError(f"max_events({max_event}) should be greater than 0!")
        if num_traces < 0:
            raise ValueError(f"num_traces({num_traces}) should be greater or equal than 0!")

        """DEF"""
        self.__py_logger = logging.getLogger("Log generator")
        self.log_length: int = num_traces
        self.max_events: int = max_event
        self.min_events: int = min_event

        # Distributions Setting
        self.traces_length: typing.Union[collections.Counter, typing.Dict] = {}
        self.__available_distributions: typing.List[str] = Distribution.get_distributions()
        self.__distributor_type: str = None
        self.set_distributor_type(distributor_type)
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

    def set_distributor_type(self, distributor_type: str):
        if distributor_type not in self.__available_distributions:
            raise ValueError(f"Invalid distributor_type:{distributor_type}. Valid options are 'uniform', 'gaussian', 'custom'")
        self.__distributor_type = distributor_type

    def add_constraints_to_violate(self, constrains_to_violate: typing.Union[str, list[str]] = True):
        if isinstance(constrains_to_violate, str):
            self.violable_constraints.append(constrains_to_violate)
        else:
            self.violable_constraints = constrains_to_violate
        return self
