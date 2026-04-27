# -*- coding: utf-8 -*-
"""
算法实现：缓存无关算法 / co_matrix_multiply

本文件实现 co_matrix_multiply 相关的算法功能。
"""

import math
import random
from typing import List, Tuple, Optional


# 算法配置常量
# =============================================================================
# CACHE_SIZE: 模拟的缓存大小用于性能分析
CACHE_SIZE = 1024

# CACHE_LINE_SIZE: 缓存行大小字节数
CACHE_LINE_SIZE = 64

# ELEMENTS_PER_CACHE_LINE: 每个缓存行可容纳的元素个数
ELEMENTS_PER_CACHE_LINE = CACHE_LINE_SIZE // 8  # 假设double占8字节

# MATRIX_BLOCK_SIZE: 基本矩阵块大小
MATRIX_BLOCK_SIZE = 32


def create_matrix(rows: int, cols: int, fill: float = 0.0) -> List[List[float]]:
    """
    创建指定大小的矩阵
    
    Args:
        rows: 矩阵行数
        cols: 矩阵列数
        fill: 填充值默认为0.0
        
    Returns:
        rows×cols的二维列表矩阵
    """
    return [[fill for _ in range(cols)] for _ in range(rows)]


def generate_random_matrix(rows: int, cols: int, seed: int = 42) -> List[List[float]]:
    """
    生成指定大小的随机矩阵
    
    Args:
        rows: 矩阵行数
        cols: 矩阵列数
        seed: 随机种子用于可重复性
        
    Returns:
        rows×cols的随机矩阵
    """
    random.seed(seed)
    return [[random.random() for _ in range(cols)] for _ in range(rows)]


def matrix_multiply(A: List[List[float]], B: List[List[float]], 
                   n: Optional[int] = None) -> List[List[float]]:
    """
    标准矩阵乘法实现用于对比验证
    
    使用三重循环的标准算法时间复杂度为O(n³)
    
    Args:
        A: 左矩阵
        B: 右矩阵
        n: 矩阵维度如果为None则使用A的行数
        
    Returns:
        乘积矩阵 C = A × B
    """
    if n is None:
        n = len(A)
    
    C = create_matrix(n, n)
    
    for i in range(n):
        for k in range(n):
            aik = A[i][k]
            for j in range(n):
                C[i][j] += aik * B[k][j]
    
    return C


def cache_oblivious_matrix_multiply(A: List[List[float]], B: List[List[float]],
                                    C: List[List[float]], n: int,
                                    row_a: int = 0, col_a: int = 0,
                                    row_b: int = 0, col_b: int = 0,
                                    row_c: int = 0, col_c: int = 0) -> None:
    """
    缓存无关矩阵乘法的核心递归实现
    
    该算法采用分治策略将矩阵划分为子矩阵进行递归计算
    关键优化点在于递归顺序确保了良好的缓存局部性
    
    算法步骤:
    1. 基例处理当矩阵规模小于阈值时使用标准的三重循环
    2. 递归地将三个矩阵各划分为四个n/2×n/2的子矩阵
    3. 按特定顺序计算8个子矩阵乘积并累加到结果矩阵
    
    Args:
        A: 左矩阵
        B: 右矩阵
        C: 结果矩阵（原地修改）
        n: 当前子矩阵的维度
        row_a: A矩阵中当前子矩阵的起始行索引
        col_a: A矩阵中当前子矩阵的起始列索引
        row_b: B矩阵中当前子矩阵的起始行索引
        col_b: B矩阵中当前子矩阵的起始列索引
        row_c: C矩阵中当前子矩阵的起始行索引
        col_c: C矩阵中当前子矩阵的起始列索引
    """
    # 基例:小规模矩阵使用标准算法
    if n <= MATRIX_BLOCK_SIZE:
        standard_multiply_block(A, B, C, n, row_a, col_a, row_b, col_b, row_c, col_c)
        return
    
    # 计算分割维度（尝试使分割接近正方形）
    half_n = n // 2
    
    # 定义子矩阵的起始坐标以减少重复计算
    # A矩阵的四个子矩阵: A11, A12, A21, A22
    # B矩阵的四个子矩阵: B11, B12, B21, B22
    # C矩阵的四个子矩阵: C11, C12, C21, C22
    
    # 递归计算 C11 = A11×B11 + A12×B21
    # 先计算 A11×B11 并累加到 C11
    cache_oblivious_matrix_multiply(
        A, B, C, half_n,
        row_a, col_a,          # A11的起始位置
        row_b, col_b,          # B11的起始位置
        row_c, col_c           # C11的起始位置
    )
    
    # 再计算 A12×B21 并累加到 C11
    cache_oblivious_matrix_multiply(
        A, B, C, half_n,
        row_a, col_a + half_n,  # A12的起始位置
        row_b + half_n, col_b,  # B21的起始位置
        row_c, col_c            # C11的起始位置
    )
    
    # 递归计算 C12 = A11×B12 + A12×B22
    cache_oblivious_matrix_multiply(
        A, B, C, half_n,
        row_a, col_a,           # A11
        row_b, col_b + half_n,  # B12
        row_c, col_c + half_n   # C12
    )
    
    cache_oblivious_matrix_multiply(
        A, B, C, half_n,
        row_a, col_a + half_n,  # A12
        row_b + half_n, col_b + half_n,  # B22
        row_c, col_c + half_n    # C12
    )
    
    # 递归计算 C21 = A21×B11 + A22×B21
    cache_oblivious_matrix_multiply(
        A, B, C, half_n,
        row_a + half_n, col_a,   # A21
        row_b, col_b,            # B11
        row_c + half_n, col_c    # C21
    )
    
    cache_oblivious_matrix_multiply(
        A, B, C, half_n,
        row_a + half_n, col_a + half_n,  # A22
        row_b + half_n, col_b,           # B21
        row_c + half_n, col_c            # C21
    )
    
    # 递归计算 C22 = A21×B12 + A22×B22
    cache_oblivious_matrix_multiply(
        A, B, C, half_n,
        row_a + half_n, col_a,   # A21
        row_b, col_b + half_n,   # B12
        row_c + half_n, col_c + half_n  # C22
    )
    
    cache_oblivious_matrix_multiply(
        A, B, C, half_n,
        row_a + half_n, col_a + half_n,  # A22
        row_b + half_n, col_b + half_n,  # B22
        row_c + half_n, col_c + half_n   # C22
    )


