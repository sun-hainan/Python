# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / tree_sort



本文件实现 tree_sort 相关的算法功能。

"""



from __future__ import annotations



"""

Tree_sort algorithm.



Build a Binary Search Tree and then iterate thru it to get a sorted list.

"""





from collections.abc import Iterator

from dataclasses import dataclass





@dataclass

class Node:

    val: int

    left: Node | None = None

    right: Node | None = None





# __iter__ 函数实现

    def __iter__(self) -> Iterator[int]:

        if self.left:

    # 条件判断

            yield from self.left

        yield self.val

        if self.right:

    # 条件判断

            yield from self.right





# __len__ 函数实现

    def __len__(self) -> int:

        return sum(1 for _ in self)

    # 返回结果





# insert 函数实现

    def insert(self, val: int) -> None:

        if val < self.val:

    # 条件判断

            if self.left is None:

    # 条件判断

                self.left = Node(val)

            else:

                self.left.insert(val)

        elif val > self.val:

            if self.right is None:

    # 条件判断

                self.right = Node(val)

            else:

                self.right.insert(val)







# tree_sort 函数实现

def tree_sort(arr: list[int]) -> tuple[int, ...]:

    """

    >>> tree_sort([])

    ()

    >>> tree_sort((1,))

    (1,)

    >>> tree_sort((1, 2))

    (1, 2)

    >>> tree_sort([5, 2, 7])

    (2, 5, 7)

    >>> tree_sort((5, -4, 9, 2, 7))

    (-4, 2, 5, 7, 9)

    >>> tree_sort([5, 6, 1, -1, 4, 37, 2, 7])

    (-1, 1, 2, 4, 5, 6, 7, 37)



    # >>> tree_sort(range(10, -10, -1)) == tuple(sorted(range(10, -10, -1)))

    # True

    """

    if len(arr) == 0:

    # 条件判断

        return tuple(arr)

    # 返回结果

    root = Node(arr[0])

    for item in arr[1:]:

    # 遍历循环

        root.insert(item)

    return tuple(root)

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

    print(f"{tree_sort([5, 6, 1, -1, 4, 37, -3, 7]) = }")

