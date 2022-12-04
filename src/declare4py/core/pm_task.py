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
    decl_model : LTLModel
    
"""
from __future__ import annotations


class PMTask:

    def __init__(self, log: LogAnalyzer | None, ltl_model: LTLModel):
        if log is None:
            log = LogAnalyzer()
        self.log_analyzer: LogAnalyzer = log
        self.decl_model: LTLModel = ltl_model

    @abstractmethod
    def run(self):
        pass
