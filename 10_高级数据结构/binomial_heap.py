"""
二项堆 (Binomial Heap)
======================

一种支持合并操作的优先队列数据结构，由多个二项树组成。
每个二项树 B_k 是度数为 k 的有序树，具有独特的递归结构。

核心性质：
- B_0 是单节点树
- B_k 由两个 B_{k-1} 树合并而成（根节点度数+1）
- B_k 有 2^k 个节点，高度为 k

时间复杂度：
- insert(x):       O(log n) 最坏，O(1) 期望
- find_min():      O(log n)  // 需遍历根表
- extract_min():   O(log n)
- decrease_key():  O(log n)
- delete():       O(log n)
- merge(h1, h2):   O(log n)

本实现：二项堆的完整操作，含减关键值和删除
"""

from typing import Optional, List


class BinomialTreeNode:
    """
    二项堆的树节点
    
    Attributes:
        key: 节点键值
        degree: 子树根节点的数量（度）
        parent: 父节点指针
        child: 指向某个子节点（最左子节点）
        sibling: 下一个兄弟节点
    """
    
    def __init__(self, key: int):
        """
        初始化二项树节点
        
        Args:
            key: 节点的关键字值
        """
        self.key: int = key                        # 节点键值
        self.degree: int = 0                       # 子树根节点数量
        self.parent: Optional[BinomialTreeNode] = None  # 父节点
        self.child: Optional[BinomialTreeNode] = None   # 最左子节点
        self.sibling: Optional[BinomialTreeNode] = None  # 右兄弟节点


