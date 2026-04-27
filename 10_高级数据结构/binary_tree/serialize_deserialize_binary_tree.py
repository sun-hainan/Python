# -*- coding: utf-8 -*-

"""

算法实现：binary_tree / serialize_deserialize_binary_tree



本文件实现 serialize_deserialize_binary_tree 相关的算法功能。

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

# 算法模块：deserialize

# =============================================================================

class TreeNode:

    # TreeNode class



    # TreeNode class

    """

    A binary tree node has a value, left child, and right child.



    Props:

        value: The value of the node.

        left: The left child of the node.

        right: The right child of the node.

    """





    value: int = 0

    left: TreeNode | None = None

    right: TreeNode | None = None



    def __post_init__(self):

    # __post_init__ function



    # __post_init__ function

        if not isinstance(self.value, int):

            raise TypeError("Value must be an integer.")



    def __iter__(self) -> Iterator[TreeNode]:

    # __iter__ function



    # __iter__ function

        """

        Iterate through the tree in preorder.



        Returns:

            An iterator of the tree nodes.



        >>> list(TreeNode(1))

        [1,null,null]

        >>> tuple(TreeNode(1, TreeNode(2), TreeNode(3)))

        (1,2,null,null,3,null,null, 2,null,null, 3,null,null)

        """

        yield self

        yield from self.left or ()

        yield from self.right or ()



    def __len__(self) -> int:

    # __len__ function



    # __len__ function

        """

        Count the number of nodes in the tree.



        Returns:

            The number of nodes in the tree.



        >>> len(TreeNode(1))

        1

        >>> len(TreeNode(1, TreeNode(2), TreeNode(3)))

        3

        """

        return sum(1 for _ in self)



    def __repr__(self) -> str:

    # __repr__ function



    # __repr__ function

        """

        Represent the tree as a string.



        Returns:

            A string representation of the tree.



        >>> repr(TreeNode(1))

        '1,null,null'

        >>> repr(TreeNode(1, TreeNode(2), TreeNode(3)))

        '1,2,null,null,3,null,null'

        >>> repr(TreeNode(1, TreeNode(2), TreeNode(3, TreeNode(4), TreeNode(5))))

        '1,2,null,null,3,4,null,null,5,null,null'

        """

        return f"{self.value},{self.left!r},{self.right!r}".replace("None", "null")



    @classmethod

    def five_tree(cls) -> TreeNode:

    # five_tree function



    # five_tree function

        """

        >>> repr(TreeNode.five_tree())

        '1,2,null,null,3,4,null,null,5,null,null'

        """

        root = TreeNode(1)

        root.left = TreeNode(2)

        root.right = TreeNode(3)

        root.right.left = TreeNode(4)

        root.right.right = TreeNode(5)

        return root





def deserialize(data: str) -> TreeNode | None:

    # deserialize function



    # deserialize function

    """

    Deserialize a string to a binary tree.



    Args:

        data(str): The serialized string.



    Returns:

        The root of the binary tree.



    >>> root = TreeNode.five_tree()

    >>> serialzed_data = repr(root)

    >>> deserialized = deserialize(serialzed_data)

    >>> root == deserialized

    True

    >>> root is deserialized  # two separate trees

    False

    >>> root.right.right.value = 6

    >>> root == deserialized

    False

    >>> serialzed_data = repr(root)

    >>> deserialized = deserialize(serialzed_data)

    >>> root == deserialized

    True

    >>> deserialize("")

    Traceback (most recent call last):

        ...

    ValueError: Data cannot be empty.

    """



    if not data:

        raise ValueError("Data cannot be empty.")



    # Split the serialized string by a comma to get node values

    nodes = data.split(",")



    def build_tree() -> TreeNode | None:

    # build_tree function



    # build_tree function

        # Get the next value from the list

        value = nodes.pop(0)



        if value == "null":

            return None



        node = TreeNode(int(value))

        node.left = build_tree()  # Recursively build left subtree

        node.right = build_tree()  # Recursively build right subtree

        return node



    return build_tree()





if __name__ == "__main__":

    import doctest



    doctest.testmod()

