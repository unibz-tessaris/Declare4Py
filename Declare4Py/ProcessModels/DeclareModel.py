from __future__ import annotations

import re
import typing
from abc import ABC
from enum import Enum

from Declare4Py.ProcessModels.LTLModel import LTLModel


#ok
class DeclareModelTemplate(str, Enum):
    """ Enum class containing the metadata for each Constraint Template supported

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
                 reverseActivationTarget: bool = False):
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
            Whether the template supports cardinality, e.g., Existence template is unary
            but you can specify a number for how many times Existence should occur.
            "Existence4[A]|||" means it should occur at least 4 times.
        both_activation_condition: bool
            Whether some templates don't have a target condition, and both conditions are activation conditions.
        reverseActivationTarget: bool
            Whether some constraint templates have reverse activation and target conditions.
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
    NOT_CHAIN_RESPONSE = "Not Chain Response", True, True, False, False, False, True
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


#ok
class DeclareModelConditionParserUtility:
    """
    Class to support backward-compatibility to some older code. It contains two methods which parse and evaluate
     declare model conditions.
    """

    def __init__(self):
        super().__init__()

    def parse_data_cond(self, cond: str):  # TODO: could be improved using recursion ?
        """
        Parse the data condition
        Parameters
        ----------
        cond: str
            Could be activation or target condition

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

    def parse_time_cond(self, condition: str):
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


#ok
class DeclareModelEvent:
    """
    A class representing an event in a Declare Model, containing the event name, event type, and attributes.
    """

    def __init__(self, name: str, event_type: str):
        """
        Initializes a DeclareModelEvent instance with the provided name and event type.

        Parameters
        ----------
        name: str
            The event name, e.g., in activity(actName), actName is the event name.
        event_type: str
            The event type, e.g., in activity(actName), activity is the event type.
        """
        self.event_name = DeclareModelToken(name, "event_value")
        self.event_type = DeclareModelToken(event_type, "event_name")
        self.attributes: dict[str, DeclareModelAttr] = {}

    def set_bound_attributes(self, attrs_list: [DeclareModelAttr]) -> None:
        """
        Sets the bound attributes for the event.

        Parameters
        ----------
        attrs_list: List[DeclareModelAttr]
            A list of DeclareModelAttr instances representing the event's attributes.
        """
        self.attributes = {}
        for i in attrs_list:
            attrModel: DeclareModelAttr = i
            self.attributes[attrModel.attr_name] = attrModel

    def set_bound_attribute(self, attr: DeclareModelAttr) -> None:
        """
        Sets a single bound attribute for the event.

        Parameters
        ----------
        attr: DeclareModelAttr
            A DeclareModelAttr instance representing an event attribute.
        """
        self.attributes[attr.get_name()] = attr

    def get_event_name(self) -> str:
        """
        Returns the event name.

        Returns
        -------
        str
            The name of the event.
        """
        return self.event_name.get_name()

    def to_dict(self) -> dict:
        """
        Converts the DeclareModelEvent instance to a dictionary representation.

        Returns
        -------
        dict
            A dictionary containing the event type, encoded event type, event name, encoded event name,
            and bound attributes resources.
        """
        return {
            "event_type": self.event_type.get_name(),
            "event_encoded_type": self.event_type.get_encoded_name(),
            "event_name": self.event_name.get_name(),
            "event_encoded_name": self.event_name.get_encoded_name(),
            "bound_attributes_resources": {key: value.to_dict() for key, value in self.attributes.items()},
        }