class BinomialHeap:
    """
    二项堆
    
    由多个二项树（B_k）组成的森林，满足：
    - 每个 B_k 至多出现一次
    - 按度从小到大排列（根表是有序的）
    
    Attributes:
        heads: 根表头节点列表（heads[k] 指向度为 k 的树根）
        min_node: 指向包含最小键的节点（缓存，加速 find_min）
    """
    
    def __init__(self):
        """
        初始化空的二项堆
        """
        self.heads: List[Optional[BinomialTreeNode]] = []  # 按度索引的根表
        self.min_node: Optional[BinomialTreeNode] = None  # 最小键节点缓存
    
    def is_empty(self) -> bool:
        """
        判断堆是否为空
        
        Returns:
            空返回 True
        """
        return all(h is None for h in self.heads)
    
    def _degree_of(self, node: BinomialTreeNode) -> int:
        """
        获取节点的度
        
        Args:
            node: 二项树节点
        
        Returns:
            节点的度
        """
        return node.degree
    
    def _link_tree(self, root1: BinomialTreeNode, root2: BinomialTreeNode) -> BinomialTreeNode:
        """
        将 root2 作为 root1 的子节点（root1.key <= root2.key）
        
        二项树合并规则：
        - 较小键的节点成为新根
        - 另一个成为其子节点
        - 子节点通过 sibling 指针形成链表
        
        Args:
            root1: 将成为父节点的根
            root2: 将成为子节点的根
        
        Returns:
            合并后的新根
        """
        # 确保 root1 的键值更小
        if root1.key > root2.key:
            root1, root2 = root2, root1
        
        # 将 root2 从根表中移除
        root2.parent = root1
        
        # 将 root2 添加为 root1 的最左子节点
        root2.sibling = root1.child
        root1.child = root2
        root1.degree += 1
        
        return root1
    
    def _merge_roots(self, h1: List[Optional[BinomialTreeNode]],
                     h2: List[Optional[BinomialTreeNode]]) -> List[Optional[BinomialTreeNode]]:
        """
        合并两个根表（类似二进制加法）
        
        原理：将两个根表按度从小到大合并，
        遇到相同度的树则合并（度翻倍），产生进位。
        
        Args:
            h1: 第一个根表
            h2: 第二个根表
        
        Returns:
            合并后的新根表
        """
        # 扩展到足够长度
        max_len = max(len(h1), len(h2))
        h1 = h1 + [None] * (max_len - len(h1))
        h2 = h2 + [None] * (max_len - len(h2))
        
        result = [None] * (max_len + 1)  # 最多多一个进位
        carry: Optional[BinomialTreeNode] = None
        
        for i in range(max_len + 1):
            a = h1[i] if i < len(h1) else None
            b = h2[i] if i < len(h2) else None
            
            # 统计当前度的树数量（0, 1, 2, 或 3）
            case = (0 if a is None else 1) + (0 if b is None else 1) + (0 if carry is None else 1)
            
            if case == 0:
                # 无树
                result[i] = None
            elif case == 1:
                # 一棵树：优先使用 carry，其次 b，最后 a
                result[i] = carry if carry is not None else (b if b is not None else a)
                carry = None
            elif case == 2:
                # 两棵树：合并到 carry，进位到 i+1
                if a is not None and b is not None:
                    result[i] = None
                    carry = self._link_tree(a, b)
                else:
                    result[i] = a if a is not None else b
                    carry = None
            else:
                # case == 3: 三棵树，合并其中两个，结果放 i，第三树进位
                if a is not None and b is not None:
                    result[i] = carry if carry is not None else a
                    carry = self._link_tree(b, a if carry is None else carry)
                else:
                    result[i] = b if b is not None else a
                    carry = None
        
        # 移除末尾多余的 None
        while result and result[-1] is None:
            result.pop()
        
        return result
    
    def merge(self, other: 'BinomialHeap') -> 'BinomialHeap':
        """
        合并两个二项堆
        
        Args:
            other: 另一个二项堆
        
        Returns:
            合并后的新二项堆
        """
        new_heap = BinomialHeap()
        new_heap.heads = self._merge_roots(self.heads, other.heads)
        new_heap._update_min()
        return new_heap
    
    def insert(self, key: int) -> BinomialTreeNode:
        """
        插入新节点
        
        Args:
            key: 要插入的键值
        
        Returns:
            创建的新节点（包装为单节点二项树 B_0）
        """
        # 单节点树即 B_0
        new_node = BinomialTreeNode(key)
        new_tree = [new_node]  # 根表，只有度为 0 的树
        
        # 与当前堆合并
        if not self.heads:
            self.heads = new_tree
        else:
            self.heads = self._merge_roots(self.heads, new_tree)
        
        self._update_min()
        return new_node
    
    def _update_min(self) -> None:
        """
        更新最小节点缓存
        """
        self.min_node = None
        for tree in self.heads:
            if tree is not None:
                if self.min_node is None or tree.key < self.min_node.key:
                    self.min_node = tree
    
    def find_min(self) -> Optional[int]:
        """
        返回最小键值
        
        Returns:
            最小键值，堆为空返回 None
        """
        if self.min_node is None:
            self._update_min()
        if self.min_node is None:
            return None
        return self.min_node.key
    
    def _find_min_node(self) -> Optional[BinomialTreeNode]:
        """
        找到最小节点（实际返回树根，最小值必在某个根中）
        
        Returns:
            最小节点所在的树根
        """
        self._update_min()
        return self.min_node
    
    def extract_min(self) -> Optional[int]:
        """
        抽取最小节点
        
        步骤：
        1. 找到最小键所在的树 B_k
        2. 从根表中移除 B_k 的根节点
        3. 将 B_k 根节点的子链表反转，形成新的二项堆 H'
        4. 合并 H' 和 原堆去除 B_k 后的部分
        
        Returns:
            被删除的最小键值
        """
        if self.is_empty():
            return None
        
        # 找到最小键所在的树
        min_tree = self._find_min_node()
        min_key = min_tree.key
        
        # 从根表中找到并移除该树
        min_tree_idx = -1
        for i, tree in enumerate(self.heads):
            if tree == min_tree:
                min_tree_idx = i
                break
        
        # 移除最小树
        self.heads[min_tree_idx] = None
        
        # 将最小树的子链表反转，形成新的根表
        new_heads: List[Optional[BinomialTreeNode]] = []
        if min_tree.child is not None:
            # 反转子链表
            children = []
            child = min_tree.child
            while child is not None:
                children.append(child)
                child = child.sibling
            
            children.reverse()
            
            # 将每个子节点作为独立根（按度从小到大排列）
            # 子节点的度从 0 到 k-1，顺序与 sibling 链一致
            # 重建 sibling 链表
            for i in range(len(children) - 1):
                children[i].sibling = children[i + 1]
                children[i].parent = None
            if children:
                children[-1].sibling = None
                children[-1].parent = None
            
            # 按度排列（已经是按度从小到大：k-1, k-2, ..., 0）
            # 但实际度序列是 k-1, k-2, ..., 0，需要反转成 0, 1, ..., k-1
            children.reverse()
            new_heads = children
        
        # 合并原根表（去除最小树）和新根表
        self.heads = self._merge_roots(
            [t for t in self.heads if t is not None],
            new_heads
        )
        
        self._update_min()
        return min_key
    
    def _find_node(self, node: BinomialTreeNode, target: BinomialTreeNode) -> Optional[BinomialTreeNode]:
        """
        在树中查找目标节点
        
        Args:
            node: 当前节点
            target: 目标节点
        
        Returns:
            找到返回节点，否则返回 None
        """
        if node == target:
            return node
        
        # 检查子节点
        if node.child is not None:
            child = node.child
            while child is not None:
                result = self._find_node(child, target)
                if result is not None:
                    return result
                child = child.sibling
        
        return None
    
    def _find_node_by_key(self, node: Optional[BinomialTreeNode], key: int) -> Optional[BinomialTreeNode]:
        """
        在树中按键值查找节点（返回第一个匹配的）
        
        Args:
            node: 树根
            key: 键值
        
        Returns:
            找到返回节点，否则返回 None
        """
        if node is None:
            return None
        
        if node.key == key:
            return node
        
        if node.child is not None:
            child = node.child
            while child is not None:
                result = self._find_node_by_key(child, key)
                if result is not None:
                    return result
                child = child.sibling
        
        return None
    
    def decrease_key(self, node: BinomialTreeNode, new_key: int) -> None:
        """
        减小指定节点的键值
        
        Args:
            node: 目标节点
            new_key: 新的键值（必须小于原键值）
        """
        if new_key > node.key:
            raise ValueError("新键值必须小于原键值")
        
        node.key = new_key
        
        # 沿父链向上，维护堆性质
        current = node
        parent = current.parent
        
        while parent is not None and current.key < parent.key:
            # 交换键值（注意：只交换 key，不移动节点结构）
            current.key, parent.key = parent.key, current.key
            current = parent
            parent = current.parent
        
        # 更新最小节点
        if current.key < (self.min_node.key if self.min_node else float('inf')):
            self.min_node = current
    
    def delete(self, node: BinomialTreeNode) -> None:
        """
        删除指定节点
        
        策略：将节点键值降到负无穷（触发 decrease_key 的交换），
        然后 extract_min。
        
        Args:
            node: 要删除的节点
        """
        self.decrease_key(node, float('-inf'))
        self.extract_min()
    
    def _heap_size(self) -> int:
        """
        计算堆中节点总数
        
        Returns:
            节点数量
        """
        size = 0
        for tree in self.heads:
            if tree is not None:
                size += 2 ** tree.degree
        return size
    
    def _print_tree(self, node: Optional[BinomialTreeNode], level: int = 0) -> None:
        """
        递归打印树结构（调试用）
        
        Args:
            node: 当前节点
            level: 缩进层级
        """
        if node is None:
            return
        print("  " * level + f"-> {node.key} (degree={node.degree})")
        if node.child is not None:
            child = node.child
            while child is not None:
                self._print_tree(child, level + 1)
                child = child.sibling
    
    def display(self) -> None:
        """
        打印堆结构（调试用）
        """
        print("二项堆结构:")
        for i, tree in enumerate(self.heads):
            if tree is not None:
                print(f"B_{tree.degree} 树 (2^{tree.degree} 个节点):")
                self._print_tree(tree)


