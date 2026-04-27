# -*- coding: utf-8 -*-

"""

算法实现：缓存无关算法 / co_lcs



本文件实现 co_lcs 相关的算法功能。

"""



import random

from typing import List, Tuple, Optional, Set





# 算法配置常量

# =============================================================================

# SMALL LCS THRESHOLD: 小规模LCS问题的切换阈值

SMALL_LCS_THRESHOLD = 32



# CACHE_LINE_SIZE: 模拟的缓存行大小用于分析缓存行为

CACHE_LINE_SIZE = 64



# MATCH标记: 用于标记动态规划表中的匹配位置

MATCH = 1



# 辅助缓冲区块大小

AUX_BUFFER_SIZE = 4096





def standard_lcs(X: List, Y: List) -> Tuple[int, List]:

    """

    标准LCS动态规划实现

    

    构建m×n的DP表其中dp[i][j]表示X[0..i]和Y[0..j]的LCS长度

    状态转移方程:

        if X[i-1] == Y[j-1]: dp[i][j] = dp[i-1][j-1] + 1

        else: dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    

    Args:

        X: 第一个序列

        Y: 第二个序列

        

    Returns:

        (LCS长度, LCS序列)

    """

    m = len(X)

    n = len(Y)

    

    # 创建DP表

    dp = [[0] * (n + 1) for _ in range(m + 1)]

    

    # 填充DP表

    for i in range(1, m + 1):

        for j in range(1, n + 1):

            if X[i - 1] == Y[j - 1]:

                dp[i][j] = dp[i - 1][j - 1] + 1

            else:

                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    

    # 回溯找出LCS

    lcs_length = dp[m][n]

    lcs = []

    i, j = m, n

    

    while i > 0 and j > 0:

        if X[i - 1] == Y[j - 1]:

            lcs.append(X[i - 1])

            i -= 1

            j -= 1

        elif dp[i - 1][j] >= dp[i][j - 1]:

            i -= 1

        else:

            j -= 1

    

    lcs.reverse()

    return lcs_length, lcs





def hirschberg_lcs(X: List, Y: List) -> Tuple[int, List]:

    """

    Hirschberg算法 - 空间优化的LCS算法

    

    该算法结合了分治策略和动态规划只需要O(min(m,n))的额外空间

    基本思想是在X的中间位置将问题分成两半通过一次前向DP和一次

    后向DP来确定分割点然后递归处理左右两部分

    

    Args:

        X: 第一个序列

        Y: 第二个序列

        

    Returns:

        (LCS长度, LCS序列)

    """

    m = len(X)

    n = len(Y)

    

    # 基例:任一序列为空

    if m == 0:

        return 0, []

    if n == 0:

        return 0, []

    

    # 小规模问题使用标准算法

    if m <= SMALL_LCS_THRESHOLD or n <= SMALL_LCS_THRESHOLD:

        return standard_lcs(X, Y)

    

    # 找到X的中间位置

    mid = m // 2

    

    # 前向DP:从左到右计算到mid的行为止

    # prev_row表示dp[0..mid][j]的值

    prev_row = [0] * (n + 1)

    curr_row = [0] * (n + 1)

    

    for j in range(1, n + 1):

        if X[mid - 1] == Y[j - 1]:

            curr_row[j] = prev_row[j - 1] + 1

        else:

            curr_row[j] = max(prev_row[j], curr_row[j - 1])

    

    # 后向DP:从右到左计算从mid+1到末尾的行

    # next_row表示dp[mid+1..m][j]的值

    next_row = [0] * (n + 1)

    temp_row = [0] * (n + 1)

    

    for j in range(n - 1, -1, -1):

        if X[mid] == Y[j]:

            temp_row[j] = next_row[j + 1] + 1

        else:

            temp_row[j] = max(next_row[j], temp_row[j + 1])

    

    # 找到使总长度最大的分割点

    max_sum = -1

    split_y = 0

    

    for j in range(n + 1):

        total = curr_row[j] + temp_row[j]

        if total > max_sum:

            max_sum = total

            split_y = j

    

    # 递归处理左右两部分

    left_len, left_lcs = hirschberg_lcs(X[:mid], Y[:split_y])

    right_len, right_lcs = hirschberg_lcs(X[mid:], Y[split_y:])

    

    return left_len + right_len, left_lcs + right_lcs





