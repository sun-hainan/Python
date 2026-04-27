# -*- coding: utf-8 -*-

"""

算法实现：外部内存算法 / priority_queue_external



本文件实现 priority_queue_external 相关的算法功能。

"""



import heapq

from typing import List, Tuple





class ExternalPriorityQueue:

    """外部优先队列"""



    def __init__(self, buffer_size: int = 1000):

        """

        参数：

            buffer_size: 缓冲区大小

        """

        self.buffer_size = buffer_size

        self.buffers = []  # 分块存储

        self.sizes = []   # 每个块的大小



    def insert(self, priority: float, item) -> None:

        """

        插入元素



        参数：

            priority: 优先级

            item: 元素

        """

        # 找到合适的缓冲区

        for i, (buf_prio, buf_items) in enumerate(self.buffers):

            if buf_prio <= priority or len(buf_items) < self.buffer_size:

                heapq.heappush(buf_items, (priority, item))

                self.sizes[i] += 1

                return



        # 创建新缓冲区

        new_buffer = [(priority, item)]

        heapq.heappush(self.buffers, (priority, new_buffer))

        self.sizes.append(1)



        # 如果缓冲区太多，合并

        if len(self.buffers) > 10:

            self._merge_buffers()



    def extract_min(self) -> Tuple[float, object]:

        """

        提取最小元素



        返回：(优先级, 元素)

        """

        # 找到最小缓冲区

        while self.buffers:

            buf_prio, buf_items = heapq.heappop(self.buffers)



            if buf_items:

                item = heapq.heappop(buf_items)

                return item[0], item[1]



        return None, None



    def _merge_buffers(self) -> None:

        """合并缓冲区"""

        # 取出一半缓冲区合并

        merged = []

        while len(self.buffers) > 5:

            buf1_prio, buf1_items = heapq.heappop(self.buffers)

            buf2_prio, buf2_items = heapq.heappop(self.buffers)



            # 合并

            combined = buf1_items + buf2_items

            heapq.heapify(combined)



            merged.append((buf1_prio, combined))



        # 放回去

        for item in merged:

            self.buffers.append(item)



        heapq.heapify(self.buffers)



    def peek_min(self) -> Tuple[float, object]:

        """

        查看最小元素（不删除）



        返回：(优先级, 元素)

        """

        if not self.buffers:

            return None, None



        buf_prio, buf_items = self.buffers[0]



        if buf_items:

            item = buf_items[0]

            return item[0], item[1]



        return None, None





def priority_queue_external_complexity():

    """外部优先队列复杂度"""

    print("=== 外部优先队列复杂度 ===")

    print()

    print("内部操作：")

    print("  - insert: O(log B)")

    print("  - extract_min: O(1)")

    print("  - peek: O(1)")

    print()

    print("B = 缓冲区大小")

    print("I/O模型：O((n/B) log_{M/B}(n/B))")

    print()

    print("应用：")

    print("  - 外部排序")

    print("  - 图算法")

    print("  - 调度系统")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 外部优先队列测试 ===\n")



    # 创建优先队列

    buffer_size = 5

    pq = ExternalPriorityQueue(buffer_size)



    # 插入元素

    items = [

        (3, "Task C"),

        (1, "Task A"),

        (4, "Task D"),

        (2, "Task B"),

        (5, "Task E"),

        (1.5, "Task F")

    ]



    print("插入元素：")

    for priority, item in items:

        pq.insert(priority, item)

        print(f"  插入 {item} (优先级={priority})")



    print(f"\n缓冲区数: {len(pq.buffers)}")



    # 提取

    print("\n提取顺序（按优先级）：")

    while True:

        prio, item = pq.extract_min()

        if item is None:

            break

        print(f"  {item} (优先级={prio})")



    print()

    priority_queue_external_complexity()



    print()

    print("说明：")

    print("  - 外部优先队列用于大数据排序")

    print("  - 缓冲区减少I/O次数")

    print("  - 外部排序的基础组件")

