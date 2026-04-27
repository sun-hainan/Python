# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / ldl_decomposition

本文件实现 ldl_decomposition 相关的算法功能。
"""

from typing import Tuple, List

def ldl_decomposition(matrix: List[List[float]]) -> Tuple[List[List[float]], List[List[float]]]:
    """
    矩阵LDL分解 - 对称矩阵的分解
    
    将对称正定矩阵A分解为A = L * D * L^T
    
    Args:
        matrix: n×n的对称矩阵
    
    Returns:
        (L, D) 元组，其中L是单位下三角矩阵，D是对角矩阵
    """
    n = len(matrix)
    L = [[0.0] * n for _ in range(n)]
    D = [[0.0] * n for _ in range(n)]
    
    for i in range(n):
        D[i][i] = matrix[i][i]
        
        for j in range(i):
            D[i][i] -= L[i][j] ** 2 * D[j][j]
        
        for j in range(i):
            L[i][j] = matrix[i][j]
            for k in range(j):
                L[i][j] -= L[i][k] * L[j][k] * D[k][k]
            L[i][j] /= D[j][j] if D[j][j] != 0 else 1.0
        
        L[i][i] = 1.0
    
    return L, D

if __name__ == "__main__":
    print("=== LDL分解测试 ===")
    
    A = [[4.0, 12.0, -16.0], [12.0, 37.0, -43.0], [-16.0, -43.0, 98.0]]
    
    L, D = ldl_decomposition(A)
    
    print("L矩阵 (单位下三角):")
    for row in L:
        print(f"  {[round(x, 4) for x in row]}")
    
    print("\nD矩阵 (对角):")
    for row in D:
        print(f"  {[round(x, 4) for x in row]}")
    
    print("\n=== 2x2矩阵测试 ===")
    A2 = [[4.0, 2.0], [2.0, 5.0]]
    L2, D2 = ldl_decomposition(A2)
    print("L矩阵:")
    for row in L2:
        print(f"  {[round(x, 4) for x in row]}")
    print("D矩阵:")
    for row in D2:
        print(f"  {[round(x, 4) for x in row]}")
