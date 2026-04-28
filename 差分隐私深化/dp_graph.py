"""
图数据差分隐私 (Differential Privacy for Graph Data)
===================================================

算法原理:
---------
图数据（如社交网络、通信网络、交通网络）包含丰富的结构化信息，
节点代表实体，边代表实体间的关系。图数据的差分隐私保护面临独特挑战：

1. 边扰动（Edge Perturbation）：
   - 对每条边的存在性进行随机化扰动
   - 保持图的结构特性同时保护个体关系隐私

2. 节点扰动（Node Perturbation）：
   - 对节点属性或身份进行扰动
   - 用于保护节点敏感属性

3. 图匹配（Graph Matching）：
   - 防止攻击者通过结构特征识别图中的节点
   - 通过随机化图结构增加匹配难度

4. 度分布保护（Degree Distribution Protection）：
   - 保护节点的度（连接数）不被推断
   - 度信息可能泄露敏感关系

核心技术：
- 边敏感性：添加/移除单条边的最大影响
- 图谱方法：使用图的谱（特征值）进行扰动
- 随机化响应：边级别的概率扰动

时间复杂度: O(n + m + k * n^2) 其中n为节点数，m为边数，k为迭代次数
空间复杂度: O(n^2) 用于存储邻接矩阵或谱信息

应用场景:
--------
- 社交网络隐私：发布图结构时不泄露用户关系
- 通信网络分析：保护通信双方的关系隐私
- 交通网络发布：共享交通数据同时保护出行隐私
- 蛋白质相互作用网络：研究蛋白质关系同时保护敏感发现
"""

import numpy as np
from numpy.random import Laplace, geometric, binomial


def build_adjacency_matrix(edges, n_nodes, directed=False):
    """
    从边列表构建邻接矩阵
    
    参数:
        edges: 边列表，格式为[(u, v), ...] 或 [(u, v, weight), ...]
        n_nodes: 节点数量
        directed: 是否为有向图
    
    返回:
        adj_matrix: 邻接矩阵
        weights: 权重矩阵（如果有权重）
    """
    # 初始化邻接矩阵
    adj_matrix = np.zeros((n_nodes, n_nodes), dtype=np.float64)
    weights = None
    
    for edge in edges:
        u, v = edge[0], edge[1]
        weight = edge[2] if len(edge) > 2 else 1.0
        
        # 添加边（无向图：双向；有向图：单向）
        adj_matrix[u, v] = weight
        if not directed:
            adj_matrix[v, u] = weight
    
    return adj_matrix, weights


def edge_perturbation_dp(adj_matrix, epsilon=1.0, directed=False):
    """
    边扰动差分隐私机制
    
    原理：对图的每条边进行独立的随机化扰动，
    以指定概率添加/删除边，同时保持图的宏观结构特性
    
    参数:
        adj_matrix: 邻接矩阵
        epsilon: 隐私预算
        directed: 是否为有向图
    
    返回:
        perturbed_matrix: 扰动后的邻接矩阵
    """
    n = adj_matrix.shape[0]  # 节点数
    perturbed = adj_matrix.copy()  # 创建副本避免修改原矩阵
    
    # 边扰动的敏感性：每条边存在与否最多影响1
    # 对于无向图，扰动概率为 p = e^epsilon / (e^epsilon + 1)
    # 这实现了纯差分隐私的边扰动
    p_add = np.exp(epsilon) / (np.exp(epsilon) + 1)
    
    # 遍历上三角矩阵（避免重复处理无向图的边）
    upper_tri_indices = np.triu_indices(n, k=1)
    
    for i, j in zip(upper_tri_indices[0], upper_tri_indices[1]):
        original_edge = adj_matrix[i, j] > 0
        
        # 以一定概率翻转边的存在性
        if original_edge:
            # 边存在时，以概率 (e^epsilon + 1)/2(e^epsilon + 1) 保持存在
            # 简化：使用独立的概率决定是否删除
            delete_prob = 1 / (np.exp(epsilon) + 1)
            if np.random.random() < delete_prob:
                perturbed[i, j] = 0
                if not directed:
                    perturbed[j, i] = 0
        else:
            # 边不存在时，以概率添加
            add_prob = np.exp(epsilon) / (np.exp(epsilon) + 1)
            if np.random.random() < add_prob:
                perturbed[i, j] = 1
                if not directed:
                    perturbed[j, i] = 1
    
    return perturbed


