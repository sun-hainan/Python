# -*- coding: utf-8 -*-
"""
算法实现：信息检索 / page_rank

本文件实现 page_rank 相关的算法功能。
"""

from typing import Dict, List, Set
import random


class PageRank:
    """PageRank算法"""

    def __init__(self, damping: float = 0.85, max_iter: int = 100, tol: float = 1e-6):
        """
        参数：
            damping: 阻尼因子
            max_iter: 最大迭代次数
            tol: 收敛容忍度
        """
        self.damping = damping
        self.max_iter = max_iter
        self.tol = tol

        self.graph = {}  # page -> [outlinks]
        self.pages = set()
        self.ranks = {}

    def add_edge(self, from_page: str, to_page: str):
        """添加边 from_page -> to_page"""
        if from_page not in self.graph:
            self.graph[from_page] = set()
        self.graph[from_page].add(to_page)
        self.pages.add(from_page)
        self.pages.add(to_page)

    def compute(self) -> Dict[str, float]:
        """
        计算PageRank

        返回：{page: rank_score}
        """
        N = len(self.pages)
        if N == 0:
            return {}

        # 初始化
        self.ranks = {page: 1.0 / N for page in self.pages}

        # 迭代计算
        for iteration in range(self.max_iter):
            new_ranks = {}
            max_diff = 0.0

            for page in self.pages:
                rank_sum = 0.0

                # 找所有指向page的网页
                for prev_page, outlinks in self.graph.items():
                    if page in outlinks:
                        # page的rank按出链数分配
                        rank_sum += self.ranks[prev_page] / len(outlinks)

                # PageRank公式
                new_rank = (1 - self.damping) / N + self.damping * rank_sum
                new_ranks[page] = new_rank

                max_diff = max(max_diff, abs(new_rank - self.ranks[page]))

            self.ranks = new_ranks

            if max_diff < self.tol:
                print(f"  收敛于第{iteration+1}次迭代")
                break

        return self.ranks

    def top_k(self, k: int = 10) -> List[tuple]:
        """返回排名最高的k个网页"""
        sorted_ranks = sorted(self.ranks.items(), key=lambda x: x[1], reverse=True)
        return sorted_ranks[:k]


def power_iteration(adj_matrix: List[List[float]], d: float = 0.85,
                   max_iter: int = 100) -> List[float]:
    """
    幂迭代法计算PageRank（矩阵形式）

    参数：
        adj_matrix: 邻接矩阵
        d: 阻尼因子
    """
    n = len(adj_matrix)
    if n == 0:
        return []

    # 初始化
    ranks = [1.0 / n] * n

    for _ in range(max_iter):
        new_ranks = []
        for j in range(n):
            # 计算指向j的节点的贡献
            rank_sum = 0.0
            for i in range(n):
                if adj_matrix[i][j] > 0:
                    out_degree = sum(adj_matrix[i])
                    if out_degree > 0:
                        rank_sum += ranks[i] * adj_matrix[i][j] / out_degree

            new_rank = (1 - d) / n + d * rank_sum
            new_ranks.append(new_rank)

        ranks = new_ranks

    return ranks


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== PageRank测试 ===\n")

    # 创建简单网页图
    # A -> B, C
    # B -> C
    # C -> A
    # D -> C

    pr = PageRank(damping=0.85)

    pr.add_edge("A", "B")
    pr.add_edge("A", "C")
    pr.add_edge("B", "C")
    pr.add_edge("C", "A")
    pr.add_edge("D", "C")

    ranks = pr.compute()

    print("PageRank结果：")
    for page, rank in sorted(ranks.items(), key=lambda x: x[1], reverse=True):
        print(f"  {page}: {rank:.6f}")

    print("\n说明：")
    print("  - C被多个重要页面链接，rank较高")
    print("  - PageRank是Google搜索排名的核心算法之一")
    print("  - 现在有更多因素考虑（如主题敏感PageRank）")
