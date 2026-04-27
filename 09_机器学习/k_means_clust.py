# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / k_means_clust



本文件实现 k_means_clust 相关的算法功能。

"""



import numpy as np





def get_initial_centroids(data, k, seed=None):

    """

    随机初始化 K 个质心



    参数:

        data: 数据集

        k: 簇的数量

        seed: 随机种子（用于复现）

    """

    rng = np.random.default_rng(seed)

    n = data.shape[0]

    rand_indices = rng.integers(0, n, k)

    return data[rand_indices, :]





def assign_clusters(data, centroids):

    """

    分配阶段：将每个数据点分配给最近的质心



    返回:

        每个数据点所属的簇编号

    """

    # 计算每个点到所有质心的距离

    distances = np.linalg.norm(data[:, np.newaxis, :] - centroids[np.newaxis, :, :], axis=2)

    # 取距离最小的质心编号

    return np.argmin(distances, axis=1)





def revise_centroids(data, k, cluster_assignment):

    """

    更新阶段：重新计算每个簇的质心



    新质心 = 该簇所有点的均值

    """

    new_centroids = []

    for i in range(k):

        member_points = data[cluster_assignment == i]

        if len(member_points) > 0:

            centroid = member_points.mean(axis=0)

        else:

            centroid = data[np.random.randint(len(data))]

        new_centroids.append(centroid)

    return np.array(new_centroids)





def compute_heterogeneity(data, k, centroids, cluster_assignment):

    """

    计算异质性（目标函数值）



    J = Σ ||x_i - μ_{c_i}||²

    """

    heterogeneity = 0.0

    for i in range(k):

        member_points = data[cluster_assignment == i, :]

        if len(member_points) > 0:

            distances = np.linalg.norm(member_points - centroids[i], axis=1)

            heterogeneity += np.sum(distances ** 2)

    return heterogeneity





def kmeans(data, k, initial_centroids, maxiter=500, record_heterogeneity=None, verbose=False):

    """

    K-Means 聚类主函数



    参数:

        data: 数据集

        k: 簇的数量

        initial_centroids: 初始质心

        maxiter: 最大迭代次数

        record_heterogeneity: 记录每轮异质性



    返回:

        (最终质心, 簇分配结果)

    """

    centroids = initial_centroids[:]



    for iteration in range(maxiter):

        if verbose:

            print(f"迭代 {iteration}")



        # 1. 分配阶段

        cluster_assignment = assign_clusters(data, centroids)



        # 2. 更新阶段

        centroids = revise_centroids(data, k, cluster_assignment)



        # 3. 记录异质性

        if record_heterogeneity is not None:

            score = compute_heterogeneity(data, k, centroids, cluster_assignment)

            record_heterogeneity.append(score)



        # 检查是否收敛（簇分配不再变化）

        if len(record_heterogeneity) > 1:

            if record_heterogeneity[-1] == record_heterogeneity[-2]:

                if verbose:

                    print(f"已收敛，迭代 {iteration} 次")

                break



    return centroids, cluster_assignment





if __name__ == "__main__":

    # 生成示例数据

    np.random.seed(42)



    # 生成3个簇的数据

    cluster1 = np.random.randn(50, 2) + [0, 0]

    cluster2 = np.random.randn(50, 2) + [5, 5]

    cluster3 = np.random.randn(50, 2) + [0, 5]



    data = np.vstack([cluster1, cluster2, cluster3])

    np.random.shuffle(data)



    # 运行 K-Means

    k = 3

    initial_centroids = get_initial_centroids(data, k, seed=0)



    heterogeneity = []

    centroids, labels = kmeans(data, k, initial_centroids, record_heterogeneity=heterogeneity, verbose=True)



    print(f"\n最终质心:\n{centroids}")

    print(f"最终异质性: {heterogeneity[-1]:.2f}")

    print(f"各簇大小: {np.bincount(labels)}")

