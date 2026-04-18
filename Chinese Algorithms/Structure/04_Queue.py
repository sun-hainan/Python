"""
Queue - 队列
==========================================

【特点】
先进先出(FIFO): 最先放入的最先取出。

【操作】
- enqueue: 入队(到尾部)
- dequeue: 出队(从头部)

【应用场景】
- 任务调度队列
- 打印机队列
- BFS遍历
- 消息队列
- 排队叫号系统

【何时使用】
- 先进先出需求
- BFS算法
- 任务调度
- 异步处理

【实际案例】
# 打印队列
# 3个人打印文档，按顺序排队
print_queue = ["文档A", "文档B", "文档C"]
print_queue.pop(0)  # 先打印文档A

# 银行叫号系统
# 客户按到达顺序排队办理业务
bank_queue = ["客户1", "客户2", "客户3"]
next_customer = bank_queue.pop(0)  # 叫号：客户1

# 消息队列（异步处理）
# 订单处理：用户下单 -> 支付 -> 发货 -> 收货
order_queue = ["订单1", "订单2", "订单3"]
# 按顺序处理每个订单

# BFS - 迷宫最短路径
# 用队列存储待探索的路径
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
