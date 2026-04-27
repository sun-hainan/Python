# -*- coding: utf-8 -*-

"""

Project Euler Problem 031



解决 Project Euler 第 031 题的 Python 实现。

https://projecteuler.net/problem=031

"""



# =============================================================================

# Project Euler 问题 031

# =============================================================================

def one_pence() -> int:

    return 1

    # 返回结果





def two_pence(x: int) -> int:

    # two_pence 函数实现

    return 0 if x < 0 else two_pence(x - 2) + one_pence()





def five_pence(x: int) -> int:

    # five_pence 函数实现

    return 0 if x < 0 else five_pence(x - 5) + two_pence(x)





def ten_pence(x: int) -> int:

    # ten_pence 函数实现

    return 0 if x < 0 else ten_pence(x - 10) + five_pence(x)





def twenty_pence(x: int) -> int:

    # twenty_pence 函数实现

    return 0 if x < 0 else twenty_pence(x - 20) + ten_pence(x)





def fifty_pence(x: int) -> int:

    # fifty_pence 函数实现

    return 0 if x < 0 else fifty_pence(x - 50) + twenty_pence(x)





def one_pound(x: int) -> int:

    # one_pound 函数实现

    return 0 if x < 0 else one_pound(x - 100) + fifty_pence(x)





def two_pound(x: int) -> int:

    # two_pound 函数实现

    return 0 if x < 0 else two_pound(x - 200) + one_pound(x)





def solution(n: int = 200) -> int:

    # solution 函数实现

    """Returns the number of different ways can n pence be made using any number of

    coins?



    >>> solution(500)

    6295434

    >>> solution(200)

    73682

    >>> solution(50)

    451

    >>> solution(10)

    11

    """

    return two_pound(n)

    # 返回结果





if __name__ == "__main__":

    print(solution(int(input().strip())))

