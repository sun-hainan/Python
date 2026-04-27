# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / set_cover



本文件实现 set_cover 相关的算法功能。

"""



from typing import List, Set, Dict





def greedy_set_cover(universe: Set, sets: List[Set]) -> List[int]:

    """

    贪心集合覆盖



    参数：

        universe: 全集

        sets: 集合列表



    返回：被选中的集合索引

    """

    covered = set()

    selected = []

    remaining_sets = list(range(len(sets)))



    while covered != universe:

        # 找覆盖最多未覆盖元素的集合

        best_idx = None

        best_covered = set()



        for idx in remaining_sets:

            new_covered = sets[idx] - covered

            if len(new_covered) > len(best_covered):

                best_covered = new_covered

                best_idx = idx



        if best_idx is None or len(best_covered) == 0:

            # 无法覆盖所有元素

            break



        selected.append(best_idx)

        covered |= sets[best_idx]

        remaining_sets.remove(best_idx)



    return selected





def lazy_greedy_set_cover(universe: Set, sets: List[Set], k: int) -> List[int]:

    """

    懒惰贪心集合覆盖



    每步选择边际收益最高的集合

    """

    covered = set()

    selected = []

    remaining_sets = list(range(len(sets)))

    remaining_sets_sets = [sets[i] for i in remaining_sets]



    while len(selected) < k and covered != universe:

        # 选择边际收益最高的

        best_idx = None

        best_gain = 0



        for i, s in enumerate(remaining_sets_sets):

            gain = len(s - covered)

            if gain > best_gain:

                best_gain = gain

                best_idx = i



        if best_gain == 0:

            break



        selected.append(remaining_sets[best_idx])

        covered |= remaining_sets_sets[best_idx]

        del remaining_sets_sets[best_idx]

        del remaining_sets[best_idx]



    return selected





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 集合覆盖测试 ===\n")



    # 例：选择教室覆盖学生

    students = {'Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Heidi'}



    classrooms = [

        {'Alice', 'Bob', 'Charlie'},

        {'David', 'Eve'},

        {'Charlie', 'David', 'Eve', 'Frank'},

        {'Alice', 'Bob', 'Grace', 'Heidi'},

        {'Frank', 'Grace'},

        {'Heidi'},

    ]



    print(f"学生集合: {len(students)} 人")

    print(f"教室数量: {len(classrooms)} 个")



    selected = greedy_set_cover(students, classrooms)



    print(f"\n贪心选择: 教室 {selected}")

    print(f"选中的教室数: {len(selected)}")



    covered = set()

    for idx in selected:

        covered |= classrooms[idx]

    print(f"覆盖的学生: {covered}")



    # 计算近似比

    opt_size = 3  # 已知最优解是3

    print(f"\n近似比: {len(selected)}/{opt_size} = {len(selected)/opt_size:.2f}")



    print("\n说明：")

    print("  - 集合覆盖是NP难问题")

    print("  - 贪心算法的近似比是 O(log n)")

    print("  - 实际应用：无线基站的部署、资源分配等")

