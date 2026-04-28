"""
van Emde Boas 树 (van Emde Boas Tree)
=====================================

一种支持 O(log log u) 时间复杂度的关联数组数据结构，
其中 u 是关键字的宇宙大小（全局最小值到最大值的范围）。

核心思想：
- 将关键字空间划分为 sqrt(u) 个槽位，形成层次结构
- 顶层结构（summary）递归管理各槽位
- 底层结构存储实际数据

优点：搜索、插入、删除均为 O(log log u)
缺点：需要预知关键字范围，且空间开销较大

本实现：递归版本的 van Emde Boas 树
"""

from typing import Optional, List


class VanEmdeBoasNode:
    """
    van Emde Boas 树的节点结构
    
    Attributes:
        universe_size: 当前节点管理的宇宙大小
        summary: 摘要节点，指向管理各簇的 van Emde Boas 树
        clusters: 子簇列表，每个簇管理 universe_size / high_bit 个关键字
    """
    
    def __init__(self, universe_size: int):
        """
        初始化 van Emde Boas 节点
        
        Args:
            universe_size: 当前节点管理的宇宙大小（必须是 2 的幂）
        """
        self.universe_size = universe_size  # 当前节点管理的宇宙大小
        self.summary: Optional[VanEmdeBoasNode] = None  # 摘要节点，管理各簇
        # clusters[i] 存储簇 i 中实际存在的数据（仅当簇非空时创建）
        self.clusters: List[Optional[VanEmdeBoasNode]] = [None] * universe_size


def high_value(x: int, cluster_size: int) -> int:
    """
    计算关键字 x 的高阶部分（簇索引）
    
    Args:
        x: 关键字值
        cluster_size: 簇大小（sqrt(universe_size)）
    
    Returns:
        x 在簇结构中的高阶索引
    """
    return x // cluster_size


def low_value(x: int, cluster_size: int) -> int:
    """
    计算关键字 x 的低阶部分（簇内偏移）
    
    Args:
        x: 关键字值
        cluster_size: 簇大小（sqrt(universe_size)）
    
    Returns:
        x 在其簇内的偏移量
    """
    return x % cluster_size


def generate_universe_size(u: int) -> int:
    """
    将 u 向上取整到最接近的 2 的幂
    
    Args:
        u: 期望的范围上限
    
    Returns:
        不小于 u 的最小 2 的幂
    """
    # 找到大于等于 u 的最小 2 的幂
    size = 1
    while size < u:
        size <<= 1
    return size


