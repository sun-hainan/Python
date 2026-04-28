"""
斐波那契堆 (Fibonacci Heap)
=============================

一种用于实现优先队列的堆结构，以摊销分析著称。
与二叉堆相比，斐波那契堆在摊销意义上提供更好的时间复杂度。

摊销复杂度：
- insert(x):          O(1)
- find_min():         O(1)
- extract_min():      O(log n) 摊销
- decrease_key(x, k): O(1) 摊销
- delete(x):          O(log n) 摊销
- merge(h1, h2):      O(1)

核心结构：
- 最小堆有序的树集合（根表）
- 指针指向最小节点
- 度和 rank（子树根节点数）信息用于合并

本实现：含度数表的 Fibonacci 堆（度数合并策略）
"""

from typing import Optional, List, Callable


class FibonacciHeapNode:
    """
    斐波那契堆的节点
    
    Attributes:
        key: 节点的键值
        degree: 当前节点的度（子节点数量）
        marked: 节点是否被标记（用于 decrease_key）
        parent: 父节点指针
        child: 指向某个子节点（子节点通过 left/right 形成循环链表）
        left: 左兄弟指针
        right: 右兄弟指针
    """
    
    def __init__(self, key: int):
        """
        初始化节点
        
        Args:
            key: 节点的关键字值
        """
        self.key: int = key                    # 节点键值
        self.degree: int = 0                   # 子树根节点数量（度）
        self.marked: bool = False              # 是否被标记（删除时用）
        self.parent: Optional[FibonacciHeapNode] = None  # 父节点
        self.child: Optional[FibonacciHeapNode] = None   # 某个子节点
        # 循环双向链表指针（根节点之间或兄弟之间）
        self.left: FibonacciHeapNode = self
        self.right: FibonacciHeapNode = self


