# -*- coding: utf-8 -*-

"""

算法实现：GPU并行算法 / gpu_parallel_reduction



本文件实现 gpu_parallel_reduction 相关的算法功能。

"""



import numpy as np

from numba import cuda

import numba





def cpu_reduce(data):

    """CPU归约（求和）作为基准"""

    return np.sum(data)





@cuda.jit

def gpu_reduce_kernel(data, result, n):

    """

    GPU并行归约内核（树形归约）

    

    算法原理：

    1. 第一轮：相邻元素配对相加，数据量减半

    2. 第二轮：继续配对，直到只剩一个元素

    3. 每个block独立归约，最后CPU汇总所有block结果

    

    参数:

        data: 输入数组

        result: 输出数组（每个block一个结果）

        n: 数组长度

    """

    # 共享内存：用于block内归约

    # 大小为每个block的线程数

    shared_data = cuda.shared.array(256, dtype=np.float32)

    

    # 全局索引计算

    tid = cuda.threadIdx.x  # 线程在block内的索引

    global_idx = cuda.blockIdx.x * cuda.blockDim.x + tid

    

    # 将数据加载到共享内存

    if global_idx < n:

        shared_data[tid] = data[global_idx]

    else:

        shared_data[tid] = 0.0

    

    cuda.syncthreads()

    

    # 树形归约

    # 每轮将相邻元素相加

    # stride从block大小的一半开始，每次除以2

    stride = cuda.blockDim.x // 2

    

    for s in range(stride, 0, s // 2 if s > 1 else 1):

        # 关键优化：只让stride以内的线程参与计算

        # 这样可以避免线程束分化

        if tid < s:

            shared_data[tid] += shared_data[tid + s]

        

        cuda.syncthreads()

        

        # 动态调整stride（避免死循环）

        if s <= 1:

            break

    

    # 将block的归约结果写回全局内存

    if tid == 0:

        result[cuda.blockIdx.x] = shared_data[0]





@cuda.jit

def gpu_reduce_optimized_kernel(data, result, n):

    """

    优化版GPU归约内核

    

    优化策略：

    1. 第一阶段：多个线程协作处理一个元素，减少内存访问

    2. 使用连续内存访问模式，提高带宽利用率

    

    参数:

        data: 输入数组

        result: 输出数组

        n: 数组长度

    """

    # 共享内存

    shared_data = cuda.shared.array(256, dtype=np.float32)

    

    tid = cuda.threadIdx.x

    global_idx = cuda.blockIdx.x * cuda.blockDim.x * 2 + tid

    

    # 第一阶段：每个线程处理一对元素

    temp_sum = 0.0

    if global_idx < n:

        temp_sum += data[global_idx]

    if global_idx + cuda.blockDim.x < n:

        temp_sum += data[global_idx + cuda.blockDim.x]

    

    shared_data[tid] = temp_sum

    cuda.syncthreads()

    

    # 树形归约

    stride = cuda.blockDim.x // 2

    while stride > 0:

        if tid < stride:

            shared_data[tid] += shared_data[tid + stride]

        cuda.syncthreads()

        stride //= 2

    

    if tid == 0:

        result[cuda.blockIdx.x] = shared_data[0]





def gpu_reduce(data, optimized=True):

    """

    GPU归约封装函数

    

    参数:

        data: 输入numpy数组

        optimized: 是否使用优化版本

    

    返回:

        归约结果（标量）

    """

    n = len(data)

    data = data.astype(np.float32)

    

    # 分配GPU内存

    d_data = cuda.to_device(data)

    

    # 计算grid和block配置

    threads_per_block = 256

    blocks_per_grid = (n + threads_per_block * 2 - 1) // (threads_per_block * 2)

    

    # 中间结果数组

    d_result = cuda.to_device(np.zeros(blocks_per_grid, dtype=np.float32))

    

    # 执行内核

    if optimized:

        gpu_reduce_optimized_kernel[blocks_per_grid, threads_per_block](d_data, d_result, n)

    else:

        gpu_reduce_kernel[blocks_per_grid, threads_per_block](d_data, d_result, n)

    

    # 获取中间结果

    intermediate = d_result.copy_to_host()

    

    # 如果有多个block的结果，需要继续归约

    # 这里简化处理，直接在CPU上完成最后归约

    while len(intermediate) > 1:

        blocks = (len(intermediate) + threads_per_block * 2 - 1) // (threads_per_block * 2)

        d_result = cuda.to_device(np.zeros(blocks, dtype=np.float32))

        d_data = cuda.to_device(intermediate.astype(np.float32))

        

        if optimized:

            gpu_reduce_optimized_kernel[blocks, threads_per_block](d_data, d_result, len(intermediate))

        else:

            gpu_reduce_kernel[blocks, threads_per_block](d_data, d_result, len(intermediate))

        

        intermediate = d_result.copy_to_host()

    

    return intermediate[0]





def run_demo():

    """运行归约演示"""

    print("=" * 60)

    print("GPU并行归约 - 树形归约算法演示")

    print("=" * 60)

    

    # 测试不同规模的数据

    sizes = [1000, 10000, 100000, 1000000]

    

    for n in sizes:

        # 生成随机数据

        data = np.random.rand(n).astype(np.float32)

        

        # CPU基准

        cpu_result = cpu_reduce(data)

        

        # GPU计算（基础版）

        gpu_result_basic = gpu_reduce(data, optimized=False)

        

        # GPU计算（优化版）

        gpu_result_opt = gpu_reduce(data, optimized=True)

        

        print(f"\n数据规模: {n:,}")

        print(f"  CPU结果:     {cpu_result:.4f}")

        print(f"  GPU基础版:   {gpu_result_basic:.4f} (误差: {abs(cpu_result - gpu_result_basic):.6f})")

        print(f"  GPU优化版:   {gpu_result_opt:.4f} (误差: {abs(cpu_result - gpu_result_opt):.6f})")

    

    print("\n" + "=" * 60)

    print("并行归约核心概念:")

    print("  1. 树形归约：每轮将数据量减半，log(n)轮完成")

    print("  2. 共享内存：block内线程共享中间结果")

    print("  3. 线程同步：每轮结束后同步，确保数据准备就绪")

    print("  4. 优化策略：")

    print("     - 避免线程束分化：只用前半部分线程")

    print("     - 合并内存访问：每个线程处理多个元素")

    print("     - 展开循环：减少分支判断开销")

    print("=" * 60)





if __name__ == "__main__":

    run_demo()