# ============================ 测试代码 ============================
if __name__ == "__main__":
    print("=" * 60)
    print("二项堆 (Binomial Heap) 测试")
    print("=" * 60)
    
    # 创建二项堆
    bh = BinomialHeap()
    
    # 测试插入
    print("\n--- 测试插入 ---")
    keys = [12, 7, 25, 15, 4, 20, 8, 30, 10]
    inserted_nodes = []
    for key in keys:
        node = bh.insert(key)
        inserted_nodes.append(node)
        print(f"插入 {key}: find_min={bh.find_min()}, 堆大小≈{bh._heap_size()}")
    
    # 测试 find_min
    print(f"\n当前最小值: {bh.find_min()}")
    
    # 测试合并
    print("\n--- 测试合并 ---")
    bh2 = BinomialHeap()
    for k in [5, 18, 3]:
        bh2.insert(k)
    
    merged = bh.merge(bh2)
    print(f"合并后 find_min: {merged.find_min()}")
    print(f"合并后节点数: {merged._heap_size()}")
    merged.display()
    
    # 测试 extract_min
    print("\n--- 测试 extract_min ---")
    for _ in range(5):
        min_val = bh.extract_min()
        print(f"抽取最小值: {min_val}, 新最小值={bh.find_min()}")
    
    # 测试 decrease_key
    print("\n--- 测试 decrease_key ---")
    bh3 = BinomialHeap()
    nodes = {}
    for k in [20, 15, 10, 25]:
        nodes[k] = bh3.insert(k)
    
    print(f"原始 find_min: {bh3.find_min()}")
    bh3.decrease_key(nodes[20], 2)
    print(f"将 20 减小到 2 后 find_min: {bh3.find_min()}")
    
    # 测试 delete
    print("\n--- 测试 delete ---")
    bh4 = BinomialHeap()
    nodes4 = {}
    for k in [14, 8, 20, 5, 12]:
        nodes4[k] = bh4.insert(k)
    
    print(f"原始 find_min: {bh4.find_min()}")
    bh4.delete(nodes4[14])
    print(f"删除 14 后 find_min: {bh4.find_min()}")
    
    # 复杂度总结
    print("\n--- 二项堆复杂度总结 ---")
    print(f"{'操作':<18} {'时间复杂度':<15}")
    print("-" * 35)
    print(f"{'insert':<18} {'O(log n) 最坏, O(1) 期望':<25}")
    print(f"{'find_min':<18} {'O(log n)':<15}")
    print(f"{'extract_min':<18} {'O(log n)':<15}")
    print(f"{'decrease_key':<18} {'O(log n)':<15}")
    print(f"{'delete':<18} {'O(log n)':<15}")
    print(f"{'merge':<18} {'O(log n)':<15}")
    
    print("\n--- 二项树 B_k 的性质 ---")
    for k in range(6):
        nodes_count = 2 ** k
        height = k
        print(f"B_{k}: 节点数=2^{k}={nodes_count}, 高度={height}")