def cache_oblivious_lcs_length(X: List, Y: List,

                               x_start: int, x_end: int,

                               y_start: int, y_end: int) -> int:

    """

    缓存无关LCS长度的递归计算

    

    该函数使用分治策略计算子序列X[x_start..x_end)和Y[y_start..y_end)

    的LCS长度通过巧妙地安排计算顺序来优化缓存行为

    

    算法思想:

    1. 如果任一序列为空LCS长度为0

    2. 如果两个序列都很小直接使用标准DP

    3. 否则将X分成两半找到Y中的最佳分割点递归计算

    

    Args:

        X: 第一个序列

        Y: 第二个序列

        x_start: X的起始索引（包含）

        x_end: X的结束索引（不包含）

        y_start: Y的起始索引（包含）

        y_end: Y的结束索引（不包含）

        

    Returns:

        LCS长度

    """

    x_len = x_end - x_start

    y_len = y_end - y_start

    

    # 基例:任一序列为空

    if x_len == 0 or y_len == 0:

        return 0

    

    # 小规模问题使用标准DP

    if x_len <= SMALL_LCS_THRESHOLD or y_len <= SMALL_LCS_THRESHOLD:

        return small_lcs_dp(X, Y, x_start, x_end, y_start, y_end)

    

    # 将X分成两半

    x_mid = (x_start + x_end) // 2

    

    # 计算前向DP表:只保留到x_mid的行为止

    front_dp = compute_forward_dp(X, Y, x_start, x_mid, y_start, y_end)

    

    # 计算后向DP表:从x_mid到末尾

    back_dp = compute_backward_dp(X, Y, x_mid, x_end, y_start, y_end)

    

    # 找到Y中的最佳分割点

    max_length = -1

    best_split = y_start

    

    for j in range(y_end - y_start + 1):

        total = front_dp[j] + back_dp[j + 1]

        if total > max_length:

            max_length = total

            best_split = y_start + j

    

    # 递归处理左右两部分

    left_length = cache_oblivious_lcs_length(

        X, Y, x_start, x_mid, y_start, best_split

    )

    right_length = cache_oblivious_lcs_length(

        X, Y, x_mid, x_end, best_split, y_end

    )

    

    return left_length + right_length





def small_lcs_dp(X: List, Y: List,

                 x_start: int, x_end: int,

                 y_start: int, y_end: int) -> int:

    """

    对小规模序列使用标准动态规划计算LCS长度

    

    Args:

        X: 第一个序列

        Y: 第二个序列

        x_start: X的起始索引

        x_end: X的结束索引

        y_start: Y的起始索引

        y_end: Y的结束索引

        

    Returns:

        LCS长度

    """

    x_len = x_end - x_start

    y_len = y_end - y_start

    

    # 创建DP表

    dp = [[0] * (y_len + 1) for _ in range(x_len + 1)]

    

    # 填充DP表

    for i in range(1, x_len + 1):

        for j in range(1, y_len + 1):

            if X[x_start + i - 1] == Y[y_start + j - 1]:

                dp[i][j] = dp[i - 1][j - 1] + 1

            else:

                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    

    return dp[x_len][y_len]





def compute_forward_dp(X: List, Y: List,

                      x_start: int, x_end: int,

                      y_start: int, y_end: int) -> List[int]:

    """

    计算前向动态规划表的部分结果

    

    计算dp[x_start..x_end][y_start..y_end]中第x_end-x_start行的值

    只保留最后一行以节省空间

    

    Args:

        X: 第一个序列

        Y: 第二个序列

        x_start: 起始行索引

        x_end: 结束行索引

        y_start: 起始列索引

        y_end: 结束列索引

        

    Returns:

        动态规划表的最后一行

    """

    y_len = y_end - y_start

    

    prev_row = [0] * (y_len + 1)

    curr_row = [0] * (y_len + 1)

    

    for i in range(x_start, x_end):

        for j in range(y_start, y_end + 1):

            if j == y_start:

                curr_row[j - y_start] = 0

            elif X[i] == Y[j - 1]:

                curr_row[j - y_start] = prev_row[j - 1 - y_start] + 1

            else:

                curr_row[j - y_start] = max(

                    prev_row[j - y_start],

                    curr_row[j - 1 - y_start]

                )

        prev_row, curr_row = curr_row, prev_row

    

    return prev_row





