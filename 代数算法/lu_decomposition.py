# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / lu_decomposition

本文件实现 lu_decomposition 相关的算法功能。
"""

from typing import Tuple, List

def lu_decomposition(matrix: List[List[float]]) -> Tuple[List[List[float]], List[List[float]]]:
    """
    矩阵LU分解
    
    将方阵A分解为A = L * U，其中L是下三角矩阵，U是上三角矩阵
    
    Args:
        matrix: n×n的方阵
    
    Returns:
        (L, U) 元组
    """
    n = len(matrix)
    L = [[0.0] * n for _ in range(n)]
    U = [[0.0] * n for _ in range(n)]
    
    for i in range(n):
        for k in range(i, n):
            sum_val = sum(L[i][j] * U[j][k] for j in range(i))
            U[i][k] = matrix[i][k] - sum_val
        
        for k in range(i, n):
            if i == k:
                L[i][i] = 1.0
            else:
                sum_val = sum(L[k][j] * U[j][i] for j in range(i))
                L[k][i] = (matrix[k][i] - sum_val) / U[i][i]
    
    return L, U

def lu_solve(L, U, b):
    """使用LU分解求解线性方程组 Ax = b"""
    n = len(b)
    y = [0.0] * n
    for i in range(n):
        y[i] = b[i] - sum(L[i][j] * y[j] for j in range(i))
    
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - sum(U[i][j] * x[j] for j in range(i + 1, n))) / U[i][i]
    
    return x

if __name__ == "__main__":
    print("=== LU分解测试 ===")
    
    A = [[4.0, 3.0], [6.0, 3.0]]
    L, U = lu_decomposition(A)
    
    print("L矩阵:")
    for row in L:
        print(f"  {[round(x, 3) for x in row]}")
    
    print("U矩阵:")
    for row in U:
        print(f"  {[round(x, 3) for x in row]}")
    
    b = [10.0, 12.0]
    x = lu_solve(L, U, b)
    print(f"求解 Ax = b, b = {b}")
    print(f"解: x = {[round(v, 3) for v in x]}")
    
    print("\n=== 3x3矩阵测试 ===")
    A3 = [[2.0, 1.0, 1.0], [4.0, 3.0, 3.0], [8.0, 7.0, 9.0]]
    L3, U3 = lu_decomposition(A3)
    det = 1.0
    for i in range(len(U3)):
        det *= U3[i][i]
    print(f"3x3矩阵LU分解, 行列式 = {round(det, 4)}")
