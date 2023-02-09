from __future__ import annotations
from abc import abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")


class ProcessModel(Generic[T]):

    def __init__(self):
        self.activities: [str] = []

    @abstractmethod
    def parse_from_file(self, model_path: str, **kwargs) -> T:
        pass

    def get_model_activities(self):
        return self.activities

    # @abstractmethod
    # def parse_from_file(self, filename: str) -> T:
    #     pass
    #
    # @abstractmethod
    # def parse_from_string(self, content: str, new_line_ctrl: str = "\n") -> T:
    #     pass
    #
    # @abstractmethod
    # def parse_model(self) -> T:
    #     pass

