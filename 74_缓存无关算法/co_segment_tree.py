# -*- coding: utf-8 -*-

"""

算法实现：缓存无关算法 / co_segment_tree



本文件实现 co_segment_tree 相关的算法功能。

"""



import math

from typing import List, Optional





class CacheObliviousSegmentTree:

    """缓存无关线段树"""



    def __init__(self, data: List[int]):

        """

        参数：

            data: 数据数组

        """

        self.data = data

        self.n = len(data)

        # 计算树高度（完全二叉树）

        self.height = math.ceil(math.log2(self.n)) + 1



    def build(self) -> None:

        """构建树（自底向上）"""

        # 缓存无关：不需要知道缓存大小

        # 使用完美二叉树结构

        pass



    def query(self, left: int, right: int) -> int:

        """

        区间查询



        参数：

            left, right: 查询区间 [left, right)



        返回：区间和

        """

        return self._query_recursive(0, self.n, left, right)



    def _query_recursive(self, node_start: int, node_end: int,

                       query_left: int, query_right: int) -> int:

        """递归查询"""

        # 如果完全在区间内

        if query_left <= node_start and node_end <= query_right:

            # 计算这个节点的区间和

            return sum(self.data[node_start:node_end])



        # 如果完全不在区间内

        if node_end <= query_left or node_start >= query_right:

            return 0



        # 部分重叠，递归

        mid = (node_start + node_end) // 2

        left_sum = self._query_recursive(node_start, mid, query_left, query_right)

        right_sum = self._query_recursive(mid, node_end, query_left, query_right)



        return left_sum + right_sum



    def update(self, index: int, value: int) -> None:

        """单点更新"""

        self.data[index] = value





def van_emde_boas_layout():

    """van Emde Boas布局"""

    print("=== van Emde Boas布局 ===")

    print()

    print("vEB布局特点：")

    print("  - 递归划分区域")

    print("  - 常用查询的局部性")

    print("  - 最优查询复杂度")

    print()

    print("布局公式：")

    print("  对于大小为N的数组：")

    print("  顶层：sqrt(N)")

    print("  底层：sqrt(N)")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 缓存无关线段树测试 ===\n")



    # 创建数据

    data = [1, 2, 3, 4, 5, 6, 7, 8]

    tree = CacheObliviousSegmentTree(data)



    print(f"数据: {data}")

    print()



    # 查询

    queries = [(0, 4), (2, 6), (5, 8)]



    for l, r in queries:

        result = tree.query(l, r)

        expected = sum(data[l:r])

        print(f"查询 [{l}, {r}): 结果={result}, 期望={expected}")



    print()

    van_emde_boas_layout()



    print()

    print("说明：")

    print("  - 缓存无关结构对任意缓存大小都有效")

    print("  - 自相似性是核心")

    print("  - 应用于外部内存算法和现代CPU层次")