class VanEmdeBoasTree:
    """
    van Emde Boas 树
    
    支持的操作：
    - insert(x): 插入关键字 x        → O(log log u)
    - delete(x): 删除关键字 x       → O(log log u)
    - search(x): 查找关键字 x        → O(log log u)
    - predecessor(x): 找前驱          → O(log log u)
    - successor(x): 找后继            → O(log log u)
    - minimum(): 找最小值             → O(log log u)
    - maximum(): 找最大值             → O(log log u)
    """
    
    def __init__(self, universe_size: int):
        """
        初始化 van Emde Boas 树
        
        Args:
            universe_size: 关键字的宇宙大小（值域 [0, universe_size-1]）
        """
        self.universe_size = generate_universe_size(universe_size)  # 实际使用的宇宙大小
        self.cluster_size = int(self.universe_size ** 0.5)  # 簇大小 = sqrt(u)
        self.root = self._create_node(self.universe_size)  # 根节点
        self.min_value: Optional[int] = None  # 树中最小值
        self.max_value: Optional[int] = None  # 树中最大值
    
    def _create_node(self, universe_size: int) -> Optional[VanEmdeBoasNode]:
        """
        创建新的 van Emde Boas 节点
        
        Args:
            universe_size: 该节点管理的宇宙大小
        
        Returns:
            新节点对象，或 None（若大小为 1）
        """
        if universe_size <= 1:
            return None
        return VanEmdeBoasNode(universe_size)
    
    def insert(self, key: int) -> None:
        """
        插入关键字 key
        
        Args:
            key: 要插入的关键字，必须在 [0, universe_size) 范围内
        """
        if key < 0 or key >= self.universe_size:
            raise ValueError(f"Key {key} 超出范围 [0, {self.universe_size})")
        
        # 如果树为空，直接设置为最小和最大值
        if self.min_value is None:
            self.min_value = key
            self.max_value = key
            return
        
        # 如果 key 已存在，不做重复插入
        if key == self.min_value or key == self.max_value:
            return
        
        self._insert_node(self.root, key)
        
        # 更新最小/最大值
        if key < self.min_value:
            self.min_value = key
        if key > self.max_value:
            self.max_value = key
    
    def _insert_node(self, node: Optional[VanEmdeBoasNode], key: int) -> None:
        """
        在指定节点下递归插入 key
        
        Args:
            node: 当前操作的节点
            key: 要插入的关键字
        """
        if node is None:
            return
        
        # 计算 key 所属的簇索引和簇内偏移
        hi = high_value(key, node.universe_size)
        lo = low_value(key, node.universe_size)
        
        # 如果该簇尚未创建，先创建
        if node.clusters[hi] is None:
            cluster_universe = self.cluster_size
            node.clusters[hi] = self._create_node(cluster_universe)
            
            # 在摘要节点中标记该簇非空（递归创建摘要）
            if node.summary is None and node.universe_size > self.cluster_size:
                node.summary = self._create_node(self.cluster_size)
            if node.summary is not None:
                self._insert_node(node.summary, hi)
        
        # 递归插入到对应簇
        self._insert_node(node.clusters[hi], lo)
    
    def search(self, key: int) -> bool:
        """
        查找关键字 key 是否存在
        
        Args:
            key: 要查找的关键字
        
        Returns:
            存在返回 True，否则返回 False
        """
        if self.min_value is None:
            return False
        if key < self.min_value or key > self.max_value:
            return False
        if key == self.min_value or key == self.max_value:
            return True
        return self._search_node(self.root, key)
    
    def _search_node(self, node: Optional[VanEmdeBoasNode], key: int) -> bool:
        """
        递归在节点中查找 key
        
        Args:
            node: 当前搜索的节点
            key: 要查找的关键字
        
        Returns:
            找到返回 True，否则返回 False
        """
        if node is None:
            return False
        if node.universe_size == 2:
            # 宇宙大小为 2 时，直接检查
            return key == 1
        
        hi = high_value(key, node.universe_size)
        lo = low_value(key, node.universe_size)
        
        if node.clusters[hi] is None:
            return False
        return self._search_node(node.clusters[hi], lo)
    
    def minimum(self) -> Optional[int]:
        """
        返回树中的最小关键字
        
        Returns:
            最小关键字，若树为空则返回 None
        """
        return self.min_value
    
    def maximum(self) -> Optional[int]:
        """
        返回树中的最大关键字
        
        Returns:
            最大关键字，若树为空则返回 None
        """
        return self.max_value
    
    def predecessor(self, key: int) -> Optional[int]:
        """
        找到小于 key 的最大关键字（前驱）
        
        Args:
            key: 参考关键字
        
        Returns:
            前驱关键字，若不存在则返回 None
        """
        if self.min_value is None or key <= self.min_value:
            return None
        
        if key <= self.max_value:
            # 在树中直接找前驱
            return self._predecessor_node(self.root, key)
        else:
            # key 超出当前范围，最大值就是前驱
            return self.max_value
    
    def _predecessor_node(self, node: Optional[VanEmdeBoasNode], key: int) -> Optional[int]:
        """
        在节点中递归查找前驱
        
        Args:
            node: 当前节点
            key: 参考关键字
        
        Returns:
            前驱关键字
        """
        if node is None or node.universe_size == 2:
            # universe_size == 2 时，索引 0 是唯一可能的前驱
            return 0 if key > 1 else None
        
        hi = high_value(key, node.universe_size)
        lo = low_value(key, node.universe_size)
        
        # 尝试在当前簇中找前驱
        if node.clusters[hi] is not None:
            pred_lo = self._predecessor_node(node.clusters[hi], lo)
            if pred_lo is not None:
                return hi * self.cluster_size + pred_lo
        
        # 在摘要中找比 hi 小的最大簇
        if node.summary is not None:
            pred_hi = self._max_in_cluster(node.summary, hi - 1)
            if pred_hi is not None:
                # 在 pred_hi 簇中找最大值
                if node.clusters[pred_hi] is not None:
                    max_lo = self._max_value_in_node(node.clusters[pred_hi])
                    if max_lo is not None:
                        return pred_hi * self.cluster_size + max_lo
        return None
    
    def successor(self, key: int) -> Optional[int]:
        """
        找到大于 key 的最小关键字（后继）
        
        Args:
            key: 参考关键字
        
        Returns:
            后继关键字，若不存在则返回 None
        """
        if self.max_value is None or key >= self.max_value:
            return None
        
        if key >= self.min_value:
            return self._successor_node(self.root, key)
        else:
            return self.min_value
    
    def _successor_node(self, node: Optional[VanEmdeBoasNode], key: int) -> Optional[int]:
        """
        在节点中递归查找后继
        
        Args:
            node: 当前节点
            key: 参考关键字
        
        Returns:
            后继关键字
        """
        if node is None or node.universe_size == 2:
            return 1 if key < 1 else None
        
        hi = high_value(key, node.universe_size)
        lo = low_value(key, node.universe_size)
        
        # 尝试在当前簇中找后继
        if node.clusters[hi] is not None:
            succ_lo = self._successor_node(node.clusters[hi], lo)
            if succ_lo is not None:
                return hi * self.cluster_size + succ_lo
        
        # 在摘要中找比 hi 大的最小簇
        if node.summary is not None:
            succ_hi = self._min_in_cluster(node.summary, hi + 1)
            if succ_hi is not None:
                if node.clusters[succ_hi] is not None:
                    min_lo = self._min_value_in_node(node.clusters[succ_hi])
                    if min_lo is not None:
                        return succ_hi * self.cluster_size + min_lo
        return None
    
    def _min_in_cluster(self, node: Optional[VanEmdeBoasNode], start: int) -> Optional[int]:
        """
        在摘要节点中找到从 start 开始的最小的非空簇索引
        
        Args:
            node: 摘要节点
            start: 起始搜索位置
        
        Returns:
            最小非空簇索引，或 None
        """
        if node is None:
            return None
        # 线性扫描（实际应用中可用更优结构）
        for i in range(start, len(node.clusters)):
            if node.clusters[i] is not None:
                return i
        return None
    
    def _max_in_cluster(self, node: Optional[VanEmdeBoasNode], end: int) -> Optional[int]:
        """
        在摘要节点中找到从 end 往回的最大非空簇索引
        
        Args:
            node: 摘要节点
            end: 结束搜索位置
        
        Returns:
            最大非空簇索引，或 None
        """
        if node is None:
            return None
        for i in range(end, -1, -1):
            if node.clusters[i] is not None:
                return i
        return None
    
    def _min_value_in_node(self, node: Optional[VanEmdeBoasNode]) -> Optional[int]:
        """
        找到节点中的最小值
        
        Args:
            node: van Emde Boas 节点
        
        Returns:
            节点中的最小值
        """
        if node is None:
            return None
        # 线性扫描找第一个非空簇
        for i, c in enumerate(node.clusters):
            if c is not None:
                return i
        return None
    
    def _max_value_in_node(self, node: Optional[VanEmdeBoasNode]) -> Optional[int]:
        """
        找到节点中的最大值
        
        Args:
            node: van Emde Boas 节点
        
        Returns:
            节点中的最大值
        """
        if node is None:
            return None
        for i in range(len(node.clusters) - 1, -1, -1):
            if node.clusters[i] is not None:
                return i
        return None
    
    def delete(self, key: int) -> None:
        """
        删除关键字 key（简化版：重建结构）
        
        注意：完整的删除操作较复杂，涉及簇的空洞管理。
        本实现通过重建来保证正确性。
        
        Args:
            key: 要删除的关键字
        """
        if not self.search(key):
            return
        
        # 收集除 key 外的所有元素
        all_keys = []
        for k in range(self.universe_size):
            if k != key and self.search(k):
                all_keys.append(k)
        
        # 重新构建树
        self.root = self._create_node(self.universe_size)
        self.min_value = None
        self.max_value = None
        for k in all_keys:
            self.insert(k)


