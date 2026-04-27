# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / qr_decomposition

本文件实现 qr_decomposition 相关的算法功能。
"""

import math
import copy
from typing import Tuple, List

def qr_decomposition(matrix: List[List[float]]) -> Tuple[List[List[float]], List[List[float]]]:
    """
    QR分解 - 使用改进的Gram-Schmidt正交化
    
    Args:
        matrix: m×n的矩阵
    
    Returns:
        (Q, R) 元组
    """
    m = len(matrix)
    n = len(matrix[0])
    A = copy.deepcopy(matrix)
    
    Q = [[0.0] * n for _ in range(m)]
    R = [[0.0] * n for _ in range(n)]
    
    for j in range(n):
        v = [A[i][j] for i in range(m)]
        
        for i in range(j):
            R[i][j] = sum(Q[k][i] * A[k][j] for k in range(m))
            for k in range(m):
                v[k] -= R[i][j] * Q[k][i]
        
        R[j][j] = math.sqrt(sum(v[k] ** 2 for k in range(m)))
        
        if R[j][j] != 0:
            for k in range(m):
                Q[k][j] = v[k] / R[j][j]
        else:
            for k in range(m):
                Q[k][j] = 0.0
    
    return Q, R

if __name__ == "__main__":
    print("=== QR分解测试 ===")
    
    A = [[12.0, -51.0, 4.0], [6.0, 167.0, -68.0], [-4.0, 24.0, -41.0]]
    
    Q, R = qr_decomposition(A)
    
    print("Q矩阵:")
    for row in Q:
        print(f"  {[round(x, 4) for x in row]}")
    
    print("\nR矩阵:")
    for row in R:
        print(f"  {[round(x, 4) for x in row]}")
    
    print("\n验证 Q^T * Q = I:")
    QtQ = [[sum(Q[k][i] * Q[k][j] for k in range(len(Q))) 
             for j in range(len(Q[0]))] for i in range(len(Q[0]))]
    for row in QtQ:
        print(f"  {[round(x, 4) for x in row]}")
