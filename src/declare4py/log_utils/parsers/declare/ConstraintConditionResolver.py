from __future__ import annotations

import dataclasses
import re
import typing
import warnings
from enum import Enum
from typing import Literal
import uuid

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
    def __init__(self, parent: ConditionNode | None, value: str, children: [ConditionNode] | None = None,
                 token_index: int = 0):
        self.children = [] if children is None else children
        self.parent = parent
        self.value = value
        self.token_index = token_index
        self.uid = str(uuid.uuid4())
        self.__update_parent()
        self.__update_children_parent()

    def __update_parent(self):
        """
         If this not is not a root, then we add this node as child to parent.
        """
        if self.parent is not None:
            print("self.parent.children", self.parent.children)
            for i, pc in self.parent.children:
                print("pc", pc)
                if pc != self and pc.value == self.value:
                    self.parent.children.append(self)

    def __update_children_parent(self):
        """
         Update children parents
        """
        if self.children is not None and len(self.children) > 0:
            for child in self.children:
                child.parent = self

    def shift_bottom(self, value: str, idx: int = 0) -> ConditionNode:
        """
        Create a new node and add it as a child and children of current node are removed from current node and added
        to new node. The new node becomes of child of current node.

        In other way, children of current node are disconnected and becomes children of new node and removed from old
        node. The new node is a child of current node.

        Parameters
        ----------
        value: value of new node injecting
        idx: index

        Returns
        -------
        ConditionNode new Node
        """
        current_node_children = self.children
        cn = ConditionNode(self, value, current_node_children, idx)
        self.children = [cn]
        return cn

    def shift_bottom_children(self, value: str, children_to_shift: [ConditionNode], idx: int = 0) -> ConditionNode:
        """
        Create a new node and children_to_shift becomes children of new node and removed from there parent


                      a                ===>                                             a
                b            c         ===> we want to shift d and e              b             c
            d  e  f       g    h                                              i      f        g   h
                                                                            d   e
        See the nodes: d and e are moved to one bottom level and parent is i and i is parent b now.

        Parameters
        ----------
        value: value of new node injecting
        children_to_shift: [ConditionNode]
        idx: index

        Returns
        -------
        ConditionNode new Node
        """
        # parents_of_children_to_shift = []

        for cts in children_to_shift:
            if cts.parent is not None:
                c = cts.parent.children
                c.remove(cts)
        cn = ConditionNode(self, value, None, idx)
        cn.add_children(children_to_shift)
        self.children.append(cn)
        # for child in self.children:
        #     if child in children_to_shift:
        #         self.children.remove(child)
        return cn

    def add_child(self, cn: ConditionNode) -> None:
        if cn is None:
            return
        if cn not in self.children:
            self.children.append(cn)
        cn.parent = self

    def add_children(self, children_list: [ConditionNode]) -> None:
        for child in children_list:
            self.add_child(child)

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

    def get_height(self) -> int:
        """
        Calculate the height of provided node.
        Height is the total number of edges from leaf node to a particular node in the longest path

        Leaf is the most bottom node in the tree or the node without children

        Parameters
        ----------
        c: ConditionNode
        idx: int

        Returns
        -------
        Returns the height of the node
        """
        h = 0
        if len(self.children) == 0:
            return 0

        for child in self.children:
            n = child.get_height()
            if n > h:
                h = n

        return h + 1

    def get_inverse_height(self) -> int:
        """
        Returns the length of tree from current node to root
        or Depth of tree

        Parameters
        ----------
        Returns
        -------
        int
        """
        return self._get_inverse_height(self, 0)

    def _get_inverse_height(self, c: ConditionNode, idx: int = 0) -> int:
        """
        Returns the length of tree from current to root
        Parameters
        ----------
        c: ConditionNode is a node from where it starts climbing up till root to calculate its inverse height
        idx: int

        Returns
        -------
        int
        """
        if c is None:
            return idx
        if c.parent is None:
            return idx
        idx = 1 + self._get_inverse_height(c.parent, idx)
        return idx

    def size_sub_nodes(self, ct: ConditionNode | None = None):
        """
        Returns the size of this node.

        if this node has 3 children the total size would be 3 if children doesn't have there children

        if this node has 2 children: [node1], [node2] and [node1] has 2 children, [node2] none then size of this node is 4

        Parameters
        ----------
        ct: condition node

        Returns
        -------

        """
        if ct is None:
            ct = self
        v = 0
        if len(ct.children) > 0:
            for idx, child in enumerate(ct.children):
                v = v + child.size_sub_nodes(child)
        return v + len(ct.children)

    def display_tree_graph(self, image_name: str = "graph", format: str = "svg"):
        dot = graphviz.Digraph(comment="Graph", format=format)
        # self.generate_view_advance(dot, [self])
        self.generate_tree_graph(dot, [self])
        dot.render(f'{image_name}.gv', view=True)

    def generate_tree_graph(self, dot: graphviz.Digraph, node_list: [ConditionNode], edge_counter: int = 0):
        if node_list is None or len(node_list) == 0:
            return
        for node in node_list:
            edge_name = f"{node.uid}"
            value = f"{node.token_index}:{node.value}"
            if value is None:
                value = "Undefined"
            dot.node(edge_name, value)
            parent = node.parent
            if parent is not None:
                p_edge_name = str(node.parent.uid)
                dot.edge(p_edge_name, edge_name)
            if len(node.children) > 0:
                self.generate_tree_graph(dot, node.children, edge_counter + 1)

    def generate_view_advance(self, dot: graphviz.Digraph, node_list: [ConditionNode], edge_counter: int = 0):
        if node_list is None or len(node_list) == 0:
            return
        for node in node_list:
            if isinstance(node, list):
                self.generate_view_advance(dot, node, edge_counter + 1)
            else:
                edge_name = f"{node.uid}"
                # edge_name = f"{edge_counter}"
                value = f"{node.token_index}:{node.value}"
                if value is None:
                    value = "Undefined"
                dot.node(edge_name, value)
                parent = node.parent
                if parent is not None:
                    p_edge_name = str(node.parent.uid)
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
                    child.generate_view_advance(dot, child, lvl, edge_name)

    def to_str_list(self, cn: ConditionNode) -> [str]:
        spaces = "-" * cn.get_inverse_height()
        p_idx = "-"
        if cn.parent is not None:
            p_idx = cn.parent.token_index

        # ls = [f"{spaces}(\"idx\":\"{cn.token_index}\", \"parent_idx\":\"{p_idx}\", \"value\":\"{cn.value}\")"]
        ls = [f"{spaces}(id:{cn.token_index}, parent_id:{p_idx}, value:{cn.value})"]
        for child in cn.children:
            ls = ls + child.to_str_list(child)
        return ls

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
            cn2 = child.clone_branch(reindex, idx + i + 1)
            cn2.parent = cn
            cn.children.append(cn2)
        return cn

    def __str__(self):
        return "\n".join(self.to_str_list(self))


