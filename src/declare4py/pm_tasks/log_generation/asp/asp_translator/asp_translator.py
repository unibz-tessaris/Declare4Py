from __future__ import annotations

from src.declare4py.pm_tasks.log_generation.asp.asp_translator.declare_constraint_resolver import \
    DeclareModalConditionResolver2ASP
from src.declare4py.process_models.decl_model import DeclareModelAttributeType, DeclareModelTemplateDataModel, \
    DeclModel, DeclareParsedDataModel

"""
Abductive logic programming (ALP) is a high-level knowledge-representation framework that can be used to solve
 problems declaratively based on abductive reasoning.
"""


"""
    ASP model contains the translated code of declare model. The ASP code in this model describe the problem
    representation in ASP.
"""


class TranslatedASPModel:
    def __init__(self, scale_number: int, is_encoded: bool):
        self.lines: [str] = []
        self.values_assignment: [str] = []
        self.attributes_values: [str] = []
        self.templates_s: [str] = []
        self.fact_names: [str] = []
        self.fact_names: [str] = []
        self.scale_number: int = scale_number
        self.is_encoded: bool = is_encoded

    def define_predicate(self, name: str, predicate_name: str, is_encoded: bool = True):
        if not is_encoded:
            self.lines.append(f'{predicate_name}({name.lower()}).')
        else:
            self.lines.append(f'{predicate_name}({name}).')
        self.fact_names.append(predicate_name)

    def define_predicate_attr(self, event_name: str, attr_name: str, is_encoded: bool = True):
        if not is_encoded:
            attr_name = attr_name.lower()
            self.lines.append(f'has_attribute({event_name.lower()}, {attr_name}).')
            self.values_assignment.append(f'has_attribute({event_name.lower()}, {attr_name}).')
        else:
            self.lines.append(f'has_attribute({event_name}, {attr_name}).')
            self.values_assignment.append(f'has_attribute({event_name}, {attr_name}).')

    def set_attr_value(self, attr: str, value: dict, is_encoded: bool = True):
        if not is_encoded:
            attr = attr.lower()
        if value["value_type"] == DeclareModelAttributeType.INTEGER:
            self.add_attribute_value_to_list(f'value({attr}, {self.scale_number2int(value["value"])}).')
        elif value["value_type"] == DeclareModelAttributeType.FLOAT:
            self.add_attribute_value_to_list(f'value({attr}, {self.scale_number2int(value["value"])}).')
        elif value["value_type"] == DeclareModelAttributeType.INTEGER_RANGE:
            frm, til = self.__parse_range_value(value["value"])
            frm = self.scale_number2int(frm)
            til = self.scale_number2int(til)
            self.add_attribute_value_to_list(f'value({attr}, {frm}..{til}).')
        elif value["value_type"] == DeclareModelAttributeType.FLOAT_RANGE:
            frm, til = self.__parse_range_value(value["value"])
            frm = self.scale_number2int(frm)
            til = self.scale_number2int(til)
            self.add_attribute_value_to_list(f'value({attr}, {frm}..{til}).')
        elif value["value_type"] == DeclareModelAttributeType.ENUMERATION:
            val = value["value"].split(",")
            if not is_encoded:
                val = [v.strip().lower() for v in val]
            else:
                val = [v.strip() for v in val]
            for s in val:
                self.add_attribute_value_to_list(f'value({attr}, {s}).')

    def scale_number2int(self, num: [int | float]) -> int:
        # if isinstance(num, int) or isinstance(num, float):
        if isinstance(num, str):
            if num.__contains__('.'):
                num = float(num)
            else:
                num = int(num)
        return int(num * self.scale_number)

    def add_attribute_value_to_list(self, value: str):
        if value not in self.attributes_values:
            self.attributes_values.append(value)

    def __parse_range_value(self, value: str):
        v = value.lower().replace("integer", "")\
            .replace("float", "")\
            .replace("between", "") \
            .replace("and", "") \
            .replace("  ", " ") \
            .strip()
        (frm, til) = v.split(" ")
        return frm, til

    def add_template(self, name, ct: DeclareModelTemplateDataModel, idx: int, props: dict[str, dict]):
        self.templates_s.append(f"template({idx},\"{name}\").")
        dc = DeclareModalConditionResolver2ASP(self.scale_number, self.is_encoded)
        ls = dc.resolve_to_asp(ct, props, idx)
        if ls and len(ls) > 0:
            self.templates_s = self.templates_s + ls + ["\n"]

    def to_str(self):
        return self.__str__()

    def __str__(self) -> str:
        line = "\n".join(self.lines)
        line = line + "\n\n" + "\n".join(self.attributes_values)
        line = line + "\n\n" + "\n".join(self.templates_s)
        return line

    def __repr__(self):
        return f"{{ \"total_facts\": \"{len(self.lines) - len(self.values_assignment)}\"," \
               f" \"values_assignment\": \"{len(self.values_assignment)}\" }}"


class ASPTranslator:
    """
    ASP interpreter reads the data from the decl_model and converts it into ASP, as defining the problem
    """
    def __init__(self) -> None:
        self.asp_model: TranslatedASPModel

    def from_decl_model(self, model: DeclModel, use_encoding: bool = True) -> TranslatedASPModel:
        if use_encoding:
            keys = model.parsed_model.encode()
        else:
            keys = model.parsed_model
        scalable_precision = self.get_float_biggest_precision(keys)
        self.asp_model = TranslatedASPModel(10 ** (scalable_precision - 1), use_encoding)

        for k in keys.events:
            event = keys.events[k]
            self.asp_model.define_predicate(event.name, event.event_type, use_encoding)
            attrs = event.attributes
            for attr in attrs:
                self.asp_model.define_predicate_attr(event.name, attr, use_encoding)
                dopt = attrs[attr]
                self.asp_model.set_attr_value(attr, dopt, use_encoding)
        templates_idx = 0
        for ct in keys.templates:
            self.asp_model.add_template(ct.template_name, ct, templates_idx, keys.attributes_list)
            # template_line.append(f"template({templates_idx},\"{tmp_name}\")")
            templates_idx = templates_idx + 1
        return self.asp_model

    def get_float_biggest_precision(self, model: DeclareParsedDataModel) -> int:
        attr_list = model.attributes_list
        decimal_len_list = []
        for attr in attr_list:
            attr_dict = attr_list[attr]
            if attr_dict["value_type"] == DeclareModelAttributeType.FLOAT_RANGE or attr_dict["value_type"] == DeclareModelAttributeType.INTEGER_RANGE:
                v = attr_dict["value"].lower().replace("integer", "") \
                    .replace("float", "") \
                    .replace("between", "") \
                    .replace("and", "") \
                    .replace("  ", " ") \
                    .strip()
                (frm, til) = v.split(" ")
                precision = 1
                frm = frm.split(".")  # 10.587
                if len(frm) > 1:
                    precision = len(frm[1])  # frm[1] = 587 and length would be 3
                til = til.split(".")
                if len(til) > 1:
                    precision = max(len(til[1]), precision)
                decimal_len_list.append(precision)
        return max(decimal_len_list)