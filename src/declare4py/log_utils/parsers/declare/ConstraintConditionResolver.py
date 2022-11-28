from __future__ import annotations

import dataclasses
import re
import typing
import warnings
from enum import Enum
from typing import Literal

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


class ConditionNode:
    def __init__(self, parent: ConditionNode, value: str, children: [ConditionNode] | None = None, token_index: int = 0):
        self.children = [] if children is None else children
        self.parent = parent
        self.value = value
        self.token_index = token_index

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

    def get_bottom_up_height(self, c: ConditionNode, idx: int = 0) -> int:
        """
        Returns the length of tree from bottom to root
        Parameters
        ----------
        c: ConditionNode is a node from where it start climbing up till root to calculate its height
        idx: int

        Returns
        -------
        int
        """
        if c is None:
            return idx
        if c.parent is None:
            return idx
        idx = 1 + self.get_bottom_up_height(c.parent, idx)
        return idx

    def sub_vertices(self, ct: ConditionNode | None = None):
        if ct is None:
            ct = self
        v = 0
        if len(ct.children) > 0:
            for idx, child in enumerate(ct.children):
                v = v + child.vertices(child)
        return v + len(ct.children)

    def show_node(self):
        dot = graphviz.Digraph(comment="Graph", format="svg")
        self.generate_view_advance(dot, [self])
        dot.render('digraph.gv', view=True)

    def generate_view_advance(self, dot: graphviz.Digraph, node_list: [ConditionNode], edge_counter: int = 0):
        if node_list is None or len(node_list) == 0:
            return

        for node in node_list:
            if isinstance(node, list):
                self.generate_view_advance(dot, node, edge_counter + 1)
            else:
                edge_name = f"{node.token_index}"
                # edge_name = f"{edge_counter}"
                value = f"{node.token_index}:{node.value}"
                if value is None:
                    value = "Undefined"
                dot.node(edge_name, value)
                parent = node.parent
                if parent is not None:
                    p_edge_name = str(node.parent.token_index)
                    # p_edge_name = f"{edge_counter}_{node.parent.token_index}"
                    dot.edge(p_edge_name, edge_name)
                if len(node.children) > 0:
                    self.generate_view_advance(dot, node.children, edge_counter + 1)

    def _generate_view_list(self, dot: graphviz.Digraph, ls: [ConditionNode], lvl, node_id: str):
        edge_name = f"cond_{lvl}"
        dot.node(edge_name, edge_name)
        dot.edge(str(node_id), edge_name)
        if len(ls) > 0:
            for idx, child in enumerate(ls):
                if isinstance(child, list):
                    self._generate_view_list(dot, child, lvl, edge_name)
                else:
                    print("child", idx, child)
                    child.generate_view_advance(dot, child, lvl, edge_name)

    def to_str(self, cn: ConditionNode):
        spaces = "-" * cn.get_bottom_up_height(cn, 0)
        p_idx = "-"
        if cn.parent is not None:
            p_idx = cn.parent.token_index
        s = f"{spaces}(\"idx\":\"{cn.token_index}\", \"parent_idx\":\"{p_idx}\", \"value\":\"{cn.value}\")\n"
        for child in cn.children:
            if isinstance(child, list):
                s = s + cn.to_str_from_list(child)
                s = s + "\n"
            else:
                s = s + child.__str__()
        return s

    def to_str_from_list(self, cn: [ConditionNode]):
        s = ""
        for child in cn:
            if isinstance(child, list):
                s = s + self.to_str_from_list(child)
            else:
                s = s + child.to_str(child)
        return s

    def clone_branch(self, reindex: bool = False, idx: int = 0) -> ConditionNode:
        """
        Create a new tree from this node to its children and sub-children
        Parameters
        ----------
        reindex: bool whether should use the same index or should create from scratch.
        idx: int works only if reindex is true
        Returns
        -------
        Returns ConditionNode
        """
        cn = ConditionNode(None, self.value, [], idx if reindex else self.token_index)
        if len(self.children) == 0:
            return cn
        for i, child in enumerate(self.children):
            if isinstance(child, list):
                nls = self.clone_branch_list(child, reindex, idx)
                for n in nls:
                    n.parent = cn
                    cn.children.append(n)
            else:
                cn2 = child.clone_branch(reindex, idx + i)
                cn2.parent = cn
                cn.children.append(cn2)
        return cn

    def clone_branch_list(self, ls: [ConditionNode], reindex: bool = False, idx: int = 0):
        """
        Create a new tree from this node to its children and sub-children
        Parameters
        ----------
        ls: list of nodes
        reindex: bool whether should use the same token index or should create from scratch.
        idx: int works only if reindex is true
        Returns
        -------
        Returns ConditionNode
        """
        if ls is None or len(ls) == 0:
            return None
        nls = []
        for i, child in enumerate(ls):
            if isinstance(child, list):
                nls = self.clone_branch_list(child, reindex, idx)
            else:
                cn = child.clone_branch(child, reindex, idx)
                nls.append(cn)
        return nls

    def __str__(self):
        return self.to_str(self)


