"""
稀疏矩阵CSR格式与运算
=======================
本模块实现 Compressed Sparse Row (CSR) 格式：
- 高效存储稀疏矩阵（节省内存）
- 支持基本的矩阵运算
- 与稠密矩阵的转换

CSR格式概述：
- data: 非零元素值数组
- indices: 对应列索引数组  
- indptr: 每行起始索引数组（长度为rows+1）

Author: 算法库
"""

import numpy as np
from typing import Tuple, List, Optional


class CSRMatrix:
    """
    压缩稀疏行格式矩阵类
    
    存储结构:
        data: 非零元素值，长度为nnz（非零元素个数）
        indices: 列索引，长度为nnz
        indptr: 行指针，长度为rows+1
            第i行元素对应 data[indptr[i]:indptr[i+1]]
            对应列索引为 indices[indptr[i]:indptr[i+1]]
    """
    
    def __init__(self, data: np.ndarray, indices: np.ndarray, indptr: np.ndarray):
        """
        初始化CSR矩阵
        
        参数:
            data: 非零元素数组
            indices: 列索引数组
            indptr: 行指针数组
        """
        self.data = data
        self.indices = indices
        self.indptr = indptr
        self.shape = (len(indptr) - 1, len(indptr) - 1 if len(indptr) > 1 else max(indices) + 1)
        self.nnz = len(data)  # 非零元素个数
    
    @classmethod
    def from_dense(cls, A: np.ndarray, tol: float = 0.0) -> 'CSRMatrix':
        """
        从稠密矩阵创建CSR矩阵
        
        参数:
            A: 稠密矩阵
            tol: 小于tol的元素视为零
        
        返回:
            CSRMatrix对象
        """
        rows, cols = A.shape
        data = []
        indices = []
        indptr = [0]
        
        for i in range(rows):
            for j in range(cols):
                if abs(A[i, j]) > tol:
                    data.append(A[i, j])
                    indices.append(j)
            indptr.append(len(data))
        
        return cls(np.array(data), np.array(indices), np.array(indptr))
    
    def to_dense(self) -> np.ndarray:
        """
        转换为稠密矩阵
        
        返回:
            稠密numpy数组
        """
        rows, cols = self.shape
        A = np.zeros((rows, cols))
        
        for i in range(rows):
            start, end = self.indptr[i], self.indptr[i + 1]
            for idx in range(start, end):
                j = self.indices[idx]
                A[i, j] = self.data[idx]
        
        return A
    
    def matvec(self, x: np.ndarray) -> np.ndarray:
        """
        矩阵-向量乘积: y = A @ x
        
        参数:
            x: 输入向量 (cols,)
        
        返回:
            y: 输出向量 (rows,)
        """
        rows = self.shape[0]
        y = np.zeros(rows)
        
        for i in range(rows):
            start, end = self.indptr[i], self.indptr[i + 1]
            for idx in range(start, end):
                j = self.indices[idx]
                y[i] += self.data[idx] * x[j]
        
        return y
    
    def matvec_transpose(self, x: np.ndarray) -> np.ndarray:
        """
        转置矩阵-向量乘积: y = A.T @ x
        
        参数:
            x: 输入向量
        
        返回:
            y: 输出向量
        """
        rows, cols = self.shape
        y = np.zeros(cols)
        
        for i in range(rows):
            start, end = self.indptr[i], self.indptr[i + 1]
            for idx in range(start, end):
                j = self.indices[idx]
                y[j] += self.data[idx] * x[i]
        
        return y
    
    def __add__(self, other: 'CSRMatrix') -> 'CSRMatrix':
        """
        矩阵加法: C = A + B
        
        参数:
            other: 另一个CSR矩阵
        
        返回:
            C: 和矩阵
        """
        if self.shape != other.shape:
            raise ValueError("矩阵维度不匹配")
        
        rows = self.shape[0]
        data = []
        indices = []
        indptr = [0]
        
        for i in range(rows):
            # 合并第i行
            row_dict = {}
            
            # 从self添加
            start1, end1 = self.indptr[i], self.indptr[i + 1]
            for idx in range(start1, end1):
                j = self.indices[idx]
                row_dict[j] = row_dict.get(j, 0) + self.data[idx]
            
            # 从other添加
            start2, end2 = other.indptr[i], other.indptr[i + 1]
            for idx in range(start2, end2):
                j = other.indices[idx]
                row_dict[j] = row_dict.get(j, 0) + other.data[idx]
            
            # 排序存储
            for j in sorted(row_dict.keys()):
                if abs(row_dict[j]) > 1e-15:
                    indices.append(j)
                    data.append(row_dict[j])
            
            indptr.append(len(data))
        
        return CSRMatrix(np.array(data), np.array(indices), np.array(indptr))
    
    def __mul__(self, scalar: float) -> 'CSRMatrix':
        """
        标量乘法: B = A * scalar
        
        参数:
            scalar: 标量
        
        返回:
            B: 结果矩阵
        """
        new_data = self.data * scalar
        return CSRMatrix(new_data, self.indices.copy(), self.indptr.copy())
    
    def transpose(self) -> 'CSRMatrix':
        """
        转置操作
        
        返回:
            A.T: 转置矩阵
        """
        rows, cols = self.shape
        
        # 构建COO格式的临时表示
        coo_data = []
        coo_rows = []
        coo_cols = []
        
        for i in range(rows):
            start, end = self.indptr[i], self.indptr[i + 1]
            for idx in range(start, end):
                coo_data.append(self.data[idx])
                coo_rows.append(self.indices[idx])  # 原列 -> 新行
                coo_cols.append(i)                  # 原行 -> 新列
        
        # 按(新行, 新列)排序
        sorted_indices = np.argsort(coo_rows * cols + coo_cols)
        new_data = np.array(coo_data)[sorted_indices]
        new_indices = np.array(coo_cols)[sorted_indices]
        
        # 计算新indptr
        new_indptr = [0]
        current_row = 0
        for idx in sorted_indices:
            while coo_rows[idx] > current_row:
                current_row += 1
                new_indptr.append(len(new_data))
        
        while len(new_indptr) <= cols:
            new_indptr.append(len(new_data))
        
        return CSRMatrix(new_data, new_indices, np.array(new_indptr))
    
    def diagonal(self) -> np.ndarray:
        """
        提取对角元素
        
        返回:
            对角元素数组
        """
        rows, cols = self.shape
        diag = np.zeros(min(rows, cols))
        
        for i in range(min(rows, cols)):
            start, end = self.indptr[i], self.indptr[i + 1]
            for idx in range(start, end):
                if self.indices[idx] == i:
                    diag[i] = self.data[idx]
                    break
        
        return diag
    
    def info(self) -> dict:
        """
        返回矩阵信息
        
        返回:
            包含矩阵信息的字典
        """
        dense_size = self.shape[0] * self.shape[1] * 8  # float64
        sparse_size = (len(self.data) * 8 + 
                      len(self.indices) * 4 + 
                      len(self.indptr) * 8)
        
        return {
            'shape': self.shape,
            'nnz': self.nnz,
            'density': self.nnz / (self.shape[0] * self.shape[1]),
            'dense_size_bytes': dense_size,
            'sparse_size_bytes': sparse_size,
            'compression_ratio': dense_size / sparse_size
        }


