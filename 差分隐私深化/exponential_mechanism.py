# -*- coding: utf-8 -*-
"""
指数机制 (Exponential Mechanism)
=================================

算法原理:
指数机制是McSherry和Talwar于2007年提出的用于选择最佳输出的差分隐私机制。
当输出空间是离散的且没有自然的数值响应时，指数机制提供了一种通用的隐私保护方法。

核心思想: 以与"效用函数值(quality score)"成指数比例的概率选择输出。
具体来说，对于输出空间R中的每个候选r，选择r的概率正比于exp(ε·q(D,r)/2Δq)，
其中q(D,r)是效用函数，Δq是其敏感性。

敏感性分析:
- 离散型: Δq = max_{D,D'} |q(D,r) - q(D',r)|，遍历所有候选r取最大值
- 连续型: 需要计算效用函数关于数据的Lipschitz常数

变体:
1. 离散指数机制: 输出空间有限，如选择集合中的元素
2. 连续指数机制: 使用密度函数而非概率质量函数
3. 受限指数机制: 在某些输出上赋予零概率

时间复杂度: O(|R|·k) 其中|R|是候选空间大小，k是效用评估次数
空间复杂度: O(|R|) 用于存储候选和效用值

应用场景:
- 特征选择和模型选择
- 数据发布(如直方图bins选择)
- 推荐系统中的物品推荐
- SQL查询中的JOIN顺序优化
- 机器学习中的超参数调优
"""

import math
import numpy as np
from bisect import bisect


def exponential_mechanism(discrete_outputs, quality_scores, epsilon, sensitivity):
    """
    离散指数机制的标准实现
    
    参数:
        discrete_outputs: 可能的输出列表 (R)
        quality_scores: 每个输出的效用值列表 q(D,r)
        epsilon: 隐私预算
        sensitivity: 效用函数的敏感性 Δq
    
    返回:
        选中的输出
    
    数学原理:
    P(r) ∝ exp(ε·q(D,r) / 2Δq)
    """
    assert len(discrete_outputs) == len(quality_scores)
    assert sensitivity > 0
    
    # 计算归一化常数(但实际通过抽样算法避免显式计算)
    n_outputs = len(discrete_outputs)
    scale = epsilon / (2 * sensitivity)
    
    # 转换为概率(使用softmax技巧避免数值溢出)
    max_q = max(quality_scores)
    scaled_q = [scale * (q - max_q) for q in quality_scores]
    
    # 使用Gumbel技巧进行高效抽样
    # 从Gumbel(0,1)采样并加到scaled_q上
    gumbel_samples = np.random.gumbel(0, 1, size=n_outputs)
    perturbed_scores = scaled_q + gumbel_samples
    
    # 选择 perturbed score 最大的输出
    best_idx = np.argmax(perturbed_scores)
    
    return discrete_outputs[best_idx]


def exponential_mechanism_strict(discrete_outputs, quality_scores, epsilon, sensitivity):
    """
    严格实现的离散指数机制 (使用累积分布函数抽样)
    
    当候选空间较小时使用此方法。
    
    参数:
        discrete_outputs: 输出候选列表
        quality_scores: 效用值列表
        epsilon: 隐私参数ε
        sensitivity: 敏感性Δq
    
    返回:
        按概率分布抽样的输出
    """
    n = len(discrete_outputs)
    scale = epsilon / (2 * sensitivity)
    
    # 计算未归一化概率
    unnorm_probs = [math.exp(scale * q) for q in quality_scores]
    total = sum(unnorm_probs)
    
    # 归一化
    probs = [p / total for p in unnorm_probs]
    
    # 累积分布
    cumsum = np.cumsum([0.0] + probs)
    
    # 逆变换抽样
    u = np.random.random()
    idx = bisect(cumsum, u) - 1
    idx = min(idx, n - 1)  # 处理边界情况
    
    return discrete_outputs[idx]


