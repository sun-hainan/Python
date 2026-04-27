# -*- coding: utf-8 -*-
"""
算法实现：Structure / 02_Linked_List

本文件实现 02_Linked_List 相关的算法功能。
"""

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def reverse_list(head):
    prev = None
    curr = head
    while curr:
        next_node = curr.next
        curr.next = prev
        prev = curr
        curr = next_node
    return prev

def get_length(head):
    length = 0
    while head:
        length += 1
        head = head.next
    return length


if __name__ == "__main__":
    # 测试: get_length
    result = get_length()
    print(result)
