# -*- coding: utf-8 -*-

"""

算法实现：tests / test_greedy_knapsack



本文件实现 test_greedy_knapsack 相关的算法功能。

"""



test_greedy_knapsack.py

"""



import unittest



from greedy_knapsack import Knapsack





class TestGreedyKnapsack(unittest.TestCase):

    def test_sorted(self):

        """

        kp.calc_profit takes the required argument (profit, weight, max_weight)

        and returns whether the answer matches to the expected ones

        """

        profit = [10, 20, 30, 40, 50, 60]

        weight = [2, 4, 6, 8, 10, 12]

        max_weight = 100

        assert Knapsack.calc_profit(profit, weight, max_weight) == 210



    def test_negative_max_weight(self):

        """

        Returns ValueError for any negative max_weight value

        :return: ValueError

        """

        profit = [10, 20, 30, 40, 50, 60]

        weight = [2, 4, 6, 8, 10, 12]

        max_weight = -15

        try:

            kp = Knapsack(profit, weight, max_weight)

            kp.calc_profit(profit, weight, max_weight)

            assert False

        except ValueError:

            pass



    def test_negative_profit_value(self):

        """

        Returns ValueError for any negative profit value in the list

        :return: ValueError

        """

        profit = [10, -20, 30, 40, 50, 60]

        weight = [2, 4, 6, 8, 10, 12]

        max_weight = 15

        try:

            kp = Knapsack(profit, weight, max_weight)

            kp.calc_profit(profit, weight, max_weight)

            assert False

        except ValueError:

            pass



    def test_negative_weight_value(self):

        """

        Returns ValueError for any negative weight value in the list

        :return: ValueError

        """

        profit = [10, 20, 30, 40, 50, 60]

        weight = [2, -4, 6, -8, 10, 12]

        max_weight = 15

        try:

            kp = Knapsack(profit, weight, max_weight)

            kp.calc_profit(profit, weight, max_weight)

            assert False

        except ValueError:

            pass



    def test_null_max_weight(self):

        """

        Returns ValueError for any zero max_weight value

        :return: ValueError

        """

        profit = [10, 20, 30, 40, 50, 60]

        weight = [2, 4, 6, 8, 10, 12]

        max_weight = 0

        try:

            kp = Knapsack(profit, weight, max_weight)

            kp.calc_profit(profit, weight, max_weight)

            assert False

        except ValueError:

            pass



    def test_unequal_list_length(self):

        """

        Returns IndexError if length of lists (profit and weight) are unequal.

        :return: IndexError

        """

        profit = [10, 20, 30, 40, 50]

        weight = [2, 4, 6, 8, 10, 12]

        max_weight = 100

        try:

            kp = Knapsack(profit, weight, max_weight)

            kp.calc_profit(profit, weight, max_weight)

            assert False

        except IndexError:

            pass





if __name__ == "__main__":

    unittest.main()

