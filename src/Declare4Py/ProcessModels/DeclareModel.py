from __future__ import annotations

import base64
import copy
import re
import typing
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Union

from src.Declare4Py.ProcessModels.LTLModel import LTLModel
from src.Declare4Py.Utils.custom_utility_dict import CustomUtilityDict

"""
Class which holds most of the Constraint Template List with some information about templates themself.
"""


class DeclareModelTemplate(str, Enum):

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__) + 1
        obj = str.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, templ_str: str, is_binary: bool, is_negative: bool, supports_cardinality: bool,
                 both_activation_condition: bool = False, is_shortcut: bool = False,
                 reverseActivationTarget: bool = False):
        """

        Parameters
        ----------
        templ_str: template name
        is_binary: whether template supports 2 events
        is_negative: whether the template is negative
        supports_cardinality: whether template supports cardinality, i.e Existence template is unary
         but you can specify a number how many times Existence should occur. "Existence4[A]|||" where 4 times at least occur.
        both_activation_condition: some templates doesn't have target condition, instead both conditions are activation conditions.
        reverseActivationTarget: some C.T have reverse activation and target condition
        """
        self.templ_str = templ_str
        self.is_binary = is_binary
        self.is_negative = is_negative
        self.supports_cardinality = supports_cardinality
        self.both_activation_condition = both_activation_condition
        self.is_shortcut = is_shortcut
        self.reverseActivationTarget = reverseActivationTarget

    EXISTENCE = "Existence", False, False, True, False, False, False
    ABSENCE = "Absence", False, False, True, False, False, False
    EXACTLY = "Exactly", False, False, True, False, False, False
    INIT = "Init", False, False, False, False, False, False
    END = "End", False, False, False, False, False, False

    CHOICE = "Choice", True, False, False, True, False, False
    EXCLUSIVE_CHOICE = "Exclusive Choice", True, False, False, True, False, False

    RESPONDED_EXISTENCE = "Responded Existence", True, False, False, False, False, False
    RESPONSE = "Response", True, False, False, False, False, False
    ALTERNATE_RESPONSE = "Alternate Response", True, False, False, False, False, False
    CHAIN_RESPONSE = "Chain Response", True, False, False, False, False, False
    PRECEDENCE = "Precedence", True, False, False, False, False, True
    ALTERNATE_PRECEDENCE = "Alternate Precedence", True, False, False, False, False, True
    CHAIN_PRECEDENCE = "Chain Precedence", True, False, False, False, False, True

    # response(A, b) and precedence(a, b) = succession(a, b)
    # responded_existence(A, b) and responded_existence(b, a) = coexistence(a, b)
    # TODO implementare i checker
    SUCCESSION = "Succession", True, False, False, True, True, False
    ALTERNATE_SUCCESSION = "Alternate Succession", True, False, False, True, True, False
    CO_EXISTENCE = "Co-Existence", True, False, False, True, True, False
    CHAIN_SUCCESSION = "Chain Succession", True, False, False, True, True, False
    NOT_CHAIN_SUCCESSION = "Not Chain Succession", True, True, False, True, True, False
    NOT_CO_EXISTENCE = "Not Co-Existence", True, True, False, True, True, False
    NOT_SUCCESSION = "Not Succession", True, True, False, True, True, False

    NOT_RESPONDED_EXISTENCE = "Not Responded Existence", True, True, False, False, False, False
    NOT_RESPONSE = "Not Response", True, True, False, False, False, False
    NOT_PRECEDENCE = "Not Precedence", True, True, False, False, False, True
    NOT_CHAIN_RESPONSE = "Not Chain Response", True, True, False, False, False, False
    NOT_CHAIN_PRECEDENCE = "Not Chain Precedence", True, True, False, False, False, True

    @classmethod
    def get_template_from_string(cls, template_str):
        template_str = template_str.replace(" ", "")
        template_str = template_str.replace("-", "")
        template_str = template_str.lower()
        return next(filter(lambda t: t.templ_str.replace(" ", "").replace("-", "").lower() == template_str,
                           DeclareModelTemplate), None)

    @classmethod
    def get_unary_templates(cls):
        return tuple(filter(lambda t: not t.is_binary, DeclareModelTemplate))

    @classmethod
    def get_binary_templates(cls):
        return tuple(filter(lambda t: t.is_binary, DeclareModelTemplate))

    @classmethod
    def get_positive_templates(cls):
        return tuple(filter(lambda t: not t.is_negative, DeclareModelTemplate))

    @classmethod
    def get_negative_templates(cls):
        return tuple(filter(lambda t: t.is_negative, DeclareModelTemplate))

    @classmethod
    def get_shortcut_templates(cls):
        return tuple(filter(lambda t: t.is_shortcut, DeclareModelTemplate))

    @classmethod
    def are_conditions_reversed_applied(cls):
        return tuple(filter(lambda t: t.reverseActivationTarget, DeclareModelTemplate))

    @classmethod
    def get_binary_not_shortcut_templates(cls):
        return tuple(filter(lambda t: t.is_binary and not t.is_shortcut, DeclareModelTemplate))

    def __str__(self):
        return "<Template." + str(self.templ_str) + ": " + str(self.value) + " >"

    def __repr__(self):
        return "\"" + str(self.__str__()) + "\""


