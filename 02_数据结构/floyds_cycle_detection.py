# -*- coding: utf-8 -*-
"""
算法实现：02_数据结构 / floyds_cycle_detection

本文件实现 floyds_cycle_detection 相关的算法功能。
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Self


@dataclass

# =============================================================================
# 算法模块：unknown
# =============================================================================
class Node:
    # Node class

    # Node class
    """
    A class representing a node in a singly linked list.
    """

    data: Any
    next_node: Self | None = None


@dataclass
class LinkedList:
    # LinkedList class

    # LinkedList class
    """
    A class representing a singly linked list.
    """

    head: Node | None = None

    def __iter__(self) -> Iterator:
    # __iter__ function

    # __iter__ function
        """
        Iterates through the linked list.

        Returns:
            Iterator: An iterator over the linked list.

        Examples:
        >>> linked_list = LinkedList()
        >>> list(linked_list)
        []
        >>> linked_list.add_node(1)
        >>> tuple(linked_list)
        (1,)
        """
        visited = []
        node = self.head
        while node:
            # Avoid infinite loop in there's a cycle
            if node in visited:
                return
            visited.append(node)
            yield node.data
            node = node.next_node

    def add_node(self, data: Any) -> None:
    # add_node function

    # add_node function
        """
        Adds a new node to the end of the linked list.

        Args:
            data (Any): The data to be stored in the new node.

        Examples:
        >>> linked_list = LinkedList()
        >>> linked_list.add_node(1)
        >>> linked_list.add_node(2)
        >>> linked_list.add_node(3)
        >>> linked_list.add_node(4)
        >>> tuple(linked_list)
        (1, 2, 3, 4)
        """
        new_node = Node(data)

        if self.head is None:
            self.head = new_node
            return

        current_node = self.head
        while current_node.next_node is not None:
            current_node = current_node.next_node

        current_node.next_node = new_node

    def detect_cycle(self) -> bool:
    # detect_cycle function

    # detect_cycle function
        """
        Detects if there is a cycle in the linked list using
        Floyd's cycle detection algorithm.

        Returns:
            bool: True if there is a cycle, False otherwise.

        Examples:
        >>> linked_list = LinkedList()
        >>> linked_list.add_node(1)
        >>> linked_list.add_node(2)
        >>> linked_list.add_node(3)
        >>> linked_list.add_node(4)

        >>> linked_list.detect_cycle()
        False

        # Create a cycle in the linked list
        >>> linked_list.head.next_node.next_node.next_node = linked_list.head.next_node

        >>> linked_list.detect_cycle()
        True
        """
        if self.head is None:
            return False

        slow_pointer: Node | None = self.head
        fast_pointer: Node | None = self.head

        while fast_pointer is not None and fast_pointer.next_node is not None:
            slow_pointer = slow_pointer.next_node if slow_pointer else None
            fast_pointer = fast_pointer.next_node.next_node
            if slow_pointer == fast_pointer:
                return True

        return False


if __name__ == "__main__":
    import doctest

    doctest.testmod()

    linked_list = LinkedList()
    linked_list.add_node(1)
    linked_list.add_node(2)
    linked_list.add_node(3)
    linked_list.add_node(4)

    # Create a cycle in the linked list
    # It first checks if the head, next_node, and next_node.next_node attributes of the
    # linked list are not None to avoid any potential type errors.
    if (
        linked_list.head
        and linked_list.head.next_node
        and linked_list.head.next_node.next_node
    ):
        linked_list.head.next_node.next_node.next_node = linked_list.head.next_node

    has_cycle = linked_list.detect_cycle()
    print(has_cycle)  # Output: True
