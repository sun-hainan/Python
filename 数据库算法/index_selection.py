# -*- coding: utf-8 -*-

"""

算法实现：数据库算法 / index_selection



本文件实现 index_selection 相关的算法功能。

"""



from typing import List, Dict, Tuple, Set

from collections import defaultdict





class IndexSelector:

    """索引选择器"""



    def __init__(self):

        self.queries = []  # 查询工作负载

        self.indexes = {}  # 可选的索引



    def add_query(self, table: str, predicate: Dict, frequency: float = 1.0):

        """添加查询"""

        self.queries.append({

            'table': table,

            'predicate': predicate,

            'frequency': frequency

        })



    def estimate_query_cost_without_index(self, query: Dict) -> float:

        """估计无索引时的查询代价"""

        # 简化：全表扫描代价

        return 1000.0



    def estimate_query_cost_with_index(self, query: Dict, index: str) -> float:

        """估计有索引时的查询代价"""

        # 简化：索引扫描代价

        return 50.0



    def estimate_index_maintenance_cost(self, index: str, update_freq: float) -> float:

        """估计索引维护代价"""

        # 简化：更新频率越高，维护代价越大

        return 10.0 * update_freq



    def greedy_index_selection(self, max_indexes: int = 5) -> List[str]:

        """

        贪心索引选择



        每次选收益最高的索引

        """

        selected = []

        remaining = list(self.indexes.keys())



        for _ in range(max_indexes):

            best_idx = None

            best_benefit = -float('inf')



            for idx in remaining:

                # 计算添加该索引的收益

                benefit = 0.0

                for query in self.queries:

                    cost_before = self.estimate_query_cost_without_index(query)

                    cost_after = self.estimate_query_cost_with_index(query, idx)

                    benefit += (cost_before - cost_after) * query['frequency']



                # 减去维护代价

                update_cost = self.estimate_index_maintenance_cost(idx, 0.1)

                net_benefit = benefit - update_cost



                if net_benefit > best_benefit:

                    best_benefit = net_benefit

                    best_idx = idx



            if best_idx and best_benefit > 0:

                selected.append(best_idx)

                remaining.remove(best_idx)



        return selected





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 索引选择测试 ===\n")



    selector = IndexSelector()



    # 添加查询工作负载

    selector.add_query({'table': 'Orders', 'column': 'customer_id'}, frequency=0.4)

    selector.add_query({'table': 'Orders', 'column': 'order_date'}, frequency=0.3)

    selector.add_query({'table': 'OrderItems', 'column': 'product_id'}, frequency=0.2)

    selector.add_query({'table': 'Customers', 'column': 'region'}, frequency=0.1)



    # 可选索引

    selector.indexes = {

        'idx_orders_customer': {'table': 'Orders', 'column': 'customer_id'},

        'idx_orders_date': {'table': 'Orders', 'column': 'order_date'},

        'idx_orderitems_product': {'table': 'OrderItems', 'column': 'product_id'},

        'idx_customers_region': {'table': 'Customers', 'column': 'region'},

    }



    selected = selector.greedy_index_selection(max_indexes=3)



    print(f"可选索引: {list(selector.indexes.keys())}")

    print(f"\n贪心选择的索引: {selected}")



    total_benefit = 0

    for idx in selected:

        for query in selector.queries:

            cost_before = selector.estimate_query_cost_without_index(query)

            cost_after = selector.estimate_query_cost_with_index(query, idx)

            benefit = (cost_before - cost_after) * query['frequency']

            total_benefit += benefit



    print(f"总查询收益: {total_benefit:.2f}")



    print("\n说明：")

    print("  - 索引选择是DB自动优化的核心")

    print("  - PostgreSQL的pg_stat_user_indexes视图帮助分析")

    print("  - 实际系统考虑更多因素：统计信息、相关列等")

