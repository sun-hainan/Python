# -*- coding: utf-8 -*-

"""

算法实现：缓存无关算法 / memory_hierarchy



本文件实现 memory_hierarchy 相关的算法功能。

"""



from typing import List, Tuple





class MemoryHierarchy:

    """内存层次"""



    def __init__(self, levels: List[dict]):

        """

        参数：

            levels: 每个层的参数 {size, latency, bandwidth}

        """

        self.levels = levels



    def access(self, address: int) -> Tuple[int, int]:

        """

        访问地址



        返回：(延迟, 层级)

        """

        for i, level in enumerate(self.levels):

            size = level['size']

            if address < size:

                return level['latency'], i



        # 超出范围

        return self.levels[-1]['latency'], len(self.levels) - 1



    def optimal_cache_size(self, access_pattern: List[int]) -> int:

        """

        根据访问模式确定最优缓存大小



        参数：

            access_pattern: 访问地址序列



        返回：推荐的缓存大小

        """

        # 简化：使用工作集大小

        working_set = len(set(access_pattern))

        return working_set





def temporal_locality():

    """时间局部性"""

    print("=== 时间局部性 ===")

    print()

    print("概念：")

    print("  - 最近访问的数据可能很快再次访问")

    print("  - LRU缓存利用这个特性")

    print()

    print("评估指标：")

    print("  - 命中率 = 缓存命中 / 总访问")

    print("  - 未命中率 = 缓存未命中 / 总访问")





def spatial_locality():

    """空间局部性"""

    print()

    print("=== 空间局部性 ===")

    print()

    print("概念：")

    print("  - 访问某地址后，可能访问相邻地址")

    print("  - 预取（prefetch）利用这个特性")

    print()

    print("例子：")

    print("  - 数组遍历：顺序访问，命中率高")

    print("  - 链表遍历：随机访问，命中率低")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 内存层次模型测试 ===\n")



    # 定义层次结构

    levels = [

        {'name': 'L1 Cache', 'size': 32 * 1024, 'latency': 1, 'bandwidth': 100},

        {'name': 'L2 Cache', 'size': 256 * 1024, 'latency': 5, 'bandwidth': 50},

        {'name': 'L3 Cache', 'size': 8 * 1024 * 1024, 'latency': 20, 'bandwidth': 20},

        {'name': 'RAM', 'size': 16 * 1024 * 1024 * 1024, 'latency': 100, 'bandwidth': 10},

    ]



    hierarchy = MemoryHierarchy(levels)



    print("内存层次：")

    for i, level in enumerate(levels):

        print(f"  L{i+1}: {level['name']}, "

              f"大小={level['size']/1024:.0f}KB, "

              f"延迟={level['latency']}ns")



    print()



    # 访问测试

    addresses = [0, 1000, 2000, 3000, 1000, 2000, 5000]

    print(f"访问序列: {addresses}")



    total_latency = 0

    for addr in addresses:

        lat, level = hierarchy.access(addr)

        total_latency += lat

        print(f"  地址 {addr}: 延迟={lat}ns, L{level+1}")



    print(f"\n总延迟: {total_latency}ns")

    print(f"平均延迟: {total_latency/len(addresses):.1f}ns")



    print()

    temporal_locality()

    spatial_locality()



    print()

    print("说明：")

    print("  - 理解内存层次对算法设计很重要")

    print("  - 缓存友好的算法性能提升显著")

    print("  - Cache-oblivious算法对任何层次都有效")

