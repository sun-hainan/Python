# -*- coding: utf-8 -*-
"""
算法实现：GPU并行算法 / gpu_histogram

本文件实现 gpu_histogram 相关的算法功能。
"""

import numpy as np
from numba import cuda
import numba


def cpu_histogram(data, num_bins, data_min, data_max):
    """
    CPU直方图计算（基准）
    
    参数:
        data: 输入数据
        num_bins: 直方图bin数量
        data_min: 数据最小值
        data_max: 数据最大值
    
    返回:
        hist: 直方图数组
    """
    bin_width = (data_max - data_min) / num_bins
    hist = np.zeros(num_bins, dtype=np.int32)
    
    for value in data:
        bin_idx = int((value - data_min) / bin_width)
        bin_idx = min(bin_idx, num_bins - 1)  # 处理边界
        hist[bin_idx] += 1
    
    return hist


@cuda.jit
def gpu_histogram_atomic_kernel(data, hist, num_bins, data_min, data_max, n):
    """
    GPU直方图计算（使用原子操作）
    
    原子操作原理：
    - 多个线程可能同时写入同一个bin
    - 原子操作保证每次只有一个线程能写入
    - 使用cuda.atomic.add实现
    
    参数:
        data: 输入数据
        hist: 输出直方图
        num_bins: bin数量
        data_min: 数据最小值
        data_max: 数据最大值
        n: 数据长度
    """
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if global_idx < n:
        # 计算当前值应该落入的bin索引
        bin_width = (data_max - data_min) / num_bins
        bin_idx = int((data[global_idx] - data_min) / bin_width)
        
        # 边界检查
        if bin_idx < 0:
            bin_idx = 0
        elif bin_idx >= num_bins:
            bin_idx = num_bins - 1
        
        # 原子操作：安全地增加计数
        cuda.atomic.add(hist, bin_idx, 1)


@cuda.jit
def gpu_histogram_shared_kernel(data, hist, num_bins, data_min, data_max, n):
    """
    GPU直方图计算（使用共享内存聚合）
    
    优化策略：
    - 先将数据聚合到共享内存
    - 减少全局内存的原子操作冲突
    - 最后一次性更新全局直方图
    
    参数:
        data: 输入数据
        hist: 输出直方图
        num_bins: bin数量
        data_min: 数据最小值
        data_max: 数据最大值
        n: 数据长度
    """
    # 共享内存：用于暂存当前block的局部直方图
    local_hist = cuda.shared.array(256, dtype=numba.int32)
    
    tid = cuda.threadIdx.x
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + tid
    
    # 初始化共享内存
    if tid < num_bins:
        local_hist[tid] = 0
    cuda.syncthreads()
    
    # 局部直方图计算
    if global_idx < n:
        bin_width = (data_max - data_min) / num_bins
        bin_idx = int((data[global_idx] - data_min) / bin_width)
        
        if bin_idx < 0:
            bin_idx = 0
        elif bin_idx >= num_bins:
            bin_idx = num_bins - 1
        
        # 原子操作写入共享内存
        cuda.atomic.add(local_hist, bin_idx, 1)
    
    cuda.syncthreads()
    
    # 将局部直方图合并到全局直方图
    if tid < num_bins:
        cuda.atomic.add(hist, tid, local_hist[tid])


@cuda.jit
def gpu_cumulative_histogram_kernel(hist, cum_hist, num_bins):
    """
    GPU累加直方图计算
    
    将频率直方图转换为累加直方图
    
    参数:
        hist: 输入频率直方图
        cum_hist: 输出累加直方图
        num_bins: bin数量
    """
    tid = cuda.threadIdx.x
    
    if tid < num_bins:
        total = 0.0
        for i in range(tid + 1):
            total += hist[i]
        cum_hist[tid] = total


