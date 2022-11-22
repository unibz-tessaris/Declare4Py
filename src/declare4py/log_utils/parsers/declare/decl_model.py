from __future__ import annotations

import json
import re
from enum import Enum
import base64
import hashlib
import copy


from abc import ABC, abstractmethod
from src.declare4py.log_utils.ltl_model import LTLModel
# from src.declare4py.log_utils.parsers.declare.declare_parsers_utility import DeclareParserUtility
# from src.declare4py.log_utils.parsers.declare.declare_parsers import DeclareParser
from src.declare4py.mp_constants import Template


class DeclareModelCustomDict(dict, ABC):
    """
    Custom DICT helper class: printable and serializable object
    """
    def __init__(self, *args, **kw):
        super().__init__()
        self.key_value = dict(*args, **kw)

    def __getitem__(self, key):
        self.update_props()
        return self.key_value[key]

    def __setitem__(self, key, value):
        self.key_value[key] = value

    def __iter__(self):
        self.update_props()
        return iter(self.key_value)

    def __len__(self):
        self.update_props()
        return len(self.key_value)

    def __delitem__(self, key):
        self.update_props()
        del self.key_value[key]

    def __str__(self):
        self.update_props()
        # return json.dumps(self, default=lambda o: o.__dict__,)
        # return json.dumps(self.key_value, default=lambda o: self.default_json(o))
        # return json.dumps(self)
        return str(self.key_value)

    def to_json(self, pure=False) -> str:
        if pure:
            return json.dumps(self.key_value)
        st = str(self.key_value).replace("'", '"')
        return str(st)
        # return json.dumps(json.loads(st))
        # return o.__dict__
        # return "33"

    def __repr__(self):
        return self.__str__()

    @abstractmethod
    def update_props(self):
        pass


class DeclareModelAttributeType(str, Enum):
    INTEGER = "integer"
    FLOAT = "float"
    INTEGER_RANGE = "integer_range"
    FLOAT_RANGE = "float_range"
    ENUMERATION = "enumeration"

    def __str__(self):
        return self.value

    def __repr__(self):
        return "\""+self.__str__()+"\""


class DeclareModelEvent(DeclareModelCustomDict):
    name: str
    event_type: str
    attributes: dict[str, dict]

    def __init__(self):
        super().__init__()
        self.name = ""
        self.event_type = ""
        self.attributes = {}
        self.update_props()

    def update_props(self):
        self.key_value["name"] = self.name
        self.key_value["event_type"] = self.event_type
        self.key_value["attributes"] = self.attributes


class DeclareTemplateModalDict(DeclareModelCustomDict):
    template: Template | None
    template_name: str | None
    activities: str | None
    condition: [str] | None
    template_line: str | None
    condition_line: str | None  # |A.grade < 2  | T.mark > 2|1,5,s

    def __init__(self):
        super().__init__()
        self.template = None
        self.activities = None
        self.condition = None
        self.template_name = None

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
        self.key_value["template_line"] = self.template_line
        self.key_value["condition_line"] = self.condition_line


class DeclareParsedModel(DeclareModelCustomDict):
    attributes_list: dict[str, dict] = []
    events: dict[str, DeclareModelEvent] = {}
    template_constraints = {}
    templates: [DeclareTemplateModalDict] = []
    encoder: DeclareParsedModelEncoder
    encoded_model: DeclareParsedModelEncoder

    def __init__(self):
        super().__init__()
        self.events = {}
        self.attributes_list = {}
        self.template_constraints = {}
        self.templates = []
        self.encoded_model = None
        self.update_props()

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

    def add_template(self, line: str, template: Template, cardinality: str):
        templt = DeclareTemplateModalDict()
        self.templates.append(templt)
        templt.template = template
        templt.template_name = template.templ_str
        templt.template_line = line
        if template.supports_cardinality:
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

    def encode(self) -> DeclareParsedModel:
        if self.encoded_model is None:
            self.encoded_model = DeclareParsedModelEncoder()
        return self.encoded_model.encode(self)

    def decode_value(self, name: str) -> str:
        if self.encoded_model is None:
            self.encoded_model = DeclareParsedModelEncoder()
        return self.encoded_model.decode_value(name)


class DeclareParsedModelEncoder:
    encoded_dict = {}
    model: DeclareParsedModel

    def encode(self, dpm_orig: DeclareParsedModel) -> DeclareParsedModel:
        self.encoded_dict = {}
        dpm = copy.deepcopy(dpm_orig)  # TODO: check this. to void to get messed with reference/pointers
        self.model = DeclareParsedModel()
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
            template = DeclareTemplateModalDict()
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
            template.condition_line = "| " + " | ".join(encoded_conditions)
            a = ", ".join(template.activities)
            template.template_line = f"{template.template_name}[{a}] {template.condition_line}"

        return self.model

    def encode_attributes_list(self, attr_list: dict):
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
                found = re.findall(r"([AaTt]\.([\w:,]+))", cond_chunk, flags=re.UNICODE | re.MULTILINE)  # finds from A.grade>10 => A.grade and grade
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

    def encode_str_list(self, lst: [str]) -> [str]:
        ss = []
        for se in lst:
            if "ENCODEDSTRINGENCODEDSTRING" not in se:
                ss.append(self.encode_value(se))
            else:
                ss.append(se)
        return ss

    def encode_value(self, s) -> str:
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


class DeclModel(LTLModel):
    parsed_model: DeclareParsedModel

    def __init__(self):
        super().__init__()
        self.activities = []
        self.serialized_constraints = []
        self.constraints = []
        # self.parsed_model = DeclareParsedModel()

    def set_constraints(self):
        constraint_str = ''
        if len(self.constraints) > 0:
            for constraint in self.constraints:
                constraint_str = constraint['template'].templ_str
                if constraint['template'].supports_cardinality:
                    constraint_str += str(constraint['n'])
                constraint_str += '[' + ", ".join(constraint["activities"]) + '] |' + ' |'.join(constraint["condition"])
                self.serialized_constraints.append(constraint_str)

    def get_decl_model_constraints(self):
        return self.serialized_constraints

    def __str__(self):
        st = f"""{{"activities": {self.activities}, "serialized_constraints": {self.serialized_constraints},\
        "constraints": {self.constraints}, "parsed_model": {self.parsed_model.to_json()} }} """
        return st.replace("'", '"')
