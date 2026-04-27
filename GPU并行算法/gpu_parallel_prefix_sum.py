# -*- coding: utf-8 -*-
"""
算法实现：GPU并行算法 / gpu_parallel_prefix_sum

本文件实现 gpu_parallel_prefix_sum 相关的算法功能。
"""

import numpy as np
from numba import cuda
import numba


def cpu_prefix_sum(data):
    """CPU前缀和（串行）作为基准"""
    result = np.zeros_like(data)
    total = 0
    for i in range(len(data)):
        result[i] = total
        total += data[i]
    return result


@cuda.jit
def gpu_scan_up_sweep_kernel(data, n):
    """
    GPU Scan算法 - Up-Sweep阶段（归约树构建）
    
    算法原理：
    - 从底层开始，每轮将相邻元素配对
    - 间隔逐渐增大：1, 2, 4, 8, ...
    - 每个配对中，将右边的元素加上左边的元素
    - 最终最后一个元素保存整个数组的累加和
    
    参数:
        data: 输入/输出数组（in-place操作）
        n: 数组长度（必须是2的幂）
    """
    # 共享内存用于线程间通信
    shared_data = cuda.shared.array(256, dtype=np.float32)
    
    # 全局和局部索引
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    tid = cuda.threadIdx.x
    
    # 加载数据到共享内存
    if global_idx < n:
        shared_data[tid] = data[global_idx]
    else:
        shared_data[tid] = 0.0
    
    cuda.syncthreads()
    
    # Up-Sweep阶段：构建归约树
    # stride从1开始，每次翻倍
    stride = 1
    while stride <= cuda.blockDim.x:
        # 计算配对索引
        if tid % (stride * 2) == 0 and tid + stride < cuda.blockDim.x:
            # 只让配对的左元素线程执行加法
            shared_data[tid + stride] += shared_data[tid]
        
        cuda.syncthreads()
        stride *= 2
    
    # 将结果写回全局内存
    if global_idx < n:
        data[global_idx] = shared_data[tid]


@cuda.jit
def gpu_scan_down_sweep_kernel(data, n):
    """
    GPU Scan算法 - Down-Sweep阶段（结果传播）
    
    算法原理：
    - 从树根开始，每轮向下传播
    - 右子树的节点加上左子树的值
    - 间隔逐渐减小：..., 8, 4, 2, 1
    
    参数:
        data: 输入/输出数组（in-place操作）
        n: 数组长度（必须是2的幂）
    """
    # 共享内存
    shared_data = cuda.shared.array(256, dtype=np.float32)
    
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    tid = cuda.threadIdx.x
    
    # 加载数据
    if global_idx < n:
        shared_data[tid] = data[global_idx]
    else:
        shared_data[tid] = 0.0
    
    cuda.syncthreads()
    
    # Down-Sweep阶段：从根向下传播
    # 从最大stride开始，每次除以2
    stride = cuda.blockDim.x // 2
    while stride >= 1:
        if tid % (stride * 2) == 0 and tid + stride < cuda.blockDim.x:
            # 右子树节点加上左子树的值
            left_val = shared_data[tid]
            right_val = shared_data[tid + stride]
            shared_data[tid] = right_val  # 左子树变为原右子树值
            shared_data[tid + stride] = left_val + right_val  # 右子树累加左子树
        elif tid % (stride * 2) == stride and tid < cuda.blockDim.x:
            # 保持不变
            pass
        
        cuda.syncthreads()
        stride //= 2
    
    # 写回全局内存
    if global_idx < n:
        data[global_idx] = shared_data[tid]


@cuda.jit
def gpu_scan_kernel(data, n):
    """
    GPU完整Scan算法（合并版）
    
    参数:
        data: 输入/输出数组
        n: 数组长度
    """
    # 共享内存
    shared_data = cuda.shared.array(256, dtype=np.float32)
    
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    tid = cuda.threadIdx.x
    
    # 加载
    if global_idx < n:
        shared_data[tid] = data[global_idx]
    else:
        shared_data[tid] = 0.0
    
    cuda.syncthreads()
    
    # ========== Up-Sweep ==========
    stride = 1
    while stride < cuda.blockDim.x:
        if tid % (stride * 2) == 0 and tid + stride < cuda.blockDim.x:
            shared_data[tid + stride] += shared_data[tid]
        cuda.syncthreads()
        stride *= 2
    
    # ========== 归零最后一个元素（为down-sweep准备） ==========
    if tid == cuda.blockDim.x - 1:
        shared_data[tid] = 0.0
    cuda.syncthreads()
    
    # ========== Down-Sweep ==========
    stride = cuda.blockDim.x // 2
    while stride >= 1:
        if tid % (stride * 2) == 0 and tid + stride < cuda.blockDim.x:
            temp = shared_data[tid]
            shared_data[tid] = shared_data[tid + stride]
            shared_data[tid + stride] = temp + shared_data[tid + stride]
        cuda.syncthreads()
        stride //= 2
    
    # 写回
    if global_idx < n:
        data[global_idx] = shared_data[tid]


def round_to_power_of_two(n):
    """将n向上取整到最近的2的幂"""
    power = 1
    while power < n:
        power *= 2
    return power


def gpu_scan(data):
    """
    GPU前缀和封装函数
    
    参数:
        data: 输入numpy数组
    
    返回:
        prefix_sum: 前缀和数组
    """
    n = len(data)
    
    # 扩展到2的幂
    new_n = round_to_power_of_two(n)
    
    # 填充数据到2的幂
    extended_data = np.zeros(new_n, dtype=np.float32)
    extended_data[:n] = data.astype(np.float32)
    
    # 传输到GPU
    d_data = cuda.to_device(extended_data)
    
    # 配置
    threads_per_block = 256
    blocks_per_grid = 1  # 对于小规模数据，单block足够
    
    # 执行
    gpu_scan_kernel[blocks_per_grid, threads_per_block](d_data, new_n)
    
    # 复制回主机
    result = d_data.copy_to_host()
    
    # 截取原始长度
    return result[:n]


def run_demo():
    """运行前缀和演示"""
    print("=" * 60)
    print("GPU并行前缀和 - Blelloch Scan算法演示")
    print("=" * 60)
    
    sizes = [100, 500, 1000, 2000]
    
    for n in sizes:
        data = np.random.rand(n).astype(np.float32)
        
        # CPU基准
        cpu_result = cpu_prefix_sum(data)
        
        # GPU计算
        gpu_result = gpu_scan(data)
        
        # 验证
        max_error = np.max(np.abs(gpu_result - cpu_result))
        
        print(f"\n数组长度: {n}")
        print(f"  CPU前缀和:   {cpu_result[:5]}...")
        print(f"  GPU前缀和:   {gpu_result[:5]}...")
        print(f"  最大误差: {max_error:.6f}")
        print(f"  结果正确: {'✓' if max_error < 1e-4 else '✗'}")
    
    print("\n" + "=" * 60)
    print("Blelloch Scan算法核心概念:")
    print("  1. Up-Sweep阶段：构建完全二叉树，自底向上归约")
    print("  2. Down-Sweep阶段：从根向下传播，自顶向下展开")
    print("  3. 时间复杂度：O(log n)，远优于串行的O(n)")
    print("  4. 应用：稀疏矩阵乘法、排序、过滤等并行算法的基础")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
