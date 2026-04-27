# -*- coding: utf-8 -*-
"""
算法实现：GPU并行算法 / gpu_deep_learning

本文件实现 gpu_deep_learning 相关的算法功能。
"""

import numpy as np
from numba import cuda
import numba
import math


@cuda.jit
def gpu_matrix_add_kernel(A, B, C, m, n):
    """
    GPU矩阵加法
    
    参数:
        A, B: 输入矩阵 (m×n)
        C: 输出矩阵
        m, n: 维度
    """
    row = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y
    col = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if row < m and col < n:
        C[row * n + col] = A[row * n + col] + B[row * n + col]


@cuda.jit
def gpu_matrix_mul_kernel(A, B, C, m, n, k):
    """
    GPU矩阵乘法 C = A × B
    
    A: m×k, B: k×n, C: m×n
    
    参数:
        A, B, C: 矩阵
        m, n, k: 维度
    """
    # 使用共享内存缓存A的行
    shared_A = cuda.shared.array((16, 16), dtype=np.float32)
    shared_B = cuda.shared.array((16, 16), dtype=np.float32)
    
    tx = cuda.threadIdx.x
    ty = cuda.threadIdx.y
    
    row = cuda.blockIdx.y * cuda.blockDim.y + ty
    col = cuda.blockIdx.x * cuda.blockDim.x + tx
    
    # 累加器
    value = 0.0
    
    # 分块计算
    for b in range((k + 15) // 16):
        # 加载A到共享内存
        if row < m and (b * 16 + tx) < k:
            shared_A[ty, tx] = A[row * k + b * 16 + tx]
        else:
            shared_A[ty, tx] = 0.0
        
        # 加载B到共享内存
        if col < n and (b * 16 + ty) < k:
            shared_B[ty, tx] = B[(b * 16 + ty) * n + col]
        else:
            shared_B[ty, tx] = 0.0
        
        cuda.syncthreads()
        
        # 计算该块的贡献
        for i in range(16):
            value += shared_A[ty, i] * shared_B[i, tx]
        
        cuda.syncthreads()
    
    # 写入结果
    if row < m and col < n:
        C[row * n + col] = value


@cuda.jit
def gpu_relu_kernel(x, output, n):
    """
    GPU ReLU激活函数
    
    ReLU(x) = max(0, x)
    
    参数:
        x: 输入
        output: 输出
        n: 元素数量
    """
    idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if idx < n:
        val = x[idx]
        output[idx] = val if val > 0 else 0.0


@cuda.jit
def gpu_sigmoid_kernel(x, output, n):
    """
    GPU Sigmoid激活函数
    
    sigmoid(x) = 1 / (1 + exp(-x))
    
    参数:
        x: 输入
        output: 输出
        n: 元素数量
    """
    idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if idx < n:
        val = x[idx]
        # 防止溢出
        if val < -20:
            output[idx] = 0.0
        elif val > 20:
            output[idx] = 1.0
        else:
            output[idx] = 1.0 / (1.0 + math.exp(-val))


@cuda.jjit
def gpu_softmax_kernel(x, output, n):
    """
    GPU Softmax函数
    
    softmax(x)_i = exp(x_i) / sum(exp(x_j))
    
    参数:
        x: 输入向量
        output: 输出向量
        n: 元素数量
    """
    idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if idx < n:
        # 第一步：找最大值（数值稳定性）
        max_val = 0.0
        for i in range(n):
            if x[i] > max_val:
                max_val = x[i]
        
        # 第二步：计算exp并求和
        exp_sum = 0.0
        for i in range(n):
            exp_sum += math.exp(x[i] - max_val)
        
        # 第三步：计算softmax
        output[idx] = math.exp(x[idx] - max_val) / exp_sum


@cuda.jit
def gpu_conv2d_kernel(input_data, kernel, output_data, 
                       in_h, in_w, out_h, out_w, 
                       k_h, k_w, stride, pad):
    """
    GPU 2D卷积（简化版）
    
    参数:
        input_data: 输入特征图
        kernel: 卷积核
        output_data: 输出特征图
        in_h, in_w: 输入尺寸
        out_h, out_w: 输出尺寸
        k_h, k_w: 卷积核尺寸
        stride: 步长
        pad: 填充
    """
    # 输出坐标
    out_y = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y
    out_x = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if out_y < out_h and out_x < out_w:
        # 计算对应的输入位置
        in_y = out_y * stride - pad
        in_x = out_x * stride - pad
        
        # 累加
        sum_val = 0.0
        
        for ky in range(k_h):
            for kx in range(k_w):
                in_y_pos = in_y + ky
                in_x_pos = in_x + kx
                
                if 0 <= in_y_pos < in_h and 0 <= in_x_pos < in_w:
                    input_val = input_data[in_y_pos * in_w + in_x_pos]
                    kernel_val = kernel[ky * k_w + kx]
                    sum_val += input_val * kernel_val
        
        output_data[out_y * out_w + out_x] = sum_val


class SimpleNeuralNetwork:
    """
    简化神经网络（用于GPU推理）
    
    结构：Input -> Dense(10) -> ReLU -> Dense(10) -> Sigmoid -> Output
    """
    
    def __init__(self, input_size, hidden_size, output_size):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # 权重和偏置（简化：随机初始化）
        np.random.seed(42)
        self.W1 = np.random.randn(input_size, hidden_size).astype(np.float32) * 0.1
        self.b1 = np.zeros(hidden_size, dtype=np.float32)
        self.W2 = np.random.randn(hidden_size, output_size).astype(np.float32) * 0.1
        self.b2 = np.zeros(output_size, dtype=np.float32)
    
    def forward_gpu(self, x):
        """
        GPU前向传播
        
        参数:
            x: 输入 (input_size,)
        
        返回:
            output: 输出 (output_size,)
        """
        x = x.astype(np.float32)
        
        # 第一层：线性 + ReLU
        # y1 = x @ W1 + b1
        # y1 = ReLU(y1)
        
        # 矩阵乘法: x(1×input) @ W1(input×hidden) = y1(1×hidden)
        m1_out = np.zeros(self.hidden_size, dtype=np.float32)
        
        d_W1 = cuda.to_device(self.W1)
        d_W2 = cuda.to_device(self.W2)
        d_x = cuda.to_device(x)
        d_y1 = cuda.to_device(m1_out)
        
        # 简化的矩阵向量乘法
        @cuda.jit
        def mat_vec_mul_kernel(A, x, y, m, n):
            row = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
            if row < m:
                total = 0.0
                for j in range(n):
                    total += A[row * n + j] * x[j]
                y[row] = total
        
        threads = 256
        blocks = (self.hidden_size + threads - 1) // threads
        
        # 计算第一层
        mat_vec_mul_kernel[blocks, threads](d_W1, d_x, d_y1, self.hidden_size, self.input_size)
        y1 = d_y1.copy_to_host()
        
        # 添加偏置
        y1 += self.b1
        
        # ReLU
        d_y1_relu = cuda.to_device(y1)
        d_y1_out = cuda.to_device(np.zeros_like(y1))
        
        gpu_relu_kernel[blocks, threads](d_y1_relu, d_y1_out, self.hidden_size)
        y1_relu = d_y1_out.copy_to_host()
        
        # 第二层：线性 + Sigmoid
        d_y2 = cuda.to_device(np.zeros(self.output_size, dtype=np.float32))
        
        mat_vec_mul_kernel[blocks, threads](d_W2, d_y1_out if False else cuda.to_device(y1_relu), 
                                          d_y2, self.output_size, self.hidden_size)
        y2 = d_y2.copy_to_host()
        
        y2 += self.b2
        
        # Sigmoid
        d_y2_sigmoid = cuda.to_device(y2)
        d_output = cuda.to_device(np.zeros_like(y2))
        
        gpu_sigmoid_kernel[blocks, threads](d_y2_sigmoid, d_output, self.output_size)
        output = d_output.copy_to_host()
        
        return output
    
    def forward_cpu(self, x):
        """CPU前向传播（用于对比）"""
        # 第一层
        y1 = np.dot(x, self.W1) + self.b1
        y1 = np.maximum(0, y1)  # ReLU
        
        # 第二层
        y2 = np.dot(y1, self.W2) + self.b2
        output = 1 / (1 + np.exp(-y2))  # Sigmoid
        
        return output


def run_demo():
    """运行神经网络推理演示"""
    print("=" * 60)
    print("GPU并行算法：深度学习推理")
    print("=" * 60)
    
    # 创建网络
    input_size = 100
    hidden_size = 50
    output_size = 10
    
    nn = SimpleNeuralNetwork(input_size, hidden_size, output_size)
    
    # 测试输入
    batch_size = 1
    x = np.random.randn(input_size).astype(np.float32)
    
    print(f"\n[神经网络结构]")
    print(f"  输入: {input_size}")
    print(f"  隐藏层: {hidden_size}")
    print(f"  输出: {output_size}")
    print(f"  输入形状: {x.shape}")
    
    # CPU前向传播
    print("\n[前向传播]")
    import time
    
    start = time.time()
    output_cpu = nn.forward_cpu(x)
    cpu_time = time.time() - start
    print(f"  CPU时间: {cpu_time * 1000:.4f}ms")
    print(f"  输出形状: {output_cpu.shape}")
    print(f"  输出前5: {output_cpu[:5]}")
    
    # GPU前向传播
    try:
        start = time.time()
        output_gpu = nn.forward_gpu(x)
        gpu_time = time.time() - start
        print(f"  GPU时间: {gpu_time * 1000:.4f}ms")
        
        # 验证结果
        max_diff = np.max(np.abs(output_cpu - output_gpu))
        print(f"  CPU/GPU差异: {max_diff:.6f}")
        
        if gpu_time > 0:
            speedup = cpu_time / gpu_time if gpu_time > 0 else float('inf')
            print(f"  加速比: {speedup:.2f}x")
    except Exception as e:
        print(f"  GPU前向传播失败: {e}")
    
    print("\n" + "=" * 60)
    print("深度学习推理核心概念:")
    print("  1. 矩阵乘法: 层间计算的核心操作")
    print("  2. 激活函数: ReLU, Sigmoid, Tanh, Softmax")
    print("  3. 卷积: 权重共享的局部连接")
    print("  4. GPU优势: 大矩阵运算的并行化")
    print("  5. 批处理: 一次处理多个样本提高吞吐量")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
