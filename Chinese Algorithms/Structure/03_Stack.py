"""
Stack - 栈
==========================================

【数据结构特点】
后进先出(LIFO): 最后放入的最先取出。

【基本操作】
- push: 入栈(放到顶部)
- pop: 出栈(从顶部取出)
- peek: 查看栈顶元素

【应用场景】
- 函数调用栈
- 括号匹配检查
- 表达式求值
- 浏览器后退功能
"""

class Stack:
    """栈实现"""
    
    def __init__(self):
        self.items = []
    
    def push(self, item):
        """入栈"""
        self.items.append(item)
    
    def pop(self):
        """出栈"""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items.pop()
    
    def peek(self):
        """查看栈顶元素"""
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items[-1]
    
    def is_empty(self):
        """是否为空"""
        return len(self.items) == 0
    
    def size(self):
        """栈大小"""
        return len(self.items)


# ---------- Queue ----------
FILES['Chinese Algorithms/Structure/04_Queue.py'] = 
Queue - 队列
==========================================

【数据结构特点】
先进先出(FIFO): 最先放入的最先取出。

【基本操作】
- enqueue: 入队(到尾部)
- dequeue: 出队(从头部)

【应用场景】
- 任务调度队列
- 广度优先搜索
- 打印队列
- 消息队列
