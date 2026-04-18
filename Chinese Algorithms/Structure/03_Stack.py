"""
Stack - 栈
==========================================

【特点】
后进先出(LIFO): 最后放入的最先取出。

【操作】
- push: 入栈(放到顶部)
- pop: 出栈(从顶部取出)
- peek: 查看栈顶元素

【应用场景】
- 函数调用栈（递归）
- 括号匹配检查
- 表达式求值
- 浏览器后退
- 撤销操作

【何时使用】
- 后进先出需求
- 括号匹配
- 表达式计算
- 递归改迭代

【实际案例】
# 括号匹配检查
# "({[]})" 是合法的 "( {" 是不合法的
brackets = "{[()()]}"
is_valid = True  # 检查括号是否匹配

# 表达式求值（计算器）
# 输入 "3 + 4 * 2" 按优先级计算
expression = "3 + 4 * 2"
# 用栈实现计算器

# 浏览器后退
# 浏览顺序：淘宝 -> 京东 -> 拼多多
# 后退按钮：回到京东
back_stack = ["淘宝", "京东", "拼多多"]
back_stack.pop()  # 弹出"拼多多"，当前是"京东"
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
