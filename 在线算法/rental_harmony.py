# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / rental_harmony



本文件实现 rental_harmony 相关的算法功能。

"""



from typing import List, Dict, Tuple

import random





class RentalHarmony:

    """租屋和谐算法"""



    def __init__(self, n_rooms: int, n_players: int):

        """

        参数：

            n_rooms: 房间数

            n_players: 玩家数

        """

        self.n_rooms = n_rooms

        self.n_players = n_players



    def generate_preferences(self) -> List[List[int]]:

        """

        生成随机偏好



        返回：偏好矩阵

        """

        random.seed(42)

        preferences = []



        for _ in range(self.n_players):

            pref = list(range(self.n_rooms))

            random.shuffle(pref)

            preferences.append(pref)



        return preferences



    def greedy_allocation(self, preferences: List[List[int]],

                        room_prices: List[float]) -> Dict[int, int]:

        """

        贪婪分配



        参数：

            preferences: 玩家偏好（从高到低）

            room_prices: 房间价格



        返回：分配 (player_id -> room_id)

        """

        allocation = {}

        available_rooms = set(range(self.n_rooms))



        for player in range(self.n_players):

            # 选择最高偏好的可用房间

            for room in preferences[player]:

                if room in available_rooms:

                    allocation[player] = room

                    available_rooms.remove(room)

                    break



        return allocation



    def calculate_rent(self, allocation: Dict[int, int],

                     room_prices: List[float],

                     preferences: List[List[int]]) -> Dict[int, float]:

        """

        计算租金分配



        参数：

            allocation: 房间分配

            room_prices: 房间价格

            preferences: 玩家偏好



        返回：每个玩家应付租金

        """

        rent = {}



        for player, room in allocation.items():

            # 基础价格

            base_price = room_prices[room]



            # 根据偏好调整（更喜欢的房间付更多）

            pref_rank = preferences[player].index(room)

            adjustment = pref_rank * 0.01 * base_price



            rent[player] = base_price + adjustment



        return rent





def nash_equilibrium_rental():

    """Nash均衡的租屋分配"""

    print("=== 租屋的Nash均衡 ===")

    print()

    print("问题：")

    print("  - 房间分配 + 租金分摊")

    print("  - 每个人不能通过单方面改变获益")

    print()

    print("性质：")

    print("  - 存在性：总是存在")

    print("  - 唯一性：在某些条件下唯一")

    print()

    print("算法：")

    print("  - 拍卖-based 方法")

    print("  - 迭代改进")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 租屋和谐算法测试 ===\n")



    n_rooms = 4

    n_players = 4



    rental = RentalHarmony(n_rooms, n_players)



    # 生成偏好

    preferences = rental.generate_preferences()



    print("玩家偏好（从高到低）：")

    for i, pref in enumerate(preferences):

        print(f"  玩家 {i}: {pref}")



    # 房间价格

    room_prices = [1000, 1500, 1200, 800]

    print(f"\n房间价格: {room_prices}")

    print()



    # 分配

    allocation = rental.greedy_allocation(preferences, room_prices)



    print("分配结果：")

    for player, room in allocation.items():

        print(f"  玩家 {player} -> 房间 {room} (价格 {room_prices[room]})")



    # 计算租金

    rent = rental.calculate_rent(allocation, room_prices, preferences)



    print("\n租金分摊：")

    for player, amount in rent.items():

        print(f"  玩家 {player}: ${amount:.2f}")



    print()

    nash_equilibrium_rental()



    print()

    print("说明：")

    print("  - 租屋和谐是公平分配问题")

    print("  - 涉及房间分配和租金分摊")

    print("  - 可用博弈论分析")

