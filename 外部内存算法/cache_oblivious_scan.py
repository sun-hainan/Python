# -*- coding: utf-8 -*-

"""

算法实现：外部内存算法 / cache_oblivious_scan



本文件实现 cache_oblivious_scan 相关的算法功能。

"""



import math





def co_scan_iterative(data, block_size):

    """

    缓存无关的迭代扫描。



    每次顺序访问一个元素，但以 block_size 为单位传输。



    参数:

        data: 数据数组

        block_size: 块大小 B



    返回:

        处理后的结果（这里是简单的累加和）

    """

    n = len(data)

    result = 0



    for i in range(n):

        result += data[i]



    return result





def co_scan_recursive(data, block_size):

    """

    缓存无关的递归扫描。



    分治策略：将数据分成两半，递归处理，然后合并。



    参数:

        data: 数据数组

        block_size: 块大小



    返回:

        扫描结果

    """

    n = len(data)

    if n <= block_size:

        # 缓存内扫描

        return sum(data)



    mid = n // 2

    left_result = co_scan_recursive(data[:mid], block_size)

    right_result = co_scan_recursive(data[mid:], block_size)



    return left_result + right_result





def co_matrix_multiply(A, B, block_size):

    """

    缓存无关的矩阵乘法（分块递归）。



    核心思想：将矩阵递归分块，使得每个子矩阵运算都能在缓存内完成。



    参数:

        A, B: 输入矩阵

        block_size: 块大小



    返回:

        C = A * B

    """

    n = len(A)



    if n <= block_size:

        # 小矩阵直接相乘

        return _naive_matrix_multiply(A, B)



    # 分成 4 块

    mid = n // 2

    A11, A12, A21, A22 = _split_matrix(A, mid)

    B11, B12, B21, B22 = _split_matrix(B, mid)



    # 递归计算 8 个子乘积

    C11 = _matrix_add(co_matrix_multiply(A11, B11, block_size),

                      co_matrix_multiply(A12, B21, block_size), block_size)

    C12 = _matrix_add(co_matrix_multiply(A11, B12, block_size),

                      co_matrix_multiply(A12, B22, block_size), block_size)

    C21 = _matrix_add(co_matrix_multiply(A21, B11, block_size),

                      co_matrix_multiply(A22, B21, block_size), block_size)

    C22 = _matrix_add(co_matrix_multiply(A21, B12, block_size),

                      co_matrix_multiply(A22, B22, block_size), block_size)



    return _merge_matrix(C11, C12, C21, C22)





def _split_matrix(M, mid):

    """将矩阵分成 4 块。"""

    n = len(M)

    M11 = [row[:mid] for row in M[:mid]]

    M12 = [row[mid:] for row in M[:mid]]

    M21 = [row[:mid] for row in M[mid:]]

    M22 = [row[mid:] for row in M[mid:]]

    return M11, M12, M21, M22





def _merge_matrix(C11, C12, C21, C22):

    """合并 4 块为一个矩阵。"""

    top = [C11[i] + C12[i] for i in range(len(C11))]

    bottom = [C21[i] + C22[i] for i in range(len(C21))]

    return top + bottom





def _naive_matrix_multiply(A, B):

    """朴素矩阵乘法。"""

    n = len(A)

    C = [[0] * n for _ in range(n)]

    for i in range(n):

        for j in range(n):

            for k in range(n):

                C[i][j] += A[i][k] * B[k][j]

    return C





def _matrix_add(A, B, block_size):

    """矩阵加法。"""

    n = len(A)

    C = [[A[i][j] + B[i][j] for j in range(n)] for i in range(n)]

    return C





def co_optimal_scan_analysis(n, b):

    """

    分析缓存无关扫描的最优 I/O 复杂度。



    定理：对于 n 个元素，块大小 b，最优扫描复杂度为 Θ(n/b)

    """

    return (n + b - 1) // b





def co_optimal_matmul_analysis(n, b):

    """

    分析缓存无关矩阵乘法的最优 I/O 复杂度。



    定理：对于 n×n 矩阵，缓存大小 M，最优复杂度为

    Θ(n^3 / sqrt(M)) 或当 M >= n^2 时为 Θ(n^2/b)

    """

    m = int(math.sqrt(n * b))  # 缓存大小估计

    if m >= n * n:

        return (n * n + b - 1) // b

    return (n ** 3) // int(math.sqrt(m))





if __name__ == "__main__":

    print("=== 缓存无关算法测试 ===")



    # 扫描测试

    n = 1024

    block_size = 64

    import random

    random.seed(42)

    test_data = [random.randint(0, 100) for _ in range(n)]



    print(f"数据大小 N={n}, 块大小 B={block_size}")

    print(f"扫描 I/O 下界: {co_optimal_scan_analysis(n, block_size)}")



    iter_result = co_scan_iterative(test_data, block_size)

    recur_result = co_scan_recursive(test_data, block_size)

    naive_result = sum(test_data)

    print(f"迭代扫描结果: {iter_result}")

    print(f"递归扫描结果: {recur_result}")

    print(f"朴素求和结果: {naive_result}")



    # 矩阵乘法测试

    print("\n=== 矩阵乘法测试 ===")

    size = 4

    A = [[1, 2, 3, 4],

         [5, 6, 7, 8],

         [9, 10, 11, 12],

         [13, 14, 15, 16]]

    B = [[1, 0, 0, 0],

         [0, 1, 0, 0],

         [0, 0, 1, 0],

         [0, 0, 0, 1]]



    C = co_matrix_multiply(A, B, block_size=2)

    print("矩阵 A:")

    for row in A:

        print(f"  {row}")

    print("矩阵 B（单位矩阵）:")

    print("与 A 相同")

    print("乘积 C = A * I:")

    for row in C:

        print(f"  {[x for x in row]}")



    # 验证

    C_expected = _naive_matrix_multiply(A, B)

    print(f"\n乘积正确: {C == C_expected}")



    # I/O 分析

    print("\n=== I/O 复杂度分析 ===")

    for n in [256, 1024, 4096]:

        b = 64

        scan_io = co_optimal_scan_analysis(n, b)

        matmul_io = co_optimal_matmul_analysis(n, b)

        print(f"N={n:,}: 扫描 I/O ≈ {scan_io:,}, 矩阵乘法 I/O ≈ {matmul_io:,}")



    print("\n缓存无关算法特性:")

    print("  无需知道缓存参数 M 和 B")

    print("  在所有缓存级别都接近最优")

    print("  递归分治实现自动适应缓存层次")

