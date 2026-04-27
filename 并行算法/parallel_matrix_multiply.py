# -*- coding: utf-8 -*-
"""
算法实现：并行算法 / parallel_matrix_multiply

本文件实现 parallel_matrix_multiply 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple
import math


def sequential_matrix_multiply(matrix_a: List[List[float]], 
                              matrix_b: List[List[float]]) -> List[List[float]]:
    """
    顺序矩阵乘法（用于对比）
    
    参数:
        matrix_a: n×m矩阵
        matrix_b: m×p矩阵
    
    返回:
        n×p结果矩阵
    """
    n = len(matrix_a)
    m = len(matrix_a[0])
    p = len(matrix_b[0])
    
    # 确保维度匹配
    assert len(matrix_b) == m, "Matrix dimensions mismatch"
    
    result = [[0.0] * p for _ in range(n)]
    
    for i in range(n):
        for j in range(p):
            for k in range(m):
                result[i][j] += matrix_a[i][k] * matrix_b[k][j]
    
    return result


def fox_matrix_multiply(matrix_a: List[List[float]], 
                       matrix_b: List[List[float]], 
                       num_processors: int = 4) -> List[List[float]]:
    """
    Fox并行矩阵乘法算法
    
    算法步骤：
    1. 将矩阵划分为sqrt(p)×sqrt(p)块
    2. 对角线处理器广播自己的块
    3. 每个处理器与对应块相乘
    4. 循环移位
    
    参数:
        matrix_a: 矩阵A (n×n)
        matrix_b: 矩阵B (n×n)
        num_processors: 处理器数量（应为完全平方数）
    
    返回:
        结果矩阵
    """
    n = len(matrix_a)
    
    # 计算网格大小
    q = int(math.sqrt(num_processors))
    if q * q != num_processors:
        # 如果不是完全平方数，调整为最大平方数
        q = int(math.sqrt(num_processors // 2) + 0.5)
        while q * q > num_processors:
            q -= 1
    
    block_size = n // q
    
    # 确保矩阵可以整除
    if n % q != 0:
        # 填充到可以整除
        new_n = ((n // q) + 1) * q
        matrix_a = pad_matrix(matrix_a, new_n)
        matrix_b = pad_matrix(matrix_b, new_n)
        n = new_n
    
    # 初始化结果矩阵
    result = [[0.0] * n for _ in range(n)]
    
    # Fox算法主循环
    for k in range(q):
        # 对角线广播
        # 处理器(i, (i+k) mod q)广播自己的A块
        for i in range(q):
            source_row = i
            source_col = (i + k) % q
            block_row_start = source_row * block_size
            block_col_start = source_col * block_size
            
            # 获取A的当前块
            a_block = get_block(matrix_a, block_row_start, block_col_start, block_size)
            
            # 广播到同一行
            for j in range(q):
                # 获取B的当前块
                b_block_row = source_row * block_size
                b_block_col = j * block_size
                b_block = get_block(matrix_b, b_block_row, b_block_col, block_size)
                
                # 计算贡献
                contribution = block_multiply(a_block, b_block)
                
                # 累加到结果
                result_block_row = source_row * block_size
                result_block_col = j * block_size
                add_to_block(result, contribution, result_block_row, result_block_col)
    
    return result


def cannon_matrix_multiply(matrix_a: List[List[float]], 
                          matrix_b: List[List[float]], 
                          num_processors: int = 4) -> List[List[float]]:
    """
    Cannon并行矩阵乘法算法
    
    算法步骤：
    1. 将矩阵划分为块
    2. 初始偏移（A向左，B向上）
    3. 循环：乘累加，循环移位
    
    参数:
        matrix_a: 矩阵A
        matrix_b: 矩阵B
        num_processors: 处理器数量
    
    返回:
        结果矩阵
    """
    n = len(matrix_a)
    
    # 计算网格大小
    q = int(math.sqrt(num_processors))
    if q * q != num_processors:
        q = int(math.sqrt(num_processors // 2) + 0.5)
        while q * q > num_processors:
            q -= 1
    
    block_size = n // q
    
    # 确保矩阵可以整除
    if n % q != 0:
        new_n = ((n // q) + 1) * q
        matrix_a = pad_matrix(matrix_a, new_n)
        matrix_b = pad_matrix(matrix_b, new_n)
        n = new_n
    
    result = [[0.0] * n for _ in range(n)]
    
    # 初始偏移：A向左，B向上
    for i in range(q):
        for j in range(q):
            # 计算初始位置偏移
            offset = i
            # 这里简化处理，实际需要循环移位数据结构
    
    # 主循环
    for step in range(q):
        for i in range(q):
            for j in range(q):
                # 计算A和B的当前块位置
                a_row = i
                a_col = (j + step) % q
                b_row = (i + step) % q
                b_col = j
                
                a_block_row = a_row * block_size
                a_block_col = a_col * block_size
                b_block_row = b_row * block_size
                b_block_col = b_col * block_size
                
                a_block = get_block(matrix_a, a_block_row, a_block_col, block_size)
                b_block = get_block(matrix_b, b_block_row, b_block_col, block_size)
                
                contribution = block_multiply(a_block, b_block)
                
                result_block_row = i * block_size
                result_block_col = j * block_size
                add_to_block(result, contribution, result_block_row, result_block_col)
    
    return result


def pad_matrix(matrix: List[List[float]], new_size: int) -> List[List[float]]:
    """
    将矩阵填充到新大小
    
    参数:
        matrix: 原始矩阵
        new_size: 新的行列大小
    
    返回:
        填充后的矩阵
    """
    n = len(matrix)
    result = [[0.0] * new_size for _ in range(new_size)]
    
    for i in range(n):
        for j in range(n):
            result[i][j] = matrix[i][j]
    
    return result


def get_block(matrix: List[List[float]], row: int, col: int, 
              size: int) -> List[List[float]]:
    """
    获取矩阵的子块
    
    参数:
        matrix: 矩阵
        row: 起始行
        col: 起始列
        size: 块大小
    
    返回:
        子块矩阵
    """
    block = []
    for i in range(row, min(row + size, len(matrix))):
        block_row = []
        for j in range(col, min(col + size, len(matrix[0]))):
            block_row.append(matrix[i][j])
        # 填充到size
        while len(block_row) < size:
            block_row.append(0.0)
        block.append(block_row)
    
    while len(block) < size:
        block.append([0.0] * size)
    
    return block


def block_multiply(block_a: List[List[float]], 
                   block_b: List[List[float]]) -> List[List[float]]:
    """
    块矩阵乘法
    
    参数:
        block_a: m×k块
        block_b: k×n块
    
    返回:
        m×n块
    """
    m = len(block_a)
    k = len(block_a[0]) if block_a else 0
    n = len(block_b[0]) if block_b else 0
    
    result = [[0.0] * n for _ in range(m)]
    
    for i in range(m):
        for j in range(n):
            for p in range(k):
                result[i][j] += block_a[i][p] * block_b[p][j]
    
    return result


def add_to_block(matrix: List[List[float]], block: List[List[float]],
                row: int, col: int):
    """
    将块累加到矩阵的指定位置
    
    参数:
        matrix: 目标矩阵
        block: 要累加的块
        row: 起始行
        col: 起始列
    """
    m = len(block)
    n = len(block[0])
    
    for i in range(m):
        for j in range(n):
            if row + i < len(matrix) and col + j < len(matrix[0]):
                matrix[row + i][col + j] += block[i][j]


def matrix_multiply_simulate(matrix_a: List[List[float]],
                            matrix_b: List[List[float]],
                            num_processors: int,
                            algorithm: str = "fox") -> dict:
    """
    模拟并行矩阵乘法（不真正并行，但返回执行信息）
    
    参数:
        matrix_a: 矩阵A
        matrix_b: 矩阵B
        num_processors: 处理器数量
        algorithm: 算法名称 ("fox" 或 "cannon")
    
    返回:
        包含结果和统计信息的字典
    """
    import time
    
    start = time.time()
    
    if algorithm == "fox":
        result = fox_matrix_multiply(matrix_a, matrix_b, num_processors)
    else:
        result = cannon_matrix_multiply(matrix_a, matrix_b, num_processors)
    
    elapsed = time.time() - start
    
    n = len(result)
    
    return {
        'result': result,
        'dimensions': (n, n),
        'num_processors': num_processors,
        'algorithm': algorithm,
        'computation_time': elapsed
    }


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本矩阵乘法
    print("=" * 50)
    print("测试1: 基本矩阵乘法")
    print("=" * 50)
    
    matrix_a = [[1, 2], [3, 4]]
    matrix_b = [[5, 6], [7, 8]]
    
    result = sequential_matrix_multiply(matrix_a, matrix_b)
    print("A =", matrix_a)
    print("B =", matrix_b)
    print("A×B =", result)
    
    # 验证
    expected = [[1*5+2*7, 1*6+2*8], [3*5+4*7, 3*6+4*8]]
    print("预期 =", expected)
    print("正确 =", result == expected)
    
    # 测试用例2：Fox算法
    print("\n" + "=" * 50)
    print("测试2: Fox并行算法")
    print("=" * 50)
    
    n = 4
    matrix_a = [[i * n + j for j in range(n)] for i in range(n)]
    matrix_b = [[1] * n for _ in range(n)]
    
    print("矩阵A:")
    for row in matrix_a:
        print(f"  {row}")
    
    sim_result = matrix_multiply_simulate(matrix_a, matrix_b, 4, "fox")
    result = sim_result['result']
    
    print("\nFox算法结果:")
    for row in result:
        print(f"  {row}")
    
    # 测试用例3：不同规模
    print("\n" + "=" * 50)
    print("测试3: 不同规模矩阵")
    print("=" * 50)
    
    for n in [2, 4, 8, 16]:
        matrix_a = [[i + j for j in range(n)] for i in range(n)]
        matrix_b = [[1.0] * n for _ in range(n)]
        
        sim_result = matrix_multiply_simulate(matrix_a, matrix_b, 4, "fox")
        print(f"n={n:2d}: 计算时间={sim_result['computation_time']*1000:.2f}ms")
    
    # 测试用例4：块矩阵操作
    print("\n" + "=" * 50)
    print("测试4: 块矩阵操作")
    print("=" * 50)
    
    matrix = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]
    
    block = get_block(matrix, 1, 1, 2)
    print("从(1,1)获取的2×2块:")
    for row in block:
        print(f"  {row}")
    
    # 测试用例5：算法对比
    print("\n" + "=" * 50)
    print("测试5: Fox vs Cannon算法")
    print("=" * 50)
    
    n = 4
    matrix_a = [[i * n + j + 1 for j in range(n)] for i in range(n)]
    matrix_b = [[j * n + i + 1 for j in range(n)] for i in range(n)]
    
    fox_result = matrix_multiply_simulate(matrix_a, matrix_b, 4, "fox")
    cannon_result = matrix_multiply_simulate(matrix_a, matrix_b, 4, "cannon")
    
    print(f"Fox算法时间: {fox_result['computation_time']*1000:.2f}ms")
    print(f"Cannon算法时间: {cannon_result['computation_time']*1000:.2f}ms")
    
    # 验证结果一致性
    print(f"结果一致: {fox_result['result'] == cannon_result['result']}")
