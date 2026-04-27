# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / lcs_algorithm

本文件实现 lcs_algorithm 相关的算法功能。
"""

def lcs_length(text_a, text_b):
    """
    计算最长公共子序列的长度
    
    参数:
        text_a: 第一个文本序列
        text_b: 第二个文本序列
    
    返回:
        LCS长度和回溯路径
    """
    n = len(text_a)
    m = len(text_b)
    
    # 创建DP表，dp[i][j]表示text_a[:i]和text_b[:j]的LCS长度
    # 初始化为(n+1) x (m+1)的零矩阵
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    
    # 填充DP表
    # 遍历text_a的每个位置
    for i in range(1, n + 1):
        # 遍历text_b的每个位置
        for j in range(1, m + 1):
            if text_a[i - 1] == text_b[j - 1]:
                # 字符匹配，LCS长度加1
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                # 字符不匹配，取两个方向的最大值
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    return dp[n][m], dp


def lcs_backtrack(dp, text_a, text_b):
    """
    通过DP表回溯找出LCS的具体内容
    
    参数:
        dp: LCS长度DP表
        text_a: 第一个文本
        text_b: 第二个文本
    
    返回:
        最长公共子序列字符串
    """
    i = len(text_a)
    j = len(text_b)
    lcs_result = []
    
    # 从末尾开始回溯
    while i > 0 and j > 0:
        if text_a[i - 1] == text_b[j - 1]:
            # 字符匹配，加入LCS
            lcs_result.append(text_a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            # 来自上方，选择较大的
            i -= 1
        else:
            # 来自左方
            j -= 1
    
    # 反转得到正确顺序
    lcs_result.reverse()
    return ''.join(lcs_result)


def lcs_diff(text_a, text_b):
    """
    生成类似diff的LCS对比结果
    
    返回每个字符的状态：'equal', 'delete', 'insert'
    
    参数:
        text_a: 原始文本
        text_b: 目标文本
    
    返回:
        对比结果列表
    """
    n = len(text_a)
    m = len(text_b)
    
    # 计算DP表
    _, dp = lcs_length(text_a, text_b)
    
    # 回溯生成diff
    result = []
    i = n
    j = m
    
    while i > 0 or j > 0:
        if i > 0 and j > 0 and text_a[i - 1] == text_b[j - 1]:
            # 字符相同
            result.append(('equal', text_a[i - 1]))
            i -= 1
            j -= 1
        elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):
            # text_b中的字符是新增的
            result.append(('insert', text_b[j - 1]))
            j -= 1
        else:
            # text_a中的字符被删除
            result.append(('delete', text_a[i - 1]))
            i -= 1
    
    result.reverse()
    return result


def one_direction_diff(text_a, text_b):
    """
    简化的单向diff，用于显示从text_a到text_b的变化
    
    参数:
        text_a: 原始文本
        text_b: 目标文本
    
    返回:
        差异列表
    """
    diff = lcs_diff(text_a, text_b)
    result = []
    
    for op, char in diff:
        if op == 'equal':
            result.append(f" {char}")
        elif op == 'delete':
            result.append(f"-{char}")
        else:  # insert
            result.append(f"+{char}")
    
    return ''.join(result)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本LCS
    print("=" * 50)
    print("测试1: 基本LCS计算")
    print("=" * 50)
    
    text_a = "ABCDGH"
    text_b = "AEDFHR"
    length, _ = lcs_length(text_a, text_b)
    lcs = lcs_backtrack(_, text_a, text_b)
    print(f"文本A: {text_a}")
    print(f"文本B: {text_b}")
    print(f"LCS长度: {length}")
    print(f"LCS内容: {lcs}")
    
    # 测试用例2：Git风格的diff
    print("\n" + "=" * 50)
    print("测试2: Git风格diff输出")
    print("=" * 50)
    
    text_a = "The quick brown fox jumps"
    text_b = "The slow brown fox walks"
    print(f"原始: {text_a}")
    print(f"目标: {text_b}")
    print("\nDiff结果:")
    print(one_direction_diff(text_a, text_b))
    
    # 测试用例3：完整句子对比
    print("\n" + "=" * 50)
    print("测试3: 句子级别对比")
    print("=" * 50)
    
    words_a = ["The", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"]
    words_b = ["The", "slow", "brown", "fox", "walks", "over", "the", "tired", "dog"]
    
    # 将单词列表转换为字符串进行LCS
    str_a = ' '.join(words_a)
    str_b = ' '.join(words_b)
    
    diff_result = lcs_diff(str_a, str_b)
    print("对比结果:")
    for op, char in diff_result:
        if op == 'equal':
            print(f"  {char}", end='')
        elif op == 'delete':
            print(f"[-{char}]", end='')
        else:
            print(f"[+{char}]", end='')
    print()
    
    # 测试用例4：无公共子序列
    print("\n" + "=" * 50)
    print("测试4: 无公共子序列")
    print("=" * 50)
    
    text_a = "ABC"
    text_b = "XYZ"
    length, _ = lcs_length(text_a, text_b)
    print(f"文本A: {text_a}")
    print(f"文本B: {text_b}")
    print(f"LCS长度: {length}")
    print("Diff:", one_direction_diff(text_a, text_b))
    
    # 测试用例5：完全相同
    print("\n" + "=" * 50)
    print("测试5: 相同文本")
    print("=" * 50)
    
    text_a = "identical"
    text_b = "identical"
    length, _ = lcs_length(text_a, text_b)
    print(f"文本A: {text_a}")
    print(f"文本B: {text_b}")
    print(f"LCS长度: {length}")
    print("Diff:", one_direction_diff(text_a, text_b))
