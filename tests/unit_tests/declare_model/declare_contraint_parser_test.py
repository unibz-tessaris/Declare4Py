import unittest

from src.declare4py.log_utils.parsers.declare.ConstraintConditionResolver import DeclareConditionTokenizer


class DeclareConstraintParserTest(unittest.TestCase):

    def test_0_decl_constraint_condition_tokenize(self):
        condition = "A.attr > 2"
        dct = DeclareConditionTokenizer()
        dct.tokenize(condition)

    def test_1_decl_constraint_condition_tokenize(self):
        conditions = ["A.attr >= 2", "A.attr < 2", "A.attr = 2", "A.attr != 2"]
        expected_result = [["A.attr>=2"], "A.attr < 2", "A.attr = 2", "A.attr != 2"]
        dct = DeclareConditionTokenizer()
        for idx, cond in enumerate(conditions):
            output = dct.tokenize(cond)
            # self.assertEqual(expected_result[idx], output)

    def test_2_decl_constraint_condition_with_is_tokenize(self):
        conditions = ["A.attr is 2", "A.attr is not 2"]
        dct = DeclareConditionTokenizer()
        for cond in conditions:
            dct.tokenize(cond)

    def test_3_decl_constraint_condition_with_in_tokenize(self):
        conditions = ["A.attr in (2, x, 7r8745)", "A.attr not in (x, 2, y, zxxsd)"]
        dct = DeclareConditionTokenizer()
        for cond in conditions:
            dct.tokenize(cond)

    def test_4_decl_constraint_conjunction_conditions_tokenize(self):
        conditions = ["A.attr > 2 and A.attr < 5", "A.attr < 5 and A.attr2 in (2, x, 7r8745)"]
        dct = DeclareConditionTokenizer()
        for cond in conditions:
            dct.tokenize(cond)

    def test_5_decl_constraint_disjunction_conditions_tokenize(self):
        conditions = ["A.attr > 2 or A.attr < 5", "A.attr < 5 or A.attr2 in (2, x, 7r8745)"]
        dct = DeclareConditionTokenizer()
        for cond in conditions:
            dct.tokenize(cond)

    def test_5_decl_constraint_conditions_parenthesized_tokenize(self):
        conditions = ["(A.attr > 2) or (A.attr < 5)", "(A.attr < 5 or A.attr2 in (2, x, 7r8745))"
                      "(A.attr is xyz) and (a.attr is xsy) or (a.attr in (xd,f,e,e))"]
        dct = DeclareConditionTokenizer()
        for cond in conditions:
            dct.tokenize(cond)


if __name__ == '__main__':
    unittest.main()