class ParenthesisConditionResolverTree(ConditionNode):
    """
        Each node in this tree can represent one of the following thing parenthesis, and, or, val.
        Val is the condition i.e such as "a>3", "a in (x,y,z)" etc.
        This helps us to parse the parenthesis in the given condition.
    """

    def __init__(self, parent: ConditionNode | None, value: str = "", children: [ConditionNode] | None = None, idx: int = 0):
        if children is None:
            children = []
        self.value: str = "(" if value is None or len(value) == 0 else value
        self.children: [ConditionNode] = children
        self.parent: ConditionNode = parent
        self.token_index = idx
        super().__init__(parent, value, children, self.token_index)

    def show(self):
        dot = graphviz.Digraph(comment="Graph", format="svg")
        self.generate_view(dot)
        dot.render('digraph.parenthesis.gv', view=True)

    def generate_view(self, dot: graphviz.Digraph):
        node_id = str(self.token_index)
        dot.node(node_id, f"{node_id}:{self.get_type_of_node()}")
        if len(self.children) > 0:
            for idx, child in enumerate(self.children):
                child.generate_view(dot)
            for idx, child in enumerate(self.children):
                dot.edge(node_id, str(child.token_index))

    def get_type_of_node(self) -> str:
        if self.is_parenthesis_node():
            return "(...)"
        if self.is_AND_node():
            return "AND"
        if self.is_OR_node():
            return "OR"
        if len(self.value) > 0:
            return self.value
        return "UNKNOWN VALUE"

    def is_parenthesis_node(self):
        return self.value == "("

    def is_AND_node(self):
        return self.value.lower() == "and"

    def is_OR_node(self):
        return self.value.lower() == "or"


class LogicalOperatorNode:
    node_type: Literal["OR", "AND"] = "OR"
    pass


