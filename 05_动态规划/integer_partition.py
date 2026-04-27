# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / integer_partition



本文件实现 integer_partition 相关的算法功能。

"""



def partition(m: int) -> int:

    # partition function



    # partition function

    # partition 函数实现

    """

    >>> partition(5)

    7

    >>> partition(7)

    15

    >>> partition(100)

    190569292

    >>> partition(1_000)

    24061467864032622473692149727991

    >>> partition(-7)

    Traceback (most recent call last):

        ...

    IndexError: list index out of range

    >>> partition(0)

    Traceback (most recent call last):

        ...

    IndexError: list assignment index out of range

    >>> partition(7.8)

    Traceback (most recent call last):

        ...

    TypeError: 'float' object cannot be interpreted as an integer

    """

    memo: list[list[int]] = [[0 for _ in range(m)] for _ in range(m + 1)]

    for i in range(m + 1):

        memo[i][0] = 1



    for n in range(m + 1):

        for k in range(1, m):

            memo[n][k] += memo[n][k - 1]

            if n - k > 0:

                memo[n][k] += memo[n - k - 1][k]



    return memo[m][m - 1]





if __name__ == "__main__":

    import sys



    if len(sys.argv) == 1:

        try:

            n = int(input("Enter a number: ").strip())

            print(partition(n))

        except ValueError:

            print("Please enter a number.")

    else:

        try:

            n = int(sys.argv[1])

            print(partition(n))

        except ValueError:

            print("Please pass a number.")