"""
Class for backward-compatibility for some older code which contains two methods for declare models.
"""


class DeclareModelConditionParserUtility:

    def __init__(self):
        super().__init__()

    def parse_data_cond(self, cond: str):  # TODO: could be improved using recursion ?
        try:
            cond = cond.strip()
            if cond == "":
                return "True"
            # List containing translations from decl format to python
            py_cond, fill_enum_set = ("", False)
            while cond:
                if cond.startswith("(") or cond.startswith(")"):
                    py_cond = py_cond + " " + cond[0]
                    cond = cond[1:].lstrip()
                    fill_enum_set = py_cond.endswith(" in (")
                else:
                    if not fill_enum_set:
                        next_word = re.split(r'[\s()]+', cond)[0]
                        cond = cond[len(next_word):].lstrip()
                        if re.match(r'^[AaTt]\.', next_word):  # A. conditions
                            py_cond = py_cond + " " + '"' + next_word[2:] + '" in ' + next_word[0] \
                                      + " and " + next_word[0] + '["' + next_word[2:] + '"]'
                        elif next_word.lower() == "is":
                            if cond.lower().startswith("not"):
                                cond = cond[3:].lstrip()
                                py_cond = py_cond + " !="
                            else:
                                py_cond = py_cond + " =="
                            tmp = []
                            while cond and not (cond.startswith(')') or cond.lower().startswith('and')
                                                or cond.lower().startswith('or')):
                                w = re.split(r'[\s()]+', cond)[0]
                                cond = cond[len(w):].lstrip()
                                tmp.append(w)
                            attr = " ".join(tmp)
                            py_cond += ' "' + attr + '"'
                        elif next_word == "=":
                            py_cond = py_cond + " =="
                        elif next_word.lower() == "and" or next_word.lower() == "or":
                            py_cond = py_cond + " " + next_word.lower()
                        elif next_word.lower() == "same":
                            tmp = []
                            while cond and not (cond.startswith(')') or cond.lower().startswith('and')
                                                or cond.lower().startswith('or')):
                                w = re.split(r'[\s()]+', cond)[0]
                                cond = cond[len(w):].lstrip()
                                tmp.append(w)
                            attr = " ".join(tmp)
                            py_cond = py_cond + " " + attr + " in A and " + attr + " in T " \
                                      + 'and A["' + attr + '"] == T["' + attr + '"]'
                        elif next_word.lower() == "different":
                            tmp = []
                            while cond and not (cond.startswith(')') or cond.lower().startswith('and')
                                                or cond.lower().startswith('or')):
                                w = re.split(r'[\s()]+', cond)[0]
                                cond = cond[len(w):].lstrip()
                                tmp.append(w)
                            attr = " ".join(tmp)
                            py_cond = py_cond + " " + attr + " in A and " + attr + " in T " \
                                      + 'and A["' + attr + '"] != T["' + attr + '"]'
                        elif next_word.lower() == "true":
                            py_cond = py_cond + " True"
                        elif next_word.lower() == "false":
                            py_cond = py_cond + " False"
                        else:
                            py_cond = py_cond + " " + next_word
                    else:
                        end_idx = cond.find(')')
                        enum_set = re.split(r',\s+', cond[:end_idx])
                        enum_set = [x.strip() for x in enum_set]

                        py_cond = py_cond + ' "' + '", "'.join(enum_set) + '"'
                        cond = cond[end_idx:].lstrip()

            return py_cond.strip()
        except Exception:
            raise SyntaxError

    def parse_time_cond(self, condition):
        try:
            if condition.strip() == "":
                condition = "True"
                return condition
            if re.split(r'\s*,\s*', condition.strip())[2].lower() == "s":
                time_measure = "seconds"
            elif re.split(r'\s*,\s*', condition.strip())[2].lower() == "m":
                time_measure = "minutes"
            elif re.split(r'\s*,\s*', condition.strip())[2].lower() == "h":
                time_measure = "hours"
            elif re.split(r'\s*,\s*', condition.strip())[2].lower() == "d":
                time_measure = "days"
            else:
                time_measure = None

            min_td = "timedelta(" + time_measure + "=float(" + str(condition.split(",")[0]) + "))"
            max_td = "timedelta(" + time_measure + "=float(" + str(condition.split(",")[1]) + "))"

            condition = min_td + ' <= abs(A["time:timestamp"] - T["time:timestamp"]) <= ' + max_td
            return condition

        except Exception:
            raise SyntaxError


"""
An Enum class that specifies types of attributes of the Declare model
"""


