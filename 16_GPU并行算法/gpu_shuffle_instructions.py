# -*- coding: utf-8 -*-

"""

算法实现：GPU并行算法 / gpu_shuffle_instructions



本文件实现 gpu_shuffle_instructions 相关的算法功能。

"""



import numpy as np

from numba import cuda

import numba





@cuda.jit

def shuffle_xor_demo_kernel(data, result, n):

    """

    演示洗牌指令shfl_xor

    

    xor交换原理：

    - lane_id xor mask 得到目标lane

    - 例如 lane_id=5 (0101), mask=1 (0001), xor后=4 (0100)

    - 可以用于蝴蝶网络、归约等算法

    

    参数:

        data: 输入数据

        result: 输出结果

        n: 数据长度

    """

    shared_data = cuda.shared.array(256, dtype=np.float32)

    

    tid = cuda.threadIdx.x

    global_idx = cuda.blockIdx.x * cuda.blockDim.x + tid

    

    # 加载数据

    if global_idx < n:

        value = data[global_idx]

    else:

        value = 0.0

    

    # 将数据广播到共享内存（模拟寄存器）

    shared_data[tid] = value

    

    cuda.syncthreads()

    

    # 模拟shfl_xor操作

    # 在lane 0-31和32-63之间交换（mask=32）

    # 在相邻线程间交换（mask=1）

    

    # 阶段1: 相邻线程交换 (mask=1)

    # 线程i和线程i xor 1交换

    for delta in [1, 2, 4, 8, 16]:

        # 模拟shfl_xor

        other_value = 0.0

        other_tid = tid ^ delta  # xor操作

        

        if other_tid < cuda.blockDim.x:

            other_value = shared_data[other_tid]

        

        # 同步模拟

        cuda.syncthreads()

        

        # 将数据存回共享内存

        shared_data[tid] = value + other_value

        cuda.syncthreads()

    

    # 写入结果

    if global_idx < n:

        result[global_idx] = shared_data[tid]





@cuda.jit

def shuffle_reduce_kernel(data, result, n):

    """

    使用洗牌指令进行并行归约

    

    传统方法需要共享内存和同步

    使用洗牌指令可以直接在线程束内交换数据

    

    参数:

        data: 输入数据

        result: 输出结果

        n: 数据长度

    """

    tid = cuda.threadIdx.x

    

    # 模拟寄存器变量（在线程束内快速访问）

    value = 0.0

    

    # 每个线程加载一个元素

    global_idx = cuda.blockIdx.x * cuda.blockDim.x + tid

    if global_idx < n:

        value = data[global_idx]

    

    # 洗牌归约：每轮将数据与邻居相加

    # 线程束大小为32，log2(32)=5轮

    for delta in [1, 2, 4, 8, 16]:

        # 模拟shfl_xor

        other_value = 0.0

        other_tid = tid ^ delta

        other_value = data[other_tid] if other_tid < n else 0.0

        

        # 使用shuffle_down语义：获取delta距离的值

        # 实际GPU上这是单条指令，无同步开销

        value += other_value

    

    # 只有lane 0保存最终结果

    if tid == 0:

        result[cuda.blockIdx.x] = value





@cuda.jit

