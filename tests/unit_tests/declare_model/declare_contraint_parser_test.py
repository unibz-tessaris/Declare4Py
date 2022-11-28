import unittest

from src.declare4py.log_utils.parsers.declare.ConstraintConditionResolver import DeclareConditionTokenizer


class DeclareConstraintParserTest(unittest.TestCase):

    def test_0_decl_constraint_condition_tokenize(self):
        condition = "A.attr > 2"
        dct = DeclareConditionTokenizer()
        dct.parse_to_tree(condition)

    def test_1_decl_constraint_condition_tokenize(self):
        conditions = ["A.attr >= 2", "A.attr < 2", "A.attr = 2", "A.attr != 2"]
        expected_result = [["A.attr>=2"], "A.attr < 2", "A.attr = 2", "A.attr != 2"]
        dct = DeclareConditionTokenizer()
        for idx, cond in enumerate(conditions):
            output = dct.parse_to_tree(cond)
            # self.assertEqual(expected_result[idx], output)

    def test_2_decl_constraint_condition_with_is_tokenize(self):
        conditions = ["A.attr is 2", "A.attr is not 2"]
        dct = DeclareConditionTokenizer()
        for cond in conditions:
            dct.parse_to_tree(cond)

    def test_3_decl_constraint_condition_with_in_tokenize(self):
        conditions = ["A.attr in (2, x, 7r8745)", "A.attr not in (x, 2, y, zxxsd)"]
        dct = DeclareConditionTokenizer()
        for cond in conditions:
            dct.parse_to_tree(cond)

    def test_4_decl_constraint_conjunction_conditions_tokenize(self):
        conditions = ["A.attr > 2 and A.attr < 5", "A.attr < 5 and A.attr2 in (2, x, 7r8745)"]
        dct = DeclareConditionTokenizer()
        for cond in conditions:
            dct.parse_to_tree(cond)

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
        conditions = "(A.attr is x and A.attr2 in (x, y, z) or (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4)" \
                     " and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3)) or (A.at is x)" \
                     " or (A.ar is true) and (A.attr7 is false) and ((A.a1 is true) or (A.a2 is false))"
        dct = DeclareConditionTokenizer()
        dct.parse_to_tree(conditions)

    def test_7_decl_complex_constraint_condition(self):
        conditions = "A.grade > 8 and (A.point >= 5 and A.name in (marco, polo, franco)) or ( (A.attr > 3) and (A.attr3 > 5 and A.attr  < 4)" \
                     " and (A.attr3 in (x, y, z) and (A.attr5 > 5)) or (A.attr6 > 1 and A.attr6  < 3)) or (A.at is x)" \
                     " or (A.ar is true) and (A.attr7 is false) and ((A.a1 is true) or (A.a2 is false))"
        dct = DeclareConditionTokenizer()
        dct.parse_to_tree(conditions)

    def test_8_decl_complex_constraint_condition(self):
        conditions = "A.points > 8 or A.grade > 13 or (A.name in (x,y,z) or A.session_one is true)"
        # conditions = "A.points > 8 and A.grade > 13 or (A.name in (x,y,z) or A.session_one is true)"
        dct = DeclareConditionTokenizer()
        dct.parse_to_tree(conditions)


if __name__ == '__main__':
    unittest.main()

