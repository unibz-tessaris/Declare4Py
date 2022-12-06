from __future__ import annotations
from abc import ABC, abstractmethod

import json
import base64
import copy
import re
import typing
import warnings
from enum import Enum
import uuid

from src.declare4py.models.ltl_model import LTLModel

try:
    """
        This is an optional library used to draw the graphs in image.
        To understand a condition, represented in form of a graph would make little easy.
    """
    import graphviz
except:
    raise warnings.warn("Unable to load graphviz library. Declare model Constraint"
                        " condition will will not generate the tree views")



class DeclareTemplate(str, Enum):

    def __new__(cls, *args, **kwds):
        value = len(cls.__members__) + 1
        obj = str.__new__(cls)
        obj._value_ = value
        return obj

    def __init__(self, templ_str: str, is_binary: bool, is_negative: bool, supports_cardinality: bool):
        self.templ_str = templ_str
        self.is_binary = is_binary
        self.is_negative = is_negative
        self.supports_cardinality = supports_cardinality

    EXISTENCE = "Existence", False, False, True
    ABSENCE = "Absence", False, False, True
    EXACTLY = "Exactly", False, False, True

    INIT = "Init", False, False, False

    CHOICE = "Choice", True, False, False
    EXCLUSIVE_CHOICE = "Exclusive Choice", True, False, False
    RESPONDED_EXISTENCE = "Responded Existence", True, False, False
    RESPONSE = "Response", True, False, False
    ALTERNATE_RESPONSE = "Alternate Response", True, False, False
    CHAIN_RESPONSE = "Chain Response", True, False, False
    PRECEDENCE = "Precedence", True, False, False
    ALTERNATE_PRECEDENCE = "Alternate Precedence", True, False, False
    CHAIN_PRECEDENCE = "Chain Precedence", True, False, False

    NOT_RESPONDED_EXISTENCE = "Not Responded Existence", True, True, False
    NOT_RESPONSE = "Not Response", True, True, False
    NOT_CHAIN_RESPONSE = "Not Chain Response", True, True, False
    NOT_PRECEDENCE = "Not Precedence", True, True, False
    NOT_CHAIN_PRECEDENCE = "Not Chain Precedence", True, True, False

    @classmethod
    def get_template_from_string(cls, template_str):
        return next(filter(lambda t: t.templ_str == template_str, DeclareTemplate), None)

    @classmethod
    def get_unary_templates(cls):
        return tuple(filter(lambda t: not t.is_binary, DeclareTemplate))

    @classmethod
    def get_binary_templates(cls):
        return tuple(filter(lambda t: t.is_binary, DeclareTemplate))

    @classmethod
    def get_positive_templates(cls):
        return tuple(filter(lambda t: not t.is_negative, DeclareTemplate))

    @classmethod
    def get_negative_templates(cls):
        return tuple(filter(lambda t: t.is_negative, DeclareTemplate))

    def __str__(self):
        return "<Template." + str(self.templ_str) + ": " + str(self.value) + " >"

    def __repr__(self):
        return "\""+str(self.__str__())+"\""


