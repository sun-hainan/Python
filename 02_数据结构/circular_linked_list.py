# -*- coding: utf-8 -*-
"""
算法实现：02_数据结构 / circular_linked_list

本文件实现 circular_linked_list 相关的算法功能。
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
from typing import Any


@dataclass

# =============================================================================
# 算法模块：test_circular_linked_list
# =============================================================================
class Node:
    # Node class

    # Node class
    data: Any
    next_node: Node | None = None


@dataclass
class CircularLinkedList:
    # CircularLinkedList class

    # CircularLinkedList class
    head: Node | None = None  # Reference to the head (first node)
    tail: Node | None = None  # Reference to the tail (last node)

    def __iter__(self) -> Iterator[Any]:
    # __iter__ function

    # __iter__ function
        """
        Iterate through all nodes in the Circular Linked List yielding their data.
        Yields:
            The data of each node in the linked list.
        """

        node = self.head
        while node:
            yield node.data
            node = node.next_node
            if node == self.head:
                break

    def __len__(self) -> int:
    # __len__ function

    # __len__ function
        """
        Get the length (number of nodes) in the Circular Linked List.
        """
        return sum(1 for _ in self)

    def __repr__(self) -> str:
    # __repr__ function

    # __repr__ function
        """
        Generate a string representation of the Circular Linked List.
        Returns:
            A string of the format "1->2->....->N".
        """
        return "->".join(str(item) for item in iter(self))

    def insert_tail(self, data: Any) -> None:
    # insert_tail function

    # insert_tail function
        """
        Insert a node with the given data at the end of the Circular Linked List.
        """
        self.insert_nth(len(self), data)

    def insert_head(self, data: Any) -> None:
    # insert_head function

    # insert_head function
        """
        Insert a node with the given data at the beginning of the Circular Linked List.
        """
        self.insert_nth(0, data)

    def insert_nth(self, index: int, data: Any) -> None:
    # insert_nth function

    # insert_nth function
        """
        Insert the data of the node at the nth pos in the Circular Linked List.
        Args:
            index: The index at which the data should be inserted.
            data: The data to be inserted.

        Raises:
            IndexError: If the index is out of range.
        """
        if index < 0 or index > len(self):
            raise IndexError("list index out of range.")
        new_node: Node = Node(data)
        if self.head is None:
            new_node.next_node = new_node  # First node points to itself
            self.tail = self.head = new_node
        elif index == 0:  # Insert at the head
            new_node.next_node = self.head
            assert self.tail is not None  # List is not empty, tail exists
            self.head = self.tail.next_node = new_node
        else:
            temp: Node | None = self.head
            for _ in range(index - 1):
                assert temp is not None
                temp = temp.next_node
            assert temp is not None
            new_node.next_node = temp.next_node
            temp.next_node = new_node
            if index == len(self) - 1:  # Insert at the tail
                self.tail = new_node

    def delete_front(self) -> Any:
    # delete_front function

    # delete_front function
        """
        Delete and return the data of the node at the front of the Circular Linked List.
        Raises:
            IndexError: If the list is empty.
        """
        return self.delete_nth(0)

    def delete_tail(self) -> Any:
    # delete_tail function

    # delete_tail function
        """
        Delete and return the data of the node at the end of the Circular Linked List.
        Returns:
            Any: The data of the deleted node.
        Raises:
            IndexError: If the index is out of range.
        """
        return self.delete_nth(len(self) - 1)

    def delete_nth(self, index: int = 0) -> Any:
    # delete_nth function

    # delete_nth function
        """
        Delete and return the data of the node at the nth pos in Circular Linked List.
        Args:
            index (int): The index of the node to be deleted. Defaults to 0.
        Returns:
            Any: The data of the deleted node.
        Raises:
            IndexError: If the index is out of range.
        """
        if not 0 <= index < len(self):
            raise IndexError("list index out of range.")

        assert self.head is not None
        assert self.tail is not None
        delete_node: Node = self.head
        if self.head == self.tail:  # Just one node
            self.head = self.tail = None
        elif index == 0:  # Delete head node
            assert self.tail.next_node is not None
            self.tail.next_node = self.tail.next_node.next_node
            self.head = self.head.next_node
        else:
            temp: Node | None = self.head
            for _ in range(index - 1):
                assert temp is not None
                temp = temp.next_node
            assert temp is not None
            assert temp.next_node is not None
            delete_node = temp.next_node
            temp.next_node = temp.next_node.next_node
            if index == len(self) - 1:  # Delete at tail
                self.tail = temp
        return delete_node.data

    def is_empty(self) -> bool:
    # is_empty function

    # is_empty function
        """
        Check if the Circular Linked List is empty.
        Returns:
            bool: True if the list is empty, False otherwise.
        """
        return len(self) == 0


def test_circular_linked_list() -> None:
    # test_circular_linked_list function

    # test_circular_linked_list function
    """
    Test cases for the CircularLinkedList class.
    >>> test_circular_linked_list()
    """
    circular_linked_list = CircularLinkedList()
    assert len(circular_linked_list) == 0
    assert circular_linked_list.is_empty() is True
    assert str(circular_linked_list) == ""

    try:
        circular_linked_list.delete_front()
        raise AssertionError  # This should not happen
    except IndexError:
        assert True  # This should happen

    try:
        circular_linked_list.delete_tail()
        raise AssertionError  # This should not happen
    except IndexError:
        assert True  # This should happen

    try:
        circular_linked_list.delete_nth(-1)
        raise AssertionError
    except IndexError:
        assert True

    try:
        circular_linked_list.delete_nth(0)
        raise AssertionError
    except IndexError:
        assert True

    assert circular_linked_list.is_empty() is True
    for i in range(5):
        assert len(circular_linked_list) == i
        circular_linked_list.insert_nth(i, i + 1)
    assert str(circular_linked_list) == "->".join(str(i) for i in range(1, 6))

    circular_linked_list.insert_tail(6)
    assert str(circular_linked_list) == "->".join(str(i) for i in range(1, 7))
    circular_linked_list.insert_head(0)
    assert str(circular_linked_list) == "->".join(str(i) for i in range(7))

    assert circular_linked_list.delete_front() == 0
    assert circular_linked_list.delete_tail() == 6
    assert str(circular_linked_list) == "->".join(str(i) for i in range(1, 6))
    assert circular_linked_list.delete_nth(2) == 3

    circular_linked_list.insert_nth(2, 3)
    assert str(circular_linked_list) == "->".join(str(i) for i in range(1, 6))

    assert circular_linked_list.is_empty() is False


if __name__ == "__main__":
    import doctest

    doctest.testmod()