class DeclareModelAttributeType(str, Enum):
    INTEGER = "integer"
    FLOAT = "float"
    INTEGER_RANGE = "integer_range"
    FLOAT_RANGE = "float_range"
    ENUMERATION = "enumeration"

    def __str__(self):
        return self.value

    def __repr__(self):
        return "\"" + self.__str__() + "\""


"""

A data model contains the information about activity such as name of that activity and its attributes.

"""


class DeclareModelCoderSingletonMeta(type):
    """
        DeclareModelCoderSingletonMeta is a custom metaclass that implements the singleton pattern in Python.
        A metaclass is a special kind of class that defines the behavior of other classes. In the case of DeclareModelCoderSingletonMeta,
        it implements the __call__ method, which is called whenever an instance of the class is created.
        The __call__ method checks if an instance of the class has already been created, and if not, creates a new
        instance and stores it in a class-level dictionary _instances. If an instance has already been created,
        it simply returns the existing instance.
        To use the DeclareModelCoderSingletonMeta class, specify it as the metaclass for the class you want to make a singleton. For example:
            class Singleton(metaclass=DeclareModelCoderSingletonMeta):
                pass
        Now, every time you create an instance of the Singleton class, you will always get the same instance,
         regardless of how many times you create it. This ensures that the singleton pattern is maintained.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
         This method is called whenever an instance of the class is created.
         It checks if an instance of the class has already been created, and if not,
         creates a new instance and stores it in a class-level dictionary _instances.
         If an instance has already been created, it simply returns the existing instance.
       """
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class DeclareModelCoderSingleton(metaclass=DeclareModelCoderSingletonMeta):
    def __init__(self):
        self.encoded_values: dict[str, str] = {}
        self.event_nm_idx: int = 0
        self.event_vl_idx: int = 0
        self.attr_nm_idx: int = 0
        self.attr_vl_idx: int = 0
        self.other_counter: int = 0

    def encode_value(self, s: str, val_type: typing.Literal["event_name", "event_value", "attr_name", "attr_val"]) -> str:
        if not isinstance(s, str):
            return s
        if s.isnumeric():
            return s
        s = s.strip()
        if s in self.encoded_values:
            return s
        ns = ""
        if val_type == "event_name":
            ns = f"evt_name_{self.event_nm_idx}"
            self.event_nm_idx = self.event_nm_idx + 1
        elif val_type == "event_value":
            ns = f"evt_val_{self.event_vl_idx}"
            self.event_vl_idx = self.event_vl_idx + 1
        elif val_type == "attr_name":
            ns = f"attr_name_{self.attr_nm_idx}"
            self.attr_nm_idx = self.attr_nm_idx + 1
        elif val_type == "attr_val":
            ns = f"attr_value_{self.attr_vl_idx}"
            self.attr_vl_idx = self.attr_vl_idx + 1
        else:
            ns = f"other_{self.other_counter}"
            self.other_counter = self.other_counter + 1
        self.encoded_values[ns] = s
        return ns

    def decode_value(self, s: str) -> str:
        if not isinstance(s, str):
            return s
        if s.isnumeric():
            return s
        s = s.strip()

        for key in self.encoded_values:
            enc_str = self.encoded_values[key]
            if enc_str == s:
                return key
        raise ValueError(f"Unable to decode value {s}.")


class DeclareModelToken(ABC):

    def __init__(self, token: str, token_type: typing.Literal["event_name", "event_value", "attr_name", "attr_val"]):
        self.encoder = DeclareModelCoderSingleton()
        self.value = token
        self.token_type: typing.Literal["event_name", "event_value", "attr_name", "attr_val"] = token_type

    def get_name(self):
        return self.value

    def set_name(self, value):
        self.value = value

    def get_encoded_name(self):
        return self.encoder.encode_value(self.get_name(), self.token_type)

    def to_dict(self):
        return {
            "name": self.get_name(),
            "encoded_name": self.get_encoded_name(),
        }


class DeclareModelEventName(DeclareModelToken):
    def __init__(self, name: str):
        super().__init__(name, "event_value")


class DeclareModelEventType(DeclareModelToken):
    def __init__(self, name: str):
        super().__init__(name, "event_name")


class DeclareModelEvent:
    def __init__(self, name: str, event_type: str):
        """

        Parameters
        ----------
        name Event name is the name of event. i.e activity(actName). Activity is event type and actName is event name.
        event_type Event type is the type of event. i.e activity(actName). Activity is event type and actName is event name.

        """
        self.event_name = DeclareModelEventName(name)
        self.event_type = DeclareModelEventType(event_type)
        self.attributes: dict[str, DeclareModelAttr] = {}

    def set_bound_attributes(self, attrs_list: [DeclareModelAttr]):
        self.attributes = {}
        for i in attrs_list:
            attrModel: DeclareModelAttr = i
            self.attributes[attrModel.attr_name] = attrModel
            j = j + 1

    def set_bound_attribute(self, attr: DeclareModelAttr):
        self.attributes[attr.get_name()] = attr

    def get_event_name(self):
        return self.event_name.get_name()

    def to_dict(self):
        return {
            "event_type": self.event_type.get_name(),
            "event_encoded_type": self.event_type.get_encoded_name(),
            "event_name": self.event_name.get_name(),
            "event_encoded_name": self.event_name.get_encoded_name(),
            "bound_attributes_resources": {key: value.to_dict() for key, value in self.attributes.items()},
        }


