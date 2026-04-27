# -*- coding: utf-8 -*-
"""
算法实现：安全多方计算 / privacy_average

本文件实现 privacy_average 相关的算法功能。
"""

from typing import List


class SecureAverage:
    """安全平均计算"""

    def __init__(self, n_parties: int):
        """
        参数：
            n_parties: 参与方数量
        """
        self.n_parties = n_parties

    def simple_additive(self, values: List[float]) -> float:
        """
        简单加性分享方法

        参数：
            values: 各方数值

        返回：平均值
        """
        # 各方添加随机数
        # 简化：直接求和
        total = sum(values)
        return total / self.n_parties

    def differential_privacy_average(self, values: List[float],
                                     epsilon: float = 1.0) -> float:
        """
        差分隐私平均

        参数：
            values: 各方数值
            epsilon: 隐私预算

        返回：带噪声的平均
        """
        import numpy as np

        # 添加Laplace噪声
        sensitivity = max(values) - min(values)
        noise = np.random.laplace(0, sensitivity / epsilon)

        return sum(values) / self.n_parties + noise

    def secure_sum_via_shares(self, values: List[float],
                             n_shares: int = 3) -> float:
        """
        秘密共享求和

        参数：
            values: 各方数值
            n_shares: 分割份数

        返回：总和
        """
        import random

        # 简化的秘密共享
        shares = [[] for _ in range(n_shares)]

        for value in values:
            # 分割值
            parts = [random.random() * value for _ in range(n_shares - 1)]
            parts.append(value - sum(parts))

            for i in range(n_shares):
                shares[i].append(parts[i])

        # 各方计算部分和
        partial_sums = [sum(s) for s in shares]

        # 组合得到总和
        total = sum(partial_sums)

        return total


def smpc_applications():
    """安全多方计算应用"""
    print("=== 安全多方计算应用 ===")
    print()
    print("1. 联合数据分析")
    print("   - 多家医院合作分析病例")
    print("   - 不暴露原始数据")
    print()
    print("2. 隐私保护机器学习")
    print("   - 数据不离开本地")
    print("   - 模型在加密数据上训练")
    print()
    print("3. 竞价系统")
    print("   - 不泄露出价")
    print("   - 确定最高价")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 安全平均计算测试 ===\n")

    n_parties = 5
    secure_avg = SecureAverage(n_parties)

    # 各方数据
    values = [100.0, 120.0, 95.0, 110.0, 105.0]

    print(f"参与方数量: {n_parties}")
    print(f"各方数值: {values}")
    print()

    # 简单平均
    simple_result = secure_avg.simple_additive(values)
    print(f"简单平均: {simple_result:.2f}")

    # 差分隐私平均
    dp_result = secure_avg.differential_privacy_average(values, epsilon=1.0)
    print(f"差分隐私平均 (ε=1.0): {dp_result:.2f}")

    # 秘密共享
    ss_result = secure_avg.secure_sum_via_shares(values)
    print(f"秘密共享求和: {ss_result:.2f}")

    print()
    smpc_applications()

    print()
    print("说明：")
    print("  - 安全多方计算保护隐私")
    print("  - 多种实现方式")
    print("  - 在金融、医疗等领域重要")
