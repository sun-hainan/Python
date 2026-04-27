# -*- coding: utf-8 -*-
"""
算法实现：GPU并行算法 / cublas_cusparse

本文件实现 cublas_cusparse 相关的算法功能。
"""

import numpy as np
from numba import cuda
import numba


# ============================================================
# cuBLAS 级别1（向量-向量操作）
# ============================================================

def cpu_axpy(x, y, alpha):
    """
    CPU y = alpha*x + y (BLAS axpy)
    """
    return alpha * x + y


def cpu_dot(x, y):
    """
    CPU dot product (BLAS dot)
    """
    return np.dot(x, y)


@cuda.jit
def gpu_axpy_kernel(x, y, result, alpha, n):
    """
    GPU axpy操作: y = alpha*x + y
    
    参数:
        x: 输入向量
        y: 输入/输出向量
        result: 输出向量
        alpha: 标量
        n: 长度
    """
    idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if idx < n:
        result[idx] = alpha * x[idx] + y[idx]


@cuda.jit
def gpu_dot_kernel(x, y, result, n):
    """
    GPU点积（归约版本）
    
    参数:
        x, y: 输入向量
        result: 输出（单个值）
        n: 长度
    """
    shared_data = cuda.shared.array(256, dtype=np.float32)
    
    tid = cuda.threadIdx.x
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + tid
    
    # 加载
    if global_idx < n:
        shared_data[tid] = x[global_idx] * y[global_idx]
    else:
        shared_data[tid] = 0.0
    
    cuda.syncthreads()
    
    # 归约
    stride = cuda.blockDim.x // 2
    while stride > 0:
        if tid < stride:
            shared_data[tid] += shared_data[tid + stride]
        cuda.syncthreads()
        stride //= 2
    
    if tid == 0:
        cuda.atomic.add(result, 0, shared_data[0])


def gpu_axpy(x, y, alpha):
    """GPU axpy封装"""
    n = len(x)
    result = np.zeros(n, dtype=np.float32)
    
    d_x = cuda.to_device(x.astype(np.float32))
    d_y = cuda.to_device(y.astype(np.float32))
    d_result = cuda.to_device(result)
    
    threads = 256
    blocks = (n + threads - 1) // threads
    
    gpu_axpy_kernel[blocks, threads](d_x, d_y, d_result, np.float32(alpha), n)
    
    return d_result.copy_to_host()


def gpu_dot(x, y):
    """GPU dot封装"""
    n = len(x)
    result = np.zeros(1, dtype=np.float32)
    
    d_x = cuda.to_device(x.astype(np.float32))
    d_y = cuda.to_device(y.astype(np.float32))
    d_result = cuda.to_device(result)
    
    threads = 256
    blocks = 1
    
    gpu_dot_kernel[blocks, threads](d_x, d_y, d_result, n)
    
    return d_result.copy_to_host()[0]


# ============================================================
# cuBLAS 级别2（矩阵-向量操作）
# ============================================================

@cuda.jit
def gpu_gemv_kernel(A, x, y, m, n, trans, alpha, beta):
    """
    GPU矩阵向量乘法: y = alpha*op(A)*x + beta*y
    
    op(A) = A (trans=0) 或 A.T (trans=1)
    
    参数:
        A: 矩阵 (m×n)
        x: 向量 (n) 或 (m) 取决于trans
        y: 向量 (m) 或 (n)
        m, n: 矩阵维度
        trans: 是否转置
        alpha, beta: 标量
    """
    row = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    col = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y
    
    if trans == 0:  # 非转置：y = alpha*A*x + beta*y
        if row < m:
            total = 0.0
            for j in range(n):
                total += A[row * n + j] * x[j]
            y[row] = alpha * total + beta * y[row]
    else:  # 转置：y = alpha*A.T*x + beta*y
        if row < n:
            total = 0.0
            for i in range(m):
                total += A[i * n + row] * x[i]
            y[row] = alpha * total + beta * y[row]


