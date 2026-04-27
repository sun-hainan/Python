# -*- coding: utf-8 -*-

"""

算法实现：生物信息学 / suffix_array



本文件实现 suffix_array 相关的算法功能。

"""



from typing import List





def build_suffix_array_sa(s: str) -> List[int]:

    """

    使用简单排序构建后缀数组（O(n² log n)）



    参数：

        s: 输入字符串



    返回：后缀数组 SA[i] = 排名第i的后缀起始位置

    """

    n = len(s)

    sa = list(range(n))



    # 比较函数：按字典序比较后缀

    def cmp(i, j):

        while i < n and j < n:

            if s[i] < s[j]:

                return -1

            elif s[i] > s[j]:

                return 1

            i += 1

            j += 1

        return 0



    sa.sort(key=lambda x: (s[x], s[x+1] if x+1 < n else ''))



    return sa





def build_suffix_array_double(s: str) -> List[int]:

    """

    倍增法构建后缀数组（O(n log n)）



    参数：

        s: 输入字符串（通常加一个特殊字符）



    返回：后缀数组

    """

    n = len(s)

    sa = list(range(n))

    rank = [ord(c) for c in s]



    k = 1

    while k < n:

        # 按 (rank[i], rank[i+k]) 排序

        sa.sort(key=lambda x: (rank[x], rank[x+k] if x+k < n else -1))



        # 计算新的rank

        tmp = [0] * n

        tmp[sa[0]] = 0

        for i in range(1, n):

            prev, curr = sa[i-1], sa[i]

            if (rank[prev], rank[prev+k] if prev+k < n else -1) != \

               (rank[curr], rank[curr+k] if curr+k < n else -1):

                tmp[curr] = tmp[prev] + 1

            else:

                tmp[curr] = tmp[prev]



        rank = tmp

        if rank[sa[-1]] == n - 1:

            break

        k *= 2



    return sa





def lcp_array(s: str, sa: List[int]) -> List[int]:

    """

    构建LCP数组（最长公共前缀）



    LCP[i] = SA[i]和SA[i-1]的最长公共前缀长度



    参数：

        s: 输入字符串

        sa: 后缀数组



    返回：LCP数组

    """

    n = len(s)

    rank = [0] * n

    for i in range(n):

        rank[sa[i]] = i



    lcp = [0] * n

    h = 0

    for i in range(n):

        r = rank[i]

        if r > 0:

            j = sa[r - 1]

            while i + h < n and j + h < n and s[i+h] == s[j+h]:

                h += 1

            lcp[r] = h

            if h > 0:

                h -= 1



    return lcp





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 后缀数组测试 ===\n")



    s = "banana"



    print(f"字符串: {s}")

    print(f"后缀:")

    for i, suffix in enumerate(s):

        print(f"  {i}: {s[i:]}")



    # 构建

    sa = build_suffix_array_double(s)

    print(f"\n后缀数组: {sa}")



    print(f"\n排序后的后缀:")

    for rank, pos in enumerate(sa):

        print(f"  排名{rank}: pos={pos}, suffix='{s[pos:]}'")



    # LCP

    lcp = lcp_array(s, sa)

    print(f"\nLCP数组: {lcp}")



    print("\n应用：")

    print("  - 字符串搜索（O(log n)）")

    print("  - 最长重复子串")

    print("  - 最长公共子串")

    print("  - 基因组比对（BWT/ FM-Index）")

