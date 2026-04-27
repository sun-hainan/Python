# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / activation_functions

本文件实现 activation_functions 相关的算法功能。
"""

import numpy as np


# ============================
# ReLU及其变体
# ============================

def relu(x):
    """ReLU: max(0, x)"""
    return np.maximum(0, x)


def relu_gradient(x):
    """ReLU导数"""
    return (x > 0).astype(float)


def leaky_relu(x, alpha=0.01):
    """
    Leaky ReLU: x if x > 0 else alpha * x
    解决ReLU的"dying ReLU"问题
    """
    return np.where(x > 0, x, alpha * x)


def leaky_relu_gradient(x, alpha=0.01):
    """Leaky ReLU导数"""
    return np.where(x > 0, 1.0, alpha)


def prelu(x, alpha=None):
    """
    PReLU (Parametric ReLU): 可学习的Leaky ReLU
    alpha是可学习的参数
    """
    if alpha is None:
        alpha = np.array(0.01)
    return np.where(x > 0, x, alpha * x)


def elu(x, alpha=1.0):
    """
    ELU (Exponential Linear Unit)
    x if x > 0 else alpha * (exp(x) - 1)
    """
    return np.where(x > 0, x, alpha * (np.exp(np.clip(x, -20, 20)) - 1))


def elu_gradient(x, alpha=1.0):
    """ELU导数"""
    return np.where(x > 0, 1.0, elu(x, alpha) + alpha)


def relu6(x):
    """ReLU6: min(max(0, x), 6)"""
    return np.minimum(np.maximum(0, x), 6)


# ============================
# Sigmoid和Tanh
# ============================

def sigmoid(x):
    """Sigmoid: 1 / (1 + exp(-x))"""
    x = np.clip(x, -500, 500)
    return 1 / (1 + np.exp(-x))


def sigmoid_gradient(x):
    """Sigmoid导数: sigmoid(x) * (1 - sigmoid(x))"""
    s = sigmoid(x)
    return s * (1 - s)


def tanh(x):
    """Tanh: (exp(x) - exp(-x)) / (exp(x) + exp(-x))"""
    return np.tanh(x)


def tanh_gradient(x):
    """Tanh导数: 1 - tanh^2(x)"""
    return 1 - np.tanh(x) ** 2


def hard_tanh(x):
    """Hard Tanh: -1 if x < -1, x if -1 <= x <= 1, 1 if x > 1"""
    return np.clip(x, -1, 1)


# ============================
# GELU和Swish
# ============================

def gelu(x):
    """
    GELU (Gaussian Error Linear Unit)
    x * Phi(x)，其中Phi是标准正态分布的CDF
    近似: 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 * x^3)))
    """
    # 近似实现
    return 0.5 * x * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))


def gelu_gradient(x):
    """GELU导数"""
    # 使用近似导数
    cdf = 0.5 * (1 + np.tanh(np.sqrt(2 / np.pi) * (x + 0.044715 * x ** 3)))
    pdf = np.exp(-0.5 * x ** 2) / np.sqrt(2 * np.pi)
    return cdf + x * pdf


def swish(x, beta=1.0):
    """
    Swish: x * sigmoid(beta * x)
    当beta=1时等于SiLU（Swish-1）
    """
    return x * sigmoid(beta * x)


def swish_gradient(x, beta=1.0):
    """Swish导数"""
    s = sigmoid(beta * x)
    return s + beta * x * s * (1 - s)


def mish(x):
    """
    Mish: x * tanh(softplus(x))
    softplus(x) = log(1 + exp(x))
    """
    return x * np.tanh(np.log(1 + np.exp(np.clip(x, -20, 20))))


def mish_gradient(x):
    """Mish导数（近似）"""
    sp = np.log(1 + np.exp(np.clip(x, -20, 20)))
    t = np.tanh(sp)
    return t + x * (1 - t ** 2) * sigmoid(x)


# ============================
# Softmax（多分类输出）
# ============================

def softmax(x, axis=1):
    """
    Softmax: exp(x_i) / sum(exp(x_j))
    沿指定轴计算
    """
    # 数值稳定化：减去最大值
    x_shifted = x - np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x_shifted)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def log_softmax(x, axis=1):
    """
    Log Softmax: log(softmax(x))
    数值稳定的版本
    """
    x_shifted = x - np.max(x, axis=axis, keepdims=True)
    return x_shifted - np.log(np.sum(np.exp(x_shifted), axis=axis, keepdims=True))


# ============================
# 激活函数类（便于集成到神经网络）
# ============================

class Activation:
    """
    激活函数包装类
    
    参数:
        name: 激活函数名
    """
    
    def __init__(self, name='relu'):
        self.name = name
        self.x_cache = None
    
    def forward(self, x):
        """前馈传播"""
        self.x_cache = x
        
        if self.name == 'relu':
            return relu(x)
        elif self.name == 'leaky_relu':
            return leaky_relu(x)
        elif self.name == 'elu':
            return elu(x)
        elif self.name == 'sigmoid':
            return sigmoid(x)
        elif self.name == 'tanh':
            return tanh(x)
        elif self.name == 'gelu':
            return gelu(x)
        elif self.name == 'swish':
            return swish(x)
        elif self.name == 'mish':
            return mish(x)
        elif self.name == 'relu6':
            return relu6(x)
        else:
            raise ValueError(f"Unknown activation: {self.name}")
    
    def backward(self, grad_output):
        """反向传播"""
        if self.x_cache is None:
            raise RuntimeError("需要先执行前馈传播")
        
        x = self.x_cache
        
        if self.name == 'relu':
            return grad_output * relu_gradient(x)
        elif self.name == 'leaky_relu':
            return grad_output * leaky_relu_gradient(x)
        elif self.name == 'elu':
            return grad_output * elu_gradient(x)
        elif self.name == 'sigmoid':
            return grad_output * sigmoid_gradient(x)
        elif self.name == 'tanh':
            return grad_output * tanh_gradient(x)
        elif self.name == 'gelu':
            return grad_output * gelu_gradient(x)
        elif self.name == 'swish':
            return grad_output * swish_gradient(x)
        elif self.name == 'mish':
            return grad_output * mish_gradient(x)
        elif self.name == 'relu6':
            return grad_output * (relu6(x) > 0).astype(float)
        else:
            raise ValueError(f"Unknown activation: {self.name}")


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    print("=" * 55)
    print("激活函数测试")
    print("=" * 55)
    
    x = np.linspace(-5, 5, 100)
    
    # 测试各种激活函数
    activations = {
        'ReLU': relu(x),
        'LeakyReLU(α=0.01)': leaky_relu(x),
        'ELU(α=1)': elu(x),
        'Sigmoid': sigmoid(x),
        'Tanh': tanh(x),
        'GELU': gelu(x),
        'Swish': swish(x),
        'Mish': mish(x),
    }
    
    print("\n--- 各激活函数值范围 ---")
    for name, values in activations.items():
        print(f"  {name:25s}: [{values.min():.4f}, {values.max():.4f}]")
    
    # 测试导数
    print("\n--- 导数一致性检验 ---")
    h = 1e-5
    
    for name in ['ReLU', 'Sigmoid', 'Tanh', 'GELU', 'Swish']:
        act = Activation(name.lower() if name != 'ReLU' else 'relu')
        
        # 数值导数
        x_test = np.random.randn(10)
        numeric_grad = np.zeros_like(x_test)
        
        for i in range(len(x_test)):
            x_plus = x_test.copy()
            x_minus = x_test.copy()
            x_plus[i] += h
            x_minus[i] -= h
            
            if name == 'ReLU':
                y_plus, y_minus = relu(x_plus), relu(x_minus)
            elif name == 'Sigmoid':
                y_plus, y_minus = sigmoid(x_plus), sigmoid(x_minus)
            elif name == 'Tanh':
                y_plus, y_minus = tanh(x_plus), tanh(x_minus)
            elif name == 'GELU':
                y_plus, y_minus = gelu(x_plus), gelu(x_minus)
            elif name == 'Swish':
                y_plus, y_minus = swish(x_plus), swish(x_minus)
            
            numeric_grad[i] = (y_plus.sum() - y_minus.sum()) / (2 * h)
        
        # 解析导数
        x_test_copy = x_test.copy()
        act.forward(x_test_copy)
        analytic_grad = act.backward(np.ones(10))
        
        max_error = np.abs(numeric_grad - analytic_grad).max()
        print(f"  {name:10s}: 最大导数误差 = {max_error:.8f}")
    
    # GELU vs ReLU在Transformer中的对比
    print("\n--- GELU vs ReLU: Transformer场景 ---")
    x_large = np.array([0.0, 0.5, 1.0, 2.0, 5.0])
    
    print(f"{'x':>6} | {'ReLU':>10} | {'GELU':>10} | {'Swish':>10}")
    print("-" * 45)
    for xv in x_large:
        print(f"{xv:6.1f} | {relu(xv):10.4f} | {gelu(xv):10.4f} | {swish(xv):10.4f}")
    
    print("\n激活函数测试完成！")
