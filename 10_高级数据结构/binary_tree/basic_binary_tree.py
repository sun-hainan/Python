# -*- coding: utf-8 -*-

"""

算法实现：binary_tree / basic_binary_tree



本文件实现 basic_binary_tree 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""









from collections.abc import Iterator

from dataclasses import dataclass





@dataclass



# =============================================================================

# 算法模块：unknown

# =============================================================================

class Node:

    # Node class



    # Node class

    data: int

    left: Node | None = None

    right: Node | None = None



    def __iter__(self) -> Iterator[int]:

    # __iter__ function



    # __iter__ function

        if self.left:

            yield from self.left

        yield self.data

        if self.right:

            yield from self.right



    def __len__(self) -> int:

    # __len__ function



    # __len__ function

        return sum(1 for _ in self)



    def is_full(self) -> bool:

    # is_full function



    # is_full function

        if not self or (not self.left and not self.right):

            return True

        if self.left and self.right:

            return self.left.is_full() and self.right.is_full()

        return False





@dataclass

class BinaryTree:

    # BinaryTree class



    # BinaryTree class

    root: Node



    def __iter__(self) -> Iterator[int]:

    # __iter__ function



    # __iter__ function

        return iter(self.root)



    def __len__(self) -> int:

    # __len__ function



    # __len__ function

        return len(self.root)



    @classmethod

    def small_tree(cls) -> BinaryTree:

    # small_tree function



    # small_tree function

        """

        Return a small binary tree with 3 nodes.

        >>> binary_tree = BinaryTree.small_tree()

        >>> len(binary_tree)

        3

        >>> list(binary_tree)

        [1, 2, 3]

        """



        binary_tree = BinaryTree(Node(2))

        binary_tree.root.left = Node(1)

        binary_tree.root.right = Node(3)

        return binary_tree



    @classmethod

    def medium_tree(cls) -> BinaryTree:

    # medium_tree function



    # medium_tree function

        """

        Return a medium binary tree with 3 nodes.

        >>> binary_tree = BinaryTree.medium_tree()

        >>> len(binary_tree)

        7

        >>> list(binary_tree)

        [1, 2, 3, 4, 5, 6, 7]

        """

        binary_tree = BinaryTree(Node(4))

        binary_tree.root.left = two = Node(2)

        two.left = Node(1)

        two.right = Node(3)

        binary_tree.root.right = five = Node(5)

        five.right = six = Node(6)

        six.right = Node(7)

        return binary_tree



    def depth(self) -> int:

    # depth function



    # depth function

        """

        Returns the depth of the tree



        >>> BinaryTree(Node(1)).depth()

        1

        >>> BinaryTree.small_tree().depth()

        2

        >>> BinaryTree.medium_tree().depth()

        4

        """

        return self._depth(self.root)



    def _depth(self, node: Node | None) -> int:

    # _depth function



    # _depth function

        if not node:

            return 0

        return 1 + max(self._depth(node.left), self._depth(node.right))



    def is_full(self) -> bool:

    # is_full function



    # is_full function

        """

        Returns True if the tree is full



        >>> BinaryTree(Node(1)).is_full()

        True

        >>> BinaryTree.small_tree().is_full()

        True

        >>> BinaryTree.medium_tree().is_full()

        False

        """

        return self.root.is_full()





if __name__ == "__main__":

    import doctest



    doctest.testmod()

