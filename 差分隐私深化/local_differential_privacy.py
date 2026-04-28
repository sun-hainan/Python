# -*- coding: utf-8 -*-
"""
本地差分隐私模块

本模块实现本地差分隐私（Local Differential Privacy, LDP）技术。
在本地差分隐私中，数据扰动在用户端完成，数据收集者无法访问原始数据。

主要机制：
- 随机化响应（Randomized Response）：适用于二元问题
- 哈希机制（Hash Mechanism）：用于高频项检测
- Unary Encoding：单元编码
- 二元编码（Binary Encoding）

作者：算法实现
版本：1.0
"""

import numpy as np
from typing import List, Tuple, Dict


def randomized_response(bit: int, epsilon: float) -> int:
    """
    随机化响应（Randomized Response）

    用于二元问题（yes/no）的本地差分隐私机制。
    原理：用户以一定概率翻转自己的真实答案。

    参数:
        bit: 用户的真实答案（0或1）
        epsilon: 隐私预算

    返回:
        扰动后的答案（0或1）

    原理:
        P(报告1 | 真实1) = e^ε / (1 + e^ε)
        P(报告0 | 真实0) = e^ε / (1 + e^ε)
        P(报告1 | 真实0) = 1 / (1 + e^ε)
        P(报告0 | 真实1) = 1 / (1 + e^ε)
    """
    prob = np.exp(epsilon) / (1 + np.exp(epsilon))

    if np.random.random() < prob:
        return bit
    else:
        return 1 - bit


def estimate_population_from_rr(yes_count: int, total_count: int,
                                epsilon: float) -> float:
    """
    从随机化响应数据估计真实比例

    参数:
        yes_count: 报告"Yes"的样本数
        total_count: 总样本数
        epsilon: 隐私预算

    返回:
        真实"Yes"比例的估计值
    """
    p = np.exp(epsilon) / (1 + np.exp(epsilon))
    q = 1 / (1 + np.exp(epsilon))

    observed_ratio = yes_count / total_count
    # 使用最大似然估计
    estimated_ratio = (observed_ratio - q) / (p - q)
    return max(0.0, min(1.0, estimated_ratio))


def unary_encoding(value: int, n_categories: int, epsilon: float) -> np.ndarray:
    """
    一元编码（Unary Encoding）

    将类别值编码为n_categories维二进制向量，只有对应类别位置为1。
    然后对每个比特独立应用随机化响应。

    参数:
        value: 类别值（0到n_categories-1）
        n_categories: 类别总数
        epsilon: 隐私预算（每个比特）

    返回:
        编码后的二进制向量
    """
    encoding = np.zeros(n_categories)
    encoding[value] = 1

    # 对每个比特应用随机化响应
    for i in range(n_categories):
        encoding[i] = randomized_response(int(encoding[i]), epsilon)

    return encoding


def decode_unary(encoded: np.ndarray, epsilon: float) -> int:
    """
    解码一元编码

    参数:
        encoded: 扰动后的一元编码向量
        epsilon: 隐私预算

    返回:
        估计的类别值
    """
    n_categories = len(encoded)
    scores = []

    for cat in range(n_categories):
        # 计算每个类别的似然
        prob_correct = np.exp(epsilon) / (1 + np.exp(epsilon))
        prob_flip = 1 / (1 + np.exp(epsilon))

        # 似然比评分
        likelihood = np.prod(
            [prob_correct if encoded[i] == (1 if i == cat else 0) else prob_flip
             for i in range(n_categories)]
        )
        scores.append(likelihood)

    return int(np.argmax(scores))


def symmetric_unary_encoding(value: int, n_categories: int,
                               epsilon: float) -> np.ndarray:
    """
    对称一元编码（Symmetric Unary Encoding）

    与一元编码类似，但使用更对称的扰动方案。

    参数:
        value: 类别值
        n_categories: 类别总数
        epsilon: 隐私预算

    返回:
        扰动后的编码向量
    """
    encoding = np.zeros(n_categories)
    for i in range(n_categories):
        if i == value:
            encoding[i] = randomized_response(1, epsilon)
        else:
            encoding[i] = randomized_response(0, epsilon)
    return encoding


