from abc import abstractmethod
from clingo.script import Script


class ASPFunctions:
    """
    ASPFunctions defines functions and constants for ASP
    """

    # Defines ASP function Names
    ASP_ACTIVITY = "activity"
    ASP_HAS_ATTRIBUTE = "has_attribute"
    ASP_ATTRIBUTE_VALUE = "attribute_value"
    ASP_TIME_RANGE = "time"
    ASP_CONSTRAINT_RULE = "rule"
    ASP_TIMED_EVENT = "timed_event"
    ASP_ASSIGNED_VALUE = "assigned_value"
    ASP_FIXED_EVENT = "fixed_event_rule"
    ASP_FIXED_TIME_EVENT = "fixed_timed_event_rule"
    ASP_FIXED_PAYLOAD = "fixed_payload_rule"

    ASP_PYTHON_SCRIPT_NAME = "clingo_python_range_script"
    # Define Python range script
    ASP_PYTHON_RANGE_SCRIPT = f"""
#script ({ASP_PYTHON_SCRIPT_NAME})
from clingo.symbol import Number
import random
def range(min_val, max_val):
      return Number(random.randint(min_val.number, max_val.number))
#end.
    """

    ASP_PYTHON_RANGE_FUNCTION_FORMAT = "@range({},{})"

    # Defines the ASP String Parsing functions
    ASP_ACTIVITY_FORMAT = "activity({})"
    ASP_HAS_ATTRIBUTE_FORMAT = "has_attribute({}, {})"
    ASP_ATTRIBUTE_VALUE_FORMAT = "attribute_value({}, {})"
    ASP_ATTRIBUTE_RANGE_FORMAT = "attribute_value({}, {}..{})"
    ASP_TIME_RANGE_FORMAT = "time({}..{})."
    ASP_TIME_EVENT_FORMAT = "timed_event({}, {}, {})"
    ASP_ASSIGNED_VALUE_FORMAT = "assigned_value({}, {}, {})"
    ASP_ASSIGNED_VALUE_RANGE_FORMAT = "assigned_value({}, " + ASP_PYTHON_RANGE_FUNCTION_FORMAT + ", {})"
    ASP_FIXED_EVENT_FORMAT = "fixed_event_rule :- timed_event({}, POS, _), POS != {}"
    ASP_FIXED_TIME_EVENT_FORMAT = "fixed_timed_event_rule :- timed_event({}, POS, TIME), POS != {}, TIME != {}"
    ASP_FIXED_PAYLOAD_FORMAT = "fixed_payload_rule :- assigned_value({}, ATTR_VALUE, _), ATTR_VALUE != {}"

    # File extension
    ASP_FILE_EXTENSION = ".lp"

    # ASP ENCODING OF THE POSITIONAL BASED PROBLEM
    # !!IMPORTANT!! P is declared on runtime by clingo
    # !!IMPORTANT!! The time function ASP_TIME_RANGE is declared by the Positional Based model during the ASP construction
    ASP_ENCODING = """
% p = number of events in each trace
pos(1..p).
% Generating part
{timed_event(A,P,T) : activity(A), time(T)} = 1 :- pos(P).
{assigned_value(K,V,P) : attribute_value(K,V)} = 1 :- timed_event(A,P,_), has_attribute(A,K).
% time event rule
:- timed_event(_,P1,T1), timed_event(_,P1+1,T2), T1 >= T2.
% traces length filter
:- p != #count{P : timed_event(_, P, _)}.
%returns
#show timed_event/3.
#show assigned_value/3.
    """


class ASPClingoScript(Script):
    def execute(self, location, code):
        exec(code, self.__dict__, self.__dict__)

    def call(self, location, name, arguments):
        return getattr(self, name)(*arguments)

    def callable(self, name):
        return name in self.__dict__ and callable(self.__dict__[name])


class ASPEntity:
    """
    An Abstract ASPEntity that has to define a to_asp method
    """

    @abstractmethod
    def to_asp(self, *kwargs) -> str:
        pass