class DeclareModelAttrName(DeclareModelToken, ABC):
    def __init__(self, name: str):
        super().__init__(name, "attr_name")


class DeclareModelAttrValue(DeclareModelToken, ABC):
    """
    Declare value can be of 3 types: enumeration, float range, int range
    """
    def __init__(self, value: str, value_type: DeclareModelAttributeType):
        super().__init__(value, "attr_val")
        self.value: [DeclareModelToken] | [float] | [int] = None
        self.value_original: [str] | [float] | [int] = value
        self.attribute_value_type = value_type
        self.precision: int = 1
        self.parse_attr_value()

    def parse_attr_value(self):
        # pattern = re.compile(r"( \d+.?\d*)( and )?(\d+.?\d*)")
        if self.value_original is None:
            return
        pattern = re.compile(r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)")
        if self.attribute_value_type == DeclareModelAttributeType.FLOAT_RANGE:
            matches = pattern.findall(self.value_original)
            self.value = [float(matches[0]), float(matches[1])]
            self.precision = self.get_float_biggest_precision(self.value[0], self.value[1])
        elif self.attribute_value_type == DeclareModelAttributeType.INTEGER_RANGE:
            self.precision = 1
            match = pattern.findall(self.value_original)  # Extract the numeric
            self.value = [int(match[0]), int(match[1])]
        elif self.attribute_value_type == DeclareModelAttributeType.ENUMERATION:
            self.value = [DeclareModelToken(v.strip(), "attr_val") for v in self.value_original.split(',')]
        else:
            raise ValueError("Unable to parse the attribute value. Attribute values can be Enumeration separated"
                             " by ',', or integer range, or float range")

    def get_float_biggest_precision(self, v1: float, v2: float) -> int:
        """ Get the biggest float precision in order to scale up a number """
        decimal_len_list = []
        precision = 0
        frm = str(v1).split(".")  # 10.587
        til = str(v2).split(".")  # 3.587
        if len(frm) > 1:
            precision = len(frm[1])  # frm[1] = 587 and length would be 3
        if len(til) > 1:
            precision = max(len(til[1]), precision)
        decimal_len_list.append(precision)
        if len(decimal_len_list) == 0:
            return 0
        return max(decimal_len_list)

    def get_encoded_values(self):
        values = self.get_precisioned_value()
        if self.attribute_value_type != DeclareModelAttributeType.ENUMERATION:
            return values

    def get_precisioned_value(self) -> [DeclareModelToken] | [int]:
        """If attribute is of float type, it will return an integer value with scaled up. """
        if self.attribute_value_type == DeclareModelAttributeType.FLOAT_RANGE:
            frm = int((10 ** self.precision) * self.value[0])
            to = int((10 ** self.precision) * self.value[1])
            return [frm, to]
        # if self.attribute_value_type == DeclareModelAttributeType.INTEGER_RANGE:
        #     return [self.value[0], self.value[1]]
        # decoded_enum_values = []
        return self.value

    def to_dict(self):
        mr = []
        values = self.get_precisioned_value()
        if values is not None and len(values) > 0:
            for v in values:
                if isinstance(v, int):
                    mr.append(v)
                else:
                    mr.append(v.to_dict())
        return {
            "attribute_value_type": self.attribute_value_type,
            "precision": self.precision,
            "value_original": self.value_original,
            "value": mr,
        }

