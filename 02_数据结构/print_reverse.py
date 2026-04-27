# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / print_reverse



本文件实现 print_reverse 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""









from collections.abc import Iterable, Iterator

from dataclasses import dataclass





@dataclass



# =============================================================================

# 算法模块：make_linked_list

# =============================================================================

class Node:

    # Node class



    # Node class

    data: int

    next_node: Node | None = None





class LinkedList:

    # LinkedList class



    # LinkedList class

    """A class to represent a Linked List.

    Use a tail pointer to speed up the append() operation.

    """





    def __init__(self) -> None:

    # __init__ function



    # __init__ function

        """Initialize a LinkedList with the head node set to None.

        >>> linked_list = LinkedList()

        >>> (linked_list.head, linked_list.tail)

        (None, None)

        """

        self.head: Node | None = None

        self.tail: Node | None = None  # Speeds up the append() operation



    def __iter__(self) -> Iterator[int]:

    # __iter__ function



    # __iter__ function

        """Iterate the LinkedList yielding each Node's data.

        >>> linked_list = LinkedList()

        >>> items = (1, 2, 3, 4, 5)

        >>> linked_list.extend(items)

        >>> tuple(linked_list) == items

        True

        """

        node = self.head

        while node:

            yield node.data

            node = node.next_node



    def __repr__(self) -> str:

    # __repr__ function



    # __repr__ function

        """Returns a string representation of the LinkedList.

        >>> linked_list = LinkedList()

        >>> str(linked_list)

        ''

        >>> linked_list.append(1)

        >>> str(linked_list)

        '1'

        >>> linked_list.extend([2, 3, 4, 5])

        >>> str(linked_list)

        '1 -> 2 -> 3 -> 4 -> 5'

        """

        return " -> ".join([str(data) for data in self])



    def append(self, data: int) -> None:

    # append function



    # append function

        """Appends a new node with the given data to the end of the LinkedList.

        >>> linked_list = LinkedList()

        >>> str(linked_list)

        ''

        >>> linked_list.append(1)

        >>> str(linked_list)

        '1'

        >>> linked_list.append(2)

        >>> str(linked_list)

        '1 -> 2'

        """

        if self.tail:

            self.tail.next_node = self.tail = Node(data)

        else:

            self.head = self.tail = Node(data)



    def extend(self, items: Iterable[int]) -> None:

    # extend function



    # extend function

        """Appends each item to the end of the LinkedList.

        >>> linked_list = LinkedList()

        >>> linked_list.extend([])

        >>> str(linked_list)

        ''

        >>> linked_list.extend([1, 2])

        >>> str(linked_list)

        '1 -> 2'

        >>> linked_list.extend([3,4])

        >>> str(linked_list)

        '1 -> 2 -> 3 -> 4'

        """

        for item in items:

            self.append(item)





def make_linked_list(elements_list: Iterable[int]) -> LinkedList:

    # make_linked_list function



    # make_linked_list function

    """Creates a Linked List from the elements of the given sequence

    (list/tuple) and returns the head of the Linked List.

    >>> make_linked_list([])

    Traceback (most recent call last):

        ...

    Exception: The Elements List is empty

    >>> make_linked_list([7])

    7

    >>> make_linked_list(['abc'])

    abc

    >>> make_linked_list([7, 25])

    7 -> 25

    """

    if not elements_list:

        raise Exception("The Elements List is empty")



    linked_list = LinkedList()

    linked_list.extend(elements_list)

    return linked_list





def in_reverse(linked_list: LinkedList) -> str:

    # in_reverse function



    # in_reverse function

    """Prints the elements of the given Linked List in reverse order

    >>> in_reverse(LinkedList())

    ''

    >>> in_reverse(make_linked_list([69, 88, 73]))

    '73 <- 88 <- 69'

    """

    return " <- ".join(str(line) for line in reversed(tuple(linked_list)))





if __name__ == "__main__":

    from doctest import testmod



    testmod()

    linked_list = make_linked_list((14, 52, 14, 12, 43))

    print(f"Linked List:  {linked_list}")

    print(f"Reverse List: {in_reverse(linked_list)}")