def node_perturbation_by_degree(adj_matrix, epsilon=1.0):
    """
    基于节点度的差分隐私扰动
    
    原理：节点的度（邻居数量）是敏感的全局信息，
    通过向每个节点的度添加Laplace噪声来保护度分布
    
    参数:
        adj_matrix: 邻接矩阵
        epsilon: 隐私预算
    
    返回:
        noisy_degrees: 添加噪声后的节点度
        perturbed_matrix: 扰动后的邻接矩阵
    """
    n = adj_matrix.shape[0]
    
    # 计算原始度
    original_degrees = np.sum(adj_matrix > 0, axis=1).astype(float)
    
    # 度的敏感性为1（添加/删除一条边最多改变一个节点的度）
    sensitivity = 1.0
    
    # 添加Laplace噪声
    scale = sensitivity / epsilon
    noisy_degrees = original_degrees + Laplace(scale=scale, size=n)
    
    # 确保度非负且为整数
    noisy_degrees = np.maximum(noisy_degrees, 0).astype(int)
    
    # 创建扰动后的图（根据带噪声的度）
    perturbed = np.zeros_like(adj_matrix)
    for i in range(n):
        target_degree = noisy_degrees[i]
        if target_degree > 0:
            # 随机选择target_degree个邻居
            possible_neighbors = list(range(n))
            possible_neighbors.remove(i)  # 不自连
            neighbors = np.random.choice(possible_neighbors, 
                                         size=min(target_degree, n-1), 
                                         replace=False)
            for j in neighbors:
                perturbed[i, j] = 1
    
    return noisy_degrees, perturbed


def degree_distribution_protection(adj_matrix, epsilon=1.0):
    """
    度分布保护机制
    
    原理：通过指数机制选择度值，或者使用Report Noisy Max技术
    确保发布的度分布满足差分隐私，同时尽量保持效用
    
    参数:
        adj_matrix: 邻接矩阵
        epsilon: 隐私预算
    
    返回:
        released_degrees: 隐私保护的度序列
    """
    n = adj_matrix.shape[0]
    
    # 计算原始度
    original_degrees = np.sum(adj_matrix > 0, axis=1)
    
    # 使用Laplace机制发布度分布
    # 敏感性为1（单个节点最多影响一条边）
    sensitivity = 1.0
    scale = sensitivity / epsilon
    
    # 对每个度添加独立噪声
    noisy_degrees = original_degrees + Laplace(scale=scale, size=n)
    
    # 将噪声度转换为非负整数
    released_degrees = np.maximum(np.round(noisy_degrees), 0).astype(int)
    
    # 如果需要，可以添加更多后处理步骤确保度序列的有效性
    # 例如：确保度序列可以形成简单图
    
    return released_degrees


def graph_spectral_perturbation(adj_matrix, epsilon=1.0, n_eigenvalues=5):
    """
    图谱扰动差分隐私
    
    原理：图的谱（邻接矩阵的特征值）包含了图的全局结构信息，
    通过向特征值添加噪声并重构图来发布差分隐私图
    
    参数:
        adj_matrix: 邻接矩阵
        epsilon: 隐私预算
        n_eigenvalues: 用于重构的特征值数量
    
    返回:
        perturbed_matrix: 基于扰动谱的重构图
    """
    n = adj_matrix.shape[0]
    
    # 计算原始特征值和特征向量
    eigenvalues, eigenvectors = np.linalg.eigh(adj_matrix)
    
    # 对特征值添加Laplace噪声
    # 特征值的敏感性取决于图的结构，这里使用简化的敏感性估计
    sensitivity = 2.0 * np.max(np.abs(eigenvalues)) / n
    scale = sensitivity / epsilon
    
    noisy_eigenvalues = eigenvalues + Laplace(scale=scale, size=n)
    
    # 保持特征值的对称性（对于实对称矩阵，特征值应为实数）
    noisy_eigenvalues = np.real(noisy_eigenvalues)
    
    # 使用扰动后的特征值和原始特征向量重构矩阵
    reconstructed = eigenvectors @ np.diag(noisy_eigenvalues) @ eigenvectors.T
    
    # 将负值设为0（邻接矩阵应为非负）
    reconstructed = np.maximum(reconstructed, 0)
    
    # 二值化：大于阈值的视为有边
    threshold = np.median(reconstructed)
    perturbed_matrix = (reconstructed > threshold).astype(float)
    
    return perturbed_matrix


