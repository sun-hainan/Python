# -*- coding: utf-8 -*-
"""
算法实现：差分隐私 / privacy_budget

本文件实现 privacy_budget 相关的算法功能。
"""

from typing import List, Tuple


class PrivacyBudget:
    """隐私预算管理"""

    def __init__(self, total_epsilon: float):
        """
        参数：
            total_epsilon: 总预算
        """
        self.total_epsilon = total_epsilon
        self.used_epsilon = 0.0
        self.queries = []

    def allocate(self, epsilon: float, description: str = "") -> bool:
        """
        分配预算

        参数：
            epsilon: 请求的预算
            description: 查询描述

        返回：是否成功分配
        """
        if self.used_epsilon + epsilon > self.total_epsilon:
            return False

        self.used_epsilon += epsilon
        self.queries.append({
            'epsilon': epsilon,
            'description': description
        })

        return True

    def remaining(self) -> float:
        """剩余预算"""
        return self.total_epsilon - self.used_epsilon

    def compose_serial(self, queries: List[Tuple[float, str]]) -> float:
        """
        串行组合多个查询

        返回：总消耗预算
        """
        total = 0.0
        results = []

        for epsilon, desc in queries:
            if self.allocate(epsilon, desc):
                results.append(f"  ✓ {desc}: ε={epsilon}")
                total += epsilon
            else:
                results.append(f"  ✗ {desc}: 预算不足")

        return total

    def compose_parallel(self, queries: List[Tuple[float, str]]) -> float:
        """
        并行组合（同一数据集上的多个查询）

        返回：总消耗预算
        """
        if not queries:
            return 0.0

        # 取最大epsilon
        max_epsilon = max(ep for ep, _ in queries)

        # 分配一次
        if self.allocate(max_epsilon, f"并行查询 ({len(queries)} 个)"):
            return max_epsilon
        else:
            return 0.0


class AdaptivePrivacy:
    """自适应隐私分配"""

    def __init__(self, total_epsilon: float):
        self.budget = PrivacyBudget(total_epsilon)
        self.history = []

    def query_with_adaptive_eps(self, sensitivity: float,
                                target_accuracy: float) -> float:
        """
        根据目标精度自适应选择epsilon

        参数：
            sensitivity: 敏感度
            target_accuracy: 目标精度

        返回：选择的epsilon
        """
        # 简化：根据精度计算epsilon
        # 精度越高，需要越大epsilon
        import math

        epsilon = math.log(1 / target_accuracy) / sensitivity

        if self.budget.allocate(epsilon, f"自适应查询 (精度={target_accuracy})"):
            self.history.append({
                'epsilon': epsilon,
                'sensitivity': sensitivity,
                'accuracy': target_accuracy
            })
            return epsilon
        else:
            return 0.0

    def report_statistics(self) -> dict:
        """报告统计"""
        return {
            'total_epsilon': self.budget.total_epsilon,
            'used_epsilon': self.budget.used_epsilon,
            'remaining': self.budget.remaining(),
            'n_queries': len(self.history)
        }


def privacy_accounting_methods():
    """隐私账户方法"""
    print("=== 隐私账户方法 ===")
    print()
    print("1. 简单求和")
    print("   - ε_total = Σ ε_i")
    print("   - 最保守")
    print()
    print("2. RDP (Rényi Differential Privacy)")
    print("   - 更紧的边界")
    print("   - 用于高级组合")
    print()
    print("3. PCD (Privacy Loss Distributions)")
    print("   - 最紧密的边界")
    print("   - 复杂但精确")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 隐私预算分配测试 ===\n")

    total_epsilon = 10.0
    budget = PrivacyBudget(total_epsilon)

    print(f"总预算: ε = {total_epsilon}")
    print()

    # 串行组合
    queries = [
        (1.0, "查询1"),
        (2.0, "查询2"),
        (3.0, "查询3"),
    ]

    total = budget.compose_serial(queries)
    print(f"串行组合消耗: ε = {total:.1f}")
    print(f"剩余预算: ε = {budget.remaining():.1f}")
    print()

    # 自适应
    adaptive = AdaptivePrivacy(5.0)

    accuracies = [0.1, 0.05, 0.01]
    print("自适应查询：")
    for acc in accuracies:
        eps = adaptive.query_with_adaptive_eps(sensitivity=1.0, target_accuracy=acc)
        print(f"  目标精度 {acc}: 选择 ε = {eps:.2f}")

    stats = adaptive.report_statistics()
    print(f"\n统计: 使用了 {stats['used_epsilon']:.2f}/{stats['total_epsilon']} 预算")

    print()
    privacy_accounting_methods()

    print()
    print("说明：")
    print("  - 隐私预算有限，需要谨慎分配")
    print("  - 串行vs并行组合影响总消耗")
    print("  - 自适应方法提高效率")
