# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / greedy_knapsack



本文件实现 greedy_knapsack 相关的算法功能。

"""



from typing import List, Tuple





def greedy_knapsack(items: List[Tuple[float, float]], capacity: float) -> Tuple[float, List[int]]:

    """

    贪心背包近似算法



    参数：

        items: (重量, 价值) 列表

        capacity: 背包容量



    返回：(总价值, 被选中的物品索引)

    """

    n = len(items)



    # 计算单位价值

    ratios = [(i, items[i][1] / items[i][0], items[i]) for i in range(n)]



    # 按单位价值降序排列

    ratios.sort(key=lambda x: x[1], reverse=True)



    total_value = 0.0

    total_weight = 0.0

    selected = []



    for idx, ratio, (weight, value) in ratios:

        if total_weight + weight <= capacity:

            total_weight += weight

            total_value += value

            selected.append(idx)



    return total_value, selected





def fractional_knapsack(items: List[Tuple[float, float]], capacity: float) -> Tuple[float, List[Tuple[int, float]]]:

    """

    分数背包（可以分割物品）



    这是多项式时间可解的

    """

    ratios = [(i, items[i][1] / items[i][0], items[i]) for i in range(len(items))]

    ratios.sort(key=lambda x: x[1], reverse=True)



    total_value = 0.0

    total_weight = 0.0

    selected = []



    for idx, ratio, (weight, value) in ratios:

        if total_weight + weight <= capacity:

            total_weight += weight

            total_value += value

            selected.append((idx, 1.0))

        else:

            # 分割

            remaining = capacity - total_weight

            fraction = remaining / weight

            total_value += value * fraction

            selected.append((idx, fraction))

            break



    return total_value, selected





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 贪心背包测试 ===\n")



    items = [

        (10, 60),   # 物品0: 重量10, 价值60

        (20, 100),  # 物品1: 重量20, 价值100

        (30, 120),  # 物品2: 重量30, 价值120

    ]

    capacity = 50



    print(f"物品 (重量, 价值): {items}")

    print(f"容量: {capacity}")



    # 贪心解

    value, selected = greedy_knapsack(items, capacity)

    print(f"\n贪心近似解:")

    print(f"  总价值: {value}")

    print(f"  选中的物品: {selected}")

    print(f"  总重量: {sum(items[i][0] for i in selected)}")



    # 分数背包（最优解）

    frac_value, frac_selected = fractional_knapsack(items, capacity)

    print(f"\n分数背包最优解: {frac_value}")



    # 简单上界

    print(f"\n近似比分析:")

    print(f"  贪心值 / 最优值 ≈ {value/frac_value:.2f}")



    print("\n说明：")

    print("  - 0-1背包是NP难问题")

    print("  - 贪心解是1/2-近似")

    print("  - 更好的近似需要DP或更复杂算法")

