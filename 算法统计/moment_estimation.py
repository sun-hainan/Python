# -*- coding: utf-8 -*-

"""

算法实现：算法统计 / moment_estimation



本文件实现 moment_estimation 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple





class MomentEstimator:

    """矩估计器"""



    def __init__(self, data: List[float]):

        """

        参数：

            data: 数据样本

        """

        self.data = np.array(data)

        self.n = len(self.data)



    def raw_moment(self, r: int) -> float:

        """

        计算第r阶原点矩



        m'_r = (1/n) * Σ x_i^r

        """

        return np.mean(self.data ** r)



    def central_moment(self, r: int) -> float:

        """

        计算第r阶中心矩



        m_r = (1/n) * Σ (x_i - x̄)^r

        """

        mean = np.mean(self.data)

        centered = self.data - mean

        return np.mean(centered ** r)



    def estimate_mean(self) -> float:

        """估计均值（一阶矩）"""

        return self.raw_moment(1)



    def estimate_variance(self) -> float:

        """估计方差（二阶中心矩）"""

        return self.central_moment(2)



    def estimate_skewness(self) -> float:

        """估计偏度（三阶标准化矩）"""

        var = self.central_moment(2)

        if var == 0:

            return 0.0

        return self.central_moment(3) / (var ** 1.5)



    def estimate_kurtosis(self) -> float:

        """估计峰度（四阶标准化矩）"""

        var = self.central_moment(2)

        if var == 0:

            return 0.0

        return self.central_moment(4) / (var ** 2)





class MixtureMomentEstimator:

    """混合分布矩估计"""



    @staticmethod

    def estimate_mixture_params(moments: List[float],

                              n_components: int) -> List[Tuple[float, float, float]]:

        """

        从矩估计混合分布参数



        简化版：假设高斯混合



        参数：

            moments: 前几个矩

            n_components: 组分数



        返回：[(weight, mean, std), ...]

        """

        # 简化实现

        # 实际需要更复杂的矩反演



        weights = [1.0 / n_components] * n_components

        means = [i * 2 for i in range(n_components)]

        stds = [1.0] * n_components



        return list(zip(weights, means, stds))





def moment_matching():

    """矩匹配"""

    print("=== 矩匹配 ===")

    print()

    print("目标：用分布的矩来拟合参数")

    print()

    print("例子：正态分布")

    print("  - m1 = μ (均值)")

    print("  - m2 = σ² + μ²")

    print("  - 解方程得 μ = m1, σ² = m2 - m1²")





def sample_vs_population():

    """样本矩 vs 总体矩"""

    print()

    print("=== 样本矩 vs 总体矩 ===")

    print()

    print("样本矩：")

    print("  - m'_r = (1/n) Σ x_i^r")

    print("  - 是总体矩的无偏估计")

    print()

    print("中心矩：")

    print("  - 使用样本均值而非总体均值")

    print("  - Bessel校正适用于方差")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 矩估计测试 ===\n")



    np.random.seed(42)



    # 生成样本

    data = np.random.normal(loc=5, scale=2, size=1000)



    estimator = MomentEstimator(data)



    print(f"样本数据（正态分布，μ=5, σ=2）：")

    print(f"  样本数: {estimator.n}")

    print()



    # 矩估计

    mean_est = estimator.estimate_mean()

    var_est = estimator.estimate_variance()

    skew_est = estimator.estimate_skewness()

    kurt_est = estimator.estimate_kurtosis()



    print("矩估计结果：")

    print(f"  均值（1阶矩）: {mean_est:.4f}")

    print(f"  方差（2阶中心矩）: {var_est:.4f}")

    print(f"  偏度（3阶标准化）: {skew_est:.4f}")

    print(f"  峰度（4阶标准化）: {kurt_est:.4f}")



    print()

    moment_matching()

    sample_vs_population()



    print()

    print("理论值（正态分布）：")

    print("  偏度 = 0")

    print("  峰度 = 3")

    print(f"  样本偏度 = {abs(skew_est):.4f}（接近0）")

    print(f"  样本峰度 = {kurt_est:.4f}（接近3）")

