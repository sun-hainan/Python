"""
Linked List - 链表
==========================================

【特点】
- 插入/删除: O(1)
- 查找: O(n)
- 不需要连续内存

【应用场景】
- 音乐播放列表管理
- 浏览器前进/后退
- 撤销/重做功能
- 任务队列

【何时使用】
- 需要频繁插入/删除
- 不确定数据大小
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
