# -*- coding: utf-8 -*-

"""

算法实现：缓存无关算法 / vanEmdeBoas



本文件实现 vanEmdeBoas 相关的算法功能。

"""



import math

from typing import List, Optional, Tuple





# 常量定义

# ============================================================

# BASE_LEVEL_SPLIT_SIZE: 基础层级分裂大小参数用于控制递归深度的粒度

BASE_LEVEL_SPLIT_SIZE = 2



# MIN_UNIVERSE_SIZE: 最小宇宙大小当未处理元素范围小于此值时使用简化的底层结构

MIN_UNIVERSE_SIZE = 2



# MAX_RECURSION_DEPTH: 最大递归深度用于防止无限递归

MAX_RECURSION_DEPTH = 64





class VanEmdeBoasNode:

    """

    van Emde Boas树节点结构

    

    该节点类表示vEB树中的一个递归单元每个节点包含指向高层summary结构

    的指针和底层cluster数组的指针通过这种嵌套结构实现对整个宇宙空间的

    分层组织

    

    Attributes:

        universe_size: 当前节点管理的宇宙大小必须是2的幂

        summary: 高层摘要节点指针指向管理cluster的summary结构

        cluster: 底层cluster数组每个元素指向一个子vEB节点或空

        min_val: 当前节点维护的最小值用于快速查询

        max_val: 当前节点维护的最大值用于快速查询

    """

    

    def __init__(self, universe_size: int):

        """

        初始化vEB节点

        

        Args:

            universe_size: 宇宙大小必须是大于等于2的2的幂

        """

        self.universe_size = universe_size  # 宇宙大小必须是2的幂

        self.min_val = None                 # 当前子树的最小值

        self.max_val = None                 # 当前子树的最大值

        self.summary = None                # 高层summary节点指针

        self.cluster = []                   # 底层cluster数组

        

        # 当宇宙大小大于基础分裂阈值时创建summary和cluster

        if universe_size > BASE_LEVEL_SPLIT_SIZE:

            # 计算高层和低层的分裂点

            split_size = self._compute_split_size(universe_size)

            # 初始化cluster数组大小为分裂大小的向上取整

            cluster_count = (universe_size + split_size - 1) // split_size

            self.cluster = [None] * cluster_count

            # 递归创建summary节点其宇宙大小为cluster数量的向上取整

            self.summary = VanEmdeBoasNode(

                self._next_power_of_2(cluster_count)

            )

    

    def _compute_split_size(self, size: int) -> int:

        """

        计算van Emde Boas树递归分裂大小

        

        该函数计算在给定宇宙大小下高層cluster的最优大小根据vEB树的设计

        我们希望每个cluster的大小接近于宇宙大小的平方根这样可以实现

        O(log log u)的操作复杂度

        

        Args:

            size: 宇宙大小必须是2的幂

            

        Returns:

            分裂后每个cluster的基础大小

        """

        return int(math.sqrt(size))

    

    def _next_power_of_2(self, n: int) -> int:

        """

        计算大于等于n的最小2的幂

        

        Args:

            n: 输入的正整数

            

        Returns:

            大于等于n的最小2的幂

        """

        if n <= 0:

            return 1

        if n & (n - 1) == 0:

            return n

        n |= n >> 1

        n |= n >> 2

        n |= n >> 4

        n |= n >> 8

        n |= n >> 16

        n |= n >> 32

        return n + 1

    

    def _high(self, x: int, split_size: int) -> int:

        """

        计算元素x在cluster数组中的高层索引

        

        Args:

            x: 元素的实际值

            split_size: 分裂大小即每个cluster包含的元素个数

            

        Returns:

            x所在cluster的高层索引

        """

        return x // split_size

    

    def _low(self, x: int, split_size: int) -> int:

        """

        计算元素x在其cluster内部偏移量

        

        Args:

            x: 元素的实际值

            split_size: 分裂大小即每个cluster包含的元素个数

            

        Returns:

            x在其所在cluster中的偏移量

        """

        return x % split_size