class TraceState(str, Enum):
    VIOLATED = "Violated"
    SATISFIED = "Satisfied"
    POSSIBLY_VIOLATED = "Possibly Violated"
    POSSIBLY_SATISFIED = "Possibly Satisfied"


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
    # logical operators
    AND = "and", "AND", "and"  # TODO: don't yet whether declare model can have && sybmol as and
    OR = "or", "OR", "or"  # TODO: don't yet whether declare model can have || sybmol as or
    # numerical operations
    GT = "greater_then", "GT", ">"
    GEQ = "greater_eq", "GEQ", ">="
    LT = "less_then", "LT", "<"
    LEQ = "less_eq", "LEQ", "<="
    EQ = "equal", "EQ", "="  # TODO: would be converted in "is"
    NEQ = "not_equal", "NEQ", "!="  # TODO: should convert into  is not
    # enum operation
    IS = "is", "IS", "is"
    IS_NOT = "is not", "IS_NOT", "is not"
    IN = "in", "IN", "in"
    IN_NOT = "not in", "NOT_IN", "not in"
    # bohhh. As I know, same and different keywords are used only in target conditions
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
        self.children: [ConditionNode] = [] if children is None else children
        self.parent: ConditionNode = parent
        self.value: str = value
        self.token_index: int = token_index
        self.uid = str(uuid.uuid4())
        self.__add_node_to_parent_children()
        self.__update_children_parent()

    def __add_node_to_parent_children(self):
        """
         Add this new node to parent children if not exists
        """
        if self.parent is not None:  # if this is not a root node
            if self not in self.parent.children:  # if this node is not in the parent children list we add
                self.parent.children.append(self)

    def __update_children_parent(self):
        """
         Update children of this node and assign parent as this node
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
        for cts in children_to_shift:
            if cts.parent is not None:
                c = cts.parent.children
                if cts in c:
                    c.remove(cts)
        cn = ConditionNode(self, value, None, idx)
        cn.add_children(children_to_shift)
        for child in self.children:
            if child in children_to_shift:
                self.children.remove(child)
        return cn

    def add_child(self, cn: ConditionNode) -> None:
        if cn is None:
            return
        if cn not in self.children:
            self.children.append(cn)
        if cn.parent is not None:
            # Remove given node from parent's children list if parent exists
            if cn in cn.parent.children:
                cn.parent.children.remove(cn)
        cn.parent = self  # assign new parent

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
        self.generate_tree_graph(dot, [self])
        # dot.view()
        dot.render(f'{image_name}.gv', view=True)
        # dot.save(f'{image_name}.gv')
        # dot.render(f'{image_name}.gv')

    def generate_tree_graph(self, dot: graphviz.Digraph, node_list: [ConditionNode], edge_counter: int = 0):
        if node_list is None or len(node_list) == 0:
            return
        for node in node_list:
            edge_name = f"{node.uid}"
            value = f"{node.token_index}:{node.value}"
            if value is None:
                value = "Undefined"
            if value == '(':
                value = '(..)'
            dot.node(edge_name, value)
            parent = node.parent
            if parent is not None:
                p_edge_name = str(node.parent.uid)
                dot.edge(p_edge_name, edge_name)
            if len(node.children) > 0:
                self.generate_tree_graph(dot, node.children, edge_counter + 1)

    def to_str(self) -> str:
        """
        Converts the node into string.
        Returns
        -------
        """
        return self.tree_to_string()

    def tree_to_string(self) -> str:
        """
        Converts node and its children to string output.

        The output is also used in unit tests to test the correctness of creating correct tree
        Try to avoid the changes as much as possible in this method in order to make fails the tests

        The output is generated according to the DFS traverse

        Parameters
        ----------
        Returns
        -------
        str
        """
        spaces = "-" * self.get_inverse_height()
        p_idx = "-"
        if self.parent is not None:
            p_idx = self.parent.token_index
        s = f"{spaces}->(ID=\"{self.token_index}\", parentId=\"{p_idx}\", value:\"{self.value}\")\n"
        for child in self.children:
            s = s + child.tree_to_string()
        return s

    def clone_branch(self, reindex: bool = False, idx: int = 0) -> ConditionNode:
        new_tree_from_this_node, _ = self.__clone_branch(reindex, idx)
        return new_tree_from_this_node

    def __clone_branch(self, reindex: bool = False, idx: int = 0) -> (ConditionNode, int):
        """
        Create a new tree from this node to its children and sub-children
        Traverse DFS

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
            return cn, idx
        for child in self.children:
            idx = idx + 1
            cn2, idx = child.__clone_branch(reindex, idx)
            cn2.parent = cn
            cn.children.append(cn2)
        return cn, idx

    def unlink_parent_node(self):
        """
        Set the parent to none and remove itself from parent's children
        Returns
        -------

        """
        if self.parent is not None:
            children = self.parent.children
            children.remove(self)
            self.parent = None

    def __str__(self):
        # return "\n".join(self.to_str())
        return self.to_str()


