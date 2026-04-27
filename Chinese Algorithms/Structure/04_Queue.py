# -*- coding: utf-8 -*-

"""

算法实现：Structure / 04_Queue



本文件实现 04_Queue 相关的算法功能。

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





if __name__ == "__main__":

    # 测试: size

    result = size()

    print(result)

