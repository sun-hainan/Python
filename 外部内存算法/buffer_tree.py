# -*- coding: utf-8 -*-

"""

算法实现：外部内存算法 / buffer_tree



本文件实现 buffer_tree 相关的算法功能。

"""



from typing import List, Tuple, Optional

import heapq





class BufferTree:

    """缓冲树"""



    def __init__(self, buffer_size: int, degree: int):

        """

        参数：

            buffer_size: 每个节点的缓冲区大小

            degree: 树的度

        """

        self.B = buffer_size

        self.d = degree

        self.buffers = {}  # 节点 -> 缓冲区

        self.heap = []    # 全局最小堆（已应用的操作）



    def batch_insert(self, items: List[int]) -> None:

        """

        批量插入



        参数：

            items: 要插入的元素列表

        """

        # 如果缓冲区满，先刷新

        if len(items) >= self.B:

            self._flush_buffer(0, items)

        else:

            # 添加到缓冲区

            if 0 not in self.buffers:

                self.buffers[0] = []

            self.buffers[0].extend(items)



            # 如果缓冲区满了，刷新

            if len(self.buffers[0]) >= self.B:

                self._apply_buffer(0)



    def _flush_buffer(self, node: int, items: List[int]) -> None:

        """刷新缓冲区到子节点"""

        # 简化为直接应用到堆

        for item in items:

            heapq.heappush(self.heap, item)



    def _apply_buffer(self, node: int) -> None:

        """应用缓冲区内容"""

        if node not in self.buffers:

            return



        items = self.buffers[node]

        if not items:

            return



        # 刷新到子节点或全局堆

        if node < self.d:

            child = self.d + node * self.d

            if child not in self.buffers:

                self.buffers[child] = []

            self.buffers[child].extend(items)

        else:

            for item in items:

                heapq.heappush(self.heap, item)



        self.buffers[node] = []



    def extract_min(self) -> Optional[int]:

        """提取最小元素"""

        if not self.heap:

            return None



        # 先尝试从缓冲区刷新

        if self.buffers.get(0):

            items = self.buffers[0]

            if len(items) >= self.B // 2:

                for item in items:

                    heapq.heappush(self.heap, item)

                self.buffers[0] = []



        return heapq.heappop(self.heap) if self.heap else None



    def batch_extract_min(self, k: int) -> List[int]:

        """批量提取k个最小元素"""

        results = []

        for _ in range(k):

            item = self.extract_min()

            if item is None:

                break

            results.append(item)

        return results





def batch_processing():

    """批量处理应用"""

    print("=== 缓冲树批量处理 ===")

    print()

    print("应用场景：")

    print("  1. 事件调度：批量调度事件")

    print("  2. 数据库：批量插入/删除")

    print("  3. 网络：批量数据包处理")

    print()

    print("优势：")

    print("  - 减少IO次数")

    print("  - 提高吞吐量")

    print("  - 在外部内存中特别有效")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 缓冲树测试 ===\n")



    # 创建缓冲树

    buffer_size = 5

    bt = BufferTree(buffer_size=buffer_size, degree=4)



    # 批量插入

    print(f"缓冲区大小: {buffer_size}")

    print()



    # 测试

    batches = [

        [3, 7, 1, 9, 2],

        [5, 4, 8, 6],

        [1, 10, 3]

    ]



    for i, batch in enumerate(batches):

        bt.batch_insert(batch)

        print(f"批次{i+1}插入: {batch}")

        print(f"  堆大小: {len(bt.heap)}")



    print()



    # 提取

    print("提取前5个最小元素:")

    results = bt.batch_extract_min(5)

    print(f"  {results}")



    print()

    batch_processing()



    print()

    print("说明：")

    print("  - 缓冲树适合批量操作")

    print("  - 减少单次操作的频率")

    print("  - 在外部内存系统中很有用")

