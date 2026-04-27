# -*- coding: utf-8 -*-

"""

算法实现：软件工程算法 / levenshtein_distance



本文件实现 levenshtein_distance 相关的算法功能。

"""



from typing import List





def levenshtein_distance(s: str, t: str) -> int:

    """

    计算两个字符串的 Levenshtein 编辑距离



    Args:

        s: 源字符串

        t: 目标字符串



    Returns:

        编辑距离（最小编辑操作数）



    算法：动态规划

        dp[i][j] = 将 s[:i] 转换为 t[:j] 的最小操作数



    递推公式：

        dp[i][j] = min(

            dp[i-1][j]   + 1,    # 删除 s[i-1]

            dp[i][j-1]   + 1,    # 插入 t[j-1]

            dp[i-1][j-1] + (0 if s[i-1] == t[j-1] else 1)  # 替换或不替换

        )



    Base cases:

        dp[0][j] = j (将空串变为 t[:j] 需要 j 次插入)

        dp[i][0] = i (将 s[:i] 变为空串需要 i 次删除)

    """

    n = len(s)

    m = len(t)



    # ---- 滚动数组优化：只需保存上一行和当前行 ----

    prev_row = list(range(m + 1))  # dp[0][*]，空串->t[:j] 需要 j 次插入



    for i in range(1, n + 1):

        # curr_row[0] = i（将 s[:i] 变为空串需要 i 次删除）

        curr_row = [i] + [0] * m



        for j in range(1, m + 1):

            if s[i - 1] == t[j - 1]:

                # 字符匹配，无需操作

                curr_row[j] = prev_row[j - 1]

            else:

                # 取三种操作的最小代价 + 1

                curr_row[j] = 1 + min(

                    prev_row[j],     # 删除 s[i-1]

                    curr_row[j - 1], # 插入 t[j-1]

                    prev_row[j - 1], # 替换 s[i-1] 为 t[j-1]

                )



        prev_row = curr_row  # 滚动：当前行成为下一轮的"上一行"



    return prev_row[m]





def levenshtein_with_backtrack(s: str, t: str) -> tuple[int, List[tuple]]:

    """

    计算编辑距离并回溯得到具体编辑操作序列



    Returns:

        (distance, operations)

        operations: List of ("insert"|"delete"|"replace", s_index, t_index, char)

    """

    n = len(s)

    m = len(t)



    # dp[i][j] = 编辑距离

    dp = [[0] * (m + 1) for _ in range(n + 1)]



    # Base cases

    for i in range(n + 1):

        dp[i][0] = i  # 删除操作

    for j in range(m + 1):

        dp[0][j] = j  # 插入操作



    # 填表

    for i in range(1, n + 1):

        for j in range(1, m + 1):

            if s[i - 1] == t[j - 1]:

                dp[i][j] = dp[i - 1][j - 1]

            else:

                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])



    # ---- 回溯 ----

    operations = []

    i, j = n, m

    while i > 0 or j > 0:

        if i > 0 and j > 0 and s[i - 1] == t[j - 1]:

            # 匹配，无需操作

            operations.append(("match", i - 1, j - 1, s[i - 1]))

            i -= 1

            j -= 1

        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:

            # 删除 s[i-1]

            operations.append(("delete", i - 1, j, s[i - 1]))

            i -= 1

        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:

            # 插入 t[j-1]

            operations.append(("insert", i, j - 1, t[j - 1]))

            j -= 1

        elif i > 0 and j > 0:

            # 替换

            operations.append(("replace", i - 1, j - 1, t[j - 1]))

            i -= 1

            j -= 1



    operations.reverse()

    return dp[n][m], operations





def damerau_levenshtein_distance(s: str, t: str) -> int:

    """

    Damerau-Levenshtein 距离（扩展版）：支持相邻字符的交换操作



    操作：插入、删除、替换、相邻交换（transposition）

    """

    n = len(s)

    m = len(t)

    dp = [[0] * (m + 1) for _ in range(n + 1)]



    for i in range(n + 1):

        dp[i][0] = i

    for j in range(m + 1):

        dp[0][j] = j



    for i in range(1, n + 1):

        for j in range(1, m + 1):

            cost = 0 if s[i - 1] == t[j - 1] else 1

            dp[i][j] = min(

                dp[i - 1][j] + 1,      # 删除

                dp[i][j - 1] + 1,      # 插入

                dp[i - 1][j - 1] + cost,  # 替换

            )

            # 相邻字符交换（仅当 i>1 and j>1）

            if (

                i > 1

                and j > 1

                and s[i - 1] == t[j - 2]

                and s[i - 2] == t[j - 1]

            ):

                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + cost)



    return dp[n][m]





if __name__ == "__main__":

    print("=" * 50)

    print("Levenshtein 编辑距离 - 单元测试")

    print("=" * 50)



    test_cases = [

        ("hello", "hello"),       # 0

        ("", "abc"),               # 3（插入）

        ("abc", ""),               # 3（删除）

        ("kitten", "sitting"),     # 3 (k→s, e→i, +g)

        ("saturday", "sunday"),    # 3

        ("flaw", "lawn"),          # 2

        ("abc", "yabd"),           # 2

        ("abc", "abc"),            # 0

    ]



    print("\n测试用例:")

    all_passed = True

    for s, t in test_cases:

        dist = levenshtein_distance(s, t)

        print(f"  '{s}' -> '{t}': 距离 = {dist}")



    # 带回溯的测试

    print("\n带回溯编辑路径:")

    s, t = "kitten", "sitting"

    dist, ops = levenshtein_with_backtrack(s, t)

    print(f"  '{s}' -> '{t}': 距离 = {dist}")

    for op_type, si, ti, char in ops:

        print(f"    {op_type:8s}: pos({si},{ti}) char='{char}'")



    # Damerau-Levenshtein 测试

    print("\nDamerau-Levenshtein（支持相邻交换）:")

    da_tests = [

        ("ab", "ba"),    # 交换1次

        ("abc", "acb"),  # 交换1次

        ("abcd", "abdc"),

    ]

    for s, t in da_tests:

        dist = damerau_levenshtein_distance(s, t)

        print(f"  '{s}' -> '{t}': DL 距离 = {dist}")



    print(f"\n复杂度: O(N * M) 时间, O(min(N, M)) 空间（标准版）")

    print("算法完成。")

