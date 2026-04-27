# -*- coding: utf-8 -*-
"""
算法实现：可验证计算 / probabilistically_checkable

本文件实现 probabilistically_checkable 相关的算法功能。
"""

import random
from typing import List, Tuple


class PCPVerifier:
    """PCP验证者"""

    def __init__(self, epsilon: float = 0.1, delta: float = 0.1):
        """
        参数：
            epsilon: 错误概率容限
            delta: 查询次数参数
        """
        self.epsilon = epsilon
        self.delta = delta
        self.num_queries = int(1 / epsilon)

    def verify(self, proof: List[int], oracle_access: bool = True) -> bool:
        """
        验证证明

        参数：
            proof: 证明（长二进制串）
            oracle_access: 是否可以随机访问（PCP模型）

        返回：接受/拒绝
        """
        if oracle_access:
            # PCP查询模式：随机查询几位
            query_indices = random.sample(range(len(proof)),
                                       min(self.num_queries, len(proof)))
            queried_bits = [proof[i] for i in query_indices]

            # 模拟验证（这里用简化版）
            return self._check(queried_bits)
        else:
            # 普通NP验证
            return self._check(proof)

    def _check(self, bits: List[int]) -> bool:
        """检查查询到的位"""
        # 简化：只要有一位是1就接受
        return any(b == 1 for b in bits)


class BinaryCSP:
    """二元约束满足问题（PCP的经典应用）"""

    def __init__(self, n_vars: int, constraints: List[Tuple]):
        """
        参数：
            n_vars: 变量数
            constraints: 约束列表 [(var1, var2, forbidden_pair), ...]
        """
        self.n_vars = n_vars
        self.constraints = constraints

    def random_assignment(self) -> List[int]:
        """随机赋值"""
        return [random.randint(0, 1) for _ in range(self.n_vars)]

    def is_satisfiable(self, assignment: List[int]) -> bool:
        """检查是否满足所有约束"""
        for v1, v2, forbidden in self.constraints:
            if assignment[v1] == assignment[v2] == forbidden:
                return False
        return True

    def pcp_verify(self, proof: List[int], iterations: int = 100) -> bool:
        """
        用PCP方式验证（不需要找赋值）

        模拟：如果proof对应一个可满足赋值，
        高概率接受；如果不可满足，高概率拒绝
        """
        verifier = PCPVerifier(epsilon=0.1)
        accept_count = 0

        for _ in range(iterations):
            # 模拟：查询proof的几位
            # 这里假设proof就是真实赋值
            if verifier.verify(proof, oracle_access=True):
                accept_count += 1

        # 如果大部分都接受，说明可满足
        return accept_count > iterations * 0.7


def PCP_theorem_statement():
    """PCP定理"""
    print("=== PCP定理 ===")
    print()
    print("PCP定理（形式化表述）：")
    print()
    print("NP = PCP(log n, O(1))")
    print()
    print("含义：")
    print("  任何NP问题可以用'概率可检验证明'验证")
    print("  - 验证者只读O(log n)个随机位")
    print("  - 只查询O(1)个证明位")
    print()
    print("推论：")
    print("  - 近似算法与PCP定理密切相关")
    print("  - MAX-3SAT的NP-hard近似比是7/8")


def hardness_of_approximation():
    """近似硬度"""
    print()
    print("=== 近似硬度 ===")
    print()
    print("PCP定理导致了若干重要 hardness 结果：")
    print()
    print("  - Vertex Cover: 难以近似到 1.36 倍以内")
    print("  - MAX-3SAT: 难以近似到 7/8 倍以内")
    print("  - Set Cover: 难以近似到 (1-o(1)) * log n 倍以内")
    print("  - Graph Coloring: 难以近似到 n^{1/3}")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== PCP概率可检验证明测试 ===\n")

    random.seed(42)

    # 创建简单的二元CSP
    n_vars = 10
    constraints = [
        (0, 1, 1),  # var0和var1不能同时为1
        (1, 2, 0),  # var1和var2不能同时为0
        (2, 3, 1),  # ...
    ]

    csp = BinaryCSP(n_vars, constraints)

    # 找一个可满足赋值
    assignment = csp.random_assignment()
    print(f"随机赋值: {assignment[:5]}...")

    # 验证
    is_sat = csp.is_satisfiable(assignment)
    print(f"可满足: {is_sat}")

    print()
    PCP_theorem_statement()
    hardness_of_approximation()

    print("\n说明：")
    print("  - PCP定理是理论计算机科学的里程碑")
    print("  - 连接了计算复杂性、编码理论和组合学")
    print("  - 对近似算法的设计有深刻指导意义")
