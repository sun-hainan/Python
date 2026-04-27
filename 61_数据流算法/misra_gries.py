# -*- coding: utf-8 -*-

"""

算法实现：数据流算法 / misra_gries



本文件实现 misra_gries 相关的算法功能。

"""



from typing import List, Dict

from collections import defaultdict





class MisraGries:

    """Misra-Gries算法"""



    def __init__(self, k: int):

        """

        参数：

            k: 参数（用于1/k阈值）

        """

        self.k = k

        self.counter = defaultdict(int)

        self.total = 0



    def add(self, item) -> None:

        """添加元素"""

        self.total += 1



        if item in self.counter:

            self.counter[item] += 1

        elif len(self.counter) < self.k - 1:

            self.counter[item] = 1

        else:

            # 减少所有计数器

            for key in list(self.counter.keys()):

                self.counter[key] -= 1

                if self.counter[key] == 0:

                    del self.counter[key]



            # 再加一次（因为我们借了）

            if item in self.counter:

                self.counter[item] += 1

            elif len(self.counter) < self.k - 1:

                self.counter[item] = 1



    def get_frequent(self, threshold: float = None) -> Dict:

        """

        获取高频元素



        参数：

            threshold: 可选的自定义阈值



        返回：元素→频率的字典

        """

        if threshold is None:

            threshold = 1.0 / self.k



        min_freq = threshold * self.total



        return {item: freq for item, freq in self.counter.items()

                if freq >= min_freq}



    def estimate_frequency(self, item) -> int:

        """

        估计元素频率



        返回：频率估计（下界）

        """

        return self.counter.get(item, 0)





def misra_gries_analysis():

    """Misra-Gries分析"""

    print("=== Misra-Gries分析 ===")

    print()

    print("空间复杂度：O(k)")

    print("时间复杂度：O(1) 每元素")

    print()

    print("保证：")

    print("  - 输出频率 > 1/k 的所有元素")

    print("  - 可能输出一些频率略低的元素")

    print("  - 误差 ≤ n/k")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Misra-Gries测试 ===\n")



    # 创建算法

    k = 5

    mg = MisraGries(k)



    # 数据流

    stream = [1, 2, 3, 1, 2, 1, 4, 1, 2, 1, 3, 1, 5, 1, 1]



    print(f"k = {k}, 数据流长度 = {len(stream)}")

    print(f"阈值 = 1/k = {1/k:.2f}")

    print(f"预期频率 > {len(stream)/k:.1f} 的元素")

    print()



    # 处理流

    for item in stream:

        mg.add(item)



    # 获取高频元素

    frequent = mg.get_frequent()



    print("高频元素：")

    for item, freq in sorted(frequent.items(), key=lambda x: -x[1]):

        print(f"  元素 {item}: 频率 {freq} ({freq/len(stream)*100:.1f}%)")



    # 真实频率

    from collections import Counter

    true_freq = Counter(stream)



    print("\n真实频率：")

    for item, freq in sorted(true_freq.items(), key=lambda x: -x[1]):

        print(f"  元素 {item}: {freq}")



    print()

    misra_gries_analysis()



    print()

    print("说明：")

    print("  - Misra-Gries是确定性的Heavy Hitters算法")

    print("  - 比Count-Min/CounterSketch更节省空间")

    print("  - 用于数据流监控")

