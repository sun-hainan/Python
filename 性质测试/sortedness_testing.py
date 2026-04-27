# -*- coding: utf-8 -*-
"""
算法实现：性质测试 / sortedness_testing

本文件实现 sortedness_testing 相关的算法功能。
"""

import random
from typing import List


def is_sorted(arr: List[int]) -> bool:
    """检查数组是否已排序"""
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            return False
    return True


class SortednessTester:
    """排序性测试器"""

    def __init__(self, epsilon: float = 0.1):
        """
        参数：
            epsilon: 距离参数
        """
        self.epsilon = epsilon

    def test_sortedness(self, arr: List[int], n_checks: int = None) -> bool:
        """
        测试数组是否排序

        参数：
            arr: 输入数组
            n_checks: 检查次数（默认 O(1/epsilon)）

        返回：是否排序
        """
        n = len(arr)
        if n_checks is None:
            n_checks = int(1 / self.epsilon)

        n_checks = min(n_checks, n - 1)

        for _ in range(n_checks):
            i = random.randint(0, n - 2)
            if arr[i] > arr[i + 1]:
                return False

        return True

    def distance_to_sorted(self, arr: List[int]) -> float:
        """
        估计到排序的距离

        返回：逆序对比例（0到1之间）
        """
        n = len(arr)
        violations = 0
        samples = 0

        for _ in range(min(1000, n)):
            i = random.randint(0, n - 2)
            if arr[i] > arr[i + 1]:
                violations += 1
            samples += 1

        return violations / samples if samples > 0 else 0.0


def binary_search_check(arr: List[int]) -> bool:
    """使用二分搜索检查（确定性的 O(log n)）"""
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            return False
    return True


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 排序性测试测试 ===\n")

    random.seed(42)

    tester = SortednessTester(epsilon=0.1)

    # 测试用例
    sorted_arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    unsorted_arr = [1, 3, 2, 4, 5, 7, 6, 8, 9, 10]
    nearly_sorted = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    # 人为引入错误
    nearly_sorted[5] = 4  # 一个小错误

    print("测试用例：")
    print(f"  已排序: {sorted_arr}")
    print(f"  未排序: {unsorted_arr}")
    print(f"  几乎排序: {nearly_sorted} (一个错误)")
    print()

    for arr, name in [(sorted_arr, "已排序"), (unsorted_arr, "未排序"), (nearly_sorted, "几乎排序")]:
        result = tester.test_sortedness(arr, n_checks=20)
        distance = tester.distance_to_sorted(arr)
        print(f"{name}: {'已排序' if result else '未排序'}, 估计距离={distance:.2f}")

    print()
    print("复杂度分析：")
    print("  随机采样：O(1) 查询，概率误差")
    print("  确定性：O(n) 时间，必须检查所有相邻对")
    print()
    print("应用：")
    print("  - 数据库排序验证")
    print("  - 流数据监控")
    print("  - 外部排序验证")