"""

Parse given condition in a logical tree.

Logical tree can have 4 types of nodes: Parenthesis, AND, OR, Condition/expression
- Condition can be an logical expression such as:
 - "a>5", "a<5", "a<=5", "a>=5"
 - "a=5", "a!=8",
 - "a is enum", "a is not val",
 - "a in (alphas, alphanumeric)", "a in not (enum1, enum2)"
- Parenthesis can have other nodes, they can be "and", "or", "conditions". Parenthesis can have other parenthesis.
  - parenthesis are removed if they contain only one condition
- AND node represents conjunction operation
  - its all children are connected with "and" operand
  - ie. "and" node has 2 children: x>2, z<9. This can be seen in condition string as x>2 and z<9
- OR node represents disjunction operation
  - its all children are connected with "or" operand
  - ie. "or" node has 2 children: x>2, z<9. This can be seen in condition string as x>2 or z<9

How does it work or parse?

We tokenize the string and use tree types of trees.

1.) Tokenize the string
    1.1.) From string value, it cleans/normalizes the string by adjusting spaces, " in ", " in not", " is ",  " is not "
    converting into in some different values " in not " => "in_not", " is not " => is_not". "a in (alphas, alphanumeric)"
    is converted like this "a in ( alphas, alphanumeric )"
    1.2.) We split the normalized string with spaces
    1.3.) if we have in operator "a in ( alphas, alphanumeric )", this is converted as "a in (alphas, alphanumeric)" =>
     ["a", "in", "(", "alphas,", "alphanumeric,", ")" ] at step 1.2. So we have to unify into one expression.
2.) Coverts the tokens list into a parenthesis tree. i.e if a parenthesis token is encounter reading the token list,
    it creates a node and add next tokens as children and so on. 
3.) After parenthesis tree, we convert this tree into "OR tree" because or conditions can be imagined as splitting
    one condition in two sub condition and one of them true is sufficient to execute a captured block. In other words,
    "OR" logic has more precedence than "And" logic while parsing the condition the entire condition after parenthesis.
4.) Finally, we converts OR tree into "And tree", when we encounter "and" node while traversing(BFS way) the tree,
    we take the left and right part of "and" node and change the parent to these nodes.
5.) And tree is the logic tree and can be use for further steps, translate asp, discovery, etc
"""