def hadamard_mechanism(values: np.ndarray, epsilon: float,
                        n_categories: int) -> np.ndarray:
    """
    Hadamard机制（简化版）

    使用Hadamard矩阵进行正交扰动，提高效用。

    参数:
        values: 输入值数组
        epsilon: 隐私预算
        n_categories: 类别数

    返回:
        扰动后的结果
    """
    # 生成Hadamard矩阵（简化：使用 Walsh-Hadamard）
    def hadamard_matrix(n):
        if n == 1:
            return np.array([[1]])
        else:
            h_n = hadamard_matrix(n // 2)
            top = np.hstack([h_n, h_n])
            bottom = np.hstack([h_n, -h_n])
            return np.vstack([top, bottom])

    n = 2 ** int(np.ceil(np.log2(n_categories)))
    h = hadamard_matrix(n)

    # 选择随机行进行报告
    selected_row = np.random.randint(0, n)
    report = np.zeros(n)
    for i, val in enumerate(values):
        if i < n_categories:
            report[selected_row] += h[selected_row, i] * val

    noise_scale = 2.0 / epsilon
    report += np.random.laplace(0, noise_scale)

    return report


def local_hash(input_value: int, n_buckets: int, n_hashes: int,
               epsilon: float, salt: int = None) -> List[int]:
    """
    本地哈希机制（Local Hash）

    用于高频项检测的LDP机制。

    参数:
        input_value: 输入值
        n_buckets: 桶数量
        n_hashes: 哈希函数数量
        epsilon: 隐私预算
        salt: 随机盐值

    返回:
        哈希到的桶索引列表
    """
    if salt is None:
        salt = np.random.randint(0, 2**31)

    buckets = []
    for h in range(n_hashes):
        # 简化的哈希函数
        hash_val = (input_value * (h + 1) * 2654435761 + salt) % (2**32)
        bucket = int(hash_val % n_buckets)
        buckets.append(bucket)

    return buckets


def heavy_hitter_detection(values: List[int], epsilon: float,
                            n_buckets: int = 1024,
                            threshold: float = 0.01) -> List[Tuple[int, float]]:
    """
    高频项检测

    使用LDP机制检测频繁项。

    参数:
        values: 输入值列表
        epsilon: 隐私预算
        n_buckets: 桶数量
        threshold: 频率阈值

    返回:
        (值, 估计频率)列表
    """
    # 简化的 heavy hitter 检测
    n = len(values)
    value_counts = {}

    for val in values:
        # 随机化响应
        reported = randomized_response(1, epsilon) if val else randomized_response(0, epsilon)

        if reported == 1:
            buckets = local_hash(val, n_buckets, 1, epsilon)
            for b in buckets:
                if b not in value_counts:
                    value_counts[b] = 0
                value_counts[b] += 1

    # 估计频率
    p = np.exp(epsilon) / (1 + np.exp(epsilon))
    q = 1 / (1 + np.exp(epsilon))

    heavy_hitters = []
    for bucket, count in value_counts.items():
        # 从扰动计数估计真实计数
        estimated_count = (count - n * q) / (p - q)
        if estimated_count > threshold * n:
            heavy_hitters.append((bucket, estimated_count / n))

    return sorted(heavy_hitters, key=lambda x: x[1], reverse=True)


def compose_ldp_queries(query_results: List[np.ndarray], epsilon: float) -> np.ndarray:
    """
    LDP查询结果组合

    将多个LDP查询结果组合起来。

    参数:
        query_results: 各查询的扰动结果列表
        epsilon: 单次查询的隐私预算

    返回:
        组合后的估计值
    """
    k = len(query_results)
    total_eps = k * epsilon

    # 平均后乘以缩放因子
    combined = np.mean(query_results, axis=0)

    return combined


if __name__ == "__main__":
    print("=" * 60)
    print("本地差分隐私（LDP）测试")
    print("=" * 60)

    # 测试1：随机化响应
    print("\n【测试1】随机化响应")
    true_bits = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
    for eps in [0.5, 1.0, 2.0, 5.0]:
        np.random.seed(42)
        perturbed = [randomized_response(b, eps) for b in true_bits]
        match = sum(1 for t, p in zip(true_bits, perturbed) if t == p)
        print(f"  ε={eps}: 原始→{true_bits}")
        print(f"        扰动→{perturbed}")
        print(f"        保持比例: {match/len(true_bits)*100:.1f}%")

    # 测试2：比例估计
    print("\n【测试2】随机化响应比例估计")
    true_yes_rate = 0.3
    n_samples = 10000
    true_bits = [1 if np.random.random() < true_yes_rate else 0 for _ in range(n_samples)]
    eps = 1.0

    np.random.seed(42)
    perturbed = [randomized_response(b, eps) for b in true_bits]
    yes_count = sum(perturbed)
    estimated_rate = estimate_population_from_rr(yes_count, n_samples, eps)
    print(f"  真实Yes比例: {true_yes_rate:.2%}")
    print(f"  观测Yes数: {yes_count}")
    print(f"  估计Yes比例: {estimated_rate:.2%}")

    # 测试3：一元编码
    print("\n【测试3】一元编码/解码")
    n_categories = 5
    true_value = 2
    eps = 1.0

    np.random.seed(42)
    encoded = unary_encoding(true_value, n_categories, eps)
    decoded = decode_unary(encoded, eps)
    print(f"  真实类别: {true_value}")
    print(f"  编码向量: {encoded}")
    print(f"  解码类别: {decoded}")

    # 测试4：多次编码验证
    print("\n【测试4】一元编码准确率测试")
    n_trials = 100
    eps = 2.0
    n_categories = 10
    correct = 0

    for _ in range(n_trials):
        true_val = np.random.randint(0, n_categories)
        encoded = unary_encoding(true_val, n_categories, eps)
        decoded = decode_unary(encoded, eps)
        if decoded == true_val:
            correct += 1

    print(f"  准确率: {correct/n_trials*100:.1f}%")

    # 测试5：本地哈希
    print("\n【测试5】本地哈希机制")
    values = [1, 5, 10, 15, 20, 25]
    n_buckets = 100
    eps = 1.0

    print(f"  值: {values}")
    print(f"  桶数量: {n_buckets}")
    print(f"  哈希结果:")
    for val in values:
        buckets = local_hash(val, n_buckets, n_hashes=3, epsilon=eps)
        print(f"    值{val:2d} → 桶{buckets}")

    # 测试6：高频项检测
    print("\n【测试6】高频项检测模拟")
    np.random.seed(42)
    # 生成模拟数据（某些值出现频率较高）
    data = [1, 2, 3, 5, 5, 5, 10, 10, 10, 10, 10] * 100
    np.random.shuffle(data)

    heavy = heavy_hitter_detection(data, epsilon=2.0, n_buckets=100, threshold=0.05)
    print(f"  检测到的高频项: {heavy[:5]}")

    # 测试7：编码对比
    print("\n【测试7】不同ε下的编码准确率")
    categories = 20
    trials = 500
    print(f"  类别数={categories}, 测试次数={trials}")
    print(f"  {'ε':<8} {'准确率':<10}")
    print(f"  {'-'*20}")
    for eps in [0.5, 1.0, 2.0, 5.0]:
        correct = 0
        for _ in range(trials):
            true_val = np.random.randint(0, categories)
            encoded = unary_encoding(true_val, categories, eps)
            decoded = decode_unary(encoded, eps)
            if decoded == true_val:
                correct += 1
        print(f"  {eps:<8.1f} {correct/trials*100:.1f}%")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
