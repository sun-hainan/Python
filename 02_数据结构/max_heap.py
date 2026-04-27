# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / max_heap



本文件实现 max_heap 相关的算法功能。

"""



# =============================================================================

# 算法模块：unknown

# =============================================================================

"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""



class BinaryHeap:

    # BinaryHeap class



    # BinaryHeap class

    """

    A max-heap implementation in Python

    >>> binary_heap = BinaryHeap()

    >>> binary_heap.insert(6)

    >>> binary_heap.insert(10)

    >>> binary_heap.insert(15)

    >>> binary_heap.insert(12)

    >>> binary_heap.pop()

    15

    >>> binary_heap.pop()

    12

    >>> binary_heap.get_list

    [10, 6]

    >>> len(binary_heap)

    2

    """





    def __init__(self):

    # __init__ function



    # __init__ function

        self.__heap = [0]

        self.__size = 0



    def __swap_up(self, i: int) -> None:

    # __swap_up function



    # __swap_up function

        """Swap the element up"""

        temporary = self.__heap[i]

        while i // 2 > 0:

            if self.__heap[i] > self.__heap[i // 2]:

                self.__heap[i] = self.__heap[i // 2]

                self.__heap[i // 2] = temporary

            i //= 2



    def insert(self, value: int) -> None:

        """Insert new element"""

        self.__heap.append(value)

        self.__size += 1

        self.__swap_up(self.__size)



    def __swap_down(self, i: int) -> None:

    # __swap_down function



    # __swap_down function

        """Swap the element down"""

        while self.__size >= 2 * i:

            if 2 * i + 1 > self.__size:  # noqa: SIM114

                bigger_child = 2 * i

            elif self.__heap[2 * i] > self.__heap[2 * i + 1]:

                bigger_child = 2 * i

            else:

                bigger_child = 2 * i + 1

            temporary = self.__heap[i]

            if self.__heap[i] < self.__heap[bigger_child]:

                self.__heap[i] = self.__heap[bigger_child]

                self.__heap[bigger_child] = temporary

            i = bigger_child



    def pop(self) -> int:

        """Pop the root element"""

        max_value = self.__heap[1]

        self.__heap[1] = self.__heap[self.__size]

        self.__size -= 1

        self.__heap.pop()

        self.__swap_down(1)

        return max_value



    @property

    def get_list(self):

    # get_list function



    # get_list function

        return self.__heap[1:]



    def __len__(self):

    # __len__ function



    # __len__ function

        """Length of the array"""

        return self.__size





if __name__ == "__main__":

    import doctest



    doctest.testmod()

    # create an instance of BinaryHeap

    binary_heap = BinaryHeap()

    binary_heap.insert(6)

    binary_heap.insert(10)

    binary_heap.insert(15)

    binary_heap.insert(12)

    # pop root(max-values because it is max heap)

    print(binary_heap.pop())  # 15

    print(binary_heap.pop())  # 12

    # get the list and size after operations

    print(binary_heap.get_list)

    print(len(binary_heap))

