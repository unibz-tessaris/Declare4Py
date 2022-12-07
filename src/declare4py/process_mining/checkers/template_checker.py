from __future__ import annotations

from abc import ABC, abstractmethod

from src.declare4py.models.decl_model import DeclareParserUtility, TraceState, DeclareTemplate
from datetime import timedelta

from src.declare4py.process_mining.checkers.checker_result import CheckerResult

glob = {'__builtins__': None}


class TemplateConstraintChecker(ABC):

    def __init__(self, traces: dict, completed: bool, activities: [str], rules: dict):
        self.dpu = DeclareParserUtility()
        self.traces: dict = traces
        self.completed: bool = completed
        self.activities: [str] = activities
        self.rules: dict = rules

    @abstractmethod
    def get_check_result(self) -> CheckerResult:
        pass


class MPChoice(TemplateConstraintChecker):

    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])
        a_or_b_occurs = False
        for A in self.traces:
            if A["concept:name"] == self.activities[0] or A["concept:name"] == self.activities[1]:
                locl = {'A': A, 'T': self.traces[0], 'timedelta': timedelta, 'abs': abs, 'float': float}
                if eval(activation_rules, glob, locl) and eval(time_rule, glob, locl):
                    a_or_b_occurs = True
                    break
        state = None
        if not self.completed and not a_or_b_occurs:
            state = TraceState.POSSIBLY_VIOLATED
        elif self.completed and not a_or_b_occurs:
            state = TraceState.VIOLATED
        elif a_or_b_occurs:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)


class MPExclusiveChoice(TemplateConstraintChecker):
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])
        a_occurs = False
        b_occurs = False
        for A in self.traces:
            locl = {'A': A, 'T': self.traces[0], 'timedelta': timedelta, 'abs': abs, 'float': float}
            if not a_occurs and A["concept:name"] == self.activities[0]:
                if eval(activation_rules, glob, locl) and eval(time_rule, glob, locl):
                    a_occurs = True
            if not b_occurs and A["concept:name"] == self.activities[1]:
                if eval(activation_rules, glob, locl) and eval(time_rule, glob, locl):
                    b_occurs = True
            if a_occurs and b_occurs:
                break
        state = None
        if not self.completed and (not a_occurs and not b_occurs):
            state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and (a_occurs ^ b_occurs):
            state = TraceState.POSSIBLY_SATISFIED
        elif (a_occurs and b_occurs) or (self.completed and (not a_occurs and not b_occurs)):
            state = TraceState.VIOLATED
        elif self.completed and (a_occurs ^ b_occurs):
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)


class MPExistence(TemplateConstraintChecker):
    """
        mp-existence constraint checker
        Description: The future constraining constraint existence(n, a) indicates that
        event a must occur at least n-times in the trace.
    """

    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])
        num_activations = 0
        for A in self.traces:
            if A["concept:name"] == self.activities[0]:
                locl = {'A': A, 'T': self.traces[0], 'timedelta': timedelta, 'abs': abs, 'float': float}
                if eval(activation_rules, glob, locl) and eval(time_rule, glob, locl):
                    num_activations += 1
        n = self.rules["n"]
        state = None
        if not self.completed and num_activations < n:
            state = TraceState.POSSIBLY_VIOLATED
        elif self.completed and num_activations < n:
            state = TraceState.VIOLATED
        elif num_activations >= n:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)


class MPAbsence(TemplateConstraintChecker):
    """
        mp-absence constraint checker
        Description: The future constraining constraint absence(n + 1, a) indicates that
        event a may occur at most n − times in the trace.
    """

    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        for A in self.traces:
            if A["concept:name"] == self.activities[0]:
                locl = {'A': A, 'T': self.traces[0], 'timedelta': timedelta, 'abs': abs, 'float': float}
                if eval(activation_rules, glob, locl) and eval(time_rule, glob, locl):
                    num_activations += 1

        n = self.rules["n"]
        state = None
        if not self.completed and num_activations < n:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_activations >= n:
            state = TraceState.VIOLATED
        elif self.completed and num_activations < n:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)


