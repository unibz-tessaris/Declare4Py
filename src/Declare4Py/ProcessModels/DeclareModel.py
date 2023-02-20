from __future__ import annotations

import base64
import copy
import re
from enum import Enum
from typing import Dict, List, Union

from src.Declare4py.ProcessModels.LTLModel import LTLModel
from src.Declare4py.Utils.custom_utility_dict import CustomUtilityDict


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
                 both_activation_condition: bool = False, is_shortcut: bool = False):
        """

        Parameters
        ----------
        templ_str: template name
        is_binary: whether template supports 2 events
        is_negative: whether the template is negative
        supports_cardinality: whether template supports cardinality, i.e Existence template is unary
         but you can specify a number how many times Existence should occur. "Existence4[A]|||" where 4 times at least occur.
        both_activation_condition: some templates doesn't have target condition, instead both conditions are activation conditions.
        """
        self.templ_str = templ_str
        self.is_binary = is_binary
        self.is_negative = is_negative
        self.supports_cardinality = supports_cardinality
        self.both_activation_condition = both_activation_condition
        self.is_shortcut = is_shortcut

    EXISTENCE = "Existence", False, False, True, False, False
    ABSENCE = "Absence", False, False, True, False, False
    EXACTLY = "Exactly", False, False, True, False, False
    INIT = "Init", False, False, False, False, False

    CHOICE = "Choice", True, False, False, True, False
    EXCLUSIVE_CHOICE = "Exclusive Choice", True, False, False, True, False

    RESPONDED_EXISTENCE = "Responded Existence", True, False, False, False, False
    RESPONSE = "Response", True, False, False, False, False
    ALTERNATE_RESPONSE = "Alternate Response", True, False, False, False, False
    CHAIN_RESPONSE = "Chain Response", True, False, False, False, False
    PRECEDENCE = "Precedence", True, False, False, False, False
    ALTERNATE_PRECEDENCE = "Alternate Precedence", True, False, False, False, False
    CHAIN_PRECEDENCE = "Chain Precedence", True, False, False, False, False

    # response(A, b) and precedence(a, b) = succession(a, b)
    # responded_existence(A, b) and responded_existence(b, a) = coexistence(a, b)
    # TODO implementare i checker
    SUCCESSION = "Succession", True, False, False, True, True
    ALTERNATE_SUCCESSION = "Alternate Succession", True, False, False, True, True
    CO_EXISTENCE = "Co-Existence", True, False, False, True, True
    CHAIN_SUCCESSION = "Chain Succession", True, False, False, True, True
    NOT_CHAIN_SUCCESSION = "Not Chain Succession", True, True, False, True, True
    NOT_CO_EXISTENCE = "Not Co-Existence", True, True, False, True, True
    NOT_SUCCESSION = "Not Succession", True, True, False, True, True

    NOT_RESPONDED_EXISTENCE = "Not Responded Existence", True, True, False, False, False
    NOT_RESPONSE = "Not Response", True, True, False, False, False
    NOT_PRECEDENCE = "Not Precedence", True, True, False, False, False
    NOT_CHAIN_RESPONSE = "Not Chain Response", True, True, False, False, False
    NOT_CHAIN_PRECEDENCE = "Not Chain Precedence", True, True, False, False, False

    @classmethod
    def get_template_from_string(cls, template_str):
        return next(filter(lambda t: t.templ_str == template_str, DeclareModelTemplate), None)

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


class DeclareModelEvent(CustomUtilityDict):
    def __init__(self):
        super().__init__()
        self.name: str = ""  # name of the activity/fact
        self.event_type: str = ""  # type of fact, can be activity, trace.
        self.attributes: Dict[str, Dict] = {}
        self.update_props()

    def update_props(self):
        self.key_value["name"] = self.name
        self.key_value["event_type"] = self.event_type
        self.key_value["attributes"] = self.attributes


"""
A data model class which contains information about a parsed template constraint.
"""


