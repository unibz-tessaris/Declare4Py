from __future__ import annotations

import re
import typing
from abc import ABC
from enum import Enum

from Declare4Py.ProcessModels.LTLModel import LTLModel


class DeclareModelTemplate(str, Enum):
    """
    Enum class containing the metadata for each Constraint Template supported
    """

    def __new__(cls, *args, **kwds):
        """
        Creates a new DeclareModelTemplate instance and assigns a unique value based on the number of members.

        Parameters
        ----------
        *args
            Variable-length arguments passed to the Enum constructor.
        **kwds
            Keyword arguments passed to the Enum constructor.

        Returns
        -------
        DeclareModelTemplate
            The newly created DeclareModelTemplate instance with a unique value.
        """
        value = len(cls.__members__) + 1
        obj = str.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, templ_str: str, is_binary: bool, is_negative: bool, supports_cardinality: bool,
                 both_activation_condition: bool = False, is_shortcut: bool = False,
                 reverse_activation_target: bool = False):
        """
        Initializes a DeclareModelTemplate instance with the provided attributes.

        Parameters
        ----------
        templ_str: str
            The template name.
        is_binary: bool
            Whether the template supports two events.
        is_negative: bool
            Whether the template is negative.
        supports_cardinality: bool
            Whether the template supports cardinality, e.g., Existence template is unary,
            but you can specify a number for how many times Existence should occur.
            "Existence4[A]|||" means it should occur at least 4 times.
        both_activation_condition: bool
            Whether some templates don't have a target condition, and both conditions are activation conditions.
        reverse_activation_target: bool
            Whether some constraint templates have reverse activation and target conditions.
        """
        self.templ_str = templ_str
        self.is_binary = is_binary
        self.is_negative = is_negative
        self.supports_cardinality = supports_cardinality
        self.both_activation_condition = both_activation_condition
        self.is_shortcut = is_shortcut
        self.reverseActivationTarget = reverse_activation_target

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
    # TODO implements checker
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
        """
        Retrieves the template Enum instance from the given string representation.

        Parameters
        ----------
        template_str: str
            The string representation of the template.

        Returns
        -------
        DeclareModelTemplate
            The matching template Enum instance or None if not found.
        """
        template_str = template_str.replace(" ", "")
        template_str = template_str.replace("-", "")
        template_str = template_str.lower()
        return next(filter(lambda t: t.templ_str.replace(" ", "").replace("-", "").lower() == template_str,
                           DeclareModelTemplate), None)

    @classmethod
    def get_unary_templates(cls):
        """
        Retrieves unary templates.

        Returns
        -------
        tuple
            A tuple containing unary templates.
        """
        return tuple(filter(lambda t: not t.is_binary, DeclareModelTemplate))

    @classmethod
    def get_binary_templates(cls):
        """
       Retrieves binary templates.

       Returns
       -------
       tuple
           A tuple containing binary templates.
       """
        return tuple(filter(lambda t: t.is_binary, DeclareModelTemplate))

    @classmethod
    def get_positive_templates(cls):
        """
        Retrieves positive templates.

        Returns
        -------
        tuple
            A tuple containing positive templates.
        """
        return tuple(filter(lambda t: not t.is_negative, DeclareModelTemplate))

    @classmethod
    def get_negative_templates(cls):
        """
        Retrieves negative templates.

        Returns
        -------
        tuple
            A tuple containing negative templates.
        """
        return tuple(filter(lambda t: t.is_negative, DeclareModelTemplate))

    @classmethod
    def get_shortcut_templates(cls):
        """
        Retrieves shortcut templates.

        Returns
        -------
        tuple
            A tuple containing shortcut templates.
        """
        return tuple(filter(lambda t: t.is_shortcut, DeclareModelTemplate))

    @classmethod
    def are_conditions_reversed_applied(cls):
        """
        Retrieves templates with reversed activation and target conditions.

        Returns
        -------
        tuple
            A tuple containing templates with reversed activation and target conditions.
        """
        return tuple(filter(lambda t: t.reverseActivationTarget, DeclareModelTemplate))

    @classmethod
    def get_binary_not_shortcut_templates(cls):
        """
        Retrieves binary templates that are not shortcuts.

        Returns
        -------
        tuple
            A tuple containing binary templates that are not shortcuts.
        """
        return tuple(filter(lambda t: t.is_binary and not t.is_shortcut, DeclareModelTemplate))

    def __str__(self):
        return "<Template." + str(self.templ_str) + ": " + str(self.value) + " >"

    def __repr__(self):
        return "\"" + str(self.__str__()) + "\""


