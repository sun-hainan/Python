# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / binary_search_tree_recursive



本文件实现 binary_search_tree_recursive 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""





"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""









import unittest

from collections.abc import Iterator



import pytest







# =============================================================================

# 算法模块：binary_search_tree_example

# =============================================================================

class Node:

    # Node class



    # Node class

    def __init__(self, label: int, parent: Node | None) -> None:

    # __init__ function



    # __init__ function

        self.label = label

        self.parent = parent

        self.left: Node | None = None

        self.right: Node | None = None





class BinarySearchTree:

    # BinarySearchTree class



    # BinarySearchTree class

    def __init__(self) -> None:

    # __init__ function



    # __init__ function

        self.root: Node | None = None



    def empty(self) -> None:

    # empty function



    # empty function

        """

        Empties the tree



        >>> t = BinarySearchTree()

        >>> assert t.root is None

        >>> t.put(8)

        >>> assert t.root is not None

        """

        self.root = None



    def is_empty(self) -> bool:

    # is_empty function



    # is_empty function

        """

        Checks if the tree is empty



        >>> t = BinarySearchTree()

        >>> t.is_empty()

        True

        >>> t.put(8)

        >>> t.is_empty()

        False

        """

        return self.root is None



    def put(self, label: int) -> None:

    # put function



    # put function

        """

        Put a new node in the tree



        >>> t = BinarySearchTree()

        >>> t.put(8)

        >>> assert t.root.parent is None

        >>> assert t.root.label == 8



        >>> t.put(10)

        >>> assert t.root.right.parent == t.root

        >>> assert t.root.right.label == 10



        >>> t.put(3)

        >>> assert t.root.left.parent == t.root

        >>> assert t.root.left.label == 3

        """

        self.root = self._put(self.root, label)



    def _put(self, node: Node | None, label: int, parent: Node | None = None) -> Node:

    # _put function



    # _put function

        if node is None:

            node = Node(label, parent)

        elif label < node.label:

            node.left = self._put(node.left, label, node)

        elif label > node.label:

            node.right = self._put(node.right, label, node)

        else:

            msg = f"Node with label {label} already exists"

            raise ValueError(msg)



        return node



    def search(self, label: int) -> Node:

    # search function



    # search function

        """

        Searches a node in the tree



        >>> t = BinarySearchTree()

        >>> t.put(8)

        >>> t.put(10)

        >>> node = t.search(8)

        >>> assert node.label == 8



        >>> node = t.search(3)

        Traceback (most recent call last):

            ...

        ValueError: Node with label 3 does not exist

        """

        return self._search(self.root, label)



    def _search(self, node: Node | None, label: int) -> Node:

    # _search function



    # _search function

        if node is None:

            msg = f"Node with label {label} does not exist"

            raise ValueError(msg)

        elif label < node.label:

            node = self._search(node.left, label)

        elif label > node.label:

            node = self._search(node.right, label)



        return node



    def remove(self, label: int) -> None:

    # remove function



    # remove function

        """

        Removes a node in the tree



        >>> t = BinarySearchTree()

        >>> t.put(8)

        >>> t.put(10)

        >>> t.remove(8)

        >>> assert t.root.label == 10



        >>> t.remove(3)

        Traceback (most recent call last):

            ...

        ValueError: Node with label 3 does not exist

        """

        node = self.search(label)

        if node.right and node.left:

            lowest_node = self._get_lowest_node(node.right)

            lowest_node.left = node.left

            lowest_node.right = node.right

            node.left.parent = lowest_node

            if node.right:

                node.right.parent = lowest_node

            self._reassign_nodes(node, lowest_node)

        elif not node.right and node.left:

            self._reassign_nodes(node, node.left)

        elif node.right and not node.left:

            self._reassign_nodes(node, node.right)

        else:

            self._reassign_nodes(node, None)



    def _reassign_nodes(self, node: Node, new_children: Node | None) -> None:

    # _reassign_nodes function



    # _reassign_nodes function

        if new_children:

            new_children.parent = node.parent



        if node.parent:

            if node.parent.right == node:

                node.parent.right = new_children

            else:

                node.parent.left = new_children

        else:

            self.root = new_children



    def _get_lowest_node(self, node: Node) -> Node:

    # _get_lowest_node function



    # _get_lowest_node function

        if node.left:

            lowest_node = self._get_lowest_node(node.left)

        else:

            lowest_node = node

            self._reassign_nodes(node, node.right)



        return lowest_node



    def exists(self, label: int) -> bool:

    # exists function



    # exists function

        """

        Checks if a node exists in the tree



        >>> t = BinarySearchTree()

        >>> t.put(8)

        >>> t.put(10)

        >>> t.exists(8)

        True



        >>> t.exists(3)

        False

        """

        try:

            self.search(label)

            return True

        except ValueError:

            return False



    def get_max_label(self) -> int:

    # get_max_label function



    # get_max_label function

        """

        Gets the max label inserted in the tree



        >>> t = BinarySearchTree()

        >>> t.get_max_label()

        Traceback (most recent call last):

            ...

        ValueError: Binary search tree is empty



        >>> t.put(8)

        >>> t.put(10)

        >>> t.get_max_label()

        10

        """

        if self.root is None:

            raise ValueError("Binary search tree is empty")



        node = self.root

        while node.right is not None:

            node = node.right



        return node.label



    def get_min_label(self) -> int:

    # get_min_label function



    # get_min_label function

        """

        Gets the min label inserted in the tree



        >>> t = BinarySearchTree()

        >>> t.get_min_label()

        Traceback (most recent call last):

            ...

        ValueError: Binary search tree is empty



        >>> t.put(8)

        >>> t.put(10)

        >>> t.get_min_label()

        8

        """

        if self.root is None:

            raise ValueError("Binary search tree is empty")



        node = self.root

        while node.left is not None:

            node = node.left



        return node.label



    def inorder_traversal(self) -> Iterator[Node]:

    # inorder_traversal function



    # inorder_traversal function

        """

        Return the inorder traversal of the tree



        >>> t = BinarySearchTree()

        >>> [i.label for i in t.inorder_traversal()]

        []



        >>> t.put(8)

        >>> t.put(10)

        >>> t.put(9)

        >>> [i.label for i in t.inorder_traversal()]

        [8, 9, 10]

        """

        return self._inorder_traversal(self.root)



    def _inorder_traversal(self, node: Node | None) -> Iterator[Node]:

    # _inorder_traversal function



    # _inorder_traversal function

        if node is not None:

            yield from self._inorder_traversal(node.left)

            yield node

            yield from self._inorder_traversal(node.right)



    def preorder_traversal(self) -> Iterator[Node]:

    # preorder_traversal function



    # preorder_traversal function

        """

        Return the preorder traversal of the tree



        >>> t = BinarySearchTree()

        >>> [i.label for i in t.preorder_traversal()]

        []



        >>> t.put(8)

        >>> t.put(10)

        >>> t.put(9)

        >>> [i.label for i in t.preorder_traversal()]

        [8, 10, 9]

        """

        return self._preorder_traversal(self.root)



    def _preorder_traversal(self, node: Node | None) -> Iterator[Node]:

    # _preorder_traversal function



    # _preorder_traversal function

        if node is not None:

            yield node

            yield from self._preorder_traversal(node.left)

            yield from self._preorder_traversal(node.right)





