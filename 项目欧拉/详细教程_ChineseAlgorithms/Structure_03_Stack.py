# -*- coding: utf-8 -*-

"""

算法实现：Structure / 03_Stack



本文件实现 03_Stack 相关的算法功能。

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





if __name__ == "__main__":

    # 测试: size

    result = size()

    print(result)