def standard_multiply_block(A: List[List[float]], B: List[List[float]],
                            C: List[List[float]], n: int,
                            row_a: int, col_a: int,
                            row_b: int, col_b: int,
                            row_c: int, col_c: int) -> None:
    """
    标准的三重循环矩阵乘法用于小规模矩阵块
    
    Args:
        A: 左矩阵
        B: 右矩阵
        C: 结果矩阵
        n: 矩阵维度
        row_a: A中当前块的起始行
        col_a: A中当前块的起始列
        row_b: B中当前块的起始行
        col_b: B中当前块的起始列
        row_c: C中当前块的起始行
        col_c: C中当前块的起始列
    """
    for i in range(n):
        for k in range(n):
            aik = A[row_a + i][col_a + k]
            for j in range(n):
                C[row_c + i][col_c + j] += aik * B[row_b + k][col_b + j]


def cache_aware_block_multiply(A: List[List[float]], B: List[List[float]],
                               C: List[List[float]], n: int,
                               block_size: int = 32) -> None:
    """
    缓存感知的分块矩阵乘法
    
    该算法需要显式指定块大小参数通过将矩阵划分为适当大小的块
    来提高缓存命中率这种方法在实际系统中广泛使用但需要针对
    特定的缓存配置进行调优
    
    Args:
        A: 左矩阵
        B: 右矩阵
        C: 结果矩阵
        n: 矩阵维度
        block_size: 分块大小
    """
    for i_block in range(0, n, block_size):
        for k_block in range(0, n, block_size):
            for j_block in range(0, n, block_size):
                # 处理当前块
                i_end = min(i_block + block_size, n)
                k_end = min(k_block + block_size, n)
                j_end = min(j_block + block_size, n)
                
                for i in range(i_block, i_end):
                    for k in range(k_block, k_end):
                        aik = A[i][k]
                        for j in range(j_block, j_end):
                            C[i][j] += aik * B[k][j]


def analyze_cache_efficiency(n: int, cache_size: int = CACHE_SIZE) -> dict:
    """
    分析矩阵乘法的缓存效率
    
    缓存无关矩阵乘法的理想缓存复杂度由Frath和Sebot证明为:
    Q(n, M) = Θ(n² + n³/M^(1/2)) 对于方阵乘法
    Q(n, M) = Θ(n² + n³/M) 对于一般的 n×m × m×p 乘法
    
    Args:
        n: 矩阵维度
        cache_size: 缓存大小（字节）
        
    Returns:
        包含缓存分析结果的字典
    """
    bytes_per_element = 8  # double类型
    elements_in_cache = cache_size // bytes_per_element
    cache_lines = cache_size // CACHE_LINE_SIZE
    
    # 估算标准实现的缓存未命中次数
    # 每次计算 C[i][j] += A[i][k] * B[k][j] 可能导致多次缓存未命中
    # 假设缓存行大小为B每个矩阵元素占用8字节
    standard_cache_misses = (n ** 3) / ELEMENTS_PER_CACHE_LINE
    
    # 缓存无关实现的缓存未命中估算
    # 由于数据重用和良好的局部性实际未命中次数大大减少
    # 使用平方根分割策略时
    co_cache_misses = (n ** 2) + (n ** 3) / math.sqrt(elements_in_cache)
    
    return {
        'matrix_size': n,
        'cache_size_bytes': cache_size,
        'elements_in_cache': elements_in_cache,
        'cache_lines': cache_lines,
        'standard_cache_misses': standard_cache_misses,
        'cache_oblivious_cache_misses': co_cache_misses,
        'improvement_ratio': standard_cache_misses / co_cache_misses if co_cache_misses > 0 else float('inf')
    }


