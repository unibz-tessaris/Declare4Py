from __future__ import annotations

import re
import typing

import boolean

from src.declare4py.process_models.decl_model import DeclareTemplateModalDict, DeclareModelAttributeType


class DeclareModalConditionResolver2ASP:

    def __init__(self, scale_num: int, is_encoded: bool = False):
        self.number_scaler = scale_num
        self.is_encoded = is_encoded

    def resolve_to_asp(self, ct: DeclareTemplateModalDict, attrs: dict, idx: int = 0):
        ls = []
        activation, target_cond, time = ct.get_conditions()
        if activation:
            ls.append('activation({},{}).'.format(idx, ct.activities[0].lower()))
            exp, n2c, c2n = self.parsed_condition('activation', activation)
            conditions = set(n2c.keys())
            if exp.isliteral:
                nm = str(exp).strip()
                if len(nm) == 0:
                    ls.append('activation_condition({},T).'.format(idx))
                else:
                    ls.append('activation_condition({},T):- {}({},T).'.format(idx, nm, idx))
            s = self.tree_conditions_to_asp("activation", exp, "activation_condition", idx, conditions)
            if s and len(s) > 0:
                ls = ls + s
            for n, c in n2c.items():
                s = self.condition_to_asp(n, c, idx, attrs)
                if s and len(s) > 0:
                    ls = ls + s
        if target_cond:
            target = ct.activities[1]
            ls.append('target({},{}).'.format(idx, target.lower()))
            exp, n2c, c2n = self.parsed_condition('correlation', target_cond)
            conditions = set(n2c.keys())
            if exp.isliteral:
                ls.append('correlation_condition({},T):- {}({},T).'.format(idx, str(exp), idx))
            s = self.tree_conditions_to_asp("correlation", exp, "correlation_condition", idx, conditions)
            if s and len(s) > 0:
                ls = ls + s
            for n, c in n2c.items():
                s = self.condition_to_asp(n, c, idx, attrs)
                if s and len(s) > 0:
                    ls = ls + s
        return ls

    def condition_to_asp(self, name, cond, i, attrs):
        name = name + '({},T)'.format(i)
        string = re.sub('is not', 'is_not', cond)
        string = re.sub('not in', 'not_in', string)
        if cond.__contains__("."):
            attr = cond.split(".")[1].strip()  # A.grade>2
        else:
            attr = cond
        attr = re.search(r'\w+', attr)
        ls = []
        if attr:
            attr = attr.group(0).strip()
            if attr not in attrs:
                raise ValueError(f"Unable to find the attribute \"{attr}\" in condition \"{cond}\". name: \"{name}\"")
            attr_obj = attrs[attr]
            value_typ = attr_obj["value_type"]
            if value_typ == DeclareModelAttributeType.ENUMERATION:  # ["is_range_typ"]:  # Enumeration
                cond_type = cond.split(' ')[1]
                if cond_type == 'is':
                    v = string.split(' ')[2]
                    if not self.is_encoded:
                        v = v.lower()
                        attr = attr.lower()
                    s = 'assigned_value({},{},T)'.format(attr, v)
                    ls.append('{} :- {}.'.format(name, s))
                elif cond_type == 'is_not':
                    v = string.split(' ')[2]
                    if not self.is_encoded:
                        v = v.lower()
                        attr = attr.lower()
                    s = 'time(T), not assigned_value({},{},T)'.format(attr, v)
                    ls.append('{} :- {}.'.format(name, s))
                elif cond_type == 'in':
                    for value in string.split(' ')[2][1:-1].split(','):
                        v = value
                        if not self.is_encoded:
                            v = v.lower()
                            attr = attr.lower()
                        asp_cond = 'assigned_value({},{},T)'.format(attr, v)
                        ls.append('{} :- {}.'.format(name, asp_cond))
                # TODO:
                else:
                    asp_cond = 'time(T),'
                    if not self.is_encoded:
                        attr = attr.lower()
                    for value in cond.split(' ')[2][1:-1].split(','):
                        if not self.is_encoded:
                            value = value.lower()
                        asp_cond = asp_cond + 'not assigned_value({},{},T),'.format(attr, value)
                    asp_cond = asp_cond[:-1]
                    ls.append('{} :- {}.'.format(name, asp_cond))
            elif value_typ == DeclareModelAttributeType.INTEGER or value_typ == DeclareModelAttributeType.FLOAT or \
                    value_typ == DeclareModelAttributeType.INTEGER_RANGE or \
                    value_typ == DeclareModelAttributeType.FLOAT_RANGE:
                relations = ['<=', '>=', '=', '<', '>']
                for rel in relations:
                    if rel in cond:
                        value = string.split(rel)[1]
                        value = self.scale_number2int(value)
                        ls.append('{} :- assigned_value({},V,T),V{}{}.'.format(name, attr, rel, str(value)))
                        break
        return ls

    def parsed_condition(self, condition: typing.Literal['activation', 'correlation'], string: str):
        # s = self.parse_data_cond_to_pycond(string)
        return self.parsed_condition_2(condition, string)

    def parse_data_cond_to_pycond(self, cond: str):  # TODO: could be improved using recursion ?
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

    def parsed_condition_2(self, condition: typing.Literal['activation', 'correlation'], string: str):
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

        for i in range(len(form_list)):
            el = form_list[i]
            if '(' in el and ')' in el:
                el = re.sub(r'\( ', '(', el)
                el = re.sub(', ', ',', el)
                el = re.sub(r' \)', ')', el)
                form_list[i] = el

        keywords = {'and', 'AND', 'OR', 'or', '(', ')'}
        c = 0
        name_to_cond = dict()
        cond_to_name = dict()
        for el in form_list:
            if el not in keywords:
                c = c + 1
                name_to_cond[condition + '_condition_' + str(c)] = el
                cond_to_name[el] = condition + '_condition_' + str(c)
        form_string = ''
        for el in form_list:
            if el in cond_to_name:
                form_string = form_string + cond_to_name[el] + ' '
            else:
                form_string = form_string + el + ' '
        algebra = boolean.BooleanAlgebra()
        # print("form_list", form_list)
        # print("form_string", form_string)
        # print("condition", condition)
        # print("str", string)
        expression = algebra.parse(form_string, simplify=True)
        return expression, name_to_cond, cond_to_name

    def tree_conditions_to_asp(self, condition: typing.Literal['activation', 'correlation'],
                               expression, cond_name: str, i, conditions_names,
                               lp_st=None) -> typing.List[str] | None:
        if lp_st is None:
            lp_st = []

        def expression_to_name(expression):
            if expression.isliteral:
                condition_name = str(expression)
            else:
                condition_name = condition + '_condition_' + ''.join(
                    [str(symbol).split('_')[2] for symbol in expression.get_symbols()])
                while condition_name in conditions_names:
                    condition_name = condition_name + '_'
                conditions_names.add(condition_name)
            return condition_name + '({},T)'.format(i)

        def no_params(arg_name):
            return arg_name.split('(')[0]

        if expression.isliteral:
            return
        cond_name = cond_name + '({},T)'.format(i)
        formula_type = expression.operator
        formula_args = expression.args
        if formula_type == '|':
            for arg in formula_args:
                arg_name = expression_to_name(arg)
                lp_st.append('{} :- {}.'.format(cond_name, arg_name))
                self.tree_conditions_to_asp(condition, arg, no_params(arg_name), i, conditions_names, lp_st)
        if formula_type == '&':
            args_name = ''
            for arg in formula_args:
                arg_name = expression_to_name(arg)
                args_name = args_name + arg_name + ','
            args_name = args_name[:-1]  # remove last comma
            lp_st.append('{} :- {}.'.format(cond_name, args_name))
            for arg in formula_args:
                arg_name = expression_to_name(arg)
                self.tree_conditions_to_asp(condition, arg, no_params(arg_name), i, lp_st)
        return lp_st

    def scale_number2int(self, num: [int | float]) -> int:
        # if isinstance(num, int) or isinstance(num, float):
        if isinstance(num, str):
            if num.__contains__('.'):
                num = float(num)
            else:
                num = int(num)
        return int(num * self.number_scaler)
