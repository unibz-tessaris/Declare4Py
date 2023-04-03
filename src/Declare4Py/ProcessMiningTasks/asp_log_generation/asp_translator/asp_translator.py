from __future__ import annotations

import typing

from src.Declare4Py.ProcessMiningTasks.asp_log_generation.asp_translator.declare_constraint_resolver import \
    DeclareModelConditionResolver2ASP
from src.Declare4Py.ProcessModels.DeclareModel import DeclareModelAttributeType, DeclareModelEvent, DeclareModelAttr
from src.Declare4Py.ProcessModels.DeclareModel import DeclareModel
from src.Declare4Py.ProcessModels.DeclareModel import DeclareModelConstraintTemplate

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

    def define_predicate(self, name: str, predicate_name: str):
        """ create ASP predicate string and append to "string builder" """
        self.lines.append(f'{predicate_name}({name}).')
        self.fact_names.append(predicate_name)

    def define_predicate_attr(self, event_name: str, attr_name: str):
        """ Define declare model attribute in ASP string and append to "string builder" """
        self.lines.append(f'has_attribute({event_name}, {attr_name}).')
        self.values_assignment.append(f'has_attribute({event_name}, {attr_name}).')

    def set_attr_value(self, attr: DeclareModelAttr, is_encoded: bool = True):
        """ Set attribute value and append to "string builder" """
        attr_name = attr.attr_name.get_encoded_name() if is_encoded else attr.attr_name.get_name()
        attr_val_typ = attr.attr_value.attribute_value_type
        if attr_val_typ is not DeclareModelAttributeType.ENUMERATION:
            frm, til = attr.attr_value.get_precisioned_value()
            self.add_attribute_value_to_list(f'value({attr_name}, {frm}..{til}).')
        else:
            values = attr.attr_value.get_precisioned_value()
            if values is not None and len(values) > 0:
                for v in values:
                    val_name = v.get_encoded_name() if is_encoded else v.get_name()
                    self.add_attribute_value_to_list(f'value({attr_name}, {val_name}).')

    def scale_number2int(self, num: typing.Union[int, float], num_to_scale: int) -> int:
        """ Scale float value to integer """
        return int(num * (10 ** num_to_scale))

    def add_attribute_value_to_list(self, value: str):
        """ Create ASP list of values """
        if value not in self.attributes_values:
            self.attributes_values.append(value)

    def add_template(self, ct: DeclareModelConstraintTemplate, props: dict[str, DeclareModelAttr]):
        """
        Parse declare model template into ASP
        """
        self.templates_s.append(f"template({ct.template_index},\"{ct.get_template_name()}\").")

        ls = self.condition_resolver.resolve_to_asp(ct, props)
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

    def from_decl_model(self, decl_model: DeclareModel, use_encoding: bool = True,
                        constraint_violation: dict = None) -> TranslatedASPModel:
        """
        Translate to declare model into LP model or ASP which is, then, fed into Clingo.
        Parameters
        ----------
        decl_model: Declare model
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
        model = decl_model.parsed_model
        self.asp_model = TranslatedASPModel(use_encoding)
        for event_type in model.events:
            for ev_nm in model.events[event_type]:
                ev: DeclareModelEvent = model.events[event_type][ev_nm]
                self.asp_model.lines.append("")
                if use_encoding:
                    self.asp_model.define_predicate(ev.event_name.get_encoded_name(), ev.event_type.get_encoded_name())
                else:
                    self.asp_model.define_predicate(ev.event_name.get_name(), ev.event_type.get_name())
                attrs = ev.attributes
                if attrs:
                    for attr in attrs:
                        if use_encoding:
                            self.asp_model.define_predicate_attr(ev.event_name.get_encoded_name(),
                                                                 attrs[attr].attr_name.get_encoded_name())
                        else:
                            self.asp_model.define_predicate_attr(ev.event_name.get_name(),
                                                                 attrs[attr].attr_name.get_name())
                        self.asp_model.set_attr_value(attrs[attr], use_encoding)
        constraints_violate = {}

        for template_idx in model.templates:
            ct = model.templates[template_idx]
            self.asp_model.add_template(ct, model.attributes_list)
            constraints_violate[template_idx] = ct.violate

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
            for idx in model.templates:
                self.asp_model.add_asp_line(f'sat({idx}).')  # no constraints to violate
        return self.asp_model
