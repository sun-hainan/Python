# -*- coding: utf-8 -*-
"""
算法实现：02_数据结构 / is_palindrome

本文件实现 is_palindrome 相关的算法功能。
"""

from __future__ import annotations

"""
Project Euler Problem  - Chinese comment version
https://projecteuler.net/problem=

问题描述: (请补充关于此题目具体问题描述)
解题思路: (请补充关于此题目的解题思路和算法原理)
"""




from dataclasses import dataclass


@dataclass

# =============================================================================
# 算法模块：is_palindrome
# =============================================================================
class ListNode:
    # ListNode class

    # ListNode class
    val: int = 0
    next_node: ListNode | None = None


def is_palindrome(head: ListNode | None) -> bool:
    # is_palindrome function

    # is_palindrome function
    """
    Check if a linked list is a palindrome.

    Args:
        head: The head of the linked list.

    Returns:
        bool: True if the linked list is a palindrome, False otherwise.

    Examples:
        >>> is_palindrome(None)
        True

        >>> is_palindrome(ListNode(1))
        True

        >>> is_palindrome(ListNode(1, ListNode(2)))
        False

        >>> is_palindrome(ListNode(1, ListNode(2, ListNode(1))))
        True

        >>> is_palindrome(ListNode(1, ListNode(2, ListNode(2, ListNode(1)))))
        True
    """

    if not head:
        return True
    # split the list to two parts
    fast: ListNode | None = head.next_node
    slow: ListNode | None = head
    while fast and fast.next_node:
        fast = fast.next_node.next_node
        slow = slow.next_node if slow else None
    if slow:
        # slow will always be defined,
        # adding this check to resolve mypy static check
        second = slow.next_node
        slow.next_node = None  # Don't forget here! But forget still works!
    # reverse the second part
    node: ListNode | None = None
    while second:
        nxt = second.next_node
        second.next_node = node
        node = second
        second = nxt
    # compare two parts
    # second part has the same or one less node
    while node and head:
        if node.val != head.val:
            return False
        node = node.next_node
        head = head.next_node
    return True


def is_palindrome_stack(head: ListNode | None) -> bool:
    # is_palindrome_stack function

    # is_palindrome_stack function
    """
    Check if a linked list is a palindrome using a stack.

    Args:
        head (ListNode): The head of the linked list.

    Returns:
        bool: True if the linked list is a palindrome, False otherwise.

    Examples:
        >>> is_palindrome_stack(None)
        True

        >>> is_palindrome_stack(ListNode(1))
        True

        >>> is_palindrome_stack(ListNode(1, ListNode(2)))
        False

        >>> is_palindrome_stack(ListNode(1, ListNode(2, ListNode(1))))
        True

        >>> is_palindrome_stack(ListNode(1, ListNode(2, ListNode(2, ListNode(1)))))
        True
    """
    if not head or not head.next_node:
        return True

    # 1. Get the midpoint (slow)
    slow: ListNode | None = head
    fast: ListNode | None = head
    while fast and fast.next_node:
        fast = fast.next_node.next_node
        slow = slow.next_node if slow else None

    # slow will always be defined,
    # adding this check to resolve mypy static check
    if slow:
        stack = [slow.val]

        # 2. Push the second half into the stack
        while slow.next_node:
            slow = slow.next_node
            stack.append(slow.val)

        # 3. Comparison
        cur: ListNode | None = head
        while stack and cur:
            if stack.pop() != cur.val:
                return False
            cur = cur.next_node

    return True


def is_palindrome_dict(head: ListNode | None) -> bool:
    # is_palindrome_dict function

    # is_palindrome_dict function
    """
    Check if a linked list is a palindrome using a dictionary.

    Args:
        head (ListNode): The head of the linked list.

    Returns:
        bool: True if the linked list is a palindrome, False otherwise.

    Examples:
        >>> is_palindrome_dict(None)
        True

        >>> is_palindrome_dict(ListNode(1))
        True

        >>> is_palindrome_dict(ListNode(1, ListNode(2)))
        False

        >>> is_palindrome_dict(ListNode(1, ListNode(2, ListNode(1))))
        True

        >>> is_palindrome_dict(ListNode(1, ListNode(2, ListNode(2, ListNode(1)))))
        True

        >>> is_palindrome_dict(
        ...     ListNode(
        ...         1, ListNode(2, ListNode(1, ListNode(3, ListNode(2, ListNode(1)))))
        ...     )
        ... )
        False
    """
    if not head or not head.next_node:
        return True
    d: dict[int, list[int]] = {}
    pos = 0
    while head:
        if head.val in d:
            d[head.val].append(pos)
        else:
            d[head.val] = [pos]
        head = head.next_node
        pos += 1
    checksum = pos - 1
    middle = 0
    for v in d.values():
        if len(v) % 2 != 0:
            middle += 1
        else:
            for step, i in enumerate(range(len(v))):
                if v[i] + v[len(v) - 1 - step] != checksum:
                    return False
        if middle > 1:
            return False
    return True


if __name__ == "__main__":
    import doctest

    doctest.testmod()