class BinarySearchTreeTest(unittest.TestCase):

    # BinarySearchTreeTest class



    # BinarySearchTreeTest class

    @staticmethod

    def _get_binary_search_tree() -> BinarySearchTree:

    # _get_binary_search_tree function



    # _get_binary_search_tree function

        r"""

              8

             / \

            3   10

           / \    \

          1   6    14

             / \   /

            4   7 13

             \

              5

        """

        t = BinarySearchTree()

        t.put(8)

        t.put(3)

        t.put(6)

        t.put(1)

        t.put(10)

        t.put(14)

        t.put(13)

        t.put(4)

        t.put(7)

        t.put(5)



        return t



    def test_put(self) -> None:

        t = BinarySearchTree()

        assert t.is_empty()



        t.put(8)

        r"""

              8

        """

        assert t.root is not None

        assert t.root.parent is None

        assert t.root.label == 8



        t.put(10)

        r"""

              8

               \

                10

        """

        assert t.root.right is not None

        assert t.root.right.parent == t.root

        assert t.root.right.label == 10



        t.put(3)

        r"""

              8

             / \

            3   10

        """

        assert t.root.left is not None

        assert t.root.left.parent == t.root

        assert t.root.left.label == 3



        t.put(6)

        r"""

              8

             / \

            3   10

             \

              6

        """

        assert t.root.left.right is not None

        assert t.root.left.right.parent == t.root.left

        assert t.root.left.right.label == 6



        t.put(1)

        r"""

              8

             / \

            3   10

           / \

          1   6

        """

        assert t.root.left.left is not None

        assert t.root.left.left.parent == t.root.left

        assert t.root.left.left.label == 1



        with pytest.raises(ValueError):

            t.put(1)



    def test_search(self) -> None:

        t = self._get_binary_search_tree()



        node = t.search(6)

        assert node.label == 6



        node = t.search(13)

        assert node.label == 13



        with pytest.raises(ValueError):

            t.search(2)



    def test_remove(self) -> None:

        t = self._get_binary_search_tree()



        t.remove(13)

        r"""

              8

             / \

            3   10

           / \    \

          1   6    14

             / \

            4   7

             \

              5

        """

        assert t.root is not None

        assert t.root.right is not None

        assert t.root.right.right is not None

        assert t.root.right.right.right is None

        assert t.root.right.right.left is None



        t.remove(7)

        r"""

              8

             / \

            3   10

           / \    \

          1   6    14

             /

            4

             \

              5

        """

        assert t.root.left is not None

        assert t.root.left.right is not None

        assert t.root.left.right.left is not None

        assert t.root.left.right.right is None

        assert t.root.left.right.left.label == 4



        t.remove(6)

        r"""

              8

             / \

            3   10

           / \    \

          1   4    14

               \

                5

        """

        assert t.root.left.left is not None

        assert t.root.left.right.right is not None

        assert t.root.left.left.label == 1

        assert t.root.left.right.label == 4

        assert t.root.left.right.right.label == 5

        assert t.root.left.right.left is None

        assert t.root.left.left.parent == t.root.left

        assert t.root.left.right.parent == t.root.left



        t.remove(3)

        r"""

              8

             / \

            4   10

           / \    \

          1   5    14

        """

        assert t.root is not None

        assert t.root.left.label == 4

        assert t.root.left.right.label == 5

        assert t.root.left.left.label == 1

        assert t.root.left.parent == t.root

        assert t.root.left.left.parent == t.root.left

        assert t.root.left.right.parent == t.root.left



        t.remove(4)

        r"""

              8

             / \

            5   10

           /      \

          1        14

        """

        assert t.root.left is not None

        assert t.root.left.left is not None

        assert t.root.left.label == 5

        assert t.root.left.right is None

        assert t.root.left.left.label == 1

        assert t.root.left.parent == t.root

        assert t.root.left.left.parent == t.root.left



    def test_remove_2(self) -> None:

        t = self._get_binary_search_tree()



        t.remove(3)

        r"""

              8

             / \

            4   10

           / \    \

          1   6    14

             / \   /

            5   7 13

        """

        assert t.root is not None

        assert t.root.left is not None

        assert t.root.left.left is not None

        assert t.root.left.right is not None

        assert t.root.left.right.left is not None

        assert t.root.left.right.right is not None

        assert t.root.left.label == 4

        assert t.root.left.right.label == 6

        assert t.root.left.left.label == 1

        assert t.root.left.right.right.label == 7

        assert t.root.left.right.left.label == 5

        assert t.root.left.parent == t.root

        assert t.root.left.right.parent == t.root.left

        assert t.root.left.left.parent == t.root.left

        assert t.root.left.right.left.parent == t.root.left.right



    def test_empty(self) -> None:

        t = self._get_binary_search_tree()

        t.empty()

        assert t.root is None



    def test_is_empty(self) -> None:

        t = self._get_binary_search_tree()

        assert not t.is_empty()



        t.empty()

        assert t.is_empty()



    def test_exists(self) -> None:

        t = self._get_binary_search_tree()



        assert t.exists(6)

        assert not t.exists(-1)



    def test_get_max_label(self) -> None:

        t = self._get_binary_search_tree()



        assert t.get_max_label() == 14



        t.empty()

        with pytest.raises(ValueError):

            t.get_max_label()



    def test_get_min_label(self) -> None:

        t = self._get_binary_search_tree()



        assert t.get_min_label() == 1



        t.empty()

        with pytest.raises(ValueError):

            t.get_min_label()



    def test_inorder_traversal(self) -> None:

        t = self._get_binary_search_tree()



        inorder_traversal_nodes = [i.label for i in t.inorder_traversal()]

        assert inorder_traversal_nodes == [1, 3, 4, 5, 6, 7, 8, 10, 13, 14]



    def test_preorder_traversal(self) -> None:

        t = self._get_binary_search_tree()



        preorder_traversal_nodes = [i.label for i in t.preorder_traversal()]

        assert preorder_traversal_nodes == [8, 3, 1, 6, 4, 5, 7, 10, 14, 13]