class MPInit(TemplateConstraintChecker):
    """
        mp-init constraint checker
        Description: The future constraining constraint init(e) indicates
        that event e is the first event that occurs in the trace.
    """

    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])

        state = TraceState.VIOLATED
        if self.traces[0]["concept:name"] == self.activities[0]:
            locl = {'A': self.traces[0]}
            if eval(activation_rules, glob, locl):
                state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)


class MPExactly(TemplateConstraintChecker):
    """
        mp-exactly constraint checker
    """

    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])
        num_activations = 0
        for A in self.traces:
            if A["concept:name"] == self.activities[0]:
                locl = {'A': A, 'T': self.traces[0], 'timedelta': timedelta, 'abs': abs, 'float': float}
                if eval(activation_rules, glob, locl) and eval(time_rule, glob, locl):
                    num_activations += 1
        n = self.rules["n"]
        state = None
        if not self.completed and num_activations < n:
            state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_activations == n:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_activations > n or (self.completed and num_activations < n):
            state = TraceState.VIOLATED
        elif self.completed and num_activations == n:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)


class MPRespondedExistence(TemplateConstraintChecker):
    # mp-responded-existence constraint checker
    # Description:
    # The future constraining and history-based constraint
    # respondedExistence(a, b) indicates that, if event a occurs in the trace
    # then event b occurs in the trace as well.
    # Event a activates the constraint.
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        pendings = []
        num_fulfillments = 0
        num_violations = 0
        num_pendings = 0

        for event in self.traces:
            if event["concept:name"] == self.activities[0]:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pendings.append(event)

        for event in self.traces:
            if not pendings:
                break

            if event["concept:name"] == self.activities[1]:
                for A in reversed(pendings):
                    locl = {'A': A, 'T': event, 'timedelta': timedelta, 'abs': abs, 'float': float}
                    if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                        pendings.remove(A)
                        num_fulfillments += 1

        if self.completed:
            num_violations = len(pendings)
        else:
            num_pendings = len(pendings)

        num_activations = num_fulfillments + num_violations + num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations > 0:
            state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif self.completed and num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings,
                             num_activations=num_activations, state=state)


class MPResponse(TemplateConstraintChecker):
    # mp-response constraint checker
    # Description:
    # The future constraining constraint response(a, b) indicates that
    # if event a occurs in the trace, then event b occurs after a.
    # Event a activates the constraint.
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        pendings = []
        num_fulfillments = 0
        num_violations = 0
        num_pendings = 0

        for event in self.traces:
            if event["concept:name"] == self.activities[0]:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pendings.append(event)

            if pendings and event["concept:name"] == self.activities[1]:
                for A in reversed(pendings):
                    locl = {'A': A, 'T': event, 'timedelta': timedelta, 'abs': abs, 'float': float}
                    if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                        pendings.remove(A)
                        num_fulfillments += 1

        if self.completed:
            num_violations = len(pendings)
        else:
            num_pendings = len(pendings)

        num_activations = num_fulfillments + num_violations + num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_pendings > 0:
            state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_pendings == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif self.completed and num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings,
                             num_activations=num_activations, state=state)


class MPAlternateResponse(TemplateConstraintChecker):
    # mp-alternate-response constraint checker
    # Description:
    # The future constraining constraint alternateResponse(a, b) indicates that
    # each time event a occurs in the trace then event b occurs afterwards
    # before event a recurs.
    # Event a activates the constraint.
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        pending = None
        num_activations = 0
        num_fulfillments = 0
        num_pendings = 0

        for event in self.traces:
            if event["concept:name"] == self.activities[0]:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pending = event
                    num_activations += 1

            if event["concept:name"] == self.activities[1] and pending is not None:
                locl = {'A': pending, 'T': event, 'timedelta': timedelta, 'abs': abs, 'float': float}
                if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                    pending = None
                    num_fulfillments += 1

        if not self.completed and pending is not None:
            num_pendings = 1

        num_violations = num_activations - num_fulfillments - num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0 and num_pendings > 0:
            state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0 and num_pendings == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0 or (self.completed and num_pendings > 0):
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0 and num_pendings == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings,
                             num_activations=num_activations, state=state)


