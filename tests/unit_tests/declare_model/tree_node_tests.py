import unittest

from src.declare4py.log_utils.parsers.declare.ConstraintConditionResolver import ConditionNode


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




if __name__ == '__main__':
    unittest.main()

