# -*- coding: utf-8 -*-
"""
算法实现：在线算法 / online_paging

本文件实现 online_paging 相关的算法功能。
"""

from collections import OrderedDict
from typing import List, Set


class OnlinePaging:
    """在线分页算法"""

    def __init__(self, cache_size: int):
        """
        参数：
            cache_size: 缓存大小
        """
        self.cache_size = cache_size
        self.cache = OrderedDict()
        self.page_faults = 0
        self.hits = 0

    def access_page_lru(self, page: int) -> str:
        """
        LRU页面访问

        返回：hit 或 miss
        """
        if page in self.cache:
            # 命中，移动到末尾（最新）
            self.cache.move_to_end(page)
            self.hits += 1
            return "hit"
        else:
            # 缺页
            self.page_faults += 1

            if len(self.cache) >= self.cache_size:
                # 驱逐最老的
                self.cache.popitem(last=False)

            # 添加新页面
            self.cache[page] = True

            return "miss"

    def access_page_fifo(self, page: int, history: List[int]) -> str:
        """
        FIFO页面访问

        返回：hit 或 miss
        """
        if page in self.cache:
            self.hits += 1
            return "hit"
        else:
            self.page_faults += 1

            if len(self.cache) >= self.cache_size and history:
                # 驱逐最早的
                oldest = history[0]
                if oldest in self.cache:
                    del self.cache[oldest]

            self.cache[page] = True
            history.append(page)

            return "miss"

    def reset(self) -> None:
        """重置统计"""
        self.cache.clear()
        self.page_faults = 0
        self.hits = 0

    def hit_ratio(self, total_accesses: int) -> float:
        """命中率"""
        if total_accesses == 0:
            return 0.0
        return self.hits / total_accesses


def paging_competitive_analysis():
    """分页竞争分析"""
    print("=== 分页算法竞争分析 ===")
    print()
    print("LRU（最近最少使用）：")
    print("  - 竞争比：k")
    print("  - 最坏情况：k倍最优")
    print()
    print("FIFO（先进先出）：")
    print("  - 竞争比：k")
    print("  - 可能比LRU差")
    print()
    print("LFU（最不经常使用）：")
    print("  - 需要维护频率计数")
    print("  - 适应性好")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 在线分页算法测试 ===\n")

    cache_size = 3
    paging = OnlinePaging(cache_size)

    # 访问序列
    accesses = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]

    print(f"缓存大小: {cache_size}")
    print(f"访问序列: {accesses}")
    print()

    print("LRU访问：")
    for page in accesses:
        result = paging.access_page_lru(page)
        print(f"  页面 {page}: {result}")

    print()
    total = len(accesses)
    print(f"缺页数: {paging.page_faults}")
    print(f"命中数: {paging.hits}")
    print(f"命中率: {paging.hit_ratio(total)*100:.1f}%")

    print()
    paging_competitive_analysis()

    print()
    print("说明：")
    print("  - 在线分页是经典的在线问题")
    print("  - LRU是常用的近似算法")
    print("  - 竞争比分析是评估标准")