def shuffle_broadcast_kernel(data, result, n):

    """

    演示洗牌广播操作

    

    使用shuffle将某个线程的值广播到所有线程

    

    参数:

        data: 输入数据

        result: 输出结果

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

    

    # 模拟shfl_up: 从编号更大的lane获取值

    # 线程0获取线程31的值（广播）

    broadcast_value = shared_data[0]  # 简化模拟

    

    # 使用多次xor实现广播

    # 先与lane 16交换，再与lane 8交换，... 最终所有lane都有相同的值

    if tid < 16:

        shared_data[tid] = shared_data[tid + 16]

    cuda.syncthreads()

    if tid < 8:

        shared_data[tid] = shared_data[tid + 8]

    cuda.syncthreads()

    if tid < 4:

        shared_data[tid] = shared_data[tid + 4]

    cuda.syncthreads()

    if tid < 2:

        shared_data[tid] = shared_data[tid + 2]

    cuda.syncthreads()

    if tid < 1:

        shared_data[tid] = shared_data[tid + 1]

    cuda.syncthreads()

    

    # 写入结果（所有线程现在都有相同的值）

    if global_idx < n:

        result[global_idx] = shared_data[0]





@cuda.jit

def shuffle_scan_kernel(data, result, n):

    """

    使用洗牌指令实现并行前缀和

    

    Blelloch算法的洗牌版本

    

    参数:

        data: 输入数据

        result: 输出结果

        n: 数据长度

    """

    shared_data = cuda.shared.array(256, dtype=np.float32)

    

    tid = cuda.threadIdx.x

    global_idx = cuda.blockIdx.x * cuda.blockDim.x + tid

    

    # 加载

    if global_idx < n:

        value = data[global_idx]

    else:

        value = 0.0

    

    shared_data[tid] = value

    cuda.syncthreads()

    

    # 洗牌版Up-Sweep

    for delta in [1, 2, 4, 8, 16]:

        if tid >= delta:

            value += shared_data[tid - delta]

        cuda.syncthreads()

        shared_data[tid] = value

        cuda.syncthreads()

    

    # 清零最后一个元素

    if tid == cuda.blockDim.x - 1:

        value = 0.0

    

    shared_data[tid] = value

    cuda.syncthreads()

    

    # 洗牌版Down-Sweep

    for delta in [16, 8, 4, 2, 1]:

        if tid >= delta:

            other_value = shared_data[tid - delta]

            shared_data[tid - delta] = value

            value += other_value

        cuda.syncthreads()

        shared_data[tid] = value

        cuda.syncthreads()

    

    # 写入结果

    if global_idx < n:

        result[global_idx] = shared_data[tid]





def run_demo():

    """运行洗牌指令演示"""

    print("=" * 60)

    print("GPU洗牌指令(Shuffle Instructions)演示")

    print("=" * 60)

    

    n = 1024

    data = np.random.rand(n).astype(np.float32)

    

    # 演示1: xor洗牌

    print("\n[演示1] XOR洗牌蝴蝶网络:")

    result1 = np.zeros(n, dtype=np.float32)

    d_data = cuda.to_device(data)

    d_result = cuda.to_device(result1)

    threads = 256

    blocks = (n + threads - 1) // threads

    

    shuffle_xor_demo_kernel[blocks, threads](d_data, d_result, n)

    result1 = d_result.copy_to_host()

    print(f"  输入前10个: {data[:10]}")

    print(f"  结果前10个: {result1[:10]}")

    

    # 演示2: 洗牌归约

    print("\n[演示2] 洗牌指令并行归约:")

    result2 = np.zeros(blocks, dtype=np.float32)

    d_result2 = cuda.to_device(result2)

    shuffle_reduce_kernel[blocks, threads](d_data, d_result2, n)

    reduce_result = d_result2.copy_to_host()

    print(f"  各block归约结果: {reduce_result}")

    print(f"  CPU验证求和: {np.sum(data):.4f}")

    

    # 演示3: 洗牌广播

    print("\n[演示3] 洗牌广播操作:")

    result3 = np.zeros(n, dtype=np.float32)

    d_result3 = cuda.to_device(result3)

    shuffle_broadcast_kernel[blocks, threads](d_data, d_result3, n)

    result3 = d_result3.copy_to_host()

    print(f"  广播后所有元素相同: {len(set(result3[:100])) == 1}")

    print(f"  广播值: {result3[0]:.4f}")

    

    # 演示4: 洗牌前缀和

    print("\n[演示4] 洗牌指令并行前缀和:")

    result4 = np.zeros(n, dtype=np.float32)

    d_result4 = cuda.to_device(result4)

    shuffle_scan_kernel[blocks, threads](d_data, d_result4, n)

    result4 = d_result4.copy_to_host()

    cpu_prefix = np.cumsum(data) - data  # CPU前缀和

    print(f"  输入前10个: {data[:10]}")

    print(f"  GPU前缀和前10个: {result4[:10]}")

    print(f"  CPU前缀和前10个: {cpu_prefix[:10]}")

    print(f"  误差: {np.max(np.abs(result4 - cpu_prefix)):.6f}")

    

    print("\n" + "=" * 60)

    print("洗牌指令核心概念:")

    print("  1. shfl_xor: 按mask异或交换lanes")

    print("  2. shfl_up/down: 向上/下传递数据")

    print("  3. 优势: 无需共享内存，无同步开销")

    print("  4. 应用: 归约、前缀和、蝴蝶网络")

    print("  5. 限制: 仅在线程束(32线程)内有效")

    print("=" * 60)





if __name__ == "__main__":

    run_demo()

