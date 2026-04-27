# -*- coding: utf-8 -*-

"""

算法实现：生物信息学 / fm_index



本文件实现 fm_index 相关的算法功能。

"""



from collections import Counter





def bwt(s: str) -> str:

    """

    Burrows-Wheeler变换



    返回：最后一列

    """

    rotations = [s[i:] + s[:i] for i in range(len(s))]

    rotations.sort()

    return ''.join(r[-1] for r in rotations)





def inverse_bwt(bwt_str: str) -> str:

    """

    逆BWT变换



    参数：

        bwt_str: BWT变换后的字符串



    返回：原始字符串

    """

    n = len(bwt_str)



    # 计算每个字符的出现次数

    first_col = sorted(bwt_str)



    # 建立LF-mapping

    occ = {c: [] for c in set(bwt_str)}

    for i, c in enumerate(bwt_str):

        occ[c].append(i)



    # 重构

    result = []

    pos = 0

    for _ in range(n):

        c = first_col[pos]

        result.append(c)

        # 找到该字符的第next occurrences

        idx = occ[c].index(pos)

        pos = occ[c][idx] if idx < len(occ[c]) else occ[c][-1]



    return ''.join(reversed(result[:-1]))  # 最后一个是EOF标记





class FMIndex:

    """FM-Index全文索引"""



    def __init__(self, text: str):

        self.text = text + '$'

        self.sa = self._build_sa()

        self.bwt_str = bwt(self.text)



        # 采样SA（稀疏后缀数组）

        self.sa_sample_rate = 8

        self.sa_sampled = {i: self.sa[i] for i in range(0, len(self.text), self.sa_sample_rate)}



        # BWT中的计数

        self.C = {}

        self.Occ = {}

        self._build_index()



    def _build_sa(self):

        """构建后缀数组（简化版）"""

        n = len(self.text)

        sa = list(range(n))

        sa.sort(key=lambda x: self.text[x:])

        return sa



    def _build_index(self):

        """构建FM-Index"""

        # C[c] = c在字母表中排第几

        alphabet = sorted(set(self.bwt_str))

        rank = 0

        for c in alphabet:

            self.C[c] = rank

            rank += 1



        # Occ[c][i] = BWT[0:i]中c出现的次数

        for c in alphabet:

            self.Occ[c] = [0]

            count = 0

            for i, ch in enumerate(self.bwt_str):

                if ch == c:

                    count += 1

                self.Occ[c].append(count)



    def count(self, pattern: str) -> int:

        """

        统计pattern出现的次数



        时间：O(|pattern|)

        """

        lo, hi = 0, len(self.sa) - 1



        # 从右向左匹配

        for i in range(len(pattern) - 1, -1, -1):

            c = pattern[i]

            if c not in self.C:

                return 0



            lo = self.C[c] + self.Occ[c][lo] + 1

            hi = self.C[c] + self.Occ[c][hi]



            if lo > hi:

                return 0



        return hi - lo + 1





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== FM-Index测试 ===\n")



    text = "abracadabra"



    print(f"原文: {text}")



    # BWT

    bw = bwt(text)

    print(f"BWT: {bw}")



    # 逆BWT

    recovered = inverse_bwt(bw)

    print(f"逆BWT恢复: {recovered}")

    print(f"验证: {'✅ 正确' if recovered == text else '❌ 错误'}")



    # FM-Index

    print("\n--- FM-Index搜索 ---")

    fm = FMIndex(text)



    patterns = ["abra", "a", "br", "ca", "x"]

    for p in patterns:

        count = fm.count(p)

        print(f"  '{p}': 出现 {count} 次")



    print("\n说明：")

    print("  - BWT将相似字符聚集在一起")

    print("  - FM-Index支持O(m)搜索（m=模式长度）")

    print("  - BWA、Bowtie等基因组比对工具的核心")

