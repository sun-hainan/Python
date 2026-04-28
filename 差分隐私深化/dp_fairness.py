"""
差分隐私与公平性 (Differential Privacy & Fairness)
==================================================

算法原理:
---------
差分隐私（DP）通过向数据或算法输出添加精心校准的随机噪声来保护个体隐私，
同时试图保持统计特性。在公平性场景中，DP可用于：
1. 公平分类：确保不同敏感群体（如不同性别/种族）获得相似准确率
2. 重采样去偏：通过DP机制平衡训练数据，减少算法偏见
3. 歧视检测：量化敏感属性与决策之间的统计依赖性

核心技术：
- 敏感性分析：计算单条记录对输出的最大影响
- 噪声注入：Laplace或Gaussian机制
- 公平性约束：在优化目标中加入多样性约束

时间复杂度: O(n * d) 其中n为样本数，d为特征维度
空间复杂度: O(n * d) 用于存储数据和中间结果

应用场景:
--------
- 贷款审批系统：确保不同群体获得公平批准率
- 招聘筛选系统：去除性别/年龄歧视
- 刑事司法系统：减少种族偏见
- 广告投放系统：避免性别/年龄定向歧视
"""

import numpy as np
from numpy.random import Laplace


def laplace_mechanism(sensitivity, epsilon):
    """
    Laplace机制：向数值结果添加Laplace噪声实现差分隐私
    
    参数:
        sensitivity (float): 函数的敏感性（单条记录改变的最大影响）
        epsilon (float): 隐私预算参数，越小隐私保护越强
    
    返回:
        lambda: 一个可以添加噪声的函数
    """
    # 计算噪声尺度参数，敏感性越大或epsilon越小，噪声越大
    scale = sensitivity / epsilon
    
    def add_noise(value):
        # 从Laplace分布采样噪声并添加到原值
        noise = Laplace(scale=scale)
        return value + noise
    
    return add_noise


def fair_classifier_proportional_pred(data, sensitive_attr, epsilon=1.0):
    """
    公平分类器 - 比例预测方法
    
    原理：在差分隐私约束下，通过调整不同群体的预测概率来平衡准确率
    对于每个群体，计算其真实正类率（true positive rate），然后在
    满足DP约束的条件下进行校正
    
    参数:
        data: 包含特征的numpy数组，格式为(n_samples, n_features)
        sensitive_attr: 敏感属性数组，0/1表示两个群体
        epsilon: 隐私预算
    
    返回:
        adjusted_proba: 调整后的预测概率
    """
    n = len(sensitive_attr)  # 样本总数
    
    # 分离两个群体的样本索引
    group_0_idx = np.where(sensitive_attr == 0)[0]
    group_1_idx = np.where(sensitive_attr == 1)[0]
    
    # 计算两个群体的基础正类率（使用拉普拉斯机制添加噪声）
    # 敏感性为1/n，因为添加或移除一个样本最多影响1/n的比例
    noise_func = laplace_mechanism(1.0 / n, epsilon)
    
    # 计算各群体的正类比例估计
    base_rate_0 = len(group_0_idx) / n
    base_rate_1 = len(group_1_idx) / n
    
    # 添加差分隐私噪声
    noisy_rate_0 = noise_func(base_rate_0)
    noisy_rate_1 = noise_func(base_rate_1)
    
    # 比例因子用于平衡两个群体的预测概率
    # 确保两个群体的正类预测概率与它们在数据中的真实比例相关
    if noisy_rate_0 > 0 and noisy_rate_1 > 0:
        ratio = min(noisy_rate_0, noisy_rate_1) / max(noisy_rate_0, noisy_rate_1)
    else:
        ratio = 1.0
    
    # 返回调整后的概率（这里返回群体比例作为示例）
    return np.array([noisy_rate_0, noisy_rate_1]), ratio


