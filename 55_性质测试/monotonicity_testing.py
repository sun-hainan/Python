# -*- coding: utf-8 -*-

"""

算法实现：性质测试 / monotonicity_testing



本文件实现 monotonicity_testing 相关的算法功能。

"""



import random

from typing import List





def is_monotonic(f: List[int]) -> bool:

    """检查单调性（暴力）"""

    for i in range(len(f) - 1):

        if f[i] > f[i + 1]:

            return False

    return True





class MonotonicityTester:

    """单调性测试器"""



    def __init__(self, epsilon: float = 0.1):

        """

        参数：

            epsilon: 距离参数

        """

        self.epsilon = epsilon



    def test(self, f: List[int], n_checks: int = None) -> bool:

        """

        测试单调性



        参数：

            f: 函数（数组）

            n_checks: 检查次数



        返回：是否单调

        """

        n = len(f)

        if n_checks is None:

            n_checks = int(1 / self.epsilon)



        n_checks = min(n_checks, n * (n - 1) // 2)



        for _ in range(n_checks):

            i = random.randint(0, n - 2)

            j = random.randint(i + 1, n - 1)



            # 单调性：i < j 则 f(i) <= f(j)

            if f[i] > f[j]:

                return False



        return True



    def distance_to_monotonic(self, f: List[int]) -> float:

        """

        估计到单调函数的距离



        返回：需要修改的元素比例

        """

        n = len(f)

        violations = 0

        samples = 0



        for i in range(n):

            for j in range(i + 1, n):

                if f[i] > f[j]:

                    violations += 1

                samples += 1

                if samples >= 1000:

                    break

            if samples >= 1000:

                break



        return violations / samples if samples > 0 else 0.0





def arrow_test():

    """方向性测试"""

    print("=== 单调性测试复杂度 ===")

    print()

    print("简单测试：O(n)")

    print("采样测试：O(1/ε²)")

    print()

    print("下界：Ω(n)")

    print("  - 必须检查所有位置")

    print()

    print("应用：")

    print("  - 数据库完整性检查")

    print("  - 隐私保护数据分析")

    print("  - 学习理论中的属性测试")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 单调性测试测试 ===\n")



    random.seed(42)



    tester = MonotonicityTester(epsilon=0.1)



    # 测试用例

    monotonic = [1, 2, 3, 4, 5, 5, 6, 7]

    non_monotonic = [1, 3, 2, 4, 5, 5, 6, 7]

    nearly_monotonic = [1, 2, 3, 4, 2, 5, 6, 7]  # 一个违规



    for arr, name in [(monotonic, "单调"), (non_monotonic, "非单调"), (nearly_monotonic, "几乎单调")]:

        result = tester.test(arr, n_checks=20)

        distance = tester.distance_to_monotonic(arr)

        print(f"{name}: {'单调' if result else '非单调'}, 违规比例≈{distance:.2f}")



    print()

    print("复杂度分析：")

    print("  采样复杂度：O(1/ε²)")

    print("  确定性：O(n)")

    print()

    print("理论结果：")

    print("  - Ω(n) 下界")

    print("  - 存在 O(n) 算法")

    print("  - 采样只能达到 O(1/ε²)")



    arrow_test()