def graph_matching_defense(adj_matrix, epsilon=1.0):
    """
    图匹配防御机制
    
    原理：通过随机化图结构使得攻击者难以通过节点度、
    局部子图结构等特征进行节点身份匹配
    
    参数:
        adj_matrix: 邻接矩阵
        epsilon: 隐私预算
    
    返回:
        perturbed_matrix: 扰动后的图
        num_changes: 改变的边数
    """
    n = adj_matrix.shape[0]
    perturbed = adj_matrix.copy()
    
    # 跟踪改变的边数
    num_changes = 0
    
    # 遍历所有边对
    upper_tri_indices = np.triu_indices(n, k=1)
    
    for i, j in zip(upper_tri_indices[0], upper_tri_indices[1]):
        # 边扰动概率
        p_flip = 1 / (np.exp(epsilon) + 1)
        
        if np.random.random() < p_flip:
            # 翻转边状态
            if perturbed[i, j] > 0:
                perturbed[i, j] = 0
                perturbed[j, i] = 0
            else:
                perturbed[i, j] = 1
                perturbed[j, i] = 1
            num_changes += 1
    
    return perturbed, num_changes


def local_structure_privacy(adj_matrix, node, epsilon=1.0):
    """
    局部结构隐私保护
    
    原理：保护单个节点的邻居子图结构，
    通过随机化邻居集合来防止精确推断
    
    参数:
        adj_matrix: 邻接矩阵
        node: 目标节点索引
        epsilon: 隐私预算
    
    返回:
        noisy_neighbors: 添加噪声后的邻居集合
        perturbed_adj: 扰动后的邻接矩阵
    """
    n = adj_matrix.shape[0]
    perturbed = adj_matrix.copy()
    
    # 获取原始邻居
    original_neighbors = set(np.where(adj_matrix[node] > 0)[0])
    original_neighbors.discard(node)  # 移除自环
    
    # 计算邻居数的敏感性为1
    sensitivity = 1.0
    scale = sensitivity / epsilon
    
    # 添加Laplace噪声到邻居数量
    noisy_degree = len(original_neighbors) + Laplace(scale=scale)
    noisy_degree = max(int(round(noisy_degree)), 0)
    
    # 随机选择邻居
    all_possible = set(range(n)) - {node}
    noisy_neighbors = set(np.random.choice(list(all_possible), 
                                          size=min(noisy_degree, n-1), 
                                          replace=False))
    
    # 更新邻接矩阵
    perturbed[node] = 0
    perturbed[:, node] = 0
    for neighbor in noisy_neighbors:
        perturbed[node, neighbor] = 1
        perturbed[neighbor, node] = 1
    
    return noisy_neighbors, perturbed


def subgraph_count_dp(adj_matrix, query_node, k_hop=2, epsilon=1.0):
    """
    子图计数差分隐私
    
    原理：在k跳范围内统计子图类型（如三角形、路径），
    通过添加Laplace噪声保护局部结构
    
    参数:
        adj_matrix: 邻接矩阵
        query_node: 查询节点
        k_hop: 跳数范围
        epsilon: 隐私预算
    
    返回:
        noisy_counts: 带噪声的子图计数
    """
    n = adj_matrix.shape[0]
    
    # BFS获取k跳内的节点
    visited = {query_node}
    current_layer = {query_node}
    
    for _ in range(k_hop):
        next_layer = set()
        for node in current_layer:
            neighbors = np.where(adj_matrix[node] > 0)[0]
            for neighbor in neighbors:
                if neighbor not in visited:
                    next_layer.add(neighbor)
        visited.update(next_layer)
        current_layer = next_layer
    
    local_nodes = list(visited)
    
    # 构建局部子图
    local_adj = adj_matrix[np.ix_(local_nodes, local_nodes)]
    
    # 计数三角形（简单的子图类型）
    n_triangles = 0
    for i in range(len(local_nodes)):
        for j in range(i+1, len(local_nodes)):
            for k in range(j+1, len(local_nodes)):
                # 检查是否构成三角形
                if (local_adj[i, j] > 0 and local_adj[j, k] > 0 and local_adj[k, i] > 0):
                    n_triangles += 1
    
    # 添加噪声
    sensitivity = 1.0  # 单条边最多影响一个三角形
    scale = sensitivity / epsilon
    noisy_triangles = n_triangles + Laplace(scale=scale)
    
    return {"triangles": max(0, int(round(noisy_triangles))), 
            "local_nodes": len(local_nodes)}


