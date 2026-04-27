# -*- coding: utf-8 -*-

"""

算法实现：生物信息学 / single_cell_rna



本文件实现 single_cell_rna 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict, Optional

import math





def library_size_normalization(count_matrix: np.ndarray) -> np.ndarray:

    """

    文库大小归一化（CPM/TPM）



    参数:

        count_matrix: 基因x细胞的计数矩阵



    返回:

        归一化后的表达矩阵

    """

    # 每个细胞的文库大小

    lib_sizes = np.sum(count_matrix, axis=0)

    # 避免除以0

    lib_sizes = np.maximum(lib_sizes, 1)

    # CPM归一化

    cpm = count_matrix / lib_sizes * 1e6

    return cpm





def log_transformation(count_matrix: np.ndarray, pseudocount: float = 1.0) -> np.ndarray:

    """

    对数变换



    log(count + pseudocount)



    参数:

        count_matrix: 计数矩阵

        pseudocount: 伪计数（避免log(0)）



    返回:

        对数变换后的矩阵

    """

    return np.log2(count_matrix + pseudocount)





def highly_variable_genes(

    expr_matrix: np.ndarray,

    n_genes: int = 2000

) -> Tuple[List[int], np.ndarray]:

    """

    识别高变异基因（HVG）



    方法：计算每个基因的方差，选取方差最大的



    参数:

        expr_matrix: 表达矩阵 (genes x cells)

        n_genes: 选择的高变异基因数



    返回:

        (gene_indices, variance_scores)

    """

    # 计算每个基因的方差

    gene_variance = np.var(expr_matrix, axis=1)



    # 获取top genes

    top_indices = np.argsort(gene_variance)[::-1][:n_genes]



    return list(top_indices), gene_variance[top_indices]





def pca_reduction(expr_matrix: np.ndarray, n_components: int = 50) -> np.ndarray:

    """

    PCA降维



    参数:

        expr_matrix: 表达矩阵 (genes x cells)

        n_components: 主成分数



    返回:

        降维后的矩阵 (n_components x cells)

    """

    # 中心化

    mean = np.mean(expr_matrix, axis=1, keepdims=True)

    X_centered = expr_matrix - mean



    # SVD

    U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)



    # 返回前n_components个主成分

    pca_scores = U[:, :n_components] * S[:n_components]

    return pca_scores.T  # (n_components, n_cells)





def tsne_embedding(

    data: np.ndarray,

    perplexity: float = 30.0,

    n_iter: int = 1000,

    dim: int = 2

) -> np.ndarray:

    """

    t-SNE降维（简化版）



    参数:

        data: 输入数据 (n_samples, n_features)

        perplexity: 困惑度参数

        n_iter: 迭代次数

        dim: 目标维度



    返回:

        嵌入结果 (n_samples, dim)

    """

    n_samples, n_features = data.shape



    # 初始化

    Y = np.random.randn(n_samples, dim) * 0.001



    # 计算 pairwise distances

    distances = np.zeros((n_samples, n_samples))

    for i in range(n_samples):

        distances[i] = np.sum((data - data[i])**2, axis=1)



    # 找到合适的sigma

    target_entropy = np.log(perplexity)

    sigmas = np.ones(n_samples)



    # 简化：使用固定sigma

    sigma = 1.0



    # 计算条件概率P

    P = np.exp(-distances / (2 * sigma**2))

    np.fill_diagonal(P, 0)

    P = P / (P.sum(axis=1, keepdims=True) + 1e-10)



    # t-SNE迭代

    learning_rate = 200

    for iteration in range(n_iter):

        # 计算低维距离

        sum_Y = np.sum(Y**2, axis=1, keepdims=True)

        Q = sum_Y + sum_Y.T - 2 * Y @ Y.T

        np.fill_diagonal(Q, 1e-10)

        Q = Q / Q.sum()

        Q = Q / Q.sum(axis=1, keepdims=True)



        # 计算梯度

        L = (P - Q) @ Y

        Y = Y - learning_rate * L



        # 压缩

        Y = Y * 0.99



        if iteration % 200 == 0:

            kl_div = np.sum(P * np.log(P / (Q + 1e-10)))

            print(f'  迭代{iteration}: KL散度={kl_div:.4f}')



    return Y





def simple_clustering(

    data: np.ndarray,

    n_clusters: int,

    n_init: int = 10

) -> Tuple[np.ndarray, float]:

    """

    简化K-means聚类



    参数:

        data: 数据 (n_samples, n_features)

        n_clusters: 聚类数

        n_init: 初始化次数



    返回:

        (labels, inertia)

    """

    n_samples = len(data)

    best_labels = None

    best_inertia = float('inf')



    for init in range(n_init):

        # 随机初始化中心

        indices = np.random.choice(n_samples, n_clusters, replace=False)

        centers = data[indices].copy()



        labels = np.zeros(n_samples, dtype=int)

        changed = True

        max_iter = 100

        iteration = 0



        while changed and iteration < max_iter:

            changed = False

            iteration += 1



            # 分配

            for i in range(n_samples):

                distances = np.sum((data[i] - centers)**2, axis=1)

                new_label = np.argmin(distances)

                if new_label != labels[i]:

                    labels[i] = new_label

                    changed = True



            # 更新中心

            for k in range(n_clusters):

                cluster_points = data[labels == k]

                if len(cluster_points) > 0:

                    centers[k] = np.mean(cluster_points, axis=0)



        # 计算inertia

        inertia = 0.0

        for i in range(n_samples):

            inertia += np.sum((data[i] - centers[labels[i]])**2)



        if inertia < best_inertia:

            best_inertia = inertia

            best_labels = labels.copy()



    return best_labels, best_inertia





def cell_cycle_scoring(expr_matrix: np.ndarray) -> Dict[str, float]:

    """

    细胞周期评分（简化版）



    估算每个细胞所处的细胞周期阶段



    参数:

        expr_matrix: 表达矩阵



    返回:

        每个阶段的评分

    """

    # 简化的细胞周期标记基因

    g1_genes = [0, 5, 10]

    s_genes = [2, 7, 12]

    g2_genes = [4, 9, 14]

    m_genes = [1, 6, 11]



    if expr_matrix.shape[0] <= max(max(g1_genes), max(s_genes), max(g2_genes), max(m_genes)):

        return {'G1': 0.5, 'S': 0.3, 'G2': 0.1, 'M': 0.1}



    g1_score = np.mean(expr_matrix[g1_genes], axis=0)

    s_score = np.mean(expr_matrix[s_genes], axis=0)

    g2_score = np.mean(expr_matrix[g2_genes], axis=0)

    m_score = np.mean(expr_matrix[m_genes], axis=0)



    # 归一化

    total = g1_score + s_score + g2_score + m_score + 1e-10

    return {

        'G1': np.mean(g1_score / total),

        'S': np.mean(s_score / total),

        'G2': np.mean(g2_score / total),

        'M': np.mean(m_score / total),

    }





def doublet_detection(

    neighbor_distances: np.ndarray,

    threshold: float = 0.8

) -> np.ndarray:

    """

    双细胞检测（简化版）



    双细胞会导致相似的邻居距离模式



    参数:

        neighbor_distances: 每个细胞到k近邻的平均距离

        threshold: 阈值



    返回:

        doublet_scores

    """

    # 简化的双细胞评分

    mean_dist = np.mean(neighbor_distances)

    std_dist = np.std(neighbor_distances)



    scores = (neighbor_distances - mean_dist) / (std_dist + 1e-10)

    return scores





if __name__ == '__main__':

    print('=== 单细胞RNA分析测试 ===')



    np.random.seed(42)



    # 模拟scRNA-seq数据

    n_genes = 500

    n_cells = 100

    count_matrix = np.random.randint(0, 100, size=(n_genes, n_cells))



    print(f'\n计数矩阵: {count_matrix.shape}')



    # 测试1: 归一化

    print('\n--- 测试1: 文库大小归一化 ---')

    normalized = library_size_normalization(count_matrix)

    print(f'  归一化后范围: [{normalized.min():.2f}, {normalized.max():.2f}]')



    # 测试2: 对数变换

    print('\n--- 测试2: 对数变换 ---')

    log_expr = log_transformation(normalized)

    print(f'  对数变换后范围: [{log_expr.min():.2f}, {log_expr.max():.2f}]')



    # 测试3: 高变异基因

    print('\n--- 测试3: 高变异基因选择 ---')

    hvg_indices, hvg_variance = highly_variable_genes(log_expr, n_genes=50)

    print(f'  选择HVG数: {len(hvg_indices)}')

    print(f'  Top5方差: {hvg_variance[:5]}')



    # 测试4: PCA降维

    print('\n--- 测试4: PCA降维 ---')

    hvg_expr = log_expr[hvg_indices]

    pca_result = pca_reduction(hvg_expr, n_components=10)

    print(f'  PCA结果形状: {pca_result.shape}')



    # 测试5: 聚类

    print('\n--- 测试5: K-means聚类 ---')

    data_2d = pca_result.T

    labels, inertia = simple_clustering(data_2d, n_clusters=5)

    print(f'  聚类数: {len(set(labels))}')

    print(f'  Inertia: {inertia:.2f}')

    for k in range(5):

        count = np.sum(labels == k)

        print(f'    类别{k}: {count} 细胞')



    # 测试6: 细胞周期

    print('\n--- 测试6: 细胞周期评分 ---')

    cycle_scores = cell_cycle_scoring(log_expr)

    print(f'  周期评分: {cycle_scores}')

