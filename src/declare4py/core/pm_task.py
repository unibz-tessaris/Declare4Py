try:
    from future import annotations
except:
    pass
from abc import abstractmethod
from src.declare4py.log_utils.parsers.declare.decl_model import DeclModel
from src.declare4py.log_utils.log_analyzer import LogAnalyzer
from src.declare4py.log_utils.ltl_model import LTLModel

"""
Initializes super class PMTask

Attributes
-------
    log_analyzer : LogAnalyzer

    decl_model : DeclareModel
    
"""


class PMTask:

    def __init__(self, log: LogAnalyzer, ltl_model: LTLModel):
        self.log_analyzer: LogAnalyzer = log
        self.decl_model: DeclModel = ltl_model

    @abstractmethod
    def run(self):
        pass