class VanEmdeBoasTree:

    """

    van Emde Boas树完整实现

    

    该类提供了vEB树的完整功能包括创建、插入、删除、查找等核心操作

    vEB树通过巧妙的递归布局设计实现了对优先队列操作的亚对数时间复杂度

    特别是其空间布局设计使得每次操作访问的内存块大小与当前操作涉及

    的数据量成比例这大大减少了缓存未命中次数

    

    该实现特别展示了缓存无关算法的设计思想即算法本身不假定特定的

    缓存参数但其行为自动适应任何内存层次结构这是通过递归地按平方根

    划分空间并保持各层级数据块大小与该层级数据量成比例来实现的

    

    Attributes:

        root: vEB树的根节点

        universe_size: 树的宇宙大小

    """

    

    def __init__(self, universe_size: int):

        """

        初始化vEB树

        

        Args:

            universe_size: 宇宙大小必须是2的幂定义了元素的可能取值范围[0, u)

        """

        self.universe_size = universe_size  # 宇宙大小必须是2的幂

        self.root = VanEmdeBoasNode(universe_size)  # 树的根节点

    

    def insert(self, x: int) -> None:

        """

        将元素x插入vEB树

        

        插入操作首先检查树是否为空如果为空则同时设置最小值和最大值

        否则递归地在适当的cluster中插入该元素如果cluster之前为空

        则需要在summary中插入该cluster的高层索引

        

        Args:

            x: 要插入的元素值必须在[0, universe_size)范围内

        """

        if self.root.min_val is None:

            # 树为空时直接设置根节点的min和max

            self.root.min_val = x

            self.root.max_val = x

        else:

            # 递归地在根节点中插入x

            self._insert_recursive(self.root, x)

    

    def _insert_recursive(self, node: VanEmdeBoasNode, x: int) -> None:

        """

        递归地将元素x插入到指定vEB节点

        

        Args:

            node: 当前操作的vEB节点

            x: 要插入的元素值

        """

        if node.min_val is None:

            # 当前cluster为空设置最小值和最大值

            node.min_val = x

            node.max_val = x

        else:

            # 确保min_val <= x <= max_val的正确性

            if x < node.min_val:

                # 如果x小于当前最小值交换它们使得min_val始终是全局最小

                node.min_val, x = x, node.min_val

            if x > node.max_val:

                # 更新当前cluster的最大值

                node.max_val = x

            

            # 只有当宇宙大小大于基础分裂阈值时才需要递归

            if node.universe_size > BASE_LEVEL_SPLIT_SIZE:

                # 计算分裂大小用于确定cluster和summary

                split_size = node._compute_split_size(node.universe_size)

                # 计算x应该插入的cluster索引和cluster内的偏移

                high_index = node._high(x, split_size)

                low_value = node._low(x, split_size)

                

                # 获取目标cluster

                target_cluster = node.cluster[high_index]

                if target_cluster is None:

                    # cluster为空创建新的子vEB节点

                    target_cluster = VanEmdeBoasNode(split_size)

                    node.cluster[high_index] = target_cluster

                    # 在summary中插入该cluster的高层索引

                    self._insert_summary(node.summary, high_index)

                

                # 递归地在目标cluster中插入low_value

                self._insert_recursive(target_cluster, low_value)

    

    def _insert_summary(self, summary_node: VanEmdeBoasNode, index: int) -> None:

        """

        在summary结构中插入一个高层索引

        

        summary结构本身是一个简化版的vEB树用于追踪哪些cluster包含元素

        当我们创建一个新的非空cluster时需要更新summary结构

        

        Args:

            summary_node: summary节点

            index: 要插入的高层索引

        """

        if summary_node.min_val is None:

            # summary为空直接设置

            summary_node.min_val = index

            summary_node.max_val = index

        else:

            # 更新summary的min和max

            if index < summary_node.min_val:

                summary_node.min_val = index

            if index > summary_node.max_val:

                summary_node.max_val = index

    

    def search(self, x: int) -> bool:

        """

        搜索元素x是否存在于vEB树中

        

        Args:

            x: 要搜索的元素值

            

        Returns:

            如果x存在返回True否则返回False

        """

        if self.root.min_val is None:

            return False

        if x == self.root.min_val or x == self.root.max_val:

            return True

        if self.root.universe_size <= BASE_LEVEL_SPLIT_SIZE:

            return False

        # 递归搜索

        split_size = self.root._compute_split_size(self.root.universe_size)

        high_index = self.root._high(x, split_size)

        if self.root.cluster[high_index] is None:

            return False

        low_value = self.root._low(x, split_size)

        cluster = self.root.cluster[high_index]

        return cluster.min_val is not None and low_value >= cluster.min_val and low_value <= cluster.max_val

    

    def predecessor(self, x: int) -> Optional[int]:

        """

        查找元素x的前驱即小于x的最大元素

        

        Args:

            x: 参考元素值

            

        Returns:

            小于x的最大元素如果不存在前驱则返回None

        """

        if self.root.min_val is None:

            return None

        if x > self.root.max_val:

            return self.root.max_val

        if self.root.universe_size <= BASE_LEVEL_SPLIT_SIZE:

            # 在基础宇宙中搜索

            for val in range(x - 1, -1, -1):

                if self.search(val):

                    return val

            return None

        

        # 递归查找前驱

        split_size = self.root._compute_split_size(self.root.universe_size)

        high_index = self.root._high(x, split_size)

        cluster = self.root.cluster[high_index]

        

        if cluster is not None and cluster.max_val is not None:

            low_value = self.root._low(x, split_size)

            if cluster.min_val is not None and low_value > cluster.min_val:

                # 前驱在同一个cluster中

                return high_index * split_size + cluster.max_val

        

        # 前驱在更低的cluster中

        if high_index > 0:

            prev_cluster_index = self._max_in_summary(self.root.summary, high_index - 1)

            if prev_cluster_index is not None:

                prev_cluster = self.root.cluster[prev_cluster_index]

                if prev_cluster is not None and prev_cluster.max_val is not None:

                    return prev_cluster_index * split_size + prev_cluster.max_val

        

        # 检查当前cluster的最小值之前是否有更小的值

        if self.root.min_val < x:

            return self.root.min_val

        return None

    

    def successor(self, x: int) -> Optional[int]:

        """

        查找元素x的后继即大于x的最小元素

        

        Args:

            x: 参考元素值

            

        Returns:

            大于x的最小元素如果不存在后继则返回None

        """

        if self.root.min_val is None:

            return None

        if x < self.root.min_val:

            return self.root.min_val

        if self.root.universe_size <= BASE_LEVEL_SPLIT_SIZE:

            for val in range(x + 1, self.root.universe_size):

                if self.search(val):

                    return val

            return None

        

        split_size = self.root._compute_split_size(self.root.universe_size)

        high_index = self.root._high(x, split_size)

        cluster = self.root.cluster[high_index]

        

        if cluster is not None and cluster.min_val is not None:

            low_value = self.root._low(x, split_size)

            if low_value < cluster.max_val:

                # 后继在同一个cluster中

                return high_index * split_size + cluster.min_val

        

        # 后继在后继cluster中

        if high_index < len(self.root.cluster) - 1:

            next_cluster_index = self._min_in_summary(self.root.summary, high_index + 1)

            if next_cluster_index is not None:

                next_cluster = self.root.cluster[next_cluster_index]

                if next_cluster is not None and next_cluster.min_val is not None:

                    return next_cluster_index * split_size + next_cluster.min_val

        

        return None

    

    def _max_in_summary(self, summary_node: VanEmdeBoasNode, high: int) -> Optional[int]:

        """

        在summary中查找不超过high的最大索引

        

        Args:

            summary_node: summary节点

            high: 索引的上界

            

        Returns:

            不超过high的最大索引如果不存在则返回None

        """

        if summary_node.max_val is not None and summary_node.max_val <= high:

            return summary_node.max_val

        return None

    

    def _min_in_summary(self, summary_node: VanEmdeBoasNode, low: int) -> Optional[int]:

        """

        在summary中查找不小于low的最小索引

        

        Args:

            summary_node: summary节点

            low: 索引的下界

            

        Returns:

            不小于low的最小索引如果不存在则返回None

        """

        if summary_node.min_val is not None and summary_node.min_val >= low:

            return summary_node.min_val

        return None

    

    def delete(self, x: int) -> None:

        """

        从vEB树中删除元素x

        

        删除操作比较复杂因为需要处理cluster变为空的情况

        此时需要从summary中移除该cluster的索引并可能更新当前cluster的

        最小值和最大值

        

        Args:

            x: 要删除的元素值

        """

        if self.root.min_val is None:

            return

        if self.root.min_val == self.root.max_val == x:

            self.root.min_val = None

            self.root.max_val = None

            return

        

        if self.root.universe_size <= BASE_LEVEL_SPLIT_SIZE:

            self.root.max_val = None

            self.root.min_val = None

            return

        

        split_size = self.root._compute_split_size(self.root.universe_size)

        high_index = self.root._high(x, split_size)

        low_value = self.root._low(x, split_size)

        cluster = self.root.cluster[high_index]

        

        if cluster is None:

            return

        

        if cluster.min_val == cluster.max_val == low_value:

            # cluster中的唯一元素被删除需要更新summary

            self.root.cluster[high_index] = None

            if high_index == self.root.summary.min_val:

                # 需要找到下一个非空的cluster

                new_min = self._find_next_summary_min(self.root.summary)

                if new_min is not None:

                    self.root.min_val = new_min * split_size + self.root.cluster[new_min].min_val

                else:

                    self.root.min_val = self.root.max_val

            if high_index == self.root.summary.max_val:

                new_max = self._find_prev_summary_max(self.root.summary)

                if new_max is not None:

                    self.root.max_val = new_max * split_size + self.root.cluster[new_max].max_val

                else:

                    self.root.max_val = self.root.min_val

    

    def _find_next_summary_min(self, summary_node: VanEmdeBoasNode) -> Optional[int]:

        """找到summary中的下一个最小索引"""

        if summary_node.min_val is not None:

            return summary_node.min_val

        return None

    

    def _find_prev_summary_max(self, summary_node: VanEmdeBoasNode) -> Optional[int]:

        """找到summary中的前一个最大索引"""

        if summary_node.max_val is not None:

            return summary_node.max_val

        return None





