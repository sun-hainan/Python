# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / facility_location



本文件实现 facility_location 相关的算法功能。

"""



from typing import List, Dict, Tuple





def facility_location_lp(facilities: List[str], clients: List[str],

                         facility_cost: Dict[str, float],

                         assignment_cost: Dict[Tuple[str, str], float]) -> Dict:

    """

    简化版设施位置LP舍入



    返回：选中的设施和分配方案

    """

    # 简化：贪心选择

    selected = []

    assigned = {}



    remaining_clients = set(clients)

    remaining_facilities = list(facilities)



    while remaining_clients:

        # 找最好收益的设施（成本/能服务的客户数）

        best_facility = None

        best_ratio = float('inf')



        for f in remaining_facilities:

            # 简单启发式：贪心

            cost = facility_cost.get(f, 1.0)

            served = 0

            for c in remaining_clients:

                if (f, c) in assignment_cost or (c, f) in assignment_cost:

                    served += 1



            if served > 0:

                ratio = cost / served

                if ratio < best_ratio:

                    best_ratio = ratio

                    best_facility = f



        if best_facility is None:

            break



        selected.append(best_facility)

        remaining_facilities.remove(best_facility)



        # 分配该设施能服务的客户

        for c in list(remaining_clients):

            if (best_facility, c) in assignment_cost or (c, best_facility) in assignment_cost:

                assigned[c] = best_facility

                remaining_clients.discard(c)



    return {

        'selected_facilities': selected,

        'assignments': assigned,

        'total_cost': sum(facility_cost.get(f, 0) for f in selected)

    }





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 设施位置问题测试 ===\n")



    facilities = ['F1', 'F2', 'F3', 'F4']

    clients = ['C1', 'C2', 'C3', 'C4', 'C5']



    facility_cost = {'F1': 10, 'F2': 15, 'F3': 20, 'F4': 25}

    assignment_cost = {

        ('F1', 'C1'): 1, ('F1', 'C2'): 2, ('F1', 'C3'): 3,

        ('F2', 'C2'): 1, ('F2', 'C3'): 2, ('F2', 'C4'): 3,

        ('F3', 'C3'): 1, ('F3', 'C4'): 2, ('F3', 'C5'): 3,

        ('F4', 'C4'): 1, ('F4', 'C5'): 2,

    }



    result = facility_location_lp(facilities, clients, facility_cost, assignment_cost)



    print(f"选中的设施: {result['selected_facilities']}")

    print(f"分配方案: {result['assignments']}")

    print(f"总成本: {result['total_cost']}")



    print("\n说明：")

    print("  - 设施位置问题是经典的组合优化问题")

    print("  - 应用：仓库选址、数据中心部署")

    print("  - 近似算法保证 O(log n) 近似比")

