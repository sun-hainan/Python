# -*- coding: utf-8 -*-

"""

算法实现：GPU并行算法 / gpu_sparse_matrix



本文件实现 gpu_sparse_matrix 相关的算法功能。

"""



import numpy as np

from numba import cuda

import numba





def cpu_csr_spmv(csr_val, csr_row_ptr, csr_col_idx, x, n_rows):

    """

    CPU CSR格式稀疏矩阵向量乘法（基准）

    

    参数:

        csr_val: 非零元素值数组

        csr_row_ptr: 每行起始索引

        csr_col_idx: 非零元素列索引

        x: 输入向量

        n_rows: 矩阵行数

    

    返回:

        y: 输出向量

    """

    y = np.zeros(n_rows, dtype=np.float32)

    

    for i in range(n_rows):

        total = 0.0

        # 遍历第i行的所有非零元素

        for j in range(csr_row_ptr[i], csr_row_ptr[i + 1]):

            col = csr_col_idx[j]

            val = csr_val[j]

            total += val * x[col]

        y[i] = total

    

    return y





@cuda.jit

def gpu_csr_spmv_kernel(csr_val, csr_row_ptr, csr_col_idx, x, y, n_rows):

    """

    GPU CSR格式稀疏矩阵向量乘法内核

    

    算法原理：

    - 每个线程负责计算结果向量中的一个元素

    - 通过csr_row_ptr确定每行的非零元素范围

    - 并行访问csr_val和csr_col_idx

    

    参数:

        csr_val: 非零元素值数组

        csr_row_ptr: 每行起始索引数组

        csr_col_idx: 非零元素列索引数组

        x: 输入向量

        y: 输出向量

        n_rows: 矩阵行数

    """

    row = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x

    

    if row < n_rows:

        total = 0.0

        

        # 获取当前行在csr_val中的起止索引

        row_start = csr_row_ptr[row]

        row_end = csr_row_ptr[row + 1]

        

        # 遍历该行的所有非零元素

        for j in range(row_start, row_end):

            col = csr_col_idx[j]

            val = csr_val[j]

            total += val * x[col]

        

        y[row] = total





@cuda.jit

