import logging
import typing


class Distributor:
    """
    A class for generating trace lengths according to different distributions.
    """

    __available_distributions: typing.Type[str] = typing.Literal["uniform", "gaussian", "custom"]

    def __init__(self):
        self.__logger = logging.getLogger("Distributor")

    @staticmethod
    def get_distributions() -> typing.List[str]:
        return list(Distributor.__available_distributions.__dict__["__args__"])
