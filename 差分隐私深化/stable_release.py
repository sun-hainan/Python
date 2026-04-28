# -*- coding: utf-8 -*-
"""
稳定发布 (Stable Release / Interactive Stability)
=================================================

算法原理:
稳定发布是一种处理迭代查询的差分隐私技术。核心思想是：
在回答一系列查询时，追踪哪些中间答案是"稳定的"(即不随数据微小变化而改变)，
并只对稳定答案添加少量噪声，而对不稳定答案进行更保守的处理。

关键概念:
1. 稳定性: 一个答案如果在相邻数据集上变化很小，则称为稳定的
2. 迭代查询: 用户可以自适应地提出后续查询
3. 停止条件: 何时应该停止回答以保护隐私

与SVT的关系:
稳定发布可以看作SVT的扩展，不仅判断是否超过阈值，
还追踪阈值附近的答案稳定性。

停止条件策略:
- 基于计数: 达到C个稳定答案后停止
- 基于隐私预算: 预算耗尽时停止
- 基于阈值: 连续t个不稳定答案后停止
- 基于置信度: 答案的置信区间足够窄后停止

时间复杂度: O(k) 其中k是查询数量
空间复杂度: O(1) 仅需计数器

应用场景:
- 交互式数据分析平台
- 机器学习模型调试
- 数据库查询系统
- A/B测试平台
"""

import math
import numpy as np


def laplace_noise(scale):
    """
    生成Laplace噪声
    
    参数:
        scale: Laplace分布的尺度参数
    
    返回:
        噪声样本
    """
    u = np.random.uniform(-0.5, 0.5)
    return -scale * np.sign(u) * np.log(1 - 2 * abs(u))


class StableRelease:
    """
    稳定发布机制
    
    追踪查询答案的稳定性，并据此调整噪声尺度。
    """
    
    def __init__(self, epsilon, sensitivity, stability_threshold=1.0):
        """
        初始化
        
        参数:
            epsilon: 隐私预算
            sensitivity: 查询敏感性
            stability_threshold: 稳定性阈值，超过此值认为答案不稳定
        """
        self.epsilon = epsilon
        self.sensitivity = sensitivity
        self.stability_threshold = stability_threshold
        self.scale = sensitivity / epsilon
        self.query_count = 0
        self.stable_count = 0
        self.unstable_count = 0
        self.answers = []
    
    def answer_query(self, true_answer, previous_answer=None):
        """
        回答查询并判断稳定性
        
        参数:
            true_answer: 当前查询的真实答案
            previous_answer: 前一个答案(如果有的话)
        
        返回:
            (noisy_answer, is_stable, privacy_cost)
        """
        self.query_count += 1
        
        # 计算稳定性
        is_stable = True
        privacy_cost = self.epsilon
        
        if previous_answer is not None:
            change = abs(true_answer - previous_answer)
            if change > self.stability_threshold:
                is_stable = False
                self.unstable_count += 1
            else:
                self.stable_count += 1
        
        # 根据稳定性调整噪声
        if is_stable:
            # 稳定答案：使用较小的噪声
            noise = laplace_noise(self.scale * 0.5)
            privacy_cost = self.epsilon * 0.5
        else:
            # 不稳定答案：使用标准噪声
            noise = laplace_noise(self.scale)
            privacy_cost = self.epsilon
        
        noisy_answer = true_answer + noise
        self.answers.append((true_answer, noisy_answer, is_stable))
        
        return noisy_answer, is_stable, privacy_cost
    
    def get_total_privacy_cost(self):
        """
        获取累积隐私成本
        """
        # 简单的线性组合
        total_eps = self.stable_count * (self.epsilon * 0.5) + \
                    self.unstable_count * self.epsilon
        return total_eps


class AdaptiveStableRelease:
    """
    自适应稳定发布
    
    根据历史答案动态调整策略。
    """
    
    def __init__(self, epsilon, sensitivity, max_queries):
        """
        初始化
        
        参数:
            epsilon: 总隐私预算
            sensitivity: 敏感性
            max_queries: 最大查询数
        """
        self.epsilon = epsilon
        self.sensitivity = sensitivity
        self.max_queries = max_queries
        self.remaining_epsilon = epsilon
        self.query_count = 0
        self.results = []
        self.history_true = []
        self.history_noisy = []
    
    def answer_next(self, true_answer):
        """
        自适应回答下一个查询
        
        使用剩余预算的一部分。
        """
        if self.query_count >= self.max_queries:
            return None, False, 0
        
        if self.remaining_epsilon <= 0:
            return None, False, 0
        
        # 根据当前状态计算ε使用量
        # 如果答案变化大，使用更多预算
        eps_this_query = self.epsilon / self.max_queries
        
        if self.query_count > 0:
            prev = self.history_true[-1]
            change = abs(true_answer - prev)
            # 变化大时增加预算（但不超过剩余）
            change_ratio = min(change / self.sensitivity, 2.0)
            eps_this_query = min(eps_this_query * change_ratio, self.remaining_epsilon)
        
        scale = self.sensitivity / eps_this_query
        noise = laplace_noise(scale)
        noisy_answer = true_answer + noise
        
        self.remaining_epsilon -= eps_this_query
        self.query_count += 1
        self.history_true.append(true_answer)
        self.history_noisy.append(noisy_answer)
        self.results.append((true_answer, noisy_answer, eps_this_query))
        
        return noisy_answer, True, eps_this_query


