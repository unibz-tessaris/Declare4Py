from __future__ import annotations

import dataclasses
import re
import typing
import warnings
from enum import Enum
from typing import Literal
from types import GenericAlias


try:
    import graphviz
except:
    raise warnings.warn("Unable to load graphviz library. Declare model Constraint"
                        " condition will will not generete the tree views")


class CONDITION_NODE_TYPE(Enum):
    PARENTHESIS = "PARENTHESIS"
    AND = "AND"
    OR = "OR"
    VALUE = "VALUE"


class DECLARE_LOGIC_OP(str, Enum):

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__) + 1
        obj = str.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, operator_name: str, token: str, symbol: str):
        self.operator = operator_name
        self.token = token
        self.symbol = symbol

    AND = "and", "AND", "and"  # TODO: don't yet whether declare model can have && sybmol as and
    OR = "or", "OR", "or"  # TODO: don't yet whether declare model can have || sybmol as or
    GT = "greater_then", "GT", ">"
    GEQ = "greater_eq", "GEQ", ">="
    LT = "less_then", "LT", "<"
    LEQ = "less_eq", "LEQ", "<="
    EQ = "equal", "EQ", "="  # TODO: would be converted in "is"
    NEQ = "not_equal", "NEQ", "!="  # TODO: should convert into  is not

    IS = "is", "IS", "is"
    IS_NOT = "is not", "IS_NOT", "is not"
    IN = "in", "IN", "in"
    IN_NOT = "not in", "NOT_IN", "not in"

    SAME = "same", "SAME", "same"  # TODO: not implemented yet
    different = "different", "DIFFERENT", "different"  # TODO: not implemented yet
    exist = "exist", "EXIST", "exist"  # TODO: not implemented yet

    @classmethod
    def get_logic_op_from_string(cls, name):
        return next(filter(lambda t: t.operator == name, DECLARE_LOGIC_OP), None)

    @classmethod
    def get_token(cls, token: str):
        token = re.sub(" +", " ", token)
        token = re.sub(" ", "_", token)
        return tuple(filter(lambda t: t.token.lower() == token.lower(), DECLARE_LOGIC_OP))

    def __str__(self):
        return "<LOGIC_OP:" + str(self.operator) + ": " + str(self.value) + " >"

    def __repr__(self):
        return "\"" + str(self.__str__()) + "\""


class ConditionNodes:
    def __init__(self, parent: ConditionNodes, value: str, children: [ConditionNodes] | None, idx: int = 0):
        self.children = [] if children is None else children
        self.parent = parent
        self.value = value
        self.idx = idx

    def node_type(self) -> str:
        if self.value == "(" or self.value == ")":
            return CONDITION_NODE_TYPE.PARENTHESIS.value
        if self.value.lower() == "and":
            return CONDITION_NODE_TYPE.AND.value
        if self.value.lower() == "or":
            return CONDITION_NODE_TYPE.OR.value
        return CONDITION_NODE_TYPE.VALUE.value

    def is_root(self) -> bool:
        return self.parent is None


