# -*- coding: utf-8 -*-

"""

算法实现：算法统计 / privacy_statistics



本文件实现 privacy_statistics 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple





class PrivacyPreservingStats:

    """隐私保护统计"""



    def __init__(self, epsilon: float = 1.0):

        """

        参数：

            epsilon: 隐私预算

        """

        self.epsilon = epsilon



    def noisy_mean(self, data: List[float]) -> Tuple[float, float]:

        """

        加噪声的均值



        返回：(估计均值, 标准误差)

        """

        true_mean = np.mean(data)

        n = len(data)



        # 敏感度

        sensitivity = (max(data) - min(data)) / n



        # 添加噪声

        noise = np.random.laplace(0, sensitivity / self.epsilon)



        estimated_mean = true_mean + noise

        std_error = sensitivity / self.epsilon



        return estimated_mean, std_error



    def noisy_variance(self, data: List[float]) -> Tuple[float, float]:

        """

        加噪声的方差



        返回：(估计方差, 标准误差)

        """

        true_var = np.var(data)



        # 敏感度 = 1（方差查询的敏感度）

        sensitivity = 2.0  # 简化



        noise = np.random.laplace(0, sensitivity / self.epsilon)



        estimated_var = true_var + noise



        return estimated_var, abs(noise)



    def noisy_histogram(self, data: List[float],

                      bins: int = 10) -> Tuple[List[int], List[float]]:

        """

        加噪声的直方图



        返回：(计数直方图, bin边界)

        """

        # 计算真实直方图

        hist, bin_edges = np.histogram(data, bins=bins)



        # 对每个计数添加噪声

        noisy_hist = hist.copy()

        sensitivity = 1.0



        for i in range(len(hist)):

            noise = np.random.laplace(0, sensitivity / self.epsilon)

            noisy_hist[i] = max(0, hist[i] + noise)



        return noisy_hist.tolist(), bin_edges.tolist()





def privacy_statistics_applications():

    """隐私统计应用"""

    print("=== 隐私统计应用 ===")

    print()

    print("1. 人口普查")

    print("   - 统计全国收入分布")

    print("   - 保护个人隐私")

    print()

    print("2. 医疗统计")

    print("   - 疾病发病率")

    print("   - 不暴露具体病例")

    print()

    print("3. 用户分析")

    print("   - 行为模式统计")

    print("   - 保护用户隐私")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 隐私保护统计测试 ===\n")



    np.random.seed(42)



    # 模拟数据

    data = np.random.randn(1000) * 10 + 50



    stats = PrivacyPreservingStats(epsilon=0.5)



    print(f"数据: {len(data)} 个样本")

    print(f"隐私预算: ε = 0.5")

    print()



    # 均值

    mean, se = stats.noisy_mean(data.tolist())

    print(f"真实均值: {np.mean(data):.4f}")

    print(f"估计均值: {mean:.4f} ± {se:.4f}")



    print()



    # 直方图

    noisy_hist, edges = stats.noisy_histogram(data.tolist(), bins=5)



    print("直方图:")

    for i in range(len(noisy_hist)):

        print(f"  [{edges[i]:.1f}, {edges[i+1]:.1f}): {int(noisy_hist[i])}")



    print()

    privacy_statistics_applications()



    print()

    print("说明：")

    print("  - 差分隐私保护统计数据")

    print("  - 每个查询消耗隐私预算")

    print("  - 需要仔细规划分析")

