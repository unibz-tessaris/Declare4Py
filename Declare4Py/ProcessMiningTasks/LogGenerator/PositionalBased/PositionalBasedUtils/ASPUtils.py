from abc import abstractmethod


class ASPFunctions:
    ASP_ACTIVITY = "activity({})"
    ASP_HAS_ATTRIBUTE = "has_attribute({}, {})"
    ASP_ATTRIBUTE_VALUE = "attribute_value({}, {})"
    ASP_ATTRIBUTE_RANGE = "attribute_value({}, {}..{})"

    ASP_CONSTRAINT_RULE = "rule"
    ASP_EVENT = {"function": "event({}, {})", "name": "event", "attr_count": 2}
    ASP_ASSIGNED_VALUE = {"function": "assigned_value({}, {}, {})", "name": "assigned_value", "attr_count": 3}

    ASP_FILE_EXTENSION = ".lp"

    ASP_ENCODING = ("pos(1..p).\n"
                    + "% p = number of events in each trace\n"
                    + "{event(A,P) : activity(A)} = 1 :- pos(P).\n"
                    + "{assigned_value(K,P,V) : attribute_value(K,V)} = 1 :- event(A,P), has_attribute(A,K).\n"
                    + ":- p != #count{P: event(_, P)}.\n"
                    + "#show event/2.\n"
                    + "#show assigned_value/3.\n")


class ASPEntity:

    @abstractmethod
    def to_asp(self, *kwargs) -> str:
        pass
