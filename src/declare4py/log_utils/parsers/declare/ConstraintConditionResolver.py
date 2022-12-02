from __future__ import annotations

import re
import typing
import warnings
from enum import Enum
import uuid

try:
    """
        This is an optional library used to draw the graphs in image.
        To understand a condition, represented in form of a graph would make little easy.
    """
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

    def parse_to_logic_tree(self, condition: str, show_final_graph: bool = True):
        tokenized_list = self.tokenize(condition)
        my_tree = self.to_parenthesis_tree(tokenized_list)
        my_tree.display_tree_graph("parenthesis", format="svg")
        OR_tree = self.to_OR_tree(my_tree)
        OR_tree.display_tree_graph("or graph")
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
                c_node, token_idx, cond_index = self._to_parenthesis_tree(conds, parenthesis_node, token_idx + 1, cond_index + 1)
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
