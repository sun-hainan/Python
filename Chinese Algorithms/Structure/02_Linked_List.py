"""
Linked List - 链表
==========================================

【特点】
- 插入/删除: O(1)
- 查找: O(n)
- 不需要连续内存

【应用场景】
- 历史记录/Undo功能
- 任务队列管理
"""

class ListNode:
    """链表节点"""
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def reverse_list(head):
    """反转链表"""
    prev = None
    curr = head
    while curr:
        next_node = curr.next
        curr.next = prev
        prev = curr
        curr = next_node
    return prev


def get_length(head):
    """获取链表长度"""
    length = 0
    while head:
        length += 1
        head = head.next
    return length
