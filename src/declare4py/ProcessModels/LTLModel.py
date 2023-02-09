from abc import ABC

from src.declare4py.ProcessModels.AbstractModel import ProcessModel


class LTLModel(ProcessModel, ABC):

    def __init__(self, formula: str = None):
        super().__init__()
        self.formula: str = formula