def gpu_gemv(A, x, trans=0, alpha=1.0, beta=0.0):
    """GPU矩阵向量乘法封装"""
    m, n = A.shape
    
    d_A = cuda.to_device(A.astype(np.float32))
    
    if trans == 0:
        y = np.zeros(m, dtype=np.float32)
        d_x = cuda.to_device(x.astype(np.float32))
        d_y = cuda.to_device(y)
        
        threads = (16, 16)
        blocks = ((m + threads[0] - 1) // threads[0],
                  (1 + threads[1] - 1) // threads[1])
        
        gpu_gemv_kernel[blocks, threads](d_A, d_x, d_y, m, n, trans,
                                          np.float32(alpha), np.float32(beta))
        return d_y.copy_to_host()
    else:
        y = np.zeros(n, dtype=np.float32)
        d_x = cuda.to_device(x.astype(np.float32))
        d_y = cuda.to_device(y)
        
        threads = (16, 16)
        blocks = ((n + threads[0] - 1) // threads[0],
                  (1 + threads[1] - 1) // threads[1])
        
        gpu_gemv_kernel[blocks, threads](d_A, d_x, d_y, m, n, trans,
                                          np.float32(alpha), np.float32(beta))
        return d_y.copy_to_host()


# ============================================================
# cuBLAS 级别3（矩阵-矩阵操作）
# ============================================================

@cuda.jit
def gpu_gemm_kernel(A, B, C, m, n, k, trans_a, trans_b, alpha, beta):
    """
    GPU矩阵乘法: C = alpha*op(A)*op(B) + beta*C
    
    参数:
        A: m×k 或 k×m
        B: k×n 或 n×k
        C: m×n
        trans_a, trans_b: 是否转置
    """
    row = cuda.blockIdx.y * cuda.blockDim.y + cuda.threadIdx.y
    col = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if row < m and col < n:
        total = 0.0
        
        if trans_a == 0 and trans_b == 0:
            for p in range(k):
                total += A[row * k + p] * B[p * n + col]
        elif trans_a == 0 and trans_b == 1:
            for p in range(k):
                total += A[row * k + p] * B[col * k + p]
        elif trans_a == 1 and trans_b == 0:
            for p in range(k):
                total += A[p * m + row] * B[p * n + col]
        else:
            for p in range(k):
                total += A[p * m + row] * B[col * k + p]
        
        C[row * n + col] = alpha * total + beta * C[row * n + col]


def gpu_gemm(A, B, trans_a=0, trans_b=0, alpha=1.0, beta=0.0):
    """GPU矩阵乘法封装"""
    if trans_a == 0 and trans_b == 0:
        m, k = A.shape
        k2, n = B.shape
        assert k == k2, "矩阵维度不匹配"
        
        C = np.zeros((m, n), dtype=np.float32)
        
        d_A = cuda.to_device(A.astype(np.float32))
        d_B = cuda.to_device(B.astype(np.float32))
        d_C = cuda.to_device(C)
        
        threads = (16, 16)
        blocks = ((n + threads[0] - 1) // threads[0],
                  (m + threads[1] - 1) // threads[1])
        
        gpu_gemm_kernel[blocks, threads](d_A, d_B, d_C, m, n, k,
                                          trans_a, trans_b,
                                          np.float32(alpha), np.float32(beta))
        return d_C.copy_to_host()
    else:
        raise NotImplementedError("转置版本暂未实现")


# ============================================================
# cuSPARSE 示例
# ============================================================

def cpu_csr_spmv(csr_val, csr_row_ptr, csr_col_idx, x):
    """CPU CSR稀疏矩阵向量乘法"""
    n_rows = len(csr_row_ptr) - 1
    y = np.zeros(n_rows, dtype=np.float32)
    
    for i in range(n_rows):
        total = 0.0
        for j in range(csr_row_ptr[i], csr_row_ptr[i + 1]):
            col = csr_col_idx[j]
            val = csr_val[j]
            total += val * x[col]
        y[i] = total
    
    return y


@cuda.jit
def gpu_cusparse_csr_spmv_kernel(csr_val, csr_row_ptr, csr_col_idx, x, y, n_rows):
    """
    cuSPARSE风格CSR SpMV
    
    参数:
        csr_val: 非零元素值
        csr_row_ptr: 行指针
        csr_col_idx: 列索引
        x: 输入向量
        y: 输出向量
        n_rows: 行数
    """
    row = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if row < n_rows:
        total = 0.0
        row_start = csr_row_ptr[row]
        row_end = csr_row_ptr[row + 1]
        
        for j in range(row_start, row_end):
            col = csr_col_idx[j]
            val = csr_val[j]
            total += val * x[col]
        
        y[row] = total


def gpu_cusparse_csr_spmv(csr_val, csr_row_ptr, csr_col_idx, x):
    """GPU CSR SpMV封装"""
    n_rows = len(csr_row_ptr) - 1
    
    d_csr_val = cuda.to_device(csr_val)
    d_csr_row_ptr = cuda.to_device(csr_row_ptr)
    d_csr_col_idx = cuda.to_device(csr_col_idx)
    d_x = cuda.to_device(x.astype(np.float32))
    d_y = cuda.to_device(np.zeros(n_rows, dtype=np.float32))
    
    threads = 256
    blocks = (n_rows + threads - 1) // threads
    
    gpu_cusparse_csr_spmv_kernel[blocks, threads](
        d_csr_val, d_csr_row_ptr, d_csr_col_idx, d_x, d_y, n_rows
    )
    
    return d_y.copy_to_host()


def create_sparse_matrix(m, n, sparsity):
    """创建随机稀疏矩阵"""
    dense = np.random.rand(m, n).astype(np.float32)
    mask = np.random.rand(m, n) < sparsity
    dense[mask] = 0
    
    nnz = np.sum(~mask)
    
    csr_val = dense[~mask]
    csr_col_idx = np.argwhere(~mask)[:, 1].astype(np.int32)
    csr_row_ptr = np.zeros(m + 1, dtype=np.int32)
    
    row_counts = np.sum(~mask, axis=1)
    csr_row_ptr[1:] = np.cumsum(row_counts)
    
    return csr_val, csr_row_ptr, csr_col_idx


def run_demo():
    """运行cuBLAS/cuSPARSE演示"""
    print("=" * 60)
    print("cuBLAS与cuSPARSE使用示例")
    print("=" * 60)
    
    # ============================================================
    # cuBLAS Level 1: 向量操作
    # ============================================================
    print("\n[cuBLAS Level 1] 向量操作")
    
    n = 1000
    x = np.random.rand(n).astype(np.float32)
    y = np.random.rand(n).astype(np.float32)
    alpha = 2.5
    
    # axpy
    cpu_result_axpy = cpu_axpy(x, y, alpha)
    gpu_result_axpy = gpu_axpy(x, y, alpha)
    print(f"  axpy (y = {alpha}*x + y):")
    print(f"    CPU: {cpu_result_axpy[:5]}")
    print(f"    GPU: {gpu_result_axpy[:5]}")
    print(f"    误差: {np.max(np.abs(cpu_result_axpy - gpu_result_axpy)):.6f}")
    
    # dot
    cpu_dot_result = cpu_dot(x, y)
    gpu_dot_result = gpu_dot(x, y)
    print(f"  dot (x·y):")
    print(f"    CPU: {cpu_dot_result:.4f}")
    print(f"    GPU: {gpu_dot_result:.4f}")
    print(f"    误差: {abs(cpu_dot_result - gpu_dot_result):.6f}")
    
    # ============================================================
    # cuBLAS Level 2: 矩阵-向量操作
    # ============================================================
    print("\n[cuBLAS Level 2] 矩阵-向量操作")
    
    m, n_mat = 64, 32
    A = np.random.rand(m, n_mat).astype(np.float32)
    x = np.random.rand(n_mat).astype(np.float32)
    
    # gemv: y = A*x
    gpu_y = gpu_gemv(A, x, trans=0)
    cpu_y = A @ x
    print(f"  gemv (y = A*x, A: {m}×{n_mat}):")
    print(f"    CPU前5个: {cpu_y[:5]}")
    print(f"    GPU前5个: {gpu_y[:5]}")
    print(f"    误差: {np.max(np.abs(cpu_y - gpu_y)):.6f}")
    
    # ============================================================
    # cuBLAS Level 3: 矩阵-矩阵操作
    # ============================================================
    print("\n[cuBLAS Level 3] 矩阵-矩阵操作")
    
    m, k, n = 64, 32, 16
    A = np.random.rand(m, k).astype(np.float32)
    B = np.random.rand(k, n).astype(np.float32)
    
    # gemm: C = A*B
    gpu_C = gpu_gemm(A, B)
    cpu_C = A @ B
    print(f"  gemm (C = A*B, A: {m}×{k}, B: {k}×{n}):")
    print(f"    CPU结果形状: {cpu_C.shape}")
    print(f"    GPU结果形状: {gpu_C.shape}")
    print(f"    误差: {np.max(np.abs(cpu_C - gpu_C)):.6f}")
    
    # ============================================================
    # cuSPARSE: 稀疏矩阵操作
    # ============================================================
    print("\n[cuSPARSE] 稀疏矩阵操作")
    
    m, n_mat = 100, 100
    sparsity = 0.05
    
    csr_val, csr_row_ptr, csr_col_idx = create_sparse_matrix(m, n_mat, sparsity)
    x = np.random.rand(n_mat).astype(np.float32)
    
    print(f"  CSR SpMV (矩阵: {m}×{n_mat}, 稀疏度: {sparsity*100:.0f}%):")
    print(f"    非零元素: {len(csr_val)}")
    
    cpu_y = cpu_csr_spmv(csr_val, csr_row_ptr, csr_col_idx, x)
    gpu_y = gpu_cusparse_csr_spmv(csr_val, csr_row_ptr, csr_col_idx, x)
    
    print(f"    CPU前5个: {cpu_y[:5]}")
    print(f"    GPU前5个: {gpu_y[:5]}")
    print(f"    误差: {np.max(np.abs(cpu_y - gpu_y)):.6f}")
    
    print("\n" + "=" * 60)
    print("cuBLAS/cuSPARSE核心概念:")
    print("  1. cuBLAS: GPU优化的BLAS实现，level 1/2/3分别对应向量/矩阵向量/矩阵运算")
    print("  2. 命名规则: gemv(矩阵向量), gemm(矩阵乘法), axpy(向量运算)")
    print("  3. cuSPARSE: 稀疏矩阵专用库，高效处理非零元素")
    print("  4. 优势: 库函数经过高度优化，比手写代码更快")
    print("  5. 注意事项: 列主序vs行主序，数据类型转换")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
