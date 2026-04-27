# -*- coding: utf-8 -*-

"""

算法实现：special_numbers / ugly_numbers



本文件实现 ugly_numbers 相关的算法功能。

"""



# =============================================================================

# 算法模块：ugly_numbers

# =============================================================================

def ugly_numbers(n: int) -> int:

    # ugly_numbers function



    # ugly_numbers function

    """

    Returns the nth ugly number.

    >>> ugly_numbers(100)

    1536

    >>> ugly_numbers(0)

    1

    >>> ugly_numbers(20)

    36

    >>> ugly_numbers(-5)

    1

    >>> ugly_numbers(-5.5)

    Traceback (most recent call last):

        ...

    TypeError: 'float' object cannot be interpreted as an integer

    """

    ugly_nums = [1]



    i2, i3, i5 = 0, 0, 0

    next_2 = ugly_nums[i2] * 2

    next_3 = ugly_nums[i3] * 3

    next_5 = ugly_nums[i5] * 5



    for _ in range(1, n):

        next_num = min(next_2, next_3, next_5)

        ugly_nums.append(next_num)

        if next_num == next_2:

            i2 += 1

            next_2 = ugly_nums[i2] * 2

        if next_num == next_3:

            i3 += 1

            next_3 = ugly_nums[i3] * 3

        if next_num == next_5:

            i5 += 1

            next_5 = ugly_nums[i5] * 5

    return ugly_nums[-1]





if __name__ == "__main__":

    from doctest import testmod



    testmod(verbose=True)

    print(f"{ugly_numbers(200) = }")