def resampling_debias(data, labels, sensitive_attr, epsilon=1.0, target_ratio=None):
    """
    重采样去偏方法
    
    原理：通过差分隐私机制确定各群体应保留的比例，然后进行重采样，
    以减少敏感属性对预测结果的偏见影响
    
    参数:
        data: 特征数据数组
        labels: 标签数组
        sensitive_attr: 敏感属性（0/1群体标识）
        epsilon: 隐私预算
        target_ratio: 目标平衡比例，默认None表示完全平衡
    
    返回:
        resampled_data, resampled_labels, resampled_sensitive: 重采样后的数据
    """
    n = len(labels)  # 样本总数
    
    # 分离两个群体的索引
    group_0_idx = np.where(sensitive_attr == 0)[0]
    group_1_idx = np.where(sensitive_attr == 1)[0]
    
    # 计算两个群体的大小
    n_0 = len(group_0_idx)
    n_1 = len(group_1_idx)
    
    # 使用Laplace机制估计群体比例
    noise_func = laplace_mechanism(1.0 / n, epsilon)
    
    # 添加噪声后的比例
    ratio_0 = noise_func(n_0 / n)
    ratio_1 = noise_func(n_1 / n)
    
    # 计算目标采样比例（使两个群体在目标空间中等价）
    if target_ratio is None:
        # 完全平衡：各群体在采样后占50%
        # 根据带噪声的比例计算采样权重
        total_noisy = ratio_0 + ratio_1
        target_0 = 0.5 if total_noisy == 0 else ratio_0 / total_noisy
        target_1 = 1.0 - target_0
    else:
        target_0 = target_ratio
        target_1 = 1.0 - target_ratio
    
    # 计算每个群体需要采样的数量
    target_n_0 = int(n * target_0)
    target_n_1 = int(n * target_1)
    
    # 从各群体中采样（使用有放回采样）
    np.random.seed(42)  # 确保可复现性
    
    # 从群体0采样
    if target_n_0 <= n_0:
        sampled_0 = np.random.choice(group_0_idx, size=target_n_0, replace=False)
    else:
        sampled_0 = np.random.choice(group_0_idx, size=target_n_0, replace=True)
    
    # 从群体1采样
    if target_n_1 <= n_1:
        sampled_1 = np.random.choice(group_1_idx, size=target_n_1, replace=False)
    else:
        sampled_1 = np.random.choice(group_1_idx, size=target_n_1, replace=True)
    
    # 合并采样结果
    sampled_idx = np.concatenate([sampled_0, sampled_1])
    
    return data[sampled_idx], labels[sampled_idx], sensitive_attr[sampled_idx]


def discrimination_detection(data, decision_attr, sensitive_attr, epsilon=0.5):
    """
    歧视检测 - 通过差分隐私机制检测敏感属性与决策之间的统计依赖性
    
    原理：计算敏感群体与非敏感群体在决策上的差异，
    使用DP机制确保个体隐私不被泄露
    
    参数:
        data: 完整数据集
        decision_attr: 决策结果数组（0/1）
        sensitive_attr: 敏感属性数组（0/1）
        epsilon: 隐私预算
    
    返回:
        discrimination_score: 歧视程度评分（0-1之间）
        is_discriminatory: 是否存在显著歧视（阈值0.1）
    """
    n = len(decision_attr)  # 样本总数
    
    # 分离群体
    group_0_idx = np.where(sensitive_attr == 0)[0]
    group_1_idx = np.where(sensitive_attr == 1)[0]
    
    # 计算两个群体的决策率（正类比例）
    rate_0 = np.mean(decision_attr[sensitive_attr == 0]) if len(group_0_idx) > 0 else 0
    rate_1 = np.mean(decision_attr[sensitive_attr == 1]) if len(group_1_idx) > 0 else 0
    
    # 计算决策率差异的敏感性：单条记录最多影响1/n
    sensitivity = 1.0 / n
    
    # 使用Laplace机制添加噪声
    noise_func = laplace_mechanism(sensitivity, epsilon)
    
    noisy_rate_0 = noise_func(rate_0)
    noisy_rate_1 = noise_func(rate_1)
    
    # 计算歧视程度（两个群体决策率的绝对差异）
    discrimination_score = abs(noisy_rate_0 - noisy_rate_1)
    
    # 判断是否存在显著歧视（差异超过阈值0.1）
    is_discriminatory = discrimination_score > 0.1
    
    return discrimination_score, is_discriminatory