def compute_backward_dp(X: List, Y: List,

                       x_start: int, x_end: int,

                       y_start: int, y_end: int) -> List[int]:

    """

    计算后向动态规划表的部分结果

    

    从后向前计算dp[x_start..x_end][y_start..y_end]的值

    同样只保留最后一行

    

    Args:

        X: 第一个序列

        Y: 第二个序列

        x_start: 起始行索引

        x_end: 结束行索引

        y_start: 起始列索引

        y_end: 结束列索引

        

    Returns:

        动态规划表的最后一行

    """

    y_len = y_end - y_start

    

    next_row = [0] * (y_len + 2)  # 多一个元素便于边界处理

    curr_row = [0] * (y_len + 2)

    

    for i in range(x_end - 1, x_start - 1, -1):

        for j in range(y_end, y_start - 1, -1):

            if i == x_end - 1:

                curr_row[j - y_start + 1] = 0

            elif X[i + 1] == Y[j - 1]:

                curr_row[j - y_start + 1] = next_row[j - y_start + 2] + 1

            else:

                curr_row[j - y_start + 1] = max(

                    next_row[j - y_start + 1],

                    curr_row[j - y_start + 2]

                )

        next_row, curr_row = curr_row, next_row

    

    return next_row[1:y_len + 2]





def analyze_cache_access_pattern(length_x: int, length_y: int,

                                cache_size: int = 1024) -> dict:

    """

    分析LCS算法的缓存访问模式

    

    缓存无关LCS的关键在于减少了夸缓存行边界的访问

    该函数模拟计算不同缓存大小下的预期缓存未命中次数

    

    Args:

        length_x: 序列X的长度

        length_y: 序列Y的长度

        cache_size: 缓存大小（字节）

        

    Returns:

        包含缓存分析结果的字典

    """

    # 标准DP表访问产生的缓存未命中

    standard_accesses = length_x * length_y

    standard_cache_misses = standard_accesses // 8  # 简化估算

    

    # 缓存无关算法的缓存未命中（利用数据局部性）

    # 分治策略确保热点数据在缓存中得到重用

    cache_oblivious_misses = (

        (length_x * length_y) // 16 +

        length_x * (length_y // cache_size)

    )

    

    return {

        'x_length': length_x,

        'y_length': length_y,

        'cache_size': cache_size,

        'standard_cache_misses': standard_cache_misses,

        'cache_oblivious_misses': cache_oblivious_misses,

        'improvement_ratio': (

            standard_cache_misses / cache_oblivious_misses

            if cache_oblivious_misses > 0 else float('inf')

        )

    }





def generate_random_sequence(length: int, alphabet_size: int = 26,

                             seed: int = 42) -> List:

    """

    生成随机序列用于测试

    

    Args:

        length: 序列长度

        alphabet_size: 字母表大小

        seed: 随机种子

        

    Returns:

        随机字符序列

    """

    random.seed(seed)

    return [chr(ord('A') + random.randint(0, alphabet_size - 1))

            for _ in range(length)]





# 时间复杂度说明:

# =============================================================================

# 标准LCS算法:

#   - 时间复杂度: O(mn)

#   - 空间复杂度: O(mn) 或 O(min(m,n)) 使用空间优化版本

#

# Hirschberg算法:

#   - 时间复杂度: O(mn)

#   - 空间复杂度: O(min(m,n))

#

# 缓存无关LCS:

#   - 时间复杂度: O(mn) 与标准算法相同

#   - 空间复杂度: O(min(m,n) + y) 其中y是Y的长度

#   - 缓存复杂度: O(mn/B + m/B) 显著优于标准实现的O(mn/B)

#

# 缓存无关特性:

#   - 算法利用分治策略将大数据划分到不同缓存层级

#   - 每次递归调用只处理子问题所需的数据量

#   - 热数据在各级缓存中得到有效重用





if __name__ == "__main__":

    print("=" * 70)

    print("缓存无关最长公共子序列测试")

    print("=" * 70)

    

    # 基本正确性测试

    print("\n基本正确性测试:")

    test_cases = [

        (["A", "B", "C", "D"], ["A", "C", "B", "D"]),

        (["A", "G", "T", "T", "C"], ["A", "C", "T", "C", "T", "C"]),

        (list("AGCATG"), list("GATCGC")),

        (list("ABCD"), list("ABCD")),

        (list("ABCD"), list("WXYZ")),

    ]

    

    for i, (X, Y) in enumerate(test_cases):

        # 标准LCS

        std_len, std_lcs = standard_lcs(X, Y)

        

        # Hirschberg L CS

        h_len, h_lcs = hirschberg_lcs(X, Y)

        

        # 缓存无关LCS（只计算长度）

        co_len = cache_oblivious_lcs_length(

            X, Y, 0, len(X), 0, len(Y)

        )

        

        std_correct = (std_len == h_len)

        co_correct = (std_len == co_len)

        

        print(f"  测试 {i+1}: 标准={std_len}, Hirschberg={h_len}, "

              f"缓存无关={co_len}, "

              f"结果 {'一致' if std_correct and co_correct else '不一致'}")

    

    # Hirschberg完整LCS测试

    print("\nHirschberg完整LCS序列测试:")

    test_pairs = [

        ("AGCATG", "GATCGC"),

        ("ACCGGTCGAGTGCGCGGAAGCCGGCCGAA", "GTCGTTCGGAATGCCGTTGCTCTGTAAA"),

        ("ABCBDAB", "BDCAB"),

    ]

    

    for X_str, Y_str in test_pairs:

        X = list(X_str)

        Y = list(Y_str)

        _, lcs = hirschberg_lcs(X, Y)

        print(f"  X={X_str}, Y={Y_str}")

        print(f"  LCS={''.join(lcs)} (长度={len(lcs)})")

    

    # 性能对比测试

    print("\n性能对比测试:")

    import time

    

    sizes = [(50, 50), (100, 100), (200, 200), (500, 500)]

    

    for m, n in sizes:

        X = generate_random_sequence(m, seed=42)

        Y = generate_random_sequence(n, seed=123)

        

        # 标准算法

        start = time.perf_counter()

        std_len, _ = standard_lcs(X, Y)

        std_time = time.perf_counter() - start

        

        # Hirschberg算法

        start = time.perf_counter()

        h_len, _ = hirschberg_lcs(X, Y)

        h_time = time.perf_counter() - start

        

        # 缓存无关算法

        start = time.perf_counter()

        co_len = cache_oblivious_lcs_length(X, Y, 0, m, 0, n)

        co_time = time.perf_counter() - start

        

        print(f"  规模 {m:>4}×{n:>4}: 标准 {std_time*1000:>8.2f}ms, "

              f"Hirschberg {h_time*1000:>8.2f}ms, "

              f"缓存无关 {co_time*1000:>8.2f}ms")

    

    # 缓存行为分析

    print("\n缓存行为分析:")

    for m in [64, 128, 256]:

        for cache_size in [256, 1024, 4096]:

            analysis = analyze_cache_access_pattern(m, m, cache_size)

            print(f"  {m}×{m}, 缓存={cache_size:>5}字节: "

                  f"标准 {analysis['standard_cache_misses']:>10}, "

                  f"CO {analysis['cache_oblivious_misses']:>10}, "

                  f"改进 {analysis['improvement_ratio']:.2f}x")

    

    # 大规模测试

    print("\n大规模LCS测试:")

    large_m, large_n = 1000, 1000

    X = generate_random_sequence(large_m, seed=42)

    Y = generate_random_sequence(large_n, seed=123)

    

    start = time.perf_counter()

    co_len = cache_oblivious_lcs_length(X, Y, 0, large_m, 0, large_n)

    co_time = time.perf_counter() - start

    

    print(f"  规模 {large_m}×{large_n} 的LCS长度: {co_len}")

    print(f"  缓存无关算法耗时: {co_time*1000:.2f}ms")

    

    print("\n" + "=" * 70)

    print("测试完成!")

    print("=" * 70)

