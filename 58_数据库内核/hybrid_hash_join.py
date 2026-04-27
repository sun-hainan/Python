# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / hybrid_hash_join



本文件实现 hybrid_hash_join 相关的算法功能。

"""



import math

from typing import List, Tuple, Any, Dict, Optional





class HashTable:

    """哈希表实现"""



    def __init__(self, bucket_count: int = 1024):

        self.bucket_count = bucket_count  # 桶数量

        self.buckets: List[List[Tuple[Any, Any]]] = [[] for _ in range(bucket_count)]

        self.tuple_count = 0  # 元组总数



    def hash_function(self, key: Any) -> int:

        """哈希函数"""

        return hash(key) % self.bucket_count



    def insert(self, key: Any, value: Any):

        """插入键值对"""

        bucket_idx = self.hash_function(key)

        self.buckets[bucket_idx].append((key, value))

        self.tuple_count += 1



    def lookup(self, key: Any) -> List[Any]:

        """查找键对应的所有值"""

        bucket_idx = self.hash_function(key)

        matches = []

        for k, v in self.buckets[bucket_idx]:

            if k == key:

                matches.append(v)

        return matches





class HybridHashJoin:

    """

    混合Hash Join算法



    策略:

    1. 小表直接构建哈希表(内表)

    2. 大表分批探测(外表)

    3. 内存不足时使用分区溢出

    """



    def __init__(self, max_memory_mb: float = 256.0, tuple_size: int = 100):

        self.max_memory_bytes = max_memory_mb * 1024 * 1024  # 最大内存

        self.tuple_size = tuple_size  # 每元组大小(字节)

        self.build_partitions: List[HashTable] = []  # 构建阶段分区

        self.stats = {

            "build_tuples": 0,

            "probe_tuples": 0,

            "hash_buckets": 0,

            "partitions_created": 0,

            "overflow_count": 0

        }



    def estimate_partition_count(self, inner_rows: int) -> int:

        """

        估算分区数量

        基于内存限制和表大小

        """

        tuples_per_mb = (1024 * 1024) / self.tuple_size

        max_tuples_in_memory = int((self.max_memory_bytes / 2) / self.tuple_size)



        if inner_rows <= max_tuples_in_memory:

            return 1  # 全部放入内存



        # 保持每个分区都能放入内存

        partition_count = math.ceil(inner_rows / max_tuples_in_memory)

        return max(partition_count, 4)  # 至少4个分区



    def grace_hash_join(self, inner_relation: List[Tuple[Any, Any]],

                        outer_relation: List[Tuple[Any, Any]],

                        key_index: int = 0) -> List[Tuple[Any, Any]]:

        """

        Grace Hash Join核心算法



        参数:

            inner_relation: 内表(小表)，格式为(key, value)元组列表

            outer_relation: 外表(大表)

            key_index: 连接键在元组中的索引位置



        返回:

            连接结果列表

        """

        results = []

        partition_count = self.estimate_partition_count(len(inner_relation))



        self.stats["partitions_created"] = partition_count

        self.stats["build_tuples"] = len(inner_relation)

        self.stats["probe_tuples"] = len(outer_relation)



        # 阶段1: 分区阶段

        inner_partitions = self.partition_relation(inner_relation, partition_count, key_index)

        outer_partitions = self.partition_relation(outer_relation, partition_count, key_index)



        # 阶段2: 哈希构建与探测

        for i in range(partition_count):

            if not inner_partitions[i] or not outer_partitions[i]:

                continue



            # 构建哈希表

            ht = HashTable(bucket_count=max(256, len(inner_partitions[i]) // 10))

            for tuple_data in inner_partitions[i]:

                key = tuple_data[key_index]

                ht.insert(key, tuple_data)



            self.stats["hash_buckets"] = max(self.stats["hash_buckets"], ht.bucket_count)



            # 探测外表分区

            for probe_tuple in outer_partitions[i]:

                probe_key = probe_tuple[key_index]

                matches = ht.lookup(probe_key)

                for match in matches:

                    # 合并元组

                    result = self.combine_tuples(match, probe_tuple)

                    results.append(result)



        return results



    def partition_relation(self, relation: List[Tuple[Any, Any]],

                          partition_count: int, key_index: int) -> List[List[Tuple[Any, Any]]]:

        """

        对关系进行分区

        使用哈希函数将元组分散到不同分区

        """

        partitions: List[List[Tuple[Any, Any]]] = [[] for _ in range(partition_count)]



        for tuple_data in relation:

            key = tuple_data[key_index]

            partition_idx = hash(key) % partition_count

            partitions[partition_idx].append(tuple_data)



        return partitions



    def combine_tuples(self, left_tuple: Tuple[Any, ...],

                      right_tuple: Tuple[Any, ...]) -> Tuple[Any, ...]:

        """合并两个元组"""

        return left_tuple + right_tuple



    def hybrid_execute(self, inner_relation: List[Tuple[Any, Any]],

                       outer_relation: List[Tuple[Any, Any]],

                       key_index: int = 0,

                       use_nested_loop_threshold: float = 0.1) -> List[Tuple[Any, Any]]:

        """

        混合执行策略:

        - 小表: 直接构建哈希表

        - 大表: 分区或嵌套循环

        """

        small_relation = inner_relation if len(inner_relation) <= len(outer_relation) else outer_relation

        large_relation = outer_relation if len(inner_relation) <= len(outer_relation) else inner_relation



        # 判断是否使用嵌套循环

        if len(small_relation) < len(large_relation) * use_nested_loop_threshold:

            return self.nested_loop_join(small_relation, large_relation, key_index)

        else:

            return self.grace_hash_join(small_relation, large_relation, key_index)



    def nested_loop_join(self, inner: List[Tuple[Any, Any]],

                         outer: List[Tuple[Any, Any]],

                         key_index: int) -> List[Tuple[Any, Any]]:

        """

        嵌套循环连接(用于小表情况)

        """

        results = []

        ht = HashTable()

        for tuple_data in inner:

            ht.insert(tuple_data[key_index], tuple_data)



        for probe_tuple in outer:

            matches = ht.lookup(probe_tuple[key_index])

            for match in matches:

                results.append(self.combine_tuples(match, probe_tuple))



        return results





def print_join_stats(stats: Dict[str, Any]):

    """打印连接统计信息"""

    print("=== Hybrid Hash Join 统计 ===")

    for key, value in stats.items():

        print(f"  {key}: {value}")





if __name__ == "__main__":

    # 生成测试数据

    inner = [(i, f"inner_{i}", i * 10) for i in range(1000)]  # 1000行内表

    outer = [(i * 2 % 500, f"outer_{i}", i * 5) for i in range(5000)]  # 5000行外表



    print(f"内表大小: {len(inner)} 元组")

    print(f"外表大小: {len(outer)} 元组")



    # 执行混合Hash Join

    joiner = HybridHashJoin(max_memory_mb=64.0, tuple_size=100)

    results = joiner.hybrid_execute(inner, outer, key_index=0)



    print(f"\n连接结果: {len(results)} 行")

    print_join_stats(joiner.stats)



    # 展示部分结果

    print("\n前5条结果:")

    for r in results[:5]:

        print(f"  {r}")



    # 测试纯Grace Hash Join模式

    print("\n=== Grace Hash Join 模式 ===")

    joiner2 = HybridHashJoin(max_memory_mb=16.0, tuple_size=100)

    results2 = joiner2.grace_hash_join(inner, outer, key_index=0)

    print(f"结果: {len(results2)} 行")

    print_join_stats(joiner2.stats)