class DeclareModelTemplateDataModel(CustomUtilityDict):

    def __init__(self):
        super().__init__()
        self.template: Union[DeclareModelTemplate, None] = None
        self.activities: Union[str, None] = None
        self.condition: Union[List[str], None] = None
        self.template_name: Union[str, None] = None
        self.template_line: Union[str, None]  # Constraint lines
        self.condition_line: Union[str, None]  # |A.grade < 2  | T.mark > 2|1,5,s
        self.violate: bool = False
        self.template_index_id: int = None

    def get_conditions(self):
        return self.get_active_condition(), self.get_target_condition(), self.get_time_condition()

    def get_active_condition(self):
        if len(self.condition) > 0:
            c = self.condition[0]
            return c if len(c) > 0 else None
        return None

    def get_target_condition(self):
        if len(self.condition) > 1:
            cond_at_1_idx = self.condition[1]
            time_int = r"^[\d.]+,?([\d.]+)?[,]?(s|m|d|h)$"
            is_matched = re.search(time_int, cond_at_1_idx, re.IGNORECASE)
            if is_matched:
                return None
            c = self.condition[1]
            return c if len(c) > 0 else None
            # return self.condition[1]
        return None

    def get_time_condition(self):
        if self.contains_interval_condition():
            c = self.condition[2]
            return c if len(c) > 0 else None
            # return self.condition[2]
        return None

    def contains_interval_condition(self) -> bool:
        if self.condition is None:
            return False
        len_ = len(self.condition)
        if len_ != 3:
            return False
        return True
        # if self.condition_line is None:
        #     return False
        # parts = self.condition_line.strip("|").split("|")
        # if len(parts) == 3:
        #     time_int = r"^[\d.]+,?([\d.]+)?[,]?(s|m|d|h)$"
        #     return re.search(time, parts, re.IGNORECASE)
        # return False

    def set_conditions(self, cond_str: str):
        """
        set the cond_str
        Parameters
        ----------
        cond_str: substring after Teample[x,y] from line "Teample[x,y] |...|...|..". thus, cond_str= |...|...|..

        Returns
        -------

        """
        self.condition_line = cond_str
        conditions = cond_str.strip("|")
        conds_list = conditions.split("|")
        self.condition = [cl.strip() for cl in conds_list]

    def update_props(self):
        """
        Updates the _dict, so it has updated values when any dict op is occurred
        Returns
        -------

        """
        self.key_value["template"] = self.template
        self.key_value["activities"] = self.activities
        self.key_value["condition"] = self.condition
        self.key_value["template_name"] = self.template_name
        self.key_value["template_name"] = self.template_name
        self.key_value["violate"] = self.violate
        self.key_value["condition_line"] = self.condition_line


"""
DeclareParsedModel is dictionary type based class or it is a data model
which contains the information of about declare model which is parsed.
"""


