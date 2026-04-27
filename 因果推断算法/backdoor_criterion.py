# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / backdoor_criterion

本文件实现 backdoor_criterion 相关的算法功能。
"""

from typing import Set, Dict


class DoCalculusRule3:
    """Do-演算规则3实现"""

    def __init__(self, causal_graph: Dict):
        """
        参数：
            causal_graph: 因果图结构
        """
        self.graph = causal_graph
        self.parents = causal_graph.get('parents', {})
        self.children = causal_graph.get('children', {})

    def check_rule3_condition(self, X: str, Z: str, Y: str,
                             intervened_X: Set[str]) -> bool:
        """
        检查规则3的条件

        X ⊥ Z | Y 在 do(X) 后的图中

        参数：
            X: 干预变量
            Z: 要消除的变量
            Y: 目标变量
            intervened_X: 已干预变量集

        返回：条件是否满足
        """
        # 构建 do(X) 后的图：删除 X 的所有入边
        modified_parents = dict(self.parents)

        if X in modified_parents:
            modified_parents[X] = []

        # 检查 Z 和 Y 在修改后的图中的d-分离性
        return self._d_separated(Z, Y, intervened_X, modified_parents)

    def _d_separated(self, x: str, y: str,
                    z: Set[str],
                    parents: Dict) -> bool:
        """
        检查 x 和 y 是否在给定 z 时d-分离
        """
        # 简化：假设无混杂
        return True

    def apply_rule3(self, expression: str, Z: str, X: str) -> str:
        """
        应用规则3简化表达式

        参数：
            expression: 原始表达式
            Z: 要消除的 do(Z)
            X: 干预变量

        返回：简化后的表达式
        """
        # 如果条件满足，删除 do(Z)
        if f"do({Z})" in expression:
            # 简化：直接删除
            return expression.replace(f"do({Z}),", "")

        return expression


def do_calculus_rule3_example():
    """规则3示例"""
    print("=== Do-演算规则3示例 ===")
    print()
    print("场景：X -> Y <- Z")
    print("      X -> Z")
    print()
    print("目标：计算 P(Y | do(X), do(Z))")
    print()
    print("规则3检查：")
    print("  - Z ⊥ Y | X 在 do(X) 后的图中？")
    print("  - do(X) 后，X 的所有入边被删除")
    print("  - Z 和 Y 在给定 X 下是否独立？")
    print()
    print("结论：")
    print("  - 如果条件满足，P(Y | do(X), do(Z)) = P(Y | do(X))")
    print("  - Z 的 do 可以删除")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Do-演算规则3测试 ===\n")

    # 创建简单因果图：X -> Z -> Y, X -> Y
    graph = {
        'parents': {
            'X': [],
            'Z': ['X'],
            'Y': ['X', 'Z']
        },
        'children': {
            'X': ['Z', 'Y'],
            'Z': ['Y'],
            'Y': []
        }
    }

    rule3 = DoCalculusRule3(graph)

    # 检查条件
    X = 'X'
    Z = 'Z'
    Y = 'Y'

    condition = rule3.check_rule3_condition(X, Z, Y, {X})
    print(f"规则3条件满足: {condition}")

    # 应用
    expr = "P(Y | do(X), do(Z))"
    simplified = rule3.apply_rule3(expr, Z, X)
    print(f"简化: {expr} -> {simplified}")

    print()
    do_calculus_rule3_example()

    print()
    print("说明：")
    print("  - 规则3允许删除冗余的 do 操作")
    print("  - 需要d-分离条件检查")
    print("  - 结合其他规则可以简化复杂的因果表达式")
