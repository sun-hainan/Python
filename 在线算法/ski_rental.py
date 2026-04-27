# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / ski_rental



本文件实现 ski_rental 相关的算法功能。

"""



import random

from typing import Tuple





class SkiRental:

    """滑雪租借问题"""



    def __init__(self, rent_cost: int, buy_cost: int):

        """

        参数：

            rent_cost: 每日租金

            buy_cost: 购买价格

        """

        self.rent_cost = rent_cost

        self.buy_cost = buy_cost



        # 最优阈值：租 buy_cost / rent_cost 天后买

        self.threshold = buy_cost // rent_cost



    def online_decision(self, day: int, total_rent: int) -> str:

        """

        在线决策



        参数：

            day: 当前天数

            total_rent: 已付租金



        返回：决策 "rent" 或 "buy"

        """

        # 如果已经租了 threshold 天，买

        if day >= self.threshold:

            return "buy"

        return "rent"



    def optimal_cost(self, days: int) -> Tuple[int, str]:

        """

        计算最优成本



        返回：(成本, 策略)

        """

        rent_cost = days * self.rent_cost

        buy_cost = self.buy_cost



        if rent_cost < buy_cost:

            return rent_cost, "rent"

        return buy_cost, "buy"



    def competitive_ratio(self) -> float:

        """

        竞争比（确定性在线算法的最坏情况）



        返回：竞争比

        """

        # 最优策略是最小化 max(rent, buy)

        # 竞争比 = worst_case / optimal ≤ rent / (buy - rent) 当 buy/rent > 1 时

        # 简化计算



        if self.threshold == 0:

            return 1.0



        # 竞争比上界

        worst_case = self.rent_cost * self.threshold

        optimal = self.rent_cost * self.threshold  # 在临界点两者相等



        return worst_case / optimal if optimal > 0 else 1.0





def online_algorithm_design():

    """在线算法设计原则"""

    print("=== 在线算法设计 ===")

    print()

    print("滑雪租借问题的洞察：")

    print(f"  - 阈值: {self.threshold} 天")

    print("  - 在阈值前租，阈值后买")

    print("  - 竞争比 ≈ 2 - 1/threshold")

    print()

    print("在线算法设计原则：")

    print("  - 保守 vs 冒险")

    print("  - 确定性 vs 随机")

    print("  - 竞争分析")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 滑雪租借问题测试 ===\n")



    rent_cost = 10

    buy_cost = 100



    ski = SkiRental(rent_cost, buy_cost)



    print(f"日租金: ${rent_cost}")

    print(f"购买价: ${buy_cost}")

    print(f"阈值: {ski.threshold} 天")

    print()



    # 测试不同天数

    for days in [5, 10, 15, 20, 30]:

        cost, strategy = ski.optimal_cost(days)

        print(f"  {days}天: 成本=${cost}, 策略={strategy}")



    print()

    print(f"竞争比: {ski.competitive_ratio():.2f}")



    print()

    print("说明：")

    print("  - 滑雪租借是在线决策经典问题")

    print("  - 有确定性最优策略")

    print("  - 竞争比分析是核心工具")