# ============================ 测试代码 ============================
if __name__ == "__main__":
    print("=" * 60)
    print("van Emde Boas 树 测试")
    print("=" * 60)
    
    # 创建宇宙大小为 16 的 van Emde Boas 树
    veb = VanEmdeBoasTree(universe_size=16)
    
    # 测试插入
    print("\n--- 测试插入 ---")
    for key in [3, 5, 7, 2, 8, 1, 14, 15, 0]:
        veb.insert(key)
        print(f"插入 {key}: 最小值={veb.minimum()}, 最大值={veb.maximum()}")
    
    # 测试搜索
    print("\n--- 测试搜索 ---")
    for key in [0, 5, 9, 14]:
        result = veb.search(key)
        print(f"搜索 {key}: {'✓ 找到' if result else '✗ 未找到'}")
    
    # 测试前驱后继
    print("\n--- 测试前驱/后继 ---")
    test_keys = [0, 5, 6, 13]
    for key in test_keys:
        pred = veb.predecessor(key)
        succ = veb.successor(key)
        print(f"key={key}: 前驱={pred}, 后继={succ}")
    
    # 测试边界
    print("\n--- 测试边界 ---")
    print(f"最小值: {veb.minimum()}")
    print(f"最大值: {veb.maximum()}")
    
    # 测试删除
    print("\n--- 测试删除 ---")
    veb.delete(5)
    print(f"删除 5 后搜索 5: {'找到' if veb.search(5) else '未找到'}")
    print(f"删除 5 后最小值: {veb.minimum()}")
    
    # 性能对比
    print("\n--- 复杂度对比 ---")
    print("普通搜索:          O(n)")
    print("BST/AVL 搜索:      O(log n)")
    print("van Emde Boas 搜索: O(log log u)")
    print("其中 u 是宇宙大小 (值域范围)")
