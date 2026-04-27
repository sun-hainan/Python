# -*- coding: utf-8 -*-
"""
算法实现：软件工程算法 / Rabin_karp_rolling

本文件实现 Rabin_karp_rolling 相关的算法功能。
"""

from typing import List, Tuple, Optional


class RabinKarp:
    """
    Rabin-Karp 滚动哈希字符串匹配器

    使用多项式哈希：
        H(c_0, c_1, ..., c_{k-1}) = (c_0 * d^{k-1} + c_1 * d^{k-2} + ... + c_{k-1}) mod q
    滚动更新时利用 Horner 法则：
        H[i+1] = d * (H[i] - c_i * d^{k-1}) + c_{i+k}  mod q
    """

    def __init__(self, base: int = 256, mod: int = 10**9 + 9):
        # base: 进制基数（通常选质数，如 256 表示字节）
        self.base = base
        # mod: 模数（使用大质数减少碰撞）
        self.mod = mod
        # pow_base_k: 预计算的 base^{k-1} mod mod（用于哈希窗口快速更新）
        self.pow_base_k: int = 0

    def _precompute_powers(self, pattern_len: int):
        """预计算 base^{pattern_len-1} mod mod"""
        self.pow_base_k = 1
        for _ in range(pattern_len - 1):
            self.pow_base_k = (self.pow_base_k * self.base) % self.mod

    def _hash_str(self, s: str) -> int:
        """计算字符串 s 的多项式哈希"""
        h = 0
        for ch in s:
            h = (h * self.base + ord(ch)) % self.mod
        return h

    def _roll_hash(self, old_hash: int, old_char: str, new_char: str, window_len: int) -> int:
        """
        滚动更新哈希值

        H_new = (base * (H_old - old_char * base^{window_len-1}) + new_char) mod mod
        """
        # 移除最高位字符的贡献
        new_hash = (old_hash - ord(old_char) * self.pow_base_k) % self.mod
        # 左移并加上新字符
        new_hash = (new_hash * self.base + ord(new_char)) % self.mod
        # Python 负数取模修正
        new_hash = (new_hash + self.mod) % self.mod
        return new_hash

    def search(
        self, text: str, pattern: str, verify: bool = True
    ) -> List[int]:
        """
        在文本 text 中查找模式 pattern 的所有出现位置

        Args:
            text:    文本串
            pattern: 模式串
            verify:  哈希相等时是否用朴素比较验证（防止碰撞）

        Returns:
            模式在文本中出现的起始位置列表
        """
        n = len(text)
        m = len(pattern)

        if m == 0 or n < m:
            return []

        self._precompute_powers(m)

        # ---- 计算模式串和文本第一个窗口的哈希值 ----
        pattern_hash = self._hash_str(pattern)
        window_hash = self._hash_str(text[:m])

        matches: List[int] = []
        i = 0

        while i <= n - m:
            # ---- 哈希匹配检查 ----
            if window_hash == pattern_hash:
                # 哈希碰撞：使用朴素比较验证
                if not verify or all(text[i + j] == pattern[j] for j in range(m)):
                    matches.append(i)

            # ---- 滚动到下一个窗口 ----
            if i < n - m:
                window_hash = self._roll_hash(
                    window_hash,
                    text[i],
                    text[i + m],
                    m,
                )
            i += 1

        return matches


def rabin_karp_search(
    text: str, pattern: str, base: int = 256, mod: int = 10**9 + 9
) -> List[int]:
    """
    Rabin-Karp 搜索的简单封装函数
    """
    rk = RabinKarp(base=base, mod=mod)
    return rk.search(text, pattern)


def find_all_matches_kmp(text: str, pattern: str) -> List[int]:
    """
    作为对比：KMP 算法的实现（线性时间，不依赖哈希）
    KMP 找到模式串的前缀函数，避免重复匹配。
    """
    m = len(pattern)
    if m == 0:
        return [0]

    # ---- 构建 LPS（Longest Proper Prefix which is also Suffix）数组 ----
    lps = [0] * m
    length = 0  # 当前前缀匹配长度
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1

    # ---- 在文本中搜索 ----
    matches = []
    n = len(text)
    i = 0  # text 指针
    j = 0  # pattern 指针
    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1
            if j == m:
                matches.append(i - j)
                j = lps[j - 1]
        else:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1

    return matches


if __name__ == "__main__":
    print("=" * 50)
    print("Rabin-Karp 字符串匹配（滚动哈希）- 单元测试")
    print("=" * 50)

    test_cases = [
        ("ABABDABACDABABCABAB", "ABABCABAB"),
        ("Hello, World!", "World"),
        ("AAAAA", "AAA"),
        ("abcdefg", "xyz"),
        ("a" * 1000 + "b", "a" * 10 + "b"),
        ("The quick brown fox jumps over the lazy dog", "fox"),
        ("ABCABCABC", "ABC"),
    ]

    rk = RabinKarp(base=256, mod=10**9 + 9)

    print("\n测试用例:")
    for text, pattern in test_cases:
        matches = rk.search(text, pattern)
        print(f"\n  文本: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print(f"  模式: '{pattern}'")
        if matches:
            print(f"  匹配位置: {matches}")
            for pos in matches:
                print(f"    位置 {pos}: '{text[pos:pos+len(pattern)]}'")
        else:
            print(f"  无匹配")

    # 对比 KMP
    print("\n" + "=" * 40)
    print("与 KMP 算法对比（验证正确性）:")
    for text, pattern in test_cases[:4]:
        rk_matches = sorted(rk.search(text, pattern))
        kmp_matches = sorted(find_all_matches_kmp(text, pattern))
        match = "✓" if rk_matches == kmp_matches else "✗"
        print(f"  {match} RK: {rk_matches} | KMP: {kmp_matches}")

    # 性能测试
    import time

    print("\n性能测试（长文本）:")
    long_text = "ACGT" * 25000 + "ACGT"  # 100001 个字符
    long_pattern = "ACGT" * 10
    start = time.perf_counter()
    rk.search(long_text, long_pattern, verify=False)
    rk_time = time.perf_counter() - start
    start = time.perf_counter()
    find_all_matches_kmp(long_text, long_pattern)
    kmp_time = time.perf_counter() - start
    print(f"  文本长度: {len(long_text)}, 模式长度: {len(long_pattern)}")
    print(f"  Rabin-Karp: {rk_time*1000:.2f}ms")
    print(f"  KMP:         {kmp_time*1000:.2f}ms")

    print(f"\n复杂度: O(N + M) 平均时间，O(NM) 最坏（哈希碰撞）")
    print("算法完成。")
