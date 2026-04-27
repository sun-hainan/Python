# -*- coding: utf-8 -*-

"""

算法实现：压缩感知 / restricted_isometry



本文件实现 restricted_isometry 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple





class RestrictedIsometryProperty:

    """RIP性质检验"""



    def __init__(self, delta: float = 0.5, k: int = None):

        """

        参数：

            delta: RIP常数

            k: 稀疏度

        """

        self.delta = delta

        self.k = k



    def check_rip(self, Phi: np.ndarray, k: int, n_trials: int = 50) -> Tuple[bool, float]:

        """

        近似检查RIP性质（采样法）



        参数：

            Phi: 测量矩阵 (M × N)

            k: 稀疏度

            n_trials: 采样次数



        返回：(是否满足RIP, 估计的RIP常数)

        """

        M, N = Phi.shape



        max_rip = 0

        min_rip = float('inf')



        for _ in range(n_trials):

            # 随机生成k-稀疏向量

            x = np.zeros(N)

            support = np.random.choice(N, k, replace=False)

            x[support] = np.random.randn(k)



            # 测量

            y = Phi @ x

            measured_norm = np.linalg.norm(y) ** 2

            true_norm = np.linalg.norm(x) ** 2



            ratio = measured_norm / true_norm if true_norm > 0 else 0



            max_rip = max(max_rip, ratio)

            min_rip = min(min_rip, ratio)



        delta_estimate = max(max_rip - 1, 1 - min_rip)



        return delta_estimate <= self.delta, delta_estimate





class GaussianMatrix:

    """高斯随机测量矩阵"""



    def __init__(self, M: int, N: int):

        """

        参数：

            M: 测量数

            N: 信号维度

        """

        self.Phi = np.random.randn(M, N) / np.sqrt(M)



    def get_matrix(self) -> np.ndarray:

        return self.Phi



    def measure(self, signal: np.ndarray) -> np.ndarray:

        """获取测量值"""

        return self.Phi @ signal





class RIPAnalysis:

    """RIP分析工具"""



    @staticmethod

    def theoretical_bound(M: int, N: int, k: int, delta: float = 0.5) -> bool:

        """

        理论RIP保证（Gershgorin圆盘定理）



        对于M×N的高斯矩阵

        如果 M ≥ C · k · log(N/k) / δ²

        则以高概率满足RIP

        """

        import math



        # 常数C ≈ 1（简化）

        C = 1.0



        required_M = C * k * math.log(N / k) / (delta ** 2)



        return M >= required_M





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== RIP性质测试 ===\n")



    np.random.seed(42)



    # 设置参数

    N = 100  # 信号维度

    k = 10   # 稀疏度

    M = 50   # 测量数



    print(f"信号维度: N = {N}")

    print(f"稀疏度: k = {k}")

    print(f"测量数: M = {M}")

    print()



    # 创建高斯测量矩阵

    Phi = np.random.randn(M, N) / np.sqrt(M)



    # 检查RIP

    rip_checker = RestrictedIsometryProperty(delta=0.5, k=k)

    is_rip, delta_est = rip_checker.check_rip(Phi, k, n_trials=100)



    print(f"RIP检查（δ=0.5）:")

    print(f"  是否满足: {'是' if is_rip else '否'}")

    print(f"  估计δ: {delta_est:.4f}")

    print()



    # 理论保证

    has_theoretical = RIPAnalysis.theoretical_bound(M, N, k)

    print(f"理论保证（M ≥ C·k·log(N/k)/δ²）:")

    print(f"  {'满足' if has_theoretical else '不满足'}")



    print()

    print("RIP的应用：")

    print("  1. 压缩感知：保证稀疏信号恢复")

    print("  2. 字典学习：验证过完备字典的RIP")

    print("  3. 扰动分析：测量误差的影响")

    print()

    print("说明：")

    print("  - RIP是压缩感知的核心理论")

    print("  - 高斯/伯努利矩阵以高概率满足RIP")

    print("  - 实际中常使用RIP常数 δ ∈ (0, 0.5)")

