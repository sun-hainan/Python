# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / stack



本文件实现 stack 相关的算法功能。

"""



from __future__ import annotations

from typing import TypeVar



T = TypeVar("T")





class StackOverflowError(BaseException):

    """栈溢出异常：push时栈已满"""

    pass





class StackUnderflowError(BaseException):

    """栈下溢异常：pop时栈为空"""

    pass





class Stack[T]:

    """

    栈实现



    示例:

        >>> S = Stack(2)  # 容量为2

        >>> S.push(10)

        >>> S.push(20)

        >>> print(S)

        [10, 20]

    """



    def __init__(self, limit: int = 10):

        self.stack: list[T] = []

        self.limit = limit  # 栈容量限制



    def __bool__(self) -> bool:

        return bool(self.stack)



    def __str__(self) -> str:

        return str(self.stack)



    def push(self, data: T) -> None:

        """

        入栈：将元素压入栈顶



        如果栈已满，抛出 StackOverflowError



        示例:

            >>> S = Stack(2)

            >>> S.push(10)

            >>> S.push(20)

            >>> S.push(30)  # 抛出异常

        """

        if len(self.stack) >= self.limit:

            raise StackOverflowError

        self.stack.append(data)



    def pop(self) -> T:

        """

        出栈：取出并返回栈顶元素



        如果栈为空，抛出 StackUnderflowError



        示例:

            >>> S = Stack()

            >>> S.push(10)

            >>> S.pop()

            10

        """

        if not self.stack:

            raise StackUnderflowError

        return self.stack.pop()



    def peek(self) -> T:

        """

        查看栈顶元素（不取出）



        示例:

            >>> S = Stack()

            >>> S.push(10)

            >>> S.push(20)

            >>> S.peek()

            20

        """

        if not self.stack:

            raise StackUnderflowError

        return self.stack[-1]



    def is_empty(self) -> bool:

        """检查栈是否为空"""

        return not bool(self.stack)



    def is_full(self) -> bool:

        """检查栈是否已满"""

        return self.size() == self.limit



    def size(self) -> int:

        """返回栈中元素数量"""

        return len(self.stack)



    def __contains__(self, item: T) -> bool:

        """检查元素是否在栈中"""

        return item in self.stack





def test_stack() -> None:

    """测试栈功能"""

    stack: Stack[int] = Stack(10)



    # 测试基本操作

    print(f"初始状态: {stack}, 是否为空: {stack.is_empty()}")



    # 入栈

    for i in range(5):

        stack.push(i)

        print(f"push({i}): {stack}")



    # 查看栈顶

    print(f"栈顶元素(peek): {stack.peek()}")

    print(f"栈大小: {stack.size()}")



    # 出栈

    print(f"pop(): {stack.pop()}, 剩余: {stack}")

    print(f"pop(): {stack.pop()}, 剩余: {stack}")



    # 反转操作验证

    stack.reverse()

    print(f"反转后: {stack}")





if __name__ == "__main__":

    test_stack()

