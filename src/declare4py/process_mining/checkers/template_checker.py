from __future__ import annotations

from src.declare4py.models.decl_model import DeclareParserUtility, TraceState
from datetime import timedelta

from src.declare4py.process_mining.model_checking.checker_result import CheckerResult


glob = {'__builtins__': None}


class TemplateConstraintChecker:
    def __init__(self):
        self.dpu = DeclareParserUtility()


class ChoiceTemplatesConstraintChecker(TemplateConstraintChecker):
    
    def __init__(self, traces: dict | list, completed: bool, event1: str, event2: str, rules: dict):
        super().__init__()
        self.traces = traces
        self.completed = completed
        self.event1 = event1
        self.event2 = event2
        self.rules = rules
    
    # mp-choice constraint checker
    def mp_choice(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])
        a_or_b_occurs = False
        for A in self.traces:
            if A["concept:name"] == self.event1 or A["concept:name"] == self.event2:
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

    # mp-exclusive-choice constraint checker
    # Description:
    def mp_exclusive_choice(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])
        a_occurs = False
        b_occurs = False
        for A in self.traces:
            locl = {'A': A, 'T': self.traces[0], 'timedelta': timedelta, 'abs': abs, 'float': float}
            if not a_occurs and A["concept:name"] == self.event1:
                if eval(activation_rules, glob, locl) and eval(time_rule, glob, locl):
                    a_occurs = True
            if not b_occurs and A["concept:name"] == self.event2:
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


class ExistenceTemplatesConstraintChecker(TemplateConstraintChecker):

    def __init__(self, traces: dict, completed: bool, event1: str, rules: dict):
        super().__init__()
        self.traces = traces
        self.completed = completed
        self.event1 = event1
        self.rules = rules

    # mp-existence constraint checker
    # Description:
    # The future constraining constraint existence(n, a) indicates that
    # event a must occur at least n-times in the trace.
    def mp_existence(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        for A in self.traces:
            if A["concept:name"] == self.event1:
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

    # mp-absence constraint checker
    # Description:
    # The future constraining constraint absence(n + 1, a) indicates that
    # event a may occur at most n − times in the trace.
    def mp_absence(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        for A in self.traces:
            if A["concept:name"] == self.event1:
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

    # mp-init constraint checker
    # Description:
    # The future constraining constraint init(e) indicates that
    # event e is the first event that occurs in the trace.
    def mp_init(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])

        state = TraceState.VIOLATED
        if self.traces[0]["concept:name"] == self.event1:
            locl = {'A': self.traces[0]}
            if eval(activation_rules, glob, locl):
                state = TraceState.SATISFIED

        return CheckerResult(num_fulfillments=None, num_violations=None, num_pendings=None, num_activations=None,
                             state=state)

    # mp-exactly constraint checker
    # Description:
    def mp_exactly(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])
        num_activations = 0
        for A in self.traces:
            if A["concept:name"] == self.event1:
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


