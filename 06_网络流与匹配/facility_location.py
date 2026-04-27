# -*- coding: utf-8 -*-

"""

算法实现：06_网络流与匹配 / facility_location



本文件实现 facility_location 相关的算法功能。

"""



import heapq

from collections import defaultdict





class FacilityLocation:

    """设施选址问题"""

    

    def __init__(self):

        self.facilities = []  # 设施列表

        self.clients = []  # 客户列表

        self.open_cost = {}  # facility_id -> opening cost

        self.service_cost = {}  # (facility, client) -> service cost

    

    def add_facility(self, fid, open_cost):

        """添加一个候选设施"""

        self.facilities.append(fid)

        self.open_cost[fid] = open_cost

    

    def add_client(self, cid):

        """添加一个客户"""

        self.clients.append(cid)

    

    def set_service_cost(self, fid, cid, cost):

        """设置设施到客户的连接成本"""

        self.service_cost[(fid, cid)] = cost

    

    def greedy_approximation(self):

        """

        贪心近似算法

        

        思想：

        1. 计算每个客户的"净成本" = service_cost - facility_benefit

        2. 每次选择使总成本增加最少的设施

        3. 重复直到没有设施能降低总成本

        

        近似比：O(log n)

        """

        open_facilities = set()

        assigned_clients = {}  # client -> assigned facility

        

        # 计算每个客户连接到每个设施的成本

        # 初始化：所有客户未分配

        

        remaining_clients = set(self.clients)

        remaining_facilities = set(self.facilities)

        

        total_cost = 0

        iteration = 0

        

        while remaining_clients and remaining_facilities:

            iteration += 1

            

            best_facility = None

            best_cost_delta = float('inf')

            best_assignments = []

            

            # 尝试每个候选设施

            for fid in remaining_facilities:

                facility_cost = self.open_cost[fid]

                assignments = []

                

                # 计算该设施能服务哪些剩余客户

                for cid in remaining_clients:

                    sc = self.service_cost.get((fid, cid), float('inf'))

                    assignments.append((cid, sc))

                

                # 按服务成本排序

                assignments.sort(key=lambda x: x[1])

                

                # 计算开设此设施带来的增量成本

                # = 设施开设成本 + 所有新客户服务成本 - 原成本（假设无穷大表示未服务）

                delta = facility_cost

                for cid, sc in assignments:

                    delta += sc

                

                if delta < best_cost_delta:

                    best_cost_delta = delta

                    best_facility = fid

                    best_assignments = assignments

            

            if best_facility is None or best_cost_delta == float('inf'):

                break

            

            # 开设最佳设施

            open_facilities.add(best_facility)

            remaining_facilities.discard(best_facility)

            total_cost += self.open_cost[best_facility]

            

            # 分配客户

            for cid, sc in best_assignments[:3]:  # 最多分配3个

                if cid in remaining_clients:

                    assigned_clients[cid] = best_facility

                    remaining_clients.discard(cid)

                    total_cost += sc

        

        return open_facilities, assigned_clients, total_cost

    

    def lagrangian_relaxation(self, lambda_val=1.0):

        """

        拉格朗日松弛近似

        

        将容量约束松弛，引入惩罚项 lambda * (opened - assigned)

        转化为贪心选择

        

        参数 lambda 控制设施开放和服务分配的权衡

        """

        # 计算每个设施的"调整成本"

        adjusted_cost = {}

        

        for fid in self.facilities:

            # 服务成本调整

            service_sum = sum(self.service_cost.get((fid, cid), 0) 

                           for cid in self.clients)

            adjusted_cost[fid] = self.open_cost[fid] - lambda_val * len(self.clients)

        

        # 按调整成本排序

        sorted_facilities = sorted(self.facilities, key=lambda f: adjusted_cost[f])

        

        # 选择调整成本为负的设施

        selected = [f for f in sorted_facilities if adjusted_cost[f] < 0]

        

        # 分配客户到最近的选择设施

        assigned = {}

        for cid in self.clients:

            best_fid = None

            best_sc = float('inf')

            for fid in selected:

                sc = self.service_cost.get((fid, cid), float('inf'))

                if sc < best_sc:

                    best_sc = sc

                    best_fid = fid

            if best_fid:

                assigned[cid] = best_fid

        

        return selected, assigned





def build_facility_location_example():

    """构建设施选址示例"""

    fl = FacilityLocation()

    

    # 添加设施

    fl.add_facility('A', 10)  # 设施A，开设成本10

    fl.add_facility('B', 15)  # 设施B，开设成本15

    fl.add_facility('C', 12)  # 设施C，开设成本12

    

    # 添加客户

    for c in ['c1', 'c2', 'c3', 'c4']:

        fl.add_client(c)

    

    # 设置服务成本（设施到客户的成本）

    costs = {

        ('A', 'c1'): 2, ('A', 'c2'): 3, ('A', 'c3'): 4, ('A', 'c4'): 5,

        ('B', 'c1'): 4, ('B', 'c2'): 2, ('B', 'c3'): 6, ('B', 'c4'): 3,

        ('C', 'c1'): 5, ('C', 'c2'): 4, ('C', 'c3'): 2, ('C', 'c4'): 6,

    }

    

    for (f, c), cost in costs.items():

        fl.set_service_cost(f, c, cost)

    

    return fl





if __name__ == "__main__":

    print("=" * 55)

    print("设施选址问题（Facility Location）")

    print("=" * 55)

    

    fl = build_facility_location_example()

    

    print("\n设施信息：")

    for fid in fl.facilities:

        print(f"  {fid}: 开设成本 = {fl.open_cost[fid]}")

    

    print("\n客户服务成本矩阵：")

    for fid in fl.facilities:

        row = [fl.service_cost.get((fid, c), 'N/A') for c in fl.clients]

        print(f"  {fid}: {row}")

    

    print("\n贪心近似算法：")

    open_f, assigned, total = fl.greedy_approximation()

    

    print(f"\n选择的设施: {open_f}")

    print(f"客户分配: {assigned}")

    print(f"总成本: {total}")

    

    # 验证

    facility_cost = sum(fl.open_cost[f] for f in open_f)

    service_cost = sum(fl.service_cost[(assigned[c], c)] for c in assigned)

    print(f"\n验证：设施成本 {facility_cost} + 服务成本 {service_cost} = {facility_cost + service_cost}")

