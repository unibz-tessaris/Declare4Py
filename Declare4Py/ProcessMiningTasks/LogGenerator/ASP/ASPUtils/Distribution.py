import collections
import logging
import typing
import fractions
import numpy as np


class Distribution:
    """
    A class for generating trace lengths according to different distributions.
    """

    # Defining Logger
    __logger = logging.getLogger("Distribution")

    # Defining possible distributions
    __available_distributions: typing.Type[str] = typing.Literal["uniform", "gaussian", "custom"]

    @staticmethod
    def get_distributions() -> typing.List[str]:
        """
        Returns the list of possible distributions

        Returns:
            A list containing the available distributions as strings
        """

        return list(Distribution.__available_distributions.__dict__["__args__"])

    @staticmethod
    def distribution(
            min_num_events_or_mu: typing.Union[int, float],
            max_num_events_or_sigma: typing.Union[int, float],
            num_traces: int,
            dist_type: typing.Literal["uniform", "gaussian", "custom"] = "uniform",
            custom_probabilities: typing.Union[typing.List[float], None] = None
    ) -> collections.Counter:
        """
        Generates trace lengths according to the specified distribution.

        Args:
            min_num_events_or_mu: The minimum trace length for uniform distributions, or the mean of the distribution for normal distributions.
            max_num_events_or_sigma: The maximum trace length for uniform distributions, or the standard deviation of the distribution for normal distributions.
            num_traces: The number of traces to generate.
            dist_type: The type of distribution to use. Can be "uniform", "gaussian", or "custom". Default is "uniform".
            custom_probabilities: A list of custom probabilities to use for the "custom" distribution type. Default is None

        Returns:
            For "uniform", "gaussian" and "custom" distribution types, a `collections.Counter` object containing the count of each trace length generated.

        Raises:
            AttributeError: If the distribution type is not in the list of possible distributions
       """

        Distribution.__logger.debug(f"Distribution() {dist_type} min_mu: {min_num_events_or_mu}"
                                   f" max_sigma: {max_num_events_or_sigma} num_traces: {num_traces}"
                                   f" custom_prob: {custom_probabilities}")

        if dist_type not in Distribution.get_distributions():
            raise AttributeError(f"Specified type of distribution {dist_type} not supported yet.")

        if dist_type == "gaussian":
            return Distribution.normal_distribution(float(min_num_events_or_mu), float(max_num_events_or_sigma), num_traces)
        elif dist_type == "uniform":
            return Distribution.uniform_distribution(int(min_num_events_or_mu), int(max_num_events_or_sigma), num_traces)
        else:  # Custom
            return Distribution.custom_distribution(int(min_num_events_or_mu), int(max_num_events_or_sigma), num_traces,
                                                    custom_probabilities)

    @staticmethod
    def normal_distribution(mu: float, sigma: float, num_traces: int) -> collections.Counter:
        """
        Generates trace lengths according to a normal (Gaussian) distribution.

        Args:
            mu: The mean of the distribution.
            sigma: The standard deviation of the distribution.
            num_traces: The number of traces to generate.

        Returns:
            A `collections.Counter` object containing the count of each trace length generated.

        Raises:
            ValueError: If Mu is lower than 2
            ValueError: If Sigma is a negative number | lower than zero

        Notes:
            Trace lengths less than 1 are not included in the output.
        """

        if mu < 2:
            raise ValueError(f"MU must be greater than 1")
        if sigma < 0:
            raise ValueError(f"Sigma must be a positive value")

        trace_lens = np.random.normal(mu, sigma, num_traces)
        trace_lens = np.round(trace_lens)
        trace_lens = trace_lens[trace_lens > 1]
        return collections.Counter(trace_lens)

    @staticmethod
    def uniform_distribution(min_num: int, max_num: int, num_traces: int) -> collections.Counter:
        """
        Generates trace lengths according to a uniform distribution.

        Args:
            min_num: The minimum trace length.
            max_num: The maximum trace length.
            num_traces: The number of traces to generate.

        Returns:
            A `collections.Counter` object containing the count of each trace length generated.
        """

        return Distribution.custom_distribution(min_num, max_num, num_traces)

    @staticmethod
    def custom_distribution(min_num: int, max_num: int, num_traces: int,
                            probabilities: typing.Union[None, typing.List[float]] = None) -> collections.Counter:
        """
        Generates trace lengths according to a custom distribution specified by the `probabilities` list.

        Args:
            min_num: The minimum trace length.
            max_num: The maximum trace length.
            num_traces: The number of traces to generate.
            probabilities: A list of probabilities for each trace length from `min_num` to `max_num`.
                The list must have a length equal to `max_num - min_num + 1`, and the sum of the probabilities must be 1.

        Returns:
            A `collections.Counter` object containing the count of each trace length generated.
        """

        return Distribution.__distribute_random_choices(min_num, max_num, num_traces, probabilities)

    @staticmethod
    def __distribute_random_choices(
            min_num: int,
            max_num: int,
            num_traces: int,
            probabilities: typing.Union[None, typing.List[float]] = None
    ) -> collections.Counter:

        if probabilities is None:
            Distribution.__logger.debug("Probabilities not provided, using uniform probabilities")
            probabilities = Distribution.__get_uniform_probabilities(max_num - min_num + 1)

        s = sum(probabilities)
        Distribution.__logger.debug(f"Probabilities sum is {s}")
        if s != 1:
            raise ValueError(f"Sum of provided list must be 1 but found {s}")

        prefixes = range(min_num, max_num + 1)
        prob_len = len(probabilities)

        if prob_len != len(prefixes):
            raise ValueError(
                f"Number of probabilities provided are {prob_len} but min and max difference is {len(prefixes)}")

        trace_lens = np.random.choice(prefixes, num_traces, p=probabilities)
        Distribution.__logger.debug(f"Distribution result: {trace_lens}")
        return collections.Counter(trace_lens)

    @staticmethod
    def __get_uniform_probabilities(num_probabilities: int) -> typing.List[fractions.Fraction]:
        return [fractions.Fraction(1, num_probabilities) for _ in range(0, num_probabilities)]


if __name__ == "__main__":
    p = Distribution.normal_distribution(2.1, 3.5, 20)
    print(p)
