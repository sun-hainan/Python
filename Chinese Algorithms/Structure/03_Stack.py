"""
Stack - 栈
==========================================

【特点】
后进先出(LIFO)

【应用场景】
- 函数调用栈
- 括号匹配检查
- 表达式求值
- 浏览器后退
- 撤销操作

【何时使用】
- 后进先出需求
- 括号匹配
"""

class Stack:
    def __init__(self):
        self.items = []
    
    def push(self, item):
        self.items.append(item)
    
    def pop(self):
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items.pop()
    
    def peek(self):
        if self.is_empty():
            raise IndexError("Stack is empty")
        return self.items[-1]
    
    def is_empty(self):
        return len(self.items) == 0
    
    def size(self):
        return len(self.items)
