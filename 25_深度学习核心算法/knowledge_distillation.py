# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / knowledge_distillation

本文件实现 knowledge_distillation 相关的算法功能。
"""

import numpy as np


def temperature_softmax(logits, temperature=1.0):
    """
    温度缩放Softmax：放大或缩小logits的分布
    
    参数:
        logits: 模型输出的logits (batch_size, num_classes)
        temperature: 温度参数 T>1时分布更平滑，T<1时更尖锐
    返回:
        probs: 温度缩放后的概率分布
    """
    scaled_logits = logits / temperature
    # 数值稳定化
    scaled_logits = scaled_logits - np.max(scaled_logits, axis=1, keepdims=True)
    exp_logits = np.exp(scaled_logits)
    probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
    return probs


def compute_distillation_loss(student_logits, teacher_probs, temperature=1.0, alpha=0.5):
    """
    计算蒸馏损失：结合硬标签和软标签损失
    
    损失函数 = α * KL(student_soft || teacher_soft) + (1-α) * CE(student || hard_labels)
    
    参数:
        student_logits: 学生模型的logits
        teacher_probs: 教师模型的软标签概率
        temperature: 温度参数
        alpha: 软标签损失的权重
    返回:
        loss: 蒸馏总损失
        soft_loss: 软标签损失
        hard_loss: 硬标签损失
    """
    # 硬标签损失（使用普通softmax的交叉熵）
    hard_loss = cross_entropy_loss(student_logits, teacher_probs)
    
    # 软标签损失（KL散度，使用温度缩放）
    student_soft = temperature_softmax(student_logits, temperature)
    
    # KL(student || teacher) = sum(student * log(student/teacher))
    # 乘以T^2是因为前面的scaled_logits除以了T
    soft_loss = kl_divergence(student_soft, teacher_probs) * (temperature ** 2)
    
    # 加权组合
    loss = alpha * soft_loss + (1 - alpha) * hard_loss
    
    return loss, soft_loss, hard_loss


def kl_divergence(p, q, eps=1e-8):
    """
    计算KL散度 KL(p || q)
    
    参数:
        p: 目标分布（学生）
        q: 参考分布（教师）
    返回:
        kl: KL散度（标量）
    """
    p = np.clip(p, eps, 1.0)
    q = np.clip(q, eps, 1.0)
    return np.sum(p * np.log(p / q), axis=1).mean()


def cross_entropy_loss(logits, targets):
    """交叉熵损失（硬标签版本）"""
    probs = np.exp(logits - np.max(logits, axis=1, keepdims=True))
    probs = probs / np.sum(probs, axis=1, keepdims=True)
    return -np.sum(targets * np.log(probs + 1e-8), axis=1).mean()


class KnowledgeDistiller:
    """
    知识蒸馏器
    
    参数:
        temperature: 温度参数（默认4.0，越高软标签越平滑）
        alpha: 软标签损失权重（默认0.7）
        hard_label_weight: 硬标签损失权重（默认0.3）
    """
    
    def __init__(self, temperature=4.0, alpha=0.7):
        self.temperature = temperature
        self.alpha = alpha
    
    def distill(self, student_logits, teacher_logits, hard_labels=None):
        """
        执行知识蒸馏
        
        参数:
            student_logits: 学生模型logits
            teacher_logits: 教师模型logits
            hard_labels: 真实标签（可选，有则计算硬标签损失）
        返回:
            total_loss: 总蒸馏损失
            metrics: 包含各项损失的字典
        """
        # 教师软标签（使用温度缩放）
        teacher_probs = temperature_softmax(teacher_logits, self.temperature)
        
        # 学生软标签
        student_soft = temperature_softmax(student_logits, self.temperature)
        
        # 软标签损失（KL散度）
        soft_loss = kl_divergence(student_soft, teacher_probs) * (self.temperature ** 2)
        
        metrics = {'soft_loss': soft_loss}
        
        if hard_labels is not None:
            # 硬标签损失
            hard_loss = cross_entropy_loss(student_logits, hard_labels)
            total_loss = self.alpha * soft_loss + (1 - self.alpha) * hard_loss
            metrics['hard_loss'] = hard_loss
        else:
            total_loss = soft_loss
        
        metrics['total_loss'] = total_loss
        
        return total_loss, metrics
    
    def compute_teacher_temperature(self, teacher_logits):
        """
        评估教师模型输出的"硬度"，帮助选择合适温度
        
        返回:
            entropy: 平均熵（越高说明分布越均匀，越需要高温度）
        """
        probs = temperature_softmax(teacher_logits, temperature=1.0)
        entropy = -np.sum(probs * np.log(probs + 1e-8), axis=1).mean()
        return entropy


class FeatureDistiller:
    """
    特征蒸馏：将教师中间层的特征迁移到学生
    
    参数:
        feature_dim_s: 学生特征维度
        feature_dim_t: 教师特征维度
    """
    
    def __init__(self, feature_dim_s, feature_dim_t):
        self.feature_dim_s = feature_dim_s
        self.feature_dim_t = feature_dim_t
        
        # 适配层：将学生特征映射到与教师相同维度
        if feature_dim_s != feature_dim_t:
            self.adapter = np.random.randn(feature_dim_s, feature_dim_t) * 0.01
        else:
            self.adapter = None
    
    def forward(self, student_features, teacher_features):
        """
        计算特征蒸馏损失
        
        参数:
            student_features: 学生特征 (batch, dim_s)
            teacher_features: 教师特征 (batch, dim_t)
        返回:
            loss: 特征蒸馏损失
        """
        if self.adapter is not None:
            # 使用适配层映射维度
            student_mapped = student_features @ self.adapter
        else:
            student_mapped = student_features
        
        # MSE损失（也可以使用L1损失）
        loss = np.mean((student_mapped - teacher_features) ** 2)
        
        return loss


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("知识蒸馏测试")
    print("=" * 55)
    
    batch_size = 32
    num_classes = 10
    
    # 模拟教师和学生logits
    teacher_logits = np.random.randn(batch_size, num_classes)
    student_logits = np.random.randn(batch_size, num_classes)
    
    # 模拟硬标签
    hard_labels = np.zeros((batch_size, num_classes))
    hard_labels[np.arange(batch_size), np.random.randint(0, num_classes, batch_size)] = 1.0
    
    # 测试温度缩放
    print("\n--- 温度缩放效果 ---")
    base_probs = temperature_softmax(teacher_logits, temperature=1.0)
    print(f"原始概率分布（温度=1）: {base_probs[0].round(3)}")
    print(f"概率熵: {-np.sum(base_probs[0] * np.log(base_probs[0] + 1e-8)):.4f}")
    
    for temp in [1.0, 2.0, 4.0, 8.0]:
        scaled_probs = temperature_softmax(teacher_logits, temperature=temp)
        entropy = -np.sum(scaled_probs[0] * np.log(scaled_probs[0] + 1e-8))
        print(f"温度={temp}: 熵={entropy:.4f}, 最大概率={scaled_probs[0].max():.4f}")
    
    # 测试知识蒸馏
    print("\n--- 知识蒸馏损失 ---")
    distiller = KnowledgeDistiller(temperature=4.0, alpha=0.7)
    
    total_loss, metrics = distiller.distill(student_logits, teacher_logits, hard_labels)
    
    print(f"总损失: {total_loss:.4f}")
    print(f"软标签损失: {metrics['soft_loss']:.4f}")
    print(f"硬标签损失: {metrics['hard_loss']:.4f}")
    
    # 测试不同alpha的影响
    print("\n--- 不同alpha值的影响 ---")
    for alpha in [0.0, 0.3, 0.5, 0.7, 1.0]:
        dist = KnowledgeDistiller(temperature=4.0, alpha=alpha)
        _, m = dist.distill(student_logits, teacher_logits, hard_labels)
        print(f"  alpha={alpha}: soft_loss={m['soft_loss']:.4f}, hard_loss={m['hard_loss']:.4f}")
    
    # 测试特征蒸馏
    print("\n--- 特征蒸馏 ---")
    feat_distiller = FeatureDistiller(feature_dim_s=128, feature_dim_t=256)
    
    student_feat = np.random.randn(batch_size, 128)
    teacher_feat = np.random.randn(batch_size, 256)
    
    feat_loss = feat_distiller.forward(student_feat, teacher_feat)
    print(f"特征蒸馏损失: {feat_loss:.4f}")
    
    # 测试教师温度评估
    print("\n--- 教师模型温度评估 ---")
    entropy = distiller.compute_teacher_temperature(teacher_logits)
    print(f"教师输出熵: {entropy:.4f}")
    if entropy > 1.5:
        print("建议使用较高温度（>=4）来软化分布")
    else:
        print("分布已经比较柔和，可以尝试较低温度（<=2）")
    
    print("\n知识蒸馏测试完成！")
