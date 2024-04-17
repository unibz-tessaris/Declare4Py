from __future__ import annotations
from abc import ABC

from Declare4Py.ProcessMiningTasks.AbstractPMTask import AbstractPMTask
from Declare4Py.D4PyEventLog import D4PyEventLog
from Declare4Py.ProcessModels.AbstractModel import ProcessModel

import logging
import typing
import collections

from Declare4Py.ProcessMiningTasks.LogGenerator.ASP.ASPUtils.Distribution import Distribution


class AbstractLogGenerator(AbstractPMTask, ABC):
    """
    An abstract class for verifying whether the behavior of a given process model, as recorded in a log,
    is in line with some expected behaviors provided in the form of a process model ()
    """

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
        self.__Abs_Log_Gen_Logger = logging.getLogger("Abstract Log Generator")

        self.log_length: int = 0
        self.max_events: int = 0
        self.min_events: int = 0
        self.verbose: bool = False

        """Check Init Conditions"""
        self.set_verbose(verbose)
        self.set_total_traces(total_traces)
        self.set_min_max_events(min_event, max_event)

        """Initialize Distributions Setting"""
        self.distribution_type: str = Distribution.UNIFORM
        self.custom_probabilities: None = None
        self.mu: typing.Union[float, None] = None
        self.sigma: typing.Union[float, None] = None

    def compute_distribution(self, num_traces: typing.Union[int, None] = None, ) -> collections.Counter:
        """
        Computes the distribution of the traces as a Counter object using
        distribution_type, min-max events or mu and signa or custom_probabilities

        Parameters:
            num_traces (int):
                number of traces to generate
        Returns:
            The Distribution of the traces probabilities as a Counter object
        """
        if num_traces is None:
            num_traces = self.log_length

        if self.distribution_type == Distribution.GAUSSIAN:
            return Distribution(self.mu, self.sigma, num_traces, self.distribution_type, self.custom_probabilities, self.verbose).get_distribution()
        else:
            return Distribution(self.min_events, self.max_events, num_traces, self.distribution_type, self.custom_probabilities, self.verbose).get_distribution()

    def change_distribution_settings(
            self,
            min_num_events_or_mu: typing.Union[int, float, None] = None,
            max_num_events_or_sigma: typing.Union[int, float, None] = None,
            dist_type: typing.Union[str, None] = None,
    ):
        """
        It changes the distribution of the Log Generator if new parameters or values are inserted
        If some values are None the current values will not be changed

        Parameters:
            min_num_events_or_mu:
                The minimum trace length for uniform distributions, or the mean of the distribution for normal distributions.
            max_num_events_or_sigma:
                The maximum trace length for uniform distributions, or the standard deviation of the distribution for normal distributions.
            dist_type:
                The type of distribution to use. Can be "uniform", "gaussian", or "custom". Default is "uniform".
        Raises:
            ValueError:
                The class will raise ValueErrors if at least one parameter is invalid.
        """
        if dist_type is not None:
            self.set_distribution_type(dist_type)

        msg = f"The distribution type is set to {self.distribution_type} with "

        # If the dist is gaussian sets mu and sigma
        if self.distribution_type == Distribution.GAUSSIAN:
            # Sets mu and sigma
            self.set_mu_sigma(min_num_events_or_mu, max_num_events_or_sigma)
            msg += f"mu = {self.mu} and sigma = {self.sigma}"
        else:
            # Sets new min max events
            self.set_min_max_events(min_num_events_or_mu, max_num_events_or_sigma)
            msg += f"min events = {self.min_events} and max events = {self.max_events}"

        self.__debug_message(msg)

    def set_custom_probabilities(self, custom_probabilities: typing.Union[list, None]):
        """
        It sets the custom probabilities of the Log Generator

        Parameters:
            custom_probabilities:
                A list of custom probabilities to use for the "custom" distribution type. Default is None
        """
        self.custom_probabilities = custom_probabilities

    def set_mu_sigma(self, mu: typing.Union[int, float, None] = None, sigma: typing.Union[int, float, None] = None):
        """
        Sets the mu and sigma values
        Int numbers are transformed into floats

        Raises:
            ValueError:
                If min_event is not of type float
            ValueError:
                If max_event is not of type float
        """

        if mu is None and sigma is None:  # Do not change values
            return

        # Otherwise a change has been made
        if mu is not None:
            if not isinstance(mu, float) and not isinstance(mu, int):
                raise ValueError(f"mu is not of type float but of type {type(mu)}!")
            self.mu = float(mu)

        if sigma is not None:
            if not isinstance(sigma, float) and not isinstance(mu, int):
                raise ValueError(f"sigma is not of type float but of type {type(sigma)}!")
            self.sigma = float(sigma)

        if self.sigma is None or self.mu is None:
            raise ValueError(f"Mu and sigma must be both assigned simultaneously. sigma is {self.sigma}, mu is {self.mu}")

    def set_min_max_events(self, min_events: typing.Union[int, float, None] = None, max_events: typing.Union[int, float, None] = None):
        """
        Sets the minimum number of events and the maximum number of events for the logger
        Float numbers are transformed into ints

        Raises:
            ValueError:
                If min_event is not a positive integer
            ValueError:
                If max_event is not a positive integer
        """

        if min_events is None and max_events is None:  # Do not change values
            return

        # Otherwise a change has been made
        if min_events is not None:
            if not isinstance(min_events, int) and not isinstance(min_events, float):
                raise ValueError(f"min_events is not of type int but of type {type(min_events)}!")
            self.min_events = int(min_events)

        if max_events is not None:
            if not isinstance(max_events, int) and not isinstance(min_events, float):
                raise ValueError(f"max_events is not of type int but of type {type(max_events)}!")
            self.max_events = int(max_events)

        if self.min_events > self.max_events:  # swap if min is bigger than max
            self.max_events, self.min_events = self.min_events, self.max_events

        if self.min_events <= 0 and self.max_events <= 0:
            raise ValueError(f"min_events({self.min_events}) and max_events({self.max_events}) events should be greater than 0!")
        if self.min_events <= 0:
            raise ValueError(f"min_events({self.min_events}) should be greater than 0!")
        if self.max_events <= 0:
            raise ValueError(f"max_events({self.max_events}) should be greater than 0!")

    def set_total_traces(self, log_length: int):
        """
        Sets the number of traces for the distribution

        Raises:
            ValueError: If num_traces is not a positive integer
        """

        if log_length is None:  # Do not change
            return

        # Otherwise a changes has been made
        if not isinstance(log_length, int):
            raise ValueError(f"num_traces is not of type int!")
        if log_length <= 0:
            raise ValueError(f"num_traces({log_length}) must be greater than zero!")

        self.log_length = log_length

    def set_distribution_type(self, distribution_type: str):
        """
        Sets the distribution type of the generator

        Raises:
            ValueError: If the distribution type is not valid
        """
        if Distribution.has_distribution(distribution_type):
            self.distribution_type = distribution_type.upper()
        else:
            raise ValueError(f"Distribution type '{distribution_type}' is not valid!")

    def set_verbose(self, verbose: bool):
        """
        Sets verbose for debugging information
        """

        if isinstance(verbose, bool):
            self.verbose = verbose

    def __debug_message(self, msg: any):
        """
        Used for debugging purposes, If verbose is True, the message is printed.
        """

        if self.verbose:
            self.__Abs_Log_Gen_Logger.debug(str(msg))
