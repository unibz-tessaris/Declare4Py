from __future__ import annotations

from abc import ABC

from Declare4Py.ProcessMiningTasks.AbstractPMTask import AbstractPMTask
from Declare4Py.D4PyEventLog import D4PyEventLog
from Declare4Py.ProcessModels.AbstractModel import ProcessModel

import logging
import typing
import collections

from Declare4Py.ProcessMiningTasks.LogGenerator.ASP.ASPUtils.Distribution import Distribution

"""

An abstract class for verifying whether the behavior of a given process model, as recorded in a log,
 is in line with some expected behaviors provided in the form of a process model ()

Parameters
-------
    consider_vacuity : bool
        True means that vacuously satisfied traces are considered as satisfied, violated otherwise.

"""


class AbstractLogGenerator(AbstractPMTask, ABC):

    def __init__(
            self,
            log: D4PyEventLog,
            num_traces: int,
            min_event: int,
            max_event: int,
            process_model: ProcessModel
    ):

        super().__init__(log, process_model)

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
        self.possible_distributions = Distribution.get_distributions()
        self.distributor_type: str = "uniform"
        self.custom_probabilities: None = None
        self.scale: typing.Union[float, None] = None
        self.loc: typing.Union[float, None] = None

    def set_distribution(self, distributor_type: str = "uniform",
                         custom_probabilities: typing.Optional[typing.List[float]] = None,
                         loc: float = None, scale: float = None):
        """
        We specify rules regarding the length of a trace that spans between a minimum and a maximum.
         This span is set according to a uniform, gaussian or custom distribution.

        Parameters
        ----------
        distributor_type: str
            "uniform", "gaussian", "custom"
        custom_probabilities: list, optional
            it must be used when custom distribution is chosen
        loc: float
            used for gaussian/normal distribution
        scale: float
            used for gaussian/normal distribution

        Returns
        -------

        """
        if distributor_type.lower() not in self.possible_distributions:
            raise ValueError(f"Invalid distribution {distributor_type}")

        self.distributor_type = distributor_type.lower()
        self.custom_probabilities = custom_probabilities
        self.scale = scale
        self.loc = loc

    def compute_distribution(self, total_traces: typing.Union[int, None] = None) -> collections.Counter:
        """
         The compute_distribution method computes the distribution of the number of events in a trace based on
         the distributor_type parameter. If the distributor_type is "gaussian", it uses the loc and scale parameters
         to compute a Gaussian distribution. Otherwise, it uses a uniform or custom distribution.

         Parameters
         total_traces: int, optional
            the number of traces
        """
        self.__py_logger.info("Computing distribution")

        """INIT Conditions"""
        if total_traces is None:
            total_traces = self.log_length
        if total_traces == 0:
            return collections.Counter()

        """DEF"""
        traces_len: collections.Counter = collections.Counter()

        if self.distributor_type == "gaussian":
            print()
        else:
            print()

        self.__py_logger.info(f"Distribution result {traces_len}")
        self.traces_length = traces_len
        return traces_len
