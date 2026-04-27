# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / distribute_coins



本文件实现 distribute_coins 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""





"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""









from dataclasses import dataclass

from typing import NamedTuple





@dataclass



# =============================================================================

# 算法模块：distribute_coins

# =============================================================================

class TreeNode:

    # TreeNode class



    # TreeNode class

    data: int

    left: TreeNode | None = None

    right: TreeNode | None = None





class CoinsDistribResult(NamedTuple):

    # CoinsDistribResult class



    # CoinsDistribResult class

    moves: int

    excess: int





def distribute_coins(root: TreeNode | None) -> int:

    # distribute_coins function



    # distribute_coins function

    """

    >>> distribute_coins(TreeNode(3, TreeNode(0), TreeNode(0)))

    2

    >>> distribute_coins(TreeNode(0, TreeNode(3), TreeNode(0)))

    3

    >>> distribute_coins(TreeNode(0, TreeNode(0), TreeNode(3)))

    3

    >>> distribute_coins(None)

    0

    >>> distribute_coins(TreeNode(0, TreeNode(0), TreeNode(0)))

    Traceback (most recent call last):

     ...

    ValueError: The nodes number should be same as the number of coins

    >>> distribute_coins(TreeNode(0, TreeNode(1), TreeNode(1)))

    Traceback (most recent call last):

     ...

    ValueError: The nodes number should be same as the number of coins

    """



    if root is None:

        return 0



    # Validation

    def count_nodes(node: TreeNode | None) -> int:

    # count_nodes function



    # count_nodes function

        """

        >>> count_nodes(None)

        0

        """

        if node is None:

            return 0



        return count_nodes(node.left) + count_nodes(node.right) + 1



    def count_coins(node: TreeNode | None) -> int:

    # count_coins function



    # count_coins function

        """

        >>> count_coins(None)

        0

        """

        if node is None:

            return 0



        return count_coins(node.left) + count_coins(node.right) + node.data



    if count_nodes(root) != count_coins(root):

        raise ValueError("The nodes number should be same as the number of coins")



    # Main calculation

    def get_distrib(node: TreeNode | None) -> CoinsDistribResult:

    # get_distrib function



    # get_distrib function

        """

        >>> get_distrib(None)

        namedtuple("CoinsDistribResult", "0 2")

        """



        if node is None:

            return CoinsDistribResult(0, 1)



        left_distrib_moves, left_distrib_excess = get_distrib(node.left)

        right_distrib_moves, right_distrib_excess = get_distrib(node.right)



        coins_to_left = 1 - left_distrib_excess

        coins_to_right = 1 - right_distrib_excess



        result_moves = (

            left_distrib_moves

            + right_distrib_moves

            + abs(coins_to_left)

            + abs(coins_to_right)

        )

        result_excess = node.data - coins_to_left - coins_to_right



        return CoinsDistribResult(result_moves, result_excess)



    return get_distrib(root)[0]





if __name__ == "__main__":

    import doctest



    doctest.testmod()