class DeclareConditionTokenizer:
    # operatorsRegex = r" *(is_not|is|not_in|in|or|and|not|same|different|exist|<=|>=|<|>|=|!=) *"
    operatorsRegex = r" *(is_not|is|not_in|in|or|and|not|<=|>=|<|>|=|!=) *"

    def normalize_condition_string_to_tokenize(self, condition: str) -> str:
        string = re.sub(r'\)', ' ) ', condition)
        string = re.sub(r'\(', ' ( ', string)
        string = string.strip()
        string = re.sub(' +', ' ', string)
        string = re.sub(r' *is *not *', '!=', string)
        string = re.sub(r' *is *', '=', string)
        # string = re.sub(r'is not', 'is_not', string)
        string = re.sub(r'not in', 'not_in', string)
        string = re.sub(r' *> *', '>', string)
        string = re.sub(r' *< *', '<', string)
        string = re.sub(r' *= *', '=', string)
        string = re.sub(r' *!= *', '!=', string)
        string = re.sub(r' *<= *', '<=', string)
        string = re.sub(r' *>= *', '>=', string)
        return string

    def parse_to_logic_tree(self, condition: str, show_final_graph: bool = False):
        tokenized_list = self.tokenize(condition)
        my_tree = self.to_parenthesis_tree(tokenized_list)
        # my_tree.display_tree_graph("parenthesis", format="svg")
        OR_tree = self.to_OR_tree(my_tree)
        # OR_tree.display_tree_graph("or graph")
        and_tree = self.generate_AND_tree(OR_tree)
        if show_final_graph:
            and_tree.display_tree_graph()
        return and_tree

    def to_OR_tree(self, parenthesis_solved_Tree: ConditionNode):
        OR_root = ConditionNode(None, "")
        ptree = parenthesis_solved_Tree.clone_branch(False, 0)
        return self.resolve_boolean_logic_tree_or(OR_root, ptree, ptree.size_sub_nodes() + 1)

    def generate_AND_tree(self, or_tree: ConditionNode):
        or_tree = or_tree.clone_branch(False, 0)
        self.resolve_boolean_logic_tree_and(ConditionNode(None, ""), or_tree)
        return or_tree

    def resolve_boolean_logic_tree_and(self, and_tree: ConditionNode, or_tree: ConditionNode):
        """
        Tree traverse here is BFS breadth first search.
        Basically, we check all the children of or_tree and find "and" node. if there are more "and" nodes, we take last node
        and all other siblings to this node except other "and" nodes.
        Parameters
        ----------
        and_tree: an node
        or_tree: conditionNode. An OR tree to be parsed and converted into and tree

        Returns
        -------
        """
        if or_tree is None:
            return []
        if len(or_tree.children) == 0:  # or len(or_tree.children) == 1:
            return or_tree
        and_dict = []
        ls = []
        an_and_node: ConditionNode | None = None

        for node in or_tree.children:
            if node.value.strip().lower() == "and":
                # if an_and_node is not None:
                #     an_and_node.delete_node()
                an_and_node = node
                and_dict.append({"and_node": node, "left_part": ls})
                ls = []
            else:
                ls.append(node)

        if len(and_dict) == 0:  # if didn't find any and in the siblings
            and_tree.children = and_tree.children + ls
            # for atl in and_tree.children:
            #     atl.parent = and_tree
        elif len(ls) > 0:  # elsewise ls can not be empty, so
            for d in and_dict:
                # we take the last "and" node and add the all the children to it and updates
                an_and_node.children = an_and_node.children + d["left_part"]
            an_and_node.children = an_and_node.children + ls  # last remained nodes those were not added in and_dict
            for lan in an_and_node.children:
                lan.parent = an_and_node
                or_tree.children.remove(lan)
            and_tree.children = [an_and_node]
            or_tree.children = [an_and_node]
        for i, node in enumerate(and_tree.children):
            nn = ConditionNode(None, node.value, [], node.token_index)
            p = self.resolve_boolean_logic_tree_and(nn, node)
            # p.parent = node.parent
            # nn.children = p.children
        return and_tree

    def resolve_boolean_logic_tree_or(self, or_tree: ConditionNode, ptree: ConditionNode, new_node_idx: int = 0):
        """
        Traverse here is LS DFS Left Side Depth First Search
        Parameters
        ----------
        :param ConditionNode or_tree: Maybe an empty root node
        :param ConditionNode ptree: first level of tree, which is generated from after conditions tokenized
        :param int new_node_idx: a start number that will be used when new nodes are created and assigned as to them

        Returns
        -------

        """
        if ptree is None:
            return []
        if len(ptree.children) == 0:
            return ConditionNode(ptree.parent, ptree.value, ptree.children, ptree.token_index)

        left_side = []
        or_flag = False
        for pNode in ptree.children:
            if pNode.value.lower() == "or":
                if len(left_side) == 0:
                    raise SyntaxError(f"Impossible to start a condition with \"OR\"")
                new_node_idx = new_node_idx + 1
                or_tree.shift_bottom_children(f"OR", left_side, new_node_idx)
                or_flag = True
                left_side = []
            elif pNode.value == '(':
                new_node_idx = new_node_idx + 1
                new_node = ConditionNode(None, '(', [], pNode.token_index)
                s = self.resolve_boolean_logic_tree_or(new_node, pNode, new_node_idx)
                left_side.append(s)
            else:
                cn = ConditionNode(None, pNode.value, None, pNode.token_index)
                left_side.append(cn)
        if len(left_side) > 0:
            new_node_idx = new_node_idx + 1
            if or_flag:
                ConditionNode(or_tree, f"OR", left_side, new_node_idx)
            else:
                or_tree.children = or_tree.children + left_side
                for ls in left_side:
                    ls.parent = or_tree
        return or_tree

    def tokenize(self, condition: str) -> [str]:
        normalized_condition = self.normalize_condition_string_to_tokenize(condition)
        if len(normalized_condition) == 0:
            return normalized_condition
        split_cond = normalized_condition.split(" ")
        new_cond: [str] = self.__unify_enum_conditions(split_cond)
        return new_cond

    def to_parenthesis_tree(self, conds: [str], token_idx: int = 1) -> ConditionNode | None:
        open_parenthesis = [idx for idx in conds if idx == '(']
        close_parenthesis = [idx for idx in conds if idx == ')']
        if len(open_parenthesis) != len(close_parenthesis):
            raise SyntaxError("Condition is incorrect. Open parenthesis and closing parenthesis in condition are not "
                              "equal")
        if len(conds) == 0:
            return None
        if len(conds) == 1:
            return ConditionNode(None, conds[0], [], token_idx)
        cond_index = 0
        parent = ConditionNode(None, "---")
        out, _, _ = self._to_parenthesis_tree(conds, parent, token_idx, cond_index)
        return out

    def _to_parenthesis_tree(
            self, conds: [str], parent: ConditionNode, token_idx: int = 0, cond_index: int = 0
    ) -> (ConditionNode, int, int):
        """
        Traverse LS DFS
        Parameters
        ----------
        conds list[str]: array/list of tokens created by tokenize method
        parent: Root Node
        token_idx: Nodes token number starting from
        cond_index

        Returns
        -------

        """
        conds_len = len(conds)
        if conds_len == 0 or conds_len - cond_index <= 0:
            return parent
        while len(conds) > cond_index:
            cond = conds[cond_index]
            if cond.strip() == '(':
                parenthesis_node = ConditionNode(parent, "(", None, token_index=token_idx)
                parenthesis_node.value = "("
                parenthesis_node.token_index = token_idx
                c_node, token_idx, cond_index = self._to_parenthesis_tree(conds, parenthesis_node, token_idx + 1,
                                                                          cond_index + 1)
                if len(c_node.children) == 1:  # we simplify the parenthesis
                    parenthesis_node.token_index = c_node.children[0].token_index
                    parenthesis_node.value = c_node.children[0].value
                    parenthesis_node.children = []
            elif cond.strip() == ')':
                return parent, token_idx - 1, cond_index
            else:
                ConditionNode(parent, value=cond, children=None, token_index=token_idx)
            token_idx = token_idx + 1
            cond_index = cond_index + 1
        return parent, token_idx, cond_index

    def __tokenize_parenthesized_condition(self, split_cond: [str], idx: int) -> ([str | typing.List[typing.Any]], int):
        """

        Parameters
        ----------
        split_cond
        idx

        Returns
        -------

        """
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