class MPChainResponse(TemplateConstraintChecker):
    # mp-chain-response constraint checker
    # Description:
    # The future constraining constraint chain_response(a, b) indicates that,
    # each time event a occurs in the trace, event b occurs immediately afterwards.
    # Event a activates the constraint.
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        num_fulfillments = 0
        num_pendings = 0

        for index, event in enumerate(self.traces):

            if event["concept:name"] == self.activities[0]:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    if index < len(self.traces) - 1:
                        if self.traces[index + 1]["concept:name"] == self.activities[1]:
                            locl = {'A': event, 'T': self.traces[index + 1], 'timedelta': timedelta, 'abs': abs,
                                    'float': float}
                            if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                                num_fulfillments += 1
                    else:
                        if not self.completed:
                            num_pendings = 1

        num_violations = num_activations - num_fulfillments - num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0 and num_pendings > 0:
            state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0 and num_pendings == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0 or (self.completed and num_pendings > 0):
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0 and num_pendings == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings,
                             num_activations=num_activations, state=state)


class MPPrecedence(TemplateConstraintChecker):
    # mp-precedence constraint checker
    # Description:
    # The history-based constraint precedence(a,b) indicates that event b occurs
    # only in the trace, if preceded by a. Event b activates the constraint.
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        num_fulfillments = 0
        Ts = []

        for event in self.traces:
            if event["concept:name"] == self.activities[0]:
                Ts.append(event)

            if event["concept:name"] == self.activities[1]:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    for T in Ts:
                        locl = {'A': event, 'T': T, 'timedelta': timedelta, 'abs': abs, 'float': float}
                        if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                            num_fulfillments += 1
                            break

        num_violations = num_activations - num_fulfillments
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=None,
                             num_activations=num_activations, state=state)


class MPAlternatePrecedence(TemplateConstraintChecker):
    # mp-alternate-precedence constraint checker
    # Description:
    # The history-based constraint alternatePrecedence(a, b) indicates that
    # each time event b occurs in the trace
    # it is preceded by event a and no other event b can recur in between.
    # Event b activates the constraint.
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        num_fulfillments = 0
        Ts = []

        for event in self.traces:
            if event["concept:name"] == self.activities[0]:
                Ts.append(event)

            if event["concept:name"] == self.activities[1]:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    num_activations += 1
                    for T in Ts:
                        locl = {'A': event, 'T': T, 'timedelta': timedelta, 'abs': abs, 'float': float}
                        if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                            num_fulfillments += 1
                            break
                    Ts = []
        num_violations = num_activations - num_fulfillments
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None
        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED
        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=None,
                             num_activations=num_activations, state=state)


class MPChainPrecedence(TemplateConstraintChecker):
    # mp-chain-precedence constraint checker
    # Description:
    # The history-based constraint chain_precedence(a, b) indicates that,
    # each time event b occurs in the trace, event a occurs immediately beforehand.
    # Event b activates the constraint.
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        num_fulfillments = 0

        for index, event in enumerate(self.traces):
            if event["concept:name"] == self.activities[1]:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    if index != 0 and self.traces[index - 1]["concept:name"] == self.activities[0]:
                        locl = {'A': event, 'T': self.traces[index - 1], 'timedelta': timedelta, 'abs': abs,
                                'float': float}
                        if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                            num_fulfillments += 1

        num_violations = num_activations - num_fulfillments
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=None,
                             num_activations=num_activations, state=state)


class MPNotRespondedExistence(TemplateConstraintChecker):
    # mp-not-responded-existence constraint checker
    # Description:
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        pendings = []
        num_fulfillments = 0
        num_violations = 0
        num_pendings = 0

        for event in self.traces:
            if event["concept:name"] == self.activities[0]:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pendings.append(event)

        for event in self.traces:
            if not pendings:
                break

            if event["concept:name"] == self.activities[1]:
                for A in reversed(pendings):
                    locl = {'A': A, 'T': event, 'timedelta': timedelta, 'abs': abs, 'float': float}
                    if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                        pendings.remove(A)
                        num_violations += 1

        if self.completed:
            num_fulfillments = len(pendings)
        else:
            num_pendings = len(pendings)

        num_activations = num_fulfillments + num_violations + num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings,
                             num_activations=num_activations, state=state)


