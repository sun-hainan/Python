# -*- coding: utf-8 -*-
"""
算法实现：GPU并行算法 / gpu_parallel_sorting

本文件实现 gpu_parallel_sorting 相关的算法功能。
"""

import numpy as np
from numba import cuda
import numba


def cpu_bitonic_sort(data):
    """CPU位序列排序（作为基准）"""
    return np.sort(data)


@cuda.jit
def bitonic_compare_and_swap(data, start, stride, direction):
    """
    Bitonic Sort的比较-交换操作
    
    参数:
        data: 数据数组
        start: 当前段的起始索引
        stride: 比较元素之间的间隔
        direction: 1=升序, 0=降序
    """
    tid = cuda.threadIdx.x
    
    # 计算配对索引
    idx1 = start + tid * stride * 2
    idx2 = idx1 + stride
    
    # 获取当前线程负责的元素
    if idx1 < len(data) and idx2 < len(data):
        val1 = data[idx1]
        val2 = data[idx2]
        
        # 比较并交换
        if direction == 1:  # 升序
            if val1 > val2:
                data[idx1] = val2
                data[idx2] = val1
        else:  # 降序
            if val1 < val2:
                data[idx1] = val2
                data[idx2] = val1


def bitonic_sort_step(data, threads, stride, block_size, direction):
    """
    执行Bitonic Sort的一步
    
    参数:
        data: 数据数组
        threads: 线程数
        stride: 比较间隔
        block_size: 每个比较组的元素数
        direction: 排序方向
    """
    @cuda.jit
    def kernel(data, n, stride, block_size, direction):
        tid = cuda.threadIdx.x
        start = cuda.blockIdx.x * block_size * 2
        
        # 计算组内位置
        group_idx = tid // stride
        if group_idx % 2 == 0:
            dir_to_use = 1  # 升序
        else:
            dir_to_use = 0  # 降序
        
        # 实际的比较-交换
        start_idx = start + (tid % (block_size * 2))
        partner_idx = start_idx + stride
        
        if start_idx < n and partner_idx < n:
            if dir_to_use == 1:  # 升序
                if data[start_idx] > data[partner_idx]:
                    temp = data[start_idx]
                    data[start_idx] = data[partner_idx]
                    data[partner_idx] = temp
            else:  # 降序
                if data[start_idx] < data[partner_idx]:
                    temp = data[start_idx]
                    data[start_idx] = data[partner_idx]
                    data[partner_idx] = temp
    
    blocks = (len(data) + threads - 1) // threads
    kernel[blocks, threads](data, len(data), stride, block_size, direction)


def gpu_bitonic_sort(data):
    """
    GPU位序列排序
    
    算法原理：
    1. 首先构建位序列（升序-降序交替）
    2. 然后逐步合并，最终得到完全有序序列
    
    参数:
        data: 输入数组（长度必须是2的幂）
    
    返回:
        排序后的数组
    """
    n = len(data)
    
    # 扩展到2的幂
    new_n = 1
    while new_n < n:
        new_n *= 2
    
    extended = np.zeros(new_n, dtype=np.float32)
    extended[:n] = data.astype(np.float32)
    
    # 复制到GPU
    d_data = cuda.to_device(extended)
    
    threads = 256
    block_size = 256
    
    # 阶段1: 2的幂次循环
    size = 2
    while size <= new_n:
        # 子阶段: 在size内进行bitonic比较
        stride = size // 2
        while stride > 0:
            blocks = (new_n + threads - 1) // threads
            block_sz = size
            
            @cuda.jit
            def bitonic_kernel(arr, n, stride, block_sz):
                tid = cuda.threadIdx.x
                # 每个block处理一个bitonic序列
                block_start = cuda.blockIdx.x * block_sz * 2
                pos_in_block = tid % block_sz
                
                # 计算全局索引
                idx1 = block_start + pos_in_block
                idx2 = idx1 + stride
                
                if idx1 < n and idx2 < n:
                    # 确定排序方向
                    group_idx = pos_in_block // stride
                    if (block_start // (block_sz * 2)) % 2 == 0:
                        dir_asc = group_idx % 2 == 0
                    else:
                        dir_asc = group_idx % 2 == 1
                    
                    if dir_asc:
                        if arr[idx1] > arr[idx2]:
                            temp = arr[idx1]
                            arr[idx1] = arr[idx2]
                            arr[idx2] = temp
                    else:
                        if arr[idx1] < arr[idx2]:
                            temp = arr[idx1]
                            arr[idx1] = arr[idx2]
                            arr[idx2] = temp
            
            bitonic_kernel[blocks, threads](d_data, new_n, stride, block_sz)
            
            stride //= 2
        
        size *= 2
    
    result = d_data.copy_to_host()
    return result[:n]


@cuda.jit
def odd_even_merge_kernel(data, n, phase):
    """
    奇偶归并排序的内核
    
    原理：
    - 奇数索引元素与下一个偶数索引元素比较
    - 偶数索引元素与下一个奇数索引元素比较
    - phase为0时执行奇-偶比较，phase为1时执行偶-奇比较
    
    参数:
        data: 数据数组
        n: 数组长度
        phase: 阶段（0或1）
    """
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    # 计算配对索引
    if phase == 0:
        # 奇-偶：比较索引i和i+1（i为奇数）
        if global_idx % 2 == 1 and global_idx + 1 < n:
            if data[global_idx] > data[global_idx + 1]:
                temp = data[global_idx]
                data[global_idx] = data[global_idx + 1]
                data[global_idx + 1] = temp
    else:
        # 偶-奇：比较索引i和i+1（i为偶数）
        if global_idx % 2 == 0 and global_idx + 1 < n:
            if data[global_idx] > data[global_idx + 1]:
                temp = data[global_idx]
                data[global_idx] = data[global_idx + 1]
                data[global_idx + 1] = temp


def gpu_odd_even_sort(data):
    """
    GPU奇偶排序（适用于小规模数据）
    
    参数:
        data: 输入数组
    
    返回:
        排序后的数组
    """
    n = len(data)
    d_data = cuda.to_device(data.astype(np.float32))
    
    threads = 256
    blocks = (n + threads - 1) // threads
    
    # 奇偶排序需要n轮
    for phase in range(n):
        odd_even_merge_kernel[blocks, threads](d_data, n, phase % 2)
    
    return d_data.copy_to_host()


def run_demo():
    """运行排序演示"""
    print("=" * 60)
    print("GPU并行排序 - Bitonic Sort与奇偶归并排序演示")
    print("=" * 60)
    
    sizes = [128, 256, 512, 1024]
    
    for n in sizes:
        data = np.random.rand(n).astype(np.float32)
        
        # CPU排序（基准）
        cpu_sorted = np.sort(data)
        
        # GPU Bitonic Sort
        gpu_bitonic = gpu_bitonic_sort(data)
        
        # 验证
        bitonic_correct = np.allclose(gpu_bitonic, cpu_sorted)
        
        print(f"\n数组长度: {n}")
        print(f"  原始数据前5个: {data[:5]}")
        print(f"  CPU排序前5个:   {cpu_sorted[:5]}")
        print(f"  GPU Bitonic前5个: {gpu_bitonic[:5]}")
        print(f"  Bitonic正确: {'✓' if bitonic_correct else '✗'}")
    
    print("\n" + "=" * 60)
    print("并行排序核心概念:")
    print("  1. Bitonic Sort: 基于比较网络，深度O(log²n)")
    print("  2. 奇偶归并排序: 适合GPU的银行排序变体")
    print("  3. 关键优化: 合并内存访问，最小化同步开销")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
