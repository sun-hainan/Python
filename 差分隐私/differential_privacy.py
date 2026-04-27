# -*- coding: utf-8 -*-
"""
算法实现：差分隐私 / differential_privacy

本文件实现 differential_privacy 相关的算法功能。
"""

import random
import math


def laplace_noise(scale: float) -> float:
    """
    生成Laplace噪声

    分布：p(x) = (1/2b) * exp(-|x|/b)
    其中 b = 1/epsilon（当sensitivity=1时）

    参数：
        scale: 尺度参数b

    返回：随机噪声
    """
    u = random.uniform(-0.5, 0.5)
    return -scale * math.copysign(1, u) * math.log(1 - 2 * abs(u))


def sensitivity(count: int, epsilon: float) -> float:
    """
    计算敏感度

    对于计数查询，敏感度 = 1
    """
    return 1.0


def noisy_count(true_count: int, epsilon: float) -> float:
    """
    添加噪声的计数查询

    参数：
        true_count: 真实计数
        epsilon: 隐私参数

    返回：带噪声的计数
    """
    scale = 1.0 / epsilon
    noise = laplace_noise(scale)
    return max(0, true_count + noise)


def dp_average(true_sum: float, n: int, epsilon: float) -> float:
    """
    差分隐私的平均查询

    对于求和查询，需要先clip到已知范围
    """
    clip_low = 0
    clip_high = 100

    clipped_sum = max(clip_low, min(true_sum, clip_high))
    scale = (clip_high - clip_low) / (epsilon * n)
    noise = laplace_noise(scale)

    return (clipped_sum / n) + noise


class DifferentialPrivacy:
    """差分隐私机制"""

    def __init__(self, epsilon: float = 1.0, delta: float = 0.0):
        self.epsilon = epsilon
        self.delta = delta

    def laplace_mechanism(self, query_result: float, sensitivity: float) -> float:
        """Laplace机制"""
        scale = sensitivity / self.epsilon
        noise = laplace_noise(scale)
        return query_result + noise

    def gaussian_mechanism(self, query_result: float, sensitivity: float, delta: float = None) -> float:
        """Gaussian机制（更弱的隐私保证）"""
        if delta is None:
            delta = self.delta

        # 对于(ε, δ)-DP，使用σ = sensitivity * sqrt(2 * log(1.25/δ)) / ε
        sigma = sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / self.epsilon
        noise = random.gauss(0, sigma)
        return query_result + noise


def composition_theorem():
    """
    组合定理

    连续查询k次，总隐私损失约为 O(sqrt(k * log(1/δ)) * ε
    """
    print("=== 组合定理 ===")
    print()
    print("k次查询的总隐私损失:")
    print("  基本组合: k * ε")
    print("  高级组合: ε * sqrt(2k * log(1/δ))")
    print()
    print("这意味着:")
    print("  - 10次查询: ~3.2 * ε (当δ很小时)")
    print("  - 100次查询: ~10 * ε")
    print("  - 隐私预算需要相应增加")


def privacy_loss_tracking():
    """
    隐私损失追踪
    """
    print()
    print("=== 隐私损失追踪 ===")
    print()
    print("每次查询都会产生隐私损失")
    print("跟踪总隐私损失是FP-DP的核心")
    print()
    print("方法:")
    print("  1. 追踪 RDP (Rényi Differential Privacy)")
    print("  2. 追踪 f-DP (f-Differential Privacy)")
    print("  3. 使用 privacy accountant")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 差分隐私测试 ===\n")

    random.seed(42)

    # 测试计数查询
    true_count = 1000
    epsilon = 1.0

    print(f"真实计数: {true_count}")
    print(f"隐私参数 ε = {epsilon}")
    print()

    print("多次查询的结果（带噪声）:")
    for i in range(5):
        noisy = noisy_count(true_count, epsilon)
        error = abs(noisy - true_count)
        print(f"  查询{i+1}: {noisy:.2f} (误差: {error:.2f})")

    print()

    # 统计验证
    n_trials = 10000
    noisy_results = [noisy_count(true_count, epsilon) for _ in range(n_trials)]
    mean_error = sum(abs(n - true_count) for n in noisy_results) / n_trials

    print(f"MAE: {mean_error:.2f}")
    print(f"理论MAE（对于Laplace）: {1/epsilon:.2f}")

    print()
    composition_theorem()

    print("\n说明：")
    print("  - Laplace机制适合隐私保护计数")
    print("  - Gaussian机制允许(ε,δ)-DP")
    print("  - 组合定理保证多次查询的总体隐私损失")
