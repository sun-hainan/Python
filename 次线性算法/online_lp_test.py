# -*- coding: utf-8 -*-
"""
算法实现：次线性算法 / online_lp_test

本文件实现 online_lp_test 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple


class OnlineLPTester:
    """在线LP测试"""

    def __init__(self, n: int):
        """
        参数：
            n: 变量数
        """
        self.n = n
        self.constraints = []
        self.current_solution = None

    def add_constraint(self, a: np.ndarray, b: float) -> bool:
        """
        添加约束并检查

        参数：
            a: 约束系数向量
            b: 约束右端

        返回：是否仍然可行
        """
        self.constraints.append((a, b))

        # 检查可行性
        is_feas = self._check_feasibility()

        return is_feas

    def _check_feasibility(self) -> bool:
        """检查当前约束是否可行"""
        if not self.constraints:
            return True

        # 构建问题
        m = len(self.constraints)
        A = np.array([c[0] for c in self.constraints])
        b = np.array([c[1] for c in self.constraints])

        # 尝试找解：最小化 ||Ax - b||² s.t. x自由
        # 简化：使用最小二乘
        try:
            x = np.linalg.lstsq(A, b, rcond=None)[0]

            # 验证约束
            for i, (a, bi) in enumerate(self.constraints):
                if np.dot(a, x) > bi + 1e-6:
                    return False

            self.current_solution = x
            return True

        except:
            return False

    def get_solution(self) -> np.ndarray:
        """获取当前可行解"""
        if self.current_solution is None:
            self._check_feasibility()

        return self.current_solution if self.current_solution is not None else np.zeros(self.n)


def online_vs_offline():
    """在线 vs 离线"""
    print("=== 在线 vs 离线LP测试 ===")
    print()
    print("离线：")
    print("  - 已知所有约束")
    print("  - 可以整体优化")
    print()
    print("在线：")
    print("  - 约束逐步到达")
    print("  - 每步都要更新")
    print()
    print("复杂度：")
    print("  - 离线：O(n³)")
    print("  - 在线：O(n²) 每步")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 在线线性规划测试 ===\n")

    # 创建测试
    n = 3
    tester = OnlineLPTester(n)

    print(f"变量数: {n}")
    print()

    # 逐步添加约束
    constraints = [
        (np.array([1.0, 0.0, 0.0]), 5.0),   # x1 ≤ 5
        (np.array([0.0, 1.0, 0.0]), 4.0),   # x2 ≤ 4
        (np.array([0.0, 0.0, 1.0]), 3.0),   # x3 ≤ 3
    ]

    for i, (a, b) in enumerate(constraints):
        is_feas = tester.add_constraint(a, b)
        print(f"约束 {i+1}: {'可行' if is_feas else '不可行'}")

    print()
    solution = tester.get_solution()
    print(f"可行解: {solution}")

    print()
    online_vs_offline()

    print()
    print("说明：")
    print("  - 在线测试用于流数据")
    print("  - 每步需要高效更新")
    print("  - 在网络路由、调度中有应用")