class ParenthesisConditionResolverTree:
    """
        Each node in this tree can represent one of the following thing parenthesis, and, or, val.
        Val is the condition i.e such as "a>3", "a in (x,y,z)" etc.
        This helps us to parse the parenthesis in the given condition.
    """

    def __init__(self,
                 parent: ParenthesisConditionResolverTree | None,
                 parenthesis: bool = False,
                 is_and: bool = False,
                 is_or: bool = False,
                 is_val: str = "",
                 children: [ParenthesisConditionResolverTree] | None = None
                 ):
        if children is None:
            children = []
        self.is_parenthesis: bool = parenthesis
        self.is_and: bool = is_and
        self.is_or: bool = is_or
        self.is_val: str = is_val
        self.children: [ParenthesisConditionResolverTree] = children
        self.parent: ParenthesisConditionResolverTree = parent
        self.idx = 0

    def get_bottom_up_length(self, c: ParenthesisConditionResolverTree, idx: int = 0):
        if c is None:
            return idx
        if c.parent is None:
            return idx
        idx = 1 + c.parent.get_bottom_up_length(c.parent, idx)
        return idx

    def show(self):
        dot = graphviz.Digraph(comment="Graph", format="svg")
        self.generate_view(dot)
        dot.render('digraph.gv', view=True)

    def generate_view(self, dot: graphviz.Digraph):
        node_id = str(self.idx)
        dot.node(node_id, self.get_type_of_node())
        if len(self.children) > 0:
            for idx, child in enumerate(self.children):
                child.generate_view(dot)
            for idx, child in enumerate(self.children):
                dot.edge(node_id, str(child.idx))

    def vertices(self, ct: ParenthesisConditionResolverTree | None = None):
        if ct is None:
            ct = self
        v = 0
        if len(ct.children) > 0:
            for idx, child in enumerate(ct.children):
                v = v + child.vertices(child)
        return v + len(ct.children)

    def parent_condition_node(self):
        if self.parent is None:
            return None
        return ConditionNodes(self.parent.parent_condition_node(), self.parent.is_val, self.parent.children)


    def to_condition_node(self):
        pass

    def get_type_of_node(self) -> str:
        if self.is_parenthesis:
            return "(...)"
        if self.is_and:
            return "AND"
        if self.is_or:
            return "OR"
        if len(self.is_val) > 0:
            return self.is_val
        return "UNKNOWN"

    def get_node_value(self) -> str:
        if self.is_parenthesis:
            return "("
        if self.is_or:
            return "or"
        if self.is_and:
            return "and"
        return self.is_val


    def __str__(self):
        spaces = "-" * self.get_bottom_up_length(self, 0) + "->"
        s = spaces
        # s = s + f"Total Children: {len(self.children)}"
        # s = s + f" parenthesis={self.is_parenthesis}, AND={self.is_and}, OR={self.is_or}"
        # s = s + f" -> {self.is_val}  idx: {self.idx}"
        if self.is_parenthesis:
            s = s + f"({self.is_val}"
        else:
            s = s + f"{self.is_val}"
        s = s + "\n"
        for child in self.children:
            s = s + child.__str__()
            # s = s + "\n"
        if self.is_parenthesis:
            s = s + spaces + f")\n"
        return s


class LogicalOperatorNode:
    node_type: Literal["OR", "AND"] = "OR"
    pass


class ORLogicalOperatorNode(LogicalOperatorNode):
    node_type = "OR"
    conditions: [ConditionNodes] = []


