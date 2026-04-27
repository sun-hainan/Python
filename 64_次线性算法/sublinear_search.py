# -*- coding: utf-8 -*-

"""

算法实现：次线性算法 / sublinear_search



本文件实现 sublinear_search 相关的算法功能。

"""



import random

from typing import List, Tuple





class SublinearSearch:

    """次线性搜索"""



    def __init__(self, data: List[int]):

        """

        参数：

            data: 已排序的数据

        """

        self.data = data

        self.index = self._build_index()



    def _build_index(self) -> dict:

        """

        构建跳表风格索引



        返回：索引结构

        """

        n = len(self.data)

        index = {}



        # 每隔 sqrt(n) 个元素建一个索引

        step = max(1, int(n ** 0.5))



        for i in range(0, n, step):

            index[i] = self.data[i]



        return index



    def search(self, target: int) -> Tuple[bool, int]:

        """

        搜索目标



        返回：(是否找到, 索引)

        """

        n = len(self.data)



        # 使用索引快速定位范围

        step = max(1, int(n ** 0.5))



        # 找到target可能存在的范围

        prev_idx = 0

        for idx in range(0, n, step):

            if self.data[idx] <= target:

                prev_idx = idx

            else:

                break



        # 在小范围内线性搜索

        end_idx = min(prev_idx + step, n)

        for i in range(prev_idx, end_idx):

            if self.data[i] == target:

                return True, i



        return False, -1



    def exponential_search(self, target: int) -> Tuple[bool, int]:

        """

        指数搜索（适用于无界数组）



        返回：(是否找到, 索引)

        """

        n = len(self.data)



        # 首先找到target可能存在的范围

        bound = 1

        while bound < n and self.data[bound] < target:

            bound *= 2



        # 二分搜索

        left = bound // 2

        right = min(bound, n)



        # 二分查找

        while left < right:

            mid = (left + right) // 2

            if self.data[mid] < target:

                left = mid + 1

            else:

                right = mid



        if left < n and self.data[left] == target:

            return True, left



        return False, -1





def sublinear_algorithm_complexity():

    """次线性算法复杂度"""

    print("=== 次线性搜索复杂度 ===")

    print()

    print("跳表搜索：")

    print("  - 预处理：O(n)")

    print("  - 查询：O(√n)")

    print()

    print("指数搜索：")

    print("  - 无界数组：O(log n)")

    print("  - 有界数组：O(log n)")

    print()

    print("应用：")

    print("  - 数据库索引")

    print("  - 文件系统")

    print("  - 排序数据搜索")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 次线性搜索测试 ===\n")



    # 创建排序数据

    n = 10000

    data = sorted(random.sample(range(n * 2), n))



    search = SublinearSearch(data)



    print(f"数据大小: {n}")

    print(f"索引大小: {len(search.index)}")

    print()



    # 搜索测试

    test_targets = [data[0], data[1234], data[5678], data[-1], 99999]



    print("搜索测试：")

    for target in test_targets:

        found, idx = search.search(target)

        status = f"找到 @{idx}" if found else "未找到"

        print(f"  目标 {target}: {status}")



    print()

    print("指数搜索：")

    for target in test_targets[:3]:

        found, idx = search.exponential_search(target)

        status = f"找到 @{idx}" if found else "未找到"

        print(f"  目标 {target}: {status}")



    print()

    sublinear_algorithm_complexity()



    print()

    print("说明：")

    print("  - 次线性搜索利用预处理")

    print("  - 适用于静态数据")

    print("  - 数据库索引的基础")

