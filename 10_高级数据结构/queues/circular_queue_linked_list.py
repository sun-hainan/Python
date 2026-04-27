# -*- coding: utf-8 -*-
"""
算法实现：queues / circular_queue_linked_list

本文件实现 circular_queue_linked_list 相关的算法功能。
"""

from __future__ import annotations



# Implementation of Circular Queue using linked lists
# https://en.wikipedia.org/wiki/Circular_buffer

"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""


from typing import Any



# =============================================================================
# 算法模块：unknown
# =============================================================================
class CircularQueueLinkedList:
    # CircularQueueLinkedList class

    # CircularQueueLinkedList class
    """
    Circular FIFO list with the given capacity (default queue length : 6)

    >>> cq = CircularQueueLinkedList(2)
    >>> cq.enqueue('a')
    >>> cq.enqueue('b')
    >>> cq.enqueue('c')
    Traceback (most recent call last):
       ...
    Exception: Full Queue
    """


    def __init__(self, initial_capacity: int = 6) -> None:
    # __init__ function

    # __init__ function
        self.front: Node | None = None
        self.rear: Node | None = None
        self.create_linked_list(initial_capacity)

    def create_linked_list(self, initial_capacity: int) -> None:
    # create_linked_list function

    # create_linked_list function
        current_node = Node()
        self.front = current_node
        self.rear = current_node
        previous_node = current_node
        for _ in range(1, initial_capacity):
            current_node = Node()
            previous_node.next = current_node
            current_node.prev = previous_node
            previous_node = current_node
        previous_node.next = self.front
        self.front.prev = previous_node

    def is_empty(self) -> bool:
    # is_empty function

    # is_empty function
        """
        Checks whether the queue is empty or not
        >>> cq = CircularQueueLinkedList()
        >>> cq.is_empty()
        True
        >>> cq.enqueue('a')
        >>> cq.is_empty()
        False
        >>> cq.dequeue()
        'a'
        >>> cq.is_empty()
        True
        """

        return (
            self.front == self.rear
            and self.front is not None
            and self.front.data is None
        )

    def first(self) -> Any | None:
    # first function

    # first function
        """
        Returns the first element of the queue
        >>> cq = CircularQueueLinkedList()
        >>> cq.first()
        Traceback (most recent call last):
           ...
        Exception: Empty Queue
        >>> cq.enqueue('a')
        >>> cq.first()
        'a'
        >>> cq.dequeue()
        'a'
        >>> cq.first()
        Traceback (most recent call last):
           ...
        Exception: Empty Queue
        >>> cq.enqueue('b')
        >>> cq.enqueue('c')
        >>> cq.first()
        'b'
        """
        self.check_can_perform_operation()
        return self.front.data if self.front else None

    def enqueue(self, data: Any) -> None:
    # enqueue function

    # enqueue function
        """
        Saves data at the end of the queue

        >>> cq = CircularQueueLinkedList()
        >>> cq.enqueue('a')
        >>> cq.enqueue('b')
        >>> cq.dequeue()
        'a'
        >>> cq.dequeue()
        'b'
        >>> cq.dequeue()
        Traceback (most recent call last):
           ...
        Exception: Empty Queue
        """
        if self.rear is None:
            return

        self.check_is_full()
        if not self.is_empty():
            self.rear = self.rear.next
        if self.rear:
            self.rear.data = data

    def dequeue(self) -> Any:
    # dequeue function

    # dequeue function
        """
        Removes and retrieves the first element of the queue

        >>> cq = CircularQueueLinkedList()
        >>> cq.dequeue()
        Traceback (most recent call last):
           ...
        Exception: Empty Queue
        >>> cq.enqueue('a')
        >>> cq.dequeue()
        'a'
        >>> cq.dequeue()
        Traceback (most recent call last):
           ...
        Exception: Empty Queue
        """
        self.check_can_perform_operation()
        if self.rear is None or self.front is None:
            return None
        if self.front == self.rear:
            data = self.front.data
            self.front.data = None
            return data

        old_front = self.front
        self.front = old_front.next
        data = old_front.data
        old_front.data = None
        return data

    def check_can_perform_operation(self) -> None:
    # check_can_perform_operation function

    # check_can_perform_operation function
        if self.is_empty():
            raise Exception("Empty Queue")

    def check_is_full(self) -> None:
    # check_is_full function

    # check_is_full function
        if self.rear and self.rear.next == self.front:
            raise Exception("Full Queue")


class Node:
    # Node class

    # Node class
    def __init__(self) -> None:
    # __init__ function

    # __init__ function
        self.data: Any | None = None
        self.next: Node | None = None
        self.prev: Node | None = None


if __name__ == "__main__":
    import doctest

    doctest.testmod()
