# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / list_update



本文件实现 list_update 相关的算法功能。

"""



from typing import List, Tuple

import random





class ListUpdate:

    """列表更新算法"""



    def __init__(self, initial_list: List[int]):

        """

        参数：

            initial_list: 初始列表顺序

        """

        self.initial_list = initial_list.copy()

        self.list = initial_list.copy()

        self.access_cost = 0



    def mtf(self, item: int) -> int:

        """

        Move-to-Front策略



        参数：

            item: 访问的元素



        返回：成本

        """

        # 找到元素位置

        pos = self.list.index(item)



        # 成本 = 位置 + 1（从1开始计数）

        cost = pos + 1



        # 移动到前面

        self.list.pop(pos)

        self.list.insert(0, item)



        self.access_cost += cost

        return cost



    def transpose(self, item: int) -> int:

        """

        Transpose策略（与前一个交换）



        参数：

            item: 访问的元素



        返回：成本

        """

        pos = self.list.index(item)



        cost = pos + 1



        # 与前一个交换

        if pos > 0:

            self.list[pos], self.list[pos-1] = self.list[pos-1], self.list[pos]



        self.access_cost += cost

        return cost



    def fc(self, item: int) -> int:

        """

        Frequency Count策略



        参数：

            item: 访问的元素



        返回：成本

        """

        pos = self.list.index(item)



        cost = pos + 1



        # 频率增加（简化：不真正重新排序）

        # 实际应该按频率维护有序列表



        self.access_cost += cost

        return cost



    def reset(self) -> None:

        """重置到初始状态"""

        self.list = self.initial_list.copy()

        self.access_cost = 0



    def simulate(self, access_sequence: List[int], strategy: str = 'mtf') -> dict:

        """

        模拟访问序列



        返回：模拟结果

        """

        costs = []



        for item in access_sequence:

            if strategy == 'mtf':

                cost = self.mtf(item)

            elif strategy == 'transpose':

                cost = self.transpose(item)

            elif strategy == 'fc':

                cost = self.fc(item)

            else:

                cost = 0



            costs.append(cost)



        return {

            'total_cost': self.access_cost,

            'costs': costs,

            'n_accesses': len(access_sequence)

        }





def list_update_competitive():

    """列表更新竞争比"""

    print("=== 列表更新竞争比 ===")

    print()

    print("MTF（移动到前面）：")

    print("  - 竞争比：2")

    print("  - 最坏情况2倍最优")

    print()

    print("Transpose：")

    print("  - 无界竞争比")

    print("  - 可能非常差")

    print()

    print("Frequency Count：")

    print("  - 竞争比：O(log n)")

    print("  - 介于MTF和Transpose之间")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 列表更新测试 ===\n")



    # 初始列表

    initial = [1, 2, 3, 4, 5]



    # 访问序列

    accesses = [3, 1, 4, 2, 3, 5, 1, 2, 3, 4]



    print(f"初始列表: {initial}")

    print(f"访问序列: {accesses}")

    print()



    # MTF策略

    lu = ListUpdate(initial)

    result_mtf = lu.simulate(accesses, 'mtf')



    print(f"MTF成本: {result_mtf['total_cost']}")

    print(f"  列表: {lu.list}")

    print()



    # Transpose策略

    lu.reset()

    result_trans = lu.simulate(accesses, 'transpose')



    print(f"Transpose成本: {result_trans['total_cost']}")

    print(f"  列表: {lu.list}")

    print()



    # 比较

    print("成本比较：")

    print(f"  MTF: {result_mtf['total_cost']}")

    print(f"  Transpose: {result_trans['total_cost']}")



    print()

    list_update_competitive()



    print()

    print("说明：")

    print("  - MTF是2竞争的在线算法")

    print("  - 实际中表现很好")

    print("  - 是访问局部性的体现")

