from abc import abstractmethod


class ASPFunctions:
    """
    ASPFunctions defines functions and constants for ASP
    """
    # Defines the ASP parsing functions
    ASP_ACTIVITY = "activity({})"
    ASP_HAS_ATTRIBUTE = "has_attribute({}, {})"
    ASP_ATTRIBUTE_VALUE = "attribute_value({}, {})"
    ASP_ATTRIBUTE_RANGE = "attribute_value({}, {}..{})"
    ASP_TIME_RANGE = "time({}..{})."

    # Defines the ASP constraint parsing rule
    ASP_CONSTRAINT_RULE = "rule"

    # Defines the event and attribute functions
    ASP_TIMED_EVENT = "timed_event({}, {}, {})"
    ASP_TIMED_EVENT_NAME = "timed_event"
    ASP_ASSIGNED_VALUE = "assigned_value({}, {}, {})"
    ASP_ASSIGNED_VALUE_NAME = "assigned_value"

    # File extension
    ASP_FILE_EXTENSION = ".lp"

    # ASP ENCODING OF THE POSITIONAL BASED PROBLEM
    # !!IMPORTANT!! P is declared on runtime by clingo
    # !!IMPORTANT!! The time function is declared by the Positional Based model
    ASP_ENCODING = ("% p = number of events in each trace\n"
                    + "pos(1..p).\n"
                    + "% Generating part\n"
                    + "{timed_event(A,P,T) : activity(A), time(T)} = 1 :- pos(P).\n"
                    + "{assigned_value(K,V,P) : attribute_value(K,V)} = 1 :- timed_event(A,P,_), has_attribute(A,K).\n"
                    + "% time event rule\n"
                    + ":- timed_event(_,P1,T1), timed_event(_,P1+1,T2), T1 >= T2.\n"
                    + "% traces length filter"
                    + ":- p != #count{P : timed_event(_, P, _)}.\n"
                    + "%returns\n"
                    + "#show timed_event/3.\n"
                    + "#show assigned_value/3.\n")


class ASPEntity:
    """
    An Abstract ASPEntity that has to define a to_asp method
    """
    @abstractmethod
    def to_asp(self, *kwargs) -> str:
        pass
