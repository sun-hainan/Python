# -*- coding: utf-8 -*-

"""

算法实现：GPU并行算法 / gpu_matrix_multiply



本文件实现 gpu_matrix_multiply 相关的算法功能。

"""



import numpy as np

from numba import cuda

import math





# Tile大小定义：16x16是CUDA常用的最佳tile大小

TILE_SIZE = 16





def cpu_matrix_multiply(A, B, n):

    """

    CPU矩阵乘法（O(n³)）作为基准

    

    参数:

        A: n×n 矩阵

        B: n×n 矩阵

        n: 矩阵维度

    

    返回:

        C: n×n 结果矩阵

    """

    C = np.zeros((n, n), dtype=np.float32)

    for i in range(n):

        for j in range(n):

            total = 0.0

            for k in range(n):

                total += A[i, k] * B[k, j]

            C[i, j] = total

    return C





@cuda.jit

def gpu_matrix_multiply_kernel(A, B, C, n):

    """

    GPU分块矩阵乘法内核

    

    算法原理：

    1. 每个线程负责计算C中的一个元素

    2. 将A的一行和B的一列划分为多个tile

    3. 每个tile加载到共享内存，减少全局内存访问

    

    参数:

        A: n×n 左矩阵（行优先存储）

        B: n×n 右矩阵（行优先存储）

        C: n×n 结果矩阵

        n: 矩阵维度

    """

    # 共享内存声明：存储当前处理的Tile

    # tile_A: 存放A的当前tile（一行的一部分）

    # tile_B: 存放B的当前tile（一列的一部分）

    tile_A = cuda.shared.array((TILE_SIZE, TILE_SIZE), dtype=np.float32)

    tile_B = cuda.shared.array((TILE_SIZE, TILE_SIZE), dtype=np.float32)

    

    # 计算当前线程负责的全局行列索引

    row = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y

    col = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x

    

    # 检查边界

    if row >= n or col >= n:

        return

    

    # 累积计算结果（用于矩阵乘法的累加）

    result = 0.0

    

    # 循环遍历所有tile

    # numTiles = ceil(n / TILE_SIZE)

    num_tiles = (n + TILE_SIZE - 1) // TILE_SIZE

    

    for tile_idx in range(num_tiles):

        # 计算当前tile在全局内存中的起始位置

        # tile在A中：行=row, 列=tile_idx*TILE_SIZE

        # tile在B中：行=tile_idx*TILE_SIZE, 列=col

        a_start_col = tile_idx * TILE_SIZE

        b_start_row = tile_idx * TILE_SIZE

        

        # 将数据从全局内存加载到共享内存

        # 注意：需要处理边界情况（tile可能不完整）

        

        # 加载A的tile（当前行，tile内的列）

        a_tile_row = cuda.threadIdx.y

        a_tile_col = cuda.threadIdx.x

        a_global_row = row

        a_global_col = a_start_col + a_tile_col

        if a_global_col < n:

            tile_A[a_tile_row, a_tile_col] = A[a_global_row, a_global_col]

        else:

            tile_A[a_tile_row, a_tile_col] = 0.0

        

        # 加载B的tile（tile内的行，当前列）

        b_tile_row = cuda.threadIdx.y

        b_tile_col = cuda.threadIdx.x

        b_global_row = b_start_row + b_tile_row

        b_global_col = col

        if b_global_row < n:

            tile_B[b_tile_row, b_tile_col] = B[b_global_row, b_global_col]

        else:

            tile_B[b_tile_row, b_tile_col] = 0.0

        

        # 同步：等待所有线程完成数据加载

        cuda.syncthreads()

        

        # 计算当前tile的贡献

        # C[row, col] += sum(A[row, k] * B[k, col]) for k in current tile

        for k in range(TILE_SIZE):

            result += tile_A[cuda.threadIdx.y, k] * tile_B[k, cuda.threadIdx.x]

        

        # 同步：确保当前tile计算完成后再加载下一个tile

        cuda.syncthreads()

    

    # 写入结果

    C[row, col] = result





def gpu_matrix_multiply(A, B):

    """

    GPU矩阵乘法封装函数

    

    参数:

        A: n×n numpy数组

        B: n×n numpy数组

    

    返回:

        C: n×n 结果矩阵

    """

    n = A.shape[0]

    

    # 确保数据类型正确

    A = A.astype(np.float32)

    B = B.astype(np.float32)

    C = np.zeros((n, n), dtype=np.float32)

    

    # 传输数据到GPU

    d_A = cuda.to_device(A)

    d_B = cuda.to_device(B)

    d_C = cuda.to_device(C)

    

    # 配置grid和block

    # 使用二维结构，每个block是TILE_SIZE×TILE_SIZE

    threads_per_block = (TILE_SIZE, TILE_SIZE)

    blocks_per_grid_x = (n + TILE_SIZE - 1) // TILE_SIZE

    blocks_per_grid_y = (n + TILE_SIZE - 1) // TILE_SIZE

    blocks_per_grid = (blocks_per_grid_x, blocks_per_grid_y)

    

    # 执行内核

    gpu_matrix_multiply_kernel[blocks_per_grid, threads_per_block](d_A, d_B, d_C, n)

    

    # 复制结果回主机

    return d_C.copy_to_host()





def run_demo():

    """运行矩阵乘法演示"""

    print("=" * 60)

    print("GPU矩阵乘法 - 分块Tile算法演示")

    print("=" * 60)

    

    # 测试不同大小的矩阵

    sizes = [64, 128, 256]

    

    for n in sizes:

        print(f"\n矩阵维度: {n}×{n}")

        

        # 生成随机测试矩阵

        A = np.random.rand(n, n).astype(np.float32)

        B = np.random.rand(n, n).astype(np.float32)

        

        # GPU计算

        C_gpu = gpu_matrix_multiply(A, B)

        

        # CPU计算（用于验证）

        C_cpu = cpu_matrix_multiply(A, B, n)

        

        # 验证结果（允许浮点误差）

        max_error = np.max(np.abs(C_gpu - C_cpu))

        print(f"  最大误差: {max_error:.6f}")

        print(f"  结果正确: {'✓' if max_error < 1e-4 else '✗'}")

    

    print("\n" + "=" * 60)

    print("分块矩阵乘法核心思想:")

    print("  1. 将大矩阵划分为TILE_SIZE×TILE_SIZE的小块")

    print("  2. 每个块加载到共享内存，减少全局内存访问")

    print("  3. 一个线程负责计算结果矩阵中的一个元素")

    print("  4. 通过tiling可以成百倍提升内存访问效率")

    print("=" * 60)





if __name__ == "__main__":

    run_demo()