#vedere se funziona
class DeclareModelEncoder:
    """ A singleton class which encodes and decodes the given values. It contains the information of encoded values
     during its lifecycle, so, it can decode the values back.
    """

    instance = None

    # Constructor
    def __new__(cls):
        """
        A singleton class which encodes and decodes the given values. It contains the information of encoded values
        during its lifecycle, so, it can decode the values back.
        """
        if cls.instance is None:
            cls.instance = super(DeclareModelEncoder, cls).__new__(cls)
        return cls.instance

    encoded_values: dict[str, str] = {}
    _inverse_encoded_values_store: dict[str, str] = {}
    event_nm_idx: int = 0
    event_vl_idx: int = 0
    attr_nm_idx: int = 0
    attr_vl_idx: int = 0
    other_counter: int = 0

    @classmethod
    def encode_value(cls, val2encode: str, val_type: typing.Literal["event_name", "event_value", "attr_name", "attr_val"]) -> str:
        """
        Encode the given value
        Parameters
        ----------
        val2encode: str
            value to encode
        val_type: str, optional
            type of value it is. Ie. the value can be the name of activity, attribute or its values(enumeration).

        Returns
        -------

        """
        if not isinstance(val2encode, str):
            return val2encode
        if val2encode.isnumeric():
            return val2encode
        val2encode = val2encode.strip()
        if val2encode in cls.encoded_values:
            return val2encode
        if val2encode in cls._inverse_encoded_values_store:
            return cls._inverse_encoded_values_store[val2encode]

        encoded_val = ""
        if val_type == "event_name":
            encoded_val = f"evt_name_{cls.event_nm_idx}"
            cls.event_nm_idx = cls.event_nm_idx + 1
        elif val_type == "event_value":
            encoded_val = f"evt_val_{cls.event_vl_idx}"
            cls.event_vl_idx = cls.event_vl_idx + 1
        elif val_type == "attr_name":
            encoded_val = f"attr_name_{cls.attr_nm_idx}"
            cls.attr_nm_idx = cls.attr_nm_idx + 1
        elif val_type == "attr_val":
            encoded_val = f"attr_value_{cls.attr_vl_idx}"
            cls.attr_vl_idx = cls.attr_vl_idx + 1
        else:
            encoded_val = f"other_{cls.other_counter}"
            cls.other_counter = cls.other_counter + 1

        cls.encoded_values[encoded_val] = val2encode
        cls._inverse_encoded_values_store[val2encode] = encoded_val
        return encoded_val

    @classmethod
    def decode_value(cls, s: str) -> str:

        """
        Decode the given value if it finds in the encoded_values list.
        Parameters
        ----------
        s: str
            a string value to decode.

        Returns
        -------
        str
        """

        if not isinstance(s, str):
            return s
        if s.isnumeric():
            return s
        s = s.strip()
        if s in cls.encoded_values:
            return cls.encoded_values[s]

        if s in cls._inverse_encoded_values_store:
            return cls._inverse_encoded_values_store[s]
        raise ValueError(f"Unable to decode value {s}.")

    @classmethod
    def to_dict(cls) -> dict:
        return {
            "event_nm_idx": cls.event_nm_idx,
            "event_vl_idx": cls.event_vl_idx,
            "attr_nm_idx": cls.attr_nm_idx,
            "attr_vl_idx": cls.attr_vl_idx,
            "other_counter": cls.other_counter,
            "encoded_values": cls.encoded_values,
            "inverse_encoded_values": cls._inverse_encoded_values_store
        }


#ok
class DeclareModelToken(ABC):
    """A Data model that represent each word of declare model as token."""

    def __init__(self, token: str, token_type: typing.Literal["event_name", "event_value", "attr_name", "attr_val"]):
        self.encoder = DeclareModelEncoder()
        self.value = token
        self.token_type: typing.Literal["event_name", "event_value", "attr_name", "attr_val"] = token_type

    def get_name(self) -> str:
        """Returns the name of the token"""
        return self.value

    def set_name(self, value) -> None:
        self.value = value

    def get_encoded_name(self) -> str:
        """Returns the encoded values of token.
        Returns
        -------
        str
        """
        if self.value.lower() == "activity" and self.token_type == "event_name":
            return "activity"
        return self.encoder.encode_value(self.get_name(), self.token_type)

    def to_dict(self) -> dict:
        """ Returns the dict which represents the object itself. This is for generating the JSON object"""
        return {
            "name": self.get_name(),
            "encoded_name": self.get_encoded_name(),
        }


#ok
class DeclareModelAttrValue(DeclareModelToken, ABC):
    """
    A class representing a Declare Model Attribute Value, which can be one of three types: enumeration, float range, or integer range.
    """

    def __init__(self, value: str, value_type: str):
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
        self.value: [DeclareModelToken] | [float] | [int] = None
        self.value_original: [str] | [float] | [int] = value
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
        if self.attribute_value_type == DeclareModelAttr.FLOAT_RANGE:
            matches = pattern.findall(self.value_original)
            self.value = [float(matches[0]), float(matches[1])]
            self.precision = self.get_float_biggest_precision(self.value[0], self.value[1])
        elif self.attribute_value_type == DeclareModelAttr.INTEGER_RANGE:
            self.precision = 1
            match = pattern.findall(self.value_original)  # Extract the numeric
            self.value = [int(match[0]), int(match[1])]
        elif self.attribute_value_type == DeclareModelAttr.ENUMERATION:
            self.value = [DeclareModelToken(v.strip(), "attr_val") for v in self.value_original.split(',')]
        else:
            raise ValueError("Unable to parse the attribute value. Attribute values can be Enumeration separated"
                             " by ',', or integer range, or float range")

    def get_float_biggest_precision(self, v1: float, v2: float) -> int:
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

    def get_precisioned_value(self) -> [DeclareModelToken] | [int]:
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
        if self.attribute_value_type == DeclareModelAttr.FLOAT_RANGE:
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