class DeclareModelAttr:
    """Attr can be imagined as resources shared between events"""
    def __init__(self, attr: str, value: str = None):
        self.attr_name = DeclareModelAttrName(attr)
        if value is not None:
            self.value_type = self.detect_declare_attr_value_type(value)
            self.attr_value = DeclareModelAttrValue(value, self.value_type)
        else:
            self.attr_value: DeclareModelAttrValue = None
        self.attached_events: dict[str, DeclareModelEvent] = {}

    def get_name(self) -> str:
        return self.attr_name.get_name()

    def set_attached_events(self, ev_list: [DeclareModelEvent]):
        self.attached_events = []
        for ev in ev_list:
            self.set_attached_event(ev)
        # self.attached_events = ev_list

    def set_attached_event(self, event: DeclareModelEvent):
        ev_nm = event.get_event_name()
        for i in self.attached_events:
            if i == ev_nm:
                # event already exists. or we can raise a warning that indicates
                # two or more times to same attributes to same event are declared
                return
        self.attached_events[event.get_event_name()] = event
        event.set_bound_attribute(self)

    def detect_declare_attr_value_type(self, value: str) -> DeclareModelAttributeType:
        """
        Detect the type of value assigned to an attribute assigned
        Parameters
        ----------
        value: assigned value
        Returns DeclareModelAttributeType
        -------
        """
        value = value.strip()
        v2 = value.replace("  ", "")
        if re.search(r"^[+-]?\d+$", value, re.MULTILINE):
            return DeclareModelAttributeType.INTEGER
        elif re.search(r"^[+-]?\d+(?:\.\d+)?$", value, re.MULTILINE):
            return DeclareModelAttributeType.FLOAT
        elif v2 and v2.lower().startswith("integer between"):
            # ^integer * between *[+-]?\d+(?:\.\d+)? *and [+-]?\d+(?:\.\d+)?$
            return DeclareModelAttributeType.INTEGER_RANGE
        elif v2 and v2.lower().startswith("float between"):
            # ^float * between *[+-]?\d+(?:\.\d+)? *and [+-]?\d+(?:\.\d+)?$
            return DeclareModelAttributeType.FLOAT_RANGE
        else:
            return DeclareModelAttributeType.ENUMERATION

    def set_attr_value(self, value: str):
        self.value_type = self.detect_declare_attr_value_type(value)
        self.attr_value = DeclareModelAttrValue(value, self.value_type)

    def to_dict(self):
        return {
            "attribute_name": self.attr_name.get_name(),
            "attribute_encoded_name": self.attr_name.get_encoded_name(),
            "attr_value": self.attr_value.to_dict(),
        }


class DeclareModelConstraintTemplate:
    def __init__(self, template_line: str, template_number_id: int):
        self.line = template_line
        self.events_activities: [DeclareModelEvent] = []
        self.cardinality: int = 0  # cardinality is only for unary and 0 means template doesn't have
        self.template: DeclareModelTemplate = None
        self.template_index: int = template_number_id
        self.violate: bool = False
        self._conditions_line: str = None
        self._conditions: [str] = []  # conditions: activation, target, time

    def get_template_name(self):
        if self.template.supports_cardinality and self.cardinality > 0:
            return self.template.templ_str + str(self.cardinality)
        return self.template.templ_str

    def get_conditions(self):
        """
        Returns parsed conditions: active, target, and time condition if there are
        """
        return self.get_activation_condition(), self.get_target_condition(), self.get_time_condition()

    def parse_constraint_conditions(self):
        compiler = re.compile(r"^(.*)\[(.*)\]\s*(.*)$")
        al = compiler.fullmatch(self.line)
        if len(al.group()) >= 3:
            conditions = al.group(3).strip()
            if len(conditions) == 0:
                return
            if len(conditions) > 1 and not conditions.startswith("|"):
                raise SyntaxError(f"Unable to parse template {self.template.templ_str}'s conditions."
                                  f" Conditions should start with \"|\"")
            self._conditions_line = conditions
            conditions = conditions.strip("|")
            conds_list = conditions.split("|")
            self._conditions = [cl.strip() for cl in conds_list]
            """ Some declare models use T.attribute for target conditions reference and some uses B.attributes"""
            if self.template.is_binary and len(conds_list) < 2:
                raise ValueError(f"Unable to parse the conditions of binary constraint template")
            if len(conds_list) > 3:
                raise ValueError(f"Unable to parse the line due to the exceeds conditions (> 3)")

    def get_activation_condition(self):
        """ Returns active conditions """
        if self._conditions and self.template.reverseActivationTarget:  # if template has reverse conditions, so we xyz
            if len(self._conditions) > 1:
                c = self._conditions[1]
                return c
        else:
            if len(self._conditions) > 0:
                c = self._conditions[0]
                return c
                # return c if len(c) > 1 else None
        return None

    def get_target_condition(self):
        """ Returns target conditions """
        cond = ""
        if self._conditions and self.template.reverseActivationTarget:
            if len(self._conditions) > 0:
                cond = self._conditions[0]
        else:
            if len(self._conditions) > 1:
                cond = self._conditions[1]
        time_int = r"^[\d.]+,?([\d.]+)?[,]?(s|m|d|h)$"
        is_matched = re.search(time_int, cond, re.IGNORECASE)
        if is_matched:
            return None
        return cond if len(cond) > 0 else None

    def get_time_condition(self):
        """ Returns time condition """
        if self.contains_interval_condition():
            c = self._conditions[2]
            return c if len(c) > 0 else None
            # return self.condition[2]
        return None

    def contains_interval_condition(self) -> bool:
        """ Return a boolean value if a constraint template contains a time condition """
        if self._conditions is None:
            return False
        len_ = len(self._conditions)
        if len_ != 3:
            return False
        return True

    def to_dict(self):
        return {
            "template": self.get_template_name(),
            "index": self.template_index,
            "cardinality": self.cardinality,
            "condition_line": self._conditions_line,
            "activation_condition": self.get_activation_condition(),
            "target_condition": self.get_target_condition(),
            "time_condition": self.get_time_condition(),
            "violate": self.violate,
            "events_involved": [e.to_dict() for e in self.events_activities],
        }


