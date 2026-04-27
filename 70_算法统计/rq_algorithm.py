# -*- coding: utf-8 -*-

"""

算法实现：算法统计 / rq_algorithm



本文件实现 rq_algorithm 相关的算法功能。

"""



import numpy as np

from typing import Tuple





class RQAlgorithm:

    """RQ算法（简化实现）"""



    def __init__(self, n_factors: int = 10):

        """

        参数：

            n_factors: 隐因子数

        """

        self.n_factors = n_factors



    def fit(self, matrix: np.ndarray, max_iter: int = 100) -> Tuple[np.ndarray, np.ndarray]:

        """

        分解矩阵



        参数：

            matrix: 输入矩阵 (m × n)

            max_iter: 最大迭代



        返回：(U, V) 使得 U @ V ≈ matrix

        """

        m, n = matrix.shape



        # 初始化

        U = np.random.randn(m, self.n_factors) * 0.1

        V = np.random.randn(self.n_factors, n) * 0.1



        for iteration in range(max_iter):

            # 更新U（固定V）

            for i in range(m):

                # 解最小二乘

                residual = matrix[i] - U[i] @ V

                # 简化更新

                U[i] += 0.01 * residual @ V.T / (np.linalg.norm(V) ** 2 + 1e-6)



            # 更新V（固定U）

            for j in range(n):

                residual = matrix[:, j] - U @ V[:, j]

                V[:, j] += 0.01 * U.T @ residual / (np.linalg.norm(U) ** 2 + 1e-6)



            # 计算误差

            error = np.linalg.norm(matrix - U @ V) / np.linalg.norm(matrix)



            if iteration % 20 == 0:

                print(f"  迭代 {iteration}: 相对误差 = {error:.6f}")



        return U, V



    def predict(self, U: np.ndarray, V: np.ndarray, i: int, j: int) -> float:

        """

        预测元素



        返回：预测值

        """

        return U[i] @ V[:, j]



    def low_rank_approximation(self, matrix: np.ndarray, rank: int) -> np.ndarray:

        """

        低秩逼近（SVD）



        返回：rank近似的矩阵

        """

        U, s, Vt = np.linalg.svd(matrix, full_matrices=False)



        # 取前rank个

        U_k = U[:, :rank]

        s_k = s[:rank]

        Vt_k = Vt[:rank, :]



        return U_k @ np.diag(s_k) @ Vt_k





def rq_applications():

    """RQ应用"""

    print("=== RQ算法应用 ===")

    print()

    print("1. 推荐系统")

    print("   - 用户-物品评分矩阵")

    print("   - 找到用户和物品的隐向量")

    print()

    print("2. 降维")

    print("   - 高维数据降到低维")

    print("   - 保留主要结构")

    print()

    print("3. 图像处理")

    print("   - 图像去噪")

    print("   - 压缩")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== RQ算法测试 ===\n")



    np.random.seed(42)



    # 创建低秩矩阵

    m, n = 20, 15

    rank = 3



    # 生成真实U和V

    true_U = np.random.randn(m, rank) * 5

    true_V = np.random.randn(rank, n) * 5



    # 真实矩阵

    true_matrix = true_U @ true_V



    # 添加噪声

    noise = np.random.randn(m, n) * 0.5

    observed_matrix = true_matrix + noise



    print(f"矩阵大小: {m} × {n}")

    print(f"真实秩: {rank}")

    print()



    # RQ分解

    rq = RQAlgorithm(n_factors=rank)



    print("RQ分解：")

    U, V = rq.fit(observed_matrix, max_iter=100)



    print()



    # 重构

    reconstructed = U @ V



    # 计算误差

    error = np.linalg.norm(observed_matrix - reconstructed) / np.linalg.norm(observed_matrix)

    print(f"相对误差: {error:.4f}")

    print()



    # 预测

    pred = rq.predict(U, V, i=0, j=0)

    true_val = true_matrix[0, 0]

    print(f"预测 [{0},{0}]: {pred:.2f}")

    print(f"真实值: {true_val:.2f}")



    print()

    rq_applications()



    print()

    print("说明：")

    print("  - RQ用于矩阵分解")

    print("  - 是推荐系统的基础算法")

    print("  - 比SVD更灵活")

