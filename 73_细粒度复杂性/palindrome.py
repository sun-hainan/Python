# -*- coding: utf-8 -*-

"""

算法实现：细粒度复杂性 / palindrome



本文件实现 palindrome 相关的算法功能。

"""



from typing import List, Tuple





def longest_palindrome_manacher(s: str) -> Tuple[int, int]:

    """

    Manacher算法:线性时间找最长回文

    O(n)时间,O(n)空间

    

    Args:

        s: 输入字符串

    

    Returns:

        (最长回文起始位置, 结束位置(不包括))

    """

    n = len(s)

    if n == 0:

        return 0, 0

    

    # 预处理:在字符间插入分隔符

    t = '#' + '#'.join(s) + '#'

    m = len(t)

    

    # P[i] = 以t[i]为中心的最长回文的半径

    P = [0] * m

    

    center = 0

    right = 0

    max_len = 0

    max_center = 0

    

    for i in range(m):

        # 计算初始半径

        if i < right:

            mirror = 2 * center - i

            P[i] = min(right - i, P[mirror])

        

        # 尝试扩展

        while i - P[i] - 1 >= 0 and i + P[i] + 1 < m and t[i - P[i] - 1] == t[i + P[i] + 1]:

            P[i] += 1

        

        # 更新中心和边界

        if i + P[i] > right:

            center = i

            right = i + P[i]

        

        # 更新最大

        if P[i] > max_len:

            max_len = P[i]

            max_center = i

    

    # 转换回原始字符串索引

    start = (max_center - max_len) // 2

    return start, start + (max_len - 1) + 1





def expand_around_center(s: str) -> Tuple[int, int]:

    """

    中心扩展法:O(n²)

    

    Args:

        s: 输入字符串

    

    Returns:

        (起始, 结束+1)

    """

    n = len(s)

    if n == 0:

        return 0, 0

    

    start, end = 0, 0

    

    for i in range(n):

        # 奇数长度回文

        l = r = i

        while l >= 0 and r < n and s[l] == s[r]:

            if r - l + 1 > end - start:

                start, end = l, r + 1

            l -= 1

            r += 1

        

        # 偶数长度回文

        l, r = i, i + 1

        while l >= 0 and r < n and s[l] == s[r]:

            if r - l + 1 > end - start:

                start, end = l, r + 1

            l -= 1

            r += 1

    

    return start, end





def all_palindromic_substrings(s: str) -> List[str]:

    """

    找出所有回文子串

    

    Args:

        s: 输入字符串

    

    Returns:

        所有回文子串列表

    """

    n = len(s)

    result = []

    

    for center in range(2 * n - 1):

        # 中心位置

        if center % 2 == 0:

            # 中心在字符上

            l = r = center // 2

        else:

            # 中心在间隙上

            l = center // 2

            r = l + 1

        

        while l >= 0 and r < n and s[l] == s[r]:

            result.append(s[l:r+1])

            l -= 1

            r += 1

    

    return result





def count_palindromic_substrings(s: str) -> int:

    """

    计算回文子串数量

    

    Args:

        s: 输入字符串

    

    Returns:

        回文子串数量

    """

    n = len(s)

    count = 0

    

    # 中心扩展

    for center in range(2 * n - 1):

        if center % 2 == 0:

            l = r = center // 2

        else:

            l = center // 2

            r = l + 1

        

        while l >= 0 and r < n and s[l] == s[r]:

            count += 1

            l -= 1

            r += 1

    

    return count





def is_palindrome(s: str, l: int, r: int) -> bool:

    """

    检查s[l:r]是否是回文

    

    Args:

        s: 字符串

        l: 起始

        r: 结束

    

    Returns:

        是否为回文

    """

    while l < r:

        if s[l] != s[r]:

            return False

        l += 1

        r -= 1

    return True





def shortest_palindromic_insertions(s: str) -> int:

    """

    计算最少需要插入多少字符才能变成回文

    

    Args:

        s: 输入字符串

    

    Returns:

        最少插入数

    """

    n = len(s)

    # 使用KMP思想找最长前缀后缀匹配

    # 实际上需要计算s和reverse(s)的最长公共前缀

    

    rev = s[::-1]

    

    # 找s的前缀和rev的后缀的最长匹配

    for i in range(n, 0, -1):

        if s[:i] == rev[n-i:]:

            return n - i

    

    return n - 1





# 测试代码

if __name__ == "__main__":

    # 测试1: Manacher算法

    print("测试1 - Manacher算法:")

    test_strings = ["babad", "cbbd", "a", "ac", "banana"]

    

    for s in test_strings:

        start, end = longest_palindrome_manacher(s)

        lps = s[start:end]

        print(f"  '{s}' -> 最长回文: '{lps}'")

    

    # 测试2: 中心扩展法对比

    print("\n测试2 - 中心扩展法:")

    s2 = "babad"

    start2, end2 = expand_around_center(s2)

    lps2 = s2[start2:end2]

    print(f"  '{s2}' -> 最长回文: '{lps2}'")

    

    # 测试3: 所有回文子串

    print("\n测试3 - 所有回文子串:")

    s3 = "aaa"

    pals = all_palindromic_substrings(s3)

    print(f"  '{s3}' 的回文子串: {pals}")

    print(f"  数量: {len(pals)}")

    

    # 测试4: 回文子串计数

    print("\n测试4 - 回文子串计数:")

    for s in ["abc", "aaa", "aba", "abacaba"]:

        count = count_palindromic_substrings(s)

        print(f"  '{s}' -> {count}个回文子串")

    

    # 测试5: 性能对比

    print("\n测试5 - 性能对比:")

    import time

    import random

    import string

    

    random.seed(42)

    s5 = ''.join(random.choices(string.ascii_lowercase, k=10000))

    

    start = time.time()

    manacher_result = longest_palindrome_manacher(s5)

    time_manacher = time.time() - start

    

    start = time.time()

    expand_result = expand_around_center(s5)

    time_expand = time.time() - start

    

    print(f"  字符串长度: {len(s5)}")

    print(f"  Manacher: {time_manacher:.4f}s")

    print(f"  中心扩展: {time_expand:.4f}s")

    print(f"  加速比: {time_expand/time_manacher:.1f}x")

    

    # 测试6: 最短插入变回文

    print("\n测试6 - 最短插入变回文:")

    for s in ["abc", "ab", "aab", "abcd"]:

        insertions = shortest_palindromic_insertions(s)

        print(f"  '{s}' 需要插入{insertions}个字符")

    

    # 测试7: 验证正确性

    print("\n测试7 - 验证正确性:")

    test_cases = [

        "babad",

        "cbbd",

        "a",

        "racecar",

        "forgeeksskeegfor",

    ]

    

    for s in test_cases:

        m_start, m_end = longest_palindrome_manacher(s)

        e_start, e_end = expand_around_center(s)

        

        m_lps = s[m_start:m_end]

        e_lps = s[e_start:e_end]

        

        print(f"  '{s}'")

        print(f"    Manacher: '{m_lps}' (长度{len(m_lps)})")

        print(f"    中心扩展: '{e_lps}' (长度{len(e_lps)})")

        print(f"    一致: {len(m_lps) == len(e_lps)}")

    

    print("\n所有测试完成!")

