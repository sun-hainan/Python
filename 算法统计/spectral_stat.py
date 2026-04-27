# -*- coding: utf-8 -*-

"""

算法实现：算法统计 / spectral_stat



本文件实现 spectral_stat 相关的算法功能。

"""



import numpy as np

from typing import List





class SpectralStatistics:

    """谱统计"""



    def __init__(self):

        pass



    def marchenko_pastur(self, n: int, p: int, sigma: float = 1.0) -> np.ndarray:

        """

        Marchenko-Pastur分布（随机矩阵特征值的极限分布）



        参数：

            n: 矩阵维度

            p: 样本数

            sigma: 噪声标准差



        返回：支持区间

        """

        # 比率

        ratio = p / n

        sqrt_ratio = np.sqrt(ratio)



        # MP分布的支撑

        lambda_min = sigma ** 2 * (1 - sqrt_ratio) ** 2

        lambda_max = sigma ** 2 * (1 + sqrt_ratio) ** 2



        return np.array([lambda_min, lambda_max])



    def empirical_spectrum(self, matrix: np.ndarray) -> np.ndarray:

        """

        计算经验谱



        参数：

            matrix: 对称矩阵



        返回：特征值数组

        """

        eigenvalues = np.linalg.eigvalsh(matrix)

        return np.sort(eigenvalues)[::-1]



    def plasma_test(self, eigenvalues: np.ndarray, n: int, p: int) -> bool:

        """

        检验特征值是否来自随机矩阵



        返回：是否通过检验

        """

        mp_support = self.marchenko_pastur(n, p)

        min_eig = eigenvalues[-1]

        max_eig = eigenvalues[0]



        # 检查是否在MP支持内

        in_support = (min_eig >= mp_support[0] * 0.9 and

                      max_eig <= mp_support[1] * 1.1)



        return in_support



    def spiked_covariance(self, eigenvalues: np.ndarray, threshold: float) -> dict:

        """

        检测"尖峰"特征值



        参数：

            eigenvalues: 特征值

            threshold: 阈值



        返回：尖峰信息

        """

        spiked = [i for i, eig in enumerate(eigenvalues) if eig > threshold]



        return {

            'n_spikes': len(spiked),

            'spike_indices': spiked,

            'top_eigenvalues': eigenvalues[:min(5, len(eigenvalues))].tolist()

        }



    def wigner_semicircle(self, n: int) -> np.ndarray:

        """

        Wigner半圆分布



        返回：支持区间

        """

        radius = 2 * np.sqrt(n)

        return np.array([-radius, radius])





def spectral_analysis_applications():

    """谱分析应用"""

    print("=== 谱统计应用 ===")

    print()

    print("1. 统计学")

    print("   - 随机矩阵理论")

    print("   - 高维数据分析")

    print()

    print("2. 量子物理")

    print("   - 能级统计")

    print("   - Wigner-Dyson分布")

    print()

    print("3. 金融数学")

    print("   - 协方差矩阵估计")

    print("   - 风险管理")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 谱统计测试 ===\n")



    np.random.seed(42)



    # 创建随机矩阵

    n, p = 100, 50

    matrix = np.random.randn(n, p) @ np.random.randn(p, n) / p



    spec = SpectralStatistics()



    # 经验谱

    eigenvalues = spec.empirical_spectrum(matrix)



    print(f"矩阵大小: {n} × {n}")

    print(f"特征值数量: {len(eigenvalues)}")

    print(f"最大特征值: {eigenvalues[0]:.4f}")

    print(f"最小特征值: {eigenvalues[-1]:.4f}")

    print()



    # Marchenko-Pastur支持

    mp_support = spec.marchenko_pastur(n, p)

    print(f"MP支持区间: [{mp_support[0]:.4f}, {mp_support[1]:.4f}]")



    # 检验

    is_random = spec.plasma_test(eigenvalues, n, p)

    print(f"通过MP检验: {'✅' if is_random else '❌'}")

    print()



    # 检测尖峰

    threshold = np.mean(eigenvalues) + 2 * np.std(eigenvalues)

    spike_info = spec.spiked_covariance(eigenvalues, threshold)



    print(f"尖峰检测 (阈值={threshold:.2f}):")

    print(f"  尖峰数: {spike_info['n_spikes']}")

    print(f"  顶部特征值: {[f'{e:.2f}' for e in spike_info['top_eigenvalues'][:3]]}")



    print()

    spectral_analysis_applications()



    print()

    print("说明：")

    print("  - 谱统计用于高维数据分析")

    print("  - MP分布描述噪声矩阵的特征值")

    print("  - 用于检测信号和噪声")

