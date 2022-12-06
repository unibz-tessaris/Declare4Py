from __future__ import annotations

from abc import abstractmethod
from src.declare4py.models.ltl_model import LTLModel
from src.declare4py.models.process_models import ProcessModel
from src.declare4py.process_mining.log_analyzer import LogAnalyzer

"""
Initializes super class PMTask

Attributes
-------
    log_analyzer : LogAnalyzer
    decl_model : LTLModel
    
"""


class PMTask(ProcessModel):

    def __init__(self, log: LogAnalyzer | None, ltl_model: LTLModel):
        super().__init__()
        if log is None:
            log = LogAnalyzer()
        self.log_analyzer: LogAnalyzer = log
        self.ltl_model: LTLModel = ltl_model

    @abstractmethod
    def run(self, *args, **kwargs):
        pass
