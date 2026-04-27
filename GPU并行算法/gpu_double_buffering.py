# -*- coding: utf-8 -*-
"""
算法实现：GPU并行算法 / gpu_double_buffering

本文件实现 gpu_double_buffering 相关的算法功能。
"""

import numpy as np
from numba import cuda
import numba
import time


@cuda.jit
def process_kernel(data_in, data_out, n, multiplier):
    """
    处理内核（示例：数据转换）
    
    参数:
        data_in: 输入数据
        data_out: 输出数据
        n: 数据长度
        multiplier: 乘数
    """
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if global_idx < n:
        # 模拟一些计算
        val = data_in[global_idx]
        data_out[global_idx] = val * multiplier + np.sin(val)


@cuda.jit
def pipeline_stage1_kernel(data_in, temp, n):
    """
    流水线第一阶段：预处理
    
    参数:
        data_in: 输入数据
        temp: 中间结果
        n: 数据长度
    """
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if global_idx < n:
        temp[global_idx] = data_in[global_idx] * 2.0


@cuda.jit
def pipeline_stage2_kernel(temp, data_out, n):
    """
    流水线第二阶段：后处理
    
    参数:
        temp: 中间结果
        data_out: 最终输出
        n: 数据长度
    """
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if global_idx < n:
        data_out[global_idx] = temp[global_idx] + 1.0


def cpu_baseline(data, num_iterations):
    """
    CPU串行处理（基准）
    
    参数:
        data: 输入数据
        num_iterations: 迭代次数
    
    返回:
        总耗时
    """
    start = time.time()
    
    result = data.copy()
    for _ in range(num_iterations):
        result = result * 2.0 + 1.0
    
    return time.time() - start


def gpu_single_buffer(data, num_iterations):
    """
    GPU单缓冲处理（传统方式）
    
    问题：需要等待数据传输完成才能开始计算
    
    参数:
        data: 输入数据
        num_iterations: 迭代次数
    
    返回:
        总耗时
    """
    start = time.time()
    
    n = len(data)
    d_data = cuda.to_device(data)
    
    threads = 256
    blocks = (n + threads - 1) // threads
    
    for _ in range(num_iterations):
        # 执行处理
        process_kernel[blocks, threads](d_data, d_data, n, 2.0)
    
    result = d_data.copy_to_host()
    
    return time.time() - start


def gpu_double_buffer(data, num_iterations):
    """
    GPU双缓冲处理（流水线方式）
    
    优势：
    - 两个缓冲区交替使用
    - 计算和数据传输可以重叠
    - 减少内存分配开销
    
    参数:
        data: 输入数据
        num_iterations: 迭代次数
    
    返回:
        总耗时
    """
    start = time.time()
    
    n = len(data)
    
    # 分配两个缓冲区
    buffer_a = cuda.to_device(data)
    buffer_b = cuda.to_device(np.zeros_like(data))
    
    threads = 256
    blocks = (n + threads - 1) // threads
    
    # 流水线处理
    for i in range(num_iterations):
        # 交替读写缓冲区
        if i % 2 == 0:
            process_kernel[blocks, threads](buffer_a, buffer_b, n, 2.0)
            # 交换引用
            buffer_a, buffer_b = buffer_b, buffer_a
        else:
            process_kernel[blocks, threads](buffer_a, buffer_b, n, 2.0)
            buffer_a, buffer_b = buffer_b, buffer_a
    
    result = buffer_a.copy_to_host()
    
    return time.time() - start


def gpu_pipeline_2stage(data, num_iterations):
    """
    GPU两阶段流水线
    
    演示多阶段流水线的双缓冲
    
    参数:
        data: 输入数据
        num_iterations: 迭代次数
    
    返回:
        总耗时
    """
    start = time.time()
    
    n = len(data)
    
    # 分配缓冲区
    # buffer_in -> temp1 -> temp2 -> buffer_out
    buffer_in = cuda.to_device(data)
    temp1 = cuda.to_device(np.zeros_like(data))
    temp2 = cuda.to_device(np.zeros_like(data))
    buffer_out = cuda.to_device(np.zeros_like(data))
    
    threads = 256
    blocks = (n + threads - 1) // threads
    
    # 双缓冲：交替使用两套缓冲区
    use_buffer_set_a = True
    
    for _ in range(num_iterations):
        if use_buffer_set_a:
            # 阶段1: buffer_in -> temp1
            pipeline_stage1_kernel[blocks, threads](buffer_in, temp1, n)
            # 阶段2: temp1 -> temp2 -> buffer_out
            pipeline_stage2_kernel[blocks, threads](temp1, temp2, n)
            pipeline_stage1_kernel[blocks, threads](temp2, buffer_out, n)
        else:
            # 反向交替
            pipeline_stage1_kernel[blocks, threads](buffer_out, temp1, n)
            pipeline_stage2_kernel[blocks, threads](temp1, temp2, n)
            pipeline_stage1_kernel[blocks, threads](temp2, buffer_in, n)
        
        use_buffer_set_a = not use_buffer_set_a
    
    result = buffer_out.copy_to_host()
    
    return time.time() - start


def run_demo():
    """运行双缓冲流水线演示"""
    print("=" * 60)
    print("GPU双缓冲流水线(Ping-Pong Buffering)演示")
    print("=" * 60)
    
    n = 100000
    data = np.random.rand(n).astype(np.float32)
    num_iterations = 100
    
    print(f"\n数据规模: {n:,}, 迭代次数: {num_iterations}")
    
    # CPU基准
    cpu_time = cpu_baseline(data, num_iterations)
    print(f"\n[性能对比]")
    print(f"  CPU串行: {cpu_time:.4f}秒")
    
    # GPU单缓冲
    try:
        gpu_single_time = gpu_single_buffer(data, num_iterations)
        print(f"  GPU单缓冲: {gpu_single_time:.4f}秒")
        print(f"  加速比: {cpu_time/gpu_single_time:.1f}x")
    except Exception as e:
        print(f"  GPU单缓冲: 失败 ({e})")
    
    # GPU双缓冲
    try:
        gpu_double_time = gpu_double_buffer(data, num_iterations)
        print(f"  GPU双缓冲: {gpu_double_time:.4f}秒")
        print(f"  加速比: {cpu_time/gpu_double_time:.1f}x")
    except Exception as e:
        print(f"  GPU双缓冲: 失败 ({e})")
    
    # GPU两阶段流水线
    try:
        gpu_pipeline_time = gpu_pipeline_2stage(data, num_iterations)
        print(f"  GPU两阶段流水线: {gpu_pipeline_time:.4f}秒")
        print(f"  加速比: {cpu_time/gpu_pipeline_time:.1f}x")
    except Exception as e:
        print(f"  GPU两阶段流水线: 失败 ({e})")
    
    print("\n" + "=" * 60)
    print("双缓冲流水线核心概念:")
    print("  1. Ping-Pong Buffer: 两个缓冲区交替读写")
    print("  2. 流水线并行: 不同阶段同时执行")
    print("  3. 内存预取: 下一批数据提前加载")
    print("  4. 减少分配: 避免循环内重复malloc")
    print("  5. 适用场景: 视频处理、流数据、迭代计算")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