class DeclareModelConditionParserUtility:
    """
    Class to support backward-compatibility to some older code. It contains two methods which parse and evaluate
     declare model conditions.
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    def parse_data_cond(cond: str):  # TODO: could be improved using recursion ?
        """
        Parse the data condition
        Parameters
        ----------
        cond: str
            Could be activation or target condition
            Parsing modello declare, deve ancora trasformarlo in asp
        Returns
        -------
            str
        """
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
                            py_cond = (py_cond + " " + attr + " in A and " + attr + " in T "
                                       + 'and A["' + attr + '"] == T["' + attr + '"]')
                        elif next_word.lower() == "different":
                            tmp = []
                            while cond and not (cond.startswith(')') or cond.lower().startswith('and')
                                                or cond.lower().startswith('or')):
                                w = re.split(r'[\s()]+', cond)[0]
                                cond = cond[len(w):].lstrip()
                                tmp.append(w)
                            attr = " ".join(tmp)
                            py_cond = (py_cond + " " + attr + " in A and " + attr + " in T "
                                       + 'and A["' + attr + '"] != T["' + attr + '"]')
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

    @staticmethod
    def parse_time_cond(condition: str):
        """
        Parse time condition
        Parameters
        ----------
        condition: str
        Returns
        -------
        str
        """
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


class DeclareModelToken(ABC):
    """A Data model that represent each word of declare model as token."""

    def __init__(self,
                 name: str,
                 model_type: typing.Literal["event_name", "event_value", "attr_name", "attr_val"] | str
                 ):

        if not isinstance(name, str):
            raise ValueError("Invalid instance for value name, should be a string!")
        self.__name: str = name

        if model_type in ["event_name", "event_value", "attr_name", "attr_val"]:
            self.__model_type: str = model_type
        else:
            self.__model_type: str = f"other"

        self.encoder: _Encoder = _Encoder()

    def get_name(self) -> str:
        """Returns the name of the token"""
        return self.__name

    def set_name(self, name):
        """Sets the name of the token"""
        self.__name = name

    def get_encoded_name(self) -> str:
        """Returns the encoded values of token.
        Returns
        -------
        str
        """
        if self.__name.lower() == "activity" and self.__model_type == "event_name":
            return "activity"
        return self.encoder.encode_value(self.get_name(), typing.Type[self.__model_type])

    def to_dict(self) -> typing.Dict[str, str]:
        """ Returns the dict which represents the object itself. This is for generating the JSON object"""
        return {
            self.__model_type: self.get_name(),
            f"encoded_{self.__model_type}": self.get_encoded_name(),
        }


class DeclareModelEvent:
    """
    A class representing an event in a Declare Model, containing the event name, event type, and attributes.
    """

    def __init__(self,
                 event_name: str,
                 event_value: str
                 ):
        """
        Initializes a DeclareModelEvent instance with the provided name and event type.

        Parameters
        ----------
        event_name: str
            The event name, e.g., in activity(actName), actName is the event name.
        event_value: str
            The event type, e.g., in activity(actName), activity is the event type.
        """

        self.__event_name: DeclareModelToken = DeclareModelToken(event_name, "event_name")
        self.__event_value: DeclareModelToken = DeclareModelToken(event_value, "event_value")

        self.attributes: dict[str, DeclareModelAttr] = {}

    def set_bound_attributes(self, attrs_list: typing.List[DeclareModelAttr]):
        """
        Sets the bound attributes for the event.

        Parameters
        ----------
        attrs_list: List[DeclareModelAttr]
            A list of DeclareModelAttr instances representing the event's attributes.
        """
        self.attributes = {}
        for i in attrs_list:
            attr_model: DeclareModelAttr = i
            self.attributes[attr_model.get_attr_name()] = attr_model

    def set_bound_attribute(self, attr: DeclareModelAttr):
        """
        Sets a single bound attribute for the event.

        Parameters
        ----------
        attr: DeclareModelAttr
            A DeclareModelAttr instance representing an event attribute.
        """
        self.attributes[attr.get_attr_name()] = attr

    def get_event_name(self) -> str:
        """Returns the name of the event"""
        return self.__event_name.get_name()

    def get_encoded_event_name(self) -> str:
        """Returns the encoded name of the event"""
        return self.__event_name.get_encoded_name()

    def get_event_value(self) -> str:
        """Returns the value of the event"""
        return self.__event_value.get_name()

    def get_encoded_event_value(self) -> str:
        """Returns the encoded value of the event"""
        return self.__event_value.get_encoded_name()

    def to_dict(self) -> typing.Dict:

        #  typing.Dict[str, typing.Union[str, dict]]:

        """
        Converts the DeclareModelEvent instance to a dictionary representation.

        Returns
        -------
        dict
            A dictionary containing the event type, encoded event type, event name, encoded event name,
            and bound attributes resources.
        """
        return {"event_names": self.__event_name.to_dict(), "event_values": self.__event_value.to_dict(), "bound_attributes_resources": {key: value.to_dict() for key, value in self.attributes.items()}}


class DeclareModelAttr:
    """
    A class representing the attribute of declare model, An attribute can be imagined as resources shared
     between events. Contains information about the name of attribute, values, events attached to it.
    """

    INTEGER = "integer"
    FLOAT = "float"
    INTEGER_RANGE = "integer_range"
    FLOAT_RANGE = "float_range"
    ENUMERATION = "enumeration"

    def __init__(self, attr_name: str, attr_value: str | None = None):

        self.__attr_name: DeclareModelToken = DeclareModelToken(attr_name, "attr_name")
        self.__value_type: typing.Union[DeclareModelAttributeType, None] = None
        self.__attr_value: typing.Union[DeclareModelAttrValue, None] = None

        if attr_value is not None:
            self.__value_type = DeclareModelAttributeType.detect_declare_attr_value_type(attr_value)
            self.__attr_value = DeclareModelAttrValue(attr_value, self.__value_type)

        self.attached_events: dict[str, DeclareModelEvent] = {}

    def get_attr_name(self) -> str:
        """Returns the name of the attribute """
        return self.__attr_name.get_name()

    def get_encoded_attr_name(self) -> str:
        """Returns the encoded name of the attribute """
        return self.__attr_name.get_encoded_name()

    def get_attr_value(self) -> str | None:
        """Returns the value of the attribute """
        if self.__attr_value is not None:
            return self.__attr_value.get_name()
        return None

    def get_encoded_attr_value(self) -> str | None:
        """Returns the encoded value of the attribute """
        if self.__attr_value is not None:
            return self.__attr_value.get_encoded_name()
        return None

    def set_attached_events(self, ev_list: [DeclareModelEvent]):
        """Saves the attached events to a list """
        self.attached_events = []
        for ev in ev_list:
            self.set_attached_event(ev)
        # self.attached_events = ev_list

    def set_attached_event(self, event: DeclareModelEvent):
        """Saves the attached event to a list """
        ev_nm = event.get_event_name()
        for i in self.attached_events:
            if i == ev_nm:
                # event already exists. or we can raise a warning that indicates
                # two or more times to same attributes to same event are declared
                return
        self.attached_events[event.get_event_name()] = event
        event.set_bound_attribute(self)

    def set_attr_value(self, attr_value: str):
        self.__value_type = DeclareModelAttributeType.detect_declare_attr_value_type(attr_value)
        self.__attr_value = DeclareModelAttrValue(attr_value, self.__value_type)

    def to_dict(self) -> dict:
        """
        Converts the DeclareModelAttr instance to a dictionary representation.

        Returns
        -------
        dict
            A dictionary containing the attribute information.
        """
        return {**self.__attr_name.to_dict(), **{"attr_value": self.__attr_value.to_dict()}}


class DeclareModelAttrValue(DeclareModelToken, ABC):
    """
    A class representing a Declare Model Attribute Value, which can be one of three types:
        - enumeration
        - float range
        - integer range
    """

    def __init__(self, value: str, value_type: DeclareModelAttributeType):
        """
        Initializes a DeclareModelAttrValue instance with the provided value and value type.

        Parameters
        ----------
        value: str
            The attribute value as a string.
        value_type: DeclareModelAttributeType
            The type of the attribute value (enumeration, float range, or integer range).
        """
        super().__init__(value, "attr_val")
        self.value: typing.Union[typing.List[DeclareModelToken], typing.List[float], typing.List[int], None] = None
        self.value_original: str = value
        self.attribute_value_type = value_type
        self.precision: int = 1
        self.parse_attr_value()

    def parse_attr_value(self):
        """
        Parses the attribute value based on its type.
        """
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

    @staticmethod
    def get_float_biggest_precision(v1: float, v2: float) -> int:
        """
        Gets the biggest float precision to scale up a number.

        Parameters
        ----------
        v1: float
            The first float value.
        v2: float
            The second float value.

        Returns
        -------
        int
            The biggest float precision.
        """
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

    def get_precisioned_value(self) -> typing.Union[typing.List[DeclareModelToken], typing.List[int]]:
        """
        Returns the attribute value with precision applied, if it's a float range.
        If the value is type of range float or integer, it will return array of two integer values, precision applied.
        if the value is type of enumeration, then each element will be type of DeclareModelToken.
        Precision applied means that floats are converted into integer and scaled up based on decimal values.
        Returns
        -------
        Union[List[DeclareModelToken], List[int]]
            The attribute value with precision applied.
        """
        if self.attribute_value_type == DeclareModelAttributeType.FLOAT_RANGE:
            frm = int((10 ** self.precision) * self.value[0])
            to = int((10 ** self.precision) * self.value[1])
            return [frm, to]
        # if self.attribute_value_type == DeclareModelAttributeType.INTEGER_RANGE:
        #     return [self.value[0], self.value[1]]
        # decoded_enum_values = []
        return self.value

    def to_dict(self):
        """
        Converts the DeclareModelAttrValue instance to a dictionary representation.

        Returns
        -------
        dict
            A dictionary containing the attribute value type, precision, original value, and parsed value.
        """
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


class DeclareModelAttributeType(str, Enum):
    """An Enum class that specifies types of attributes of the Declare model
    """
    INTEGER = "integer"
    FLOAT = "float"
    INTEGER_RANGE = "integer_range"
    FLOAT_RANGE = "float_range"
    ENUMERATION = "enumeration"

    def __str__(self):
        return self.value

    def __repr__(self):
        return "\"" + self.__str__() + "\""

    @staticmethod
    def detect_declare_attr_value_type(value: str) -> DeclareModelAttributeType:
        """
        Detect the type of value assigned to an attribute assigned
        Parameters
        ----------
        value: str
            assigned value

        Returns
        -------
            DeclareModelAttributeType
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