class FibonacciHeap:
    """
    斐波那契堆
    
    实现优先队列的核心操作，摊销代价优秀。
    通过度数表（degree_table）合并相同度的树。
    
    Attributes:
        min_node: 指向包含最小键的节点
        total_nodes: 堆中节点总数
        degree_table: 按度索引的根节点列表（最多 log_phi(n) 个度）
    """
    
    def __init__(self):
        """
        初始化空的斐波那契堆
        """
        self.min_node: Optional[FibonacciHeapNode] = None  # 最小节点指针
        self.total_nodes: int = 0                          # 节点总数
        self.degree_table: List[Optional[FibonacciHeapNode]] = []  # 度数表
    
    def is_empty(self) -> bool:
        """
        判断堆是否为空
        
        Returns:
            空返回 True，否则返回 False
        """
        return self.total_nodes == 0
    
    def insert(self, key: int) -> FibonacciHeapNode:
        """
        插入新节点
        
        Args:
            key: 要插入的键值
        
        Returns:
            创建的新节点
        """
        new_node = FibonacciHeapNode(key)
        
        # 将新节点加入根表的循环链表中
        if self.min_node is None:
            # 堆为空，新节点自身形成循环链表
            new_node.left = new_node
            new_node.right = new_node
            self.min_node = new_node
        else:
            # 将 new_node 插入到 min_node 右侧
            self._link_node_to_root_list(new_node)
            # 更新最小节点
            if key < self.min_node.key:
                self.min_node = new_node
        
        self.total_nodes += 1
        return new_node
    
    def _link_node_to_root_list(self, node: FibonacciHeapNode) -> None:
        """
        将节点加入根表（min_node 的右侧）
        
        Args:
            node: 要加入根表的节点
        """
        node.left = self.min_node
        node.right = self.min_node.right
        self.min_node.right.left = node
        self.min_node.right = node
    
    def find_min(self) -> Optional[int]:
        """
        返回最小键值（不删除）
        
        Returns:
            最小键值，堆为空返回 None
        """
        if self.min_node is None:
            return None
        return self.min_node.key
    
    def extract_min(self) -> Optional[int]:
        """
        抽取最小节点（extract-min）
        
        步骤：
        1. 将 min_node 从根表中移除
        2. 将其子节点加入根表
        3. 通过度数表合并根表中的树
        4. 更新 min_node
        
        Returns:
            被删除的最小键值，堆为空返回 None
        """
        if self.min_node is None:
            return None
        
        min_key = self.min_node.key
        old_min = self.min_node
        
        # 将 min_node 的每个子节点加入根表
        if old_min.child is not None:
            child = old_min.child
            for _ in range(old_min.degree):
                next_child = child.right
                self._link_node_to_root_list(child)
                child.parent = None
                child = next_child
        
        # 从根表中移除 min_node
        if old_min == old_min.right:
            # min_node 是唯一根节点
            self.min_node = None
        else:
            old_min.right.left = old_min.left
            old_min.left.right = old_min.right
            self.min_node = old_min.right
        
        self.total_nodes -= 1
        
        # 合并根表（度数表）
        if self.min_node is not None:
            self._consolidate()
        
        return min_key
    
    def _consolidate(self) -> None:
        """
        通过度数表合并根表中的树
        
        原理：将所有根节点按度放入度数表，
        如果已有相同度的树，则合并（度+1），直到无冲突。
        """
        # 计算最大可能的度（O(log_phi(n))）
        max_degree = int(self.total_nodes ** 0.5) + 2
        self.degree_table = [None] * max_degree
        
        # 遍历根表，将每棵树加入度数表
        current = self.min_node
        roots_to_process = []
        
        # 收集所有根节点
        if current is not None:
            start = current
            while True:
                roots_to_process.append(current)
                current = current.right
                if current == start:
                    break
        
        # 处理每个根节点
        for root in roots_to_process:
            root.parent = None  # 解除父子关系
            degree = root.degree
            # 合并相同度的树
            while self.degree_table[degree] is not None:
                other = self.degree_table[degree]
                # 确保 root 是较小键的根
                if root.key > other.key:
                    root, other = other, root
                # 将 other 合并为 root 的子节点
                self._heap_link(other, root)
                self.degree_table[degree] = None
                degree += 1
            self.degree_table[degree] = root
        
        # 从度数表重建根表，找到新的最小节点
        self.min_node = None
        for root in self.degree_table:
            if root is not None:
                if self.min_node is None or root.key < self.min_node.key:
                    self.min_node = root
    
    def _heap_link(self, y: FibonacciHeapNode, x: FibonacciHeapNode) -> None:
        """
        将节点 y 从根表中移除，成为 x 的子节点
        
        Args:
            y: 要合并的根节点（将被作为子节点）
            x: 目标父节点
        """
        # 从根表中移除 y
        y.right.left = y.left
        y.left.right = y.right
        
        # 将 y 添加为 x 的子节点
        if x.child is None:
            x.child = y
            y.left = y
            y.right = y
        else:
            y.left = x.child
            y.right = x.child.right
            x.child.right.left = y
            x.child.right = y
        
        y.parent = x
        x.degree += 1
        y.marked = False
    
    def decrease_key(self, node: FibonacciHeapNode, new_key: int) -> None:
        """
        减小指定节点的键值
        
        Args:
            node: 目标节点
            new_key: 新的键值（必须小于等于原键值）
        """
        if new_key > node.key:
            raise ValueError("新键值必须小于等于原键值")
        
        node.key = new_key
        parent = node.parent
        
        # 如果节点不在根表且违反了最小堆性质，需要剪切
        if parent is not None and node.key < parent.key:
            # 从父节点剪切，并级联剪切
            self._cut(node, parent)
            self._cascading_cut(parent)
        
        # 更新最小节点
        if node.key < self.min_node.key:
            self.min_node = node
    
    def _cut(self, x: FibonacciHeapNode, y: FibonacciHeapNode) -> None:
        """
        将节点 x 从 y 的子链表中剪切，加入根表
        
        Args:
            x: 要剪切的节点
            y: x 的父节点
        """
        # 从 y 的子链表中移除 x
        if x.right == x:
            # x 是唯一子节点
            y.child = None
        else:
            x.right.left = x.left
            x.left.right = x.right
            y.child = x.right
        
        y.degree -= 1
        
        # 将 x 加入根表
        self._link_node_to_root_list(x)
        x.parent = None
        x.marked = False  # 剪切到根表后取消标记
    
    def _cascading_cut(self, y: FibonacciHeapNode) -> None:
        """
        级联剪切：如果父节点已被标记，则也剪切父节点
        
        Args:
            y: 父节点
        """
        parent = y.parent
        if parent is not None:
            if not y.marked:
                # 首次被剪切，标记
                y.marked = True
            else:
                # 已被标记，再次剪切
                self._cut(y, parent)
                self._cascading_cut(parent)
    
    def delete(self, node: FibonacciHeapNode) -> None:
        """
        删除指定节点（将键值降到负无穷再抽取最小）
        
        Args:
            node: 要删除的节点
        """
        # 通过 decrease_key 将键值降到极小（负无穷）
        self.decrease_key(node, float('-inf'))
        self.extract_min()
    
    def merge(self, other: 'FibonacciHeap') -> 'FibonacciHeap':
        """
        合并两个斐波那契堆
        
        Args:
            other: 另一个斐波那契堆
        
        Returns:
            合并后的新斐波那契堆
        """
        new_heap = FibonacciHeap()
        
        # 合并根表
        if self.min_node is None:
            new_heap.min_node = other.min_node
        elif other.min_node is None:
            new_heap.min_node = self.min_node
        else:
            # 将两个循环链表合并
            self_min_right = self.min_node.right
            other_min_left = other.min_node.left
            
            self.min_node.right = other.min_node
            other.min_node.left = self.min_node
            other_min_left.right = self_min_right
            self_min_right.left = other_min_left
            
            # 更新最小节点
            if other.min_node.key < self.min_node.key:
                new_heap.min_node = other.min_node
            else:
                new_heap.min_node = self.min_node
        
        new_heap.total_nodes = self.total_nodes + other.total_nodes
        return new_heap
    
    def get_size(self) -> int:
        """
        返回堆中节点数量
        
        Returns:
            节点总数
        """
        return self.total_nodes


