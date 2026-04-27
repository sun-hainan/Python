# -*- coding: utf-8 -*-
"""
算法实现：可验证计算 / linear_pcpcs

本文件实现 linear_pcpcs 相关的算法功能。
"""

import random
from typing import List


class LinearPCP:
    """线性PCP系统"""

    def __init__(self, n_variables: int, constraints: List):
        """
        参数：
            n_variables: 变量数
            constraints: 线性约束列表
        """
        self.n = n_variables
        self.constraints = constraints

    def create_proof(self, assignment: List[int]) -> dict:
        """
        创建证明

        参数：
            assignment: 变量的赋值

        返回：证明（满足约束的赋值）
        """
        # 验证赋值满足所有约束
        for a, b, c in self.constraints:
            if a * assignment[0] + b * assignment[1] != c:
                return {'valid': False}

        return {
            'valid': True,
            'assignment': assignment
        }

    def verify(self, proof: dict, queries: List[int]) -> bool:
        """
        验证证明（抽查）

        参数：
            proof: 证明
            queries: 要抽查的变量索引

        返回：是否通过
        """
        if not proof.get('valid', False):
            return False

        # 模拟抽查
        assignment = proof['assignment']
        for q in queries:
            if q >= len(assignment):
                return False

        return True


class LinearPCPVerification:
    """线性PCP验证"""

    def __init__(self, field_size: int = 97):
        self.field_size = field_size

    def random_query(self, n_vars: int, n_queries: int) -> List[int]:
        """生成随机查询"""
        return random.sample(range(n_vars), min(n_queries, n_vars))

    def verify_batch(self, proofs: List[dict], queries: List[int]) -> bool:
        """批量验证"""
        for proof in proofs:
            if not self.verify(proof, queries):
                return False
        return True


def algebraic_equations_example():
    """代数方程组示例"""
    print("=== 线性PCP示例 ===\n")

    # 简单方程组: 2x + 3y = 13, x + y = 5
    constraints = [
        (2, 3, 13),  # 2x + 3y = 13
        (1, 1, 5),    # x + y = 5
    ]

    # 解：x=2, y=3
    solution = [2, 3]

    pcq = LinearPCP(n_variables=2, constraints=constraints)
    proof = pcq.create_proof(solution)

    print(f"方程组: 2x + 3y = 13, x + y = 5")
    print(f"解: x={solution[0]}, y={solution[1]}")
    print()

    # 验证
    queries = [0, 1]  # 抽查两个变量
    is_valid = pcq.verify(proof, queries)

    print(f"验证结果: {'✅ 通过' if is_valid else '❌ 失败'}")
    print(f"抽查变量: {queries}")


def linear_vs_binary():
    """线性PCP vs 二进制PCP"""
    print()
    print("=== 线性PCP vs 二进制PCP ===")
    print()
    print("线性PCP：")
    print("  - 变量在域Fq上")
    print("  - 约束是线性方程")
    print("  - 适合算术电路")
    print()
    print("二进制PCP：")
    print("  - 变量是比特(0/1)")
    print("  - 约束是位运算")
    print("  - 适合布尔电路")


def complexity():
    """复杂度分析"""
    print()
    print("=== 复杂度 ===")
    print()
    print("线性PCP参数：")
    print("  - n: 变量数")
    print("  - m: 约束数")
    print("  - q: 查询数")
    print()
    print("验证复杂度：O(q)")
    print("证明复杂度：O(m)")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    random.seed(42)

    algebraic_equations_example()
    linear_vs_binary()
    complexity()

    print("\n说明：")
    print("  - 线性PCP是SNARK的基础")
    print("  - Groth16使用线性PCP")
    print("  - 配对检查验证等式")
