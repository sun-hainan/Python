# -*- coding: utf-8 -*-

"""

算法实现：02_数据结构 / monotonic_array



本文件实现 monotonic_array 相关的算法功能。

"""



# https://leetcode.com/problems/monotonic-array/



# =============================================================================

# 算法模块：is_monotonic

# =============================================================================

"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""



def is_monotonic(nums: list[int]) -> bool:

    # is_monotonic function



    # is_monotonic function

    """

    Check if a list is monotonic.



    >>> is_monotonic([1, 2, 2, 3])

    True

    >>> is_monotonic([6, 5, 4, 4])

    True

    >>> is_monotonic([1, 3, 2])

    False

    >>> is_monotonic([1,2,3,4,5,6,5])

    False

    >>> is_monotonic([-3,-2,-1])

    True

    >>> is_monotonic([-5,-6,-7])

    True

    >>> is_monotonic([0,0,0])

    True

    >>> is_monotonic([-100,0,100])

    True

    """



    return all(nums[i] <= nums[i + 1] for i in range(len(nums) - 1)) or all(

        nums[i] >= nums[i + 1] for i in range(len(nums) - 1)

    )





# Test the function with your examples

if __name__ == "__main__":

    # Test the function with your examples

    print(is_monotonic([1, 2, 2, 3]))  # Output: True

    print(is_monotonic([6, 5, 4, 4]))  # Output: True

    print(is_monotonic([1, 3, 2]))  # Output: False



    import doctest



    doctest.testmod()

