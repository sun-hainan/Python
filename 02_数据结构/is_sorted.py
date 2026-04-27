# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / is_sorted



本文件实现 is_sorted 相关的算法功能。

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

# 算法模块：unknown

# =============================================================================

class Node:

    # Node class



    # Node class

    data: float

    left: Node | None = None

    right: Node | None = None



    def __iter__(self) -> Iterator[float]:

    # __iter__ function



    # __iter__ function

        """

        >>> root = Node(data=2.1)

        >>> list(root)

        [2.1]

        >>> root.left=Node(data=2.0)

        >>> list(root)

        [2.0, 2.1]

        >>> root.right=Node(data=2.2)

        >>> list(root)

        [2.0, 2.1, 2.2]

        """

        if self.left:

            yield from self.left

        yield self.data

        if self.right:

            yield from self.right



    @property

    def is_sorted(self) -> bool:

    # is_sorted function



    # is_sorted function

        """

        >>> Node(data='abc').is_sorted

        True

        >>> Node(data=2,

        ...      left=Node(data=1.999),

        ...      right=Node(data=3)).is_sorted

        True

        >>> Node(data=0,

        ...      left=Node(data=0),

        ...      right=Node(data=0)).is_sorted

        True

        >>> Node(data=0,

        ...      left=Node(data=-11),

        ...      right=Node(data=3)).is_sorted

        True

        >>> Node(data=5,

        ...      left=Node(data=1),

        ...      right=Node(data=4, left=Node(data=3))).is_sorted

        False

        >>> Node(data='a',

        ...      left=Node(data=1),

        ...      right=Node(data=4, left=Node(data=3))).is_sorted

        Traceback (most recent call last):

            ...

        TypeError: '<' not supported between instances of 'str' and 'int'

        >>> Node(data=2,

        ...      left=Node([]),

        ...      right=Node(data=4, left=Node(data=3))).is_sorted

        Traceback (most recent call last):

            ...

        TypeError: '<' not supported between instances of 'int' and 'list'

        """

        if self.left and (self.data < self.left.data or not self.left.is_sorted):

            return False

        return not (

            self.right and (self.data > self.right.data or not self.right.is_sorted)

        )





if __name__ == "__main__":

    import doctest



    doctest.testmod()

    tree = Node(data=2.1, left=Node(data=2.0), right=Node(data=2.2))

    print(f"Tree {list(tree)} is sorted: {tree.is_sorted = }.")

    assert tree.right

    tree.right.data = 2.0

    print(f"Tree {list(tree)} is sorted: {tree.is_sorted = }.")

    tree.right.data = 2.1

    print(f"Tree {list(tree)} is sorted: {tree.is_sorted = }.")