def continuous_exponential_mechanism(quality_density, domain, epsilon, sensitivity, n_samples=1):
    """
    连续指数机制
    
    适用于输出空间连续的场景。
    
    参数:
        quality_density: 效用密度函数 q(x)，返回实数值
        domain: 输出域 (min_val, max_val)
        epsilon: 隐私参数
        sensitivity: 密度函数的敏感性
        n_samples: 采样数量
    
    返回:
        从 exp(ε·q(x)/2Δq) / Z dx 采样的值
    """
    # 使用Metropolis-Hastings抽样
    min_val, max_val = domain
    scale = epsilon / (2 * sensitivity)
    
    samples = []
    current = np.random.uniform(min_val, max_val)
    current_density = math.exp(scale * quality_density(current))
    
    # 固定步数Metropolis
    step_size = (max_val - min_val) * 0.1
    
    for _ in range(1000):  # burn-in
        proposal = current + np.random.uniform(-step_size, step_size)
        proposal = np.clip(proposal, min_val, max_val)
        proposal_density = math.exp(scale * quality_density(proposal))
        
        # 接受概率
        accept_prob = min(1.0, proposal_density / current_density)
        
        if np.random.random() < accept_prob:
            current = proposal
            current_density = proposal_density
    
    # 正式采样
    for _ in range(n_samples):
        for _ in range(100):  # 步数
            proposal = current + np.random.uniform(-step_size, step_size)
            proposal = np.clip(proposal, min_val, max_val)
            proposal_density = math.exp(scale * quality_density(proposal))
            
            accept_prob = min(1.0, proposal_density / current_density)
            
            if np.random.random() < accept_prob:
                current = proposal
                current_density = proposal_density
        
        samples.append(current)
    
    return samples if n_samples > 1 else samples[0]


def compute_sensitivity_discrete(database, query_function, outputs):
    """
    计算离散效用函数的敏感性
    
    参数:
        database: 数据集 (作为列表)
        query_function: q(D, r) -> 效用值的函数
        outputs: 所有可能的输出候选
    
    返回:
        敏感性Δq
    """
    n = len(database)
    max_sensitivity = 0.0
    
    # 对每个可能的输出，计算相邻数据集的最大差异
    for r in outputs:
        # 遍历所有相邻数据集对(通过移除每个元素)
        for i in range(n):
            # D_i: 移除第i个元素
            D_i = database[:i] + database[i+1:]
            q_D = query_function(database, r)
            q_Di = query_function(D_i, r)
            
            diff = abs(q_D - q_Di)
            max_sensitivity = max(max_sensitivity, diff)
    
    return max_sensitivity


class ExponentialMechanism:
    """
    指数机制的面向对象封装
    
    提供状态保持和多次采样能力。
    """
    
    def __init__(self, epsilon, sensitivity):
        """
        初始化
        
        参数:
            epsilon: 隐私预算
            sensitivity: 效用函数敏感性
        """
        self.epsilon = epsilon
        self.sensitivity = sensitivity
        self.scale = epsilon / (2 * sensitivity)
        self.sample_count = 0
    
    def select(self, outputs, quality_scores):
        """
        根据效用分数选择输出
        
        参数:
            outputs: 输出候选列表
            quality_scores: 对应的效用值
        
        返回:
            选中的输出
        """
        self.sample_count += 1
        return exponential_mechanism(outputs, quality_scores, self.epsilon, self.sensitivity)
    
    def select_strict(self, outputs, quality_scores):
        """
        使用严格概率分布选择
        """
        self.sample_count += 1
        return exponential_mechanism_strict(outputs, quality_scores, self.epsilon, self.sensitivity)