"""
A data model class which contains information about a parsed template constraint.
"""

# class DeclareModelTemplateDataModel(CustomUtilityDict):
#     # TODO: create getter and setters for properties and make properties
#     #  private, so the logic of providing correct condition and activity
#     #  based on correct constraint templates. I.E Existence and Absence case
#     #  where Existence1 and Absence1 doesn't exist but other unary does.
#     #  one more case is for the reverseConditions of some constraints
#
#     def __init__(self):
#         super().__init__()
#         self.template: Union[DeclareModelTemplate, None] = None
#         self.activities: Union[str, None] = None
#         self.condition: Union[List[str], None] = None
#         self.template_name: Union[str, None] = None
#         self.template_line: Union[str, None] = None  # Constraint lines
#         self.condition_line: Union[str, None] = None  # |A.grade < 2  | T.mark > 2|1,5,s
#         self.violate: bool = False
#         self.template_index_id: int = None
#
#     def get_conditions(self):
#         """
#         Returns parsed conditions: active, target, and time condition if there are
#         """
#         return self.get_active_condition(), self.get_target_condition(), self.get_time_condition()
#
#     def get_active_condition(self):
#         """ Returns active conditions """
#         if self.template.reverseActivationTarget:  # if template has reverse conditions, so we xyz
#             if len(self.condition) > 1:
#                 c = self.condition[1]
#                 return c
#         else:
#             if len(self.condition) > 0:
#                 c = self.condition[0]
#                 return c
#                 # return c if len(c) > 1 else None
#         return None
#
#     def get_target_condition(self):
#         """ Returns target conditions """
#         cond = ""
#         if self.template.reverseActivationTarget:
#             if len(self.condition) > 0:
#                 cond = self.condition[0]
#         else:
#             if len(self.condition) > 1:
#                 cond = self.condition[1]
#         time_int = r"^[\d.]+,?([\d.]+)?[,]?(s|m|d|h)$"
#         is_matched = re.search(time_int, cond, re.IGNORECASE)
#         if is_matched:
#             return None
#         return cond if len(cond) > 0 else None
#
#     def get_time_condition(self):
#         """ Returns time condition """
#         if self.contains_interval_condition():
#             c = self.condition[2]
#             return c if len(c) > 0 else None
#             # return self.condition[2]
#         return None
#
#     def contains_interval_condition(self) -> bool:
#         """ Return a boolean value if a constraint template contains a time condition """
#         if self.condition is None:
#             return False
#         len_ = len(self.condition)
#         if len_ != 3:
#             return False
#         return True
#
#     def set_conditions(self, cond_str: str):
#         """Set coditions part of a constraint template """
#         """
#         set the cond_str
#         Parameters
#         ----------
#         cond_str: substring after Teample[x,y] from line "Teample[x,y] |...|...|..". thus, cond_str= |...|...|..
#
#         Returns
#         -------
#
#         """
#         self.condition_line = cond_str
#         if self.condition_line is None:
#             self.condition_line = "||"
#         conditions = cond_str.strip("|")
#         conds_list = conditions.split("|")
#         self.condition = [cl.strip() for cl in conds_list]
#
#     def update_props(self):
#         """
#         Updates the _dict, so it has updated values when any dict op is occurred
#         Returns
#         -------
#
#         """
#         self.key_value["template"] = self.template
#         self.key_value["activities"] = self.activities
#         self.key_value["condition"] = self.condition
#         self.key_value["template_name"] = self.template_name
#         self.key_value["template_line"] = self.template_line
#         self.key_value["violate"] = self.violate
#         self.key_value["condition_line"] = self.condition_line


"""
DeclareParsedModel is dictionary type based class or it is a data model
which contains the information of about declare model which is parsed.
"""