class DeclareParsedDataModel(CustomUtilityDict):

    def __init__(self):
        super().__init__()
        self.events: Dict[str, DeclareModelEvent] = {}
        self.attributes_list: Dict[str, Dict] = {}
        self.template_constraints = {}
        self.templates: List[DeclareModelTemplateDataModel] = []
        self.encoded_model: DeclareModelCoder = None
        self.encoder: DeclareModelCoder = None
        self.update_props()
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

        event_name, event_type = (name, event_type)
        if event_name in self.events:
            raise KeyError(f"Multiple times the same activity [{event_name}] is declared")
        self.events[event_name] = DeclareModelEvent()
        self.events[event_name].name = event_name
        self.events[event_name].event_type = event_type

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
        if event_name not in self.events:
            raise ValueError(f"Unable to find the event or activity {event_name}")
        dme: DeclareModelEvent = self.events[event_name]
        attrs = dme.attributes
        if attrs is None:
            attrs = {}
            dme.attributes = attrs
        if attr_name in self.attributes_list:
            attrs[attr_name] = self.attributes_list[attr_name]  # saving the same reference. Same attr cannot have two values
        else:
            attrs[attr_name] = {"value": "", "value_type": ""}

        if attr_name not in self.attributes_list:
            # we save the reference of attributes in separate list
            # for improving computation
            self.attributes_list[attr_name] = attrs[attr_name]
            self.attributes_list[attr_name]["events_attached"] = [event_name]
        else:
            self.attributes_list[attr_name]["events_attached"].append(event_name)

    def add_attribute_value(self, attr_name: str, attr_type: DeclareModelAttributeType, attr_value: str):
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
        if attr_name not in self.attributes_list:
            raise ValueError(f"Unable to find attribute {attr_name}")
        attribute = self.attributes_list[attr_name]
        attribute["value"] = attr_value
        attribute["value_type"] = attr_type
        if attr_type == DeclareModelAttributeType.FLOAT:
            frm = str(attr_value).split(".")  # 10.587  # attribute["range_precision"] = len(frm[1])
            precision = len(frm[1])
            attribute["value"] = int((10 ** precision) * frm)
            attribute["range_precision"] = precision
        elif attr_type == DeclareModelAttributeType.INTEGER:
            attribute["range_precision"] = 0

        if attr_type == DeclareModelAttributeType.FLOAT_RANGE or attr_type == DeclareModelAttributeType.INTEGER_RANGE:
            pattern = re.compile(r"( \d+.?\d*)( and )?(\d+.?\d*)")
            match = pattern.findall(attr_value)
            # Extract the float values
            if match:
                (val1, val2) = (0, 0)
                if attr_type == DeclareModelAttributeType.INTEGER_RANGE:
                    val1 = int(match[0][0])
                    val2 = int(match[0][2])
                    attribute["range_precision"] = 0
                if attr_type == DeclareModelAttributeType.FLOAT_RANGE:
                    v = attr_value.replace("float between", "").replace("and", "---")
                    v = v.strip().split(" --- ")
                    # val1 = float(match[0][0])
                    # val2 = float(match[0][2])
                    val1 = float(v[0])
                    val2 = float(v[1])
                    attribute["range_precision"] = self.get_float_biggest_precision(val1, val2)
                attribute["from"] = val1
                attribute["to"] = val2

    def get_float_biggest_precision(self, v1: float, v2: float) -> int:
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

    def add_template(self, line: str, template: DeclareModelTemplate, cardinality: str, template_idx: int = None):
        templt = DeclareModelTemplateDataModel()
        self.templates.append(templt)
        templt.template = template
        templt.template_name = template.templ_str
        templt.template_line = line
        templt.template_index_id = template_idx or self.total_templates
        self.total_templates = self.total_templates + 1
        if template.supports_cardinality and int(cardinality) > 1:
            templt.template_name += str(cardinality)
        compiler = re.compile(r"^(.*)\[(.*)\]\s*(.*)$")
        al = compiler.fullmatch(line)
        if al is None:
            return
        if len(al.group()) >= 2:
            events = al.group(2).strip().split(",")  # A, B
            events = [e.strip() for e in events]  # [A, B]
            templt.activities = events
        if len(al.group()) >= 3:
            conditions = al.group(3).strip()
            if len(conditions) == 0:
                return
            if len(conditions) > 1 and not conditions.startswith("|"):
                raise SyntaxError(f"Unable to parse template {template.templ_str}'s conditions."
                                  f" Conditions should start with \"|\"")
            templt.condition_line = conditions
            conditions = conditions.strip("|")
            conds_list = conditions.split("|")
            templt.condition = [cl.strip() for cl in conds_list]
            conds_len = len(conds_list)
            if conds_len > 3:
                raise ValueError(f"Unable to parse the line due to the exceeds conditions (> 3)")

    def update_props(self):
        """
        Updates the _dict, so it has updated values when any dict op is occurred
        Returns
        -------

        """
        self.key_value["events"] = self.events
        self.key_value["attributes_list"] = self.attributes_list
        self.key_value["template_constraints"] = self.template_constraints
        self.key_value["templates"] = self.templates

    def encode(self) -> DeclareParsedDataModel:
        if self.encoded_model is None:
            self.encoded_model = DeclareModelCoder()
        return self.encoded_model.encode(self)

    def decode_value(self, name: str) -> str:
        if self.encoded_model is None:
            self.encoded_model = DeclareModelCoder()
        return self.encoded_model.decode_value(name)