# ============================ 测试代码 ============================
if __name__ == "__main__":
    print("=" * 60)
    print("斐波那契堆 (Fibonacci Heap) 测试")
    print("=" * 60)
    
    # 创建斐波那契堆
    fib_heap = FibonacciHeap()
    
    # 测试插入
    print("\n--- 测试插入 ---")
    keys_to_insert = [10, 3, 18, 7, 2, 15, 1, 6, 4, 8]
    for key in keys_to_insert:
        node = fib_heap.insert(key)
        print(f"插入 {key}: 堆大小={fib_heap.get_size()}, 最小值={fib_heap.find_min()}")
    
    # 测试 find_min
    print(f"\n当前最小值: {fib_heap.find_min()}")
    
    # 测试 extract_min
    print("\n--- 测试 extract_min ---")
    for _ in range(5):
        min_val = fib_heap.extract_min()
        print(f"抽取最小值: {min_val}, 新最小值={fib_heap.find_min()}, 堆大小={fib_heap.get_size()}")
    
    # 重新插入测试 decrease_key
    print("\n--- 测试 decrease_key ---")
    node_18 = fib_heap.insert(18)
    print(f"插入 18: 最小值={fib_heap.find_min()}")
    fib_heap.decrease_key(node_18, 1)
    print(f"将 18 减小到 1: 最小值={fib_heap.find_min()}")
    
    # 测试 merge
    print("\n--- 测试 merge ---")
    h1 = FibonacciHeap()
    for k in [5, 12, 3]:
        h1.insert(k)
    
    h2 = FibonacciHeap()
    for k in [9, 1, 7]:
        h2.insert(k)
    
    merged = h1.merge(h2)
    print(f"合并后最小值: {merged.find_min()}")
    print(f"合并后大小: {merged.get_size()}")
    
    # 连续抽取验证堆性质
    print("\n--- 连续抽取验证 ---")
    result = []
    while not merged.is_empty():
        result.append(merged.extract_min())
    print(f"按顺序抽取: {result}")
    
    # 复杂度总结
    print("\n--- 斐波那契堆 vs 二叉堆 复杂度对比 ---")
    print(f"{'操作':<20} {'斐波那契堆(摊销)':<20} {'二叉堆':<15}")
    print("-" * 55)
    print(f"{'insert':<20} {'O(1)':<20} {'O(log n)':<15}")
    print(f"{'find_min':<20} {'O(1)':<20} {'O(1)':<15}")
    print(f"{'extract_min':<20} {'O(log n)':<20} {'O(log n)':<15}")
    print(f"{'decrease_key':<20} {'O(1)':<20} {'O(log n)':<15}")
    print(f"{'delete':<20} {'O(log n)':<20} {'O(log n)':<15}")
    print(f"{'merge':<20} {'O(1)':<20} {'O(n)':<15}")
