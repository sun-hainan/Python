# -*- coding: utf-8 -*-

"""

算法实现：数据流算法 / lossy_counting



本文件实现 lossy_counting 相关的算法功能。

"""



from collections import defaultdict

from typing import List, Tuple





class LossyCounting:

    """Lossy Counting算法"""



    def __init__(self, epsilon: float):

        """

        参数：

            epsilon: 误差参数

        """

        self.epsilon = epsilon

        self.counters = defaultdict(int)

        self.current_bucket = 1

        self.bucket_size = 0



    def _compute_bucket_size(self, total: int) -> int:

        """

        计算桶大小



        返回：桶大小

        """

        # 桶大小 = ceil(1 / epsilon)

        return int(1 / self.epsilon)



    def add(self, item, total_count: int) -> None:

        """

        添加元素



        参数：

            item: 元素

            total_count: 当前处理的总元素数

        """

        self.bucket_size = self._compute_bucket_size(total_count)



        # 当前桶号 = ceil(current_count / bucket_size)

        self.current_bucket = (total_count + self.bucket_size - 1) // self.bucket_size



        # 增加计数

        self.counters[item] += 1



        # 如果计数等于桶号，删除

        if self.counters[item] == self.current_bucket:

            del self.counters[item]



    def get_frequent(self, threshold: float) -> List[Tuple]:

        """

        获取高频元素



        参数：

            threshold: 频率阈值（0到1之间）



        返回：元素及其估计频率

        """

        min_count = threshold * self.bucket_size * self.current_bucket



        frequent = []

        for item, count in self.counters.items():

            if count >= min_count:

                # 估计频率可能偏高

                estimated_freq = count / self.bucket_size / self.current_bucket

                frequent.append((item, count, estimated_freq))



        return sorted(frequent, key=lambda x: -x[1])



    def reset(self) -> None:

        """重置计数器"""

        self.counters.clear()

        self.current_bucket = 1





def lossy_counting_properties():

    """Lossy Counting性质"""

    print("=== Lossy Counting性质 ===")

    print()

    print("保证：")

    print("  - 不会漏掉频率 > εN 的元素")

    print("  - 可能包含频率 < εN 的元素（假阳性）")

    print("  - 计数误差 ≤ bucket_number")

    print()

    print("空间：")

    print("  - O(1/ε) 个计数器")

    print()

    print("应用：")

    print("  - 网络流量监控")

    print("  - 热点发现")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Lossy Counting测试 ===\n")



    epsilon = 0.01  # 1%误差

    lc = LossyCounting(epsilon)



    # 模拟数据流

    data_stream = [1, 2, 1, 3, 1, 2, 1, 4, 1] * 100



    print(f"数据流长度: {len(data_stream)}")

    print(f"阈值: {epsilon * 100}%")

    print()



    for i, item in enumerate(data_stream, 1):

        lc.add(item, i)



    print(f"桶号: {lc.current_bucket}")

    print(f"计数器数量: {len(lc.counters)}")

    print()



    # 获取高频

    threshold = 0.05

    frequent = lc.get_frequent(threshold)



    print(f"频率 > {threshold*100}% 的元素:")

    for item, count, est in frequent:

        print(f"  元素 {item}: 计数={count}, 估计频率={est:.4f}")



    print()

    lossy_counting_properties()



    print()

    print("说明：")

    print("  - Lossy Counting是近似算法")

    print("  - 保证不漏掉高频元素")

    print("  - 空间高效 O(1/ε)")

