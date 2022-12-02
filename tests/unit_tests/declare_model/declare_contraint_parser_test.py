import unittest
import warnings

from src.declare4py.log_utils.parsers.declare.ConstraintConditionResolver import DeclareConditionTokenizer


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
            actual = my_tree.tree_to_string().strip()
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
            actual = my_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_3_tree_2(self):
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

    def test_3_decl_constraint_conditions_parse_4_tree_2(self):
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

    def test_3_decl_constraint_conditions_parse_5_tree_2(self):
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


    # TESTING THIRD LEVEL TREE OF CONDITION RESOLVER STRATEGY

    def test_3_decl_constraint_conditions_parse_1_tree_3(self):
        # conditions = ["A.attr > 2 and A.attr < 5", "A.attr < 5 and A.attr2 in (2, x, 7r8745)"]
        conditions = ["A.attr > 2"]
        expected = ["->(ID=\"1\", parentId=\"-\", value:\"A.attr>2\")"]
        dct = DeclareConditionTokenizer()
        for i, cond in enumerate(conditions):
            tokenized_list = dct.tokenize(cond)
            my_tree = dct.to_parenthesis_tree(tokenized_list)
            actual = my_tree.tree_to_string().strip()
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
            actual = my_tree.tree_to_string().strip()
            self.assertEqual(expected[i], actual)

    def test_3_decl_constraint_conditions_parse_3_tree_3(self):
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

    def test_3_decl_constraint_conditions_parse_4_tree_3(self):
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

    def test_3_decl_constraint_conditions_parse_5_tree_3(self):
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

    # ..................................................

    def test_5_decl_constraint_disjunction_conditions_tokenize(self):
        conditions = ["A.attr > 2 or A.attr < 5", "A.attr < 5 or A.attr2 in (2, x, 7r8745)"]
        dct = DeclareConditionTokenizer()
        for cond in conditions:
            dct.parse_to_tree(cond)

    def test_5_decl_constraint_conditions_parenthesized_tokenize(self):
        conditions = ["(A.attr > 2) or (A.attr < 5)", "(A.attr < 5 or A.attr2 in (2, x, 7r8745))"
                      "(A.attr is xyz) and (a.attr is xsy) or (a.attr in (xd,f,e,e))"]
        dct = DeclareConditionTokenizer()
        for cond in conditions:
            dct.parse_to_tree(cond)

    def test_6_decl_complex_constraint_condition(self):
        # conditions = "(A.attr is x and A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4)" \
        #              " and (A.attr3 in (x, y, z) and (A.attr5 > 5) or (A.attr6 > 1 and A.attr6  < 3)) or (A.at is x)" \
        #              " or (A.ar is true) and (A.attr7 is false) and ((A.a1 is true) or (A.a2 is false)))"
        conditions = "(A.attr is x and A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4)" \
                     " and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3) or (A.at is x)" \
                     " or (A.ar is true) and (A.attr7 is false) and (A.a1 is true) or (A.a2 is false))"
        dct = DeclareConditionTokenizer()
        dct.parse_to_tree(conditions)

    def test_7_decl_complex_constraint_condition(self):
        conditions = "A.grade > 8 and (A.point >= 5 and A.name in (marco, polo, franco)) or (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4)" \
                     " and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3) or (A.at is x)" \
                     " or (A.ar is true) and (A.attr7 is false) and ((A.a1 is true) or (A.a2 is false)))"
        dct = DeclareConditionTokenizer()
        dct.parse_to_tree(conditions)

    def test_8_decl_complex_constraint_condition(self):
        # conditions = "A.attr is x and (A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4)) and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3)"
        conditions = "A.attr is x and (A.attr2 in (x, y, z) or (A.attr > 3)) and (A.attr3 is yes and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3)"
        # conditions = "A.points > 8 and A.grade > 13 or (A.name in (x,y,z) or A.session_one is true)"
        dct = DeclareConditionTokenizer()
        dct.parse_to_tree(conditions)

    def test_9_decl_complex_constraint_condition(self):
        conditions = "(A.attr is x and A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4) and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3))"
        # conditions = "A.points > 8 and A.grade > 13 or (A.name in (x,y,z) or A.session_one is true)"
        dct = DeclareConditionTokenizer()
        dct.parse_to_tree(conditions)

    def test_10_decl_complex_constraint_condition(self):
        conditions = "(A.attr is x and A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3)) and A.ciao is hello"
        # conditions = "A.points > 8 and A.grade > 13 or (A.name in (x,y,z) or A.session_one is true)"
        dct = DeclareConditionTokenizer()
        dct.parse_to_tree(conditions)


    def test_11_decl_complex_constraint_condition(self):
        # conditions = "A.points > 8 or A.grade > 13 or (A.name in (x,y,z) or A.session_one is true) or (B.name is x and B.has in (y, z))"
        # conditions = "(A.attr is x and A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4) and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3))"
        conditions = "(A.attr is x and A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4 or B>5 or B in (c,d) or b is true) and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3))"
        conditions = "(A.attr is x and A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4 or B>5 or B in (c,d) or b is true) and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3))"
        conditions = "A.points > 8 and A.grade > 13 or (A.name in (x,y,z) or A.session_one is true)"
        conditions = "A.points > 8 or A.grade > 13 or (A.name in (x,y,z) or A.session_one is true)"
        dct = DeclareConditionTokenizer()
        dct.parse_to_tree(conditions)

    def test_12_decl_complex_constraint_condition(self):
        conditions = "A.points > 8 or A.grade > 13 or (A.name in (x,y,z) or A.session_one is true) or (B.name is x and B.has in (y, z))"
        # conditions = "A.points > 8 and A.grade > 13 or (A.name in (x,y,z) or A.session_one is true)"
        dct = DeclareConditionTokenizer()
        dct.parse_to_tree(conditions)

    def test_13_decl_complex_constraint_condition(self):
        # conditions = "A.points > 8 and A.grade > 13 and (A.name in (x,y,z) or A.session_one is true) and (B.name is x and B.has in (y, z))"
        conditions = "A.points > 8 and (B.name is x and B.has in (y, z))"
        conditions = "A.points > 8 and B.name is X"
        conditions = "A.points > 8"
        # conditions = "(B.name is x and B.has in (y, z))"
        # conditions = "B.name is x and B.has in (y, z)"
        # conditions = "A.points > 8 and A.grade > 13 or (A.name in (x,y,z) or A.session_one is true)"
        dct = DeclareConditionTokenizer()
        dct.parse_to_tree(conditions)


if __name__ == '__main__':
    unittest.main()