class DeclareParserUtility:

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


class DeclareParseDetector:
    CONSTRAINTS_TEMPLATES_PATTERN = r"^(.*)\[(.*)\]\s*(.*)$"

    def __init__(self, lines: [str]):
        self.lines = lines

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
        x = re.search(r"^(?!bind)([a-zA-Z_,0-9.?: ]+) *(: *[\w,.? ]+)$", line, re.MULTILINE)
        if x is None:
            return False
        groups_len = len(x.groups())
        return groups_len >= 2

    @staticmethod
    def is_constraint_template_definition(line: str) -> bool:
        x = re.search(DeclareParseDetector.CONSTRAINTS_TEMPLATES_PATTERN, line, re.MULTILINE)
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


class DeclareParser:

    def __init__(self):
        super().__init__()
        self.model: DeclModel | None = None
        self.dp_utilty = DeclareParserUtility()

    def parse_decl_model(self, model_path) -> None:
        """
        Parse the input DECLARE model.

        Parameters
        ----------
        model_path : str
            File path where the DECLARE model is stored.
        """
        self.model = self.parse_decl_from_file(model_path)

    def parse_data_cond(self, cond: str):
        return self.dp_utilty.parse_data_cond(cond)

    def parse_time_cond(self, condition: str):
        return self.dp_utilty.parse_data_cond(condition)

    def parse_decl_from_file(self, path: str) -> DeclModel:
        return self.parse_from_file(path)

    def parse_decl_from_string(self, decl_string: str) -> DeclModel:
        return self.parse_from_string(decl_string)

    def parse_from_file(self, filename: str) -> DeclModel:
        with open(filename, "r+") as file:
            self.lines = file.readlines()
        model: DeclModel = self.parse()
        return model

    def parse_from_string(self, content: str, new_line_ctrl: str = "\n") -> DeclModel:
        self.lines = content.split(new_line_ctrl)
        model: DeclModel = self.parse()
        return model

    def parse(self) -> DeclModel:
        return self.parse_decl(self.lines)

    def parse_decl(self, lines) -> DeclModel:
        decl_model = DeclModel()
        dpm = DeclareParsedModel()
        decl_model.parsed_model = dpm
        for line in lines:
            line = line.strip()
            if len(line) <= 1 or line.startswith("#"):  # line starting with # considered a comment line
                continue
            if DeclareParseDetector.is_event_name_definition(line):  # split[0].strip() == 'activity':
                split = line.split(maxsplit=1)
                decl_model.activities.append(split[1].strip())
                dpm.add_event(split[1], split[0])
            elif DeclareParseDetector.is_event_attributes_definition(line):
                split = line.split(": ", maxsplit=1)  # Assume complex "bind act3: categorical, integer, org:group"
                event_name = split[0].split(" ", maxsplit=1)[1].strip()
                attrs = split[1].strip().split(",", )
                for attr in attrs:
                    dpm.add_attribute(event_name, attr.strip())
            elif DeclareParseDetector.is_events_attrs_value_definition(line):
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
                typ = DeclareParseDetector.detect_declare_attr_value_type(value)
                for attr in attributes_list:
                    dpm.add_attribute_value(attr, typ, value)
            elif DeclareParseDetector.is_constraint_template_definition(line):
                split = line.split("[", 1)
                template_search = re.search(r'(^.+?)(\d*$)', split[0])
                if template_search is not None:
                    template_str, cardinality = template_search.groups()
                    template = DeclareTemplate.get_template_from_string(template_str)
                    if template is not None:
                        activities = split[1].split("]")[0]
                        tmp = {
                            "template": template,
                            "activities": activities,
                            "condition": re.split(r'\s+\|', line)[1:]
                        }
                        if template.supports_cardinality:
                            tmp['n'] = 1 if not cardinality else int(cardinality)
                            cardinality = tmp['n']
                        decl_model.constraints.append(tmp)
                        dpm.add_template(line.strip(), template, cardinality)
        decl_model.set_constraints()
        dpm.template_constraints = decl_model.constraints
        return decl_model


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
    template: DeclareTemplate | None
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

    def add_template(self, line: str, template: DeclareTemplate, cardinality: str):
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


class DeclModel(LTLModel):
    parsed_model: DeclareParsedModel

    def __init__(self):
        super().__init__()
        self.activities = []
        self.serialized_constraints = []
        self.constraints = []
        self.parsed_model = DeclareParsedModel()

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