class DeclareModelConstraintTemplate:
    """
    A class representing a Declare Model Constraint Template.
    Some properties are created private so the logic of providing correct information such as conditions and
    activity name based on the constraint templates.
    I.E Existence and Absence case where Existence1 and Absence1 doesn't exist but other unary does.
    Another case is for the reverseConditions of some constraints.
    """

    def __init__(self, template_line: str, template_number_id: int):
        """
        Initializes a DeclareModelConstraintTemplate instance with the provided template line and template number ID.

        Parameters
        ----------
        template_line: str
            The constraint template line as a string.
        template_number_id: int
            The template number ID.
        """
        self.line = template_line
        self.events_activities: [DeclareModelEvent] = []
        self.cardinality: int = 0  # cardinality is only for unary and 0 means template doesn't have
        self.template: typing.Union[DeclareModelTemplate, None] = None
        self.template_index: int = template_number_id
        self.violate: bool = False
        self._template_name: typing.Union[str, None] = None
        self._conditions_line: typing.Union[str, None] = None
        self._conditions: [str] = []  # conditions: activation, target, time

    def get_template_name(self) -> str:
        """
        Returns the template name, considering the cardinality if supported by the template.

        Returns
        -------
        str
            The template name.
        """
        if self.template.supports_cardinality:
            new_name = self.template.templ_str
            if self.cardinality > 0:
                new_name = self.template.templ_str + str(self.cardinality)
            # if self._template_name.lower() == "existence1" or self._template_name.lower() == "absence1":
            if new_name.lower() == "existence1" or new_name.lower() == "absence1":
                new_name = new_name.replace("1", "")
            return new_name
        return self.template.templ_str

    def get_conditions(self):
        """
        Returns the parsed conditions: activation, target, and time conditions if present.

        Returns
        -------
        tuple
            A tuple containing activation, target, and time conditions.
        """
        return self.get_activation_condition(), self.get_target_condition(), self.get_time_condition()

    def parse_constraint_conditions(self):
        """
        Parses the constraint conditions in the template line.
        """
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
            conditions_list = conditions.split("|")
            self._conditions = [cl.strip() for cl in conditions_list]
            """ Some declare models use T.attribute for target conditions reference and some uses B.attributes"""
            if self.template.is_binary and len(conditions_list) < 2:
                raise ValueError(f"Unable to parse the conditions of binary constraint template")
            if len(conditions_list) > 3:
                raise ValueError(f"Unable to parse the line due to the exceeds conditions (> 3)")

    def get_activation_condition(self):
        """
        Returns the activation condition.

        Returns
        -------
        str
            The activation condition, if present. Otherwise, None.
        """
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
        """
        Returns the target condition.

        Returns
        -------
        str
            The target condition, if present. Otherwise, None.
        """
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
        """
        Returns the time condition.

        Returns
        -------
        str
            The time condition, if present. Otherwise, None.
        """
        if self.contains_interval_condition():
            c = self._conditions[2]
            return c if len(c) > 0 else None
            # return self.condition[2]
        return None

    def contains_interval_condition(self) -> bool:
        """
        Determines whether the constraint template contains a time condition.

        Returns
        -------
        bool
            True if the template contains a time condition, otherwise False.
        """
        if self._conditions is None:
            return False
        len_ = len(self._conditions)
        if len_ != 3:
            return False
        return True

    def to_dict(self):
        """
        Converts the DeclareModelConstraintTemplate instance to a dictionary representation.

        Returns
        -------
        dict
            A dictionary containing the template name, index, cardinality, condition line, activation condition,
            target condition, time condition, violation status, and events involved.
        """
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


