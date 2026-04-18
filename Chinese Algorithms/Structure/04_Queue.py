"""
Queue - 队列
==========================================

【特点】
先进先出(FIFO)

【应用场景】
- 打印队列
- 银行叫号系统
- BFS遍历
- 消息队列

【何时使用】
- 先进先出需求
- BFS算法
"""

from collections import deque

class Queue:
    def __init__(self):
        self.items = deque()
    
    def enqueue(self, item):
        self.items.append(item)
    
    def dequeue(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items.popleft()
    
    def front(self):
        if self.is_empty():
            raise IndexError("Queue is empty")
        return self.items[0]
    
    def is_empty(self):
        return len(self.items) == 0
    
    def size(self):
        return len(self.items)
