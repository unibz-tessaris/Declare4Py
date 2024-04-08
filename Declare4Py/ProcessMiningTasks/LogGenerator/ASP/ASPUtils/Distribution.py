import collections
import logging
import typing
import fractions
import numpy as np
import warnings


class Distribution:

    """
    A Class used to generate probability distributions.
    """

    UNIFORM: typing.final(str) = "UNIFORM"
    GAUSSIAN: typing.final(str) = "GAUSSIAN"
    CUSTOM: typing.final(str) = "CUSTOM"

    __DISTRIBUTIONS: typing.final(typing.List[str]) = [UNIFORM, GAUSSIAN, CUSTOM]

    def __init__(self,
                 min_num_events_or_mu: typing.Union[int, float],
                 max_num_events_or_sigma: typing.Union[int, float],
                 num_traces: int,
                 dist_type: typing.Union[str, None] = None,
                 custom_probabilities: typing.Union[typing.List[float], None] = None,
                 verbose=False):

        """
        Args:
            min_num_events_or_mu:
                The minimum trace length for uniform distributions, or the mean of the distribution for normal distributions.
            max_num_events_or_sigma:
                The maximum trace length for uniform distributions, or the standard deviation of the distribution for normal distributions.
            num_traces:
                The number of traces to generate.
            dist_type:
                The type of distribution to use. Can be "uniform", "gaussian", or "custom". Default is "uniform".
            custom_probabilities:
                A list of custom probabilities to use for the "custom" distribution type. Default is None
            verbose:
                If True, prints debugging information. Default is False.

        Raises:
            ValueError:
                If min_num_events_or_mu or max_num_events_or_sigma are not integers or floats.
            ValueError:
                If num_traces is not a positive integer.
        """

        """Initialize Distribution"""
        self.__distribution_logger = logging.getLogger("Distribution")
        self.min_num_events_or_mu: typing.Union[int, float] = 0
        self.max_num_events_or_sigma: typing.Union[int, float] = 0
        self.num_traces: int = 0
        self.verbose: bool = False
        self.dist_type = ""
        self.custom_probabilities: typing.Union[typing.List[float], None] = custom_probabilities

        """Check Init Conditions and sets the constructor parameters"""
        self.set_verbose(verbose)
        self.set_distribution_type(dist_type)
        self.set_min_num_events_or_mu(min_num_events_or_mu)
        self.set_max_num_events_or_sigma(max_num_events_or_sigma)
        self.set_num_traces(num_traces)

        self.__debug_message(f"Distribution() {self.dist_type} min_mu: {self.min_num_events_or_mu}"
                             f" max_sigma: {self.max_num_events_or_sigma} num_traces: {self.num_traces}"
                             f" custom_prob: {self.custom_probabilities}")

        self.distribution: collections.Counter = self.distribute_probabilities()

    def distribute_probabilities(self) -> collections.Counter:
        """
        Generates trace lengths according to the specified distribution.
        Returns:
            For "uniform", "gaussian" and "custom" distribution types, a `collections.Counter` object containing the count of each trace length generated.
       """

        if self.dist_type == Distribution.GAUSSIAN:
            self.__debug_message("Calculating Normal Distribution")
            self.distribution = self.__normal_distribution()
        elif self.dist_type == Distribution.UNIFORM:
            self.__debug_message("Calculating Uniform Distribution")
            self.distribution = self.__distribute_random_choices()
        else:  # Custom
            self.__debug_message("Calculating Custom Distribution")
            self.distribution = self.__distribute_random_choices()
        return self.distribution

    def __normal_distribution(self) -> collections.Counter:
        """
        Generates trace lengths according to a normal (Gaussian) distribution.

        Returns:
            A `collections.Counter` object containing the count of each trace length generated.

        Raises:
            ValueError: If Mu is lower than 2
            ValueError: If Sigma is a negative number | lower than zero

        Notes:
            Trace lengths less than 1 are not included in the output.
        """

        mu: float = float(self.min_num_events_or_mu)
        sigma: float = float(self.max_num_events_or_sigma)

        if mu < 1:
            raise ValueError(f"MU must be greater than 1")
        if sigma < 0:
            raise ValueError(f"Sigma must be a positive value")

        trace_lens = np.random.normal(mu, sigma, self.num_traces)
        trace_lens = np.round(trace_lens)
        trace_lens = trace_lens[trace_lens > 1]
        return collections.Counter(trace_lens)

    def __distribute_random_choices(self) -> collections.Counter:
        """
        Generates trace lengths according to a uniform or custom distribution.

        Returns:
            A `collections.Counter` object containing the count of each trace length generated.

        Raises:
            ValueError: If the probability sum is not 1
            ValueError: If the number of events is not the same as the number of probabilities provided
        """

        min_num = int(self.min_num_events_or_mu)
        max_num = int(self.max_num_events_or_sigma)

        # Checks if the probability is Uniform or if the custom probabilities are None
        # In this case generates the probabilities using the Uniform Distribution
        if self.dist_type == Distribution.UNIFORM or self.custom_probabilities is None:
            self.__debug_message("Generating Uniform Probabilities since either distribution is uniform or custom probabilities are None")
            num_probabilities = max_num - min_num + 1
            probabilities = [fractions.Fraction(1, num_probabilities) for _ in range(0, num_probabilities)]
        else:
            probabilities = self.custom_probabilities

        # Checks essential conditions
        s = sum(probabilities)
        self.__debug_message(f"Probabilities sum is {s}")
        if s != 1:
            raise ValueError(f"Sum of provided list must be 1 but found {s}")

        prefixes = range(min_num, max_num + 1)
        prob_len = len(probabilities)

        if prob_len != len(prefixes):
            raise ValueError(
                f"Number of probabilities provided are {prob_len} but min and max difference is {len(prefixes)}")

        # Generates the traces
        trace_lens = np.random.choice(prefixes, self.num_traces, p=probabilities)
        self.__debug_message(f"Distribution result: {trace_lens}")
        return collections.Counter(trace_lens)

    @staticmethod
    def has_distribution(distribution: str) -> bool:
        return distribution.upper() in Distribution.__DISTRIBUTIONS

    def set_min_num_events_or_mu(self, min_num_events_or_mu: typing.Union[int, float]):
        """
        Sets min_num_events_or_mu for the distribution

        Raises:
            ValueError: If min_num_events_or_mu is not of type int or float
        """

        if not (isinstance(min_num_events_or_mu, int) or isinstance(min_num_events_or_mu, float)):
            raise ValueError(f"min_num_events_or_mu is not of type int or float but of type {type(min_num_events_or_mu)}!")
        else:
            self.min_num_events_or_mu: typing.Union[int, float] = min_num_events_or_mu

    def set_max_num_events_or_sigma(self, max_num_events_or_sigma: typing.Union[int, float]):
        """
        Sets max_num_events_or_sigma for the distribution

        Raises:
            ValueError: If max_num_events_or_sigma is not of type int or float
        """

        if not (isinstance(max_num_events_or_sigma, int) or isinstance(max_num_events_or_sigma, float)):
            raise ValueError(f"max_num_events_or_sigma is not of type int or float but of type {type(max_num_events_or_sigma)}!")
        else:
            self.max_num_events_or_sigma: typing.Union[int, float] = max_num_events_or_sigma

    def set_verbose(self, verbose: bool):
        """
        Sets verbose for debugging information
        """

        if isinstance(verbose, bool):
            self.verbose = verbose

    def set_num_traces(self, num_traces: int):
        """
        Sets the number of traces for the distribution

        Raises:
            ValueError: If num_traces is not a positive integer
        """

        if not isinstance(num_traces, int):
            raise ValueError(f"num_traces is not of type int!")
        if num_traces <= 0:
            raise ValueError(f"num_traces({num_traces}) must be greater than zero!")
        self.num_traces = num_traces

    def set_distribution_type(self, dist_type: typing.Union[str, None]):
        """
        Sets the distribution type for the distribution

        Note:
            If the distribution type is None, the default Uniform distribution type is used.
        """

        if dist_type is None or not Distribution.has_distribution(dist_type):
            warnings.warn(f"WARNING: Distribution {dist_type} not in {Distribution.__DISTRIBUTIONS}. Default Distribution is set to {Distribution.UNIFORM}")
            self.dist_type = Distribution.UNIFORM
        else:
            self.dist_type = dist_type

    def get_distribution(self) -> collections.Counter:
        """
        Returns the distribution

        Returns:
            The `collections.Counter` object containing the count of each trace generated through the distribution.
        """
        return self.distribution

    def get_distribution_type(self) -> str:
        """
        Returns the distribution type

        Returns:
            Returns the distribution type
        """
        return self.dist_type

    def __debug_message(self, msg: any):
        """
        Used for debugging purposes, If verbose is True, the message is printed.
        """
        if self.verbose:
            self.__distribution_logger.debug(str(msg))


"""
if __name__ == '__main__':
    print(Distribution(6, 10, 10, "NOT UNIFORM", None, True).get_distribution())
    print(Distribution(6, 10, 10, "UNIFORM", None, True).get_distribution())
    print(Distribution(1.5, 0.15, 1000, Distribution.GAUSSIAN, None, True).get_distribution())
    print(Distribution(2, 4, 10, Distribution.CUSTOM, [0.3333333333333333, 0.3333333333333333, 0.3333333333333333], True).get_distribution())
"""