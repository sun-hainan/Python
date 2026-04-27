# -*- coding: utf-8 -*-

"""

Project Euler Problem 207



解决 Project Euler 第 207 题的 Python 实现。

https://projecteuler.net/problem=207

"""



import math







# =============================================================================

# Project Euler 问题 207

# =============================================================================

def check_partition_perfect(positive_integer: int) -> bool:

    """



    Check if t = f(positive_integer) = log2(sqrt(4*positive_integer+1)/2 + 1/2) is a

    real number.



    >>> check_partition_perfect(2)

    True



    >>> check_partition_perfect(6)

    False



    """



    exponent = math.log2(math.sqrt(4 * positive_integer + 1) / 2 + 1 / 2)



    return exponent == int(exponent)

    # 返回结果





def solution(max_proportion: float = 1 / 12345) -> int:

    # solution 函数实现

    """

    Find m for which the proportion of perfect partitions to total partitions is lower

    than max_proportion



    >>> solution(1) > 5

    True



    >>> solution(1/2) > 10

    True



    >>> solution(3 / 13) > 185

    True



    """



    total_partitions = 0

    perfect_partitions = 0



    integer = 3

    while True:

    # 条件循环

        partition_candidate = (integer**2 - 1) / 4

        # if candidate is an integer, then there is a partition for k

        if partition_candidate == int(partition_candidate):

            partition_candidate = int(partition_candidate)

            total_partitions += 1

            if check_partition_perfect(partition_candidate):

                perfect_partitions += 1

        if (

            perfect_partitions > 0

            and perfect_partitions / total_partitions < max_proportion

        ):

            return int(partition_candidate)

    # 返回结果

        integer += 1





if __name__ == "__main__":

    print(f"{solution() = }")

