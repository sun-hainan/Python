# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / linear_congruential_generator



本文件实现 linear_congruential_generator 相关的算法功能。

"""



__author__ = "Tobias Carryer"



from time import time





class LinearCongruentialGenerator:

    """

    A pseudorandom number generator.

    """



    # The default value for **seed** is the result of a function call, which is not

    # normally recommended and causes ruff to raise a B008 error. However, in this case,

    # it is acceptable because `LinearCongruentialGenerator.__init__()` will only be

    # called once per instance and it ensures that each instance will generate a unique

    # sequence of numbers.



    def __init__(self, multiplier, increment, modulo, seed=int(time())):  # noqa: B008

        """

        These parameters are saved and used when nextNumber() is called.



        modulo is the largest number that can be generated (exclusive). The most

        efficient values are powers of 2. 2^32 is a common value.

        """

        self.multiplier = multiplier

        self.increment = increment

        self.modulo = modulo

        self.seed = seed





# next_number 函数实现

    def next_number(self):

        """

        The smallest number that can be generated is zero.

        The largest number that can be generated is modulo-1. modulo is set in the

        constructor.

        """

        self.seed = (self.multiplier * self.seed + self.increment) % self.modulo

        return self.seed

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    # Show the LCG in action.

    lcg = LinearCongruentialGenerator(1664525, 1013904223, 2 << 31)

    while True:

    # 条件循环

        print(lcg.next_number())

