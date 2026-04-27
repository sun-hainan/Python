# -*- coding: utf-8 -*-

"""

算法实现：外部内存算法 / external_priority_queue



本文件实现 external_priority_queue 相关的算法功能。

"""



import random

import math





class ExternalMinHeap:

    """

    外部最小堆。



    将堆组织成磁盘块，每块包含多个元素。

    支持批量插入和提取最小元素。

    """



    def __init__(self, block_size=4, max_blocks_in_memory=8):

        self.block_size = block_size  # 每块元素数

        self.max_blocks = max_blocks_in_memory  # 内存中最多块数

        self.blocks = []  # 磁盘块列表

        self.num_elements = 0



    def _get_parent(self, i):

        """获取父节点索引。"""

        return (i - 1) // self.block_size



    def _get_children(self, i):

        """获取子块索引列表。"""

        block_idx = i // self.block_size

        offset = i % self.block_size



        # 简化：每个块内的元素作为独立节点

        left = 2 * i + 1

        right = 2 * i + 2

        return left, right



    def _heapify_up(self, idx):

        """从下往上堆化。"""

        while idx > 0:

            parent = (idx - 1) // 2

            # 找到所有元素

            all_items = [item for block in self.blocks for item in block]

            if all_items and idx < len(all_items) and parent < len(all_items):

                if all_items[idx] < all_items[parent]:

                    # 交换

                    pi = idx // self.block_size

                    offset_i = idx % self.block_size

                    pp = parent // self.block_size

                    offset_p = parent % self.block_size



                    self.blocks[pi][offset_i], self.blocks[pp][offset_p] = \

                        self.blocks[pp][offset_p], self.blocks[pi][offset_i]

                    idx = parent

                else:

                    break

            else:

                break



    def _heapify_down(self, idx):

        """从上往下堆化。"""

        all_items = [item for block in self.blocks for item in block]

        n = len(all_items)



        while True:

            smallest = idx

            left = 2 * idx + 1

            right = 2 * idx + 2



            if left < n and all_items[left] < all_items[smallest]:

                smallest = left

            if right < n and all_items[right] < all_items[smallest]:

                smallest = right



            if smallest != idx:

                # 交换

                pi_s = smallest // self.block_size

                offset_s = smallest % self.block_size

                pi_i = idx // self.block_size

                offset_i = idx % self.block_size



                self.blocks[pi_s][offset_s], self.blocks[pi_i][offset_i] = \

                    self.blocks[pi_i][offset_i], self.blocks[pi_s][offset_s]

                idx = smallest

            else:

                break



    def insert(self, item):

        """插入元素。"""

        # 找到或创建最后一个块

        if not self.blocks or len(self.blocks[-1]) >= self.block_size:

            self.blocks.append([])



        self.blocks[-1].append(item)

        self.num_elements += 1



        # 堆化

        self._rebuild_heap()



    def extract_min(self):

        """提取最小元素。"""

        if not self.blocks or not self.blocks[0]:

            return None



        # 最小元素在第一个块的第一个位置

        min_item = self.blocks[0][0]



        # 移除最小元素

        self.blocks[0].pop(0)

        self.num_elements -= 1



        # 如果第一个块空了，删除它

        if not self.blocks[0]:

            self.blocks.pop(0)



        # 重建堆

        self._rebuild_heap()



        return min_item



    def _rebuild_heap(self):

        """重建整个堆结构。"""

        # 收集所有元素

        all_items = []

        for block in self.blocks:

            all_items.extend(block)



        if not all_items:

            return



        # 排序（简化：实际用堆化）

        all_items.sort()



        # 重新分块

        self.blocks = []

        for i in range(0, len(all_items), self.block_size):

            block = all_items[i:i + self.block_size]

            self.blocks.append(block)



    def peek_min(self):

        """查看最小元素（不删除）。"""

        if self.blocks and self.blocks[0]:

            return self.blocks[0][0]

        return None



    def size(self):

        """返回元素数量。"""

        return self.num_elements





def external_merge_with_priority_queue(sorted_runs, output_file, block_size):

    """

    使用外部优先队列合并多个有序段。



    这是外部排序的关键步骤。



    参数:

        sorted_runs: 有序段列表

        output_file: 输出文件（模拟）

        block_size: 块大小

    """

    import heapq



    pq = []  # 优先队列：(元素, run_id, element_idx)



    # 初始化：将每个有序段的第一个元素入队

    for run_id, run in enumerate(sorted_runs):

        if run:

            heapq.heappush(pq, (run[0], run_id, 0))



    result = []

    while pq:

        val, run_id, elem_idx = heapq.heappop(pq)

        result.append(val)



        # 从同一有序段取下一个元素

        next_idx = elem_idx + 1

        if next_idx < len(sorted_runs[run_id]):

            next_val = sorted_runs[run_id][next_idx]

            heapq.heappush(pq, (next_val, run_id, next_idx))



        # 模拟输出

        if len(result) >= block_size:

            # 写出到磁盘

            output_file.append(result)

            result = []



    if result:

        output_file.append(result)



    return output_file





if __name__ == "__main__":

    print("=== 外部优先队列测试 ===")



    # 创建外部最小堆

    pq = ExternalMinHeap(block_size=4)



    # 插入元素

    test_values = [15, 10, 20, 17, 8, 25, 30, 5]

    print(f"插入元素: {test_values}")



    for val in test_values:

        pq.insert(val)

        print(f"  插入 {val}, 堆块数: {len(pq.blocks)}, 大小: {pq.size()}")



    # 提取最小

    print("\n提取元素:")

    while pq.size() > 0:

        min_val = pq.extract_min()

        print(f"  最小值: {min_val}")



    # 外部归并测试

    print("\n=== 外部归并测试 ===")

    sorted_runs = [

        [1, 3, 5, 7],

        [2, 4, 6, 8],

        [0, 9, 10, 11],

        [12, 13, 14, 15]

    ]



    output = []

    external_merge_with_priority_queue(sorted_runs, output, block_size=4)

    print(f"有序段: {sorted_runs}")

    print(f"合并结果: {output}")

    print(f"完全有序: {output[0] + output[1] == list(range(16))}")



    print("\n外部优先队列特性:")

    print("  最小堆结构：O(log n) 插入和提取")

    print("  外部版本：将元素组织成块以减少 I/O")

    print("  批量操作：提高吞吐量")

    print("  应用：外部排序、最小生成树、Dijkstra")