class ORLogicalOperatorNode(LogicalOperatorNode):
    node_type = "OR"
    children: [ConditionNode] = []


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
        my_tree, _, _ = self.__to_tree_start(tokenized_list, root)
        # OR_root = ORLogicalOperatorNode()
        OR_root = ConditionNode(None, "")
        # self.__parse_to_or_tree(OR_root, my_tree)
        self.__generate_or_tree_bfs(OR_root, my_tree)
        print(tokenized_list)
        # print(my_tree)
        print("OR_root")
        print(OR_root)
        my_tree.show()
        OR_root.show_node()

    def __generate_or_tree_bfs(self, or_tree: ConditionNode, ptree: ParenthesisConditionResolverTree, idx: int = 0):
        if ptree is None or len(ptree.children) == 0:
            return or_tree
        left_side = []
        for pNode in ptree.children:
            if pNode.value.lower() == "or":
                if len(left_side) == 0:
                    raise SyntaxError("Impossible to start a condition with OR or and ")
                idx = idx + 1
                OR_sub_tree = ConditionNode(or_tree, f"cond_{idx}", left_side, idx)
                or_tree.children.append(OR_sub_tree)
                for n in left_side:
                    n.parent = OR_sub_tree
                left_side = []
            else:
                idx = idx + 1
                cn = ConditionNode(or_tree, pNode.value, None, idx)
                left_side.append(cn)
                if pNode.value == "(":
                    new_sub_tree = pNode.clone_branch(reindex=True, idx=idx)
                    idx = len(new_sub_tree.children)
                    cn.children = new_sub_tree.children
                    # for n in pNode.children:
                    #     cn.children.append()
        if len(left_side) > 0:
            idx = idx + 1
            OR_sub_tree = ConditionNode(or_tree, f"cond_{idx}", left_side, idx)
            or_tree.children.append(OR_sub_tree)
            for n in left_side:
                n.parent = OR_sub_tree
        return or_tree.children

    def __parse_to_or_tree(self, or_tree: ConditionNode, ptree: ParenthesisConditionResolverTree, idx: int = 0, parent_idx: int = 0):
        if ptree is None or len(ptree.children) == 0:
            return or_tree
        left_side = []
        for pNode in ptree.children:
            if pNode.value.lower() == "or":
                if len(left_side) == 0:
                    raise SyntaxError("Impossible to start a condition with OR or and ")
                idx = idx + 1
                OR_sub_tree = ConditionNode(or_tree, f"cond_{idx}", left_side, idx)
                or_tree.children.append(OR_sub_tree)
                for n in left_side:
                    if isinstance(n, ConditionNode):
                        n.parent = OR_sub_tree
                left_side = []
            elif pNode.value == "(":
                idx = idx + 1
                parenthesis_node = ConditionNode(or_tree, '(', [], idx)  # create sub node
                node_list = self.__parse_to_or_tree(parenthesis_node, pNode, idx)
                left_side = [parenthesis_node] + left_side  # + node_list
                idx = idx + len(node_list)
            else:
                idx = idx + 1
                cn = ConditionNode(or_tree, pNode.value, None, idx)
                left_side.append(cn)
        if len(left_side) > 0:
            idx = idx + 1
            OR_sub_tree = ConditionNode(or_tree, f"cond_{idx}", left_side, idx)
            or_tree.children.append(OR_sub_tree)
            # for n in left_side:
            #     or_tree.children.append(n)
        return or_tree.children

    def __parse_to_or_tree2(self, ortree: ORLogicalOperatorNode, ptree: ParenthesisConditionResolverTree):
        if ptree is None or len(ptree.children) == 0:
            return ortree
        left_side = []
        for p in ptree.children:
            print(p)
            if p.value.lower() == "or":
                if len(left_side) == 0:
                    raise SyntaxError("Impossible to start a condition with OR or and ")
                ortree.children.append(left_side)
                left_side = []
            if p.value == "(":
                OR_sub_tree = ORLogicalOperatorNode()
                node_p = self.__parse_to_or_tree(OR_sub_tree, p)
                for n in node_p:
                    left_side.append(n)
            else:
                cn = ConditionNode(p, p.value, None)
                left_side.append(cn)
        return ortree.children


    def to_graph(self, my_tree: ParenthesisConditionResolverTree):
        my_tree.show_node()

    def tokenize(self, condition: str) -> [str]:
        normalized_condition = self.__normalize_condition(condition)
        if len(normalized_condition) == 0:
            return normalized_condition
        split_cond = normalized_condition.split(" ")
        print("normalized_condition", normalized_condition)
        print("split_cond", split_cond)
        new_cond: [str] = self.__unify_enum_conditions(split_cond)
        return new_cond

    def __to_tree_start(self, conds: [str], parent: ConditionNode, token_idx: int = 0) -> (ConditionNode, int):
        cond_index = 0
        if token_idx == 0 and conds[0].strip() != '(':
            # parent = ParenthesisConditionResolverTree(parent, "", [], 1)
            token_idx = token_idx + 1
        return self.__to_tree(conds, parent, token_idx, cond_index)

    def __to_tree(self, conds: [str], parent: ConditionNode, token_idx: int = 0, cond_index: int = 0) -> (ConditionNode, int):
        while len(conds) > cond_index:
            cond = conds[cond_index]
            if cond.strip() == '(':
                current_idx = token_idx
                parenthesis_node = parent if current_idx == 0 else ParenthesisConditionResolverTree(parent, "(", None, idx=token_idx)
                parenthesis_node.value = "("
                parenthesis_node.token_index = token_idx
                c_node, token_idx, cond_index = self.__to_tree(conds, parenthesis_node, token_idx + 1, cond_index + 1)
                if current_idx == 0:
                    parent = c_node
                else:
                    parent.children.append(c_node)
            elif cond.strip() == ')':
                return parent, token_idx, cond_index
            else:
                c = ParenthesisConditionResolverTree(parent, value=cond, children=None, idx=token_idx)
                parent.children.append(c)
            token_idx = token_idx + 1
            cond_index = cond_index + 1
        return parent, token_idx, cond_index

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


