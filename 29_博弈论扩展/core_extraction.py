# -*- coding: utf-8 -*-

"""

算法实现：博弈论扩展 / core_extraction



本文件实现 core_extraction 相关的算法功能。

"""



from typing import List, Tuple, Set





class CooperativeGame:

    """合作博弈"""



    def __init__(self, n_players: int, value_function):

        """

        参数：

            n_players: 玩家数量

            value_function: 联盟值函数 v(S) -> 数值

        """

        self.n_players = n_players

        self.value = value_function



    def is_in_core(self, allocation: List[float]) -> bool:

        """

        检查分配是否在Core中



        返回：是否满足Core条件

        """

        # 条件1：效率性

        total_value = sum(allocation)

        if abs(total_value - self.value(set(range(self.n_players)))) > 1e-6:

            return False



        # 条件2：个人理性

        for i in range(self.n_players):

            if allocation[i] < self.value({i}):

                return False



        # 条件3：没有coalition能改进

        from itertools import combinations



        for size in range(2, self.n_players + 1):

            for coalition in combinations(range(self.n_players), size):

                coalition_set = set(coalition)



                # coalition的值

                coalition_value = self.value(coalition_set)



                # coalition中每个人能得到的最大

                coalition_allocation = sum(allocation[i] for i in coalition)

                if coalition_allocation < coalition_value - 1e-6:

                    return False



        return True



    def find_core(self) -> List[List[float]]:

        """

        尝试找出Core中的分配



        简化版：只检查一些候选分配

        """

        candidates = []



        # 均匀分配

        均匀 = [self.value({i}) for i in range(self.n_players)]

        total = sum(均匀)



        if self.is_in_core(均匀):

            candidates.append(均匀)



        return candidates





def simple_coalition_game():

    """简单合作博弈"""

    print("=== 简单合作博弈 Core ===\n")



    n = 3



    # 定义值函数

    # v({i}) = 1 (单干收益)

    # v({i,j}) = 4 (两人合作)

    # v({1,2,3}) = 9 (三人合作)



    def v(s: Set[int]) -> float:

        if len(s) == 0:

            return 0

        if len(s) == 1:

            return 1

        if len(s) == 2:

            return 4

        if len(s) == 3:

            return 9

        return 0



    game = CooperativeGame(n, v)



    # 检查均匀分配

    allocation = [3, 3, 3]

    print(f"分配 {allocation}: ", end="")

    print("在Core中" if game.is_in_core(allocation) else "不在Core中")



    allocation = [4, 2.5, 2.5]

    print(f"分配 {allocation}: ", end="")

    print("在Core中" if game.is_in_core(allocation) else "不在Core中")



    allocation = [5, 2, 2]

    print(f"分配 {allocation}: ", end="")

    print("在Core中" if game.is_in_core(allocation) else "不在Core中")



    print("\n说明：")

    print("  - [3,3,3]: 满足所有条件，在Core中")

    print("  - [5,2,2]: 两人联盟{1,2}只得到4，但分配给他们5+2=7，不合理")

    print("  - Core可能为空（如简单多数投票博弈）")





def market_game():

    """市场交易博弈"""

    print("\n=== 市场交易 Core ===\n")



    # 简化：两个买家，一个卖家

    # 卖家成本0，买家估值不同

    # 任何在[成本, 最大估值]之间的价格都可以成交



    print("场景：卖家有一件商品，成本$0")

    print("      买家A估值$80，买家B估值$50")

    print()



    print("可能的分配：")

    print("  - 不交易：各得0")

    print("  - A买：卖家得[0,80]，A得[0,0]")

    print("  - B买：卖家得[0,50]，B得[0,0]")

    print()



    print("Core中的分配：")

    print("  - {A买,价格$60}: [卖家60, A20, B0] 是一种Core分配")

    print("  - 任何[卖家50-80]的价格都可能形成Core")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    simple_coalition_game()

    market_game()



    print("\n说明：")

    print("  - Core是合作博弈的核心解概念")

    print("  - 满足稳定性：没人能形成更好的联盟")

    print("  - 但Core可能为空")

