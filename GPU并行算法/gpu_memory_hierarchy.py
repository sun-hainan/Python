# -*- coding: utf-8 -*-
"""
算法实现：GPU并行算法 / gpu_memory_hierarchy

本文件实现 gpu_memory_hierarchy 相关的算法功能。
"""

import numpy as np
from numba import cuda
import numba


@cuda.jit
def global_memory_access_kernel(data, result, n):
    """
    演示全局内存访问模式
    
    全局内存特点：
    - 容量大(数GB)，但延迟高(数百周期)
    - 需要合并访问才能高效利用带宽
    - 通过L1/L2缓存加速
    
    参数:
        data: 输入数据
        result: 输出结果
        n: 数据长度
    """
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if global_idx < n:
        # 合并访问：相邻线程访问相邻内存
        # 这是高效的访问模式
        value = data[global_idx]
        result[global_idx] = value * 2.0


@cuda.jit
def shared_memory_demo_kernel(data, result, n):
    """
    演示共享内存使用
    
    共享内存特点：
    - 位于芯片上，延迟极低(~1周期)
    - 需要手动管理加载/存储
    - 同一block内线程共享
    
    参数:
        data: 输入数据
        result: 输出结果
        n: 数据长度
    """
    # 共享内存声明
    shared_data = cuda.shared.array(256, dtype=np.float32)
    
    tid = cuda.threadIdx.x
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + tid
    
    # 加载数据到共享内存
    if global_idx < n:
        shared_data[tid] = data[global_idx]
    
    # 同步等待所有线程完成加载
    cuda.syncthreads()
    
    # 在共享内存中进行计算
    if global_idx > 0 and global_idx < n:
        # 利用共享内存的高速访问
        left = shared_data[tid - 1]
        right = shared_data[tid]
        shared_data[tid] = (left + right) / 2.0
    
    cuda.syncthreads()
    
    # 写回全局内存
    if global_idx < n:
        result[global_idx] = shared_data[tid]


@cuda.jit
def register_demo_kernel(data, result, n):
    """
    演示寄存器的使用
    
    寄存器特点：
    - 每个线程私有
    - 速度最快(~0周期)
    - 数量有限，超出则溢出到本地内存
    
    参数:
        data: 输入数据
        result: 输出结果
        n: 数据长度
    """
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if global_idx < n:
        # 寄存器变量：编译器自动管理
        value = data[global_idx]
        
        # 多个算术操作
        temp1 = value * 3.14
        temp2 = temp1 + 10.0
        temp3 = temp2 / 2.0
        temp4 = temp3 - 5.0
        
        result[global_idx] = temp4


@cuda.jit
def memory_coalescing_kernel(data, result, n):
    """
    演示内存合并访问
    
    合并访问：相邻线程访问相邻地址
    非合并访问：线程访问分散地址
    
    参数:
        data: 输入数据
        result: 输出结果
        n: 数据长度
    """
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if global_idx < n:
        # 合并访问：线程i访问data[i]
        coalesced_val = data[global_idx]
        
        # 非合并访问：线程i访问data[i*stride]
        # 这会导致内存访问效率低下
        stride = 73  # 一个质数，打散访问模式
        non_coalesced_idx = (global_idx * stride) % n
        non_coalesced_val = data[non_coalesced_idx]
        
        result[global_idx] = coalesced_val + non_coalesced_val * 0.1


@cuda.jit
def constant_memory_kernel(data, multiplier, result, n):
    """
    演示常量内存的使用
    
    常量内存特点：
    - 只读，适合存储不变的数据
    - 通过缓存加速读取
    - 所有线程同时读取相同位置时效率最高
    
    参数:
        data: 输入数据
        multiplier: 常量乘数
        result: 输出结果
        n: 数据长度
    """
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if global_idx < n:
        # 使用常量内存进行计算
        result[global_idx] = data[global_idx] * multiplier


def run_demo():
    """运行内存层次演示"""
    print("=" * 60)
    print("GPU内存层次结构详解")
    print("=" * 60)
    
    n = 1000
    data = np.random.rand(n).astype(np.float32)
    result = np.zeros(n, dtype=np.float32)
    
    threads = 256
    blocks = (n + threads - 1) // threads
    
    # 全局内存演示
    print("\n[演示1] 全局内存访问:")
    d_data = cuda.to_device(data)
    d_result = cuda.to_device(result)
    global_memory_access_kernel[blocks, threads](d_data, d_result, n)
    result = d_result.copy_to_host()
    print(f"  结果前5个: {result[:5]}")
    print(f"  验证: data[i]*2 = {data[0]*2:.4f}, result[0] = {result[0]:.4f}")
    
    # 共享内存演示
    print("\n[演示2] 共享内存（相邻平均）:")
    d_result = cuda.to_device(np.zeros(n, dtype=np.float32))
    shared_memory_demo_kernel[blocks, threads](d_data, d_result, n)
    result = d_result.copy_to_host()
    print(f"  结果前10个: {result[:10]}")
    expected = (data[:10] + np.roll(data[:10], 1)) / 2.0
    expected[0] = data[0]
    print(f"  预期前10个: {expected}")
    
    # 寄存器演示
    print("\n[演示3] 寄存器使用:")
    d_result = cuda.to_device(np.zeros(n, dtype=np.float32))
    register_demo_kernel[blocks, threads](d_data, d_result, n)
    result = d_result.copy_to_host()
    print(f"  结果前5个: {result[:5]}")
    expected = (((data[:5] * 3.14) + 10.0) / 2.0) - 5.0
    print(f"  预期前5个: {expected}")
    
    # 内存合并访问演示
    print("\n[演示4] 内存合并vs非合并:")
    d_result = cuda.to_device(np.zeros(n, dtype=np.float32))
    memory_coalescing_kernel[blocks, threads](d_data, d_result, n)
    result = d_result.copy_to_host()
    print(f"  结果前10个: {result[:10]}")
    
    # 常量内存演示
    print("\n[演示5] 常量内存:")
    multiplier = np.float32(2.5)
    d_multiplier = cuda.to_device(np.array([multiplier]))
    d_result = cuda.to_device(np.zeros(n, dtype=np.float32))
    constant_memory_kernel[blocks, threads](d_data, d_multiplier, d_result, n)
    result = d_result.copy_to_host()
    print(f"  乘数: {multiplier}")
    print(f"  结果前5个: {result[:5]}")
    print(f"  验证: data[i]*2.5 = {data[0]*2.5:.4f}, result[0] = {result[0]:.4f}")
    
    print("\n" + "=" * 60)
    print("GPU内存层次总结:")
    print("  ┌─────────────────┬──────────┬────────────┐")
    print("  │ 内存类型         │ 延迟     │ 作用域     │")
    print("  ├─────────────────┼──────────┼────────────┤")
    print("  │ 寄存器          │ ~0周期   │ 线程私有   │")
    print("  │ 本地内存        │ ~400周期 │ 线程私有   │")
    print("  │ 共享内存        │ ~1周期   │ block内共享│")
    print("  │ 全局内存        │ ~400周期 │ 全局可见   │")
    print("  │ 常量内存        │ ~1周期   │ 全局只读   │")
    print("  └─────────────────┴──────────┴────────────┘")
    print("  优化策略:")
    print("    1. 尽量使用寄存器，避免溢出")
    print("    2. 共享内存复用数据，减少全局内存访问")
    print("    3. 合并内存访问，提高带宽利用率")
    print("    4. 访问模式尽量一致，便于缓存")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