def binary_search_tree_example() -> None:

    r"""

    Example

                  8

                 / \

                3   10

               / \    \

              1   6    14

                 / \   /

                4   7 13

                \

                5



    Example After Deletion

                  4

                 / \

                1   7

                     \

                      5



    """



    t = BinarySearchTree()

    t.put(8)

    t.put(3)

    t.put(6)

    t.put(1)

    t.put(10)

    t.put(14)

    t.put(13)

    t.put(4)

    t.put(7)

    t.put(5)



    print(

        """

            8

           / \\

          3   10

         / \\    \\

        1   6    14

           / \\   /

          4   7 13

           \\

            5

        """

    )



    print("Label 6 exists:", t.exists(6))

    print("Label 13 exists:", t.exists(13))

    print("Label -1 exists:", t.exists(-1))

    print("Label 12 exists:", t.exists(12))



    # Prints all the elements of the list in inorder traversal

    inorder_traversal_nodes = [i.label for i in t.inorder_traversal()]

    print("Inorder traversal:", inorder_traversal_nodes)



    # Prints all the elements of the list in preorder traversal

    preorder_traversal_nodes = [i.label for i in t.preorder_traversal()]

    print("Preorder traversal:", preorder_traversal_nodes)



    print("Max. label:", t.get_max_label())

    print("Min. label:", t.get_min_label())



    # Delete elements

    print("\nDeleting elements 13, 10, 8, 3, 6, 14")

    print(

        """

          4

         / \\

        1   7

             \\

              5

        """

    )

    t.remove(13)

    t.remove(10)

    t.remove(8)

    t.remove(3)

    t.remove(6)

    t.remove(14)



    # Prints all the elements of the list in inorder traversal after delete

    inorder_traversal_nodes = [i.label for i in t.inorder_traversal()]

    print("Inorder traversal after delete:", inorder_traversal_nodes)



    # Prints all the elements of the list in preorder traversal after delete

    preorder_traversal_nodes = [i.label for i in t.preorder_traversal()]

    print("Preorder traversal after delete:", preorder_traversal_nodes)



    print("Max. label:", t.get_max_label())

    print("Min. label:", t.get_min_label())





if __name__ == "__main__":

    binary_search_tree_example()

