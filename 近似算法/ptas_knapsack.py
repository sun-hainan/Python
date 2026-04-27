# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / ptas_knapsack



本文件实现 ptas_knapsack 相关的算法功能。

"""



from typing import List, Tuple





def ptas_knapsack(items: List[Tuple[float, float]], capacity: float,

                 epsilon: float = 0.1) -> Tuple[float, List[int]]:

    """

    PTAS 背包近似算法



    参数：

        items: (重量, 价值) 列表

        capacity: 背包容量

        epsilon: 近似误差参数



    返回：(近似最优价值, 选中的物品)

    """

    n = len(items)



    if n == 0:

        return 0.0, []



    # 按价值降序

    sorted_items = sorted(enumerate(items), key=lambda x: x[1][1], reverse=True)



    # 找出高价值物品（不超过 1/epsilon 个）

    k = max(1, int(1.0 / epsilon))

    high_value = sorted_items[:min(k, n)]



    best_value = 0.0

    best_selected = []



    # 对高价值物品枚举所有子集（2^k）

    from itertools import combinations



    for r in range(len(high_value) + 1):

        for combo in combinations(range(len(high_value)), r):

            weight = 0.0

            value = 0.0

            selected = [high_value[i][0] for i in combo]

            indices = set(selected)



            for i in combo:

                idx, (w, v) = high_value[i]

                weight += w

                value += v



            if weight <= capacity:

                # 贪心添加剩余的小物品

                for i, (w, v) in items:

                    if i not in indices and weight + w <= capacity:

                        weight += w

                        value += v

                        selected.append(i)

                        indices.add(i)



                if value > best_value:

                    best_value = value

                    best_selected = selected



    return best_value, best_selected





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== PTAS背包测试 ===\n")



    import random

    random.seed(42)



    # 生成随机物品

    n = 30

    items = [(random.uniform(1, 20), random.uniform(10, 100)) for _ in range(n)]

    capacity = 100



    print(f"物品数: {n}, 容量: {capacity}")



    # PTAS 解

    value, selected = ptas_knapsack(items, capacity, epsilon=0.1)



    print(f"\nPTAS (ε=0.1) 解:")

    print(f"  总价值: {value:.2f}")

    print(f"  选中物品数: {len(selected)}")



    # 贪心对比

    from greedy_knapsack import greedy_knapsack

    greedy_value, _ = greedy_knapsack(items, capacity)

    print(f"\n贪心解: {greedy_value:.2f}")

    print(f"PTAS vs 贪心: +{(value - greedy_value)/greedy_value * 100:.1f}%")



    print("\n说明：")

    print("  - PTAS是理论上的近似方案")

    print("  - ε越小，近似比越好，但运行时间指数增长")

    print("  - 实际常用FPTAS（伪多项式）")