# ============== 测试代码 ==============
if __name__ == "__main__":
    print("=" * 60)
    print("图数据差分隐私 - 测试演示")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 创建测试图：简单社交网络
    n_nodes = 10
    edges = [
        (0, 1), (0, 2), (0, 3),
        (1, 2), (1, 4),
        (2, 3), (2, 5),
        (3, 6),
        (4, 5), (4, 7),
        (5, 7),
        (6, 8), (6, 9),
        (7, 8),
        (8, 9)
    ]
    
    adj_matrix, _ = build_adjacency_matrix(edges, n_nodes, directed=False)
    
    print(f"\n原始图: {n_nodes} 节点, {len(edges)} 条边")
    print(f"原始度分布: {np.sum(adj_matrix > 0, axis=1)}")
    
    # 测试1：边扰动
    print("\n" + "-" * 40)
    print("测试1: 边扰动差分隐私")
    print("-" * 40)
    
    for eps in [0.5, 1.0, 2.0]:
        perturbed = edge_perturbation_dp(adj_matrix, epsilon=eps)
        n_edges_perturbed = int(np.sum(perturbed > 0) / 2)
        print(f"  epsilon={eps}: 扰动后边数={n_edges_perturbed}")
    
    # 测试2：度分布保护
    print("\n" + "-" * 40)
    print("测试2: 度分布保护")
    print("-" * 40)
    
    protected_degrees = degree_distribution_protection(adj_matrix, epsilon=1.0)
    original_degrees = np.sum(adj_matrix > 0, axis=1)
    
    print(f"原始度: {original_degrees}")
    print(f"保护后度: {protected_degrees}")
    print(f"度差异: {np.abs(original_degrees - protected_degrees)}")
    
    # 测试3：图谱扰动
    print("\n" + "-" * 40)
    print("测试3: 图谱扰动")
    print("-" * 40)
    
    spectral_perturbed = graph_spectral_perturbation(adj_matrix, epsilon=1.0)
    print(f"原始特征值数量: {len(np.linalg.eigvalsh(adj_matrix))}")
    print(f"扰动后边数: {int(np.sum(spectral_perturbed > 0) / 2)}")
    
    # 测试4：图匹配防御
    print("\n" + "-" * 40)
    print("测试4: 图匹配防御")
    print("-" * 40)
    
    defended, num_changes = graph_matching_defense(adj_matrix, epsilon=1.0)
    defended_edges = int(np.sum(defended > 0) / 2)
    print(f"原始边数: {len(edges)}")
    print(f"防御后边数: {defended_edges}")
    print(f"改变的边数: {num_changes}")
    
    # 测试5：局部结构隐私
    print("\n" + "-" * 40)
    print("测试5: 局部结构隐私保护")
    print("-" * 40)
    
    target_node = 0
    noisy_neighbors, perturbed_adj = local_structure_privacy(
        adj_matrix, target_node, epsilon=1.0
    )
    original_neighbors = set(np.where(adj_matrix[target_node] > 0)[0])
    original_neighbors.discard(target_node)
    
    print(f"节点{target_node}的原始邻居: {original_neighbors}")
    print(f"扰动后的邻居: {noisy_neighbors}")
    print(f"邻居变化: {len(original_neighbors ^ noisy_neighbors)}")
    
    # 测试6：子图计数
    print("\n" + "-" * 40)
    print("测试6: 子图计数差分隐私")
    print("-" * 40)
    
    for node in [0, 4, 8]:
        counts = subgraph_count_dp(adj_matrix, node, k_hop=2, epsilon=1.0)
        print(f"  节点{node}的2跳子图: {counts}")
    
    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)