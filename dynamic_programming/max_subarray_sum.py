"""
最大子数组和 (Maximum Subarray Sum / Kadane's Algorithm) - 中文注释版
==========================================

问题定义：
    给定一个数组，找出其中连续子数组的最大和。

经典案例：
    输入: [-2, 1, -3, 4, -1, 2, 1, -5, 4]
    输出: 6（对应子数组 [4, -1, 2, 1]）

算法对比：
    1. 暴力 O(n³)：枚举所有子数组
    2. 前缀和优化 O(n²)：枚举起点 + 线性扫描
    3. Kadane 算法 O(n)：最优解，动态规划思想

Kadane 算法核心思想：
    定义 dp[i] = 以第 i 个元素结尾的最大子数组和

    状态转移：
        dp[i] = max(dp[i-1] + arr[i], arr[i])
        解释：要么把 arr[i] 接在前面的子数组后面，要么从 arr[i] 重新开始

    空间优化：由于 dp[i] 只依赖 dp[i-1]，可以用一个变量代替数组

时间复杂度：O(n)
空间复杂度：O(1)
"""

from collections.abc import Sequence


def max_subarray_sum(
    arr: Sequence[float], allow_empty_subarrays: bool = False
) -> float:
    """
    最大子数组和 - Kadane 算法

    参数:
        arr: 输入数组
        allow_empty_subarrays: 是否允许空子数组（允许则返回 0）

    返回:
        最大子数组和

    示例:
        >>> max_subarray_sum([2, 8, 9])
        19
        >>> max_subarray_sum([0, 0])
        0
        >>> max_subarray_sum([-1.0, 0.0, 1.0])
        1.0
        >>> max_subarray_sum([1, 2, 3, 4, -2])
        10
        >>> max_subarray_sum([-2, 1, -3, 4, -1, 2, 1, -5, 4])
        6
        >>> max_subarray_sum([-2, -3, -1, -4, -6])
        -1
        >>> max_subarray_sum([-2, -3, -1, -4, -6], allow_empty_subarrays=True)
        0
        >>> max_subarray_sum([])
        0
    """
    if not arr:
        return 0

    # 初始化
    max_sum = 0 if allow_empty_subarrays else float("-inf")
    curr_sum = 0.0

    for num in arr:
        # 核心公式：要么接在前面，要么重新开始
        # 如果允许空数组，则可以从 0 开始
        curr_sum = max(0 if allow_empty_subarrays else num, curr_sum + num)
        max_sum = max(max_sum, curr_sum)

    return max_sum


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
    print(f"最大子数组和: {max_subarray_sum(nums)}")  # 6
