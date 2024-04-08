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
"""


class AbstractLogGenerator(AbstractPMTask, ABC):

    def __init__(
            self,
            total_traces: int,
            min_event: int,
            max_event: int,
            process_model: ProcessModel,
            log: typing.Union[D4PyEventLog, None] = None,
            verbose: bool = False
    ):

        super().__init__(log, process_model)

        """Initialize Abstract Log Generator"""
        self.__py_logger = logging.getLogger("Abstract Log Generator")

        self.total_traces: int = 0
        self.max_events: int = 0
        self.min_events: int = 0
        self.verbose: bool = False

        """Check Init Conditions"""
        self.set_total_traces(total_traces)
        self.set_min_max_events(min_event, max_event)

        """Initialize Distributions Setting"""
        self.distribution: Distribution = Distribution(min_event, max_event, total_traces, Distribution.UNIFORM, None, verbose)
        self.total_traces_distribution: typing.Union[collections.Counter, typing.Dict] = self.distribution.get_distribution()
        self.distribution_type: str = Distribution.UNIFORM
        self.custom_probabilities: None = None
        self.mu: typing.Union[float, None] = None
        self.sigma: typing.Union[float, None] = None

    def compute_distribution(
            self,
            min_num_events_or_mu: typing.Union[int, float, None] = None,
            max_num_events_or_sigma: typing.Union[int, float, None] = None,
            total_traces: typing.Union[int, None] = None,
            dist_type: str = Distribution.UNIFORM,
            custom_probabilities: typing.Optional[typing.List[float]] = None
    ) -> collections.Counter:

        """
        Computes the distribution of the given process model.
        It changes the distribution of the Log Generator if new parameters or values are inserted
        If some values are None the current will be selected and used

        Parameters:
            min_num_events_or_mu:
                The minimum trace length for uniform distributions, or the mean of the distribution for normal distributions.
            max_num_events_or_sigma:
                The maximum trace length for uniform distributions, or the standard deviation of the distribution for normal distributions.
            total_traces:
                The number of traces to generate.
            dist_type:
                The type of distribution to use. Can be "uniform", "gaussian", or "custom". Default is "uniform".
            custom_probabilities:
                A list of custom probabilities to use for the "custom" distribution type. Default is None

        Raises:
            ValueError:
                The Distribution class will raise ValueErrors if the parameters are invalid.
        """

        # Sets the new number of traces
        self.set_total_traces(total_traces)
        self.custom_probabilities = custom_probabilities

        # If the dist is gaussian sets mu and sigma
        if dist_type == Distribution.GAUSSIAN:

            if min_num_events_or_mu is None:
                raise ValueError("min_num_events_or_mu cannot be None")
            if max_num_events_or_sigma is None:
                raise ValueError("min_num_events_or_mu cannot be None")

            # Sets mu and sigma
            self.mu = min_num_events_or_mu = float(min_num_events_or_mu)
            self.sigma = max_num_events_or_sigma = float(max_num_events_or_sigma)

        else:
            # Resets mu and sigma
            self.mu = None
            self.sigma = None

            # Sets new min max events
            self.set_min_max_events(min_num_events_or_mu, max_num_events_or_sigma)

            # Recover values
            min_num_events_or_mu = self.min_events
            max_num_events_or_sigma = self.max_events

        # Create the new distribution
        self.distribution = Distribution(min_num_events_or_mu, max_num_events_or_sigma, self.total_traces, dist_type, self.custom_probabilities, self.verbose)
        self.total_traces_distribution = self.distribution.get_distribution()
        self.distribution_type = self.distribution.get_distribution_type()

        self.debug_message(f"New Distribution min_num_events_or_mu: {min_num_events_or_mu}, "
                           f"max_num_events_or_sigma: {max_num_events_or_sigma}, num_traces: {self.total_traces}, "
                           f"distribution: {dist_type}, probabilities: {custom_probabilities} calculated")

        return self.total_traces_distribution

    def recompute_distribution(self):
        """
        Generates another distribution using the current distribution settings
        """

        self.total_traces_distribution = self.distribution.distribute_probabilities()

    def set_min_max_events(self, min_event: typing.Union[int, float, None], max_event: typing.Union[int, float, None]):
        """
        Sets the minimum number of events and the maximum number of events for the logger

        Raises:
            ValueError:
                If min_event is not a positive integer
            ValueError:
                If max_event is not a positive integer
        """

        if min_event is None and max_event is None:  # Do not change values
            return

        # Otherwise a change has been made
        # If one is None the current value is used
        if min_event is None:
            min_event = self.min_events
        if max_event is None:
            max_event = self.max_events

        # Checks essential conditions on the min max events
        if not isinstance(min_event, int):
            if isinstance(min_event, float):
                min_event = int(min_event)
            else:
                raise ValueError(f"min_events is not of type int but of type {type(min_event)}!")
        if not isinstance(max_event, int):
            if isinstance(max_event, float):
                max_event = int(max_event)
            else:
                raise ValueError(f"max_event is not of type int but of type {type(min_event)}!")

        if min_event > max_event:  # swap if min is bigger than max
            max_event, min_event = min_event, max_event
        if min_event <= 0 and max_event <= 0:
            raise ValueError(f"min_events({min_event}) and max_events({max_event}) events should be greater than 0!")
        if min_event <= 0:
            raise ValueError(f"min_events({min_event}) should be greater than 0!")
        if max_event <= 0:
            raise ValueError(f"max_events({max_event}) should be greater than 0!")

        # Assign
        self.max_events: int = max_event
        self.min_events: int = min_event

    def set_total_traces(self, total_traces: int):
        """
        Sets the number of traces for the distribution

        Raises:
            ValueError: If num_traces is not a positive integer
        """

        if total_traces is None:  # Do not change
            return

        # Otherwise a changes has been made
        if not isinstance(total_traces, int):
            raise ValueError(f"num_traces is not of type int!")
        if total_traces <= 0:
            raise ValueError(f"num_traces({total_traces}) must be greater than zero!")

        self.total_traces = total_traces

    def set_verbose(self, verbose: bool):
        """
        Sets verbose for debugging information
        """

        if isinstance(verbose, bool):
            self.verbose = verbose

    def debug_message(self, msg: any):
        """
        Used for debugging purposes, If verbose is True, the message is printed.
        """

        if self.verbose:
            self.__py_logger.debug(str(msg))
