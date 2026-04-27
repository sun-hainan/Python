# -*- coding: utf-8 -*-

"""

算法实现：组合优化 / submodular_optimization



本文件实现 submodular_optimization 相关的算法功能。

"""



import random

from typing import List, Set, Callable





class SubmodularFunction:

    """子模函数基类"""



    def value(self, S: Set[int]) -> float:

        """计算f(S)"""

        raise NotImplementedError



    def marginal_gain(self, S: Set[int], v: int) -> float:

        """计算加入v的边际收益 f(S ∪ {v}) - f(S)"""

        return self.value(S | {v}) - self.value(S)





class CoverageFunction(SubmodularFunction):

    """覆盖函数（经典的子模函数）"""



    def __init__(self, sets: List[Set[int]]):

        """

        参数：

            sets: 集合列表，f(S) = |∪_{i∈S} sets[i]|

        """

        self.sets = sets



    def value(self, S: Set[int]) -> float:

        """覆盖的元素数量"""

        covered = set()

        for i in S:

            covered |= self.sets[i]

        return len(covered)





class FacilityLocation(SubmodularFunction):

    """设施位置函数"""



    def __init__(self, similarity_matrix, user_rep_indices):

        """

        参数：

            similarity_matrix: 用户-设施相似度矩阵

            user_rep_indices: 用户代表索引

        """

        self.sim = similarity_matrix

        self.users = user_rep_indices

        self.n_facilities = len(similarity_matrix)



    def value(self, S: Set[int]) -> float:

        """每个用户到最近设施的相似度之和"""

        total = 0.0

        for u in self.users:

            best = 0.0

            for f in S:

                best = max(best, self.sim[u][f])

            total += best

        return total





class LazyGreedy:

    """懒贪心优化"""



    def __init__(self, func: SubmodularFunction, k: int):

        """

        参数：

            func: 子模函数

            k: 选择元素数量

        """

        self.func = func

        self.k = k



    def maximize(self, elements: List[int]) -> Set[int]:

        """

        贪心最大化（1 - 1/e 近似）



        参数：

            elements: 可选元素列表



        返回：选中的k个元素

        """

        S = set()

        priorities = []  # (marginal_gain, element)



        # 初始化优先级

        for e in elements:

            mg = self.func.marginal_gain(S, e)

            priorities.append((self.k - mg, e))  # 用负值实现最大堆



        # 转换为最大堆

        from heapq import nlargest

        priorities.sort(reverse=True)



        while len(S) < self.k:

            # 获取最高边际收益的元素

            mg_e = priorities.pop(0)

            mg, e = self.k - mg_e[0], mg_e[1]



            # 验证边际收益

            actual_mg = self.func.marginal_gain(S, e)



            if abs(actual_mg - mg) < 1e-6:

                S.add(e)

            else:

                # 更新优先级

                priorities.append((self.k - actual_mg, e))

                priorities.sort(reverse=True)



        return S





def card_constrained():

    """基数约束下的子模最大化"""

    print("=== 基数约束子模最大化 ===")

    print()

    print("问题：")

    print("  max f(S)  s.t. |S| ≤ k")

    print()

    print("贪心算法：")

    print("  1. 初始化 S = ∅")

    print("  2. 选择使 f(S ∪ {v}) 最大的 v")

    print("  3. 重复直到 |S| = k")

    print()

    print("近似比：1 - 1/e ≈ 0.632")

    print()

    print("应用：")

    print("  - 影响力最大化：选择k个种子用户")

    print("  - 传感器放置：选择k个传感器位置")

    print("  - 文本摘要：选择k个句子")





def continuous_greedy():

    """连续贪心算法"""

    print()

    print("=== 连续贪心（针对冠函数） ===")

    print()

    print("步骤：")

    print("  1. 映射到多面体：计算域的凸包")

    print("  2. 分数解：x = (1/t) * Σ_{i=1}^t S_i")

    print("  3. 积分：∫_0^1 gradient(x) dx")

    print("  4. 舍入：随机化舍入得到离散解")

    print()

    print("舍入方法：")

    print("  - Swap rounding（交换舍入）")

    print("  - Pipage rounding")

    print("  - 成本效益舍入")





def submodular_minimization():

    """子模最小化"""

    print()

    print("=== 子模最小化 ===")

    print()

    print("问题：min f(S)")

    print()

    print("方法：")

    print("  - 椭球法（多项式时间）")

    print("  - 割平面法")

    print("  - 坐标下降")

    print()

    print("应用：")

    print("  - 聚类（最小化差异）")

    print("  - 图像分割")

    print("  - 马尔科夫随机场")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 子模优化测试 ===\n")



    # 示例：覆盖函数

    sets = [

        {1, 2, 3},

        {2, 3, 4},

        {3, 4, 5},

        {4, 5, 6},

    ]



    cov = CoverageFunction(sets)

    k = 2



    print(f"集合系统：{len(sets)}个集合")

    print(f"目标：选择{k}个集合覆盖最多元素")

    print()



    # 懒贪心

    elements = list(range(len(sets)))

    greedy = LazyGreedy(cov, k)

    result = greedy.maximize(elements)



    print(f"贪心选择：{result}")

    print(f"覆盖元素数：{cov.value(result)}")



    # 验证子模性

    print()

    print("验证子模性：")

    S, T = {0}, {0, 1}

    v = 2



    f_S = cov.value(S)

    f_T = cov.value(T)

    f_Sv = cov.value(S | {v})

    f_Tv = cov.value(T | {v})



    mg_S = f_Sv - f_S

    mg_T = f_Tv - f_T



    print(f"  f({{0}} ∪ {{2}}) - f({{0}}) = {mg_S:.1f}")

    print(f"  f({{0,1}} ∪ {{2}}) - f({{0,1}}) = {mg_T:.1f}")

    print(f"  子模性：{mg_S >= mg_T} (应为True)")



    card_constrained()

    continuous_greedy()

    submodular_minimization()



    print()

    print("说明：")

    print("  - 子模函数在组合优化中很重要")

    print("  - 贪心算法给出1-1/e近似")

    print("  - 实际应用中效果通常更好")

