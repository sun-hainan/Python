# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / middle_element_of_linked_list



本文件实现 middle_element_of_linked_list 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""













# =============================================================================

# 算法模块：unknown

# =============================================================================

class Node:

    # Node class



    # Node class

    def __init__(self, data: int) -> None:

    # __init__ function



    # __init__ function

        self.data = data

        self.next = None





class LinkedList:

    # LinkedList class



    # LinkedList class

    def __init__(self):

    # __init__ function



    # __init__ function

        self.head = None



    def push(self, new_data: int) -> int:

    # push function



    # push function

        new_node = Node(new_data)

        new_node.next = self.head

        self.head = new_node

        return self.head.data



    def middle_element(self) -> int | None:

    # middle_element function



    # middle_element function

        """

        >>> link = LinkedList()

        >>> link.middle_element()

        No element found.

        >>> link.push(5)

        5

        >>> link.push(6)

        6

        >>> link.push(8)

        8

        >>> link.push(8)

        8

        >>> link.push(10)

        10

        >>> link.push(12)

        12

        >>> link.push(17)

        17

        >>> link.push(7)

        7

        >>> link.push(3)

        3

        >>> link.push(20)

        20

        >>> link.push(-20)

        -20

        >>> link.middle_element()

        12

        >>>

        """



        slow_pointer = self.head

        fast_pointer = self.head

        if self.head:

            while fast_pointer and fast_pointer.next:

                fast_pointer = fast_pointer.next.next

                slow_pointer = slow_pointer.next

            return slow_pointer.data

        else:

            print("No element found.")

            return None





if __name__ == "__main__":

    link = LinkedList()

    for _ in range(int(input().strip())):

        data = int(input().strip())

        link.push(data)

    print(link.middle_element())

