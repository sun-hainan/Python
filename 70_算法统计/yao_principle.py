# -*- coding: utf-8 -*-

"""

算法实现：算法统计 / yao_principle



本文件实现 yao_principle 相关的算法功能。

"""



import random

from typing import List, Callable





class YaoFramework:

    """Yao's minimax框架"""



    def __init__(self):

        pass



    def construct_distribution(self, input_space: List,

                              probabilities: List[float]) -> dict:

        """

        构造输入分布



        参数：

            input_space: 输入空间

            probabilities: 概率分布



        返回：分布字典

        """

        return {x: p for x, p in zip(input_space, probabilities)}



    def expected_cost(self, algorithm: Callable,

                     distribution: dict,

                     n_trials: int = 1000) -> float:

        """

        计算算法的期望代价



        参数：

            algorithm: 算法函数

            distribution: 输入分布

            n_trials: 试验次数



        返回：期望代价

        """

        total_cost = 0.0



        inputs = list(distribution.keys())

        probs = list(distribution.values())



        for _ in range(n_trials):

            # 按分布采样

            x = random.choices(inputs, weights=probs, k=1)[0]

            cost = algorithm(x)

            total_cost += cost



        return total_cost / n_trials



    def lower_bound_via_yao(self, algorithms: List[Callable],

                           input_space: List,

                           distribution: dict) -> float:

        """

        使用Yao原理证明下界



        返回：下界估计

        """

        # 最小期望代价（最优随机算法）

        min_expected = float('inf')



        for algo in algorithms:

            expected = self.expected_cost(algo, distribution)

            min_expected = min(min_expected, expected)



        return min_expected





def yao_principle_example():

    """Yao原理示例"""

    print("=== Yao原理示例 ===")

    print()

    print("问题：寻找数组中最大元素")

    print()

    print("确定算法：必须比较所有 n-1 对")

    print("  期望比较次数 = n-1")

    print()

    print("随机算法：")

    print("  - 随机选择起始位置")

    print("  - 比较相邻元素直到找到最大")

    print("  - 期望比较次数 = n-1")

    print()

    print("Yao的下界：")

    print("  - 构造输入分布")

    print("  - 证明任何随机算法期望至少 n-1 比较")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Yao's minimax测试 ===\n")



    random.seed(42)



    yao = YaoFramework()



    # 输入空间：所有排列

    inputs = [[1, 2], [2, 1]]



    # 均匀分布

    dist = yao.construct_distribution(inputs, [0.5, 0.5])



    print(f"输入: {inputs}")

    print(f"分布: {dist}")

    print()



    # 定义算法

    def algo_linear(arr):

        """线性搜索最大"""

        max_val = arr[0]

        comparisons = 0

        for x in arr[1:]:

            if x > max_val:

                max_val = x

            comparisons += 1

        return comparisons



    # 计算期望代价

    expected = yao.expected_cost(algo_linear, dist, n_trials=1000)



    print(f"线性搜索期望比较次数: {expected:.3f}")



    print()

    yao_principle_example()



    print()

    print("说明：")

    print("  - Yao原理连接随机和分布")

    print("  - 用于证明下界")

    print("  - 是算法分析的重要工具")