def create_laplacian_1d(n: int) -> CSRMatrix:
    """
    创建一维拉普拉斯矩阵（有限差分）
    
    矩阵形式:
        [-1  2  -1   0  ...]
        [ 0 -1   2  -1  ...]
        ...
    
    参数:
        n: 矩阵维度
    
    返回:
        L: CSR格式的一维拉普拉斯矩阵
    """
    # 对角线元素: 2
    # 下对角线元素: -1
    # 上对角线元素: -1
    
    diag = np.ones(n) * 2
    off_diag = np.ones(n - 1) * (-1)
    
    # 构建data和indices
    data = np.concatenate([off_diag, diag, off_diag])
    indices = np.concatenate([
        np.arange(1, n),      # 下对角线列索引
        np.arange(0, n),      # 对角线列索引
        np.arange(0, n - 1)   # 上对角线列索引
    ])
    indptr = np.concatenate([
        np.array([0]),
        np.arange(1, n + 1),      # 每行开始的累积索引
        np.array([2 * n - 1])
    ])
    
    return CSRMatrix(data, indices, indptr)


if __name__ == "__main__":
    print("=" * 55)
    print("稀疏矩阵CSR格式测试")
    print("=" * 55)
    
    # 创建测试矩阵
    # [[1, 0, 2],
    #  [0, 3, 0],
    #  [4, 0, 5]]
    
    data = np.array([1, 2, 3, 4, 5])
    indices = np.array([0, 2, 1, 0, 2])
    indptr = np.array([0, 2, 3, 5])
    
    A_csr = CSRMatrix(data, indices, indptr)
    
    print(f"\n矩阵维度: {A_csr.shape}")
    print(f"非零元素: {A_csr.nnz}")
    print(f"稠密表示:\n{A_csr.to_dense()}")
    
    # 矩阵-向量乘积测试
    x = np.array([1, 2, 3])
    y = A_csr.matvec(x)
    y_expected = A_csr.to_dense() @ x
    print(f"\nA @ x = {y}")
    print(f"验证: {y_expected}")
    print(f"正确: {np.allclose(y, y_expected)}")
    
    # 从稠密矩阵创建
    print("\n--- 从稠密矩阵创建 ---")
    B_dense = np.random.randn(100, 100)
    B_dense[np.abs(B_dense) < 0.5] = 0  # 稀疏化
    B_csr = CSRMatrix.from_dense(B_dense, tol=0.5)
    
    info = B_csr.info()
    print(f"维度: {info['shape']}")
    print(f"非零元素: {info['nnz']}")
    print(f"密度: {info['density']:.4f}")
    print(f"压缩比: {info['compression_ratio']:.2f}x")
    
    # 验证运算正确性
    x = np.random.randn(100)
    y_csr = B_csr.matvec(x)
    y_dense = B_dense @ x
    print(f"\n矩阵-向量乘积验证: {np.allclose(y_csr, y_dense)}")
    
    # 一维拉普拉斯矩阵
    print("\n--- 一维拉普拉斯矩阵 (n=5) ---")
    L = create_laplacian_1d(5)
    print("稠密形式:")
    print(L.to_dense())
    
    x = np.array([1, 2, 3, 4, 5])
    y = L.matvec(x)
    # 期望: [1*2 - 2, 2*2 - 1 - 3, 3*2 - 2 - 4, 4*2 - 3 - 5, 5*2 - 4] 
    #     = [0, 0, 0, 0, 0] (在边界为0的情况下)
    print(f"L @ x = {y}")
    
    print("\n测试通过！CSR稀疏矩阵工作正常。")