class ParenthesisConditionResolverTree(ConditionNode):
    """
        Each node in this tree can represent one of the following thing parenthesis, and, or, val.
        Val is the condition i.e such as "a>3", "a in (x,y,z)" etc.
        This helps us to parse the parenthesis in the given condition.
    """

    def __init__(self, parent: ConditionNode | None, value: str = "", children: [ConditionNode] | None = None,
                 idx: int = 0):
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
        my_tree, _, _ = self.to_parenthesis_tree(tokenized_list, root)
        # OR_root = ORLogicalOperatorNode()
        OR_root = ConditionNode(None, "")
        # self.__parse_to_or_tree(OR_root, my_tree)
        self.__generate_or_tree_bfs(OR_root, my_tree)
        print(tokenized_list)
        # print(my_tree)
        # print("OR_root")
        print(OR_root)
        my_tree.display_tree_graph("parenthesis")
        OR_root.display_tree_graph("or graph")

    def __generate_or_tree_bfs(self, or_tree: ConditionNode, ptree: ParenthesisConditionResolverTree, idx: int = 0):
        if ptree is None or len(ptree.children) == 0:
            return or_tree
        left_side = []
        for pNode in ptree.children:
            if pNode.value.lower() == "or":
                if len(left_side) == 0:
                    raise SyntaxError("Impossible to start a condition with OR or and ")
                idx = idx + 1
                # ConditionNode(or_tree, f"cond_{idx}", left_side, idx)
                or_tree.shift_bottom_children(f"cond_{idx}", left_side, idx)
                left_side = []
                # continue
            else:
                idx = idx + 1
                cn = ConditionNode(None, pNode.value, None, idx)
                if pNode.value == "(":
                    cn = pNode.clone_branch(reindex=True, idx=idx)
                    cn.parent = or_tree
                    idx = idx + pNode.size_sub_nodes()
                left_side.append(cn)

        if len(left_side) > 0:
            idx = idx + 1
            # ConditionNode(or_tree, f"cond_{idx}", left_side, idx)
            # or_tree.children.append(OR_sub_tree)
            # for n in left_side:
            #     n.parent = OR_sub_tree

        if len(or_tree.children) > 0:
            for t in or_tree.children:  # or children are cond_n
                for n in t.children:
                    idx = idx + 1
                    # n.children = self.__generate_or_tree_bfs(t, n, idx)
        return or_tree.children

    def tokenize(self, condition: str) -> [str]:
        normalized_condition = self.__normalize_condition(condition)
        if len(normalized_condition) == 0:
            return normalized_condition
        split_cond = normalized_condition.split(" ")
        print("normalized_condition", normalized_condition)
        print("split_cond", split_cond)
        new_cond: [str] = self.__unify_enum_conditions(split_cond)
        return new_cond

    def to_parenthesis_tree(self, conds: [str], parent: ConditionNode, token_idx: int = 0) -> (ConditionNode, int):
        cond_index = 0
        if token_idx == 0 and conds[0].strip() != '(':
            token_idx = token_idx + 1
        return self._to_parenthesis_tree(conds, parent, token_idx, cond_index)

    def _to_parenthesis_tree(
            self, conds: [str], parent: ConditionNode, token_idx: int = 0, cond_index: int = 0
    ) -> (ConditionNode, int):
        while len(conds) > cond_index:
            cond = conds[cond_index]
            if cond.strip() == '(':
                current_idx = token_idx
                parenthesis_node = parent if current_idx == 0 else ParenthesisConditionResolverTree(
                    parent, "(", None, idx=token_idx)
                parenthesis_node.value = "("
                parenthesis_node.token_index = token_idx
                c_node, token_idx, cond_index = self._to_parenthesis_tree(conds, parenthesis_node, token_idx + 1,
                                                                          cond_index + 1)
                if current_idx == 0:
                    parent = c_node
            elif cond.strip() == ')':
                return parent, token_idx, cond_index
            else:
                ParenthesisConditionResolverTree(parent, value=cond, children=None, idx=token_idx)
            token_idx = token_idx + 1
            cond_index = cond_index + 1
        return parent, token_idx, cond_index

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