class DeclareParsedDataModel:
    """
    DeclareParsedDataModel holds the parsed data from the Declare Model, including events, attributes, and templates.

    Attributes
    ----------
    events : dict
        A dictionary containing the events in the Declare Model, categorized by their event type.
    attributes_list : dict
        A dictionary containing the attributes of the Declare Model.
    templates : dict
        A dictionary containing the constraint templates of the Declare Model.
    total_templates : int
        The total number of constraint templates in the Declare Model.
    """

    def __init__(self):
        super().__init__()
        self.events: dict[str, dict[str, DeclareModelEvent]] = {}
        self.attributes_list: dict[str, DeclareModelAttr] = {}
        self.templates: dict[int, DeclareModelConstraintTemplate] = {}
        self.total_templates = 0

    def get_total_events(self) -> int:
        """Returns the total events"""
        num = 0
        for k, v in self.events.items():
            num = num + len(v)
        return num

    def add_event(self, name: str, event_type: str) -> None:
        """
        Add an event to the events dictionary if it does not already exist.

        Parameters
        ----------
        name : str
            The name of the event or activity.
        event_type : str
            The type of the event, typically "activity".
        """
        event_types: dict[str, DeclareModelEvent] = {}
        if event_type in self.events:
            event_types = self.events[event_type]
        self.events[event_type] = event_types

        if name in event_types:
            raise KeyError(f"Multiple times the same event name and event type [{event_type} {name}] is declared!")
        event_types[name] = DeclareModelEvent(name, event_type)

    def add_attribute(self, event_name: str, attr_name: str):
        """
        Add a bounded attribute to the event/activity.

        Parameters
        ----------
        event_name : str
            The name of the event to which the attribute is bound.
        attr_name : str
            The name of the attribute.
        """
        event_model: typing.Union[DeclareModelEvent, None] = None
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
            self.attributes_list[attr.get_attr_name()] = attr
        attr.set_attached_event(event_model)

    def add_attribute_value(self, attr_name: str, attr_value: str):
        """
        Add the attribute information to the attribute list.

        Parameters
        ----------
        attr_name : str
            The name of the attribute.
        attr_value : str
            The value of the attribute.
        """
        attr_name = attr_name.strip()
        if attr_name not in self.attributes_list:
            raise ValueError(f"Unable to find attribute {attr_name}")
        attribute = self.attributes_list[attr_name]
        attribute.set_attr_value(attr_value)

    def add_template(self, line: str, template: DeclareModelTemplate, cardinality: str, template_idx: int = None):
        """
        Add a parsed constraint template to the parsed model.

        Parameters
        ----------
        line : str
            The line containing the constraint template.
        template : DeclareModelTemplate
            The DeclareModelTemplate object representing the constraint template.
        cardinality : str
            The cardinality of the constraint template.
        template_idx : int, optional
            The index of the constraint template in the model, defaults to None.
        """
        tmplt = DeclareModelConstraintTemplate(line, template_idx or self.total_templates)
        self.templates[self.total_templates] = tmplt
        self.total_templates = self.total_templates + 1
        tmplt.template = template
        if cardinality and len(cardinality) > 0:
            tmplt.cardinality = int(cardinality)
        else:
            tmplt.cardinality = 0
        compiler = re.compile(r"^(.*)\[(.*)\]\s*(.*)$")
        al = compiler.fullmatch(line)
        if len(al.group()) >= 1:
            template_name = al.group(1).strip()
            tmplt._template_name = template_name.strip()
        if len(al.group()) >= 2:
            events = al.group(2).strip()
            events = [e.strip() for e in events.split(',')]
            if template.is_binary:
                tmplt.events_activities = [self.find_event_by_name(events[0]), self.find_event_by_name(events[1])]
            else:
                tmplt.events_activities = [self.find_event_by_name(events[0])]
        tmplt.parse_constraint_conditions()

    def find_event_by_name(self, name: str):
        """
        Find an event by its name in the Declare Model.

        Parameters
        ----------
        name : str
            The name of the event to find.

        Returns
        -------
        DeclareModelEvent or None
            The found event or None if not found.
        """
        for ev_type in self.events:
            for ev_nm in self.events[ev_type]:
                if ev_nm.strip() == name.strip():
                    return self.events[ev_type][ev_nm]
        # TODO: raise an error.
        return None

    # TODO ask professor the uniqueness of encoded variables
    @staticmethod
    def decode_value(val: str, is_encoded: bool) -> str:
        """
        Decode a value if it is encoded.

        Parameters
        ----------
        val : str
            The value to decode.
        is_encoded : bool
            A boolean indicating whether the value is encoded or not.

        Returns
        -------
        str
            The decoded value.
        """
        if is_encoded:

            val_type = "other"
            for type_name in ["event_name", "event_value", "attr_name", "attr_val"]:
                if val.find(type_name) != -1:
                    val_type = type_name
                    break

            val = _Encoder().decode_value(val, typing.Type[val_type])
        return val

    def to_dict(self):
        """
        Convert the DeclareParsedDataModel object to a dictionary representation.

        Returns
        -------
        dict
            The dictionary representation of the DeclareParsedDataModel object.
        """
        return {
            "events": {outer_key: {inner_key: value.to_dict() for inner_key, value in inner_dict.items()} for
                       outer_key, inner_dict in self.events.items()},
            "attributes": {key: value.to_dict() for key, value in self.attributes_list.items()},
            "constraint_templates": {key: value.to_dict() for key, value in self.templates.items()},
        }

    def to_json(self):
        return self.to_json()