def compute_van_emde_boas_layout_depth(universe_size: int) -> int:

    """

    计算给定宇宙大小下vEB树的布局深度

    

    van Emde Boas树的关键特性之一是其递归布局深度为O(log log u)

    其中u是宇宙大小该函数通过递归计算来验证这一性质

    

    Args:

        universe_size: 宇宙大小必须是2的幂

        

    Returns:

        vEB树的递归深度

    """

    depth = 0

    size = universe_size

    while size > BASE_LEVEL_SPLIT_SIZE:

        size = int(math.sqrt(size))

        depth += 1

    return depth





def simulate_cache_aware_access(tree: VanEmdeBoasTree, operations: List[Tuple[str, int]]) -> int:

    """

    模拟缓存感知的访问模式并计算模拟的缓存未命中次数

    

    该函数通过跟踪每次操作访问的内存块来模拟缓存行为假设缓存行大小

    与vEB树的节点大小相关联虽然这不是真正的缓存无关实现但可以展示

    vEB树设计如何减少缓存未命中

    

    Args:

        tree: van Emde Boas树

        operations: 操作列表每个元素为(操作名, 元素值)

        

    Returns:

        模拟的缓存未命中次数

    """

    cache_miss_count = 0

    accessed_blocks = set()

    

    for op_name, value in operations:

        if op_name == "insert":

            tree.insert(value)

        elif op_name == "search":

            tree.search(value)

        elif op_name == "delete":

            tree.delete(value)

        

        # 模拟访问根节点

        root_block = id(tree.root) // 64

        if root_block not in accessed_blocks:

            cache_miss_count += 1

            accessed_blocks.add(root_block)

    

    return cache_miss_count





