# -*- coding: utf-8 -*-

"""

算法实现：数据流算法 / heavy_hitter



本文件实现 heavy_hitter 相关的算法功能。

"""



from collections import defaultdict, Counter





class HeavyHitterTester:

    """重击元素测试器"""



    def __init__(self, theta: float = 0.01):

        """

        参数：

            theta: 频率阈值

        """

        self.theta = theta

        self.counter = Counter()

        self.total = 0



    def add(self, item) -> None:

        """添加元素"""

        self.counter[item] += 1

        self.total += 1



    def get_heavy_hitters(self) -> list:

        """

        获取重元素



        返回：超过阈值的元素列表

        """

        threshold = self.theta * self.total



        return [(item, count) for item, count in self.counter.items()

                if count >= threshold]



    def estimate_frequency(self, item) -> int:

        """

        估计元素频率



        返回：估计值

        """

        return self.counter.get(item, 0)





class SpaceSaving:

    """Space-Saving算法"""



    def __init__(self, k: int):

        """

        参数：

            k: 保留的元素数

        """

        self.k = k

        self.counters = {}  # item -> count

        self.errors = {}    # item -> error



    def add(self, item) -> None:

        """添加元素"""

        if item in self.counters:

            self.counters[item] += 1

        elif len(self.counters) < self.k:

            self.counters[item] = 1

            self.errors[item] = 0

        else:

            # 找到最小计数器

            min_item = min(self.counters, key=self.counters.get)

            min_count = self.counters[min_item]



            # 更新错误

            self.errors[item] = min_count



            # 替换

            del self.counters[min_item]

            self.counters[item] = min_count + 1



    def get_top_k(self, k: int = None) -> list:

        """获取Top-k"""

        if k is None:

            k = self.k



        sorted_items = sorted(self.counters.items(),

                             key=lambda x: x[1], reverse=True)



        return sorted_items[:k]



    def estimate(self, item) -> int:

        """估计频率"""

        if item in self.counters:

            return self.counters[item]

        elif item in self.errors:

            return self.errors[item]

        return 0





def heavy_hitter_algorithms():

    """重元素算法比较"""

    print("=== Heavy Hitter算法比较 ===")

    print()

    print("Space-Saving：")

    print("  - 空间：O(k)")

    print("  - 时间：O(1)")

    print("  - 保证：Top-k 的估计误差 ≤ n/k")

    print()

    print("Count-Min Sketch：")

    print("  - 空间：O(1/δ * log(1/ε))")

    print("  - 时间：O(1)")

    print("  - 保证：上界估计")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 重元素测试 ===\n")



    # 数据流

    stream = [1, 2, 1, 3, 1, 2, 1, 4, 1, 2, 1, 3, 1, 2, 1] * 10



    # Heavy Hitter测试

    theta = 0.1

    hh = HeavyHitterTester(theta)



    for item in stream:

        hh.add(item)



    print(f"阈值: {theta*100}%")

    print(f"流长度: {len(stream)}")

    print(f"阈值计数: {theta * hh.total:.0f}")

    print()



    heavy_hitters = hh.get_heavy_hitters()

    print("Heavy Hitters：")

    for item, count in heavy_hitters:

        print(f"  元素 {item}: {count} ({count/len(stream)*100:.1f}%)")



    print()



    # Space-Saving

    k = 3

    ss = SpaceSaving(k)



    for item in stream:

        ss.add(item)



    print(f"Space-Saving Top-{k}：")

    for item, count in ss.get_top_k(k):

        print(f"  元素 {item}: {count}")



    print()

    heavy_hitter_algorithms()



    print()

    print("说明：")

    print("  - Heavy Hitter用于流数据分析")

    print("  - 应用于网站分析、网络监控")

    print("  - Space-Saving是高效算法")

