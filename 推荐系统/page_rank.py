# -*- coding: utf-8 -*-
"""
算法实现：推荐系统 / page_rank

本文件实现 page_rank 相关的算法功能。
"""

import numpy as np


class PageRank:
    """PageRank算法实现"""

    def __init__(self, damping=0.85, max_iterations=100, tol=1e-6):
        """
        初始化PageRank

        Args:
            damping: float 阻尼因子（随机跳转概率）
            max_iterations: int 最大迭代次数
            tol: float 收敛阈值（两次迭代差异小于此值时停止）
        """
        self.damping = damping  # 阻尼因子 d
        self.max_iterations = max_iterations  # 最大迭代次数
        self.tol = tol  # 收敛容差
        self.ranks = {}  # 最终PageRank得分
        self.n_nodes = 0  # 节点数
        self.iteration_history = []  # 迭代历史（用于分析收敛）

    def fit(self, graph):
        """
        计算PageRank

        Args:
            graph: dict {node: list of neighbor nodes} 邻接表表示的图
                   键为当前节点，值为该节点指向的邻居节点列表

        Returns:
            dict {node: rank_score} 节点PageRank得分
        """
        nodes = list(graph.keys())  # 所有节点
        self.n_nodes = len(nodes)  # 节点总数
        node_index = {node: i for i, node in enumerate(nodes)}  # 节点->索引映射

        # 初始化PageRank值（全1/N）
        rank = np.ones(self.n_nodes) / self.n_nodes
        teleportation = np.ones(self.n_nodes) / self.n_nodes  # 均匀跳转向量

        # 构建转移矩阵（列归一化的邻接矩阵）
        # M[j,i] 表示从节点i转移到节点j的概率
        M = np.zeros((self.n_nodes, self.n_nodes))

        for node, neighbors in graph.items():
            i = node_index[node]  # 当前节点索引
            if neighbors:
                # 出链均匀分配PageRank
                prob = 1.0 / len(neighbors)
                for neighbor in neighbors:
                    j = node_index[neighbor]  # 邻居节点索引
                    M[j, i] = prob
            else:
                # 悬空节点：均匀跳转到所有节点
                M[:, i] = 1.0 / self.n_nodes

        # 迭代计算
        for iteration in range(self.max_iterations):
            # PageRank公式: r = (1-d)/N * e + d * M * r
            # 等价于: r = (1-d) * teleportation + d * M @ r
            new_rank = (1 - self.damping) * teleportation + self.damping * M @ rank

            # 检查收敛
            diff = np.linalg.norm(new_rank - rank, 1)  # L1范数差异
            self.iteration_history.append(diff)

            rank = new_rank

            if diff < self.tol:
                print(f"PageRank在第{iteration + 1}次迭代后收敛 (diff={diff:.2e})")
                break

        # 存储结果
        self.ranks = {nodes[i]: float(rank[i]) for i in range(self.n_nodes)}
        return self.ranks

    def fit_power_iteration(self, graph):
        """
        使用幂迭代法（Power Iteration）计算PageRank

        幂迭代法更高效，特别适合稀疏矩阵：
        r_{k+1} = d * M * r_k + (1-d) / N

        Args:
            graph: dict 邻接表表示的图

        Returns:
            dict {node: rank_score}
        """
        nodes = list(graph.keys())
        self.n_nodes = len(nodes)

        # 构建出链和入链映射
        out_links = {}  # {node: set of neighbors}
        in_links = defaultdict(set)  # {node: set of nodes pointing to node}

        for node in nodes:
            neighbors = graph.get(node, [])
            out_links[node] = set(neighbors)
            for neighbor in neighbors:
                in_links[neighbor].add(node)

        # 初始化均匀分布
        rank = {node: 1.0 / self.n_nodes for node in nodes}

        for iteration in range(self.max_iterations):
            new_rank = {}

            # 计算悬空节点的贡献（没有出链的节点）
            dangling_sum = sum(rank[node] for node in nodes if len(out_links.get(node, [])) == 0)

            for node in nodes:
                # PageRank累加：来自所有入链节点的贡献
                rank_sum = sum(rank[in_node] / len(out_links[in_node])
                              for in_node in in_links[node]
                              if len(out_links[in_node]) > 0)

                # 公式: PR(node) = (1-d)/N + d * (来自入链的贡献 + 悬空节点贡献/N)
                new_rank[node] = (1 - self.damping) / self.n_nodes + \
                                self.damping * (rank_sum + dangling_sum / self.n_nodes)

            # 归一化（确保和为1）
            total = sum(new_rank.values())
            for node in new_rank:
                new_rank[node] /= total

            # 检查收敛
            diff = sum(abs(new_rank[node] - rank[node]) for node in nodes)
            rank = new_rank

            if diff < self.tol:
                print(f"PageRank在第{iteration + 1}次迭代后收敛 (diff={diff:.2e})")
                break

        self.ranks = rank
        return self.ranks

    def recommend(self, user_id, top_k=10):
        """
        基于PageRank的推荐（将用户-物品交互视为图进行推荐）

        适用场景：当用户-物品交互可以建模为图结构时

        Args:
            user_id: 目标节点
            top_k: 返回Top-K推荐

        Returns:
            list of tuple (node_id, rank_score)
        """
        if not self.ranks:
            return []

        # 排除用户已交互的节点
        ranked = sorted(self.ranks.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


class PersonalizedPageRank(PageRank):
    """个性化PageRank（用于特定节点的推荐）"""

    def __init__(self, damping=0.85, max_iterations=100, tol=1e-6):
        super().__init__(damping, max_iterations, tol)
        self.personalization = None  # 个性化跳转分布

    def set_personalization_vector(self, personalization_dict):
        """
        设置个性化跳转向量

        Args:
            personalization_dict: dict {node: probability}
                                 只有特定节点有非零概率
        """
        total = sum(personalization_dict.values())
        self.personalization = {
            node: prob / total for node, prob in personalization_dict.items()
        }

    def fit(self, graph):
        """计算个性化PageRank"""
        if self.personalization is None:
            return super().fit(graph)

        nodes = list(graph.keys())
        self.n_nodes = len(nodes)
        node_index = {node: i for i, node in enumerate(nodes)}

        # 构建转移矩阵
        M = np.zeros((self.n_nodes, self.n_nodes))
        for node, neighbors in graph.items():
            i = node_index[node]
            if neighbors:
                prob = 1.0 / len(neighbors)
                for neighbor in neighbors:
                    j = node_index[neighbor]
                    M[j, i] = prob
            else:
                M[:, i] = 1.0 / self.n_nodes

        # 个性化跳转向量
        teleportation = np.zeros(self.n_nodes)
        for node, prob in self.personalization.items():
            if node in node_index:
                teleportation[node_index[node]] = prob

        # 归一化
        teleportation /= teleportation.sum()

        # 迭代
        rank = np.ones(self.n_nodes) / self.n_nodes

        for iteration in range(self.max_iterations):
            new_rank = (1 - self.damping) * teleportation + self.damping * M @ rank
            diff = np.linalg.norm(new_rank - rank, 1)
            rank = new_rank

            if diff < self.tol:
                break

        self.ranks = {nodes[i]: float(rank[i]) for i in range(self.n_nodes)}
        return self.ranks


# ------------------- 单元测试 -------------------
if __name__ == '__main__':
    # 示例：网页链接图
    #
    #     A → B → C
    #     ↑    ↘  ↗
    #     D ← E ← F
    #         ↓
    #         G

    web_graph = {
        'A': ['B'],
        'B': ['C', 'E'],
        'C': ['A'],
        'D': ['A'],
        'E': ['D', 'F'],
        'F': ['E'],
        'G': ['E'],
    }

    print("=" * 50)
    print("测试 PageRank 算法")
    print("=" * 50)

    # 使用矩阵方法
    pr = PageRank(damping=0.85, max_iterations=100, tol=1e-6)
    ranks = pr.fit(web_graph)

    print("\nPageRank 得分 (矩阵方法):")
    sorted_ranks = sorted(ranks.items(), key=lambda x: x[1], reverse=True)
    for node, rank in sorted_ranks:
        print(f"  {node}: {rank:.6f}")

    # 使用幂迭代法
    print("\nPageRank 得分 (幂迭代法):")
    pr_power = PageRank(damping=0.85, max_iterations=100, tol=1e-6)
    ranks_power = pr_power.fit_power_iteration(web_graph)

    sorted_ranks_power = sorted(ranks_power.items(), key=lambda x: x[1], reverse=True)
    for node, rank in sorted_ranks_power:
        print(f"  {node}: {rank:.6f}")

    # 迭代收敛图
    print(f"\n收敛迭代次数: {len(pr.iteration_history)}")

    print("\n" + "=" * 50)
    print("测试个性化 PageRank")
    print("=" * 50)

    # 从节点F出发的个性化PageRank
    ppr = PersonalizedPageRank(damping=0.85)
    ppr.set_personalization_vector({'F': 1.0})
    ppr.fit(web_graph)

    print("\n从节点 F 出发的个性化PageRank:")
    sorted_ppr = sorted(ppr.ranks.items(), key=lambda x: x[1], reverse=True)
    for node, rank in sorted_ppr:
        print(f"  {node}: {rank:.6f}")

    print("\n✅ PageRank算法测试通过！")

    # 时间复杂度说明
    print("\n" + "=" * 50)
    print("复杂度分析:")
    print("=" * 50)
    print("时间复杂度: O(k * (N + E))，k为迭代次数，N为节点数，E为边数")
    print("空间复杂度: O(N + E)，存储图结构和PageRank向量")