class DeclareModel(LTLModel):
    CONSTRAINTS_TEMPLATES_PATTERN = r"^(.*)\[(.*)\]\s*(.*)$"  # Regex pattern for parsing constraint templates.
    """
    The DeclareModel class is a subclass of LTLModel that is used to represent and manipulate Declare models.
     It includes methods for parsing, setting constraints, writing to a file, and more.
     Attributes:
        CONSTRAINTS_TEMPLATES_PATTERN: A regular expression pattern for parsing constraint templates.
        payload: A list of strings representing the payload.
        serialized_constraints: A list of strings representing the serialized constraints.
        constraints: A list of constraint objects.
        parsed_model: An instance of DeclareParsedDataModel representing the parsed Declare model.
        declare_model_lines: A list of strings representing the lines of the Declare model.
    """

    def __init__(self):
        super().__init__()
        # self.activities = []
        self.payload: [str] = []
        self.serialized_constraints: [str] = []
        self.constraints = []
        self.parsed_model: DeclareParsedDataModel = DeclareParsedDataModel()
        self.declare_model_lines: [str] = []

    def set_constraints(self):
        """Sets the constraints for the Declare model"""
        for constraint in self.constraints:
            constraint_str = constraint['template'].templ_str
            if constraint['template'].supports_cardinality:
                constraint_str += str(constraint['n'])
            constraint_str += '[' + ", ".join(constraint["activities"]) + '] |' + ' |'.join(constraint["condition"])
            self.serialized_constraints.append(constraint_str)

    def get_decl_model_constraints(self):
        """Returns the serialized constraints of the Declare model"""
        return self.serialized_constraints

    def to_file(self, model_path: str, **kwargs):
        """Writes the Declare model to a file."""
        if model_path is not None:
            with open(model_path, 'w') as f:
                for activity_name in self.activities:
                    f.write(f"activity {activity_name}\n")
                for constraint in self.serialized_constraints:
                    f.write(f"{constraint}\n")

    def parse_from_string(self, content: str, new_line_ctrl: str = "\n") -> DeclareModel:
        """
        Parses a Declare model from a string
        Parameters
        ----------
        content: str
            Declare model in string format
        new_line_ctrl: str
            new line char
        Returns
        -------
            DeclareModel
        """
        if type(content) is not str:
            raise RuntimeError("You must specify a string as input model.")
        lines = content.split(new_line_ctrl)
        self.declare_model_lines = lines
        self.parse(lines)
        return self

    def parse_from_file(self, filename: str, **kwargs) -> DeclareModel:
        """
        Parameters
        ----------
        filename: str
            text file containing declare model
        kwargs

        Returns
        -------

        """
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


