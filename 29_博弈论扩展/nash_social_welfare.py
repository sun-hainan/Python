# -*- coding: utf-8 -*-

"""

算法实现：博弈论扩展 / nash_social_welfare



本文件实现 nash_social_welfare 相关的算法功能。

"""



import random

from typing import List, Callable





class NashWelfare:

    """Nash社会福利函数"""



    @staticmethod

    def welfare(allocation: List[float]) -> float:

        """

        计算Nash福利



        参数：

            allocation: 各人收入列表



        返回：min(allocation)

        """

        return min(allocation) if allocation else 0.0



    @staticmethod

    def utilitarian_welfare(allocation: List[float]) -> float:

        """

        功利主义福利：总和最大化



        W = Σ x_i

        """

        return sum(allocation)



    @staticmethod

    def egalitarian_welfare(allocation: List[float]) -> float:

        """

        罗尔斯主义福利：最大化最小收入



        W = min(x_i)

        """

        return min(allocation)



    @staticmethod

    def generalized_welfare(allocation: List[float], alpha: float) -> float:

        """

        广义福利函数



        alpha=1: 功利主义

        alpha=0: 罗尔斯主义

        -alpha < 1: 在两者之间

        """

        n = len(allocation)

        if alpha == 1:

            return sum(allocation)

        else:

            # (1/n) * Σ x_i^(1-alpha) 当alpha != 1

            return (sum(x ** (1 - alpha) for x in allocation) / n) ** (1 / (1 - alpha))





class SocialChoice:

    """社会选择"""



    def __init__(self, n_agents: int, preference_functions: List[Callable]):

        """

        参数：

            n_agents: 代理人数

            preference_functions: 每个代理的效用函数

        """

        self.n_agents = n_agents

        self.preferences = preference_functions



    def rank_allocations(self, allocations: List[List[float]]) -> List[int]:

        """

       对社会分配排序



        返回：按Nash福利降序的分配索引

        """

        nw = NashWelfare()

        welfare_scores = [(nw.welfare(a), i) for i, a in enumerate(allocations)]

        welfare_scores.sort(key=lambda x: x[0], reverse=True)

        return [idx for _, idx in welfare_scores]





def comparison_example():

    """功利主义 vs 罗尔斯主义"""

    print("=== 功利主义 vs 罗尔斯主义 ===\n")



    allocations = [

        [100, 100, 100],      # 完全平等

        [300, 0, 0],          # 极度不平等

        [50, 150, 100],        # 中等不平等

        [33, 33, 34],         # 几乎平等

    ]



    nw = NashWelfare()



    print("分配方案:")

    for i, a in enumerate(allocations):

        util = nw.utilitarian_welfare(a)

        nash = nw.egalitarian_welfare(a)

        print(f"  {i+1}. {a}: 功利主义={util}, Nash(最小收入)={nash}")



    print()

    print("按Nash福利排序: 1 > 4 > 3 > 2")

    print("按功利主义排序: 2 > 1 > 3 > 4")





def poverty_minimization():

    """贫困最小化"""

    print()

    print("=== 贫困最小化 ===")

    print()

    print("罗尔斯主义（最大化最小收入）：")

    print("  - 关注最弱势群体")

    print("  - 可能牺牲整体效率")

    print()

    print("例子：")

    print("  政策A：100人每人得到10，总和1000")

    print("  政策B：99人每人得到20，1人得到0，总和1980")

    print()

    print("Nash选择B，因为最大化最小收入")

    print("功利主义也选择B")

    print("但第101人会反对B（得到了0）")





def efficiency_tradeoff():

    """效率与公平的权衡"""

    print()

    print("=== 效率-公平权衡 ===")

    print()

    print("GDP vs 贫困率：")

    print("  - 功利主义：选GDP最高的")

    print("  - 罗尔斯主义：选贫困率最低的")

    print()

    print("实际政策需要在两者之间找平衡")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    comparison_example()

    poverty_minimization()

    efficiency_tradeoff()



    print("\n说明：")

    print("  - Nash福利关注最弱势群体")

    print("  - 功利主义关注整体效用")

    print("  - 实际选择取决于价值观")

