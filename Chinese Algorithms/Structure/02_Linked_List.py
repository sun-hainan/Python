"""
Linked List - 链表
==========================================

【特点】
- 插入/删除: O(1)
- 查找: O(n)
- 不需要连续内存

【应用场景】
- 音乐播放器播放列表
- 浏览器前进/后退
- 任务队列
- 撤销/重做功能

【何时使用】
- 需要频繁插入/删除
- 不确定数据大小
- 实现栈/队列

【实际案例】
# 音乐播放器播放列表
# 歌曲列表：[歌曲A] -> [歌曲B] -> [歌曲C]
# 删除歌曲B，添加歌曲D：O(1)操作
playlist = ["歌曲A", "歌曲B", "歌曲C"]
# 删除B: O(1)
# 添加D到B后面: O(1)

# 浏览器前进/后退
# 浏览历史：页面1 -> 页面2 -> 页面3
# 后退：回到页面2
# 前进：到页面3

# 撤销/重做功能
# Ctrl+Z撤销，Ctrl+Y重做
# 用两个栈实现
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