class DeclareParsedDataModel:
    def __init__(self):
        super().__init__()
        self.events: dict[str, dict[str, DeclareModelEvent]] = {}
        self.attributes_list: Dict[str, DeclareModelAttr] = {}
        self.templates: Dict[int, DeclareModelConstraintTemplate] = {}
        self.total_templates = 0

    def add_event(self, name: str, event_type: str) -> None:
        """
        Add an event to events dictionary if not exists yet.

        Parameters
        ----------
        name  the name of event or activity
        event_type  the type of the event, generally its "activity"

        Returns
        -------
        """
        event_types: dict[str, DeclareModelEvent] = {}
        if event_type in self.events:
            event_types = self.events[event_type]
        self.events[event_type] = event_types

        if name in event_types:
            raise KeyError(f"Multiple times the same event name and event type [{event_type} {name}] is declared!")
        event_types[name] = DeclareModelEvent(name, event_type)

    def add_attribute(self, event_name: str, attr_name: str):
        f"""
        Add the bounded attribute to the event/activity

        Parameters
        ----------
        event_name: the name of event that for which the {attr_name} is bounded to.
        attr_name: attribute name
        Returns
        -------

        """
        event_model: DeclareModelEvent = None
        for i in self.events:
            if event_name not in self.events[i]:
                raise ValueError(f"Unable to find the event or activity {event_name}")
            else:
                event_model = self.events[i][event_name]
                break

        attr: DeclareModelAttr
        attr_name = attr_name.strip()
        if attr_name in self.attributes_list:
            attr = self.attributes_list[attr_name]
        else:
            attr = DeclareModelAttr(attr_name)
            self.attributes_list[attr.get_name()] = attr
        attr.set_attached_event(event_model)

    def add_attribute_value(self, attr_name: str, attr_value: str):
        """
        Adding the attribute information
        Parameters
        ----------
        attr_name: str
        attr_type: DeclareModelAttributeType
        attr_value: str

        Returns
        -------
        """
        attr_name = attr_name.strip()
        if attr_name not in self.attributes_list:
            raise ValueError(f"Unable to find attribute {attr_name}")
        attribute = self.attributes_list[attr_name]
        attribute.set_attr_value(attr_value)

    def add_template(self, line: str, template: DeclareModelTemplate, cardinality: str, template_idx: int = None):
        """ Add parsed constraint template in parsed model """
        # templt = DeclareModelTemplateDataModel()
        # self.templates.append(templt)
        tmplt = DeclareModelConstraintTemplate(line, template_idx or self.total_templates)
        self.templates[self.total_templates] = tmplt
        self.total_templates = self.total_templates + 1
        tmplt.template = template
        if cardinality and len(cardinality) > 1:
            tmplt.cardinality = int(cardinality)
        else:
            tmplt.cardinality = 0
        compiler = re.compile(r"^(.*)\[(.*)\]\s*(.*)$")
        al = compiler.fullmatch(line)
        if len(al.group()) >= 2:
            events = al.group(2).strip()
            events = [e.strip() for e in events.split(',')]
            if template.is_binary:
                tmplt.events_activities = [self.find_event_by_name(events[0]), self.find_event_by_name(events[1])]
            else:
                tmplt.events_activities = [self.find_event_by_name(events[0])]
        tmplt.parse_constraint_conditions()

    def find_event_by_name(self, name: str):
        for ev_type in self.events:
            for ev_nm in self.events[ev_type]:
                if ev_nm.strip() == name.strip():
                    return self.events[ev_type][ev_nm]
        # TODO: raise an error.
        return None

    def to_dict(self):
        return {
            "events": {outer_key: {inner_key: value.to_dict() for inner_key, value in inner_dict.items()} for outer_key, inner_dict in self.events.items()},
            "attributes": {key: value.to_dict() for key, value in self.attributes_list.items()},
            "constraint_templates": {key: value.to_dict() for key, value in self.templates.items()},
        }