# 时间复杂度说明:

# =============================================================================

# 基础操作的时间复杂度:

#   - 插入(insert):        O(log log u) 平均时间

#   - 搜索(search):        O(log log u) 平均时间

#   - 前驱(predecessor):   O(log log u) 平均时间

#   - 后继(successor):     O(log log u) 平均时间

#   - 删除(delete):        O(log log u) 平均时间

# 其中u为宇宙大小即元素取值范围[0, u-1]

#

# 空间复杂度:

#   - 总空间: O(u) 其中u为宇宙大小

#   - 每个节点额外维护min和max值使得操作时可以快速跳过空子树

#

# 缓存无关特性:

#   - vEB树的递归布局使得每次操作访问的内存块大小与该操作涉及的数据量成正比

#   - 高层操作访问较大的连续内存块低层操作访问较小的内存块

#   - 这种自相似的布局使得算法自然地适应内存层次结构的各个级别

#   - 理论上缓存未命中次数为O(log log u)当宇宙大小u远大于缓存大小时

#     这比标准的二叉搜索树结构的O(log u)缓存未命中次数更优





if __name__ == "__main__":

    # 测试 van Emde Boas 树的基本功能

    print("=" * 70)

    print("van Emde Boas 树 - 缓存无关数据结构测试")

    print("=" * 70)

    

    # 创建宇宙大小为16的vEB树

    universe = 16

    veb_tree = VanEmdeBoasTree(universe)

    print(f"\n创建宇宙大小为 {universe} 的 vEB 树")

    

    # 测试插入操作

    test_elements = [3, 5, 7, 2, 8, 9, 1, 4]

    print(f"\n插入测试元素: {test_elements}")

    for elem in test_elements:

        veb_tree.insert(elem)

        print(f"  插入 {elem}: min={veb_tree.root.min_val}, max={veb_tree.root.max_val}")

    

    # 测试搜索操作

    print(f"\n搜索测试:")

    search_elements = [3, 5, 10, 1]

    for elem in search_elements:

        found = veb_tree.search(elem)

        print(f"  搜索 {elem}: {'找到' if found else '未找到'}")

    

    # 测试前驱操作

    print(f"\n前驱查询测试:")

    predecessor_tests = [6, 5, 0, 10]

    for elem in predecessor_tests:

        pred = veb_tree.predecessor(elem)

        print(f"  {elem} 的前驱: {pred}")

    

    # 测试后继操作

    print(f"\n后继查询测试:")

    successor_tests = [4, 5, 8, 0]

    for elem in successor_tests:

        succ = veb_tree.successor(elem)

        print(f"  {elem} 的后继: {succ}")

    

    # 测试删除操作

    print(f"\n删除测试:")

    delete_elements = [5, 3, 7]

    for elem in delete_elements:

        veb_tree.delete(elem)

        print(f"  删除 {elem}: min={veb_tree.root.min_val}, max={veb_tree.root.max_val}")

    

    # 验证删除后的搜索

    print(f"\n删除后搜索测试:")

    for elem in [3, 5]:

        found = veb_tree.search(elem)

        print(f"  搜索 {elem}: {'找到' if found else '未找到'}")

    

    # 测试布局深度计算

    print(f"\n不同宇宙大小的vEB树布局深度:")

    for u in [256, 1024, 65536, 16777216]:

        depth = compute_van_emde_boas_layout_depth(u)

        print(f"  宇宙大小 {u:>10}: 深度 {depth}")

    

    # 测试缓存感知访问

    print(f"\n缓存感知访问模拟:")

    ops = [("insert", 3), ("insert", 7), ("search", 5), ("insert", 10), ("search", 3)]

    cache_misses = simulate_cache_aware_access(veb_tree, ops)

    print(f"  {len(ops)} 个操作的模拟缓存未命中次数: {cache_misses}")

    

    # 大规模插入测试

    print(f"\n大规模测试 (宇宙大小 1024, 插入 500 个随机元素):")

    import random

    random.seed(42)

    large_tree = VanEmdeBoasTree(1024)

    large_elements = [random.randint(0, 1023) for _ in range(500)]

    for elem in large_elements:

        large_tree.insert(elem)

    print(f"  插入完成: min={large_tree.root.min_val}, max={large_tree.root.max_val}")

    

    # 验证数据完整性

    found_count = sum(1 for e in large_elements if large_tree.search(e))

    print(f"  搜索验证: {found_count}/{len(large_elements)} 个元素仍可找到")

    

    print("\n" + "=" * 70)

    print("测试完成!")

    print("=" * 70)

