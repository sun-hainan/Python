# -*- coding: utf-8 -*-

"""

算法实现：缓存无关算法 / van_emde_boas



本文件实现 van_emde_boas 相关的算法功能。

"""



import math

from typing import List, Optional





class vanEmdeBoasNode:

    """

    van Emde Boas树节点

    """

    def __init__(self, universe_size: int, value: Optional[int] = None):

        """

        初始化

        

        Args:

            universe_size: 宇宙大小(值的范围)

            value: 如果是叶子节点,存储的值

        """

        self.u = universe_size

        self.value = value

        self.children = []  # 子节点列表

        self.summary = None  # 摘要指针

        

        if universe_size > 1:

            # 计算分割点

            self.high_bit = 1 << (universe_size.bit_length() // 2)

            self.low_mask = self.high_bit - 1

            self.num_children = (universe_size + self.high_bit - 1) // self.high_bit

    

    def high(self, x: int) -> int:

        """高半部分"""

        return x // self.high_bit

    

    def low(self, x: int) -> int:

        """低半部分"""

        return x & self.low_mask

    

    def index(self, high: int, low: int) -> int:

        """从高部和低部重建索引"""

        return high * self.high_bit + low





class vanEmdeBoasTree:

    """

    van Emde Boas树

    支持的操作:O(log log U)时间

    - insert

    - delete  

    - search

    - predecessor

    - successor

    - minimum

    - maximum

    """

    

    def __init__(self, universe_size: int):

        """

        初始化

        

        Args:

            universe_size: 宇宙大小(最大值的上界)

        """

        self.u = universe_size

        self.min = None

        self.max = None

        self.root = self._create_node(universe_size)

    

    def _create_node(self, u: int) -> vanEmdeBoasNode:

        """创建节点"""

        if u <= 1:

            return vanEmdeBoasNode(u, None)

        

        node = vanEmdeBoasNode(u)

        

        # 递归创建子节点

        num_children = (u + node.high_bit - 1) // node.high_bit

        node.children = [self._create_node(node.high_bit) for _ in range(num_children)]

        

        # 创建摘要

        if u > node.high_bit:

            node.summary = self._create_node(num_children)

        

        return node

    

    def insert(self, x: int):

        """

        插入值

        

        Args:

            x: 要插入的值

        """

        if self.min is None:

            self.min = self.max = x

            return

        

        if x < self.min:

            self.min, x = x, self.min

        

        if x > self.max:

            self.max = x

        

        self._insert(self.root, x)

    

    def _insert(self, node: vanEmdeBoasNode, x: int):

        """递归插入"""

        if node.u <= 1:

            node.value = x if x == 0 else None

            return

        

        h = node.high(x)

        l = node.low(x)

        

        if node.summary and node.children[h].min is None:

            self._insert(node.summary, h)

        

        self._insert(node.children[h], l)

    

    def delete(self, x: int):

        """

        删除值

        

        Args:

            x: 要删除的值

        """

        if self.min is None or x > self.max:

            return

        

        if self.min == self.max == x:

            self.min = self.max = None

            return

        

        if x == self.min:

            # 找下一个最小值

            next_min = self._successor(self.root, x + 1)

            self.min = next_min

        

        self._delete(self.root, x)

        

        if self.min is not None and self.max == x:

            self.max = self._predecessor(self.root, x - 1)

    

    def _delete(self, node: vanEmdeBoasNode, x: int):

        """递归删除"""

        if node.u <= 1:

            node.value = None

            return

        

        h = node.high(x)

        l = node.low(x)

        

        self._delete(node.children[h], l)

        

        # 检查是否需要更新summary

        if node.summary and node.children[h].min is None:

            self._delete(node.summary, h)

    

    def search(self, x: int) -> bool:

        """

        搜索值

        

        Args:

            x: 要搜索的值

        

        Returns:

            是否存在

        """

        if self.min is None or x < self.min or x > self.max:

            return False

        

        return self._search(self.root, x)

    

    def _search(self, node: vanEmdeBoasNode, x: int) -> bool:

        """递归搜索"""

        if node.u <= 1:

            return node.value is not None

        

        h = node.high(x)

        l = node.low(x)

        

        if node.children[h].min is not None and l >= node.children[h].min:

            return self._search(node.children[h], l)

        

        return False

    

    def successor(self, x: int) -> Optional[int]:

        """

        找后继

        

        Args:

            x: 基准值

        

        Returns:

            后继或None

        """

        if self.max is None or x >= self.max:

            return None

        

        if self.min is not None and x < self.min:

            return self.min

        

        return self._successor(self.root, x + 1)

    

    def _successor(self, node: vanEmdeBoasNode, x: int) -> Optional[int]:

        """递归找后继"""

        if node.u <= 1:

            return node.value if node.value is not None else None

        

        h = node.high(x)

        l = node.low(x)

        

        # 如果当前cluster有后继

        if node.children[h].max is not None and l < node.children[h].max:

            cluster_succ = self._successor(node.children[h], l)

            if cluster_succ is not None:

                return node.index(h, cluster_succ)

        

        # 检查下一个非空cluster

        if node.summary:

            next_cluster = self._successor(node.summary, h + 1)

            if next_cluster is not None:

                return node.index(next_cluster, node.children[next_cluster].min)

        

        return None

    

    def predecessor(self, x: int) -> Optional[int]:

        """

        找前驱

        

        Args:

            x: 基准值

        

        Returns:

            前驱或None

        """

        if self.min is None or x <= self.min:

            return None

        

        if self.max is not None and x > self.max:

            return self.max

        

        return self._predecessor(self.root, x - 1)

    

    def _predecessor(self, node: vanEmdeBoasNode, x: int) -> Optional[int]:

        """递归找前驱"""

        if node.u <= 1:

            return node.value if node.value is not None else None

        

        h = node.high(x)

        l = node.low(x)

        

        # 如果当前cluster有前驱

        if node.children[h].min is not None and l > node.children[h].min:

            cluster_pred = self._predecessor(node.children[h], l)

            if cluster_pred is not None:

                return node.index(h, cluster_pred)

        

        # 检查上一个非空cluster

        if node.summary:

            prev_cluster = self._predecessor(node.summary, h - 1)

            if prev_cluster is not None:

                return node.index(prev_cluster, node.children[prev_cluster].max)

        

        return None

    

    def minimum(self) -> Optional[int]:

        """返回最小值"""

        return self.min

    

    def maximum(self) -> Optional[int]:

        """返回最大值"""

        return self.max





def van_emde_boas_layout(size: int) -> List[int]:

    """

    生成van Emde Boas布局顺序

    

    Args:

        size: 数组大小

    

    Returns:

        布局顺序

    """

    if size <= 1:

        return [0]

    

    # 计算分割点

    h = 1 << (size.bit_length() // 2)

    

    # 递归生成

    layout = []

    

    # 前半部分

    for i in range(h):

        sub_layout = van_emde_boas_layout(min(h, size - i * h))

        for j in sub_layout:

            if i * h + j < size:

                layout.append(i * h + j)

    

    return layout





# 测试代码

if __name__ == "__main__":

    # 测试1: 基本操作

    print("测试1 - 基本操作:")

    v = vanEmdeBoasTree(16)

    

    for x in [3, 5, 7, 2, 8]:

        v.insert(x)

        print(f"  插入{x}: min={v.min}, max={v.max}")

    

    print(f"\n  搜索5: {v.search(5)}")

    print(f"  搜索4: {v.search(4)}")

    print(f"  后继5: {v.successor(5)}")

    print(f"  前驱5: {v.predecessor(5)}")

    

    # 测试2: 完整序列

    print("\n测试2 - 插入完整序列:")

    v2 = vanEmdeBoasTree(16)

    

    for x in range(16):

        v2.insert(x)

    

    print(f"  最小: {v2.minimum()}")

    print(f"  最大: {v2.maximum()}")

    

    for x in [0, 5, 10, 15]:

        print(f"  前驱{x}: {v2.predecessor(x)}")

        print(f"  后继{x}: {v2.successor(x)}")

    

    # 测试3: 删除

    print("\n测试3 - 删除:")

    v3 = vanEmdeBoasTree(16)

    

    for x in [3, 5, 7, 2, 8, 1, 4, 6]:

        v3.insert(x)

    

    print(f"  初始: min={v3.minimum()}, max={v3.maximum()}")

    

    for del_x in [3, 5, 8]:

        v3.delete(del_x)

        print(f"  删除{del_x}: min={v3.minimum()}, max={v3.maximum()}")

    

    # 测试4: 布局

    print("\n测试4 - van Emde Boas布局:")

    for size in [7, 8, 15, 16, 31, 32]:

        layout = van_emde_boas_layout(size)

        print(f"  size={size}: 布局长度={len(layout)}")

    

    # 测试5: 边界情况

    print("\n测试5 - 边界情况:")

    v5 = vanEmdeBoasTree(2)

    v5.insert(1)

    print(f"  插入1: min={v5.minimum()}, max={v5.maximum()}")

    print(f"  后继0: {v5.successor(0)}")

    

    v5.delete(1)

    print(f"  删除1后: min={v5.minimum()}")

    

    print("\n所有测试完成!")

