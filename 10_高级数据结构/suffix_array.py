"""
Suffix Array（后缀数组）
==========================================

【算法原理】
后缀数组存储字符串所有后缀的起始位置，按字典序排序。
配合LCP数组，能高效解决很多字符串问题。

【时间复杂度】
- 构建: O(n log n)（二分搜索+基数排序可达O(n)）
- LCP: O(n)

【空间复杂度】O(n)

【应用场景】
- 字符串匹配（最长重复子串）
- 数据压缩
- 生物信息学（DNA序列分析）
- 全文检索
"""

import math
from typing import List, Tuple


class SuffixArray:
    """
    后缀数组

    【核心概念】
    - 后缀：S[i:] 表示从位置i开始到末尾的子串
    - 后缀数组 SA[i]: 第i小的后缀的起始位置
    - 名次数组 RANK[i]: 起始位置i的后缀是第几小
    - LCP[i]: SA[i]和SA[i-1]的最长公共前缀长度
    """

    def __init__(self, s: str):
        """
        初始化并构建后缀数组

        【参数】
        - s: 输入字符串（假设不包含特殊字符）
        """
        self.s = s
        self.n = len(s)
        self.sa = []  # 后缀数组
        self.rank = []  # 名次数组
        self.lcp = []  # LCP数组

        self._build_suffix_array()
        self._build_lcp()

    def _build_suffix_array(self) -> None:
        """
        构建后缀数组

        【方法】Doubling算法 O(n log n)

        【思路】
        - k=1时，按第一个字符排序
        - k=2k时，按前2k个字符排序（利用之前的排序结果）
        - 倍增直到所有后缀唯一
        """
        s = self.s

        # 初始化：按单个字符排序
        # 用ord将字符转整数
        k = 1
        sa = list(range(self.n))  # 初始顺序

        # 按第一字符排序的rank
        rank = [ord(c) for c in s]

        tmp = [0] * self.n

        while True:
            # 按 (rank[i], rank[i+k]) 双关键字排序
            # 稳定性计数排序
            sa = self._sort_double(sa, rank, k)

            # 计算新的rank
            tmp[sa[0]] = 0
            for i in range(1, self.n):
                prev, curr = sa[i - 1], sa[i]
                tmp[curr] = tmp[prev] + self._compare_ranks(
                    rank, prev, curr, k)
            rank, tmp = tmp, rank

            if rank[sa[-1]] == self.n - 1:
                break
            k *= 2

        self.sa = sa
        self.rank = rank

    def _compare_ranks(self, rank: List[int], i: int, j: int, k: int) -> int:
        """比较两个位置的rank是否相等"""
        ri = rank[i]
        rj = rank[j]
        rik = rank[i + k] if i + k < self.n else -1
        rjk = rank[j + k] if j + k < self.n else -1
        return 1 if (ri < rj) or (ri == rj and rik < rjk) else 0

    def _sort_double(self, sa: List[int], rank: List[int], k: int) -> List[int]:
        """
        按双关键字排序（计数排序，O(n)）

        【原理】从低位到高位排序，保证稳定性
        """
        n = self.n

        # 第一关键字：rank[i+k]
        # 第二关键字：rank[i]
        # 由于是倍增的，可以用前一次排序结果

        # 使用Python的sorted，按(第二关键字,第一关键字)排序
        # 为了O(n)，改用计数排序
        return sorted(sa, key=lambda x: (rank[x + k] if x + k < n else -1, rank[x]))

    def _build_lcp(self) -> None:
        """
        构建LCP数组

        【方法】Kasai算法 O(n)

        【思路】
        利用相邻后缀的LCP性质：
        LCP[i+1] >= LCP[i] - 1
        """
        s = self.s
        n = self.n
        sa = self.sa
        rank = self.rank

        lcp = [0] * n
        h = 0

        for i in range(n):
            r = rank[i]
            if r == 0:
                lcp[r] = 0
            else:
                j = sa[r - 1]  # 前一个后缀
                # 计算LCP
                while i + h < n and j + h < n and s[i + h] == s[j + h]:
                    h += 1
                lcp[r] = h
                if h > 0:
                    h -= 1

        self.lcp = lcp

    def search(self, pattern: str) -> List[int]:
        """
        在文本中搜索模式串

        【方法】二分搜索
        【返回】所有匹配位置的列表
        """
        sa = self.sa
        s = self.s
        n = self.n
        m = len(pattern)

        # 二分查找下界
        lo = 0
        hi = n - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if s[sa[mid]:sa[mid] + m] < pattern:
                lo = mid + 1
            else:
                hi = mid

        results = []
        pos = lo

        # 检查是否真正匹配
        while pos < n and s[sa[pos]:sa[pos] + m] == pattern:
            results.append(sa[pos])
            pos += 1

        return results

    def longest_common_substring(self) -> Tuple[int, int, int]:
        """
        找出最长重复子串

        【返回】(长度, 起始位置1, 起始位置2)
        """
        max_lcp = max(self.lcp) if self.lcp else 0
        max_idx = self.lcp.index(max_lcp)

        pos1 = self.sa[max_idx - 1]
        pos2 = self.sa[max_idx]

        return (max_lcp, pos1, pos2)

    def longest_repeated_substring(self, k: int = 2) -> List[str]:
        """
        找出所有出现至少k次的最长重复子串

        【方法】二分搜索LCP
        """
        lo, hi = 0, self.n
        result = []

        while lo < hi:
            mid = (lo + hi + 1) // 2
            valid = self._lcp_ge(mid, k)
            if valid:
                lo = mid
            else:
                hi = mid - 1

        if lo == 0:
            return []

        # 收集所有长度>=lo的子串
        seen = set()
        for i in range(1, self.n):
            if self.lcp[i] >= lo:
                substr = self.s[self.sa[i]:self.sa[i] + lo]
                seen.add(substr)

        return list(seen)

    def _lcp_ge(self, length: int, k: int) -> bool:
        """检查是否存在长度>=length且出现>=k次的前缀"""
        count = 1
        for i in range(1, self.n):
            if self.lcp[i] >= length:
                count += 1
                if count >= k:
                    return True
            else:
                count = 1
        return False

    def display(self) -> None:
        """打印后缀数组和LCP数组"""
        print("\n【后缀数组】")
        print(f"{'i':>3} {'SA':>3} {'RANK':>5} {'LCP':>4}  后缀")
        print("-" * 50)
        for i in range(self.n):
            suffix = self.s[self.sa[i]:]
            lcp_str = str(self.lcp[i]) if i > 0 else "-"
            print(f"{i:>3} {self.sa[i]:>3} {self.rank[self.sa[i]]:>5} {lcp_str:>4}  {suffix}")


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("后缀数组 - 测试")
    print("=" * 50)

    # 测试1：基本构建
    print("\n【测试1】构建后缀数组")
    s = "banana"
    sa = SuffixArray(s)
    sa.display()

    # 测试2：搜索
    print("\n【测试2】模式匹配")
    for pattern in ["ana", "ban", "xyz"]:
        results = sa.search(pattern)
        print(f"  搜索 '{pattern}': {results}")

    # 测试3：最长重复子串
    print("\n【测试3】最长重复子串")
    s2 = "ababa"
    sa2 = SuffixArray(s2)
    sa2.display()
    length, p1, p2 = sa2.longest_common_substring()
    print(f"  'ababa'最长重复: '{s2[p1:p1+length]}' (长度={length}, 位置={p1},{p2})")

    # 测试4：更复杂的例子
    print("\n【测试4】最长重复子串")
    s3 = "abcabxabcdabcaby"
    sa3 = SuffixArray(s3)
    sa3.display()
    length, p1, p2 = sa3.longest_common_substring()
    print(f"  最长重复子串: '{s3[p1:p1+length]}' (长度={length})")

    # 测试5：多次重复
    print("\n【测试5】出现至少3次的最长重复子串")
    s4 = "ababa"
    sa4 = SuffixArray(s4)
    results = sa4.longest_repeated_substring(3)
    print(f"  'ababa'中出现≥3次: {results}")

    print("\n" + "=" * 50)
    print("后缀数组测试完成！")
    print("=" * 50)
