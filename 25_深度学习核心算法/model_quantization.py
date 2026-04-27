# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / model_quantization

本文件实现 model_quantization 相关的算法功能。
"""

import numpy as np


# ============================
# 量化基础函数
# ============================

def symmetric_quantize(values, bits=8):
    """
    对称量化：将float32映射到整数
    
    公式: q = round(values / scale)
    其中 scale = max(|values|) / (2^(bits-1) - 1)
    
    参数:
        values: 待量化浮点数组
        bits: 量化位数（默认8位）
    返回:
        quantized: 整数数组
        scale: 量化缩放因子
    """
    max_val = np.max(np.abs(values))
    if max_val == 0:
        max_val = 1.0
    
    # 计算缩放因子
    qmax = 2 ** (bits - 1) - 1
    scale = max_val / qmax
    
    # 量化
    quantized = np.round(values / scale)
    quantized = np.clip(quantized, -qmax - 1, qmax)
    
    return quantized.astype(np.int8), scale


def symmetric_dequantize(quantized, scale):
    """
    反量化：将整数还原为浮点
    
    公式: values = q * scale
    """
    return quantized.astype(np.float32) * scale


def asymmetric_quantize(values, bits=8):
    """
    非对称量化：允许零点偏移
    适用于数值分布不关于0对称的情况（如ReLU输出）
    
    参数:
        values: 待量化浮点数组
        bits: 量化位数
    返回:
        quantized: 整数数组
        scale: 缩放因子
        zero_point: 零点
    """
    min_val = np.min(values)
    max_val = np.max(values)
    
    qmin, qmax = 0, 2 ** bits - 1
    
    scale = (max_val - min_val) / (qmax - qmin) if max_val != min_val else 1.0
    zero_point = qmin - min_val / scale if scale != 0 else 0.0
    zero_point = int(np.round(np.clip(zero_point, qmin, qmax)))
    
    quantized = np.round(values / scale + zero_point)
    quantized = np.clip(quantized, qmin, qmax).astype(np.uint8)
    
    return quantized, scale, zero_point


def asymmetric_dequantize(quantized, scale, zero_point):
    """非对称反量化"""
    return (quantized.astype(np.float32) - zero_point) * scale


# ============================
# 量化层
# ============================

class QuantizedLinear:
    """
    量化全连接层
    
    参数:
        weight: 原始浮点权重
        bias: 偏置（可选）
        bits_weight: 权重量化位数
        bits_activation: 激活值量化位数
    """
    
    def __init__(self, weight, bias=None, bits_weight=8, bits_activation=8):
        self.weight_fp32 = weight.astype(np.float32)
        self.bias_fp32 = bias.astype(np.float32) if bias is not None else None
        self.bits_weight = bits_weight
        self.bits_activation = bits_activation
        
        # 离线量化权重
        self.weight_q, self.weight_scale = symmetric_quantize(self.weight_fp32, bits_weight)
        self.weight_dq = symmetric_dequantize(self.weight_q, self.weight_scale)
    
    def forward(self, x, quantize_activation=True):
        """
        前向传播
        
        参数:
            x: 输入浮点张量 (batch, in_features)
            quantize_activation: 是否对输出进行动态量化
        返回:
            output: 浮点输出
            output_q: 量化输出（如果quantize_activation=True）
            output_scale: 输出缩放因子（如果quantize_activation=True）
        """
        # 反量化权重后计算
        output = x @ self.weight_dq
        if self.bias_fp32 is not None:
            output += self.bias_fp32
        
        if quantize_activation:
            # 动态量化输出
            output_q, output_scale = symmetric_quantize(output, self.bits_activation)
            return output, output_q, output_scale
        return output, None, None


class DynamicQuantizedLinear:
    """
    动态量化线性层（运行时量化）
    权重在初始化时量化存储，激活值在运行时动态量化
    """
    
    def __init__(self, in_features, out_features, bias=True, bits=8):
        self.in_features = in_features
        self.out_features = out_features
        
        # 初始化权重（随机）
        self.weight_fp32 = np.random.randn(out_features, in_features).astype(np.float32) * 0.01
        self.bias_fp32 = np.zeros(out_features, dtype=np.float32) if bias else None
        
        # 量化权重
        self.weight_q, self.weight_scale = symmetric_quantize(self.weight_fp32, bits)
        self.weight_dq = symmetric_dequantize(self.weight_q, self.weight_scale)
        self.bits = bits
    
    def forward(self, x):
        """
        动态量化前向传播
        
        参数:
            x: 浮点输入 (batch, in_features)
        返回:
            output: 浮点输出
        """
        # 反量化权重后计算
        output = x @ self.weight_dq.T
        if self.bias_fp32 is not None:
            output += self.bias_fp32
        return output
    
    def quantize_and_forward(self, x):
        """
        量化前向传播（完整INT8计算路径）
        """
        # 动态量化输入
        x_q, x_scale = symmetric_quantize(x, self.bits)
        x_dq = symmetric_dequantize(x_q, x_scale)
        
        # INT8矩阵乘法（用浮点模拟）
        output = x_dq @ self.weight_dq.T
        if self.bias_fp32 is not None:
            output += self.bias_fp32
        
        # 量化输出
        output_q, output_scale = symmetric_quantize(output, self.bits)
        
        return output, output_q, output_scale, output_scale


# ============================
# FP16混合精度
# ============================

class FP16MixedPrecision:
    """
    FP16混合精度计算
    在保持关键层精度的同时，使用FP16加速计算
    """
    
    def __init__(self, master_weights):
        """
        参数:
            master_weights: 主权重副本（FP32）
        """
        self.master_weights = [w.astype(np.float16) for w in master_weights]
        self.master_weights_fp32 = [w.astype(np.float32) for w in master_weights]
    
    def to_fp16(self, values):
        """转换为FP16"""
        return values.astype(np.float16)
    
    def to_fp32(self, values):
        """转换为FP32"""
        return values.astype(np.float32)
    
    def forward_with_cast(self, x, cast_to_fp16=True):
        """带精度转换的前向传播"""
        if cast_to_fp16:
            x_fp16 = self.to_fp16(x)
            w_fp16 = self.weight_fp16 if hasattr(self, 'weight_fp16') else None
            return x_fp16, w_fp16
        return x


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("模型量化测试")
    print("=" * 55)
    
    # 测试1：对称量化
    print("\n--- 对称量化测试 ---")
    values = np.random.randn(100) * 10
    q, scale = symmetric_quantize(values, bits=8)
    dq = symmetric_dequantize(q, scale)
    
    print(f"原始值范围: [{values.min():.2f}, {values.max():.2f}]")
    print(f"量化缩放因子: {scale:.4f}")
    print(f"量化值范围: [{q.min()}, {q.max()}]")
    print(f"反量化误差(MSE): {np.mean((values - dq)**2):.6f}")
    
    # 测试2：非对称量化
    print("\n--- 非对称量化测试 ---")
    relu_values = np.abs(np.random.randn(100) * 5)  # ReLU输出，总为正
    q_asym, scale_asym, zp = asymmetric_quantize(relu_values, bits=8)
    dq_asym = asymmetric_dequantize(q_asym, scale_asym, zp)
    
    print(f"原始值范围: [{relu_values.min():.2f}, {relu_values.max():.2f}]")
    print(f"缩放因子: {scale_asym:.4f}, 零点: {zp}")
    print(f"反量化误差(MSE): {np.mean((relu_values - dq_asym)**2):.6f}")
    
    # 测试3：量化线性层
    print("\n--- 量化线性层测试 ---")
    batch_size = 32
    in_feat = 128
    out_feat = 64
    
    weight = np.random.randn(out_feat, in_feat).astype(np.float32) * 0.01
    bias = np.random.randn(out_feat).astype(np.float32) * 0.01
    
    layer = QuantizedLinear(weight, bias, bits_weight=8, bits_activation=8)
    
    x = np.random.randn(batch_size, in_feat).astype(np.float32)
    output, output_q, output_scale = layer.forward(x)
    
    print(f"输入形状: {x.shape}")
    print(f"输出形状: {output.shape}")
    print(f"输出范围: [{output.min():.2f}, {output.max():.2f}]")
    print(f"量化后输出范围: [{output_q.min()}, {output_q.max()}]")
    
    # 测试4：动态量化
    print("\n--- 动态量化测试 ---")
    dyn_layer = DynamicQuantizedLinear(in_feat, out_feat)
    x_test = np.random.randn(16, in_feat).astype(np.float32)
    
    output_fp32 = dyn_layer.forward(x_test)
    output_full, output_q, out_scale, out_qscale = dyn_layer.quantize_and_forward(x_test)
    
    print(f"FP32输出范围: [{output_fp32.min():.4f}, {output_fp32.max():.4f}]")
    print(f"INT8输出范围: [{output_q.min()}, {output_q.max()}]")
    print(f"输出缩放因子: {out_qscale:.6f}")
    
    # 测试5：量化误差分析
    print("\n--- 不同位数的量化误差对比 ---")
    original = np.random.randn(1000) * 5
    
    for bits in [4, 6, 8, 10, 12]:
        q, s = symmetric_quantize(original, bits=bits)
        dq = symmetric_dequantize(q, s)
        mse = np.mean((original - dq) ** 2)
        snr = 10 * np.log10(np.var(original) / (mse + 1e-10))
        print(f"  {bits:2d}位: MSE={mse:.6f}, SNR={snr:.2f}dB")
    
    print("\n模型量化测试完成！")