def stable_release_with_stopping(queries, epsilon, sensitivity, 
                                  stop_after_stable=5, 
                                  stop_after_unstable=3):
    """
    带停止条件的稳定发布
    
    参数:
        queries: 查询生成函数列表或生成器
        epsilon: 隐私预算
        sensitivity: 敏感性
        stop_after_stable: 连续稳定答案达到此数时停止
        stop_after_unstable: 连续不稳定答案达到此数时停止
    
    返回:
        收集到的稳定答案列表
    """
    scale = sensitivity / epsilon
    
    answers = []
    consecutive_stable = 0
    consecutive_unstable = 0
    prev_answer = None
    
    for true_answer in queries:
        # 添加噪声
        noise = laplace_noise(scale)
        noisy_answer = true_answer + noise
        
        # 判断稳定性
        if prev_answer is None:
            is_stable = True
        else:
            diff = abs(true_answer - prev_answer)
            is_stable = diff <= sensitivity
        
        if is_stable:
            consecutive_stable += 1
            consecutive_unstable = 0
        else:
            consecutive_unstable += 1
            consecutive_stable = 0
        
        answers.append({
            'true': true_answer,
            'noisy': noisy_answer,
            'stable': is_stable
        })
        
        prev_answer = true_answer
        
        # 检查停止条件
        if consecutive_stable >= stop_after_stable:
            break
        if consecutive_unstable >= stop_after_unstable:
            break
    
    return answers


class ConfidenceBasedStopping:
    """
    基于置信度的停止机制
    
    当答案的置信区间足够窄时停止。
    """
    
    def __init__(self, epsilon, sensitivity, confidence_level=0.95):
        """
        初始化
        
        参数:
            epsilon: 隐私预算
            sensitivity: 敏感性
            confidence_level: 目标置信水平
        """
        self.epsilon = epsilon
        self.sensitivity = sensitivity
        self.confidence_level = confidence_level
        self.scale = sensitivity / epsilon
        self.answers = []
    
    def add_query(self, true_answer):
        """
        添加查询并检查是否应该停止
        
        参数:
            true_answer: 真实答案
        
        返回:
            (noisy_answer, should_stop)
        """
        noise = laplace_noise(self.scale)
        noisy_answer = true_answer + noise
        self.answers.append(noisy_answer)
        
        # 计算置信区间
        # Laplace分布的γ分位数
        gamma = 1 - (1 - confidence_level) / 2
        z = -math.log(2 * (1 - gamma)) * self.scale
        
        mean_answer = np.mean(self.answers)
        # 标准误差
        se = np.std(self.answers) / math.sqrt(len(self.answers)) if len(self.answers) > 1 else z
        
        # 置信区间宽度
        ci_width = 2 * z * self.scale
        
        # 停止条件：区间宽度小于某个阈值
        should_stop = len(self.answers) >= 5 and ci_width < self.sensitivity * 0.1
        
        return noisy_answer, should_stop
    
    def get_final_answer(self):
        """
        获取最终答案(带噪声的平均值)
        """
        if not self.answers:
            return None
        return np.mean(self.answers)


