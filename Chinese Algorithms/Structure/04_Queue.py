"""
Queue - 队列
==========================================

【特点】
先进先出(FIFO)

【应用场景】
- 任务调度队列
- 广度优先搜索
- 打印队列
"""

from collections import deque

class Queue:
    """队列实现"""
    
    def __init__(self):
        self.items = deque()
    
    def enqueue(self, item):
        """入队"""
        self.items.append(item)
    
    def dequeue(self):
        """出队"""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items.popleft()
    
    def front(self):
        """查看队首"""
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items[0]
    
    def is_empty(self):
        return len(self.items) == 0
    
    def size(self):
        return len(self.items)