class DeclareModelCoder:
    def __init__(self):
        self.encoded_dict: dict = {}
        self.model: DeclareParsedDataModel

    def encode(self, dpm_orig: DeclareParsedDataModel) -> DeclareParsedDataModel:
        self.encoded_dict = {}
        dpm = copy.deepcopy(dpm_orig)  # TODO: check this. to void to get messed with reference/pointers
        self.model = DeclareParsedDataModel()
        for event_name, event_obj in dpm.events.items():
            self.model.events[self.encode_event_name(event_name)] = event_obj
            for prop in event_obj:
                if prop == "name":
                    event_obj.name = self.encode_event_name(event_name)
                if prop == "event_type":
                    event_obj.event_type = self.encode_event_type(event_obj[prop])
                if prop == "attributes":
                    event_obj.attributes = self.encode_attributes_list(event_obj["attributes"])
        # self.encode_attributes_list(dpm.attributes_list)

        # self.model.templates = copy.deepcopy(dpm_orig.templates)
        self.model.templates = []
        for tmpl in dpm_orig.templates:
            template = DeclareModelTemplateDataModel()
            self.model.templates.append(template)
            template.template_name = tmpl["template_name"]
            template.template = tmpl["template"]
            template.activities = self.encode_str_list(tmpl["activities"])
            a, t, tm = tmpl.get_conditions()
            encoded_conditions = []
            if a is not None:
                # c = self.parsed_condition("A.grade > 10 and A.name in (x, y)  or A.grade < 3 and A.name in (z, v)
                # or A.name not in (4, 2, 6)")
                # c = self.parsed_condition("A.grade > 10 and A.name in (x, y) or A.name in (z, v) T.type > 78 or "
                # "t.nae is memo and (T.InfectionSuspected is true) AND"
                #                           " (T.SIRSCriteria2OrMore is true) AND (T.DiagnosticECG is true) ")
                encoded_conditions.append(self.parsed_condition(a))
            else:
                encoded_conditions.append("")
            if t is not None:
                encoded_conditions.append(self.parsed_condition(t))
            else:
                encoded_conditions.append("")
            if tm is not None:
                encoded_conditions.append(tm)
            template.condition = encoded_conditions
            template.violate = tmpl.violate
            template.template_index_id = tmpl.template_index_id
            template.condition_line = "| " + " | ".join(encoded_conditions)
            a = ", ".join(template.activities)
            template.template_line = f"{template.template_name}[{a}] {template.condition_line}"

        return self.model

    def encode_attributes_list(self, attr_list: Dict):
        d = {}
        for attr_name, attr_obj in attr_list.items():
            e_attr_name = self.encode_value(attr_name)
            self.model.attributes_list[e_attr_name] = attr_obj
            d[e_attr_name] = {}
            if attr_obj['value_type'] is DeclareModelAttributeType.ENUMERATION:
                attr_obj['value'] = self.encode_enum_list(attr_obj["value"])
            if 'events_attached' in attr_obj:
                attr_obj['events_attached'] = self.encode_str_list(attr_obj['events_attached'])
            d[e_attr_name] = attr_obj
        return d

    def parsed_condition(self, string: str):
        string = re.sub(r'\)', ' ) ', string)
        string = re.sub(r'\(', ' ( ', string)
        string = string.strip()
        string = re.sub(' +', ' ', string)
        string = re.sub('is not', 'is_not', string)
        string = re.sub('not in', 'not_in', string)
        string = re.sub(' *> *', '>', string)
        string = re.sub(' *< *', '<', string)
        string = re.sub(' *= *', '=', string)
        string = re.sub(' *<= *', '<=', string)
        string = re.sub(' *>= *', '>=', string)
        form_list = string.split(" ")
        for i in range(len(form_list) - 1, -1, -1):
            el = form_list[i]
            if el == 'in' or el == 'not_in':
                end_index = form_list[i:].index(')')
                start_index = i - 1
                end_index = end_index + i + 1
                form_list[start_index:end_index] = [' '.join(form_list[start_index:end_index])]
            elif el == 'is' or el == 'is_not':
                start_index = i - 1
                end_index = i + 2
                form_list[start_index:end_index] = [' '.join(form_list[start_index:end_index])]
        keywords = {'and', 'or', '(', ')', 'is', 'same', 'different'}
        idx = 0
        for cond_chunk in form_list:
            idx = idx + 1
            if cond_chunk.lower() in keywords:
                continue
            elif cond_chunk.lower() == "not_in":
                form_list[idx - 1] = "not in"
            elif re.match(r'^[AaTt]\.', cond_chunk):  # A.grade>10
                found = re.findall(r"([AaTt]\.([\w:,]+))", cond_chunk,
                                   flags=re.UNICODE | re.MULTILINE)  # finds from A.grade>10 => A.grade and grade
                if found:  # [('A.grade', 'grade'), ('A.mark', 'mark')]
                    for f in found:
                        act_tar_cond, attr = f
                        ct = act_tar_cond.split(".")[0]  # condition_type: A or T
                        attr_encoded = self.encode_value(attr)
                        form_list[idx - 1] = cond_chunk.replace(ct + "." + attr, ct + "." + attr_encoded)
                cond_chunk = form_list[idx - 1]
                cond_chunk_split = cond_chunk.lower().split(" ")  # A.name in ( z, v )
                if "is" in cond_chunk_split:
                    cond_chunk = cond_chunk.replace("  ", "").strip()
                    val = cond_chunk.split(" is ")  # case: T.InfectionSuspected is xyz
                    val0 = val[0]  # "T.InfectionSuspected"
                    val1 = self.encode_value(val[1])  # "xyz"
                    cond_chunk = val0 + " is " + val1
                    form_list[idx - 1] = cond_chunk
                elif "not_in" in cond_chunk_split:
                    cond_chunk = cond_chunk.replace("  ", "").strip()
                    val = cond_chunk.split(" not_in ")  # case: A.name not in ( z, v )
                    val1 = val[1].replace("(", "").replace(")", "").strip()  # "z, v"
                    val1 = [v.strip() for v in val1.split(",")]  # ["z", "v"]
                    items = []
                    for v in val1:
                        items.append(self.encode_value(v))
                    val1 = "(" + ", ".join(items) + ")"
                    cond_chunk = val[0] + " not in " + val1
                    form_list[idx - 1] = cond_chunk
                elif "in" in cond_chunk_split:
                    cond_chunk = cond_chunk.replace("  ", "").strip()
                    val = cond_chunk.split(" in ")  # case: A.name in ( z, v )
                    val1 = val[1].replace("(", "").replace(")", "").strip()  # "z, v"
                    val1 = [v.strip() for v in val1.split(",")]  # ["z", "v"]
                    items = []
                    for v in val1:
                        items.append(self.encode_value(v))
                    val1 = "(" + ", ".join(items) + ")"
                    cond_chunk = val[0] + " in " + val1
                    form_list[idx - 1] = cond_chunk
            else:
                raise ValueError(f"Unable to encode the {cond_chunk} condition. This is not supported to encode yet")
                # if matched

        return " ".join(form_list)

    def encode_event_name(self, s) -> str:
        return self.encode_value(s)

    def encode_event_type(self, s) -> str:
        return self.encode_value(s)

    def encode_enum_list(self, s) -> str:
        ss = s.split(",")
        ss = [self.encode_value(se) for se in ss]
        return ", ".join(ss)

    def encode_str_list(self, input_list: List[str]) -> List[str]:
        ss = []
        for se in input_list:
            if "ENCODEDSTRINGENCODEDSTRING" not in se:
                ss.append(self.encode_value(se))
            else:
                ss.append(se)
        return ss

    def encode_value(self, s) -> str:
        if "ENCODEDSTRINGENCODEDSTRING" in s:  # s is already encoded
            return s
        if s not in self.encoded_dict:
            v = base64.b64encode(s.encode())
            # v = v.decode("utf-8")
            # doesn't work because sm times has starts from a digit and clingo fails
            # v = hashlib.md5(s.encode()).hexdigest()
            # self.encoded_dict[s] = v
            b64_str = v.decode("utf-8")
            b64_str = b64_str.replace("=", "EEEQUALSIGNNN")
            if b64_str[0].isupper():
                b = b64_str[0]
                b = f"lowerlower{b}lowerlower"
                b64_str = b + b64_str[1:]
            # maybe sometimes maybe by bug we encode the string multiple times, we would like to decode
            # till last encoded str
            b64_str = b64_str + "ENCODEDSTRINGENCODEDSTRING"
            self.encoded_dict[s] = b64_str
        return self.encoded_dict[s]

    def decode_value(self, s: str) -> str:
        if not isinstance(s, str):
            return s
        if "ENCODEDSTRINGENCODEDSTRING" not in s:  # s doesn't have ENCODEDSTRINGENCODEDSTRING then its already decoded
            return s
        vals: [str] = list(self.encoded_dict.values())  # ["..", ".."]
        s = s.strip()
        if s in vals:
            idx = vals.index(s)
            if idx <= -1:
                return s
            s = s.replace("EEEQUALSIGNNN", "=")
            s = s.replace("ENCODEDSTRINGENCODEDSTRING", "=")
            if s.startswith("lowerlower"):
                s = s.replace("lowerlower", "")
            n_val = base64.b64decode(s)
            s = n_val.decode("utf-8")
            if s.__contains__("ENCODEDSTRINGENCODEDSTRING"):
                return self.decode_value(s)
        return s


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
                typ = DeclareModel.detect_declare_attr_value_type(value)
                for attr in attributes_list:
                    declare_parsed_model.add_attribute_value(attr, typ, value)
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
                        declare_parsed_model.add_template(line, template, cardinality)
        self.set_constraints()
        declare_parsed_model.template_constraints = self.constraints

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

