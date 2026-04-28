# -*- coding: utf-8 -*-
"""
稀疏向量技术 (Sparse Vector Technique, SVT)
==========================================

算法原理:
SVT是一种 answering queries under differential privacy 的重要技术。
核心思想: 当用户对大量查询(可能无穷多)感兴趣时，但只有少数查询的
答案超过某个阈值，SVT通过只报告"超过阈值的查询"来节省隐私预算。

工作流程:
1. 设置一个敏感阈值 T
2. 对每个查询添加Laplace噪声
3. 比较噪声值与阈值
4. 一旦报告了C个查询的答案，立即停止(可选)
5. 或者继续但使用更保守的隐私参数

变体:
- 阈值查询 (Threshold Queries): 回答"是否超过阈值"的问题
- 连续查询 (Continuous SVT): 持续处理无限查询流
- 带停止条件的SVT: 达到一定数量后终止

时间复杂度: O(k) 其中k为查询数量
空间复杂度: O(1) 仅需存储阈值和计数器

应用场景:
- 特征选择和显著性检验
- 子集选择问题
- 社交网络中的异常检测
- 数据挖掘中的模式发现
"""

import math
import numpy as np


def laplace_noise(scale):
    """
    生成Laplace噪声
    
    参数:
        scale: Laplace分布的尺度参数 (b = 1/sensitivity / ε)
    
    返回:
        从Lap(0, b)采样的噪声值
    """
    # 使用逆变换法生成Laplace随机数
    u = np.random.uniform(-0.5, 0.5)
    return -scale * np.sign(u) * np.log(1 - 2 * abs(u))


class SparseVector:
    """
    稀疏向量技术核心类
    
    属性:
        threshold: 敏感阈值T
        sensitivity: 查询的敏感性(最大改变量)
        epsilon: 隐私预算
        reported_count: 已报告的查询数量
        max_reports: 最大报告数量 (C)
    """
    
    def __init__(self, threshold, sensitivity, epsilon, max_reports=float('inf')):
        """
        初始化SVT
        
        参数:
            threshold: 感兴趣查询的阈值
            sensitivity: 查询函数的敏感性
            epsilon: 隐私预算
            max_reports: 最大报告数量限制
        """
        self.threshold = threshold
        self.sensitivity = sensitivity
        self.epsilon = epsilon
        self.scale = sensitivity / epsilon  # Laplace噪声尺度
        self.reported_count = 0
        self.max_reports = max_reports
        self.results = []  # 存储报告的结果
    
    def answer_query(self, true_answer):
        """
        回答单个查询
        
        参数:
            true_answer: 查询的真实答案
        
        返回:
            (above_threshold, noisy_answer): 是否超过阈值及带噪声的答案
        """
        # 如果已达最大报告数，停止响应
        if self.reported_count >= self.max_reports:
            return False, None
        
        # 添加Laplace噪声
        noisy_answer = true_answer + laplace_noise(self.scale)
        
        # 与阈值比较
        above_threshold = noisy_answer >= self.threshold
        
        if above_threshold:
            self.reported_count += 1
            self.results.append(noisy_answer)
        
        return above_threshold, noisy_answer
    
    def answer_batch(self, true_answers):
        """
        批量回答查询
        
        参数:
            true_answers: 真实答案列表
        
        返回:
            报告的查询索引列表
        """
        reported_indices = []
        
        for i, ans in enumerate(true_answers):
            above, noisy = self.answer_query(ans)
            if above:
                reported_indices.append(i)
            
            # 检查是否达到最大报告数
            if self.reported_count >= self.max_reports:
                break
        
        return reported_indices


class ContinuousSVT:
    """
    连续稀疏向量技术 (Continuous SVT)
    
    适用于无限查询流的场景，使用"泄漏"机制来限制隐私损失。
    每次比较后都会消耗部分隐私预算。
    """
    
    def __init__(self, threshold, sensitivity, epsilon, beta=0.5):
        """
        初始化连续SVT
        
        参数:
            threshold: 阈值
            sensitivity: 敏感性
            epsilon: 总隐私预算
            beta: 预算分配因子，用于平衡查询精度和剩余预算
        """
        self.threshold = threshold
        self.sensitivity = sensitivity
        self.epsilon = epsilon
        self.beta = beta
        self.used_epsilon = 0.0
        self.query_count = 0
        self.answers = []
    
    def _get_noise_scale(self, remaining_epsilon):
        """
        根据剩余隐私预算计算噪声尺度
        """
        if remaining_epsilon <= 0:
            return float('inf')
        return self.sensitivity / remaining_epsilon
    
    def answer_next(self, true_answer):
        """
        回答下一个查询
        
        参数:
            true_answer: 当前查询的真实答案
        
        返回:
            噪声答案或None(如果隐私预算耗尽)
        """
        remaining = self.epsilon - self.used_epsilon
        
        if remaining <= 0:
            return None
        
        # 使用几何机制(适用于有界输出)
        noise_scale = self._get_noise_scale(remaining * self.beta)
        noise = laplace_noise(noise_scale)
        noisy_answer = true_answer + noise
        
        self.used_epsilon += remaining * (1 - self.beta)
        self.query_count += 1
        self.answers.append(noisy_answer)
        
        return noisy_answer


