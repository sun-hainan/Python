# -*- coding: utf-8 -*-

"""

算法实现：tests / test_knapsack



本文件实现 test_knapsack 相关的算法功能。

"""



import unittest



from knapsack import knapsack as k





class Test(unittest.TestCase):

    def test_base_case(self):

        """

        test for the base case

        """

        cap = 0

        val = [0]

        w = [0]

        c = len(val)

        assert k.knapsack(cap, w, val, c) == 0



        val = [60]

        w = [10]

        c = len(val)

        assert k.knapsack(cap, w, val, c) == 0



    def test_easy_case(self):

        """

        test for the easy case

        """

        cap = 3

        val = [1, 2, 3]

        w = [3, 2, 1]

        c = len(val)

        assert k.knapsack(cap, w, val, c) == 5



    def test_knapsack(self):

        """

        test for the knapsack

        """

        cap = 50

        val = [60, 100, 120]

        w = [10, 20, 30]

        c = len(val)

        assert k.knapsack(cap, w, val, c) == 220



    def test_knapsack_repetition(self):

        """

        test for the knapsack repetition

        """

        cap = 50

        val = [60, 100, 120]

        w = [10, 20, 30]

        c = len(val)

        assert k.knapsack(cap, w, val, c, True) == 300





if __name__ == "__main__":

    unittest.main()

