import unittest
import warnings

from src.declare4py.log_utils.parsers.declare.declare_condition_parser import DeclareConditionTokenizer
from src.declare4py.log_utils.parsers.declare.declare_condition_parser import ConditionNode


class DeclareConstraintParserTest(unittest.TestCase):

    def test_0_decl_constraint_condition_tokenize_1(self):
        condition = "A.attr > 2"
        dct = DeclareConditionTokenizer()
        s = dct.tokenize(condition)
        self.assertEqual(["A.attr>2"], s, "Expecting the same condition")

    def test_1_decl_constraint_condition_tokenize_2(self):
        conditions = ["A.attr >= 2", "A.attr < 2", "A.attr = 2", "A.attr != 2",
                      "A.attr is True", "A.attr is False", "A.attr is false", "(A.attr > 5)"]
        expected_result = [
            ["A.attr>=2"], ["A.attr<2"], ["A.attr=2"], ["A.attr!=2"], ["A.attr=True"],
            ["A.attr=False"], ["A.attr=false"], ["(", "A.attr>5", ")"]
        ]
        dct = DeclareConditionTokenizer()
        for idx, cond in enumerate(conditions):
            output = dct.tokenize(cond)
            self.assertEqual(expected_result[idx], output)

    def test_1_decl_constraint_condition_tokenize_3(self):
        # Checking "is" and "is not"
        conditions = ["A.attr is 2", "A.attr is not 2"]
        expected_result = [["A.attr=2"], ["A.attr!=2"]]
        warnings.warn("not sure for this tests yet")
        dct = DeclareConditionTokenizer()
        for idx, cond in enumerate(conditions):
            output = dct.tokenize(cond)
            self.assertEqual(expected_result[idx], output)

    def test_1_decl_constraint_condition_tokenize_4(self):
        conditions = ["A.attr in (2, 3, x)", "A.attr not in (2, 3, x)"]
        expected_result = [["A.attr in (2,3,x)"], ["A.attr not_in (2,3,x)"]]
        dct = DeclareConditionTokenizer()
        for idx, cond in enumerate(conditions):
            output = dct.tokenize(cond)
            self.assertEqual(expected_result[idx], output)

    def test_1_decl_constraint_condition_in_tokenize(self):
        conditions = ["A.attr in (2, 3, x)", "A.attr not in (2, 3, x)", "(A.attr not in (2, 3, x))"]
        expected_result = [
            ["A.attr", "in", "(", "2,", "3,", "x", ")"],
            ["A.attr", "not_in", "(", "2,", "3,", "x", ")"],
            ["(", "A.attr", "not_in", "(", "2,", "3,", "x", ")", ")"]
        ]
        dct = DeclareConditionTokenizer()
        for idx, cond in enumerate(conditions):
            output = dct.normalize_condition_string_to_tokenize(cond)
            split_cond = output.split(" ")
            self.assertEqual(expected_result[idx], split_cond)

    def test_2_decl_constraint_condition_tokenize_1(self):
        conditions = ["A.attr >= 2 and A.attr<5", "A.attr != 2 or A.attr is True"]
        expected_result = [["A.attr>=2", "and", "A.attr<5"], ["A.attr!=2", "or", "A.attr=True"]]
        dct = DeclareConditionTokenizer()
        for idx, cond in enumerate(conditions):
            output = dct.tokenize(cond)
            self.assertEqual(expected_result[idx], output)

    def test_2_decl_constraint_condition_tokenize_2(self):
        conditions = ["A.attr >= 2 and A.attr<5 and A.attr2 in (2, x, 7r8745)"]
        expected_result = [["A.attr>=2", "and", "A.attr<5", "and", "A.attr2 in (2,x,7r8745)"]]
        dct = DeclareConditionTokenizer()
        for idx, cond in enumerate(conditions):
            output = dct.tokenize(cond)
            self.assertEqual(expected_result[idx], output)

    # TESTING FIRST LEVEL TREE OF CONDITION RESOLVER STRATEGY

    def test_3_decl_constraint_conditions_parse_1_tree_1(self):
        # conditions = ["A.attr > 2 and A.attr < 5", "A.attr < 5 and A.attr2 in (2, x, 7r8745)"]
        conditions = ["A.attr > 2"]
        expected = ["->(ID=\"1\", parentId=\"-\", value:\"A.attr>2\")"]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            actual = my_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_2_tree_1(self):
        conditions = [
            "A.attr > 2",
            "A.attr = 2",
            "A.attr is 2",
            "A.attr is not 2",
            "A.attr in (x,y,z)",
            "A.attr not_in (x,y,z)"
        ]
        expected = [
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr>2\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr=2\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr=2\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr!=2\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr in (x,y,z)\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr not_in (x,y,z)\")",
        ]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            actual = my_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_3_tree_1(self):
        conditions = ["A.attr > 2 and A.attr = 2 or A.attr is 2 or A.attr is not 2"]
        expected = [
            """->(ID="0", parentId="-", value:"---")
-->(ID="1", parentId="0", value:"A.attr>2")
-->(ID="2", parentId="0", value:"and")
-->(ID="3", parentId="0", value:"A.attr=2")
-->(ID="4", parentId="0", value:"or")
-->(ID="5", parentId="0", value:"A.attr=2")
-->(ID="6", parentId="0", value:"or")
-->(ID="7", parentId="0", value:"A.attr!=2")"""]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            actual = my_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_4_tree_1(self):
        conditions = ["A.attr > 2 and (A.attr = 2 or A.attr is 2) or A.attr is not 2"]
        expected = [
            """->(ID="0", parentId="-", value:"---")
-->(ID="1", parentId="0", value:"A.attr>2")
-->(ID="2", parentId="0", value:"and")
-->(ID="3", parentId="0", value:"(")
--->(ID="4", parentId="3", value:"A.attr=2")
--->(ID="5", parentId="3", value:"or")
--->(ID="6", parentId="3", value:"A.attr=2")
-->(ID="7", parentId="0", value:"or")
-->(ID="8", parentId="0", value:"A.attr!=2")"""]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            actual = my_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_5_tree_1(self):
        conditions = ["A.attr > 2 and (A.attr = 8 and A.attr > 3) or A.attr is not 2"]
        expected = [
            """->(ID="0", parentId="-", value:"---")
-->(ID="1", parentId="0", value:"A.attr>2")
-->(ID="2", parentId="0", value:"and")
-->(ID="3", parentId="0", value:"(")
--->(ID="4", parentId="3", value:"A.attr=8")
--->(ID="5", parentId="3", value:"and")
--->(ID="6", parentId="3", value:"A.attr>3")
-->(ID="7", parentId="0", value:"or")
-->(ID="8", parentId="0", value:"A.attr!=2")"""]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            actual = my_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    # TESTING SECOND LEVEL TREE OF CONDITION RESOLVER STRATEGY

    def test_3_decl_constraint_conditions_parse_1_tree_2(self):
        # conditions = ["A.attr > 2 and A.attr < 5", "A.attr < 5 and A.attr2 in (2, x, 7r8745)"]
        conditions = ["A.attr > 2"]
        expected = ["->(ID=\"1\", parentId=\"-\", value:\"A.attr>2\")"]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            or_tree = dct.to_OR_tree(my_tree)
            actual = or_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_2_tree_2(self):
        conditions = [
            "A.attr > 2",
            "A.attr = 2",
            "A.attr is 2",
            "A.attr is not 2",
            "A.attr in (x,y,z)",
            "A.attr not_in (x,y,z)"
        ]
        expected = [
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr>2\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr=2\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr=2\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr!=2\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr in (x,y,z)\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr not_in (x,y,z)\")",
        ]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            or_tree = dct.to_OR_tree(my_tree)
            actual = or_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_3_tree_2(self):
        conditions = ["A.attr > 2 and A.attr = 2 or A.attr is 2 or A.attr is not 2"]
        expected = [
            """->(ID="0", parentId="-", value:"")
-->(ID="9", parentId="0", value:"OR")
--->(ID="1", parentId="9", value:"A.attr>2")
--->(ID="2", parentId="9", value:"and")
--->(ID="3", parentId="9", value:"A.attr=2")
-->(ID="10", parentId="0", value:"OR")
--->(ID="5", parentId="10", value:"A.attr=2")
-->(ID="11", parentId="0", value:"OR")
--->(ID="7", parentId="11", value:"A.attr!=2")"""]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            # my_tree.display_tree_graph("parenthesis")  # if want to see the graph
            or_tree = dct.to_OR_tree(my_tree)
            # or_tree.display_tree_graph()
            actual = or_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_4_tree_2(self):
        conditions = ["A.attr > 2 and (A.attr = 2 or A.attr is 2) or A.attr is not 2"]
        expected = [
            """->(ID="0", parentId="-", value:"")
-->(ID="11", parentId="0", value:"OR")
--->(ID="1", parentId="11", value:"A.attr>2")
--->(ID="2", parentId="11", value:"and")
--->(ID="3", parentId="11", value:"(")
---->(ID="11", parentId="3", value:"OR")
----->(ID="4", parentId="11", value:"A.attr=2")
---->(ID="12", parentId="3", value:"OR")
----->(ID="6", parentId="12", value:"A.attr=2")
-->(ID="12", parentId="0", value:"OR")
--->(ID="8", parentId="12", value:"A.attr!=2")"""]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            # my_tree.display_tree_graph("parenthesis")
            or_tree = dct.to_OR_tree(my_tree)
            # or_tree.display_tree_graph()
            actual = or_tree.tree_to_string().strip()
            # print(actual)
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_5_tree_2(self):
        conditions = ["A.attr > 2 and (A.attr = 8 and A.attr > 3) or A.attr is not 2"]
        expected = [
            """->(ID="0", parentId="-", value:"")
-->(ID="11", parentId="0", value:"OR")
--->(ID="1", parentId="11", value:"A.attr>2")
--->(ID="2", parentId="11", value:"and")
--->(ID="3", parentId="11", value:"(")
---->(ID="4", parentId="3", value:"A.attr=8")
---->(ID="5", parentId="3", value:"and")
---->(ID="6", parentId="3", value:"A.attr>3")
-->(ID="12", parentId="0", value:"OR")
--->(ID="8", parentId="12", value:"A.attr!=2")"""]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            or_tree = dct.to_OR_tree(my_tree)
            actual = or_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_6_tree_2(self):
        conditions = ["A.attr > 2 and (A.attr = 2 or (A.attr is 2 and A.ciao is hello (bru>4 or tup>5 or (chad is false)))) or A.attr is not 2"]
        expected = ["""->(ID="0", parentId="-", value:"")
-->(ID="20", parentId="0", value:"OR")
--->(ID="1", parentId="20", value:"A.attr>2")
--->(ID="2", parentId="20", value:"and")
--->(ID="3", parentId="20", value:"(")
---->(ID="20", parentId="3", value:"OR")
----->(ID="4", parentId="20", value:"A.attr=2")
---->(ID="22", parentId="3", value:"OR")
----->(ID="6", parentId="22", value:"(")
------>(ID="7", parentId="6", value:"A.attr=2")
------>(ID="8", parentId="6", value:"and")
------>(ID="9", parentId="6", value:"A.ciao=hello")
------>(ID="10", parentId="6", value:"(")
------->(ID="23", parentId="10", value:"OR")
-------->(ID="11", parentId="23", value:"bru>4")
------->(ID="24", parentId="10", value:"OR")
-------->(ID="13", parentId="24", value:"tup>5")
------->(ID="25", parentId="10", value:"OR")
-------->(ID="16", parentId="25", value:"chad=false")
-->(ID="21", parentId="0", value:"OR")
--->(ID="18", parentId="21", value:"A.attr!=2")"""]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            or_tree = dct.to_OR_tree(my_tree)
            actual = or_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)


    # TESTING THIRD LEVEL TREE OF CONDITION RESOLVER STRATEGY

    def test_3_decl_constraint_conditions_parse_1_tree_3(self):
        # conditions = ["A.attr > 2 and A.attr < 5", "A.attr < 5 and A.attr2 in (2, x, 7r8745)"]
        conditions = ["A.attr > 2"]
        expected = ["->(ID=\"1\", parentId=\"-\", value:\"A.attr>2\")"]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            or_tree = dct.to_OR_tree(my_tree)
            and_tree = dct.generate_AND_tree(or_tree)
            actual = and_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_2_tree_3(self):
        conditions = [
            "A.attr > 2",
            "A.attr = 2",
            "A.attr is 2",
            "A.attr is not 2",
            "A.attr in (x,y,z)",
            "A.attr not_in (x,y,z)"
        ]
        expected = [
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr>2\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr=2\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr=2\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr!=2\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr in (x,y,z)\")",
            "->(ID=\"1\", parentId=\"-\", value:\"A.attr not_in (x,y,z)\")",
        ]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            or_tree = dct.to_OR_tree(my_tree)
            and_tree = dct.generate_AND_tree(or_tree)
            actual = and_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_3_tree_3(self):
        conditions = ["A.attr > 2 and A.attr = 2 or A.attr is 2 or A.attr is not 2"]
        expected = [
            """->(ID="0", parentId="-", value:"")
-->(ID="9", parentId="0", value:"OR")
--->(ID="2", parentId="9", value:"and")
---->(ID="1", parentId="2", value:"A.attr>2")
---->(ID="3", parentId="2", value:"A.attr=2")
-->(ID="10", parentId="0", value:"OR")
--->(ID="5", parentId="10", value:"A.attr=2")
-->(ID="11", parentId="0", value:"OR")
--->(ID="7", parentId="11", value:"A.attr!=2")"""]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            or_tree = dct.to_OR_tree(my_tree)
            # or_tree.display_tree_graph("or_tree")
            and_tree = dct.generate_AND_tree(or_tree)
            # and_tree.display_tree_graph()
            actual = and_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_4_tree_3(self):
        conditions = ["A.attr > 2 and (A.attr = 2 or A.attr is 2) or A.attr is not 2"]
        expected = [
            """->(ID="0", parentId="-", value:"")
-->(ID="11", parentId="0", value:"OR")
--->(ID="2", parentId="11", value:"and")
---->(ID="1", parentId="2", value:"A.attr>2")
---->(ID="3", parentId="2", value:"(")
----->(ID="11", parentId="3", value:"OR")
------>(ID="4", parentId="11", value:"A.attr=2")
----->(ID="12", parentId="3", value:"OR")
------>(ID="6", parentId="12", value:"A.attr=2")
-->(ID="12", parentId="0", value:"OR")
--->(ID="8", parentId="12", value:"A.attr!=2")"""]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            or_tree = dct.to_OR_tree(my_tree)
            # or_tree.display_tree_graph("or_tree")
            and_tree = dct.generate_AND_tree(or_tree)
            # and_tree.display_tree_graph()
            actual = and_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_5_tree_3(self):
        conditions = ["A.attr > 2 and (A.attr = 8 and A.attr > 3) or A.attr is not 2"]
        expected = [
            """->(ID="0", parentId="-", value:"")
-->(ID="11", parentId="0", value:"OR")
--->(ID="2", parentId="11", value:"and")
---->(ID="1", parentId="2", value:"A.attr>2")
---->(ID="3", parentId="2", value:"(")
----->(ID="5", parentId="3", value:"and")
------>(ID="4", parentId="5", value:"A.attr=8")
------>(ID="6", parentId="5", value:"A.attr>3")
-->(ID="12", parentId="0", value:"OR")
--->(ID="8", parentId="12", value:"A.attr!=2")"""]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            or_tree = dct.to_OR_tree(my_tree)
            and_tree = dct.generate_AND_tree(or_tree)
            actual = and_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_6_tree_3(self):
        conditions = ["A.attr > 2 and (A.attr = 2 or (A.attr is 2 and A.ciao is hello (bru>4 or tup>5 or (chad is false)))) or A.attr is not 2"]
        expected = ["""->(ID="0", parentId="-", value:"")
-->(ID="20", parentId="0", value:"OR")
--->(ID="2", parentId="20", value:"and")
---->(ID="1", parentId="2", value:"A.attr>2")
---->(ID="3", parentId="2", value:"(")
----->(ID="20", parentId="3", value:"OR")
------>(ID="4", parentId="20", value:"A.attr=2")
----->(ID="22", parentId="3", value:"OR")
------>(ID="6", parentId="22", value:"(")
------->(ID="8", parentId="6", value:"and")
-------->(ID="7", parentId="8", value:"A.attr=2")
-------->(ID="9", parentId="8", value:"A.ciao=hello")
-------->(ID="10", parentId="8", value:"(")
--------->(ID="23", parentId="10", value:"OR")
---------->(ID="11", parentId="23", value:"bru>4")
--------->(ID="24", parentId="10", value:"OR")
---------->(ID="13", parentId="24", value:"tup>5")
--------->(ID="25", parentId="10", value:"OR")
---------->(ID="16", parentId="25", value:"chad=false")
-->(ID="21", parentId="0", value:"OR")
--->(ID="18", parentId="21", value:"A.attr!=2")"""]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            or_tree = dct.to_OR_tree(my_tree)
            and_tree = dct.generate_AND_tree(or_tree)
            actual = and_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    # ..................................................

    def test_5_decl_constraint_conditions_parenthesized_tokenize(self):
        conditions = [
            "(A.attr > 2) or (A.attr < 5)",
            "(A.attr < 5 or A.attr2 in (2, x, 7r8745))",
            "(A.attr is xyz) and (a.attr is xsy) or (a.attr in (xd,f,e,e))"
        ]
        expected = ["""->(ID="0", parentId="-", value:"")
-->(ID="5", parentId="0", value:"OR")
--->(ID="2", parentId="5", value:"A.attr>2")
-->(ID="6", parentId="0", value:"OR")
--->(ID="5", parentId="6", value:"A.attr<5")""",
                    """->(ID="0", parentId="-", value:"")
-->(ID="1", parentId="0", value:"(")
--->(ID="7", parentId="1", value:"OR")
---->(ID="2", parentId="7", value:"A.attr<5")
--->(ID="8", parentId="1", value:"OR")
---->(ID="4", parentId="8", value:"A.attr2 in (2,x,7r8745)")""",
                    """->(ID="0", parentId="-", value:"")
-->(ID="7", parentId="0", value:"OR")
--->(ID="3", parentId="7", value:"and")
---->(ID="2", parentId="3", value:"A.attr=xyz")
---->(ID="5", parentId="3", value:"a.attr=xsy")
-->(ID="8", parentId="0", value:"OR")
--->(ID="8", parentId="8", value:"a.attr in (xd,f,e,e)")"""]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            logic_tree = dct.parse_to_logic_tree(cond)
            actual = logic_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_6_decl_complex_constraint_condition(self):
        conditions = "(A.attr is x and A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4)" \
                     " and (A.attr3 in (x, y, z) and (A.attr5 > 5) or (A.attr6 > 1 and A.attr6  < 3)) or (A.at is x)" \
                     " or (A.ar is true) and (A.attr7 is false) and ((A.a1 is true) or (A.a2 is false)))"
        # conditions = "(A.attr is x and A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4)" \
        #              " and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3) or (A.at is x)" \
        #              " or (A.ar is true) and (A.attr7 is false) and (A.a1 is true) or (A.a2 is false))"
        expected = """->(ID="0", parentId="-", value:"")
-->(ID="1", parentId="0", value:"(")
--->(ID="35", parentId="1", value:"OR")
---->(ID="3", parentId="35", value:"and")
----->(ID="2", parentId="3", value:"A.attr=x")
----->(ID="4", parentId="3", value:"A.attr2 in (x,y,z)")
--->(ID="38", parentId="1", value:"OR")
---->(ID="13", parentId="38", value:"and")
----->(ID="7", parentId="13", value:"A.attr>3")
----->(ID="9", parentId="13", value:"(")
------>(ID="11", parentId="9", value:"and")
------->(ID="10", parentId="11", value:"A.attr3>5")
------->(ID="12", parentId="11", value:"A.attr<4")
----->(ID="14", parentId="13", value:"(")
------>(ID="38", parentId="14", value:"OR")
------->(ID="16", parentId="38", value:"and")
-------->(ID="15", parentId="16", value:"A.attr3 in (x,y,z)")
-------->(ID="18", parentId="16", value:"A.attr5>5")
------>(ID="40", parentId="14", value:"OR")
------->(ID="20", parentId="40", value:"(")
-------->(ID="22", parentId="20", value:"and")
--------->(ID="21", parentId="22", value:"A.attr6>1")
--------->(ID="23", parentId="22", value:"A.attr6<3")
--->(ID="39", parentId="1", value:"OR")
---->(ID="26", parentId="39", value:"A.at=x")
--->(ID="41", parentId="1", value:"OR")
---->(ID="33", parentId="41", value:"and")
----->(ID="29", parentId="33", value:"A.ar=true")
----->(ID="32", parentId="33", value:"A.attr7=false")
----->(ID="34", parentId="33", value:"(")
------>(ID="41", parentId="34", value:"OR")
------->(ID="36", parentId="41", value:"A.a1=true")
------>(ID="42", parentId="34", value:"OR")
------->(ID="39", parentId="42", value:"A.a2=false")"""
        dct = DeclareConditionTokenizer()
        dts = dct.parse_to_logic_tree(conditions)
        # print(dts.tree_to_string())
        actual = dts.tree_to_string().strip()
        self.assertEqual(expected, actual)

    # @unittest.expectedFailure
    def test_7_decl_complex_constraint_condition(self):
        conditions = "A.grade > 8 and (A.point >= 5 and A.name in (marco, polo, franco)) or (A.attr > 3) and" \
                     " (A.attr3 > 5 and A.attr  < 4)" \
                     " and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3) or (A.at is x)" \
                     " or (A.ar is true) and (A.attr7 is false) and ((A.a1 is true) or (A.a2 is false)))"
        dct = DeclareConditionTokenizer()
        with self.assertRaises(SyntaxError):
            dct.parse_to_logic_tree(conditions)

    def test_8_decl_complex_constraint_condition(self):
        """
        Starting without parenthesis a condition
        Returns
        -------

        """
        conditions = "A.attr is x and (A.attr2 in (x, y, z) or (A.attr > 3)) and (A.attr3 is yes and" \
                     " (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3)"
        # conditions = "A.points > 8 and A.grade > 13 or (A.name in (x,y,z) or A.session_one is true)"
        dct = DeclareConditionTokenizer()
        lt = dct.parse_to_logic_tree(conditions)  # lt = LogicalTree
        self.assertEqual("""->(ID="0", parentId="-", value:"")
-->(ID="20", parentId="0", value:"OR")
--->(ID="8", parentId="20", value:"and")
---->(ID="1", parentId="8", value:"A.attr=x")
---->(ID="3", parentId="8", value:"(")
----->(ID="19", parentId="3", value:"OR")
------>(ID="4", parentId="19", value:"A.attr2 in (x,y,z)")
----->(ID="20", parentId="3", value:"OR")
------>(ID="7", parentId="20", value:"A.attr>3")
---->(ID="9", parentId="8", value:"(")
----->(ID="11", parentId="9", value:"and")
------>(ID="10", parentId="11", value:"A.attr3=yes")
------>(ID="13", parentId="11", value:"A.attr5>5")
-->(ID="22", parentId="0", value:"OR")
--->(ID="15", parentId="22", value:"(")
---->(ID="17", parentId="15", value:"and")
----->(ID="16", parentId="17", value:"A.attr6>1")
----->(ID="18", parentId="17", value:"A.attr6<3")""", lt.tree_to_string().strip())

    def test_9_decl_complex_constraint_condition(self):
        """
        Whole condition wrapped in Parenthesis
        Returns
        -------

        """
        conditions = "(A.attr is x and A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4)" \
                     " and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3))"
        expected = """->(ID="0", parentId="-", value:"")
-->(ID="1", parentId="0", value:"(")
--->(ID="24", parentId="1", value:"OR")
---->(ID="3", parentId="24", value:"and")
----->(ID="2", parentId="3", value:"A.attr=x")
----->(ID="4", parentId="3", value:"A.attr2 in (x,y,z)")
--->(ID="27", parentId="1", value:"OR")
---->(ID="13", parentId="27", value:"and")
----->(ID="7", parentId="13", value:"A.attr>3")
----->(ID="9", parentId="13", value:"(")
------>(ID="11", parentId="9", value:"and")
------->(ID="10", parentId="11", value:"A.attr3>5")
------->(ID="12", parentId="11", value:"A.attr<4")
----->(ID="14", parentId="13", value:"(")
------>(ID="16", parentId="14", value:"and")
------->(ID="15", parentId="16", value:"A.attr3 in (x,y,z)")
------->(ID="18", parentId="16", value:"A.attr5>5")
--->(ID="29", parentId="1", value:"OR")
---->(ID="20", parentId="29", value:"(")
----->(ID="22", parentId="20", value:"and")
------>(ID="21", parentId="22", value:"A.attr6>1")
------>(ID="23", parentId="22", value:"A.attr6<3")"""
        dct = DeclareConditionTokenizer()
        lt = dct.parse_to_logic_tree(conditions)
        self.assertEqual(expected, lt.tree_to_string().strip())

    def test_10_decl_complex_constraint_condition(self):
        # After first parenthesis there is and condition at the end outside of parenthesis
        conditions = "(A.attr is x and A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 in (x, y, z) and (A.attr5 > 5)) " \
                     "or (A.attr6 > 1 and A.attr6  < 3)) and A.ciao is hello"
        # conditions = "A.points > 8 and A.grade > 13 or (A.name in (x,y,z) or A.session_one is true)"
        expected = """->(ID="0", parentId="-", value:"")
-->(ID="19", parentId="0", value:"and")
--->(ID="1", parentId="19", value:"(")
---->(ID="21", parentId="1", value:"OR")
----->(ID="3", parentId="21", value:"and")
------>(ID="2", parentId="3", value:"A.attr=x")
------>(ID="4", parentId="3", value:"A.attr2 in (x,y,z)")
---->(ID="23", parentId="1", value:"OR")
----->(ID="8", parentId="23", value:"and")
------>(ID="7", parentId="8", value:"A.attr>3")
------>(ID="9", parentId="8", value:"(")
------->(ID="11", parentId="9", value:"and")
-------->(ID="10", parentId="11", value:"A.attr3 in (x,y,z)")
-------->(ID="13", parentId="11", value:"A.attr5>5")
---->(ID="25", parentId="1", value:"OR")
----->(ID="15", parentId="25", value:"(")
------>(ID="17", parentId="15", value:"and")
------->(ID="16", parentId="17", value:"A.attr6>1")
------->(ID="18", parentId="17", value:"A.attr6<3")
--->(ID="20", parentId="19", value:"A.ciao=hello")"""
        dct = DeclareConditionTokenizer()
        dct.parse_to_logic_tree(conditions)
        lt = dct.parse_to_logic_tree(conditions)
        actual = lt.tree_to_string().strip()
        # print(actual)
        self.assertEqual(expected, actual)

    def test_11_decl_complex_constraint_condition(self):
        # conditions = "A.points > 8 and A.grade > 13 and (A.name in (x,y,z) or A.session_one is true) and (B.name is x and B.has in (y, z))"
        # conditions = "A.points > 8 and (B.name is x and B.has in (y, z))"
        # conditions = "A.points > 8 and B.name is X"
        # conditions = "A.points > 8"
        # conditions = "(B.name is x and B.has in (y, z))"
        # conditions = "B.name is x and B.has in (y, z)"
        expected = """->(ID="0", parentId="-", value:"")
-->(ID="10", parentId="0", value:"OR")
--->(ID="2", parentId="10", value:"and")
---->(ID="1", parentId="2", value:"A.points>8")
---->(ID="3", parentId="2", value:"A.grade>13")
-->(ID="12", parentId="0", value:"OR")
--->(ID="5", parentId="12", value:"(")
---->(ID="12", parentId="5", value:"OR")
----->(ID="6", parentId="12", value:"A.name in (x,y,z)")
---->(ID="13", parentId="5", value:"OR")
----->(ID="8", parentId="13", value:"A.session_one=true")"""
        conditions = "A.points > 8 and A.grade > 13 or (A.name in (x,y,z) or A.session_one is true)"
        dct = DeclareConditionTokenizer()
        lt = dct.parse_to_logic_tree(conditions)
        actual = lt.tree_to_string().strip()
        self.assertEqual(expected, actual)

if __name__ == '__main__':
    unittest.main()

