# -*- coding: utf-8 -*-
"""
算法实现：生物信息学 / blast_heuristic

本文件实现 blast_heuristic 相关的算法功能。
"""

from collections import defaultdict


class BLASTAligner:
    """BLAST启发式比对"""

    def __init__(self, word_size: int = 3, threshold: int = 11):
        """
        参数：
            word_size: k-mer大小（蛋白质通常3，DNA通常11）
            threshold: 词得分阈值
        """
        self.word_size = word_size
        self.threshold = threshold

        # 计分矩阵（简化BLOSUM62）
        self.match = 2
        self.mismatch = -1
        self.gap = -2

    def words_from_sequence(self, seq: str) -> list:
        """从序列提取所有k-mer"""
        return [seq[i:i+self.word_size] for i in range(len(seq) - self.word_size + 1)]

    def ungapped_extension(self, seq1: str, start1: int, seq2: str, start2: int) -> int:
        """无空位延伸，返回得分"""
        score = 0
        max_score = 0

        # 双向延伸
        # 正向
        i, j = start1, start2
        while i < len(seq1) and j < len(seq2):
            s = self.match if seq1[i] == seq2[j] else self.mismatch
            score += s
            max_score = max(max_score, score)
            i += 1
            j += 1

        return max_score

    def seed_and_extend(self, query: str, subject: str) -> list:
        """
        种子延伸策略

        返回：HSP列表 [(start1, end1, start2, end2, score), ...]
        """
        # 建立查询的词索引
        query_words = self.words_from_sequence(query)
        word_pos = defaultdict(list)
        for i, w in enumerate(query_words):
            word_pos[w].append(i)

        # 在目标序列中搜索匹配的词
        subject_words = self.words_from_sequence(subject)
        hits = []

        for j, w in enumerate(subject_words):
            if w in word_pos:
                for qi in word_pos[w]:
                    # 种子命中
                    score = self.ungapped_extension(query, qi, subject, j)
                    if score >= self.threshold:
                        hits.append((qi, j, score))

        # 合并重叠命中
        hits.sort()
        HSPs = []
        for start1, start2, score in hits:
            HSPs.append((start1, start1 + self.word_size,
                        start2, start2 + self.word_size,
                        score))

        return HSPs

    def compute_expect(self, score: float, query_len: int, subject_len: int) -> float:
        """
        计算E-value（期望值）

        E = K * m * n * e^(-lambda * S)
        """
        lambda_param = 0.318  # 简化
        K = 0.1
        m, n = query_len, subject_len
        return K * m * n * pow(2.718, -lambda_param * score)


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== BLAST启发式比对测试 ===\n")

    blast = BLASTAligner(word_size=3, threshold=6)

    query = "ACDEFGHIKLMP"
    subject = "XXXXXXXXACDEFGHIKLMPXXXXXXXX"

    print(f"查询: {query}")
    print(f"目标: {subject}")

    hsps = blast.seed_and_extend(query, subject)

    print(f"\n找到 {len(hsps)} 个HSP:")
    for start1, end1, start2, end2, score in hsps:
        print(f"  查询[{start1}:{end1}] vs 目标[{start2}:{end2}], 得分={score}")

    # E-value
    for start1, end1, start2, end2, score in hsps:
        evalue = blast.compute_expect(score, len(query), len(subject))
        print(f"  E-value: {evalue:.6f}")

    print("\n说明：")
    print("  - BLAST是生物信息学最常用的搜索工具")
    print("  - 启发式：用种子+延伸避免全矩阵计算")
    print("  - E-value < 0.001 通常认为显著")
