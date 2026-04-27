# -*- coding: utf-8 -*-

"""

算法实现：stacks / stack_with_doubly_linked_list



本文件实现 stack_with_doubly_linked_list 相关的算法功能。

"""



from __future__ import annotations







# A complete working Python program to demonstrate all

# stack operations using a doubly linked list



"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""





from typing import TypeVar



T = TypeVar("T")







# =============================================================================

# 算法模块：unknown

# =============================================================================

class Node[T]:

    # Node class



    # Node class

    def __init__(self, data: T):

    # __init__ function



    # __init__ function

        self.data = data  # Assign data

        self.next: Node[T] | None = None  # Initialize next as null

        self.prev: Node[T] | None = None  # Initialize prev as null





class Stack[T]:

    # Stack class



    # Stack class

    """

    >>> stack = Stack()

    >>> stack.is_empty()

    True

    >>> stack.print_stack()

    stack elements are:

    >>> for i in range(4):

    ...     stack.push(i)

    ...

    >>> stack.is_empty()

    False

    >>> stack.print_stack()

    stack elements are:

    3->2->1->0->

    >>> stack.top()

    3

    >>> len(stack)

    4

    >>> stack.pop()

    3

    >>> stack.print_stack()

    stack elements are:

    2->1->0->

    """





    def __init__(self) -> None:

    # __init__ function



    # __init__ function

        self.head: Node[T] | None = None



    def push(self, data: T) -> None:

    # push function



    # push function

        """add a Node to the stack"""

        if self.head is None:

            self.head = Node(data)

        else:

            new_node = Node(data)

            self.head.prev = new_node

            new_node.next = self.head

            new_node.prev = None

            self.head = new_node



    def pop(self) -> T | None:

        """pop the top element off the stack"""

        if self.head is None:

            return None

        else:

            assert self.head is not None

            temp = self.head.data

            self.head = self.head.next

            if self.head is not None:

                self.head.prev = None

            return temp



    def top(self) -> T | None:

    # top function



    # top function

        """return the top element of the stack"""

        return self.head.data if self.head is not None else None



    def __len__(self) -> int:

        temp = self.head

        count = 0

        while temp is not None:

            count += 1

            temp = temp.next

        return count



    def is_empty(self) -> bool:

        return self.head is None



    def print_stack(self) -> None:

        print("stack elements are:")

        temp = self.head

        while temp is not None:

            print(temp.data, end="->")

            temp = temp.next





# Code execution starts here

if __name__ == "__main__":

    # Start with the empty stack

    stack: Stack[int] = Stack()



    # Insert 4 at the beginning. So stack becomes 4->None

    print("Stack operations using Doubly LinkedList")

    stack.push(4)



    # Insert 5 at the beginning. So stack becomes 4->5->None

    stack.push(5)



    # Insert 6 at the beginning. So stack becomes 4->5->6->None

    stack.push(6)



    # Insert 7 at the beginning. So stack becomes 4->5->6->7->None

    stack.push(7)



    # Print the stack

    stack.print_stack()



    # Print the top element

    print("\nTop element is ", stack.top())



    # Print the stack size

    print("Size of the stack is ", len(stack))



    # pop the top element

    stack.pop()



    # pop the top element

    stack.pop()



    # two elements have now been popped off

    stack.print_stack()



    # Print True if the stack is empty else False

    print("\nstack is empty:", stack.is_empty())

