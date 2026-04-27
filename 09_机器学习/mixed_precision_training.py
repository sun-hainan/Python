# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / mixed_precision_training

本文件实现 mixed_precision_training 相关的算法功能。
"""

import numpy as np


class MixedPrecisionTrainer:
    """
    混合精度训练器概念实现

    参数:
        model: 模型
        optimizer: 优化器
        loss_scaling_factor: 初始损失缩放因子
    """

    def __init__(self, model, optimizer, loss_scaling_factor=2**10):
        self.model = model
        self.optimizer = optimizer
        self.loss_scaling_factor = loss_scaling_factor
        self.fp16_weights = {}  # FP16权重副本
        self.fp32_weights = {}   # FP32主权重

        # 初始化权重副本
        for name, param in model.get_weights().items():
            self.fp32_weights[name] = param.astype(np.float32)
            self.fp16_weights[name] = param.astype(np.float16)

    def _to_fp16(self, X):
        """转换为FP16"""
        return X.astype(np.float16)

    def _to_fp32(self, X):
        """转换为FP32"""
        return X.astype(np.float32)

    def _check_overflow(self, grad):
        """检查梯度是否溢出"""
        return np.any(np.isinf(grad)) or np.any(np.isnan(grad))

    def train_step(self, X, y):
        """
        单步训练

        流程:
        1. FP16前向传播
        2. 损失缩放
        3. FP16反向传播
        4. 检查溢出
        5. 缩放回FP32梯度
        6. FP32权重更新
        """
        # 1. 转换为FP16
        X_fp16 = self._to_fp16(X)

        # 2. FP16前向传播
        y_pred_fp16 = self.model.forward_fp16(X_fp16)

        # 3. 计算损失并缩放
        loss = self._compute_loss(y_pred_fp16, y)
        loss_scaled = loss * self.loss_scaling_factor

        # 4. FP16反向传播
        grads_fp16 = self.model.backward_fp16(y_pred_fp16, y)

        # 5. 检查溢出
        has_overflow = any(self._check_overflow(g) for g in grads_fp16.values())

        if has_overflow:
            # 溢出：降低缩放因子，跳过更新
            self.loss_scaling_factor = max(1.0, self.loss_scaling_factor / 2)
            return loss, True  # 返回overflow标志
        else:
            # 6. 缩放回FP32并更新
            grads_fp32 = {k: g.astype(np.float32) / self.loss_scaling_factor
                         for k, g in grads_fp16.items()}

            # FP32权重更新
            self.optimizer.update(self.fp32_weights, grads_fp32)

            # 同步FP16权重
            for name in self.fp16_weights:
                self.fp16_weights[name] = self.fp32_weights[name].astype(np.float16)

            # 动态调整缩放因子
            self.loss_scaling_factor = min(2**15, self.loss_scaling_factor * 1.01)

            return loss, False

    def _compute_loss(self, y_pred, y_true):
        """计算交叉熵损失"""
        eps = 1e-10
        return -np.mean(y_true * np.log(y_pred + eps))


class LossScaler:
    """
    动态损失缩放器

    策略：
    - 如果连续N步无溢出，增加缩放因子
    - 如果发生溢出，降低缩放因子
    """

    def __init__(self, init_scale=2**10, scale_factor=2.0, lookback=2000):
        self.scale = init_scale
        self.scale_factor = scale_factor
        self.lookback = lookback
        self.best_scale = init_scale
        self.steps_since_last_overflow = 0
        self.overflow_count = 0

    def update(self, has_overflow):
        """
        更新缩放因子

        参数:
            has_overflow: 是否有溢出
        """
        if has_overflow:
            # 溢出：大幅降低
            self.scale = max(1.0, self.scale / 2)
            self.steps_since_last_overflow = 0
            self.overflow_count += 1
        else:
            self.steps_since_last_overflow += 1
            # 连续稳定：尝试增加缩放因子
            if self.steps_since_last_overflow >= self.lookback:
                self.scale = min(self.scale * self.scale_factor, 2**15)
                self.best_scale = self.scale
                self.steps_since_last_overflow = 0

        return self.scale


def demonstrate_mixed_precision():
    """演示混合精度训练概念"""
    np.random.seed(42)

    print("=" * 60)
    print("混合精度训练概念演示")
    print("=" * 60)

    # FP16数值范围演示
    print("\n1. 浮点精度对比:")
    print(f"   FP16:")
    print(f"     最小正数: {np.finfo(np.float16).tiny}")
    print(f"     最大值: {np.finfo(np.float16).max}")
    print(f"     精度(小数位数): {np.finfo(np.float16).precision}")
    print(f"   FP32:")
    print(f"     最小正数: {np.finfo(np.float32).tiny}")
    print(f"     最大值: {np.finfo(np.float32).max}")
    print(f"     精度: {np.finfo(np.float32).precision}")

    # 内存占用对比
    print("\n2. 内存占用对比:")
    n_elements = 1000000
    bytes_fp16 = n_elements * 2
    bytes_fp32 = n_elements * 4
    print(f"   {n_elements} 元素:")
    print(f"     FP16: {bytes_fp16 / 1024 / 1024:.2f} MB")
    print(f"     FP32: {bytes_fp32 / 1024 / 1024:.2f} MB")
    print(f"     节省: {(bytes_fp32 - bytes_fp16) / bytes_fp32 * 100:.1f}%")

    # 损失缩放演示
    print("\n3. 损失缩放效果:")
    small_grad = np.float16(1e-8)
    scaled_grad = small_grad * 2**10
    print(f"   原始梯度: {small_grad}")
    print(f"   缩放后: {scaled_grad} (避免下溢)")

    # 溢出检测演示
    print("\n4. 溢出检测:")
    large_value = np.float16(65500)
    try:
        result = large_value * 10
        print(f"   FP16 大值乘法: {large_value} * 10 = {result} (溢出!)")
    except:
        print(f"   检测到溢出")

    # 动态缩放演示
    print("\n5. 动态损失缩放:")
    scaler = LossScaler(init_scale=1024)

    # 模拟训练
    overflow_history = [False, False, True, False, False, False, False]
    for step, has_overflow in enumerate(overflow_history):
        scale = scaler.update(has_overflow)
        status = "溢出!" if has_overflow else "正常"
        print(f"   Step {step + 1}: 缩放因子={scale:.0f}, 状态={status}")

    print("\n6. 混合精度训练流程:")
    print("   ┌─────────────────────────────────────────┐")
    print("   │ 1. FP32权重 -> FP16权重                 │")
    print("   │ 2. FP16前向传播                        │")
    print("   │ 3. 损失 * 缩放因子                     │")
    print("   │ 4. FP16反向传播                        │")
    print("   │ 5. 检查溢出                            │")
    print("   │   ├─ 溢出: 降低因子，跳过              │")
    print("   │   └─ 正常: 梯度/缩放因子，FP32更新     │")
    print("   │ 6. FP32权重更新                       │")
    print("   │ 7. 同步回FP16                         │")
    print("   └─────────────────────────────────────────┘")


if __name__ == "__main__":
    demonstrate_mixed_precision()
