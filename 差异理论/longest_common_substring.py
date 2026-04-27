# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / longest_common_substring

本文件实现 longest_common_substring 相关的算法功能。
"""

def longest_common_substring(str_a, str_b):
    """
    找出两个字符串的最长公共子串
    
    参数:
        str_a: 第一个字符串
        str_b: 第二个字符串
    
    返回:
        (最长子串, 长度, 在str_a中的位置, 在str_b中的位置)
    """
    n = len(str_a)
    m = len(str_b)
    
    # DP表，dp[i][j]表示以str_a[i-1]和str_b[j-1]结尾的公共子串长度
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    
    # 记录最大长度和位置
    max_length = 0
    max_i = 0  # 在str_a中的结束位置（1-based）
    max_j = 0  # 在str_b中的结束位置（1-based）
    
    # 填充DP表
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if str_a[i - 1] == str_b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                
                # 更新最大长度
                if dp[i][j] > max_length:
                    max_length = dp[i][j]
                    max_i = i
                    max_j = j
            else:
                dp[i][j] = 0
    
    # 提取最长公共子串
    substring = str_a[max_i - max_length:max_i]
    
    return substring, max_length, max_i - max_length, max_j - max_length


def longest_common_substring_all(str_a, str_b):
    """
    找出所有最长公共子串
    
    参数:
        str_a: 第一个字符串
        str_b: 第二个字符串
    
    返回:
        所有最长公共子串的列表
    """
    n = len(str_a)
    m = len(str_b)
    
    # DP表
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    
    # 找出最大长度
    max_length = 0
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if str_a[i - 1] == str_b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                max_length = max(max_length, dp[i][j])
    
    # 收集所有最长子串
    substrings = set()
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if dp[i][j] == max_length:
                substring = str_a[i - max_length:i]
                substrings.add(substring)
    
    return list(substrings)


def longest_common_substring_length(str_a, str_b):
    """
    只计算最长公共子串的长度（空间优化版本）
    
    使用滚动数组，将空间复杂度降到O(min(n, m))
    
    参数:
        str_a: 第一个字符串
        str_b: 第二个字符串
    
    返回:
        最长公共子串的长度
    """
    # 确保str_a是较短的字符串
    if len(str_a) > len(str_b):
        str_a, str_b = str_b, str_a
    
    n = len(str_a)
    m = len(str_b)
    
    # 只需要两行
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)
    
    max_length = 0
    
    for j in range(1, m + 1):
        for i in range(1, n + 1):
            if str_a[i - 1] == str_b[j - 1]:
                curr[i] = prev[i - 1] + 1
                max_length = max(max_length, curr[i])
            else:
                curr[i] = 0
        
        # 交换行
        prev, curr = curr, prev
    
    return max_length


def lcs_with_positions(str_a, str_b):
    """
    找出最长公共子串及其在两个字符串中的位置
    
    参数:
        str_a: 第一个字符串
        str_b: 第二个字符串
    
    返回:
        包含位置信息的字典
    """
    n = len(str_a)
    m = len(str_b)
    
    # DP表
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    
    max_length = 0
    result = []
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if str_a[i - 1] == str_b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                
                if dp[i][j] > max_length:
                    max_length = dp[i][j]
                    result = [{
                        'substring': str_a[i - max_length:i],
                        'pos_a': i - max_length,
                        'pos_b': j - max_length,
                        'length': max_length
                    }]
                elif dp[i][j] == max_length:
                    result.append({
                        'substring': str_a[i - max_length:i],
                        'pos_a': i - max_length,
                        'pos_b': j - max_length,
                        'length': max_length
                    })
            else:
                dp[i][j] = 0
    
    return {
        'max_length': max_length,
        'matches': result
    }


def diff_using_lcs(str_a, str_b):
    """
    使用最长公共子串进行diff分析
    
    参数:
        str_a: 原始字符串
        str_b: 新字符串
    
    返回:
        差异列表 [(type, content, position), ...]
    """
    result = lcs_with_positions(str_a, str_b)
    
    if result['max_length'] == 0:
        # 没有公共子串，全部是替换
        return [('delete', str_a, 0), ('insert', str_b, 0)]
    
    diff_result = []
    
    # 按位置排序所有匹配
    all_events = []
    
    # 添加标记点
    prev_a = 0
    prev_b = 0
    
    for match in result['matches']:
        pos_a = match['pos_a']
        pos_b = match['pos_b']
        
        # 添加删除部分
        if pos_a > prev_a:
            deleted = str_a[prev_a:pos_a]
            if deleted:
                diff_result.append(('delete', deleted, prev_a))
        
        # 添加插入部分
        if pos_b > prev_b:
            inserted = str_b[prev_b:pos_b]
            if inserted:
                diff_result.append(('insert', inserted, prev_b))
        
        # 添加公共部分
        diff_result.append(('equal', match['substring'], pos_a))
        
        prev_a = pos_a + match['length']
        prev_b = pos_b + match['length']
    
    # 处理末尾
    if prev_a < len(str_a):
        diff_result.append(('delete', str_a[prev_a:], prev_a))
    if prev_b < len(str_b):
        diff_result.append(('insert', str_b[prev_b:], prev_b))
    
    return diff_result


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本最长公共子串
    print("=" * 50)
    print("测试1: 基本最长公共子串")
    print("=" * 50)
    
    test_cases = [
        ("ababc", "abcdaba"),  # 应该是 "ababa" 或 "daba"
        ("ABAB", "BABA"),      # 应该是 "ABA" 或 "BAB"
        ("算法", "算abc法"),   # 应该是 "算" 或 "法"
        ("same", "different"),  # 应该无公共子串
    ]
    
    for str_a, str_b in test_cases:
        substring, length, pos_a, pos_b = longest_common_substring(str_a, str_b)
        print(f"'{str_a}' 与 '{str_b}'")
        print(f"  最长公共子串: '{substring}'")
        print(f"  长度: {length}, 位置: A[{pos_a}], B[{pos_b}]")
        print()
    
    # 测试用例2：所有最长公共子串
    print("=" * 50)
    print("测试2: 所有最长公共子串")
    print("=" * 50)
    
    str_a = "ABAB"
    str_b = "BABA"
    
    substrings = longest_common_substring_all(str_a, str_b)
    print(f"'{str_a}' 与 '{str_b}' 的所有最长公共子串: {substrings}")
    
    # 测试用例3：空间优化版本
    print("\n" + "=" * 50)
    print("测试3: 空间优化版本")
    print("=" * 50)
    
    str_a = "thisisatest"
    str_b = "testing123testing"
    
    length_optimized = longest_common_substring_length(str_a, str_b)
    substring, length, _, _ = longest_common_substring(str_a, str_b)
    
    print(f"'{str_a}' 与 '{str_b}'")
    print(f"  标准版本长度: {length}")
    print(f"  优化版本长度: {length_optimized}")
    print(f"  最长子串: '{substring}'")
    
    # 测试用例4：位置信息
    print("\n" + "=" * 50)
    print("测试4: 位置信息")
    print("=" * 50)
    
    str_a = "ABCDEF"
    str_b = "XYZABCUVWABC"
    
    result = lcs_with_positions(str_a, str_b)
    print(f"'{str_a}' 与 '{str_b}'")
    print(f"最长长度: {result['max_length']}")
    for match in result['matches']:
        print(f"  子串: '{match['substring']}' @ A[{match['pos_a']}], B[{match['pos_b']}]")
    
    # 测试用例5：diff应用
    print("\n" + "=" * 50)
    print("测试5: Diff应用")
    print("=" * 50)
    
    str_a = "ABCDEFGH"
    str_b = "ABXYDEFMN"
    
    diff = diff_using_lcs(str_a, str_b)
    print(f"原始: '{str_a}'")
    print(f"新:   '{str_b}'")
    print("\n差异:")
    for op, content, pos in diff:
        if op == 'equal':
            print(f"  {content}", end='')
        elif op == 'delete':
            print(f"[-{content}-]", end='')
        else:
            print(f"[+{content}+]", end='')
    print()
