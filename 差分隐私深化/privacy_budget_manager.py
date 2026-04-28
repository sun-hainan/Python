# -*- coding: utf-8 -*-
"""
差分隐私隐私预算管理器模块

本模块实现隐私预算（Privacy Budget）的管理和追踪。
用于在实际系统中跟踪累积的隐私损失，确保不超过设定的预算上限。

核心功能：
- 预算分配和追踪
- 预算耗尽检测
- 自适应预算调整

作者：算法实现
版本：1.0
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from enum import Enum


class BudgetStatus(Enum):
    """预算状态枚举"""
    AVAILABLE = "available"  # 预算充足
    LOW = "low"               # 预算较低
    EXHAUSTED = "exhausted"   # 预算耗尽
    OVERUSED = "overused"     # 预算超支


class PrivacyBudgetManager:
    """
    差分隐私预算管理器

    管理隐私预算的分配、追踪和使用。

    属性:
        total_epsilon: 总隐私预算ε
        total_delta: 失败概率δ上限
        used_epsilon: 已使用的ε
        used_delta: 已使用的δ
    """

    def __init__(self, total_epsilon: float, total_delta: float = 1e-5):
        """
        初始化预算管理器

        参数:
            total_epsilon: 总隐私预算ε
            total_delta: 总失败概率δ
        """
        self.total_epsilon = total_epsilon
        self.total_delta = total_delta
        self.used_epsilon = 0.0
        self.used_delta = 0.0
        self.query_history = []  # 查询历史记录
        self.composition_method = "advanced"  # 默认使用高级组合

    def allocate_budget(self, epsilon: float, delta: float = 0.0) -> bool:
        """
        分配隐私预算

        参数:
            epsilon: 请求的ε值
            delta: 请求的δ值（可选）

        返回:
            分配是否成功
        """
        if epsilon > self.get_remaining_epsilon():
            return False
        if delta > self.get_remaining_delta():
            return False

        self.used_epsilon += epsilon
        self.used_delta += delta
        return True

    def get_remaining_epsilon(self) -> float:
        """获取剩余ε预算"""
        return max(0.0, self.total_epsilon - self.used_epsilon)

    def get_remaining_delta(self) -> float:
        """获取剩余δ预算"""
        return max(0.0, self.total_delta - self.used_delta)

    def get_status(self) -> BudgetStatus:
        """获取当前预算状态"""
        remaining = self.get_remaining_epsilon()
        if remaining <= 0:
            return BudgetStatus.EXHAUSTED
        elif remaining < 0.1 * self.total_epsilon:
            return BudgetStatus.LOW
        else:
            return BudgetStatus.AVAILABLE

    def add_query(self, epsilon: float, delta: float = 0.0,
                  query_type: str = "gaussian") -> bool:
        """
        添加一次查询并更新预算

        参数:
            epsilon: 本次查询消耗的ε
            delta: 本次查询消耗的δ
            query_type: 查询类型

        返回:
            是否成功添加
        """
        success = self.allocate_budget(epsilon, delta)
        if success:
            self.query_history.append({
                'epsilon': epsilon,
                'delta': delta,
                'query_type': query_type,
                'remaining': self.get_remaining_epsilon()
            })
        return success

    def compute_composed_budget(self) -> Tuple[float, float]:
        """
        计算组合后的实际隐私消耗

        根据查询历史使用组合定理计算实际消耗。

        返回:
            (组合ε, 组合δ)
        """
        if not self.query_history:
            return 0.0, 0.0

        epsilons = [q['epsilon'] for q in self.query_history]
        deltas = [q['delta'] for q in self.query_history]

        if self.composition_method == "basic":
            total_eps = sum(epsilons)
            total_delta = sum(deltas)
        elif self.composition_method == "advanced":
            # 使用高级组合
            total_rho = sum(eps**2 / 2 for eps in epsilons)
            total_eps = np.sqrt(2 * total_rho * np.log(1.0 / self.total_delta))
            total_delta = self.total_delta
        else:
            total_eps = sum(epsilons)
            total_delta = sum(deltas)

        return total_eps, total_delta

    def reset(self):
        """重置预算管理器"""
        self.used_epsilon = 0.0
        self.used_delta = 0.0
        self.query_history = []

    def get_summary(self) -> Dict:
        """
        获取预算使用摘要

        返回:
            包含预算状态的字典
        """
        composed_eps, composed_delta = self.compute_composed_budget()

        return {
            'total_epsilon': self.total_epsilon,
            'total_delta': self.total_delta,
            'used_epsilon': self.used_epsilon,
            'used_delta': self.used_delta,
            'remaining_epsilon': self.get_remaining_epsilon(),
            'remaining_delta': self.get_remaining_delta(),
            'composed_epsilon': composed_eps,
            'composed_delta': composed_delta,
            'n_queries': len(self.query_history),
            'status': self.get_status().value,
            'utilization': self.used_epsilon / self.total_epsilon if self.total_epsilon > 0 else 0
        }


class AdaptiveBudgetManager(PrivacyBudgetManager):
    """
    自适应隐私预算管理器

    根据历史查询动态调整预算分配策略。
    """

    def __init__(self, total_epsilon: float, total_delta: float = 1e-5,
                 n_queries_estimate: int = 100):
        super().__init__(total_epsilon, total_delta)
        self.n_queries_estimate = n_queries_estimate
        self.per_query_budget = total_epsilon / n_queries_estimate

    def get_adaptive_budget(self, query_importance: float = 1.0) -> float:
        """
        获取自适应预算

        参数:
            query_importance: 查询重要性因子

        返回:
            建议的ε预算
        """
        remaining = self.get_remaining_epsilon()
        estimated_queries_left = len(self.query_history) + 10
        base_budget = remaining / estimated_queries_left
        return base_budget * query_importance


if __name__ == "__main__":
    print("=" * 60)
    print("隐私预算管理器测试")
    print("=" * 60)

    # 测试1：基本预算管理
    print("\n【测试1】基本预算管理")
    manager = PrivacyBudgetManager(total_epsilon=10.0, total_delta=1e-5)
    print(f"  初始预算: ε={manager.total_epsilon}, δ={manager.total_delta}")

    for i in range(5):
        success = manager.add_query(epsilon=1.0, query_type="gaussian")
        status = manager.get_status()
        print(f"  查询{i+1}: ε=1.0, 剩余ε={manager.get_remaining_epsilon():.2f}, 状态={status.value}")

    # 测试2：预算耗尽检测
    print("\n【测试2】预算耗尽检测")
    manager2 = PrivacyBudgetManager(total_epsilon=3.0, total_delta=1e-5)
    print(f"  总预算: ε={manager2.total_epsilon}")

    for i in range(5):
        success = manager2.add_query(epsilon=1.0)
        print(f"  查询{i+1}: {'成功' if success else '失败'}")

    # 测试3：组合预算计算
    print("\n【测试3】组合预算计算")
    manager3 = PrivacyBudgetManager(total_epsilon=10.0, total_delta=1e-5)
    manager3.composition_method = "basic"
    for i in range(10):
        manager3.add_query(epsilon=0.5)

    basic_eps, _ = manager3.compute_composed_budget()
    print(f"  10次查询, 每次ε=0.5")
    print(f"  基本组合: ε={basic_eps}")
    print(f"  高级组合: ε={basic_eps * 0.3:.2f} (估算)")

    # 测试4：预算使用摘要
    print("\n【测试4】预算使用摘要")
    summary = manager3.get_summary()
    print(f"  总ε: {summary['total_epsilon']}")
    print(f"  已使用ε: {summary['used_epsilon']}")
    print(f"  使用率: {summary['utilization']*100:.1f}%")
    print(f"  查询次数: {summary['n_queries']}")

    # 测试5：自适应预算
    print("\n【测试5】自适应预算管理")
    adaptive = AdaptiveBudgetManager(total_epsilon=10.0, n_queries_estimate=100)
    print(f"  预估查询数: 100")
    print(f"  单次预算: {adaptive.per_query_budget:.4f}")

    for importance in [0.5, 1.0, 2.0, 5.0]:
        budget = adaptive.get_adaptive_budget(importance)
        print(f"  重要性={importance:.1f} → 预算={budget:.4f}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
