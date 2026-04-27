# -*- coding: utf-8 -*-

"""

算法实现：DP / 01_Fibonacci



本文件实现 01_Fibonacci 相关的算法功能。

"""



class Fibonacci:

    """

    斐波那契数列计算器(缓存优化)

    """

    def __init__(self):

        self.cache = [0, 1]

    

    def get_nth(self, n):

        while len(self.cache) <= n:

            self.cache.append(self.cache[-1] + self.cache[-2])

        return self.cache[n]

    

    def get_sequence(self, n):

        self.get_nth(n - 1)

        return self.cache[:n]





if __name__ == "__main__":

    # 测试: get_sequence

    result = get_sequence()

    print(result)

