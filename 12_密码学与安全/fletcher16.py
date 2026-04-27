# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / fletcher16



本文件实现 fletcher16 相关的算法功能。

"""



# fletcher16 函数实现

def fletcher16(text: str) -> int:

    """

    Loop through every character in the data and add to two sums.



    >>> fletcher16('hello world')

    6752

    >>> fletcher16('onethousandfourhundredthirtyfour')

    28347

    >>> fletcher16('The quick brown fox jumps over the lazy dog.')

    5655

    """

    data = bytes(text, "ascii")

    sum1 = 0

    sum2 = 0

    for character in data:

    # 遍历循环

        sum1 = (sum1 + character) % 255

        sum2 = (sum1 + sum2) % 255

    return (sum2 << 8) | sum1

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