def gpu_histogram(data, num_bins=16, use_shared=True):
    """
    GPU直方图计算封装函数
    
    参数:
        data: 输入numpy数组
        num_bins: bin数量
        use_shared: 是否使用共享内存优化
    
    返回:
        hist: 直方图数组
    """
    data = data.astype(np.float32)
    n = len(data)
    
    data_min = np.min(data)
    data_max = np.max(data)
    
    # 初始化直方图
    hist = np.zeros(num_bins, dtype=np.int32)
    
    # 传输到GPU
    d_data = cuda.to_device(data)
    d_hist = cuda.to_device(hist)
    
    # 配置grid和block
    threads = 256
    blocks = (n + threads - 1) // threads
    
    # 执行内核
    if use_shared:
        gpu_histogram_shared_kernel[blocks, threads](
            d_data, d_hist, num_bins, data_min, data_max, n
        )
    else:
        gpu_histogram_atomic_kernel[blocks, threads](
            d_data, d_hist, num_bins, data_min, data_max, n
        )
    
    return d_hist.copy_to_host()


def gpu_cumulative_histogram(hist):
    """
    GPU累加直方图计算
    
    参数:
        hist: 频率直方图
    
    返回:
        cum_hist: 累加直方图
    """
    num_bins = len(hist)
    cum_hist = np.zeros(num_bins, dtype=np.float32)
    
    d_hist = cuda.to_device(hist.astype(np.int32))
    d_cum = cuda.to_device(cum_hist)
    
    threads = num_bins
    gpu_cumulative_histogram_kernel[1, threads](d_hist, d_cum, num_bins)
    
    return d_cum.copy_to_host()


def run_demo():
    """运行直方图演示"""
    print("=" * 60)
    print("GPU并行直方图计算演示")
    print("=" * 60)
    
    sizes = [1000, 10000, 100000]
    num_bins = 16
    
    for n in sizes:
        # 生成均匀分布的随机数据
        data = np.random.uniform(0, 100, n).astype(np.float32)
        data_min, data_max = 0.0, 100.0
        
        # CPU基准
        cpu_hist = cpu_histogram(data, num_bins, data_min, data_max)
        
        # GPU计算（原子操作）
        gpu_hist_atomic = gpu_histogram(data, num_bins, use_shared=False)
        
        # GPU计算（共享内存优化）
        gpu_hist_shared = gpu_histogram(data, num_bins, use_shared=True)
        
        # 计算总计数验证
        total_atomic = np.sum(gpu_hist_atomic)
        total_shared = np.sum(gpu_hist_shared)
        
        print(f"\n数据规模: {n:,}, Bin数量: {num_bins}")
        print(f"  CPU直方图:    {cpu_hist}")
        print(f"  GPU原子操作:  {gpu_hist_atomic}")
        print(f"  GPU共享内存:  {gpu_hist_shared}")
        print(f"  CPU总数: {n}, GPU原子总数: {total_atomic}, GPU共享总数: {total_shared}")
        print(f"  原子操作正确: {'✓' if np.allclose(cpu_hist, gpu_hist_atomic) else '✗'}")
        print(f"  共享内存正确: {'✓' if np.allclose(cpu_hist, gpu_hist_shared) else '✗'}")
    
    # 累加直方图演示
    print("\n" + "-" * 40)
    print("累加直方图示例:")
    sample_data = np.array([1.0, 2.0, 2.0, 3.0, 3.0, 3.0, 4.0, 4.0, 5.0])
    freq_hist = cpu_histogram(sample_data, 5, 1.0, 5.0)
    cum_hist = gpu_cumulative_histogram(freq_hist)
    print(f"  频率直方图: {freq_hist}")
    print(f"  累加直方图: {cum_hist}")
    
    print("\n" + "=" * 60)
    print("并行直方图核心概念:")
    print("  1. 原子操作: cuda.atomic.add保证并发安全")
    print("  2. 共享内存优化: 减少全局内存原子操作冲突")
    print("  3. 局部聚合: 每个block先计算局部直方图，再合并")
    print("  4. 应用: 图像处理、统计分析、数据分桶")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
