from abc import ABC

from src.Declare4py.ProcessModels.AbstractModel import ProcessModel


class LTLModel(ProcessModel, ABC):

    def __init__(self):
        super().__init__()
        self.formula: str = ""
        self.parsed_formula = None

    def parse_from_string(self, content: str, new_line_ctrl: str = "\n"):
        if type(content) is not str:
            raise RuntimeError("You must specify a string as input formula.")
        # @Diellsimeone, usare il parsing in logaut
        # ma prima devi sostituire i numeri con lettere e mettere tutto in lowercase
        # raccogliere la expception del parser se la formula di input non è ben formata
        self.formula = content
        self.parsed_formula = None