def gpu_csr_spmv_warp_kernel(csr_val, csr_row_ptr, csr_col_idx, x, y, n_rows):

    """

    GPU CSR SpMV优化内核（线程束级别）

    

    优化策略：

    - 多个相邻线程协作处理一行

    - 减少线程发散

    - 更好地利用内存合并访问

    

    参数:

        csr_val: 非零元素值数组

        csr_row_ptr: 每行起始索引数组

        csr_col_idx: 非零元素列索引数组

        x: 输入向量

        y: 输出向量

        n_rows: 矩阵行数

    """

    # 每个线程束处理一行

    warp_id = cuda.threadIdx.x // 32

    lane_id = cuda.threadIdx.x % 32

    

    # 线程束内的第一个线程负责该行的索引范围

    row = cuda.blockIdx.x * (cuda.blockDim.x // 32) + warp_id

    

    if row < n_rows:

        row_start = csr_row_ptr[row]

        row_end = csr_row_ptr[row + 1]

        row_nnz = row_end - row_start  # 该行非零元素数量

        

        # 线程束内线程协作累加

        thread_sum = 0.0

        

        # 每个线程处理多个非零元素

        for j in range(row_start + lane_id, row_end, 32):

            col = csr_col_idx[j]

            val = csr_val[j]

            thread_sum += val * x[col]

        

        # 线程束内归约

        # 模拟shfl指令

        shared = cuda.shared.array(32, dtype=np.float32)

        shared[lane_id] = thread_sum

        cuda.syncthreads()

        

        if lane_id < 16:

            shared[lane_id] += shared[lane_id + 16]

        cuda.syncthreads()

        if lane_id < 8:

            shared[lane_id] += shared[lane_id + 8]

        cuda.syncthreads()

        if lane_id < 4:

            shared[lane_id] += shared[lane_id + 4]

        cuda.syncthreads()

        if lane_id < 2:

            shared[lane_id] += shared[lane_id + 2]

        cuda.syncthreads()

        if lane_id < 1:

            shared[0] += shared[1]

        

        if lane_id == 0:

            y[row] = shared[0]





def create_sparse_matrix(m, n, sparsity):

    """

    创建稀疏矩阵并返回CSR格式

    

    参数:

        m: 行数

        n: 列数

        sparsity: 稀疏度（0-1之间，1表示全是零）

    

    返回:

        csr_val, csr_row_ptr, csr_col_idx, dense_matrix

    """

    # 生成稀疏矩阵

    dense = np.zeros((m, n), dtype=np.float32)

    nnz = int(m * n * (1 - sparsity))  # 非零元素数量

    

    # 随机放置非零元素

    rows = np.random.randint(0, m, nnz)

    cols = np.random.randint(0, n, nnz)

    vals = np.random.rand(nnz).astype(np.float32)

    

    for i in range(nnz):

        dense[rows[i], cols[i]] = vals[i]

    

    # 转换为CSR格式

    csr_val = []

    csr_col_idx = []

    csr_row_ptr = [0]

    

    for i in range(m):

        count = 0

        for j in range(n):

            if dense[i, j] != 0:

                csr_val.append(dense[i, j])

                csr_col_idx.append(j)

                count += 1

        csr_row_ptr.append(csr_row_ptr[-1] + count)

    

    csr_val = np.array(csr_val, dtype=np.float32)

    csr_col_idx = np.array(csr_col_idx, dtype=np.int32)

    csr_row_ptr = np.array(csr_row_ptr, dtype=np.int32)

    

    return csr_val, csr_row_idx, csr_col_idx, dense





def create_sparse_matrix_v2(m, n, sparsity):

    """

    创建稀疏矩阵并返回CSR格式（简化版本）

    """

    # 生成随机稀疏矩阵

    dense = np.random.rand(m, n).astype(np.float32)

    

    # 应用稀疏度

    mask = np.random.rand(m, n) < sparsity

    dense[mask] = 0

    

    # 统计非零元素

    nnz = np.sum(~mask)

    

    # 构建CSR格式

    csr_val = dense[~mask].astype(np.float32)

    csr_col_idx = np.argwhere(~mask)[:, 1].astype(np.int32)

    csr_row_ptr = np.zeros(m + 1, dtype=np.int32)

    

    row_counts = np.sum(~mask, axis=1)

    csr_row_ptr[1:] = np.cumsum(row_counts)

    

    return csr_val, csr_row_ptr, csr_col_idx, dense





def gpu_csr_spmv(csr_val, csr_row_ptr, csr_col_idx, x, n_rows):

    """

    GPU CSR SpMV封装函数

    

    参数:

        csr_val: 非零元素值数组

        csr_row_ptr: 每行起始索引数组

        csr_col_idx: 非零元素列索引数组

        x: 输入向量

        n_rows: 矩阵行数

    

    返回:

        y: 输出向量

    """

    n = len(x)

    

    # 传输数据到GPU

    d_csr_val = cuda.to_device(csr_val)

    d_csr_row_ptr = cuda.to_device(csr_row_ptr)

    d_csr_col_idx = cuda.to_device(csr_col_idx)

    d_x = cuda.to_device(x)

    d_y = cuda.to_device(np.zeros(n_rows, dtype=np.float32))

    

    # 配置grid和block

    threads = 256

    blocks = (n_rows + threads - 1) // threads

    

    # 执行内核

    gpu_csr_spmv_kernel[blocks, threads](d_csr_val, d_csr_row_ptr, d_csr_col_idx, d_x, d_y, n_rows)

    

    return d_y.copy_to_host()





def run_demo():

    """运行稀疏矩阵乘法演示"""

    print("=" * 60)

    print("GPU稀疏矩阵乘法 - CSR格式演示")

    print("=" * 60)

    

    # 测试不同规模的稀疏矩阵

    sizes = [(100, 100, 0.1), (500, 500, 0.05), (1000, 1000, 0.01)]

    

    for m, n, sparsity in sizes:

        print(f"\n矩阵尺寸: {m}×{n}, 稀疏度: {sparsity*100:.0f}%")

        

        # 创建稀疏矩阵

        csr_val, csr_row_ptr, csr_col_idx, dense = create_sparse_matrix_v2(m, n, sparsity)

        x = np.random.rand(n).astype(np.float32)

        

        print(f"  非零元素数量: {len(csr_val):,}")

        print(f"  压缩率: {len(csr_val)/(m*n)*100:.2f}%")

        

        # CPU计算

        y_cpu = cpu_csr_spmv(csr_val, csr_row_ptr, csr_col_idx, x, m)

        

        # GPU计算

        y_gpu = gpu_csr_spmv(csr_val, csr_row_ptr, csr_col_idx, x, m)

        

        # 验证

        max_error = np.max(np.abs(y_cpu - y_gpu))

        print(f"  最大误差: {max_error:.6f}")

        print(f"  结果正确: {'✓' if max_error < 1e-4 else '✗'}")

    

    print("\n" + "=" * 60)

    print("稀疏矩阵CSR格式核心概念:")

    print("  1. CSR格式: val存储值，row_ptr指向每行起始，col_idx存储列")

    print("  2. 优势: 高压缩率，适合行优先访问")

    print("  3. SpMV: 稀疏矩阵向量乘法，并行度高")

    print("  4. 优化: 线程束协作，减少发散")

    print("  5. 应用: 图算法、有限元、机器学习稀疏操作")

    print("=" * 60)





if __name__ == "__main__":

    run_demo()