class RelationTemplatesConstraintChecker(TemplateConstraintChecker):

    def __init__(self, traces: dict, completed: bool, event1: str, event2: str, rules: dict):
        super().__init__()
        self.traces = traces
        self.completed = completed
        self.event1 = event1
        self.event2 = event2
        self.rules = rules

    # mp-responded-existence constraint checker
    # Description:
    # The future constraining and history-based constraint
    # respondedExistence(a, b) indicates that, if event a occurs in the trace
    # then event b occurs in the trace as well.
    # Event a activates the constraint.
    def mp_responded_existence(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        pendings = []
        num_fulfillments = 0
        num_violations = 0
        num_pendings = 0

        for event in self.traces:
            if event["concept:name"] == self.event1:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pendings.append(event)

        for event in self.traces:
            if not pendings:
                break

            if event["concept:name"] == self.event2:
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

    # mp-response constraint checker
    # Description:
    # The future constraining constraint response(a, b) indicates that
    # if event a occurs in the trace, then event b occurs after a.
    # Event a activates the constraint.
    def mp_response(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        pendings = []
        num_fulfillments = 0
        num_violations = 0
        num_pendings = 0

        for event in self.traces:
            if event["concept:name"] == self.event1:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pendings.append(event)

            if pendings and event["concept:name"] == self.event2:
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

    # mp-alternate-response constraint checker
    # Description:
    # The future constraining constraint alternateResponse(a, b) indicates that
    # each time event a occurs in the trace then event b occurs afterwards
    # before event a recurs.
    # Event a activates the constraint.
    def mp_alternate_response(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        pending = None
        num_activations = 0
        num_fulfillments = 0
        num_pendings = 0

        for event in self.traces:
            if event["concept:name"] == self.event1:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pending = event
                    num_activations += 1

            if event["concept:name"] == self.event2 and pending is not None:
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

    # mp-chain-response constraint checker
    # Description:
    # The future constraining constraint chain_response(a, b) indicates that,
    # each time event a occurs in the trace, event b occurs immediately afterwards.
    # Event a activates the constraint.
    def mp_chain_response(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        num_fulfillments = 0
        num_pendings = 0

        for index, event in enumerate(self.traces):

            if event["concept:name"] == self.event1:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    if index < len(self.traces) - 1:
                        if self.traces[index + 1]["concept:name"] == self.event2:
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

    # mp-precedence constraint checker
    # Description:
    # The history-based constraint precedence(a,b) indicates that event b occurs
    # only in the trace, if preceded by a. Event b activates the constraint.
    def mp_precedence(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        num_fulfillments = 0
        Ts = []

        for event in self.traces:
            if event["concept:name"] == self.event1:
                Ts.append(event)

            if event["concept:name"] == self.event2:
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

    # mp-alternate-precedence constraint checker
    # Description:
    # The history-based constraint alternatePrecedence(a, b) indicates that
    # each time event b occurs in the trace
    # it is preceded by event a and no other event b can recur in between.
    # Event b activates the constraint.
    def mp_alternate_precedence(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        num_fulfillments = 0
        Ts = []

        for event in self.traces:
            if event["concept:name"] == self.event1:
                Ts.append(event)

            if event["concept:name"] == self.event2:
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

    # mp-chain-precedence constraint checker
    # Description:
    # The history-based constraint chain_precedence(a, b) indicates that,
    # each time event b occurs in the trace, event a occurs immediately beforehand.
    # Event b activates the constraint.
    def mp_chain_precedence(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        num_fulfillments = 0

        for index, event in enumerate(self.traces):
            if event["concept:name"] == self.event2:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    if index != 0 and self.traces[index - 1]["concept:name"] == self.event1:
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


class NegativeRelationTemplatesConstraintChecker(TemplateConstraintChecker):

    def __init__(self, traces: dict, completed: bool, event1: str, event2: str, rules: dict):
        super().__init__()
        self.traces = traces
        self.completed = completed
        self.event1 = event1
        self.event2 = event2
        self.rules = rules

    # mp-not-responded-existence constraint checker
    # Description:
    def mp_not_responded_existence(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        pendings = []
        num_fulfillments = 0
        num_violations = 0
        num_pendings = 0

        for event in self.traces:
            if event["concept:name"] == self.event1:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pendings.append(event)

        for event in self.traces:
            if not pendings:
                break

            if event["concept:name"] == self.event2:
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

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=num_pendings,
                             num_activations=num_activations, state=state)

    # mp-not-response constraint checker
    # Description:
    def mp_not_response(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        pendings = []
        num_fulfillments = 0
        num_violations = 0
        num_pendings = 0

        for event in self.traces:
            if event["concept:name"] == self.event1:
                locl = {'A': event}
                if eval(activation_rules, glob, locl):
                    pendings.append(event)

            if pendings and event["concept:name"] == self.event2:
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

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=num_pendings,
                             num_activations=num_activations, state=state)

    # mp-not-chain-response constraint checker
    # Description:
    def mp_not_chain_response(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        num_violations = 0
        num_pendings = 0

        for index, event in enumerate(self.traces):

            if event["concept:name"] == self.event1:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    if index < len(self.traces) - 1:
                        if self.traces[index+1]["concept:name"] == self.event2:
                            locl = {'A': event, 'T': self.traces[index+1], 'timedelta': timedelta, 'abs': abs, 'float': float}
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

        return CheckerResult(num_fulfillments=num_fulfillments, num_violations=num_violations, num_pendings=num_pendings,
                             num_activations=num_activations, state=state)

    # mp-not-precedence constraint checker
    # Description:
    def mp_not_precedence(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        num_violations = 0
        Ts = []

        for event in self.traces:
            if event["concept:name"] == self.event1:
                Ts.append(event)

            if event["concept:name"] == self.event2:
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

    # mp-not-chain-precedence constraint checker
    # Description:
    def mp_not_chain_precedence(self):
        activation_rules = self.dpu.parse_data_cond(self.rules["activation"])
        correlation_rules = self.dpu.parse_data_cond(self.rules["correlation"])
        time_rule = self.dpu.parse_time_cond(self.rules["time"])

        num_activations = 0
        num_violations = 0

        for index, event in enumerate(self.traces):

            if event["concept:name"] == self.event2:
                locl = {'A': event}

                if eval(activation_rules, glob, locl):
                    num_activations += 1

                    if index != 0 and self.traces[index-1]["concept:name"] == self.event1:
                        locl = {'A': event, 'T': self.traces[index-1], 'timedelta': timedelta, 'abs': abs, 'float': float}
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

# class Template_Checkers:
#     def __init__(self):
#         self.choice =
#         self.existence = {}
#
#     def choice_template(self, name, traces: int, completed: bool):

        
