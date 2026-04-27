# -*- coding: utf-8 -*-
"""
算法实现：组合优化 / laminar_family

本文件实现 laminar_family 相关的算法功能。
"""

from typing import List, Set, Tuple


class LaminarFamily:
    """层状族"""

    def __init__(self):
        self.family: List[Set] = []

    def add_set(self, S: Set) -> bool:
        """
        添加集合到层状族

        返回：是否成功（保持层状性）
        """
        for existing in self.family:
            # 检查不相交和包含关系
            if S and existing:
                if S.intersection(existing) and not (S.issubset(existing) or existing.issubset(S)):
                    return False

        self.family.append(S)
        return True

    def is_laminar(self) -> bool:
        """检查是否是层状族"""
        for i, Si in enumerate(self.family):
            for j, Sj in enumerate(self.family):
                if i != j:
                    inter = Si.intersection(Sj)
                    if inter and not (Si.issubset(Sj) or Sj.issubset(Si)):
                        return False
        return True

    def get_max_sets(self) -> List[Set]:
        """获取极大集合"""
        max_sets = []
        for S in self.family:
            is_maximal = True
            for other in self.family:
                if S != other and other.issubset(S) and len(other) < len(S):
                    is_maximal = False
                    break
            if is_maximal:
                max_sets.append(S)
        return max_sets

    def optimize_with_laminar_constraints(self, weights: List[float],
                                         elements: List[str]) -> Set[str]:
        """
        在层状族约束下优化

        参数：
            weights: 元素权重
            elements: 元素列表

        返回：选中的元素
        """
        n = len(elements)
        element_index = {e: i for i, e in enumerate(elements)}

        # 贪心选择
        selected = set()

        # 按层状结构选择
        for layer_set in self.family:
            layer_elements = [e for e in layer_set if e in element_index]
            layer_weights = [(weights[element_index[e]], e) for e in layer_elements]
            layer_weights.sort(reverse=True)

            # 选择最高的
            if layer_weights:
                selected.add(layer_weights[0][1])

        return selected


def laminar_family_properties():
    """层状族性质"""
    print("=== 层状族性质 ===")
    print()
    print("定义：")
    print("  对于任意 A, B ∈ L")
    print("  要么 A ∩ B = ∅")
    print("  要么 A ⊆ B 或 B ⊆ A")
    print()
    print("例子：")
    print("  {{1,2}, {3}, {1}, {2,3,4}} 不是层状")
    print("  {{1,2,3}, {1}, {2}, {3}} 是层状")
    print()
    print("优化：")
    print("  - 线性规划求解")
    print("  - 贪心近似算法")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 层状族优化测试 ===\n")

    lam = LaminarFamily()

    # 添加集合
    sets = [
        {1, 2, 3},
        {1, 2},
        {3},
        {1},
        {4, 5}
    ]

    print("添加集合：")
    for S in sets:
        success = lam.add_set(S)
        print(f"  {S}: {'成功' if success else '失败'}")

    print(f"\n是层状族: {lam.is_laminar()}")

    # 极大集合
    max_sets = lam.get_max_sets()
    print(f"极大集合: {max_sets}")

    # 优化
    elements = list(range(1, 6))
    weights = [5.0, 3.0, 4.0, 2.0, 1.0]

    result = lam.optimize_with_laminar_constraints(weights, elements)
    print(f"\n权重: {dict(zip(elements, weights))}")
    print(f"优化选择: {result}")

    print()
    laminar_family_properties()

    print()
    print("说明：")
    print("  - 层状族用于约束结构优化")
    print("  - 在森林管理、资源分配中有应用")
    print("  - 可以高效求解线性规划")
