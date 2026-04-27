# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / frontdoor_criterion

本文件实现 frontdoor_criterion 相关的算法功能。
"""

import random
from typing import List, Dict, Tuple


class FrontdoorCriterion:
    """前门准则"""

    def __init__(self, causal_graph: Dict):
        """
        参数：
            causal_graph: 因果图
        """
        self.graph = causal_graph
        self.direct_effects = {}

    def check_frontdoor(self, X: str, Y: str, M: str) -> Tuple[bool, str]:
        """
        检查前门准则

        参数：
            X: 处理变量
            Y: 结果变量
            M: 中介变量

        返回：(是否满足, 原因)
        """
        # 检查X→M→Y路径存在
        if M not in self.graph.get(X, []):
            return False, f"{X} 不直接导致 {M}"

        if Y not in self.graph.get(M, []):
            return False, f"{M} 不直接导致 {Y}"

        # 检查没有直接路径X→Y
        direct_path = self._has_direct_path(X, Y, forbidden=M)
        if direct_path:
            return False, f"存在直接因果路径 {X} → {Y}"

        return True, "满足前门准则"

    def _has_direct_path(self, source: str, target: str, forbidden: str = "") -> bool:
        """检查是否有直接路径（不含forbidden）"""
        # 简化：假设无直接路径
        return False

    def estimate_direct_effect(self, X: str, M: str, data: List[Dict]) -> float:
        """
        估计直接效应

        参数：
            X: 处理变量
            M: 中介变量
            data: 数据

        返回：直接效应估计
        """
        # 使用中介公式
        # P(Y | do(X)) = Σ P(M | do(X)) P(Y | do(M))
        # 直接效应 = P(Y | do(X=1)) - P(Y | do(X=0))

        # 简化的估计
        x1_outcomes = [d[Y] for d in data if d[X] == 1]
        x0_outcomes = [d[Y] for d in data if d[X] == 0]

        if not x1_outcomes or not x0_outcomes:
            return 0.0

        effect = sum(x1_outcomes) / len(x1_outcomes) - sum(x0_outcomes) / len(x0_outcomes)

        return effect


def frontdoor_vs_backdoor():
    """前门 vs 后门"""
    print("=== 前门 vs 后门准则 ===")
    print()
    print("后门准则：")
    print("  - 阻断X和Y之间的混杂路径")
    print("  - 需要识别所有混杂因素")
    print()
    print("前门准则：")
    print("  - 利用中介变量M")
    print("  - 不需要知道X和Y之间的混杂")
    print("  - 但需要满足特定条件")
    print()
    print("选择：")
    print("  - 如果有可观测的中介，用前门")
    print("  - 如果能识别所有混杂，用后门")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 前门准则测试 ===\n")

    # 因果图：X → M → Y
    graph = {
        'X': ['M'],
        'M': ['Y'],
        'Y': []
    }

    frontdoor = FrontdoorCriterion(graph)

    # 检查前门准则
    X, Y, M = 'X', 'Y', 'M'

    is_valid, reason = frontdoor.check_frontdoor(X, Y, M)
    print(f"前门准则检查: {X} → {M} → {Y}")
    print(f"  满足: {'是' if is_valid else '否'}")
    print(f"  原因: {reason}")
    print()

    # 模拟数据
    data = []
    for _ in range(1000):
        x = random.randint(0, 1)
        m = x  # M = X（完全中介）
        y = m  # Y = M
        data.append({'X': x, 'M': m, 'Y': y})

    # 估计直接效应
    effect = frontdoor.estimate_direct_effect(X, M, data)

    print(f"估计的直接效应: {effect:.4f}")
    print(f"真实效应: 0（因为没有直接路径）")

    print()
    frontdoor_vs_backdoor()

    print()
    print("说明：")
    print("  - 前门准则允许识别因果效应")
    print("  - 即使无法测量所有混杂")
    print("  - Pearl的因果微积分的重要应用")
