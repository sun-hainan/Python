# -*- coding: utf-8 -*-
"""
算法实现：次线性算法 / juntas_test

本文件实现 juntas_test 相关的算法功能。
"""

import random
from typing import List, Set


class JuntasTester:
    """Juntas测试器"""

    def __init__(self, epsilon: float = 0.1):
        """
        参数：
            epsilon: 距离参数
        """
        self.epsilon = epsilon

    def is_k_junta(self, function_table: List[int], k: int) -> bool:
        """
        检查函数是否是k-Junta

        参数：
            function_table: 函数真值表（2^n位）
            k: 阈值

        返回：是否是k-Junta
        """
        n = len(function_table).bit_length() - 1

        # 找到所有"影响"变量
        influential_vars = self._find_influential_variables(function_table, n)

        return len(influential_vars) <= k

    def _find_influential_variables(self, table: List[int], n: int) -> Set[int]:
        """
        找到有影响的变量

        使用采样和比较
        """
        influential = set()
        n_samples = int(1 / (self.epsilon ** 2))

        for var in range(n):
            # 检查这个变量是否真的影响输出
            differences = 0
            samples = 0

            for _ in range(n_samples):
                x = [random.randint(0, 1) for _ in range(n)]

                # 翻转这个变量
                x_flipped = x.copy()
                x_flipped[var] ^= 1

                # 计算索引
                idx = sum(bit << i for i, bit in enumerate(x))
                idx_flipped = sum(bit << i for i, bit in enumerate(x_flipped))

                if table[idx] != table[idx_flipped]:
                    differences += 1
                samples += 1

            # 如果翻转导致输出变化的概率较高，则变量是重要的
            if differences / samples > self.epsilon:
                influential.add(var)

        return influential

    def estimate_k(self, function_table: List[int]) -> int:
        """
        估计函数依赖的变量数

        返回：估计的k值
        """
        n = len(function_table).bit_length() - 1
        influential = self._find_influential_variables(function_table, n)
        return len(influential)


def juntas_algorithm():
    """Juntas算法"""
    print("=== Juntas测试算法 ===")
    print()
    print("朴素算法：")
    print("  - 检查每个变量是否独立")
    print("  - 需要 2^n 查询")
    print()
    print("改进算法：")
    print("  - 使用采样估计影响")
    print("  - O(n / ε²) 查询")
    print()
    print("最优算法：")
    print("  - 达到 Ω(n / ε²) 下界")
    print("  - 使用自适应采样")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Juntas测试测试 ===\n")

    random.seed(42)

    tester = JuntasTester(epsilon=0.1)

    # 测试函数：只依赖于变量0和1
    n = 5
    # function_table[x0,x1,x2,x3,x4] = x0 XOR x1
    def make_table():
        table = []
        for i in range(2 ** n):
            bits = [(i >> j) & 1 for j in range(n)]
            val = bits[0] ^ bits[1]  # 只依赖x0和x1
            table.append(val)
        return table

    function_table = make_table()

    print(f"函数依赖变量: 0, 1 (2-Junta)")
    print()

    # 检查
    is_2_junta = tester.is_k_junta(function_table, k=2)
    is_1_junta = tester.is_k_junta(function_table, k=1)

    print(f"是2-Junta: {'是' if is_2_junta else '否'}")
    print(f"是1-Junta: {'是' if is_1_junta else '否'}")

    # 估计k
    estimated_k = tester.estimate_k(function_table)
    print(f"估计k: {estimated_k}")

    print()
    juntas_algorithm()

    print()
    print("说明：")
    print("  - Juntas测试是性质测试的重要问题")
    print("  - 与学习理论相关")
    print("  - 应用：特征选择、变量重要性")
