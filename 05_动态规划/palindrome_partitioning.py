# -*- coding: utf-8 -*-
"""
算法实现：05_动态规划 / palindrome_partitioning

本文件实现 palindrome_partitioning 相关的算法功能。
"""

def find_minimum_partitions(string: str) -> int:
    # find_minimum_partitions function

    # find_minimum_partitions function
    # find_minimum_partitions 函数实现
    """
    Returns the minimum cuts needed for a palindrome partitioning of string

    >>> find_minimum_partitions("aab")
    1
    >>> find_minimum_partitions("aaa")
    0
    >>> find_minimum_partitions("ababbbabbababa")
    3
    """
    length = len(string)
    cut = [0] * length
    is_palindromic = [[False for i in range(length)] for j in range(length)]
    for i, c in enumerate(string):
        mincut = i
        for j in range(i + 1):
            if c == string[j] and (i - j < 2 or is_palindromic[j + 1][i - 1]):
                is_palindromic[j][i] = True
                mincut = min(mincut, 0 if j == 0 else (cut[j - 1] + 1))
        cut[i] = mincut
    return cut[length - 1]


if __name__ == "__main__":
    s = input("Enter the string: ").strip()
    ans = find_minimum_partitions(s)
    print(f"Minimum number of partitions required for the '{s}' is {ans}")
