# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / lazy_segment_tree



本文件实现 lazy_segment_tree 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""









import math







# =============================================================================

# 算法模块：unknown

# =============================================================================

class SegmentTree:

    # SegmentTree class



    # SegmentTree class

    def __init__(self, size: int) -> None:

    # __init__ function



    # __init__ function

        self.size = size

        # approximate the overall size of segment tree with given value

        self.segment_tree = [0 for i in range(4 * size)]

        # create array to store lazy update

        self.lazy = [0 for i in range(4 * size)]

        self.flag = [0 for i in range(4 * size)]  # flag for lazy update



    def left(self, idx: int) -> int:

    # left function



    # left function

        """

        >>> segment_tree = SegmentTree(15)

        >>> segment_tree.left(1)

        2

        >>> segment_tree.left(2)

        4

        >>> segment_tree.left(12)

        24

        """



        return idx * 2



    def right(self, idx: int) -> int:

    # right function



    # right function

        """

        >>> segment_tree = SegmentTree(15)

        >>> segment_tree.right(1)

        3

        >>> segment_tree.right(2)

        5

        >>> segment_tree.right(12)

        25

        """

        return idx * 2 + 1



    def build(

    # build function



    # build function

        self, idx: int, left_element: int, right_element: int, a: list[int]

    ) -> None:

        if left_element == right_element:

            self.segment_tree[idx] = a[left_element - 1]

        else:

            mid = (left_element + right_element) // 2

            self.build(self.left(idx), left_element, mid, a)

            self.build(self.right(idx), mid + 1, right_element, a)

            self.segment_tree[idx] = max(

                self.segment_tree[self.left(idx)], self.segment_tree[self.right(idx)]

            )



    def update(

    # update function



    # update function

        self, idx: int, left_element: int, right_element: int, a: int, b: int, val: int

    ) -> bool:

        """

        update with O(lg n) (Normal segment tree without lazy update will take O(nlg n)

        for each update)



        update(1, 1, size, a, b, v) for update val v to [a,b]

        """

        if self.flag[idx] is True:

            self.segment_tree[idx] = self.lazy[idx]

            self.flag[idx] = False

            if left_element != right_element:

                self.lazy[self.left(idx)] = self.lazy[idx]

                self.lazy[self.right(idx)] = self.lazy[idx]

                self.flag[self.left(idx)] = True

                self.flag[self.right(idx)] = True



        if right_element < a or left_element > b:

            return True

        if left_element >= a and right_element <= b:

            self.segment_tree[idx] = val

            if left_element != right_element:

                self.lazy[self.left(idx)] = val

                self.lazy[self.right(idx)] = val

                self.flag[self.left(idx)] = True

                self.flag[self.right(idx)] = True

            return True

        mid = (left_element + right_element) // 2

        self.update(self.left(idx), left_element, mid, a, b, val)

        self.update(self.right(idx), mid + 1, right_element, a, b, val)

        self.segment_tree[idx] = max(

            self.segment_tree[self.left(idx)], self.segment_tree[self.right(idx)]

        )

        return True



    # query with O(lg n)

    def query(

    # query function



    # query function

        self, idx: int, left_element: int, right_element: int, a: int, b: int

    ) -> int | float:

        """

        query(1, 1, size, a, b) for query max of [a,b]

        >>> A = [1, 2, -4, 7, 3, -5, 6, 11, -20, 9, 14, 15, 5, 2, -8]

        >>> segment_tree = SegmentTree(15)

        >>> segment_tree.build(1, 1, 15, A)

        >>> segment_tree.query(1, 1, 15, 4, 6)

        7

        >>> segment_tree.query(1, 1, 15, 7, 11)

        14

        >>> segment_tree.query(1, 1, 15, 7, 12)

        15

        """

        if self.flag[idx] is True:

            self.segment_tree[idx] = self.lazy[idx]

            self.flag[idx] = False

            if left_element != right_element:

                self.lazy[self.left(idx)] = self.lazy[idx]

                self.lazy[self.right(idx)] = self.lazy[idx]

                self.flag[self.left(idx)] = True

                self.flag[self.right(idx)] = True

        if right_element < a or left_element > b:

            return -math.inf

        if left_element >= a and right_element <= b:

            return self.segment_tree[idx]

        mid = (left_element + right_element) // 2

        q1 = self.query(self.left(idx), left_element, mid, a, b)

        q2 = self.query(self.right(idx), mid + 1, right_element, a, b)

        return max(q1, q2)



    def __str__(self) -> str:

    # __str__ function



    # __str__ function

        return str([self.query(1, 1, self.size, i, i) for i in range(1, self.size + 1)])





if __name__ == "__main__":

    A = [1, 2, -4, 7, 3, -5, 6, 11, -20, 9, 14, 15, 5, 2, -8]

    size = 15

    segt = SegmentTree(size)

    segt.build(1, 1, size, A)

    print(segt.query(1, 1, size, 4, 6))

    print(segt.query(1, 1, size, 7, 11))

    print(segt.query(1, 1, size, 7, 12))

    segt.update(1, 1, size, 1, 3, 111)

    print(segt.query(1, 1, size, 1, 15))

    segt.update(1, 1, size, 7, 8, 235)

    print(segt)

