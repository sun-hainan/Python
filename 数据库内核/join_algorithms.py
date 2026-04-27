# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / join_algorithms



本文件实现 join_algorithms 相关的算法功能。

"""



from typing import List, Callable, Any, Optional, Tuple

from dataclasses import dataclass



# 数据记录（模拟元组）

@dataclass

class Record:

    key: Any              # 连接键

    payload: Any          # 负载数据

    table_name: str = ""  # 来源表名

    

    def __repr__(self):

        return f"Record(key={self.key}, payload={self.payload})"





class NestedLoopJoin:

    """

    嵌套循环连接（Nested Loop Join）

    外层表遍历，内层表建立索引或全扫描

    适用于：小表驱动大表、有索引的场景

    """

    

    def __init__(self, outer_table: List[Record], inner_table: List[Record], 

                 key_extractor: Callable[[Record], Any]):

        self.outer_table = outer_table    # 外层表（驱动表，通常小表）

        self.inner_table = inner_table    # 内层表（被驱动表）

        self.key_extractor = key_extractor  # 键提取函数

    

    def join(self) -> List[Tuple[Record, Record]]:

        """

        执行嵌套循环连接

        返回: [(外层记录, 内层记录), ...]

        """

        results = []

        

        # 外层循环：遍历外层表每条记录

        for outer_rec in self.outer_table:

            outer_key = self.key_extractor(outer_rec)

            

            # 内层循环：遍历内层表寻找匹配

            for inner_rec in self.inner_table:

                inner_key = self.key_extractor(inner_rec)

                

                if outer_key == inner_key:

                    results.append((outer_rec, inner_rec))

        

        return results

    

    def join_with_index(self, inner_index: dict) -> List[Tuple[Record, Record]]:

        """

        使用索引的嵌套循环连接

        inner_index: {key -> [records]} 内层表的索引

        """

        results = []

        

        for outer_rec in self.outer_table:

            outer_key = self.key_extractor(outer_rec)

            

            # 通过索引快速查找

            if outer_key in inner_index:

                for inner_rec in inner_index[outer_key]:

                    results.append((outer_rec, inner_rec))

        

        return results





class HashJoin:

    """

    Hash连接（Hash Join）

    分为Build阶段（构建Hash表）和Probe阶段（探查）

    适用于：等值连接、大表连接

    """

    

    def __init__(self, build_table: List[Record], probe_table: List[Record],

                 key_extractor: Callable[[Record], Any], 

                 num_buckets: int = 100):

        self.build_table = build_table  # 构建表（小表）

        self.probe_table = probe_table  # 探查表（大表）

        self.key_extractor = key_extractor

        self.num_buckets = num_buckets  # Hash桶数量

    

    def _hash_function(self, key: Any) -> int:

        """Hash函数"""

        return hash(key) % self.num_buckets

    

    def join(self) -> List[Tuple[Record, Record]]:

        """执行Hash连接"""

        results = []

        

        # ========== Build阶段 ==========

        hash_table = {}  # {bucket_id: [(key, record), ...]}

        

        for rec in self.build_table:

            key = self.key_extractor(rec)

            bucket = self._hash_function(key)

            

            if bucket not in hash_table:

                hash_table[bucket] = []

            hash_table[bucket].append((key, rec))

        

        # ========== Probe阶段 ==========

        for probe_rec in self.probe_table:

            probe_key = self.key_extractor(probe_rec)

            bucket = self._hash_function(probe_key)

            

            if bucket in hash_table:

                for build_key, build_rec in hash_table[bucket]:

                    if build_key == probe_key:

                        results.append((build_rec, probe_rec))

        

        return results

    

    def join_parallel(self, num_workers: int = 4) -> List[Tuple[Record, Record]]:

        """

        并行Hash连接（简化版）

        将Probe表分片，多线程并行探查

        """

        import threading

        results = []

        results_lock = threading.Lock()

        

        # 将Probe表分片

        chunk_size = max(1, len(self.probe_table) // num_workers)

        chunks = [self.probe_table[i:i+chunk_size] 

                  for i in range(0, len(self.probe_table), chunk_size)]

        

        # Build阶段（共享）

        hash_table = {}

        for rec in self.build_table:

            key = self.key_extractor(rec)

            bucket = self._hash_function(key)

            if bucket not in hash_table:

                hash_table[bucket] = []

            hash_table[bucket].append((key, rec))

        

        def probe_chunk(chunk: List[Record]):

            nonlocal results

            local_results = []

            

            for probe_rec in chunk:

                probe_key = self.key_extractor(probe_rec)

                bucket = self._hash_function(probe_key)

                

                if bucket in hash_table:

                    for build_key, build_rec in hash_table[bucket]:

                        if build_key == probe_key:

                            local_results.append((build_rec, probe_rec))

            

            with results_lock:

                results.extend(local_results)

        

        threads = [threading.Thread(target=probe_chunk, args=(c,)) for c in chunks]

        for t in threads:

            t.start()

        for t in threads:

            t.join()

        

        return results





class SortMergeJoin:

    """

    Sort-Merge连接（Sort Merge Join）

    两个表先排序，然后归并扫描

    适用于：有序数据、范围连接

    """

    

    def __init__(self, left_table: List[Record], right_table: List[Record],

                 key_extractor: Callable[[Record], Any]):

        self.left_table = left_table    # 左表

        self.right_table = right_table  # 右表

        self.key_extractor = key_extractor

    

    def _sort_table(self, table: List[Record]) -> List[Record]:

        """按键排序"""

        return sorted(table, key=self.key_extractor)

    

    def join(self) -> List[Tuple[Record, Record]]:

        """执行Sort-Merge连接"""

        results = []

        

        # 排序

        sorted_left = self._sort_table(self.left_table)

        sorted_right = self._sort_table(self.right_table)

        

        i = 0  # 左表指针

        j = 0  # 右表指针

        

        while i < len(sorted_left) and j < len(sorted_right):

            left_key = self.key_extractor(sorted_left[i])

            right_key = self.key_extractor(sorted_right[j])

            

            if left_key < right_key:

                # 左表键较小，左指针前进

                i += 1

            elif left_key > right_key:

                # 右表键较小，右指针前进

                j += 1

            else:

                # 键相等，收集所有匹配

                left_start = i

                while i < len(sorted_left) and self.key_extractor(sorted_left[i]) == right_key:

                    i += 1

                

                right_start = j

                while j < len(sorted_right) and self.key_extractor(sorted_right[j]) == left_key:

                    j += 1

                

                # 笛卡尔积收集匹配对

                for li in range(left_start, i):

                    for rj in range(right_start, j):

                        results.append((sorted_left[li], sorted_right[rj]))

        

        return results





if __name__ == "__main__":

    # 构造测试数据

    orders = [

        Record(key=1, payload="order_A", table_name="orders"),

        Record(key=2, payload="order_B", table_name="orders"),

        Record(key=3, payload="order_C", table_name="orders"),

    ]

    

    customers = [

        Record(key=2, payload="cust_X", table_name="customers"),

        Record(key=1, payload="cust_Y", table_name="customers"),

        Record(key=4, payload="cust_Z", table_name="customers"),

    ]

    

    print("=" * 60)

    print("Join算法演示")

    print("=" * 60)

    

    # 1. 嵌套循环连接

    nlj = NestedLoopJoin(orders, customers, lambda r: r.key)

    result_nlj = nlj.join()

    print(f"\n1. 嵌套循环连接结果 ({len(result_nlj)} 条):")

    for pair in result_nlj:

        print(f"   {pair[0].payload} (key={pair[0].key}) <-> {pair[1].payload} (key={pair[1].key})")

    

    # 2. Hash连接

    hj = HashJoin(orders, customers, lambda r: r.key)

    result_hj = hj.join()

    print(f"\n2. Hash连接结果 ({len(result_hj)} 条):")

    for pair in result_hj:

        print(f"   {pair[0].payload} (key={pair[0].key}) <-> {pair[1].payload} (key={pair[1].key})")

    

    # 3. Sort-Merge连接

    smj = SortMergeJoin(orders, customers, lambda r: r.key)

    result_smj = smj.join()

    print(f"\n3. Sort-Merge连接结果 ({len(result_smj)} 条):")

    for pair in result_smj:

        print(f"   {pair[0].payload} (key={pair[0].key}) <-> {pair[1].payload} (key={pair[1].key})")

    

    print("\n各算法复杂度对比:")

    print("  Nested Loop: O(n*m) - 适用于小表或有大索引")

    print("  Hash Join:   O(n+m) - 适用于等值连接、大表")

    print("  Sort-Merge:  O(n*log(n) + m*log(m) + n+m) - 适用于已有序数据")

