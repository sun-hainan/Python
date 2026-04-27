# -*- coding: utf-8 -*-
"""
算法实现：03_字符串算法 / prefix_function

本文件实现 prefix_function 相关的算法功能。
"""

def prefix_function(input_string: str) -> list:
    # prefix_function function

    # prefix_function function
    # prefix_function 函数实现
    """
    For the given string this function computes value for each index(i),
    which represents the longest coincidence of prefix and suffix
    for given substring (input_str[0...i])

    For the value of the first element the algorithm always returns 0

    >>> prefix_function("aabcdaabc")
    [0, 1, 0, 0, 0, 1, 2, 3, 4]
    >>> prefix_function("asdasdad")
    [0, 0, 0, 1, 2, 3, 4, 0]
    """

    # list for the result values
    prefix_result = [0] * len(input_string)

    for i in range(1, len(input_string)):
        # use last results for better performance - dynamic programming
        j = prefix_result[i - 1]
        while j > 0 and input_string[i] != input_string[j]:
            j = prefix_result[j - 1]

        if input_string[i] == input_string[j]:
            j += 1
        prefix_result[i] = j

    return prefix_result


def longest_prefix(input_str: str) -> int:
    # longest_prefix function

    # longest_prefix function
    # longest_prefix 函数实现
    """
    Prefix-function use case
    Finding longest prefix which is suffix as well

    >>> longest_prefix("aabcdaabc")
    4
    >>> longest_prefix("asdasdad")
    4
    >>> longest_prefix("abcab")
    2
    """

    # just returning maximum value of the array gives us answer
    return max(prefix_function(input_str))


if __name__ == "__main__":
    import doctest

    doctest.testmod()