if __name__ == "__main__":
    # 测试稳定发布
    
    print("=" * 60)
    print("稳定发布 (Stable Release) 测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1: 基本稳定发布
    print("\n[测试1] 基本稳定发布机制")
    
    epsilon = 1.0
    sensitivity = 1.0
    sr = StableRelease(epsilon, sensitivity, stability_threshold=1.0)
    
    # 模拟查询序列(答案相对稳定)
    query_answers = [10, 11, 10.5, 11.2, 10.8, 11, 10.9, 11.1, 10.7, 11]
    
    print(f"  ε={epsilon}, Δ={sensitivity}, 稳定性阈值=1.0")
    print(f"  查询序列: {query_answers}")
    print()
    
    results = []
    prev = None
    for i, ans in enumerate(query_answers):
        noisy, is_stable, cost = sr.answer_query(ans, prev)
        results.append((ans, noisy, is_stable))
        prev = ans
        status = "稳定" if is_stable else "不稳定"
        print(f"  Q{i+1}: 真值={ans:>5.1f}, 噪声值={noisy:>6.2f}, {status}, ε消耗={cost:.3f}")
    
    print(f"\n  总ε消耗: {sr.get_total_privacy_cost():.3f}")
    print(f"  稳定答案: {sr.stable_count}, 不稳定答案: {sr.unstable_count}")
    
    # 测试2: 自适应稳定发布
    print("\n[测试2] 自适应稳定发布")
    
    np.random.seed(42)
    
    epsilon = 2.0
    sensitivity = 1.0
    max_q = 10
    
    adaptive = AdaptiveStableRelease(epsilon, sensitivity, max_q)
    
    # 变化较大的查询序列
    query_answers = [10, 25, 15, 30, 20, 35, 25, 40, 30, 45]
    
    print(f"  总ε={epsilon}, 最大查询数={max_q}")
    print(f"  查询序列: {query_answers}")
    print()
    
    for i, ans in enumerate(query_answers):
        noisy, success, cost = adaptive.answer_next(ans)
        if success:
            print(f"  Q{i+1}: 真值={ans:>2}, 噪声值={noisy:>6.2f}, ε消耗={cost:.3f}, 剩余ε={adaptive.remaining_epsilon:.3f}")
    
    print(f"\n  最终剩余ε: {adaptive.remaining_epsilon:.4f}")
    
    # 测试3: 带停止条件的稳定发布
    print("\n[测试3] 带停止条件的稳定发布")
    
    np.random.seed(42)
    
    def query_generator():
        """模拟查询生成器"""
        # 前10个相对稳定
        for _ in range(10):
            yield 50 + np.random.normal(0, 0.5)
        # 后5个不稳定
        for _ in range(5):
            yield 50 + np.random.uniform(20, 40)
    
    results = stable_release_with_stopping(
        query_generator(),
        epsilon=1.0,
        sensitivity=1.0,
        stop_after_stable=3,
        stop_after_unstable=2
    )
    
    print(f"  停止条件: 连续3个稳定 或 连续2个不稳定")
    print(f"  收集到的答案:")
    for i, r in enumerate(results):
        status = "✓稳定" if r['stable'] else "✗不稳定"
        print(f"    {i+1}: 真值={r['true']:.2f}, 噪声={r['noisy']:.2f}, {status}")
    
    # 测试4: 置信度停止机制
    print("\n[测试4] 基于置信度的停止")
    
    np.random.seed(42)
    
    confidence_stop = ConfidenceBasedStopping(
        epsilon=1.0,
        sensitivity=1.0,
        confidence_level=0.95
    )
    
    true_value = 100.0
    print(f"  真实值: {true_value}")
    print(f"  目标置信水平: 95%")
    print()
    
    for i in range(20):
        noisy, should_stop = confidence_stop.add_query(true_value)
        mean_noisy = confidence_stop.get_final_answer()
        print(f"  查询{i+1}: 噪声值={noisy:.2f}, 当前均值={mean_noisy:.2f if mean_noisy else 'N/A'}", end="")
        if should_stop:
            print(" [停止]", end="")
        print()
        if should_stop:
            break
    
    # 测试5: 稳定性分析
    print("\n[测试5] 稳定性对噪声精度的影响")
    
    np.random.seed(42)
    
    epsilon = 1.0
    sensitivity = 1.0
    
    print(f"  ε={epsilon}, Δ={sensitivity}")
    print(f"  {'类型':>10} | {'平均MSE':>12} | {'最大误差':>12}")
    print("  " + "-" * 40)
    
    # 稳定查询
    stable_answers = [10 + np.random.normal(0, 0.1) for _ in range(1000)]
    sr_stable = StableRelease(epsilon, sensitivity)
    for ans in stable_answers:
        sr_stable.answer_query(ans)
    
    stable_mse = np.mean([(r[1]-r[0])**2 for r in sr_stable.answers])
    stable_max_err = max(abs(r[1]-r[0]) for r in sr_stable.answers)
    print(f"  {'稳定查询':>10} | {stable_mse:>12.4f} | {stable_max_err:>12.4f}")
    
    # 不稳定查询
    np.random.seed(42)
    unstable_answers = [10 + np.random.uniform(-5, 5) for _ in range(1000)]
    sr_unstable = StableRelease(epsilon, sensitivity)
    for ans in unstable_answers:
        sr_unstable.answer_query(ans)
    
    unstable_mse = np.mean([(r[1]-r[0])**2 for r in sr_unstable.answers])
    unstable_max_err = max(abs(r[1]-r[0]) for r in sr_unstable.answers)
    print(f"  {'不稳定查询':>10} | {unstable_mse:>12.4f} | {unstable_max_err:>12.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成 - 稳定性可减少不必要的隐私预算消耗")
    print("=" * 60)
