# -*- coding: utf-8 -*-

"""

算法实现：binary_tree / symmetric_tree



本文件实现 symmetric_tree 相关的算法功能。

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









from dataclasses import dataclass





@dataclass



# =============================================================================

# 算法模块：make_symmetric_tree

# =============================================================================

class Node:

    # Node class



    # Node class

    """

    A Node represents an element of a binary tree, which contains:



    Attributes:

    data: The value stored in the node (int).

    left: Pointer to the left child node (Node or None).

    right: Pointer to the right child node (Node or None).



    Example:

    >>> node = Node(1, Node(2), Node(3))

    >>> node.data

    1

    >>> node.left.data

    2

    >>> node.right.data

    3

    """



    data: int

    left: Node | None = None

    right: Node | None = None





def make_symmetric_tree() -> Node:

    # make_symmetric_tree function



    # make_symmetric_tree function

    r"""

    Create a symmetric tree for testing.



    The tree looks like this:

           1

         /   \

        2     2

      / \    / \

     3   4   4  3



    Returns:

    Node: Root node of a symmetric tree.



    Example:

    >>> tree = make_symmetric_tree()

    >>> tree.data

    1

    >>> tree.left.data == tree.right.data

    True

    >>> tree.left.left.data == tree.right.right.data

    True

    """

    root = Node(1)

    root.left = Node(2)

    root.right = Node(2)

    root.left.left = Node(3)

    root.left.right = Node(4)

    root.right.left = Node(4)

    root.right.right = Node(3)

    return root





def make_asymmetric_tree() -> Node:

    r"""

    Create an asymmetric tree for testing.



    The tree looks like this:

           1

         /   \

        2     2

      / \    / \

     3   4   3  4



    Returns:

    Node: Root node of an asymmetric tree.



    Example:

    >>> tree = make_asymmetric_tree()

    >>> tree.data

    1

    >>> tree.left.data == tree.right.data

    True

    >>> tree.left.left.data == tree.right.right.data

    False

    """

    root = Node(1)

    root.left = Node(2)

    root.right = Node(2)

    root.left.left = Node(3)

    root.left.right = Node(4)

    root.right.left = Node(3)

    root.right.right = Node(4)

    return root





def is_symmetric_tree(tree: Node) -> bool:

    """

    Check if a binary tree is symmetric (i.e., a mirror of itself).



    Parameters:

    tree: The root node of the binary tree.



    Returns:

    bool: True if the tree is symmetric, False otherwise.



    Example:

    >>> is_symmetric_tree(make_symmetric_tree())

    True

    >>> is_symmetric_tree(make_asymmetric_tree())

    False

    """

    if tree:

        return is_mirror(tree.left, tree.right)

    return True  # An empty tree is considered symmetric.





def is_mirror(left: Node | None, right: Node | None) -> bool:

    """

    Check if two subtrees are mirror images of each other.



    Parameters:

    left: The root node of the left subtree.

    right: The root node of the right subtree.



    Returns:

    bool: True if the two subtrees are mirrors of each other, False otherwise.



    Example:

    >>> tree1 = make_symmetric_tree()

    >>> is_mirror(tree1.left, tree1.right)

    True

    >>> tree2 = make_asymmetric_tree()

    >>> is_mirror(tree2.left, tree2.right)

    False

    """

    if left is None and right is None:

        # Both sides are empty, which is symmetric.

        return True

    if left is None or right is None:

        # One side is empty while the other is not, which is not symmetric.

        return False

    if left.data == right.data:

        # The values match, so check the subtrees recursively.

        return is_mirror(left.left, right.right) and is_mirror(left.right, right.left)

    return False





if __name__ == "__main__":

    from doctest import testmod



    testmod()