def verify_matrix_correctness(C1: List[List[float]], C2: List[List[float]],
                              tolerance: float = 1e-9) -> bool:
    """
    验证两个矩阵是否相等（浮点容差内）
    
    Args:
        C1: 第一个矩阵
        C2: 第二个矩阵
        tolerance: 允许的绝对误差
        
    Returns:
        如果两矩阵相等返回True
    """
    if len(C1) != len(C2) or len(C1[0]) != len(C2[0]):
        return False
    
    for i in range(len(C1)):
        for j in range(len(C1[0])):
            if abs(C1[i][j] - C2[i][j]) > tolerance:
                return False
    return True


# 时间复杂度说明:
# =============================================================================
# 时间复杂度（比较次数）:
#   - 标准矩阵乘法: O(n³)
#   - Strassen算法: O(n^(2.807)) 比标准算法更优
#   - 缓存无关矩阵乘法: O(n³) 与标准算法相同
#
# 缓存复杂度（缓存未命中次数）:
#   - 标准实现: O(n³/B) 其中B是缓存行大小
#   - 缓存感知分块: O(n³/B) 但常数因子更小
#   - 缓存无关实现: O(n² + n³/M^(1/2)) 其中M是缓存大小
#
# 空间复杂度:
#   - 标准实现: O(n²) 用于存储结果矩阵
#   - 缓存无关实现: 原地操作时为O(1)额外空间
#   - 分块实现: O(block_size²) 用于缓存热点数据
#
# 缓存无关特性:
#   - 算法不假设特定的缓存参数
#   - 递归分割自动适应任意缓存大小
#   - 矩阵的递归分割确保数据在各级缓存中都被高效重用


if __name__ == "__main__":
    print("=" * 70)
    print("缓存无关矩阵乘法测试")
    print("=" * 70)
    
    # 基本正确性测试
    print("\n基本正确性测试:")
    test_sizes = [4, 8, 16, 32]
    
    for n in test_sizes:
        # 生成随机测试矩阵
        A = generate_random_matrix(n, n, seed=42)
        B = generate_random_matrix(n, n, seed=123)
        
        # 标准乘法
        C_standard = matrix_multiply(A, B, n)
        
        # 缓存无关乘法
        C_co = create_matrix(n, n, fill=0.0)
        cache_oblivious_matrix_multiply(A, B, C_co, n)
        
        # 缓存感知分块乘法
        C_ca = create_matrix(n, n, fill=0.0)
        cache_aware_block_multiply(A, B, C_ca, n, block_size=32)
        
        # 验证结果
        correct_co = verify_matrix_correctness(C_standard, C_co)
        correct_ca = verify_matrix_correctness(C_standard, C_ca)
        
        print(f"  维度 {n:>3}: 缓存无关 {'通过' if correct_co else '失败'}, "
              f"缓存感知 {'通过' if correct_ca else '失败'}")
    
    # 性能对比测试
    print("\n性能对比测试:")
    import time
    
    sizes = [64, 128, 256, 512]
    
    for n in sizes:
        A = generate_random_matrix(n, n, seed=42)
        B = generate_random_matrix(n, n, seed=123)
        
        # 缓存无关乘法计时
        C_co = create_matrix(n, n, fill=0.0)
        start = time.perf_counter()
        cache_oblivious_matrix_multiply(A, B, C_co, n)
        co_time = time.perf_counter() - start
        
        # 缓存感知分块乘法计时
        C_ca = create_matrix(n, n, fill=0.0)
        start = time.perf_counter()
        cache_aware_block_multiply(A, B, C_ca, n, block_size=32)
        ca_time = time.perf_counter() - start
        
        # Python内置乘法（使用numpy风格但这里是纯Python实现）
        C_std = matrix_multiply(A, B, n)
        
        print(f"  维度 {n:>4}: 缓存无关 {co_time*1000:>8.2f}ms, "
              f"缓存感知 {ca_time*1000:>8.2f}ms")
    
    # 缓存效率分析
    print("\n缓存效率分析:")
    for cache_size in [256, 1024, 4096, 16384]:
        for n in [64, 128, 256]:
            analysis = analyze_cache_efficiency(n, cache_size)
            print(f"  n={n:>4}, 缓存={cache_size:>6}字节: "
                  f"标准 {analysis['standard_cache_misses']:>12.1f} 未命中, "
                  f"CO {analysis['cache_oblivious_cache_misses']:>12.1f} 未命中, "
                  f"改进比 {analysis['improvement_ratio']:>6.1f}x")
    
    # 大规模测试
    print("\n大规模矩阵乘法测试:")
    large_n = 256
    print(f"  生成 {large_n}×{large_n} 的随机矩阵")
    
    A = generate_random_matrix(large_n, large_n, seed=42)
    B = generate_random_matrix(large_n, large_n, seed=123)
    
    C_result = create_matrix(large_n, large_n, fill=0.0)
    start = time.perf_counter()
    cache_oblivious_matrix_multiply(A, B, C_result, large_n)
    elapsed = time.perf_counter() - start
    
    print(f"  缓存无关乘法耗时: {elapsed*1000:.2f}ms")
    print(f"  结果验证: {'通过' if verify_matrix_correctness(matrix_multiply(A, B, large_n), C_result) else '失败'}")
    
    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)