class _Encoder(object):
    """
    The Encoder class is used by the DeclareModelToken class in order to encode and decode the value of the Model

    This class uses the singleton pattern to maintain uniqueness between decoded model names for each model type

    Utilizes the TypeEncoder class in order to define uniqueness of each DeclareModelToken utilizing name and type
    and not only name
    """

    instance = None

    class TypeEncoder:
        """
        The TypeEncoder class is used by the Encoder class in order to store the encoded values for each type.

        This class stores also the number of encoded values and the inverse store of the decoded values
        """

        def __init__(self, model_type: str):
            self.model_type: str = model_type
            self.counter: int = 0
            self.encoded_values: dict[str, str] = {}
            self.inverse_encoded_values_store: dict[str, str] = {}

        def encode_value(self, val_to_encode: str, val_type: str) -> str:
            """
            Encode the given value
            Parameters
            ----------
            val_to_encode: str
                value to encode
            val_type: str, optional
                type of value it is. I.e. the value can be the name of activity, attribute or its values(enumeration).

            Returns
            -------
            str: The encoded value
            """

            if val_type != self.model_type:
                return val_to_encode
            if val_to_encode in self.encoded_values:
                return val_to_encode
            if val_to_encode in self.inverse_encoded_values_store:
                return self.inverse_encoded_values_store[val_to_encode]

            encoded_val: str = f"{val_type}_{self.counter}"
            self.counter += 1

            self.encoded_values[encoded_val] = val_to_encode
            self.inverse_encoded_values_store[val_to_encode] = encoded_val
            return encoded_val

        def decode_value(self, encoded_val: str) -> str:
            """
            Decode the given value if it finds in the encoded_values list.
            Parameters
            ----------
            encoded_val: str
                a string value to decode.

            Returns
            -------
            str: The decoded value
            """

            if encoded_val in self.encoded_values:
                return self.encoded_values[encoded_val]

            if encoded_val in self.inverse_encoded_values_store:
                return self.inverse_encoded_values_store[encoded_val]

            raise ValueError(f"Unable to decode value {encoded_val}.")

    _counters: dict[str, TypeEncoder] = {
        "event_name": TypeEncoder("event_name"),
        "event_value": TypeEncoder("event_value"),
        "attr_name": TypeEncoder("attr_name"),
        "attr_val": TypeEncoder("attr_val"),
        "other": TypeEncoder("other"),
    }

    def __new__(cls):
        """
        A singleton class which encodes and decodes the given values. It contains the information of encoded values
        during its lifecycle, so, it can decode the values back.
        """
        if cls.instance is None:
            cls.instance = super(_Encoder, cls).__new__(cls)
        return cls.instance

    def encode_value(self,
                     val_to_encode: str,
                     val_type: typing.Literal["event_name", "event_value", "attr_name", "attr_val"]
                     ) -> str:
        """
        Encode the given value
        Parameters
        ----------
        val_to_encode: str
            value to encode
        val_type: str, optional
            type of value it is. I.e. the value can be the name of activity, attribute or its values(enumeration).

        Returns
        -------
        str: The encoded value
        """

        if not isinstance(val_to_encode, str):
            return val_to_encode
        if val_to_encode.isnumeric():
            return val_to_encode
        val_to_encode = val_to_encode.strip()

        if val_type in self._counters.keys():
            return self._counters[val_type].encode_value(val_to_encode, val_type)
        else:
            return self._counters["other"].encode_value(val_to_encode, val_type)

    def decode_value(self,
                     encoded_val: str,
                     val_type: typing.Literal["event_name", "event_value", "attr_name", "attr_val"]
                     ) -> str:
        """
        Decode the given value if it finds in the encoded_values list.
        Parameters
        ----------
        encoded_val: str
            a string value to decode.

        val_type: str, optional
            type of value it is. I.e. the value can be the name of activity, attribute or its values(enumeration).

        Returns
        -------
        str: The decoded value
        """

        if not isinstance(encoded_val, str):
            return encoded_val
        if encoded_val.isnumeric():
            return encoded_val
        encoded_val = encoded_val.strip()

        if val_type in self._counters.keys():
            return self._counters[val_type].decode_value(encoded_val)
        else:
            return self._counters["other"].decode_value(encoded_val)
