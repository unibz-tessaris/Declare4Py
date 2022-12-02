import unittest

from src.declare4py.log_utils.parsers.declare.ConstraintConditionResolver import ConditionNode


"""

    Unit tests for ConditionNode class/node methods
    whether they work as expected or not after new changes are implemented.
    
"""
class TreeNodeTests(unittest.TestCase):

    def test_0_create_node(self):
        cn = ConditionNode(None, "xz")
        self.assertTrue(cn.is_root())
        self.assertEqual("xz", cn.value)
        self.assertIsNotNone(cn.children)
        self.assertEqual(0, len(cn.children))
        self.assertEqual(0, cn.size_sub_nodes())

    def test_1_node_children(self):
        cn = ConditionNode(None, "parent")
        child1 = ConditionNode(cn, "child1")
        child2 = ConditionNode(cn, "child2")
        child3 = ConditionNode(cn, "child3")
        # cn.children = [child1, child2, child3]
        self.assertTrue(cn.is_root())
        self.assertFalse(child1.is_root())
        self.assertFalse(child2.is_root())
        self.assertFalse(child3.is_root())

    def test_2_node_children_length(self):
        cn = ConditionNode(None, "parent")
        child1 = ConditionNode(cn, "child1")
        child2 = ConditionNode(cn, "child2")
        child3 = ConditionNode(cn, "child3")

        self.assertIsNotNone(cn.children)
        self.assertIsNotNone(child1.children)
        self.assertIsNotNone(child2.children)
        self.assertIsNotNone(child3.children)

        self.assertEqual(3, len(cn.children))
        self.assertEqual(0, len(child1.children))
        self.assertEqual(0, len(child2.children))
        self.assertEqual(0, len(child3.children))

    def test_3_node_children_sub_nodes_size_1(self):
        cn = ConditionNode(None, "parent")
        child1 = ConditionNode(cn, "child1")
        child2 = ConditionNode(cn, "child2")
        child3 = ConditionNode(cn, "child3")

        self.assertEqual(3, cn.size_sub_nodes())
        self.assertEqual(0, child1.size_sub_nodes())
        self.assertEqual(0, child2.size_sub_nodes())
        self.assertEqual(0, child3.size_sub_nodes())

    def test_3_node_children_sub_nodes_size_2(self):
        cn = ConditionNode(None, "parent")
        child1 = ConditionNode(cn, "child1")
        child1_1 = ConditionNode(child1, "child1_1")
        child1_1_1 = ConditionNode(child1_1, "child1_1")
        child1_2 = ConditionNode(child1, "child1_2")
        child2 = ConditionNode(cn, "child2")
        child3 = ConditionNode(cn, "child3")

        self.assertEqual(6, cn.size_sub_nodes())
        self.assertEqual(3, child1.size_sub_nodes())
        self.assertEqual(0, child2.size_sub_nodes())
        self.assertEqual(0, child3.size_sub_nodes())
        self.assertEqual(1, child1_1.size_sub_nodes())

    def test_3_node_children_sub_nodes_size_3(self):
        cn = ConditionNode(None, "parent")
        child1 = ConditionNode(cn, "child1")
        child1_1 = ConditionNode(child1, "child1_1")
        child1_1_1 = ConditionNode(child1_1, "child1_1")
        child1_2 = ConditionNode(child1, "child1_2")
        child2 = ConditionNode(cn, "child2")
        child3 = ConditionNode(cn, "child3")
        self.assertEqual(6, cn.size_sub_nodes())
        self.assertEqual(3, child1.size_sub_nodes())
        self.assertEqual(0, child2.size_sub_nodes())
        self.assertEqual(0, child3.size_sub_nodes())

    def test_4_node_children_height_1(self):
        cn = ConditionNode(None, "parent")
        child1 = ConditionNode(cn, "child1")
        child1_1 = ConditionNode(child1, "child1_1")
        child1_1_1 = ConditionNode(child1_1, "child1_1_1")
        child1_2 = ConditionNode(child1, "child1_2")
        child2 = ConditionNode(cn, "child2")
        child3 = ConditionNode(cn, "child3")

    def test_4_node_children_height_2(self):
        cn = ConditionNode(None, "parent")
        child1 = ConditionNode(cn, "child1")
        child1_1 = ConditionNode(child1, "child1_1")
        child1_1_1 = ConditionNode(child1_1, "child1_1")
        child1_1_1_1 = ConditionNode(child1_1_1, "child1_1")
        child1_2 = ConditionNode(child1, "child1_2")
        child2 = ConditionNode(cn, "child2")
        child3 = ConditionNode(cn, "child3")
        self.assertEqual(4, cn.get_height())

    def test_4_node_children_height_3(self):
        cn = ConditionNode(None, "parent")
        child1 = ConditionNode(cn, "child1")
        child1_1 = ConditionNode(child1, "child1_1")
        child1_1_1 = ConditionNode(child1_1, "child1_1")
        child1_1_1_1 = ConditionNode(child1_1_1, "child1_1_1")
        child1_2 = ConditionNode(child1, "child1_2")
        child2 = ConditionNode(cn, "child2")
        child2_1 = ConditionNode(child2, "child2")
        child3 = ConditionNode(cn, "child3")
        self.assertEqual(4, cn.get_height())

    def test_5_node_children_inverse_height_1(self):
        cn = ConditionNode(None, "parent")
        child1 = ConditionNode(cn, "child1")
        child1_1 = ConditionNode(child1, "child1_1")
        child1_1_1 = ConditionNode(child1_1, "child1_1_1")
        child1_2 = ConditionNode(child1, "child1_2")
        child2 = ConditionNode(cn, "child2")
        child3 = ConditionNode(cn, "child3")
        self.assertEqual(3, cn.get_height())
        self.assertEqual(0, cn.get_inverse_height())
        self.assertEqual(1, child3.get_inverse_height())
        self.assertEqual(1, child2.get_inverse_height())
        self.assertEqual(1, child3.get_inverse_height())
        self.assertEqual(3, child1_1_1.get_inverse_height())

    def test_5_node_children_inverse_height_2(self):
        cn = ConditionNode(None, "parent")
        child1 = ConditionNode(cn, "child1")
        child1_1 = ConditionNode(child1, "child1_1")
        child1_1_1 = ConditionNode(child1_1, "child1_1_1")
        child1_1_1_1 = ConditionNode(child1_1_1, "child1_1_1_1")
        child1_2 = ConditionNode(child1, "child1_2")
        child2 = ConditionNode(cn, "child2")
        ConditionNode(child2, "child2_1")
        child3 = ConditionNode(cn, "child3")
        self.assertEqual(0, cn.get_inverse_height())
        self.assertEqual(1, child3.get_inverse_height())
        self.assertEqual(1, child2.get_inverse_height())
        self.assertEqual(2, child1_2.get_inverse_height())
        self.assertEqual(1, child3.get_inverse_height())
        self.assertEqual(3, child1_1_1.get_inverse_height())
        self.assertEqual(4, child1_1_1_1.get_inverse_height())

    def test_6_node_tree_1(self):
        cn = ConditionNode(None, "parent", None, 1)
        child1 = ConditionNode(cn, "child1", None, 2)
        child2 = ConditionNode(cn, "child2", None, 3)
        child3 = ConditionNode(cn, "child3", None, 4)

        child1_1 = ConditionNode(child1, "child1_1", None, 5)
        child1_2 = ConditionNode(child1, "child1_2", None, 6)
        ConditionNode(child2, "child2_1", None, 7)
        child1_1_1 = ConditionNode(child1_1, "child1_1_1", None, 8)
        child1_1_1_1 = ConditionNode(child1_1_1, "child1_1_1_1", None, 9)
        expected_result = """->(ID="1", parentId="-", value:"parent")
-->(ID="2", parentId="1", value:"child1")
--->(ID="5", parentId="2", value:"child1_1")
---->(ID="8", parentId="5", value:"child1_1_1")
----->(ID="9", parentId="8", value:"child1_1_1_1")
--->(ID="6", parentId="2", value:"child1_2")
-->(ID="3", parentId="1", value:"child2")
--->(ID="7", parentId="3", value:"child2_1")
-->(ID="4", parentId="1", value:"child3")
"""
        self.assertEqual(expected_result, cn.tree_to_string())

    def test_6_node_tree_2(self):
        cn = ConditionNode(None, "parent", None, 1)
        child1 = ConditionNode(cn, "child1", None, 2)
        child2 = ConditionNode(cn, "child2", None, 3)
        child3 = ConditionNode(cn, "child3", None, 4)
        child3_1 = ConditionNode(child3, "child3_1", None, 10)
        child3_1_1 = ConditionNode(child3_1, "child3_1_1", None, 10)

        child1_1 = ConditionNode(child1, "child1_1", None, 5)
        child1_2 = ConditionNode(child1, "child1_2", None, 6)
        ConditionNode(child2, "child2_1", None, 7)
        child1_1_1 = ConditionNode(child1_1, "child1_1_1", None, 8)
        child1_1_1_1 = ConditionNode(child1_1_1, "child1_1_1_1", None, 9)
        expected_result = """->(ID="1", parentId="-", value:"parent")
-->(ID="2", parentId="1", value:"child1")
--->(ID="5", parentId="2", value:"child1_1")
---->(ID="8", parentId="5", value:"child1_1_1")
----->(ID="9", parentId="8", value:"child1_1_1_1")
--->(ID="6", parentId="2", value:"child1_2")
-->(ID="3", parentId="1", value:"child2")
--->(ID="7", parentId="3", value:"child2_1")
-->(ID="4", parentId="1", value:"child3")
--->(ID="10", parentId="4", value:"child3_1")
---->(ID="10", parentId="10", value:"child3_1_1")
"""
        self.assertEqual(expected_result, cn.tree_to_string())

    def test_7_node_children_clone_branch_1(self):
        # ORDER matters now of token indexes
        cn = ConditionNode(None, "parent", None, 1)

        child1 = ConditionNode(cn, "child1", None, 2)
        child1_1 = ConditionNode(child1, "child1_1", None, 3)
        child1_1_1 = ConditionNode(child1_1, "child1_1_1", None, 4)
        ConditionNode(child1_1_1, "child1_1_1_1", None, 5)
        ConditionNode(child1, "child1_2", None, 6)
        child2 = ConditionNode(cn, "child2", None, 7)
        ConditionNode(child2, "child2_1", None, 8)
        ConditionNode(cn, "child3", None, 9)

        cloned_branch = cn.clone_branch(False)  # should have same indexes as root
        expected_result = """->(ID="1", parentId="-", value:"parent")
-->(ID="2", parentId="1", value:"child1")
--->(ID="3", parentId="2", value:"child1_1")
---->(ID="4", parentId="3", value:"child1_1_1")
----->(ID="5", parentId="4", value:"child1_1_1_1")
--->(ID="6", parentId="2", value:"child1_2")
-->(ID="7", parentId="1", value:"child2")
--->(ID="8", parentId="7", value:"child2_1")
-->(ID="9", parentId="1", value:"child3")"""
        actual_result = cloned_branch.tree_to_string().strip()
        self.assertEqual(expected_result, actual_result, "Should be the same output. Clone branch with reindex=False"
                                                         " should produce same graph but new references")

    def test_7_node_children_clone_branch_2(self):
        cn = ConditionNode(None, "parent", None, 1)
        child1 = ConditionNode(cn, "child1", None, 2)
        child1_1 = ConditionNode(child1, "child1_1", None, 3)
        child1_1_1 = ConditionNode(child1_1, "child1_1_1", None, 4)
        ConditionNode(child1_1_1, "child1_1_1_1", None, 5)
        ConditionNode(child1, "child1_2", None, 6)
        child2 = ConditionNode(cn, "child2", None, 7)
        ConditionNode(child2, "child2_1", None, 8)
        ConditionNode(cn, "child3", None, 9)

        expected_result = """->(ID="1", parentId="-", value:"parent")
-->(ID="2", parentId="1", value:"child1")
--->(ID="3", parentId="2", value:"child1_1")
---->(ID="4", parentId="3", value:"child1_1_1")
----->(ID="5", parentId="4", value:"child1_1_1_1")
--->(ID="6", parentId="2", value:"child1_2")
-->(ID="7", parentId="1", value:"child2")
--->(ID="8", parentId="7", value:"child2_1")
-->(ID="9", parentId="1", value:"child3")"""
        cloned_branch_2 = cn.clone_branch(True, 1)  # should have same indexes as root
        actual_result = cloned_branch_2.tree_to_string().strip()
        self.assertEqual(expected_result, actual_result)

    def test_7_node_children_clone_branch_3(self):
        cn = ConditionNode(None, "parent", None, 1)
        child1 = ConditionNode(cn, "child1", None, 2)
        child1_1 = ConditionNode(child1, "child1_1", None, 3)
        child1_1_1 = ConditionNode(child1_1, "child1_1_1", None, 4)
        ConditionNode(child1_1_1, "child1_1_1_1", None, 5)
        ConditionNode(child1, "child1_2", None, 6)
        child2 = ConditionNode(cn, "child2", None, 7)
        ConditionNode(child2, "child2_1", None, 8)
        ConditionNode(cn, "child3", None, 9)

        expected_result = """->(ID="2", parentId="-", value:"child1")
-->(ID="3", parentId="2", value:"child1_1")
--->(ID="4", parentId="3", value:"child1_1_1")
---->(ID="5", parentId="4", value:"child1_1_1_1")
-->(ID="6", parentId="2", value:"child1_2")"""
        first_child_cloned = child1.clone_branch(False)  # child1_1 must have the same indexes as of parents
        actual_result = first_child_cloned.tree_to_string().strip()
        self.assertEqual(expected_result, actual_result)

    def test_7_node_children_clone_branch_4(self):
        cn = ConditionNode(None, "parent", None, 1)
        child1 = ConditionNode(cn, "child1", None, 2)
        child1_1 = ConditionNode(child1, "child1_1", None, 3)
        child1_1_1 = ConditionNode(child1_1, "child1_1_1", None, 4)
        ConditionNode(child1_1_1, "child1_1_1_1", None, 5)
        ConditionNode(child1, "child1_2", None, 6)
        child2 = ConditionNode(cn, "child2", None, 7)
        ConditionNode(child2, "child2_1", None, 8)
        ConditionNode(cn, "child3", None, 9)

        expected_result = """->(ID="1", parentId="-", value:"child1")
-->(ID="2", parentId="1", value:"child1_1")
--->(ID="3", parentId="2", value:"child1_1_1")
---->(ID="4", parentId="3", value:"child1_1_1_1")
-->(ID="5", parentId="1", value:"child1_2")"""
        first_child_cloned = child1.clone_branch(True, 1)  # child1_1 must not have same token index as child1_1
        actual_result = first_child_cloned.tree_to_string().strip()
        self.assertEqual(expected_result, actual_result)


if __name__ == '__main__':
    unittest.main()

