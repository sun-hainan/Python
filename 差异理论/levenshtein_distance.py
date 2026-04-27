# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / levenshtein_distance

本文件实现 levenshtein_distance 相关的算法功能。
"""

def levenshtein_distance(str_a, str_b):
    """
    计算两个字符串的Levenshtein编辑距离
    
    参数:
        str_a: 第一个字符串
        str_b: 第二个字符串
    
    返回:
        编辑距离（整数）
    """
    n = len(str_a)
    m = len(str_b)
    
    # 创建DP表，dp[i][j]表示str_a[:i]到str_b[:j]的编辑距离
    # 使用(n+1) x (m+1)的矩阵
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    
    # 初始化第一行和第一列
    # 将空字符串转换为str_a[:i]需要i次插入
    for i in range(n + 1):
        dp[i][0] = i
    # 将空字符串转换为str_b[:j]需要j次插入
    for j in range(m + 1):
        dp[0][j] = j
    
    # 填充DP表
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if str_a[i - 1] == str_b[j - 1]:
                # 字符相同，无需操作
                dp[i][j] = dp[i - 1][j - 1]
            else:
                # 取三种操作的最小值加1
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # 删除str_a[i-1]
                    dp[i][j - 1],      # 插入str_b[j-1]
                    dp[i - 1][j - 1]   # 替换str_a[i-1]为str_b[j-1]
                )
    
    return dp[n][m]


def levenshtein_distance_with_trace(str_a, str_b):
    """
    计算编辑距离并记录编辑路径
    
    参数:
        str_a: 第一个字符串
        str_b: 第二个字符串
    
    返回:
        (编辑距离, 编辑路径)
        编辑路径是一个列表，包含(op, index_a, index_b, char)元组
        op为'insert', 'delete', 'replace', 'equal'
    """
    n = len(str_a)
    m = len(str_b)
    
    # DP表
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    
    # 初始化
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    
    # 填充
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if str_a[i - 1] == str_b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    
    # 回溯找编辑路径
    path = []
    i = n
    j = m
    
    while i > 0 or j > 0:
        if i > 0 and j > 0 and str_a[i - 1] == str_b[j - 1]:
            path.append(('equal', i - 1, j - 1, str_a[i - 1]))
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            path.append(('replace', i - 1, j - 1, str_b[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            path.append(('delete', i - 1, j, str_a[i - 1]))
            i -= 1
        else:
            path.append(('insert', i, j - 1, str_b[j - 1]))
            j -= 1
    
    path.reverse()
    return dp[n][m], path


def damerau_levenshtein_distance(str_a, str_b):
    """
    计算Damerau-Levenshtein编辑距离
    
    与标准Levenshtein距离不同，它还允许：
    - 相邻字符的交换（Transposition）
    
    参数:
        str_a: 第一个字符串
        str_b: 第二个字符串
    
    返回:
        编辑距离
    """
    n = len(str_a)
    m = len(str_b)
    
    # DP表
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    
    # 初始化
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    
    # 填充
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if str_a[i - 1] == str_b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(
                    dp[i - 1][j],      # 删除
                    dp[i][j - 1],      # 插入
                    dp[i - 1][j - 1]   # 替换
                )
            
            # 检查相邻字符交换
            if i > 1 and j > 1:
                if str_a[i - 1] == str_b[j - 2] and str_a[i - 2] == str_b[j - 1]:
                    dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)
    
    return dp[n][m]


def normalized_levenshtein(str_a, str_b):
    """
    计算归一化编辑距离
    
    返回0到1之间的值，0表示完全相同，1表示完全不同
    
    参数:
        str_a: 第一个字符串
        str_b: 第二个字符串
    
    返回:
        归一化距离（浮点数）
    """
    if len(str_a) == 0 and len(str_b) == 0:
        return 0.0
    
    distance = levenshtein_distance(str_a, str_b)
    max_len = max(len(str_a), len(str_b))
    
    return distance / max_len


def similarity_ratio(str_a, str_b):
    """
    计算两个字符串的相似度比率
    
    参数:
        str_a: 第一个字符串
        str_b: 第二个字符串
    
    返回:
        相似度（0到1之间的浮点数）
    """
    return 1.0 - normalized_levenshtein(str_a, str_b)


def format_edit_path(path):
    """
    格式化编辑路径为可读字符串
    
    参数:
        path: 编辑路径列表
    
    返回:
        格式化的字符串
    """
    result = []
    for op, idx_a, idx_b, char in path:
        if op == 'equal':
            result.append(f"  {char}")
        elif op == 'replace':
            result.append(f"R {char} (at {idx_a} -> {idx_b})")
        elif op == 'delete':
            result.append(f"D {char} (at {idx_a})")
        elif op == 'insert':
            result.append(f"I {char} (at {idx_b})")
    
    return '\n'.join(result)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本编辑距离
    print("=" * 50)
    print("测试1: 基本编辑距离")
    print("=" * 50)
    
    test_cases = [
        ("kitten", "sitting"),
        ("flaw", "lawn"),
        ("saturday", "sunday"),
        ("same", "same"),
        ("", "abc"),
        ("abc", ""),
    ]
    
    for str_a, str_b in test_cases:
        distance = levenshtein_distance(str_a, str_b)
        print(f"'{str_a}' -> '{str_b}': 距离 = {distance}")
    
    # 测试用例2：带路径的编辑距离
    print("\n" + "=" * 50)
    print("测试2: 编辑路径追踪")
    print("=" * 50)
    
    str_a = "abc"
    str_b = "adc"
    
    distance, path = levenshtein_distance_with_trace(str_a, str_b)
    print(f"'{str_a}' -> '{str_b}': 距离 = {distance}")
    print("\n编辑路径:")
    print(format_edit_path(path))
    
    # 测试用例3：Damerau-Levenshtein
    print("\n" + "=" * 50)
    print("测试3: Damerau-Levenshtein距离")
    print("=" * 50)
    
    # "ab" -> "ba" 只需要一次交换
    distance = damerau_levenshtein_distance("ab", "ba")
    print(f"'ab' -> 'ba': Damerau距离 = {distance}")
    
    # 标准Levenshtein需要两次操作（删除+插入）
    distance = levenshtein_distance("ab", "ba")
    print(f"'ab' -> 'ba': 标准距离 = {distance}")
    
    # 测试用例4：相似度计算
    print("\n" + "=" * 50)
    print("测试4: 字符串相似度")
    print("=" * 50)
    
    pairs = [
        ("elephant", "relevant"),
        ("晚上", "夜"),
        ("hello world", "hello"),
    ]
    
    for str_a, str_b in pairs:
        ratio = similarity_ratio(str_a, str_b)
        normalized = normalized_levenshtein(str_a, str_b)
        print(f"'{str_a}' vs '{str_b}':")
        print(f"  相似度: {ratio:.4f}")
        print(f"  归一化距离: {normalized:.4f}")
    
    # 测试用例5：实际应用 - 拼写检查
    print("\n" + "=" * 50)
    print("测试5: 拼写检查应用")
    print("=" * 50)
    
    dictionary = ["apple", "banana", "orange", "grape", "mango"]
    typo = "aple"
    
    print(f"输入: '{typo}'")
    print("可能的正确拼写:")
    
    distances = []
    for word in dictionary:
        dist = levenshtein_distance(typo, word)
        distances.append((word, dist))
    
    distances.sort(key=lambda x: x[1])
    
    for word, dist in distances[:3]:
        ratio = similarity_ratio(typo, word)
        print(f"  {word}: 距离={dist}, 相似度={ratio:.2f}")
