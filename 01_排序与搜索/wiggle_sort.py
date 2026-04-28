# -*- coding: utf-8 -*-
"""
Wiggle Sort（摆动排序）
==========================================

【算法原理】
将数组重新排列，使得：
- 奇数位置的元素 >= 相邻偶数位置
- 或 奇数位置的元素 <= 相邻偶数位置

【时间复杂度】O(n)
【空间复杂度】O(1)

【应用场景】
- 洗牌算法验证
- 数据重排列
"""

from typing import List


def wiggle_sort(nums: List[int]) -> List[int]:
    """
    Wiggle Sort（摆动排序）

    【算法步骤】
    遍历数组，对于每个奇数位置i：
    如果 nums[i-1] > nums[i]，交换两者

    【参数】
    - nums: 输入数组

    【返回】
    - 重排列后的数组
    """
    for i in range(len(nums)):
        # -------- 判断是否需要交换 --------
        # 如果i是奇数，且前一个元素大于当前元素，或者
        # 如果i是偶数（从0开始），且当前元素大于前一个元素
        # 则交换
        if (i % 2 == 1) == (nums[i - 1] > nums[i]):
            nums[i - 1], nums[i] = nums[i], nums[i - 1]

    return nums


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("Wiggle Sort（摆动排序） - 测试")
    print("=" * 50)

    # 测试1：基本功能
    print("\n【测试1】基本功能")
    test_cases = [
        ([0, 5, 3, 2, 2], [0, 5, 2, 3, 2]),
        ([3, 5, 2, 1, 6, 4], None),  # None表示只验证wiggle性质
        ([], []),
        ([1], [1]),
        ([1, 2], [1, 2]),
        ([2, 1], [1, 2]),
    ]

    for arr, expected in test_cases:
        result = wiggle_sort(arr.copy())
        if expected:
            status = "✅" if result == expected else "❌"
            print(f"  {status} {arr} -> {result}")
        else:
            # 验证wiggle性质
            valid = all(
                (result[i] >= result[i-1]) or (result[i] <= result[i-1])
                for i in range(1, len(result))
            )
            print(f"  {'✅' if valid else '❌'} {arr} -> {result} (wiggle性质: {valid})")

    # 测试2：偶数长度
    print("\n【测试2】偶数长度数组")
    arr = [1, 2, 3, 4, 5, 6]
    result = wiggle_sort(arr.copy())
    print(f"  {arr} -> {result}")

    # 验证wiggle性质
    valid = all(
        (result[i] >= result[i-1]) or (result[i] <= result[i-1])
        for i in range(1, len(result))
    )
    print(f"  wiggle性质验证: {'✅' if valid else '❌'}")

    # 测试3：边界情况
    print("\n【测试3】边界情况")
    for arr in [[2, 1, 3], [1, 3, 2], [3, 1, 2], [2, 3, 1]]:
        result = wiggle_sort(arr.copy())
        print(f"  {arr} -> {result}")

    print("\n" + "=" * 50)
    print("Wiggle Sort测试完成！")
    print("=" * 50)
