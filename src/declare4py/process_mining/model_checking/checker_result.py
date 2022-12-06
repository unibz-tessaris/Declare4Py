from __future__ import annotations

"""
Initializes class CheckerResults

Parameters
--------
    num_fulfillments: int
    num_violations: int
    num_pendings: int
    num_activations: int
    state: TraceState
"""


class CheckerResult:
    def __init__(self, num_fulfillments, num_violations, num_pendings, num_activations, state):
        # super().__init__()
        self.num_fulfillments = num_fulfillments
        self.num_violations = num_violations
        self.num_pendings = num_pendings
        self.num_activations = num_activations
        self.state = state
