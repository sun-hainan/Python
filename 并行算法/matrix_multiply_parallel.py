# -*- coding: utf-8 -*-

"""

算法实现：并行算法 / matrix_multiply_parallel



本文件实现 matrix_multiply_parallel 相关的算法功能。

"""



import random

from concurrent.futures import ThreadPoolExecutor





def matrix_multiply_parallel(matrix_a, matrix_b, num_workers=None):

    """

    并行矩阵乘法：计算 C = A × B

    

    参数:

        matrix_a: 矩阵 A (m × k)

        matrix_b: 矩阵 B (k × n)

        num_workers: 并行工作线程数

    

    返回:

        result_matrix: 矩阵 C (m × n)

    

    注意：

        - matrix_a 的列数必须等于 matrix_b 的行数

        - 返回新矩阵，不修改输入矩阵

    """

    # 验证矩阵维度兼容性

    rows_a = len(matrix_a)

    cols_a = len(matrix_a[0]) if rows_a > 0 else 0

    rows_b = len(matrix_b)

    cols_b = len(matrix_b[0]) if rows_b > 0 else 0

    

    if cols_a != rows_b:

        raise ValueError(

            f"矩阵维度不兼容: A ({rows_a}×{cols_a}) 与 B ({rows_b}×{cols_b}) "

            f"无法相乘（要求 A 的列数 = B 的行数）"

        )

    

    if cols_a == 0 or rows_b == 0:

        return []  # 空矩阵

    

    k_dim = cols_a  # 中间维度

    m_dim = rows_a  # A 的行数

    n_dim = cols_b  # B 的列数

    

    # 初始化结果矩阵（m × n），全部为 0

    result_matrix = [[0.0 for _ in range(n_dim)] for _ in range(m_dim)]

    

    # 计算每一行函数（用于并行化）

    def compute_row(row_idx):

        """计算结果矩阵的第 row_idx 行"""

        row_result = [0.0] * n_dim

        for j in range(n_dim):

            # 计算 C[row_idx][j] = Σ(A[row_idx][k] * B[k][j])

            accum = 0.0

            for k in range(k_dim):

                accum += matrix_a[row_idx][k] * matrix_b[k][j]

            row_result[j] = accum

        return row_idx, row_result

    

    # 使用线程池并行计算各行

    with ThreadPoolExecutor(max_workers=num_workers) as executor:

        futures = [executor.submit(compute_row, i) for i in range(m_dim)]

        

        for future in futures:

            row_idx, row_result = future.result()

            result_matrix[row_idx] = row_result

    

    return result_matrix





def matrix_multiply_naive(matrix_a, matrix_b):

    """

    朴素矩阵乘法（三重循环）用于对比验证

    

    参数:

        matrix_a: 矩阵 A (m × k)

        matrix_b: 矩阵 B (k × n)

    

    返回:

        result_matrix: 矩阵 C (m × n)

    """

    rows_a = len(matrix_a)

    cols_a = len(matrix_a[0]) if rows_a > 0 else 0

    rows_b = len(matrix_b)

    cols_b = len(matrix_b[0]) if rows_b > 0 else 0

    

    if cols_a != rows_b:

        raise ValueError("矩阵维度不兼容")

    

    m_dim = rows_a

    k_dim = cols_a

    n_dim = cols_b

    

    result = [[0.0 for _ in range(n_dim)] for _ in range(m_dim)]

    

    for i in range(m_dim):

        for j in range(n_dim):

            for k in range(k_dim):

                result[i][j] += matrix_a[i][k] * matrix_b[k][j]

    

    return result





def generate_random_matrix(rows, cols, value_range=10):

    """

    生成随机矩阵用于测试

    

    参数:

        rows: 行数

        cols: 列数

        value_range: 元素值范围 [0, value_range)

    

    返回:

        matrix: 随机矩阵

    """

    return [

        [random.uniform(0, value_range) for _ in range(cols)]

        for _ in range(rows)

    ]





# ==================== 测试代码 ====================



if __name__ == "__main__":

    import time

    

    print("=" * 60)

    print("并行矩阵乘法 测试")

    print("=" * 60)

    

    # 测试用例1：2×3 与 3×2 矩阵乘法

    matrix_a = [

        [1, 2, 3],

        [4, 5, 6]

    ]

    matrix_b = [

        [7, 8],

        [9, 10],

        [11, 12]

    ]

    print(f"\n[测试1] 矩阵 A (2×3):\n{matrix_a}")

    print(f"矩阵 B (3×2):\n{matrix_b}")

    

    result = matrix_multiply_parallel(matrix_a, matrix_b)

    expected = matrix_multiply_naive(matrix_a, matrix_b)

    

    print(f"结果 C (2×2):\n{result}")

    assert result == expected, "矩阵乘法结果错误！"

    print("✅ 通过\n")

    

    # 测试用例2：方阵乘法

    matrix_a = [

        [1, 2],

        [3, 4]

    ]

    matrix_b = [

        [5, 6],

        [7, 8]

    ]

    print(f"[测试2] 方阵乘法 A (2×2) × B (2×2)")

    result = matrix_multiply_parallel(matrix_a, matrix_b)

    expected = matrix_multiply_naive(matrix_a, matrix_b)

    print(f"结果:\n{result}")

    assert result == expected, "矩阵乘法结果错误！"

    print("✅ 通过\n")

    

    # 测试用例3：更大矩阵

    print(f"[测试3] 较大矩阵性能测试")

    sizes = [(50, 50, 50), (100, 100, 100), (150, 150, 150)]

    

    for m, k, n in sizes:

        matrix_a = generate_random_matrix(m, k)

        matrix_b = generate_random_matrix(k, n)

        

        start = time.time()

        result_parallel = matrix_multiply_parallel(matrix_a, matrix_b)

        time_parallel = time.time() - start

        

        start = time.time()

        result_naive = matrix_multiply_naive(matrix_a, matrix_b)

        time_naive = time.time() - start

        

        is_correct = result_parallel == result_naive

        print(f"  {m}×{k} × {k}×{n}: 并行={time_parallel:.4f}s, 朴素={time_naive:.4f}s, 正确性: {'✅' if is_correct else '❌'}")

    print()

    

    # 测试用例4：边界情况

    print("[测试4] 边界情况")

    # 空矩阵

    assert matrix_multiply_parallel([], [[1, 2]]) == [], "空矩阵A测试失败"

    # 单元素矩阵

    assert matrix_multiply_parallel([[5]], [[3]]) == [[15]], "单元素矩阵测试失败"

    print("✅ 通过")

    

    # 测试用例5：错误处理

    print("\n[测试5] 错误检测")

    try:

        matrix_multiply_parallel([[1, 2]], [[3]])  # 维度不兼容

        print("❌ 应该抛出异常")

    except ValueError as e:

        print(f"✅ 正确捕获错误: {e}")

    

    print("\n" + "=" * 60)

    print("所有测试通过！并行矩阵乘法验证完成。")

    print("=" * 60)

