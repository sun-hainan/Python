# -*- coding: utf-8 -*-
"""
算法实现：GPU并行算法 / gpu_thread_sync

本文件实现 gpu_thread_sync 相关的算法功能。
"""

import numpy as np
from numba import cuda
import numba


@cuda.jit
def syncthreads_demo_kernel(data, result, n):
    """
    演示__syncthreads()的典型使用场景
    
    场景1: 批量加载后同步
    场景2: 计算后同步
    场景3: 条件写入后的安全读取
    
    参数:
        data: 输入数组
        result: 输出数组
        n: 数组长度
    """
    # 共享内存：用于线程间数据交换
    shared_buf = cuda.shared.array(256, dtype=np.float32)
    
    tid = cuda.threadIdx.x
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + tid
    
    # ========== 场景1: 分阶段数据加载 ==========
    # 假设我们需要加载两次数据才能填满shared_buf
    if global_idx < n:
        shared_buf[tid] = data[global_idx]
    
    # 同步点1: 等待所有线程完成第一次加载
    cuda.syncthreads()
    
    # 现在可以安全地读取其他线程写入的数据
    # 例如，计算当前线程和前一个线程数据的平均值
    if global_idx > 0 and global_idx < n and tid > 0:
        shared_buf[tid] = (shared_buf[tid] + shared_buf[tid - 1]) / 2.0
    
    # 同步点2: 确保所有计算完成
    cuda.syncthreads()
    
    # ========== 场景2: 条件写入后的安全同步 ==========
    # 只有满足条件的线程才写入，但所有线程都需要等待
    if global_idx < n:
        if shared_buf[tid] > 0.5:
            shared_buf[tid] = 1.0
        else:
            shared_buf[tid] = 0.0
    
    # 关键：即使某些线程不做任何事，也需要同步
    cuda.syncthreads()
    
    # ========== 场景3: 写入结果 ==========
    if global_idx < n:
        result[global_idx] = shared_buf[tid]


@cuda.jit
def conditional_sync_kernel(data, result, threshold, n):
    """
    演示条件同步问题
    
    问题：当只有部分线程执行同步等待的操作时可能死锁
    解决：确保所有线程都到达同步点
    
    参数:
        data: 输入数据
        result: 输出结果
        threshold: 阈值
        n: 数据长度
    """
    shared_data = cuda.shared.array(256, dtype=np.float32)
    
    tid = cuda.threadIdx.x
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + tid
    
    # 加载数据
    if global_idx < n:
        shared_data[tid] = data[global_idx]
    else:
        shared_data[tid] = 0.0
    
    cuda.syncthreads()
    
    # 条件执行：如果某些线程跳过同步，可能导致死锁
    # 正确做法：所有线程都参与同步（即使不需要执行计算）
    if global_idx < n and shared_data[tid] > threshold:
        # 执行一些操作
        shared_data[tid] = shared_data[tid] * 2
    
    # 重要：所有线程都必须到达这里才能安全同步
    cuda.syncthreads()
    
    # 写入结果
    if global_idx < n:
        result[global_idx] = shared_data[tid]


@cuda.jit
def warp_level_sync_simulation(data, result, n):
    """
    模拟线程束级别的同步
    
    线程束(Warp)是32个连续线程的集合，它们执行同一条指令
    但CUDA没有直接的线程束同步，需要通过共享内存或洗涤指令
    
    本例演示如何通过共享内存实现线程束间的数据交换
    
    参数:
        data: 输入数据
        result: 输出结果
        n: 数据长度
    """
    shared_data = cuda.shared.array(256, dtype=np.float32)
    
    tid = cuda.threadIdx.x
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + tid
    
    # 加载到共享内存
    if global_idx < n:
        shared_data[tid] = data[global_idx]
    
    cuda.syncthreads()
    
    # 线程束级别的操作
    # 由于共享内存在线程束级别是交织访问的
    # 我们可以利用这个特性进行快速的线程束内通信
    
    # 计算线程束ID（每32个线程为一个线程束）
    warp_id = tid // 32
    lane_id = tid % 32  # 线程在线程束内的lane编号
    
    # 线程束内广播：lane 0广播到其他lane
    if lane_id == 0:
        # 这里是线程束的第一个线程，执行计算
        warp_sum = 0.0
        start_idx = warp_id * 32
        for i in range(32):
            if start_idx + i < n:
                warp_sum += shared_data[start_idx + i]
        shared_data[tid] = warp_sum
    else:
        shared_data[tid] = 0.0
    
    cuda.syncthreads()
    
    # 写入结果
    if global_idx < n:
        result[global_idx] = shared_data[tid]


def run_demo():
    """运行同步演示"""
    print("=" * 60)
    print("GPU线程束同步与共享内存深入理解")
    print("=" * 60)
    
    n = 1024
    data = np.random.rand(n).astype(np.float32)
    result1 = np.zeros(n, dtype=np.float32)
    result2 = np.zeros(n, dtype=np.float32)
    result3 = np.zeros(n, dtype=np.float32)
    
    threads = 256
    blocks = (n + threads - 1) // threads
    
    # 传输到GPU
    d_data = cuda.to_device(data)
    d_result1 = cuda.to_device(result1)
    d_result2 = cuda.to_device(result2)
    d_result3 = cuda.to_device(result3)
    
    # 演示1: 基础同步
    print("\n[演示1] 基础同步演示:")
    syncthreads_demo_kernel[blocks, threads](d_data, d_result1, n)
    result1 = d_result1.copy_to_host()
    print(f"  结果前10个: {result1[:10]}")
    print(f"  非零元素数量: {np.count_nonzero(result1)}")
    
    # 演示2: 条件同步
    print("\n[演示2] 条件同步演示:")
    threshold = 0.5
    conditional_sync_kernel[blocks, threads](d_data, d_result2, threshold, n)
    result2 = d_result2.copy_to_host()
    print(f"  阈值: {threshold}")
    print(f"  结果前10个: {result2[:10]}")
    print(f"  大于阈值设为2倍的数量: {np.sum(result2 > 1.0)}")
    
    # 演示3: 线程束级别同步模拟
    print("\n[演示3] 线程束级别同步模拟:")
    warp_level_sync_simulation[blocks, threads](d_data, d_result3, n)
    result3 = d_result3.copy_to_host()
    print(f"  线程束内求和结果（前320个，每个线程束一个和）: {result3[:320:32]}")
    
    print("\n" + "=" * 60)
    print("线程束同步核心概念:")
    print("  1. __syncthreads(): block内所有线程同步")
    print("  2. 死锁避免: 所有线程必须都到达同步点")
    print("  3. 线程束(Warp): 32个线程为一组，天然同步")
    print("  4. 共享内存Bank: 避免访问同一bank导致冲突")
    print("  5. 条件同步: 确保所有线程参与同步")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
