# -*- coding: utf-8 -*-

"""

算法实现：缓存无关算法 / cache_oblivious_matrix_multiply



本文件实现 cache_oblivious_matrix_multiply 相关的算法功能。

"""



from typing import List, Tuple

import random





def matrix_multiply_cache_oblivious(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:

    """

    缓存无关矩阵乘法

    使用分治法,将矩阵分成4块递归相乘

    

    Args:

        A: n×n矩阵

        B: n×n矩阵

    

    Returns:

        C = A × B

    """

    n = len(A)

    if n == 1:

        return [[A[0][0] * B[0][0]]]

    

    mid = n // 2

    

    # 分割矩阵

    A11, A12, A21, A22 = split_matrix(A, mid)

    B11, B12, B21, B22 = split_matrix(B, mid)

    

    # 递归计算8个乘积

    # 优化:使用Strassen-like优化减少递归次数

    M1 = matrix_multiply_cache_oblivious(add_matrices(A11, A22), add_matrices(B11, B22))

    M2 = matrix_multiply_cache_oblivious(add_matrices(A21, A22), B11)

    M3 = matrix_multiply_cache_oblivious(A11, subtract_matrices(B12, B22))

    M4 = matrix_multiply_cache_oblivious(A22, subtract_matrices(B21, B11))

    M5 = matrix_multiply_cache_oblivious(add_matrices(A11, A12), B22)

    M6 = matrix_multiply_cache_oblivious(subtract_matrices(A21, A11), add_matrices(B11, B12))

    M7 = matrix_multiply_cache_oblivious(subtract_matrices(A12, A22), add_matrices(B21, B22))

    

    # 组合结果

    C11 = add_matrices(subtract_matrices(add_matrices(M1, M4), M5), M7)

    C12 = add_matrices(M3, M5)

    C21 = add_matrices(M2, M4)

    C22 = add_matrices(subtract_matrices(add_matrices(M1, M3), M2), M6)

    

    return merge_matrices(C11, C12, C21, C22)





def split_matrix(M: List[List[float]], mid: int) -> Tuple:

    """将矩阵分成4块"""

    n = len(M)

    A11 = [[M[i][j] for j in range(mid)] for i in range(mid)]

    A12 = [[M[i][j] for j in range(mid, n)] for i in range(mid)]

    A21 = [[M[i][j] for j in range(mid)] for i in range(mid, n)]

    A22 = [[M[i][j] for j in range(mid, n)] for i in range(mid, n)]

    return A11, A12, A21, A22





def merge_matrices(C11, C12, C21, C22) -> List[List[float]]:

    """合并4块矩阵"""

    top = [C11[i] + C12[i] for i in range(len(C11))]

    bottom = [C21[i] + C22[i] for i in range(len(C21))]

    return [top[i] + bottom[i] for i in range(len(top))]





def add_matrices(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:

    """矩阵加法"""

    n = len(A)

    return [[A[i][j] + B[i][j] for j in range(n)] for i in range(n)]





def subtract_matrices(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:

    """矩阵减法"""

    n = len(A)

    return [[A[i][j] - B[i][j] for j in range(n)] for i in range(n)]





def naive_matrix_multiply(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:

    """

    朴素矩阵乘法:O(n³)

    

    Args:

        A: n×n矩阵

        B: n×n矩阵

    

    Returns:

        C = A × B

    """

    n = len(A)

    C = [[0.0] * n for _ in range(n)]

    

    for i in range(n):

        for k in range(n):

            aik = A[i][k]

            if aik != 0:  # 优化:跳过零

                for j in range(n):

                    C[i][j] += aik * B[k][j]

    

    return C





def blocked_matrix_multiply(A: List[List[float]], B: List[List[float]], block_size: int = 64) -> List[List[float]]:

    """

    阻塞矩阵乘法(缓存感知):O(n³/√B)

    

    Args:

        A: n×n矩阵

        B: n×n矩阵

        block_size: 阻塞大小

    

    Returns:

        C = A × B

    """

    n = len(A)

    C = [[0.0] * n for _ in range(n)]

    

    for i0 in range(0, n, block_size):

        for j0 in range(0, n, block_size):

            for k0 in range(0, n, block_size):

                # 块边界

                i1 = min(i0 + block_size, n)

                j1 = min(j0 + block_size, n)

                k1 = min(k0 + block_size, n)

                

                # 块乘法

                for i in range(i0, i1):

                    for k in range(k0, k1):

                        aik = A[i][k]

                        if aik != 0:

                            for j in range(j0, j1):

                                C[i][j] += aik * B[k][j]

    

    return C





def verify_multiplication(A: List[List[float]], B: List[List[float]], C: List[List[float]]) -> bool:

    """验证矩阵乘法结果"""

    n = len(A)

    for i in range(n):

        for j in range(n):

            expected = sum(A[i][k] * B[k][j] for k in range(n))

            if abs(C[i][j] - expected) > 1e-9:

                return False

    return True





# 测试代码

if __name__ == "__main__":

    import time

    

    # 测试1: 小矩阵

    print("测试1 - 小矩阵(8×8):")

    A1 = [[1, 2, 3, 4, 5, 6, 7, 8],

          [2, 3, 4, 5, 6, 7, 8, 9],

          [3, 4, 5, 6, 7, 8, 9, 10],

          [4, 5, 6, 7, 8, 9, 10, 11],

          [5, 6, 7, 8, 9, 10, 11, 12],

          [6, 7, 8, 9, 10, 11, 12, 13],

          [7, 8, 9, 10, 11, 12, 13, 14],

          [8, 9, 10, 11, 12, 13, 14, 15]]

    

    B1 = [[1, 0, 0, 0, 0, 0, 0, 0],

          [0, 2, 0, 0, 0, 0, 0, 0],

          [0, 0, 3, 0, 0, 0, 0, 0],

          [0, 0, 0, 4, 0, 0, 0, 0],

          [0, 0, 0, 0, 5, 0, 0, 0],

          [0, 0, 0, 0, 0, 6, 0, 0],

          [0, 0, 0, 0, 0, 0, 7, 0],

          [0, 0, 0, 0, 0, 0, 0, 8]]

    

    C_co = matrix_multiply_cache_oblivious(A1, B1)

    C_naive = naive_matrix_multiply(A1, B1)

    

    print(f"  Cache-Oblivious正确: {verify_multiplication(A1, B1, C_co)}")

    print(f"  朴素正确: {verify_multiplication(A1, B1, C_naive)}")

    

    # 测试2: 不同大小矩阵性能

    print("\n测试2 - 性能对比:")

    sizes = [32, 64, 128, 256]

    

    for size in sizes:

        # 随机生成矩阵

        random.seed(42)

        A = [[random.random() for _ in range(size)] for _ in range(size)]

        B = [[random.random() for _ in range(size)] for _ in range(size)]

        

        # 缓存无关

        start = time.time()

        C_co = matrix_multiply_cache_oblivious(A, B)

        time_co = time.time() - start

        

        # 朴素

        start = time.time()

        C_naive = naive_matrix_multiply(A, B)

        time_naive = time.time() - start

        

        # 阻塞

        start = time.time()

        C_blocked = blocked_matrix_multiply(A, B, block_size=32)

        time_blocked = time.time() - start

        

        print(f"  n={size}:")

        print(f"    Cache-Oblivious: {time_co:.4f}s")

        print(f"    朴素: {time_naive:.4f}s")

        print(f"    阻塞: {time_blocked:.4f}s")

    

    # 测试3: 验证正确性

    print("\n测试3 - 正确性验证:")

    for n in [2, 4, 8, 16]:

        A = [[random.random() for _ in range(n)] for _ in range(n)]

        B = [[random.random() for _ in range(n)] for _ in range(n)]

        

        C_co = matrix_multiply_cache_oblivious(A, B)

        C_naive = naive_matrix_multiply(A, B)

        

        diff = max(abs(C_co[i][j] - C_naive[i][j]) 

                  for i in range(n) for j in range(n))

        print(f"  n={n}: 最大差异={diff:.2e}")

    

    # 测试4: 特殊情况(稀疏矩阵)

    print("\n测试4 - 稀疏矩阵(单位矩阵):")

    n = 16

    I = [[1 if i == j else 0 for j in range(n)] for i in range(n)]

    

    random.seed(42)

    R = [[random.random() for _ in range(n)] for _ in range(n)]

    

    C = matrix_multiply_cache_oblivious(I, R)

    print(f"  I × R = R: {verify_multiplication(I, R, C)}")

    

    C = matrix_multiply_cache_oblivious(R, I)

    print(f"  R × I = R: {verify_multiplication(R, I, C)}")

    

    print("\n所有测试完成!")

