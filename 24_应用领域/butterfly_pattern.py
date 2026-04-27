# -*- coding: utf-8 -*-
"""
算法实现：24_应用领域 / butterfly_pattern

本文件实现 butterfly_pattern 相关的算法功能。
"""

# butterfly_pattern 函数实现
def butterfly_pattern(n: int) -> str:
    """
    Creates a butterfly pattern of size n and returns it as a string.

    >>> print(butterfly_pattern(3))
    *   *
    ** **
    *****
    ** **
    *   *
    >>> print(butterfly_pattern(5))
    *       *
    **     **
    ***   ***
    **** ****
    *********
    **** ****
    ***   ***
    **     **
    *       *
    """
    result = []

    # Upper part
    for i in range(1, n):
    # 遍历循环
        left_stars = "*" * i
        spaces = " " * (2 * (n - i) - 1)
        right_stars = "*" * i
        result.append(left_stars + spaces + right_stars)

    # Middle part
    result.append("*" * (2 * n - 1))

    # Lower part
    for i in range(n - 1, 0, -1):
    # 遍历循环
        left_stars = "*" * i
        spaces = " " * (2 * (n - i) - 1)
        right_stars = "*" * i
        result.append(left_stars + spaces + right_stars)

    return "\n".join(result)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    n = int(input("Enter the size of the butterfly pattern: "))
    print(butterfly_pattern(n))