class DeclareModel(LTLModel):
    CONSTRAINTS_TEMPLATES_PATTERN = r"^(.*)\[(.*)\]\s*(.*)$"

    def __init__(self):
        super().__init__()
        # self.activities = []
        self.payload: List[str] = []
        self.serialized_constraints: List[str] = []
        self.constraints: List = []
        self.parsed_model: DeclareParsedDataModel = DeclareParsedDataModel()
        self.declare_model_lines: List[str] = []

    def set_constraints(self):
        for constraint in self.constraints:
            constraint_str = constraint['template'].templ_str
            if constraint['template'].supports_cardinality:
                constraint_str += str(constraint['n'])
            constraint_str += '[' + ", ".join(constraint["activities"]) + '] |' + ' |'.join(constraint["condition"])
            self.serialized_constraints.append(constraint_str)

    def get_decl_model_constraints(self):
        return self.serialized_constraints

    def to_file(self, model_path: str, **kwargs):
        if model_path is not None:
            with open(model_path, 'w') as f:
                for activity_name in self.activities:
                    f.write(f"activity {activity_name}\n")
                for constraint in self.serialized_constraints:
                    f.write(f"{constraint}\n")

    def parse_from_string(self, content: str, new_line_ctrl: str = "\n") -> DeclareModel:
        if type(content) is not str:
            raise RuntimeError("You must specify a string as input model.")
        lines = content.split(new_line_ctrl)
        self.declare_model_lines = lines
        self.parse(lines)
        return self

    def parse_from_file(self, filename: str, **kwargs) -> DeclareModel:
        lines = []
        with open(filename, "r+") as file:
            lines = file.readlines()
        self.declare_model_lines = lines
        self.parse(lines)
        return self

    def parse(self, lines: [str]):
        declare_parsed_model = self.parsed_model
        for line in lines:
            line = line.strip()
            if len(line) <= 1 or line.startswith("#"):  # line starting with # considered a comment line
                continue
            if DeclareModel.is_event_name_definition(line):  # split[0].strip() == 'activity':
                split = line.split(maxsplit=1)
                self.activities.append(split[1].strip())
                declare_parsed_model.add_event(split[1], split[0])
            elif DeclareModel.is_event_attributes_definition(line):
                split = line.split(": ", maxsplit=1)  # Assume complex "bind act3: categorical, integer, org:group"
                event_name = split[0].split(" ", maxsplit=1)[1].strip()
                attrs = split[1].strip().split(",", )
                for attr in attrs:
                    declare_parsed_model.add_attribute(event_name, attr.strip())
            elif DeclareModel.is_events_attrs_value_definition(line):
                """
                SOME OF Possible lines for assigning values to attribute

                categorical: c1, c2, c3
                categorical: group1:v1, group1:v2, group3:v1 
                cat1, cat2: group1:v1, group1:v2, group3:v1 
                price:art1, price:art2, cat2: group1:v1, group1:v2, group3:v1 
                integer: integer between 0 and 100
                org:resource: 10
                org:resource, org:vote: 10
                org:vote, grade: 9
                org:categorical: integer between 0 and 100
                categorical: integer between 0 and 100
                base, mark: integer between -30 and 100
                org:res, grade, concept:name: integer between 0 and 100
                """
                # consider this complex line: price:art1, price:art2, cat2: group1:v1, group1:v2, group3:v1
                split = line.split(": ", maxsplit=1)
                attributes_list = split[0]  # price:art1, price:art2, cat2
                attributes_list = attributes_list.strip().split(",")
                value = split[1].strip()
                for attr in attributes_list:
                    declare_parsed_model.add_attribute_value(attr, value)
            elif DeclareModel.is_constraint_template_definition(line):
                split = line.split("[", 1)
                template_search = re.search(r'(^.+?)(\d*$)', split[0])
                if template_search is not None:
                    template_str, cardinality = template_search.groups()
                    template = DeclareModelTemplate.get_template_from_string(template_str)
                    if template is not None:
                        activities = split[1].split("]")[0]
                        activities = activities.split(", ")
                        tmp = {"template": template, "activities": activities,
                               "condition": re.split(r'\s+\|', line)[1:]}
                        if template.supports_cardinality:
                            tmp['n'] = 1 if not cardinality else int(cardinality)
                            cardinality = tmp['n']
                        self.constraints.append(tmp)
                        declare_parsed_model.add_template(line, template, str(cardinality))
        self.set_constraints()

    @staticmethod
    def is_event_name_definition(line: str) -> bool:
        x = re.search(r"^\w+ [\w ]+$", line, re.MULTILINE)
        return x is not None

    @staticmethod
    def is_event_attributes_definition(line: str) -> bool:
        x = re.search("^bind (.*?)+$", line, re.MULTILINE)
        return x is not None

    @staticmethod
    def is_events_attrs_value_definition(line: str) -> bool:
        """
        categorical: c1, c2, c3
        categorical: group1:v1, group1:v2, group3:v1       <-------- Fails to parse this line
        integer: integer between 0 and 100
        org:resource: 10
        org:resource, org:vote: 10
        org:vote, grade: 9
        org:categorical: integer between 0 and 100
        categorical: integer between 0 and 100
        base, mark: integer between 0 and 100
        org:res, grade, concept:name: integer between 0 and 100
        :param line: declare line
        :return:
        """
        x = re.search(r"^(?!bind)([a-zA-Z_,0-9.?:\- ]+) *(: *[\w,.? \-]+)$", line, re.MULTILINE)
        if x is None:
            return False
        groups_len = len(x.groups())
        return groups_len >= 2

    @staticmethod
    def is_constraint_template_definition(line: str) -> bool:
        x = re.search(DeclareModel.CONSTRAINTS_TEMPLATES_PATTERN, line, re.MULTILINE)
        return x is not None

    @staticmethod
    def detect_declare_attr_value_type(value: str) -> DeclareModelAttributeType:
        """
        Detect the type of value assigned to an attribute assigned
        Parameters
        ----------
        value: assigned value
        Returns DeclareModelAttributeType
        -------
        """
        value = value.strip()
        v2 = value.replace("  ", "")
        if re.search(r"^[+-]?\d+$", value, re.MULTILINE):
            return DeclareModelAttributeType.INTEGER
        elif re.search(r"^[+-]?\d+(?:\.\d+)?$", value, re.MULTILINE):
            return DeclareModelAttributeType.FLOAT
        elif v2 and v2.lower().startswith("integer between"):
            # ^integer * between *[+-]?\d+(?:\.\d+)? *and [+-]?\d+(?:\.\d+)?$
            return DeclareModelAttributeType.INTEGER_RANGE
        elif v2 and v2.lower().startswith("float between"):
            # ^float * between *[+-]?\d+(?:\.\d+)? *and [+-]?\d+(?:\.\d+)?$
            return DeclareModelAttributeType.FLOAT_RANGE
        else:
            return DeclareModelAttributeType.ENUMERATION

    def __str__(self):
        st = f"""{{"activities": {self.activities}, "serialized_constraints": {self.serialized_constraints},\
        "constraints": {self.constraints}, "parsed_model": {self.parsed_model.to_json()} }} """
        return st.replace("'", '"')

