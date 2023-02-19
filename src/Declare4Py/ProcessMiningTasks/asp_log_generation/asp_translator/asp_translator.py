from __future__ import annotations

from src.declare4py.ProcessMiningTasks.asp_log_generation.asp_translator.declare_constraint_resolver import \
    DeclareModelConditionResolver2ASP
from src.declare4py.ProcessModels.DeclareModel import DeclareModelAttributeType
from src.declare4py.ProcessModels.DeclareModel import DeclareModel
from src.declare4py.ProcessModels.DeclareModel import DeclareModelTemplateDataModel

"""
Abductive logic programming (ALP) is a high-level knowledge-representation framework that can be used to solve
 problems declaratively based on abductive reasoning.
"""

"""
    ASP model contains the translated code of declare model. The ASP code in this model describe the problem
    representation in ASP.
"""


class TranslatedASPModel:

    def __init__(self, is_encoded: bool):
        self.lines: [str] = []
        self.extra_asp_line: [str] = []
        self.values_assignment: [str] = []
        self.attributes_values: [str] = []
        self.templates_s: [str] = []
        self.fact_names: [str] = []
        self.is_encoded: bool = is_encoded
        self.condition_resolver = DeclareModelConditionResolver2ASP(self.is_encoded)

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
            self.add_attribute_value_to_list(f'value({attr}, {value["value"]}).')
        elif value["value_type"] == DeclareModelAttributeType.FLOAT:
            self.add_attribute_value_to_list(f'value({attr}, {(value["value"])}).')
        elif value["value_type"] == DeclareModelAttributeType.INTEGER_RANGE:
            (frm, til) = (value["from"], value["to"])
            self.add_attribute_value_to_list(f'value({attr}, {frm}..{til}).')
        elif value["value_type"] == DeclareModelAttributeType.FLOAT_RANGE:
            frm = self.scale_number2int(value["from"], value["range_precision"])
            til = self.scale_number2int(value["to"], value["range_precision"])
            self.add_attribute_value_to_list(f'value({attr}, {frm}..{til}).')
        elif value["value_type"] == DeclareModelAttributeType.ENUMERATION:
            val = value["value"].split(",")
            if not is_encoded:
                val = [v.strip().lower() for v in val]
            else:
                val = [v.strip() for v in val]
            for s in val:
                self.add_attribute_value_to_list(f'value({attr}, {s}).')

    def scale_number2int(self, num: [int | float], num_to_scale: int) -> int:
        return int(num * (10 ** num_to_scale))

    def add_attribute_value_to_list(self, value: str):
        if value not in self.attributes_values:
            self.attributes_values.append(value)

    def add_template(self, name, ct: DeclareModelTemplateDataModel, props: dict[str, dict]):
        self.templates_s.append(f"template({ct.template_index_id},\"{name}\").")
        ls = self.condition_resolver.resolve_to_asp(ct, props, ct.template_index_id)
        if ls and len(ls) > 0:
            self.templates_s = self.templates_s + ls + ["\n"]

    def add_asp_line(self, line: str):
        self.extra_asp_line.append(line)

    def to_str(self):
        return self.__str__()

    def __str__(self) -> str:
        line = "\n".join(self.lines)
        line = line + "\n\n" + "\n".join(self.attributes_values)
        line = line + "\n\n" + "\n".join(self.templates_s)
        line = line + "\n\n" + "\n".join(self.extra_asp_line)
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

    def from_decl_model(self, model: DeclareModel, use_encoding: bool = True,
                        constraint_violation: dict = None) -> TranslatedASPModel:
        """
        Translate to declare model into LP model or ASP which is, then, fed into Clingo.
        Parameters
        ----------
        model: Declare model
        use_encoding: encode event, activities, attributes. Since clingo doesn't support some chars so we need to encode it
        constraint_violation: dictionary with two keyvalue pair: { constraint_violation: bool, violate_all_constraints: bool }.
         `constraint_violation` indicates whether violation feature should be enabled or not, `violate_all_constraints`
          indicates whether all the constraints mentioned in the list should be violated (True) or some of them (False)
          and when the value is False, the constraints are chosen by clingo itself to violate.
          The `violate_all_constraints` works only if `constraint_violation` is set to True.

        Returns
        -------
        TranslatedASPModel
        """
        if use_encoding:
            keys = model.parsed_model.encode()
        else:
            keys = model.parsed_model
        self.asp_model = TranslatedASPModel(use_encoding)
        for k in keys.events:
            event = keys.events[k]
            self.asp_model.define_predicate(event.name, event.event_type, use_encoding)
            attrs = event.attributes
            for attr in attrs:
                self.asp_model.define_predicate_attr(event.name, attr, use_encoding)
                dopt = attrs[attr]
                self.asp_model.set_attr_value(attr, dopt, use_encoding)
        constraints_violate = {}
        for ct in keys.templates:
            self.asp_model.add_template(ct.template_name, ct, keys.attributes_list)
            constraints_violate[ct.template_index_id] = ct.violate

        if constraint_violation is not None and 'constraint_violation' in constraint_violation and\
                constraint_violation['constraint_violation']:
            # if model.violate_all_constraints_in_subset:
            if 'violate_all_constraints' in constraint_violation and constraint_violation['violate_all_constraints']:
                for idx, violate in constraints_violate.items():
                    if violate:
                        self.asp_model.add_asp_line(f"unsat({idx}).")
                    else:
                        self.asp_model.add_asp_line(f"sat({idx}).")
            else:
                isConstraintViolated = False
                s = ":-"
                for idx, val in constraints_violate.items():
                    if val:
                        s = s + f'sat({idx}), '
                        isConstraintViolated = True
                    else:
                        self.asp_model.add_asp_line(f"sat({idx}).")
                s = s.strip().rstrip(',')
                if isConstraintViolated:
                    self.asp_model.add_asp_line(s + '.')
        else:
            for ct in keys.templates:
                self.asp_model.add_asp_line(f'sat({ct.template_index_id}).')  # no constraints to violate

        return self.asp_model