def demographic_parity_audit(data, predictions, sensitive_attr, epsilon=1.0):
    """
    人口均等审计 - 检查预测结果是否满足人口均等性
    
    人口均等性要求：正类预测率在不同群体间相等
    P(Y=1|A=0) ≈ P(Y=1|A=1)
    
    参数:
        data: 特征数据
        predictions: 模型预测结果（0/1）
        sensitive_attr: 敏感属性
        epsilon: 隐私预算
    
    返回:
        pp_diff: 人口均等性差异（带噪声）
        passes_audit: 是否通过审计（差异<0.1）
    """
    n = len(predictions)  # 样本总数
    noise_func = laplace_mechanism(2.0 / n, epsilon)  # 敏感性为2/n（两个比例的差异）
    
    # 计算各群体的正类预测率
    rate_0 = np.mean(predictions[sensitive_attr == 0])
    rate_1 = np.mean(predictions[sensitive_attr == 1])
    
    # 添加噪声
    noisy_rate_0 = noise_func(rate_0)
    noisy_rate_1 = noise_func(rate_1)
    
    # 计算差异
    pp_diff = abs(noisy_rate_0 - noisy_rate_1)
    
    # 审计判定
    passes_audit = pp_diff < 0.1
    
    return pp_diff, passes_audit


# ============== 测试代码 ==============
if __name__ == "__main__":
    print("=" * 60)
    print("差分隐私与公平性 - 测试演示")
    print("=" * 60)
    
    # 生成模拟数据
    np.random.seed(42)  # 可复现性
    
    n_samples = 1000  # 样本数量
    
    # 生成敏感属性：假设群体0占60%，群体1占40%
    sensitive_attr = np.random.binomial(1, 0.4, n_samples)
    
    # 生成特征数据（简化模拟：2个特征）
    feature_1 = np.random.randn(n_samples) + 0.5 * sensitive_attr  # 与敏感属性相关
    feature_2 = np.random.randn(n_samples)
    data = np.column_stack([feature_1, feature_2])
    
    # 生成标签（存在一定偏见）
    # 真实标签与敏感属性和相关特征都有关联
    true_labels = (feature_1 > 0.5 + 0.3 * sensitive_attr).astype(int)
    
    print(f"\n数据集大小: {n_samples} 样本")
    print(f"群体0数量: {np.sum(sensitive_attr == 0)}")
    print(f"群体1数量: {np.sum(sensitive_attr == 1)}")
    print(f"标签分布: 正类 {np.sum(true_labels)} ({np.sum(true_labels)/n_samples:.1%})")
    
    # 测试1：公平分类器
    print("\n" + "-" * 40)
    print("测试1: 公平分类器（比例预测）")
    print("-" * 40)
    
    rates, ratio = fair_classifier_proportional_pred(data, sensitive_attr, epsilon=1.0)
    print(f"群体0估计正类率: {rates[0]:.4f}")
    print(f"群体1估计正类率: {rates[1]:.4f}")
    print(f"平衡比例: {ratio:.4f}")
    print("说明: ratio接近1表示两个群体较为平衡")
    
    # 测试2：重采样去偏
    print("\n" + "-" * 40)
    print("测试2: 重采样去偏")
    print("-" * 40)
    
    resampled_data, resampled_labels, resampled_sensitive = resampling_debias(
        data, true_labels, sensitive_attr, epsilon=1.0
    )
    
    print(f"重采样前: 群体0={np.sum(sensitive_attr==0)}, 群体1={np.sum(sensitive_attr==1)}")
    print(f"重采样后: 群体0={np.sum(resampled_sensitive==0)}, 群体1={np.sum(resampled_sensitive==1)}")
    print(f"重采样后正类比例: {np.mean(resampled_labels):.4f}")
    
    # 测试3：歧视检测
    print("\n" + "-" * 40)
    print("测试3: 歧视检测")
    print("-" * 40)
    
    # 模拟一个带有偏见的决策（群体1更容易被预测为正类）
    biased_decisions = (true_labels | (sensitive_attr & np.random.binomial(1, 0.3, n_samples))).astype(int)
    
    disc_score, is_disc = discrimination_detection(
        data, biased_decisions, sensitive_attr, epsilon=0.5
    )
    print(f"歧视评分: {disc_score:.4f}")
    print(f"存在显著歧视: {'是' if is_disc else '否'}")
    
    # 测试4：人口均等审计
    print("\n" + "-" * 40)
    print("测试4: 人口均等审计")
    print("-" * 40)
    
    # 模拟模型预测（带有偏见）
    model_predictions = (feature_1 + 0.3 * sensitive_attr > 0.8).astype(int)
    
    pp_diff, passes = demographic_parity_audit(
        data, model_predictions, sensitive_attr, epsilon=1.0
    )
    print(f"人口均等性差异: {pp_diff:.4f}")
    print(f"通过审计: {'是' if passes else '否'}")
    
    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)