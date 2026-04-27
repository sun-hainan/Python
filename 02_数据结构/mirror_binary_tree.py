# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / mirror_binary_tree



本文件实现 mirror_binary_tree 相关的算法功能。

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









from collections.abc import Iterator

from dataclasses import dataclass





@dataclass



# =============================================================================

# 算法模块：make_tree_seven

# =============================================================================

class Node:

    # Node class



    # Node class

    """

    A Node has value variable and pointers to Nodes to its left and right.

    """



    value: int

    left: Node | None = None

    right: Node | None = None



    def __iter__(self) -> Iterator[int]:

    # __iter__ function



    # __iter__ function

        if self.left:

            yield from self.left

        yield self.value

        if self.right:

            yield from self.right



    def __len__(self) -> int:

    # __len__ function



    # __len__ function

        return sum(1 for _ in self)



    def mirror(self) -> Node:

    # mirror function



    # mirror function

        """

        Mirror the binary tree rooted at this node by swapping left and right children.



        >>> tree = Node(0)

        >>> list(tree)

        [0]

        >>> list(tree.mirror())

        [0]

        >>> tree = Node(1, Node(0), Node(3, Node(2), Node(4, None, Node(5))))

        >>> tuple(tree)

        (0, 1, 2, 3, 4, 5)

        >>> tuple(tree.mirror())

        (5, 4, 3, 2, 1, 0)

        """

        self.left, self.right = self.right, self.left

        if self.left:

            self.left.mirror()

        if self.right:

            self.right.mirror()

        return self





def make_tree_seven() -> Node:

    # make_tree_seven function



    # make_tree_seven function

    r"""

    Return a binary tree with 7 nodes that looks like this:

    ::



           1

         /   \

        2     3

       / \   / \

      4   5 6   7



    >>> tree_seven = make_tree_seven()

    >>> len(tree_seven)

    7

    >>> list(tree_seven)

    [4, 2, 5, 1, 6, 3, 7]

    """

    tree = Node(1)

    tree.left = Node(2)

    tree.right = Node(3)

    tree.left.left = Node(4)

    tree.left.right = Node(5)

    tree.right.left = Node(6)

    tree.right.right = Node(7)

    return tree





def make_tree_nine() -> Node:

    r"""

    Return a binary tree with 9 nodes that looks like this:

    ::



            1

           / \

          2   3

         / \   \

        4   5   6

       / \   \

      7   8   9



    >>> tree_nine = make_tree_nine()

    >>> len(tree_nine)

    9

    >>> list(tree_nine)

    [7, 4, 8, 2, 5, 9, 1, 3, 6]

    """

    tree = Node(1)

    tree.left = Node(2)

    tree.right = Node(3)

    tree.left.left = Node(4)

    tree.left.right = Node(5)

    tree.right.right = Node(6)

    tree.left.left.left = Node(7)

    tree.left.left.right = Node(8)

    tree.left.right.right = Node(9)

    return tree





def main() -> None:

    r"""

    Mirror binary trees with the given root and returns the root



    >>> tree = make_tree_nine()

    >>> tuple(tree)

    (7, 4, 8, 2, 5, 9, 1, 3, 6)

    >>> tuple(tree.mirror())

    (6, 3, 1, 9, 5, 2, 8, 4, 7)



    nine_tree::



            1

           / \

          2   3

         / \   \

        4   5   6

       / \   \

      7   8   9



    The mirrored tree looks like this::



          1

         / \

        3   2

       /   / \

      6   5   4

         /   / \

        9   8   7

    """

    trees = {"zero": Node(0), "seven": make_tree_seven(), "nine": make_tree_nine()}

    for name, tree in trees.items():

        print(f"      The {name} tree: {tuple(tree)}")

        # (0,)

        # (4, 2, 5, 1, 6, 3, 7)

        # (7, 4, 8, 2, 5, 9, 1, 3, 6)

        print(f"Mirror of {name} tree: {tuple(tree.mirror())}")

        # (0,)

        # (7, 3, 6, 1, 5, 2, 4)

        # (6, 3, 1, 9, 5, 2, 8, 4, 7)





if __name__ == "__main__":

    import doctest



    doctest.testmod()

    main()