class MPNotResponse(TemplateConstraintChecker):
    # mp-not-response constraint checker
    # Description:
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        pendings = []
        num_fulfillments = 0
        num_violations = 0
        num_pendings = 0

        for event in self.traces:
            if event["concept:name"] == self.activities[0]:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pendings.append(event)

            if pendings and event["concept:name"] == self.activities[1]:
                for A in reversed(pendings):
                    locl = {'A': A, 'T': event, 'timedelta': timedelta, 'abs': abs, 'float': float}
                    if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                        pendings.remove(A)
                        num_violations += 1

        if self.completed:
            num_fulfillments = len(pendings)
        else:
            num_pendings = len(pendings)

        num_activations = num_fulfillments + num_violations + num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings,
                             num_activations=num_activations, state=state)


class MPNotChainResponse(TemplateConstraintChecker):
    # mp-not-chain-response constraint checker
    # Description:
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])
        num_activations = 0
        num_violations = 0
        num_pendings = 0

        for index, event in enumerate(self.traces):

            if event["concept:name"] == self.activities[0]:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    if index < len(self.traces) - 1:
                        if self.traces[index + 1]["concept:name"] == self.activities[1]:
                            locl = {'A': event, 'T': self.traces[index + 1], 'timedelta': timedelta, 'abs': abs,
                                    'float': float}
                            if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                                num_violations += 1
                    else:
                        if not self.completed:
                            num_pendings = 1

        num_fulfillments = num_activations - num_violations - num_pendings
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations,
                             num_pendings=num_pendings,
                             num_activations=num_activations, state=state)


class MPNotPrecedence(TemplateConstraintChecker):
    # mp-not-precedence constraint checker
    # Description:
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        num_violations = 0
        Ts = []

        for event in self.traces:
            if event["concept:name"] == self.activities[0]:
                Ts.append(event)

            if event["concept:name"] == self.activities[1]:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    for T in Ts:
                        locl = {'A': event, 'T': T, 'timedelta': timedelta, 'abs': abs, 'float': float}
                        if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                            num_violations += 1
                            break

        num_fulfillments = num_activations - num_violations
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=None,
                             num_activations=num_activations, state=state)


class MPNotChainPrecedence(TemplateConstraintChecker):
    # mp-not-chain-precedence constraint checker
    # Description:
    def get_check_result(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])
        num_activations = 0
        num_violations = 0

        for index, event in enumerate(self.traces):

            if event["concept:name"] == self.activities[1]:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    if index != 0 and self.traces[index - 1]["concept:name"] == self.activities[0]:
                        locl = {'A': event, 'T': self.traces[index - 1], 'timedelta': timedelta, 'abs': abs,
                                'float': float}
                        if eval(correlation_rules, glob, locl) and eval(time_rule, glob, locl):
                            num_violations += 1

        num_fulfillments = num_activations - num_violations
        vacuous_satisfaction = self.rules["vacuous_satisfaction"]
        state = None

        if not vacuous_satisfaction and num_activations == 0:
            if self.completed:
                state = TraceState.VIOLATED
            else:
                state = TraceState.POSSIBLY_VIOLATED
        elif not self.completed and num_violations == 0:
            state = TraceState.POSSIBLY_SATISFIED
        elif num_violations > 0:
            state = TraceState.VIOLATED
        elif self.completed and num_violations == 0:
            state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=None,
                             num_activations=num_activations, state=state)


class TemplateCheckers:
    def __init__(self):
        self.choice = {}
        self.existence = {}

    def get_template(self, template: DeclareTemplate, traces: dict,
                     completed: bool, activities: [str], rules: dict) -> TemplateConstraintChecker:
        """
        We have the classes with each template constraint checker and we invoke them dynamically
        and they check the result on given parameters
        Parameters
        ----------
        template: name of the declared model template
        traces
        completed
        activities: activities of declare model template which should be checked. Can be one or two activities
        rules: dict. conditions of template and 'n' for unary templates which represents 'n' times

        Returns
        -------

        """
        template_checker_name = f"MP{template.templ_str.replace(' ', '')}"
        klass = globals()[template_checker_name]
        checker_instance: TemplateConstraintChecker = klass(traces, completed, activities, rules)
        return checker_instance

