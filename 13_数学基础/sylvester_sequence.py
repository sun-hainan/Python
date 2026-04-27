# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / sylvester_sequence

本文件实现 sylvester_sequence 相关的算法功能。
"""

# =============================================================================
# 算法模块：sylvester
# =============================================================================
def sylvester(number: int) -> int:
    # sylvester function

    # sylvester function
    """
    :param number: nth number to calculate in the sequence
    :return: the nth number in Sylvester's sequence

    >>> sylvester(8)
    113423713055421844361000443

    >>> sylvester(-1)
    Traceback (most recent call last):
        ...
    ValueError: The input value of [n=-1] has to be > 0

    >>> sylvester(8.0)
    Traceback (most recent call last):
        ...
    AssertionError: The input value of [n=8.0] is not an integer
    """
    assert isinstance(number, int), f"The input value of [n={number}] is not an integer"

    if number == 1:
        return 2
    elif number < 1:
        msg = f"The input value of [n={number}] has to be > 0"
        raise ValueError(msg)
    else:
        num = sylvester(number - 1)
        lower = num - 1
        upper = num
        return lower * upper + 1


if __name__ == "__main__":
    print(f"The 8th number in Sylvester's sequence: {sylvester(8)}")