class DeclareConditionTokenizer:
    # operatorsRegex = r" *(is_not|is|not_in|in|or|and|not|same|different|exist|<=|>=|<|>|=|!=) *"
    operatorsRegex = r" *(is_not|is|not_in|in|or|and|not|<=|>=|<|>|=|!=) *"

    def __normalize_condition(self, condition: str) -> str:
        string = re.sub(r'\)', ' ) ', condition)
        string = re.sub(r'\(', ' ( ', string)
        string = string.strip()
        string = re.sub(' +', ' ', string)
        string = re.sub(r'is not', 'is_not', string)
        string = re.sub(r'not in', 'not_in', string)
        string = re.sub(r' *> *', '>', string)
        string = re.sub(r' *< *', '<', string)
        string = re.sub(r' *= *', '=', string)
        string = re.sub(r' *!= *', '!=', string)
        string = re.sub(r' *is *', '=', string)
        string = re.sub(r' *is *not *', '!=', string)
        string = re.sub(r' *<= *', '<=', string)
        string = re.sub(r' *>= *', '>=', string)
        return string

    def parse_to_tree(self, condition: str):
        """
            ['(', 'A.attr=x', 'and', 'A.attr2 in (x,y,z)', 'or', '(', 'A.attr>3', ')', ')']

        """
        tokenized_list = self.tokenize(condition)
        root = ParenthesisConditionResolverTree(None)
        my_tree, _ = self.__to_tree(tokenized_list, root)
        OR_root = ORLogicalOperatorNode()
        or_tree, _ = self.__parse_to_or_tree(OR_root, my_tree)
        print(tokenized_list)
        # print(my_tree)

    def __parse_to_or_tree(self, ortree: ORLogicalOperatorNode, ptree: ParenthesisConditionResolverTree):
        if ptree is None or len(ptree.children) == 0:
            return ortree
        left_side = []
        for p in ptree.children:
            if p.is_val.lower() == "or":
                if len(left_side) == 0:
                    raise SyntaxError("Impossible to start a condition with OR or and ")
                ortree.conditions.append(left_side)
                left_side = []
            if p.is_parenthesis:
                OR_sub_tree = ORLogicalOperatorNode()
                node_p = self.__parse_to_or_tree(OR_sub_tree, p)
                for n in node_p:
                    left_side.append(n)
            else:
                cn = ConditionNodes(ortree, p.get_node_value(), None)
                left_side.append(cn)
        return ortree.conditions


    def to_graph(self, my_tree: ParenthesisConditionResolverTree):
        my_tree.show()

    def tokenize(self, condition: str) -> [str]:
        normalized_condition = self.__normalize_condition(condition)
        if len(normalized_condition) == 0:
            return normalized_condition
        split_cond = normalized_condition.split(" ")
        new_cond: [str] = self.__unify_enum_conditions(split_cond)
        return new_cond

    def __to_tree(self, conds: [str], parent: ParenthesisConditionResolverTree, token_idx: int = 0) -> (ParenthesisConditionResolverTree, int):
        while len(conds) > token_idx:
            cond = conds[token_idx]
            if cond.strip() == '(':
                current_idx = token_idx
                parenthesis_node = parent if current_idx == 0 else ParenthesisConditionResolverTree(parent)
                parenthesis_node.is_parenthesis = True
                parenthesis_node.idx = token_idx
                c_node, token_idx = self.__to_tree(conds, parenthesis_node, token_idx + 1)
                if current_idx == 0:
                    parent = c_node
                else:
                    parent.children.append(c_node)
            elif cond.strip() == ')':
                return parent, token_idx
            else:
                c = ParenthesisConditionResolverTree(parent, is_val=cond, is_and=cond.strip().lower() == "and",
                                                     is_or=cond.strip().lower() == "or")
                c.idx = token_idx
                parent.children.append(c)
            token_idx = token_idx + 1
        return parent, token_idx

    # def __to_tree_strct2(self, conds: [str], cn: ConditionNode):
    #     pass

    def __tokenize_parenthesized_condition(self, split_cond: [str], idx: int) -> ([str | typing.List[typing.Any]], int):
        ls = []
        curr_item = split_cond[idx]
        if curr_item.strip() == '(':
            condition_str = ""
            while curr_item != ")":
                condition_str = f"{condition_str} {curr_item}".strip()
                idx = idx + 1
                curr_item = split_cond[idx].strip()
                is_in_condition = re.match(r" *(not_in|in) *", curr_item)
                if is_in_condition:
                    condition_str = " ".join(condition_str.strip().split(" ")[:-1])
                    in_cond, idx = self.__tokenize_in_not_in(split_cond, idx)
                    condition_str = f"{condition_str} {in_cond}"
                    idx = idx + 1  # go to next token
                    curr_item = split_cond[idx].strip()
                if curr_item.strip() == '(':
                    sub_cond, idx = self.__tokenize_parenthesized_condition(split_cond, idx)
                    ls.append(sub_cond)
                    idx = idx + 1
                    curr_item = split_cond[idx].strip()
            ls.insert(0, condition_str)
        return ls, idx

    def __unify_enum_conditions(self, split_cond: [str]) -> [str]:
        total_len = len(split_cond)
        new_cond, idx, st = [], 0, ""
        while total_len > idx:
            st = split_cond[idx]
            matches = re.match(r" *(not_in|in) *", st)
            if matches:
                new_cond = new_cond[:-1]  # remove last element added which should be last_Str, which must be an attr
                in_cond, idx = self.__tokenize_in_not_in(split_cond, idx)
                new_cond.append(in_cond)
            else:
                new_cond.append(st)
            idx = idx + 1
        return new_cond

    def __tokenize_in_not_in(self, split_cond: [str], idx: int) -> (str, int):
        """
        Unify the in or not in condition which is separated after normalized method and make one unique str.

        Parameters
        ----------
        split_cond after normalized the condition, splited with space
        idx: current index of split condition where the in|in_not is occurred

        Returns
        -------
         string: A.attr (in|in_not) (x,y,z)
         idx: return the index number where in or in not condition finish
        """
        is_in_condition = split_cond[idx].strip()  # can be in or not_in
        matches = re.match(r" *(not_in|in) *", is_in_condition)
        my_str = ""
        if matches:
            next_word = split_cond[idx + 1].strip()  # must be "(" after in or not_in
            # my_str = f"{last_str} {DECLARE_LOGIC_OP.get_token()} "
            my_str = f"{split_cond[idx - 1].strip()} {is_in_condition} "
            if next_word != '(':
                raise SyntaxError(f"Unable to parse the condition. After in keyword expected \"(\""
                                  f" but found {next_word}")
            while next_word != ")":
                idx = idx + 1
                next_word = split_cond[idx]
                my_str = f"{my_str}{next_word}"
                if next_word == "(":
                    pass  # something wrong in the condition something like this "A.grade in (dx,(dfd, ere)"
                    #                                                              ..............^ unhandled

        return my_str, idx


