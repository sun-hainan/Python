# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / fibonacci_search



本文件实现 fibonacci_search 相关的算法功能。

"""



from functools import lru_cache





@lru_cache



# fibonacci 函数实现

def fibonacci(k: int) -> int:

    """Finds fibonacci number in index k.



    Parameters

    ----------

    k :

        Index of fibonacci.



    Returns

    -------

    int

        Fibonacci number in position k.



    >>> fibonacci(0)

    0

    >>> fibonacci(2)

    1

    >>> fibonacci(5)

    5

    >>> fibonacci(15)

    610

    >>> fibonacci('a')

    Traceback (most recent call last):

    TypeError: k must be an integer.

    >>> fibonacci(-5)

    Traceback (most recent call last):

    ValueError: k integer must be greater or equal to zero.

    """

    if not isinstance(k, int):

    # 条件判断

        raise TypeError("k must be an integer.")

    if k < 0:

    # 条件判断

        raise ValueError("k integer must be greater or equal to zero.")

    if k == 0:

    # 条件判断

        return 0

    # 返回结果

    elif k == 1:

        return 1

    # 返回结果

    else:

        return fibonacci(k - 1) + fibonacci(k - 2)

    # 返回结果







# fibonacci_search 函数实现

def fibonacci_search(arr: list, val: int) -> int:

    """A pure Python implementation of a fibonacci search algorithm.



    Parameters

    ----------

    arr

        List of sorted elements.

    val

        Element to search in list.



    Returns

    -------

    int

        The index of the element in the array.

        -1 if the element is not found.



    >>> fibonacci_search([4, 5, 6, 7], 4)

    0

    >>> fibonacci_search([4, 5, 6, 7], -10)

    -1

    >>> fibonacci_search([-18, 2], -18)

    0

    >>> fibonacci_search([5], 5)

    0

    >>> fibonacci_search(['a', 'c', 'd'], 'c')

    1

    >>> fibonacci_search(['a', 'c', 'd'], 'f')

    -1

    >>> fibonacci_search([], 1)

    -1

    >>> fibonacci_search([.1, .4 , 7], .4)

    1

    >>> fibonacci_search([], 9)

    -1

    >>> fibonacci_search(list(range(100)), 63)

    63

    >>> fibonacci_search(list(range(100)), 99)

    99

    >>> fibonacci_search(list(range(-100, 100, 3)), -97)

    1

    >>> fibonacci_search(list(range(-100, 100, 3)), 0)

    -1

    >>> fibonacci_search(list(range(-100, 100, 5)), 0)

    20

    >>> fibonacci_search(list(range(-100, 100, 5)), 95)

    39

    """

    len_list = len(arr)

    # Find m such that F_m >= n where F_i is the i_th fibonacci number.

    i = 0

    while True:

    # 条件循环

        if fibonacci(i) >= len_list:

    # 条件判断

            fibb_k = i

            break

        i += 1

    offset = 0

    while fibb_k > 0:

    # 条件循环

        index_k = min(

            offset + fibonacci(fibb_k - 1), len_list - 1

        )  # Prevent out of range

        item_k_1 = arr[index_k]

        if item_k_1 == val:

    # 条件判断

            return index_k

    # 返回结果

        elif val < item_k_1:

            fibb_k -= 1

        elif val > item_k_1:

            offset += fibonacci(fibb_k - 1)

            fibb_k -= 2

    return -1

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

