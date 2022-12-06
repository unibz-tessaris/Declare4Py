from __future__ import annotations

from abc import ABC

from src.declare4py.models.pm_task import PMTask

"""
Initializes class Discovery, inheriting from class PMTask

Parameters
-------
    PMTask
        inheriting from PMTask
Attributes
-------
    consider_vacuity : bool
        True means that vacuously satisfied traces are considered as satisfied, violated otherwise.
        
    support : float
        the support that a discovered constraint needs to have to be included in the filtered result.

    max_declare_cardinality : int, optional
        the maximum cardinality that the algorithm checks for DECLARE templates supporting it (default 3).
"""


class Discovery(PMTask, ABC):

    def __init__(self, log, ltl_model):
        self.consider_vacuity: bool | None = None
        self.support: str | None = None
        self.max_declare_cardinality: int | None = None
        super().__init__(log, ltl_model)

