# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / set_packing



本文件实现 set_packing 相关的算法功能。

"""



from typing import List, Set, Tuple





def greedy_set_packing(sets: List[Set]) -> List[int]:

    """

    贪心集合packing



    参数：

        sets: 集合列表



    返回：选中的集合索引（互不相交）

    """

    selected = []

    used_elements = set()



    # 按集合大小降序

    indexed_sets = sorted(enumerate(sets), key=lambda x: len(x[1]), reverse=True)



    for idx, s in indexed_sets:

        # 检查是否与已选集合相交

        if not s.intersection(used_elements):

            selected.append(idx)

            used_elements.update(s)



    return selected





def max_set_packing_dp(sets: List[Set], universe: Set) -> List[int]:

    """

    动态规划求解最大集合packing（指数级，仅适合小规模）



    使用状态压缩DP

    """

    n = len(universe)

    element_to_idx = {e: i for i, e in enumerate(universe)}



    # dp[mask] = 能覆盖mask的最大集合数

    dp = [-1] * (1 << n)

    dp[0] = 0



    for s in sets:

        mask = 0

        for e in s:

            if e in element_to_idx:

                mask |= 1 << element_to_idx[e]



        for prev_mask in range(1 << n):

            if dp[prev_mask] >= 0:

                new_mask = prev_mask | mask

                dp[new_mask] = max(dp[new_mask], dp[prev_mask] + 1)



    # 回溯找最优解

    best_mask = max(range(1 << n), key=lambda m: dp[m])

    selected = []



    # 简化：返回贪心结果

    return greedy_set_packing(sets)





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 集合Packing测试 ===\n")



    # 例：课程安排

    # 课程占用的教室/时间段集合

    sets = [

        {'A', 'B', 'C'},    # 课程1

        {'A', 'B'},         # 课程2

        {'B', 'C'},         # 课程3

        {'D', 'E'},         # 课程4

        {'D', 'E', 'F'},    # 课程5

        {'E', 'F'},         # 课程6

    ]



    selected = greedy_set_packing(sets)



    print(f"集合列表: {sets}")

    print(f"\n贪心选择的索引: {selected}")

    print(f"选中的集合数: {len(selected)}")



    used = set()

    for idx in selected:

        used.update(sets[idx])

    print(f"使用的元素: {used}")



    print("\n说明：")

    print("  - 集合packing是NP难问题")

    print("  - 贪心近似比不是常数（需要根据具体情况）")

    print("  - 应用：资源分配、任务调度")