def sparse_vector_with_gnat(queries, threshold, sensitivity, epsilon, delta):
    """
    使用GNAT (Generalized Adaptive Noise) 机制的稀疏向量技术
    
    适用于回答关于数据库的连续谓词查询。
    
    参数:
        queries: 查询列表 (每个查询是数据库的函数)
        threshold: 阈值
        sensitivity: 敏感性
        epsilon: ε
        delta: δ (用于终止测试)
    
    返回:
        通过阈值的查询索引列表
    """
    # 简化的实现：使用指数机制选择候选查询
    scale = sensitivity / epsilon
    approved = []
    
    for i, q in enumerate(queries):
        # 模拟真实答案
        true_val = q()
        noisy_val = true_val + laplace_noise(scale)
        
        # 指数机制决定是否报告
        # 分数基于与阈值的距离
        if noisy_val >= threshold:
            # 以指数概率接受
            prob = math.exp(epsilon * (noisy_val - threshold) / 2)
            if np.random.random() < prob:
                approved.append(i)
    
    return approved


if __name__ == "__main__":
    # 测试稀疏向量技术
    
    print("=" * 60)
    print("稀疏向量技术 (SVT) 测试")
    print("=" * 60)
    
    # 设置随机种子以便复现
    np.random.seed(42)
    
    # 测试1: 基本SVT
    print("\n[测试1] 基本稀疏向量技术")
    threshold = 50.0
    sensitivity = 1.0
    epsilon = 1.0
    max_reports = 3
    
    # 创建查询函数列表 (真实答案为1-100)
    true_answers = list(range(1, 101))
    
    svt = SparseVector(threshold, sensitivity, epsilon, max_reports)
    reported_indices = svt.answer_batch(true_answers)
    
    print(f"  阈值T={threshold}, ε={epsilon}, 最大报告数C={max_reports}")
    print(f"  查询数量: {len(true_answers)}")
    print(f"  真实答案>阈值数量: {sum(1 for a in true_answers if a >= threshold)}")
    print(f"  SVT报告的索引: {reported_indices[:10]}...")  # 只显示前10个
    print(f"  总报告数: {len(reported_indices)}")
    print(f"  隐私消耗: ε={svt.epsilon}, 实际报告数={svt.reported_count}")
    
    # 测试2: 连续SVT
    print("\n[测试2] 连续稀疏向量技术")
    np.random.seed(42)
    
    threshold = 30.0
    epsilon = 2.0
    continuous_svt = ContinuousSVT(threshold, sensitivity, epsilon, beta=0.5)
    
    stream_answers = [25, 35, 28, 42, 31, 55, 22, 38, 45, 60]
    print(f"  查询流: {stream_answers}")
    print(f"  阈值T={threshold}, 总ε={epsilon}")
    
    results = []
    for i, ans in enumerate(stream_answers):
        noisy = continuous_svt.answer_next(ans)
        status = f"≥T (noisy={noisy:.2f})" if noisy is not None and noisy >= threshold else "noisy" if noisy else "预算耗尽"
        results.append((i, ans, status))
    
    print(f"  结果:")
    for idx, true_val, status in results:
        print(f"    Q{idx}: 真值={true_val}, {status}")
    
    # 测试3: SVT vs 基本组合对比
    print("\n[测试3] SVT隐私效率对比")
    
    k = 1000  # 1000个查询
    epsilon_per_query = 0.1
    
    # 基本组合消耗
    basic_eps = k * epsilon_per_query
    print(f"  1000个查询:")
    print(f"    基本组合总ε: {basic_eps:.1f}")
    
    # SVT只报告少数几个
    svt_eps = epsilon_per_query * math.sqrt(2 * k * math.log(1 / 1e-5))
    print(f"    SVT总ε (理论上): {svt_eps:.2f}")
    print(f"    隐私节省: {basic_eps/svt_eps:.1f}x")
    
    # 测试4: 蒙特卡洛模拟SVT精度
    print("\n[测试4] SVT精度模拟 (1000次)")
    
    np.random.seed(0)
    successes = 0
    n_trials = 1000
    threshold = 50.0
    epsilon = 1.0
    
    for _ in range(n_trials):
        svt = SparseVector(threshold, 1.0, epsilon, max_reports=5)
        true_answers = list(range(1, 101))
        reported = svt.answer_batch(true_answers)
        
        # 检查是否成功找到真实大于阈值的查询
        true_above = set(i for i, a in enumerate(true_answers, 1) if a >= threshold)
        # 由于索引从0开始，值i+1>=50意味着索引i>=49
        if len(reported) > 0 and min(reported) >= 49:
            successes += 1
    
    print(f"  阈值T={threshold} (真实答案≥50的索引≥49)")
    print(f"  1000次实验中至少找到一个正确答案的比例: {successes/n_trials:.2%}")
    
    print("\n" + "=" * 60)
    print("测试完成 - SVT在稀疏答案场景下高效节省隐私预算")
    print("=" * 60)