if __name__ == "__main__":
    # 测试指数机制
    
    print("=" * 60)
    print("指数机制 (Exponential Mechanism) 测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1: 基础离散指数机制
    print("\n[测试1] 离散指数机制 - 物品选择")
    
    # 候选物品 (如推荐系统中的商品)
    items = ["商品A", "商品B", "商品C", "商品D", "商品E"]
    
    # 效用分数 (如点击率预测)
    quality_scores = [0.85, 0.92, 0.78, 0.95, 0.88]
    
    epsilon = 1.0
    sensitivity = 1.0  # 假设效用分数敏感性为1
    
    em = ExponentialMechanism(epsilon, sensitivity)
    
    # 多次采样看分布
    selections = {item: 0 for item in items}
    n_trials = 10000
    
    for _ in range(n_trials):
        selected = em.select(items, quality_scores)
        selections[selected] += 1
    
    print(f"  候选物品: {items}")
    print(f"  效用分数: {quality_scores}")
    print(f"  ε={epsilon}, 采样{n_trials}次")
    print(f"  选择分布:")
    for item, count in selections.items():
        print(f"    {item}: {count}次 ({count/n_trials:.2%})")
    
    # 测试2: 严格实现 vs Gumbel技巧
    print("\n[测试2] 抽样方法验证")
    
    epsilon = 0.5
    sensitivity = 1.0
    em = ExponentialMechanism(epsilon, sensitivity)
    
    n_trials = 5000
    
    # Gumbel方法
    gumbel_results = []
    for _ in range(n_trials):
        result = em.select(items, quality_scores)
        gumbel_results.append(result)
    
    # 严格方法
    strict_results = []
    for _ in range(n_trials):
        result = em.select_strict(items, quality_scores)
        strict_results.append(result)
    
    print(f"  Gumbel方法 - 商品D选择率: {gumbel_results.count('商品D')/n_trials:.3f}")
    print(f"  严格方法 - 商品D选择率: {strict_results.count('商品D')/n_trials:.3f}")
    print(f"  理论概率 ∝ exp(ε·q/2Δ) = exp({epsilon}·0.95/2) = {math.exp(epsilon*0.95/2):.3f}")
    
    # 测试3: 敏感性计算示例
    print("\n[测试3] 敏感性计算")
    
    # 假设数据库是一组评分，效用函数是"选择某物品后的总效用"
    database = [4, 5, 3, 4, 5, 4, 3, 5, 4, 5]  # 用户对不同物品的评分
    
    # 物品对应的"受欢迎程度分数"
    item_popularity = {"A": 8, "B": 6, "C": 9, "D": 7, "E": 5}
    
    def utility_func(data, item):
        """计算选择某物品的效用(基于数据集中高分用户数)"""
        # 简化：效用=数据集中评分为5的数量
        return sum(1 for d in data if d >= 4)
    
    outputs = list(item_popularity.keys())
    scores = [utility_func(database, o) for o in outputs]
    
    print(f"  数据集: {database}")
    print(f"  效用函数: 评分为4+的元素个数")
    print(f"  效用分数: {dict(zip(outputs, scores))}")
    
    # 敏感性计算：移除一个元素，最多改变1
    computed_sensitivity = 1.0
    print(f"  计算敏感性: Δq = {computed_sensitivity}")
    
    # 测试4: 连续指数机制
    print("\n[测试4] 连续指数机制 - 区间选择")
    
    def quality_density(x):
        """效用密度函数: 在50附近有峰值"""
        # 简化为以50为中心的高斯
        return math.exp(-0.5 * ((x - 50) / 10) ** 2)
    
    epsilon = 1.0
    sensitivity = 1.0
    
    samples = continuous_exponential_mechanism(
        quality_density, 
        domain=(0, 100), 
        epsilon=epsilon, 
        sensitivity=sensitivity,
        n_samples=1000
    )
    
    mean_sample = np.mean(samples)
    std_sample = np.std(samples)
    
    print(f"  效用密度: 均值50, 标准差10的高斯分布")
    print(f"  ε={epsilon}, 采样1000次")
    print(f"  样本均值: {mean_sample:.2f}")
    print(f"  样本标准差: {std_sample:.2f}")
    
    # 测试5: ε影响实验
    print("\n[测试5] 不同ε值的选择性比较")
    
    quality_scores = [10, 20, 30, 40, 50]
    outputs = list(range(5))
    
    print(f"  效用分数: {quality_scores} (递增)")
    print(f"  {'ε':>6} | 选最大值比例 | 选最小值比例")
    print("  " + "-" * 35)
    
    for eps in [0.01, 0.1, 0.5, 1.0, 2.0]:
        em = ExponentialMechanism(eps, 1.0)
        results = [em.select(outputs, quality_scores) for _ in range(1000)]
        max_pct = results.count(4) / 1000 * 100
        min_pct = results.count(0) / 1000 * 100
        print(f"  {eps:>6.2f} | {max_pct:>11.1f}% | {min_pct:>12.1f}%")
    
    print("\n" + "=" * 60)
    print("测试完成 - ε越大，选择越偏向高效用值")
    print("=" * 60)
