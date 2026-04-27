# -*- coding: utf-8 -*-

"""

算法实现：外部内存算法 / sorting_network_external



本文件实现 sorting_network_external 相关的算法功能。

"""



from typing import List





class SortingNetwork:

    """排序网络"""



    def __init__(self, n: int):

        """

        参数：

            n: 输入数量

        """

        self.n = n

        self.comparators = []  # 比较器列表 (i, j)



    def add_comparator(self, i: int, j: int) -> None:

        """

        添加比较器（i < j）



        参数：

            i, j: 比较器位置

        """

        if i < j:

            self.comparators.append((i, j))



    def sort(self, data: List[int]) -> List[int]:

        """

        使用排序网络排序



        返回：排序后的数据

        """

        result = data.copy()



        for i, j in self.comparators:

            # 交换使得 result[i] <= result[j]

            if result[i] > result[j]:

                result[i], result[j] = result[j], result[i]



        return result



    def depth(self) -> int:

        """

        计算网络深度（并行比较次数）



        返回：深度

        """

        if not self.comparators:

            return 0



        # 构建依赖图

        max_depth = 0

        depths = [0] * self.n



        for i, j in self.comparators:

            # j 必须在 i 之后

            if depths[i] >= depths[j]:

                depths[j] = depths[i] + 1



        return max(depths)



    def size(self) -> int:

        """比较器数量"""

        return len(self.comparators)





def bitonic_sort_network(n: int) -> SortingNetwork:

    """

    生成双调排序网络



    参数：

        n: 输入数（必须是2的幂）



    返回：排序网络

    """

    network = SortingNetwork(n)



    def add_comparators(k: int, ascending: bool):

        if k <= 1:

            return



        half = k // 2

        for i in range(half):

            j = i + half

            if ascending:

                network.add_comparator(i, j)

            else:

                network.add_comparator(j, i)



        add_comparators(half, ascending)

        add_comparators(half, ascending)



    add_comparators(n, True)

    return network





def sorting_network_complexity():

    """排序网络复杂度"""

    print("=== 排序网络复杂度 ===")

    print()

    print("比较器数量：")

    print("  - 朴素：n(n-1)/2")

    print("  - Batcher's bitonic: O(n log²n)")

    print()

    print("网络深度：")

    print("  - 朴素：n-1")

    print("  - Batcher's: O(log²n)")

    print()

    print("应用：")

    print("  - 硬件排序")

    print("  - 并行排序")

    print("  - 网络排序")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 排序网络测试 ===\n")



    # 创建8输入排序网络（简单版）

    network = SortingNetwork(8)



    # 添加比较器（冒泡排序网络）

    n = 8

    for i in range(n - 1):

        for j in range(n - 1 - i):

            network.add_comparator(j, j + 1)



    print(f"比较器数量: {network.size()}")

    print(f"网络深度: {network.depth()}")

    print()



    # 测试

    import random

    data = [random.randint(0, 100) for _ in range(8)]



    print(f"输入: {data}")

    sorted_data = network.sort(data)

    print(f"输出: {sorted_data}")

    print(f"正确: {'✅' if sorted_data == sorted(data) else '❌'}")



    print()

    sorting_network_complexity()



    print()

    print("说明：")

    print("  - 排序网络是硬件友好的排序方法")

    print("  - 适合并行实现")

    print("  - Batcher's算法是最优网络之一")

