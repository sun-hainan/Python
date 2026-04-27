# -*- coding: utf-8 -*-

"""

算法实现：差分隐私 / budget_tracker



本文件实现 budget_tracker 相关的算法功能。

"""



from typing import List, Tuple, Optional

from dataclasses import dataclass

from datetime import datetime





@dataclass

class PrivacyQuery:

    """隐私查询"""

    description: str

    epsilon: float

    delta: Optional[float]

    timestamp: str





class PrivacyBudgetTracker:

    """隐私预算追踪器"""



    def __init__(self, total_epsilon: float, total_delta: float = 0.0):

        """

        参数：

            total_epsilon: 总ε预算

            total_delta: 总δ预算

        """

        self.total_epsilon = total_epsilon

        self.total_delta = total_delta

        self.used_epsilon = 0.0

        self.used_delta = 0.0

        self.queries = []



    def query(self, epsilon: float, description: str,

             delta: float = 0.0) -> Tuple[bool, float]:

        """

        执行查询（如果预算足够）



        参数：

            epsilon: 请求的ε

            description: 查询描述

            delta: 可选的δ



        返回：(是否允许, 剩余预算)

        """

        if self.used_epsilon + epsilon > self.total_epsilon:

            return False, self.remaining_epsilon()



        if self.used_delta + delta > self.total_delta:

            return False, self.remaining_delta()



        self.used_epsilon += epsilon

        self.used_delta += delta



        query = PrivacyQuery(

            description=description,

            epsilon=epsilon,

            delta=delta,

            timestamp=datetime.now().isoformat()

        )

        self.queries.append(query)



        return True, self.remaining_epsilon()



    def remaining_epsilon(self) -> float:

        """剩余ε预算"""

        return self.total_epsilon - self.used_epsilon



    def remaining_delta(self) -> float:

        """剩余δ预算"""

        return self.total_delta - self.used_delta



    def report(self) -> dict:

        """生成报告"""

        return {

            'total_epsilon': self.total_epsilon,

            'used_epsilon': self.used_epsilon,

            'remaining_epsilon': self.remaining_epsilon(),

            'total_delta': self.total_delta,

            'used_delta': self.used_delta,

            'remaining_delta': self.remaining_delta(),

            'n_queries': len(self.queries)

        }



    def can_afford(self, epsilon: float, delta: float = 0.0) -> bool:

        """检查是否负担得起"""

        return (self.remaining_epsilon() >= epsilon and

                self.remaining_delta() >= delta)





def privacy_accounting_systems():

    """隐私账户系统"""

    print("=== 隐私账户系统 ===")

    print()

    print("1. 简单求和")

    print("   - ε_total = Σ ε_i")

    print("   - 保守但安全")

    print()

    print("2. RDP (Rényi DP)")

    print("   - 更紧的边界")

    print("   - 用于高级组合")

    print()

    print("3. PCD (Privacy Loss Distributions)")

    print("   - 最紧密的组合")

    print("   - OpenDP库使用")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 隐私预算追踪测试 ===\n")



    # 创建追踪器

    tracker = PrivacyBudgetTracker(total_epsilon=10.0, total_delta=1e-5)



    print(f"总预算: ε = 10.0, δ = 1e-5")

    print()



    # 执行查询

    queries = [

        (0.5, "统计平均收入"),

        (1.0, "统计年龄分布"),

        (0.3, "直方图"),

        (2.0, "机器学习训练"),

    ]



    for epsilon, desc in queries:

        allowed, remaining = tracker.query(epsilon, desc)



        status = "✅ 允许" if allowed else "❌ 拒绝"

        print(f"{status} {desc}: ε={epsilon}, 剩余={remaining:.2f}")



    print()



    # 报告

    report = tracker.report()



    print("隐私预算报告：")

    print(f"  使用ε: {report['used_epsilon']:.2f} / {report['total_epsilon']}")

    print(f"  剩余ε: {report['remaining_epsilon']:.2f}")

    print(f"  查询数: {report['n_queries']}")



    print()

    privacy_accounting_systems()



    print()

    print("说明：")

    print("  - 隐私预算必须谨慎管理")

    print("  - 超支会破坏隐私保证")

    print("  - 建议使用专业库如OpenDP")

