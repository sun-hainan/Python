# -*- coding: utf-8 -*-

"""

算法实现：GPU并行算法 / cuda_programming_model



本文件实现 cuda_programming_model 相关的算法功能。

"""



import numpy as np

from numba import cuda

import numba





def cpu_version(data, scale):

    """CPU版本：简单元素级运算（作为对比基准）"""

    result = np.zeros_like(data)

    for i in range(len(data)):

        result[i] = data[i] * scale + 10

    return result





@cuda.jit

def gpu_thread_hierarchy_kernel(data, result, scale, n):

    """

    CUDA内核：演示线程层次结构

    

    参数:

        data: 输入数组

        result: 输出数组

        scale: 缩放因子

        n: 数组长度

    """

    # cuda.blockIdx.x: 当前block在grid中的索引

    # cuda.blockIdx.y: y方向block索引

    # cuda.blockIdx.z: z方向block索引

    block_idx_x = cuda.blockIdx.x

    

    # cuda.threadIdx.x: 当前线程在block内的索引

    # cuda.threadIdx.y: y方向线程索引

    # cuda.threadIdx.z: z方向线程索引

    thread_idx_x = cuda.threadIdx.x

    

    # cuda.blockDim.x: 每个block在x方向的线程数

    # cuda.blockDim.y: 每个block在y方向的线程数

    block_dim_x = cuda.blockDim.x

    

    # 计算当前线程对应的全局数据索引

    # 全局索引 = block在grid中的偏移 * block内线程数 + 线程在block内的偏移

    global_idx = block_idx_x * block_dim_x + thread_idx_x

    

    # 边界检查：确保不越界

    if global_idx < n:

        result[global_idx] = data[global_idx] * scale + 10





@cuda.jit

def gpu_shared_memory_kernel(data, result, n):

    """

    CUDA内核：演示共享内存的使用

    

    共享内存特点：

    - 位于芯片上，访问延迟远低于全局内存

    - 同一个block内的线程共享

    - 使用shared关键字声明

    

    参数:

        data: 输入数组

        result: 输出数组

        n: 数组长度

    """

    # 声明共享内存，大小为每个block的线程数

    # shared内存位于芯片上，访问速度极快

    shared_data = cuda.shared.array(256, dtype=numba.float32)

    

    # 计算全局索引和线程索引

    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x

    thread_idx = cuda.threadIdx.x

    

    # 边界检查：数据加载到共享内存

    if global_idx < n:

        shared_data[thread_idx] = data[global_idx]

    

    # 同步：等待所有线程完成数据加载

    # 这是使用共享内存的关键步骤！

    cuda.syncthreads()

    

    # 在共享内存中进行计算（这里以简单的累加为例）

    if global_idx < n and thread_idx > 0:

        shared_data[thread_idx] += shared_data[thread_idx - 1]

    

    # 再次同步，然后写回全局内存

    cuda.syncthreads()

    

    if global_idx < n:

        result[global_idx] = shared_data[thread_idx]





def get_cuda_config(n, threads_per_block=256):

    """

    计算CUDA网格和block配置

    

    参数:

        n: 数据总量

        threads_per_block: 每个block的线程数（受硬件限制）

    

    返回:

        blocks_per_grid: grid中block的数量

        threads_per_block: 每个block的线程数

    """

    # 确保线程数是256的倍数（硬件最佳实践）

    if threads_per_block > 256:

        threads_per_block = 256

    

    # 计算需要的block数量，向上取整

    blocks_per_grid = (n + threads_per_block - 1) // threads_per_block

    

    return blocks_per_grid, threads_per_block





def run_cuda_demo():

    """运行CUDA并行编程演示"""

    print("=" * 60)

    print("CUDA并行编程模型演示")

    print("=" * 60)

    

    # 检查CUDA是否可用

    if cuda.is_available():

        print(f"CUDA设备: {cuda.get_current_device().name}")

    else:

        print("警告: CUDA不可用，将使用模拟模式")

    

    # 创建测试数据

    n = 1000

    data = np.random.rand(n).astype(np.float32)

    result = np.zeros(n, dtype=np.float32)

    

    # 配置grid和block

    blocks_per_grid, threads_per_block = get_cuda_config(n)

    print(f"\n线程配置: {blocks_per_grid} blocks × {threads_per_block} threads/block")

    print(f"总线程数: {blocks_per_grid * threads_per_block}")

    

    # 复制数据到GPU

    d_data = cuda.to_device(data)

    d_result = cuda.to_device(result)

    

    # 执行内核：线程层次演示

    print("\n[演示1] 线程层次结构:")

    gpu_thread_hierarchy_kernel[blocks_per_grid, threads_per_block](d_data, d_result, 2.0, n)

    result = d_result.copy_to_host()

    print(f"  结果前5个元素: {result[:5]}")

    print(f"  计算验证 (data[i]*2+10): {data[0]*2+10:.4f}")

    

    # 重新准备数据

    d_result = cuda.to_device(np.zeros(n, dtype=np.float32))

    

    # 执行内核：共享内存演示

    print("\n[演示2] 共享内存（前缀累加）:")

    gpu_shared_memory_kernel[blocks_per_grid, threads_per_block](d_data, d_result, n)

    result = d_result.copy_to_host()

    print(f"  结果前10个元素: {result[:10]}")

    

    # CPU版本对比

    print("\n[对比] CPU版本结果前5个:")

    cpu_result = cpu_version(data, 2.0)

    print(f"  {cpu_result[:5]}")

    

    print("\n" + "=" * 60)

    print("CUDA编程模型核心概念总结:")

    print("  1. Grid/Block/Thread三层层次结构")

    print("  2. blockDim: 每个block的维度")

    print("  3. blockIdx: 当前block在grid中的索引")

    print("  4. threadIdx: 当前线程在block中的索引")

    print("  5. 共享内存: 同一block内线程共享，访问高速")

    print("  6. syncthreads(): 线程同步屏障")

    print("=" * 60)





if __name__ == "__main__":

    run_cuda_demo()

