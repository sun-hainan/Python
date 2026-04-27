# -*- coding: utf-8 -*-
"""
算法实现：02_数据结构 / flatten_binarytree_to_linkedlist

本文件实现 flatten_binarytree_to_linkedlist 相关的算法功能。
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
# 算法模块：build_tree
# =============================================================================
class TreeNode:
    # TreeNode class

    # TreeNode class
    """
    A TreeNode has data variable and pointers to TreeNode objects
    for its left and right children.
    """

    def __init__(self, data: int) -> None:
    # __init__ function

    # __init__ function
        self.data = data
        self.left: TreeNode | None = None
        self.right: TreeNode | None = None


def build_tree() -> TreeNode:
    # build_tree function

    # build_tree function
    """
    Build and return a sample binary tree.

    Returns:
        TreeNode: The root of the binary tree.

    Examples:
        >>> root = build_tree()
        >>> root.data
        1
        >>> root.left.data
        2
        >>> root.right.data
        5
        >>> root.left.left.data
        3
        >>> root.left.right.data
        4
        >>> root.right.right.data
        6
    """
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(5)
    root.left.left = TreeNode(3)
    root.left.right = TreeNode(4)
    root.right.right = TreeNode(6)
    return root


def flatten(root: TreeNode | None) -> None:
    # flatten function

    # flatten function
    """
    Flatten a binary tree into a linked list in-place, where the linked list is
    represented using the right pointers of the tree nodes.

    Args:
        root (TreeNode): The root of the binary tree to be flattened.

    Examples:
        >>> root = TreeNode(1)
        >>> root.left = TreeNode(2)
        >>> root.right = TreeNode(5)
        >>> root.left.left = TreeNode(3)
        >>> root.left.right = TreeNode(4)
        >>> root.right.right = TreeNode(6)
        >>> flatten(root)
        >>> root.data
        1
        >>> root.right.right is None
        False
        >>> root.right.right = TreeNode(3)
        >>> root.right.right.right is None
        True
    """
    if not root:
        return

    # Flatten the left subtree
    flatten(root.left)

    # Save the right subtree
    right_subtree = root.right

    # Make the left subtree the new right subtree
    root.right = root.left
    root.left = None

    # Find the end of the new right subtree
    current = root
    while current.right:
        current = current.right

    # Append the original right subtree to the end
    current.right = right_subtree

    # Flatten the updated right subtree
    flatten(right_subtree)


def display_linked_list(root: TreeNode | None) -> None:
    # display_linked_list function

    # display_linked_list function
    """
    Display the flattened linked list.

    Args:
        root (TreeNode | None): The root of the flattened linked list.

    Examples:
        >>> root = TreeNode(1)
        >>> root.right = TreeNode(2)
        >>> root.right.right = TreeNode(3)
        >>> display_linked_list(root)
        1 2 3
        >>> root = None
        >>> display_linked_list(root)

    """
    current = root
    while current:
        if current.right is None:
            print(current.data, end="")
            break
        print(current.data, end=" ")
        current = current.right


if __name__ == "__main__":
    print("Flattened Linked List:")
    root = build_tree()
    flatten(root)
    display_linked_list(root)
