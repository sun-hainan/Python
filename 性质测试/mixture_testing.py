# -*- coding: utf-8 -*-

"""

算法实现：性质测试 / mixture_testing



本文件实现 mixture_testing 相关的算法功能。

"""



import random

import numpy as np

from typing import List, Tuple

from collections import Counter





class MixtureTester:

    """混合分布测试器"""



    def __init__(self, epsilon: float = 0.1):

        """

        参数：

            epsilon: 距离参数

        """

        self.epsilon = epsilon



    def test_two_component(self, samples: List[float],

                         threshold: float) -> Tuple[bool, float]:

        """

        测试是否来自两个成分



        参数：

            samples: 样本

            threshold: 分离阈值



        返回：(是否混合, 混合比例估计)

        """

        n = len(samples)



        # 统计两边的样本数

        below = sum(1 for s in samples if s < threshold)

        above = sum(1 for s in samples if s >= threshold)



        ratio = min(below, above) / n



        # 如果两边都有显著样本，认为是混合

        is_mixture = ratio > self.epsilon



        mixing_ratio = ratio * 2  # 估计



        return is_mixture, mixing_ratio



    def em_algorithm(self, samples: List[float],

                    n_components: int = 2) -> dict:

        """

        EM算法估计混合参数



        参数：

            samples: 样本

            n_components: 成分数



        返回：参数估计

        """

        # 简化EM：假设高斯混合

        n = len(samples)



        # 随机初始化

        means = [np.min(samples), np.max(samples)]

        stds = [1.0, 1.0]

        weights = [0.5, 0.5]



        max_iter = 50

        for iteration in range(max_iter):

            # E步骤：计算每个样本属于各成分的概率

            responsibilities = []



            for s in samples:

                probs = []

                for j in range(n_components):

                    p = weights[j] * self._normal_pdf(s, means[j], stds[j])

                    probs.append(p)



                total = sum(probs)

                responsibilities.append([p / total for p in probs])



            # M步骤：更新参数

            for j in range(n_components):

                N_j = sum(r[j] for r in responsibilities)



                if N_j > 0:

                    # 更新均值

                    means[j] = sum(s * r[j] for s, r in zip(samples, responsibilities)) / N_j



                    # 更新标准差

                    variance = sum(r[j] * (s - means[j]) ** 2

                                  for s, r in zip(samples, responsibilities)) / N_j

                    stds[j] = max(0.1, np.sqrt(variance))



                    # 更新权重

                    weights[j] = N_j / n



        return {

            'means': means,

            'stds': stds,

            'weights': weights,

            'n_iterations': max_iter

        }



    def _normal_pdf(self, x: float, mean: float, std: float) -> float:

        """高斯概率密度"""

        import math

        coeff = 1.0 / (std * math.sqrt(2 * math.pi))

        exponent = -0.5 * ((x - mean) / std) ** 2

        return coeff * math.exp(exponent)





def mixture_model_applications():

    """混合模型应用"""

    print("=== 混合模型应用 ===")

    print()

    print("1. 生物信息学")

    print("   - 基因表达数据分析")

    print("   - 细胞类型识别")

    print()

    print("2. 图像分割")

    print("   - 前景/背景分离")

    print("   - 颜色聚类")

    print()

    print("3. 异常检测")

    print("   - 正常/异常混合")

    print("   - 欺诈检测")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 混合分布测试 ===\n")



    random.seed(42)



    # 创建混合分布样本

    samples = []



    # 成分1: 均值0, 标准差1

    samples.extend(np.random.randn(500) * 1 + 0)



    # 成分2: 均值5, 标准差1

    samples.extend(np.random.randn(500) * 1 + 5)



    random.shuffle(samples)



    print(f"样本数: {len(samples)}")

    print(f"样本范围: [{min(samples):.2f}, {max(samples):.2f}]")

    print()



    tester = MixtureTester(epsilon=0.1)



    # 测试两成分

    threshold = 2.5

    is_mix, ratio = tester.test_two_component(samples, threshold)



    print(f"阈值: {threshold}")

    print(f"是混合分布: {'是' if is_mix else '否'}")

    print(f"混合比例估计: {ratio:.4f}")

    print()



    # EM估计

    print("EM算法估计：")

    result = tester.em_algorithm(samples, n_components=2)



    print(f"  成分1: 均值={result['means'][0]:.2f}, 标准差={result['stds'][0]:.2f}")

    print(f"  成分2: 均值={result['means'][1]:.2f}, 标准差={result['stds'][1]:.2f}")

    print(f"  权重: {result['weights'][0]:.2f}, {result['weights'][1]:.2f}")



    print()

    mixture_model_applications()



    print()

    print("说明：")

    print("  - 混合分布测试识别数据来源")

    print("  - EM算法是标准估计方法")

    print("  - 成分数需要预先设定")

