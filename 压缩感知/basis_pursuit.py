# -*- coding: utf-8 -*-

"""

算法实现：压缩感知 / basis_pursuit



本文件实现 basis_pursuit 相关的算法功能。

"""



import numpy as np

from typing import Tuple





class BasisPursuit:

    """基追踪"""



    def __init__(self, A: np.ndarray, b: np.ndarray, lam: float = 1.0):

        """

        参数：

            A: 测量矩阵

            b: 观测向量

            lam: 正则化参数

        """

        self.A = A

        self.b = b

        self.lam = lam

        self.m, self.n = A.shape



    def solve(self) -> np.ndarray:

        """

        求解 min ||x||₁ s.t. Ax = b



        使用迭代软阈值算法（ISTA）



        返回：稀疏解

        """

        x = np.zeros(self.n)

        learning_rate = 1.0 / (np.linalg.norm(self.A, ord=2) ** 2)



        max_iter = 1000

        for _ in range(max_iter):

            # 梯度步

            gradient = self.A.T @ (self.A @ x - self.b)

            x_new = x - learning_rate * gradient



            # 软阈值

            x_new = np.sign(x_new) * np.maximum(np.abs(x_new) - self.lam * learning_rate, 0)



            # 检查收敛

            if np.linalg.norm(x_new - x) < 1e-6:

                break



            x = x_new



        return x



    def solve_lagrangian(self) -> np.ndarray:

        """

        求解 Lagrangian 版本



        min (1/2)||Ax - b||² + λ||x||₁

        """

        x = np.zeros(self.n)

        t = 1.0  # 步长



        for _ in range(1000):

            # 近似点算法

            z = x - (1/t) * self.A.T @ (self.A @ x - self.b)



            # 软阈值

            x_new = np.sign(z) * np.maximum(np.abs(z) - (self.lam / t), 0)



            if np.linalg.norm(x_new - x) < 1e-6:

                break



            x = x_new



        return x





def basis_pursuit_vs_least_squares():

    """基追踪 vs 最小二乘"""

    print("=== 基追踪 vs 最小二乘 ===")

    print()

    print("最小二乘（ L2）：")

    print("  min ||Ax - b||₂")

    print("  解：x = (A^T A)^(-1) A^T b")

    print("  问题：对噪声敏感")

    print()

    print("基追踪（ L1）：")

    print("  min ||x||₁ s.t. Ax = b")

    print("  解：通过迭代优化")

    print("  优点：稀疏解，噪声鲁棒")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 基追踪测试 ===\n")



    np.random.seed(42)



    # 创建问题

    n = 100  # 稀疏度

    m = 30   # 测量数

    A = np.random.randn(m, n)

    A = A / np.linalg.norm(A, axis=0)  # 归一化



    # 真实稀疏信号

    x_true = np.zeros(n)

    support = np.random.choice(n, 5, replace=False)

    x_true[support] = np.random.randn(5)



    # 观测

    b = A @ x_true + 0.01 * np.random.randn(m)



    print(f"信号维度: {n}")

    print(f"测量数: {m}")

    print(f"真实非零数: {np.sum(x_true != 0)}")

    print()



    # 基追踪求解

    bp = BasisPursuit(A, b, lam=0.1)

    x_rec = bp.solve_lagrangian()



    print("结果：")

    print(f"  恢复非零数: {np.sum(np.abs(x_rec) > 0.1)}")

    print(f"  恢复误差: {np.linalg.norm(x_rec - x_true):.4f}")



    print()

    basis_pursuit_vs_least_squares()



    print()

    print("应用：")

    print("  - 压缩感知信号恢复")

    print("  - 图像去噪")

    print("  - 机器学习特征选择")

