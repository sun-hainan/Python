# -*- coding: utf-8 -*-

"""

算法实现：性质测试 / code_property_test



本文件实现 code_property_test 相关的算法功能。

"""



import random

from typing import List, Tuple





class CodePropertyTester:

    """码性质测试器"""



    def __init__(self, n: int, k: int, codewords: List[List[int]]):

        """

        参数：

            n: 码字长度

            k: 信息位数

            codewords: 码字列表

        """

        self.n = n

        self.k = k

        self.codewords = codewords

        self.m = len(codewords)



    def compute_min_distance(self) -> int:

        """

        计算最小距离



        返回：最小汉明距离

        """

        min_dist = self.n + 1



        for i in range(self.m):

            for j in range(i + 1, self.m):

                dist = self._hamming_distance(self.codewords[i],

                                            self.codewords[j])

                min_dist = min(min_dist, dist)



        return min_dist



    def _hamming_distance(self, c1: List[int], c2: List[int]) -> int:

        """计算汉明距离"""

        return sum(b1 != b2 for b1, b2 in zip(c1, c2))



    def test_is_linear(self) -> Tuple[bool, float]:

        """

        测试是否是线性码



        返回：(是否线性, 置信度)

        """

        if not self.codewords:

            return True, 1.0



        n_tests = min(100, len(self.codewords))

        violations = 0



        for _ in range(n_tests):

            # 随机选两个码字

            c1, c2 = random.sample(self.codewords, 2)



            # 计算和

            c_sum = [(a + b) % 2 for a, b in zip(c1, c2)]



            # 检查和是否在码中

            if c_sum not in self.codewords:

                violations += 1



        # 如果有违规，一定不是线性码

        if violations > 0:

            return False, 1.0



        confidence = 1.0 - (1.0 / n_tests) ** n_tests

        return True, confidence



    def estimate_covering_radius(self, n_samples: int = 100) -> float:

        """

        估计覆盖半径



        返回：覆盖半径估计

        """

        max_distance = 0



        # 生成随机向量并找最近码字

        for _ in range(n_samples):

            vec = [random.randint(0, 1) for _ in range(self.n)]



            min_dist = self.n + 1

            for cw in self.codewords:

                dist = self._hamming_distance(vec, cw)

                min_dist = min(min_dist, dist)



            max_distance = max(max_distance, min_dist)



        return max_distance





def code_distance_bounds():

    """码的距离界"""

    print("=== 码的距离界 ===")

    print()

    print("Singleton界：")

    print("  d ≤ n - k + 1")

    print()

    print("Hamming界：")

    print("  2^n ≥ Σ C(n-1, i) for i=0 to t")

    print("  t = (d-1)/2")

    print()

    print("Plotkin界：")

    print("  d ≤ n / (2 * (1 - 1/|A|))")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 纠错码性质测试 ===\n")



    # 创建简单线性码（重复码）

    n = 7

    k = 1



    # 重复码：0000000 和 1111111

    codewords = [

        [0, 0, 0, 0, 0, 0, 0],

        [1, 1, 1, 1, 1, 1, 1]

    ]



    tester = CodePropertyTester(n, k, codewords)



    print(f"码参数: ({n}, {k})")

    print(f"码字: {codewords}")

    print()



    # 计算最小距离

    min_dist = tester.compute_min_distance()

    print(f"最小距离: {min_dist}")

    print(f"期望: {n} (重复码)")

    print()



    # 测试线性

    is_linear, conf = tester.test_is_linear()

    print(f"是线性码: {'是' if is_linear else '否'} (置信度 {conf:.4f})")



    # 估计覆盖半径

    radius = tester.estimate_covering_radius(50)

    print(f"覆盖半径估计: {radius}")



    print()

    code_distance_bounds()



    print()

    print("说明：")

    print("  - 码的性质测试验证码结构")

    print("  - 最小距离决定纠错能力")

    print("  - 覆盖半径决定译码复杂度")

