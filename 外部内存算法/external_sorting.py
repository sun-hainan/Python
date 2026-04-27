# -*- coding: utf-8 -*-
"""
算法实现：外部内存算法 / external_sorting

本文件实现 external_sorting 相关的算法功能。
"""

import random


class ExternalSorter:
    """外部存储器"""

    def __init__(self, chunk_size: int = 1000):
        """
        参数：
            chunk_size: 每块大小
        """
        self.chunk_size = chunk_size

    def sort_large_file(self, data: list) -> list:
        """
        大文件排序

        参数：
            data: 大数据列表

        返回：排序后的数据
        """
        # 分块
        chunks = []
        for i in range(0, len(data), self.chunk_size):
            chunk = data[i:i + self.chunk_size]
            sorted_chunk = sorted(chunk)
            chunks.append(sorted_chunk)

        # 多路合并
        return self._k_way_merge(chunks)

    def _k_way_merge(self, chunks: list) -> list:
        """
        k路合并

        返回：合并后的排序列表
        """
        if not chunks:
            return []

        result = []

        # 优先队列合并
        import heapq
        heap = []

        # 初始化堆
        for i, chunk in enumerate(chunks):
            if chunk:
                heapq.heappush(heap, (chunk[0], i, 0))

        while heap:
            val, chunk_id, pos = heapq.heappop(heap)
            result.append(val)

            # 推进该块
            if pos + 1 < len(chunks[chunk_id]):
                next_val = chunks[chunk_id][pos + 1]
                heapq.heappush(heap, (next_val, chunk_id, pos + 1))

        return result


def external_sorting_analysis():
    """外部排序分析"""
    print("=== 外部排序分析 ===")
    print()
    print("I/O模型：")
    print("  - 内存大小 M")
    print("  - 块大小 B")
    print("  - 比较次数 O((n/B) log_{M/B}(n/B))")
    print()
    print("优化：")
    print("  - 增加B减少I/O次数")
    print("  - 多路合并减少合并遍数")
    print("  - 泡沫排序减少随机I/O")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 外部存储排序测试 ===\n")

    random.seed(42)

    # 模拟大数据
    data = [random.randint(0, 1000) for _ in range(500)]

    print(f"数据大小: {len(data)}")
    print(f"原始数据前10: {data[:10]}")
    print()

    sorter = ExternalSorter(chunk_size=100)

    sorted_data = sorter.sort_large_file(data)

    print(f"排序后前10: {sorted_data[:10]}")
    print(f"验证: {'✅ 正确' if sorted_data == sorted(data) else '❌ 错误'}")

    print()
    external_sorting_analysis()

    print()
    print("说明：")
    print("  - 外部排序用于大数据")
    print("  - 分块排序 + 多路合并")
    print("  - 数据库系统的基础技术")