#ok
class DeclareModelAttr:
    """A class representing the attribute of declare model, An attribute can be imagined as resources shared
     between events. Contains information about the name of attribute, values, events attached to it.
    """

    INTEGER = "integer"
    FLOAT = "float"
    INTEGER_RANGE = "integer_range"
    FLOAT_RANGE = "float_range"
    ENUMERATION = "enumeration"

    def __init__(self, attr: str, value: str = None):
        self.attr_name = DeclareModelToken(attr, "attr_name")
        if value is not None:
            self.value_type: str = self.detect_declare_attr_value_type(value)
            self.attr_value: typing.Union[None, DeclareModelAttrValue] = DeclareModelAttrValue(value, self.value_type)
        else:
            self.attr_value: typing.Union[None, DeclareModelAttrValue] = None
        self.attached_events: dict[str, DeclareModelEvent] = {}

    def get_name(self) -> str:
        """Returns the name of the attribute """
        return self.attr_name.get_name()

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

    def detect_declare_attr_value_type(self, value: str) -> str:
        """
        Detect the type of value assigned to an attribute assigned
        Parameters
        ----------
        value: str
            assigned value

        Returns
        -------
                DeclareModelAttr
        """
        value = value.strip()
        v2 = value.replace("  ", "")
        if re.search(r"^[+-]?\d+$", value, re.MULTILINE):
            return DeclareModelAttr.INTEGER
        elif re.search(r"^[+-]?\d+(?:\.\d+)?$", value, re.MULTILINE):
            return DeclareModelAttr.FLOAT
        elif v2 and v2.lower().startswith("integer between"):
            # ^integer * between *[+-]?\d+(?:\.\d+)? *and [+-]?\d+(?:\.\d+)?$
            return DeclareModelAttr.INTEGER_RANGE
        elif v2 and v2.lower().startswith("float between"):
            # ^float * between *[+-]?\d+(?:\.\d+)? *and [+-]?\d+(?:\.\d+)?$
            return DeclareModelAttr.FLOAT_RANGE
        else:
            return DeclareModelAttr.ENUMERATION

    def set_attr_value(self, value: str):
        self.value_type = self.detect_declare_attr_value_type(value)
        self.attr_value = DeclareModelAttrValue(value, self.value_type)

    def to_dict(self):
        """
        Converts the DeclareModelAttr instance to a dictionary representation.

        Returns
        -------
        dict
            A dictionary containing the attribute informations.
        """
        return {
            "attribute_name": self.attr_name.get_name(),
            "attribute_encoded_name": self.attr_name.get_encoded_name(),
            "attr_value": self.attr_value.to_dict(),
        }


#ok
class DeclareModelConstraintTemplate:
    """
    A class representing a Declare Model Constraint Template.
    Some properties are created private so the logic of providing correct information such as conditions and activity name
    based on the constraint templates.
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

    def get_template_name(self) -> typing.Union[str, None]:
        """
        Returns the template name, considering the cardinality if supported by the template.

        Returns
        -------
        str
            The template name.
        """
        if self._template_name is None:
            return None

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
        compiler = re.compile(r"^(.*)\[(.*)]\s*(.*)$")
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
        # return self._conditions[0] if len(self._conditions) > 0 else None

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


#ok
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
        event_model: typing.Union[None, DeclareModelEvent] = None
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
        compiler = re.compile(r"^(.*)\[(.*)]\s*(.*)$")
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

    def decode_value(self, val: str, is_encoded: bool) -> str:
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
            val = DeclareModelEncoder().decode_value(val)
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
            "events": {outer_key: {inner_key: value.to_dict() for inner_key, value in inner_dict.items()} for outer_key, inner_dict in self.events.items()},
            "attributes": {key: value.to_dict() for key, value in self.attributes_list.items()},
            "constraint_templates": {key: value.to_dict() for key, value in self.templates.items()},
        }


#ok
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
    def detect_declare_attr_value_type(value: str) -> str:
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
            return DeclareModelAttr.INTEGER
        elif re.search(r"^[+-]?\d+(?:\.\d+)?$", value, re.MULTILINE):
            return DeclareModelAttr.FLOAT
        elif v2 and v2.lower().startswith("integer between"):
            # ^integer * between *[+-]?\d+(?:\.\d+)? *and [+-]?\d+(?:\.\d+)?$
            return DeclareModelAttr.INTEGER_RANGE
        elif v2 and v2.lower().startswith("float between"):
            # ^float * between *[+-]?\d+(?:\.\d+)? *and [+-]?\d+(?:\.\d+)?$
            return DeclareModelAttr.FLOAT_RANGE
        else:
            return DeclareModelAttr.ENUMERATION

    def __str__(self):
        st = f"""{{"activities": {self.activities}, "serialized_constraints": {self.serialized_constraints},\
        "constraints": {self.constraints}, "parsed_model": {self.parsed_model.to_json()} }} """
        return st.replace("'", '"')
