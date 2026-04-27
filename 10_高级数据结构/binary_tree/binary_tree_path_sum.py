# -*- coding: utf-8 -*-
"""
算法实现：binary_tree / binary_tree_path_sum

本文件实现 binary_tree_path_sum 相关的算法功能。
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






# =============================================================================
# 算法模块：unknown
# =============================================================================
class Node:
    # Node class

    # Node class
    """
    A Node has value variable and pointers to Nodes to its left and right.
    """

    def __init__(self, value: int) -> None:
    # __init__ function

    # __init__ function
        self.value = value
        self.left: Node | None = None
        self.right: Node | None = None


class BinaryTreePathSum:
    # BinaryTreePathSum class

    # BinaryTreePathSum class
    r"""
    The below tree looks like this
          10
         /  \
        5   -3
       / \    \
      3   2    11
     / \   \
    3  -2   1


    >>> tree = Node(10)
    >>> tree.left = Node(5)
    >>> tree.right = Node(-3)
    >>> tree.left.left = Node(3)
    >>> tree.left.right = Node(2)
    >>> tree.right.right = Node(11)
    >>> tree.left.left.left = Node(3)
    >>> tree.left.left.right = Node(-2)
    >>> tree.left.right.right = Node(1)

    >>> BinaryTreePathSum().path_sum(tree, 8)
    3
    >>> BinaryTreePathSum().path_sum(tree, 7)
    2
    >>> tree.right.right = Node(10)
    >>> BinaryTreePathSum().path_sum(tree, 8)
    2
    >>> BinaryTreePathSum().path_sum(None, 0)
    0
    >>> BinaryTreePathSum().path_sum(tree, 0)
    0

    The second tree looks like this
          0
         / \
        5   5

    >>> tree2 = Node(0)
    >>> tree2.left = Node(5)
    >>> tree2.right = Node(5)

    >>> BinaryTreePathSum().path_sum(tree2, 5)
    4
    >>> BinaryTreePathSum().path_sum(tree2, -1)
    0
    >>> BinaryTreePathSum().path_sum(tree2, 0)
    1
    """

    target: int

    def __init__(self) -> None:
        self.paths = 0

    def depth_first_search(self, node: Node | None, path_sum: int) -> None:
        if node is None:
            return

        if path_sum == self.target:
            self.paths += 1

        if node.left:
            self.depth_first_search(node.left, path_sum + node.left.value)
        if node.right:
            self.depth_first_search(node.right, path_sum + node.right.value)

    def path_sum(self, node: Node | None, target: int | None = None) -> int:
        if node is None:
            return 0
        if target is not None:
            self.target = target

        self.depth_first_search(node, node.value)
        self.path_sum(node.left)
        self.path_sum(node.right)

        return self.paths


if __name__ == "__main__":
    import doctest

    doctest.testmod()
