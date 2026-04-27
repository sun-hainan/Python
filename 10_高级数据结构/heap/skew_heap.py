# -*- coding: utf-8 -*-
"""
算法实现：heap / skew_heap

本文件实现 skew_heap 相关的算法功能。
"""

from __future__ import annotations



#!/usr/bin/env python3

"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""


from collections.abc import Iterable, Iterator
from typing import Any, TypeVar

T = TypeVar("T", bound=bool)



# =============================================================================
# 算法模块：unknown
# =============================================================================
class SkewNode[T: bool]:
    # SkewNode class

    # SkewNode class
    """
    One node of the skew heap. Contains the value and references to
    two children.
    """


    def __init__(self, value: T) -> None:
    # __init__ function

    # __init__ function
        self._value: T = value
        self.left: SkewNode[T] | None = None
        self.right: SkewNode[T] | None = None

    @property
    def value(self) -> T:
    # value function

    # value function
        """
        Return the value of the node.

        >>> SkewNode(0).value
        0
        >>> SkewNode(3.14159).value
        3.14159
        >>> SkewNode("hello").value
        'hello'
        >>> SkewNode(None).value

        >>> SkewNode(True).value
        True
        >>> SkewNode([]).value
        []
        >>> SkewNode({}).value
        {}
        >>> SkewNode(set()).value
        set()
        >>> SkewNode(0.0).value
        0.0
        >>> SkewNode(-1e-10).value
        -1e-10
        >>> SkewNode(10).value
        10
        >>> SkewNode(-10.5).value
        -10.5
        >>> SkewNode().value
        Traceback (most recent call last):
        ...
        TypeError: SkewNode.__init__() missing 1 required positional argument: 'value'
        """
        return self._value

    @staticmethod
    def merge(
    # merge function

    # merge function
        root1: SkewNode[T] | None, root2: SkewNode[T] | None
    ) -> SkewNode[T] | None:
        """
        Merge 2 nodes together.
        >>> SkewNode.merge(SkewNode(10),SkewNode(-10.5)).value
        -10.5
        >>> SkewNode.merge(SkewNode(10),SkewNode(10.5)).value
        10
        >>> SkewNode.merge(SkewNode(10),SkewNode(10)).value
        10
        >>> SkewNode.merge(SkewNode(-100),SkewNode(-10.5)).value
        -100
        """
        if not root1:
            return root2

        if not root2:
            return root1

        if root1.value > root2.value:
            root1, root2 = root2, root1

        result = root1
        temp = root1.right
        result.right = root1.left
        result.left = SkewNode.merge(temp, root2)

        return result


class SkewHeap[T: bool]:
    # SkewHeap class

    # SkewHeap class
    """
    A data structure that allows inserting a new value and to pop the smallest
    values. Both operations take O(logN) time where N is the size of the
    structure.
    Wiki: https://en.wikipedia.org/wiki/Skew_heap
    Visualization: https://www.cs.usfca.edu/~galles/visualization/SkewHeap.html

    >>> list(SkewHeap([2, 3, 1, 5, 1, 7]))
    [1, 1, 2, 3, 5, 7]

    >>> sh = SkewHeap()
    >>> sh.pop()
    Traceback (most recent call last):
        ...
    IndexError: Can't get top element for the empty heap.

    >>> sh.insert(1)
    >>> sh.insert(-1)
    >>> sh.insert(0)
    >>> list(sh)
    [-1, 0, 1]
    """

    def __init__(self, data: Iterable[T] | None = ()) -> None:
    # __init__ function

    # __init__ function
        """
        >>> sh = SkewHeap([3, 1, 3, 7])
        >>> list(sh)
        [1, 3, 3, 7]
        """
        self._root: SkewNode[T] | None = None
        if data:
            for item in data:
                self.insert(item)

    def __bool__(self) -> bool:
    # __bool__ function

    # __bool__ function
        """
        Check if the heap is not empty.

        >>> sh = SkewHeap()
        >>> bool(sh)
        False
        >>> sh.insert(1)
        >>> bool(sh)
        True
        >>> sh.clear()
        >>> bool(sh)
        False
        """
        return self._root is not None

    def __iter__(self) -> Iterator[T]:
    # __iter__ function

    # __iter__ function
        """
        Returns sorted list containing all the values in the heap.

        >>> sh = SkewHeap([3, 1, 3, 7])
        >>> list(sh)
        [1, 3, 3, 7]
        """
        result: list[Any] = []
        while self:
            result.append(self.pop())

        # Pushing items back to the heap not to clear it.
        for item in result:
            self.insert(item)

        return iter(result)

    def insert(self, value: T) -> None:
    # insert function

    # insert function
        """
        Insert the value into the heap.

        >>> sh = SkewHeap()
        >>> sh.insert(3)
        >>> sh.insert(1)
        >>> sh.insert(3)
        >>> sh.insert(7)
        >>> list(sh)
        [1, 3, 3, 7]
        """
        self._root = SkewNode.merge(self._root, SkewNode(value))

    def pop(self) -> T | None:
    # pop function

    # pop function
        """
        Pop the smallest value from the heap and return it.

        >>> sh = SkewHeap([3, 1, 3, 7])
        >>> sh.pop()
        1
        >>> sh.pop()
        3
        >>> sh.pop()
        3
        >>> sh.pop()
        7
        >>> sh.pop()
        Traceback (most recent call last):
            ...
        IndexError: Can't get top element for the empty heap.
        """
        result = self.top()
        self._root = (
            SkewNode.merge(self._root.left, self._root.right) if self._root else None
        )

        return result

    def top(self) -> T:
    # top function

    # top function
        """
        Return the smallest value from the heap.

        >>> sh = SkewHeap()
        >>> sh.insert(3)
        >>> sh.top()
        3
        >>> sh.insert(1)
        >>> sh.top()
        1
        >>> sh.insert(3)
        >>> sh.top()
        1
        >>> sh.insert(7)
        >>> sh.top()
        1
        """
        if not self._root:
            raise IndexError("Can't get top element for the empty heap.")
        return self._root.value

    def clear(self) -> None:
    # clear function

    # clear function
        """
        Clear the heap.

        >>> sh = SkewHeap([3, 1, 3, 7])
        >>> sh.clear()
        >>> sh.pop()
        Traceback (most recent call last):
            ...
        IndexError: Can't get top element for the empty heap.
        """
        self._root = None


if __name__ == "__main__":
    import doctest

    doctest.testmod()
