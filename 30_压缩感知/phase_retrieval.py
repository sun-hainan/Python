# -*- coding: utf-8 -*-

"""

算法实现：压缩感知 / phase_retrieval



本文件实现 phase_retrieval 相关的算法功能。

"""



import numpy as np

from typing import Tuple





class PhaseRetrieval:

    """相位恢复算法"""



    def __init__(self, m: int, n: int):

        """

        参数：

            m: 测量数

            n: 信号维度

        """

        self.m = m

        self.n = n

        self.A = self._generate_matrix()



    def _generate_matrix(self) -> np.ndarray:

        """生成传感矩阵"""

        A = np.random.randn(self.m, self.n) + 1j * np.random.randn(self.m, self.n)

        return A / np.sqrt(self.n)



    def gerchberg_saxton(self, b: np.ndarray,

                       max_iter: int = 100,

                       tol: float = 1e-6) -> np.ndarray:

        """

        Gerchberg-Saxton算法



        参数：

            b: 幅度测量 |Ax|

            max_iter: 最大迭代

            tol: 收敛容差



        返回：恢复的信号

        """

        # 初始化

        x = np.random.randn(self.n) + 1j * np.random.randn(self.n)

        x = x / np.linalg.norm(x)



        for iteration in range(max_iter):

            # 前向变换

            y = self.A @ x



            # 在幅度域施加约束

            y_constraint = b * np.exp(1j * np.angle(y))



            # 反向变换

            x_new = self.A.conj().T @ y_constraint



            # 在信号域施加约束（如果有稀疏性等）

            x = x_new / np.linalg.norm(x_new)



            # 检查收敛

            residual = np.linalg.norm(b - np.abs(y))



            if iteration % 20 == 0:

                print(f"  迭代 {iteration}: 残差 = {residual:.6f}")



            if residual < tol:

                break



        return x



    def wiener_filter_recovery(self, b: np.ndarray,

                               noise_level: float = 0.1) -> np.ndarray:

        """

        维纳滤波恢复（简化）



        参数：

            b: 幅度测量

            noise_level: 噪声水平



        返回：恢复的信号

        """

        # 简化：使用伪逆 + 维纳滤波

        pseudo_inv = np.linalg.pinv(self.A)

        x_init = pseudo_inv @ b



        # 简化维纳滤波

        # 假设信号功率谱平坦

        signal_power = np.mean(np.abs(x_init) ** 2)

        noise_power = noise_level ** 2



        # 维纳增益

        gain = signal_power / (signal_power + noise_power)



        return x_init * gain





def phase_retrieval_applications():

    """相位恢复应用"""

    print("=== 相位恢复应用 ===")

    print()

    print("1. X射线晶体学")

    print("   - 从衍射图案恢复晶体结构")

    print("   -  Nobel Prize 2011 (Shechtman)")

    print()

    print("2. 光学成像")

    print("   - 从强度测量恢复图像相位")

    print("   - 鬼成像、透射成像")

    print()

    print("3. 量子力学")

    print("   - 从幅度重建波函数")

    print("   - 量子层析成像")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 相位恢复测试 ===\n")



    np.random.seed(42)



    # 参数

    n = 50   # 信号维度

    m = 150  # 测量数（大于2n）



    pr = PhaseRetrieval(m, n)



    # 生成真实信号

    x_true = np.random.randn(n) + 1j * np.random.randn(n)

    x_true = x_true / np.linalg.norm(x_true)



    # 测量幅度

    b = np.abs(pr.A @ x_true)



    print(f"信号维度: {n}")

    print(f"测量数: {m}")

    print(f"压缩比: {m/n:.2f}")

    print()



    # Gerchberg-Saxton

    print("Gerchberg-Saxton恢复：")

    x_recovered = pr.gerchberg_saxton(b, max_iter=50)



    # 计算误差

    error = np.linalg.norm(x_recovered - x_true) / np.linalg.norm(x_true)

    print(f"\n相对误差: {error:.4f}")



    # 检查是否同构（忽略全局相位）

    inner_product = np.abs(np.vdot(x_recovered, x_true))

    print(f"内部积（应为1）: {inner_product:.4f}")



    print()

    phase_retrieval_applications()



    print()

    print("说明：")

    print("  - 相位恢复是从幅度重建信号的难题")

    print("  - Gerchberg-Saxton是经典算法")

    print("  - Wirtinger Flow等深度学习方法也在研究中")

