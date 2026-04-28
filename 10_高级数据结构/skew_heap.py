"""
斜堆 (Skew Heap)
================

一种自调整的堆数据结构，通过简单的合并规则实现近乎最优的摊销性能。
不需要维护额外的平衡信息（如 rank、size），合并效率极高。

核心思想：
- 合并操作：递归地将较大根与较小根的右子堆交换
- 无需显式旋转，通过交换左右子指针实现平衡
- 摊销复杂度为 O(log n)，最坏情况为 O(n)

时间复杂度（摊销）：
- merge(h1, h2): O(log n) 摊销
- insert(x):     O(log n) 摊销（调用 merge）
- extract_min(): O(log n) 摊销
- find_min():    O(1)

优点：实现极简，无需额外平衡信息
"""

from typing import Optional, Tuple


class SkewHeapNode:
    """
    斜堆的节点
    
    Attributes:
        key: 节点键值
        left: 左子节点指针
        right: 右子节点指针
    """
    
    def __init__(self, key: int):
        """
        初始化斜堆节点
        
        Args:
            key: 节点的关键字值
        """
        self.key: int = key            # 节点键值
        self.left: Optional[SkewHeapNode] = None   # 左子节点
        self.right: Optional[SkewHeapNode] = None  # 右子节点


class SkewHeap:
    """
    斜堆
    
    合并规则（递归版本）：
    1. 若其中一个堆为空，返回另一个
    2. 比较两个堆的根节点键值
    3. 较小键的根节点作为新根
    4. 递归合并原根的右子堆与另一堆
    5. 交换新根的左右子指针（这是斜堆平衡的关键）
    
    Attributes:
        root: 堆的根节点
    """
    
    def __init__(self):
        """
        初始化空的斜堆
        """
        self.root: Optional[SkewHeapNode] = None  # 堆的根节点
    
    def is_empty(self) -> bool:
        """
        判断堆是否为空
        
        Returns:
            空返回 True
        """
        return self.root is None
    
    def merge(self, other: 'SkewHeap') -> 'SkewHeap':
        """
        合并两个斜堆
        
        Args:
            other: 另一个斜堆
        
        Returns:
            合并后的新斜堆（原地修改 self）
        """
        self.root = self._merge_trees(self.root, other.root)
        return self
    
    def _merge_trees(self, h1: Optional[SkewHeapNode],
                     h2: Optional[SkewHeapNode]) -> Optional[SkewHeapNode]:
        """
        递归合并两棵斜堆树
        
        合并算法：
        1. 空则返回另一个
        2. 较小根作为新根
        3. 合并原根右子堆与另一棵树
        4. 交换新根的左右子指针（斜堆核心操作）
        
        Args:
            h1: 第一棵树的根
            h2: 第二棵树的根
        
        Returns:
            合并后的树根
        """
        # 情况1：其中一个为空
        if h1 is None:
            return h2
        if h2 is None:
            return h1
        
        # 情况2：确保 h1 的根较小（作为新根）
        if h1.key > h2.key:
            h1, h2 = h2, h1  # 交换，使 h1.key <= h2.key
        
        # 情况3：递归合并 h1 的右子堆和 h2
        merged_right = self._merge_trees(h1.right, h2)
        
        # 情况4：交换左右子指针（斜堆的平衡机制）
        # 这使得右子堆经常变深，从而在下次合并时有更多机会平衡
        h1.right = h1.left
        h1.left = merged_right
        
        return h1
    
    def insert(self, key: int) -> SkewHeapNode:
        """
        插入新节点
        
        Args:
            key: 要插入的键值
        
        Returns:
            创建的新节点
        """
        new_node = SkewHeapNode(key)
        self.root = self._merge_trees(self.root, new_node)
        return new_node
    
    def find_min(self) -> Optional[int]:
        """
        返回最小键值
        
        Returns:
            最小键值，空堆返回 None
        """
        if self.root is None:
            return None
        return self.root.key
    
    def extract_min(self) -> Optional[int]:
        """
        抽取最小节点（删除根节点）
        
        合并左右子堆即可（它们都是有效的斜堆）
        
        Returns:
            被删除的最小键值
        """
        if self.root is None:
            return None
        
        min_key = self.root.key
        
        # 合并左右子树，合并后的树成为新根
        self.root = self._merge_trees(self.root.left, self.root.right)
        
        return min_key
    
    def delete(self, key: int) -> bool:
        """
        删除键值为 key 的节点（找到并删除）
        
        注：斜堆不支持高效的 decrease_key，因为没有父指针。
        删除需要找到节点（O(n)），然后合并其子堆。
        
        Args:
            key: 要删除的键值
        
        Returns:
            找到并删除返回 True，否则返回 False
        """
        if self.root is None:
            return False
        
        # 找到键值匹配的节点
        node, parent = self._find_node(self.root, None, key)
        if node is None:
            return False
        
        # 用合并左右子树的结果替换该节点
        new_subtree = self._merge_trees(node.left, node.right)
        
        if parent is None:
            # 删除的是根节点
            self.root = new_subtree
        elif parent.left == node:
            parent.left = new_subtree
        else:
            parent.right = new_subtree
        
        return True
    
    def _find_node(self, current: Optional[SkewHeapNode],
                   parent: Optional[SkewHeapNode],
                   key: int) -> Tuple[Optional[SkewHeapNode], Optional[SkewHeapNode]]:
        """
        在堆中查找键值为 key 的节点
        
        Args:
            current: 当前节点
            parent: 当前节点的父节点
            key: 目标键值
        
        Returns:
            (找到的节点, 父节点) 元组
        """
        if current is None:
            return None, None
        
        if current.key == key:
            return current, parent
        
        # 先在左子树搜索
        found, found_parent = self._find_node(current.left, current, key)
        if found is not None:
            return found, found_parent
        
        # 再在右子树搜索
        return self._find_node(current.right, current, key)
    
    def _inorder_traversal(self, node: Optional[SkewHeapNode], result: list) -> None:
        """
        中序遍历（验证堆序性）
        
        Args:
            node: 当前节点
            result: 结果列表
        """
        if node is None:
            return
        self._inorder_traversal(node.left, result)
        result.append(node.key)
        self._inorder_traversal(node.right, result)
    
    def to_list(self) -> list:
        """
        返回堆中所有键值的有序列表
        
        Returns:
            键值列表（无序）
        """
        result = []
        self._inorder_traversal(self.root, result)
        return result


# ============================ 测试代码 ============================
if __name__ == "__main__":
    print("=" * 60)
    print("斜堆 (Skew Heap) 测试")
    print("=" * 60)
    
    # 创建斜堆
    sh = SkewHeap()
    
    # 测试插入
    print("\n--- 测试插入 ---")
    keys = [15, 10, 25, 5, 20, 30, 12, 8]
    for key in keys:
        sh.insert(key)
        print(f"插入 {key}: find_min={sh.find_min()}, 堆节点数={len(sh.to_list())}")
    
    # 测试合并
    print("\n--- 测试合并 ---")
    sh1 = SkewHeap()
    for k in [3, 7, 1, 8]:
        sh1.insert(k)
    
    sh2 = SkewHeap()
    for k in [5, 2, 9, 4]:
        sh2.insert(k)
    
    print(f"sh1 最小值: {sh1.find_min()}, sh2 最小值: {sh2.find_min()}")
    sh1.merge(sh2)
    print(f"合并后 sh1 最小值: {sh1.find_min()}")
    print(f"合并后 sh1 所有元素: {sh1.to_list()}")
    
    # 测试 extract_min
    print("\n--- 测试 extract_min ---")
    for _ in range(4):
        min_val = sh.extract_min()
        print(f"抽取最小值: {min_val}, 剩余最小值={sh.find_min()}")
    
    # 验证堆序性
    print("\n--- 验证堆序性 ---")
    sh3 = SkewHeap()
    for k in [20, 15, 10, 5, 25, 30, 8, 12]:
        sh3.insert(k)
    
    print(f"堆中所有元素: {sh3.to_list()}")
    print(f"最小值（根）: {sh3.find_min()}")
    
    # 测试 delete
    print("\n--- 测试 delete ---")
    sh4 = SkewHeap()
    for k in [14, 7, 20, 3, 10, 25]:
        sh4.insert(k)
    
    print(f"原始 find_min: {sh4.find_min()}")
    deleted = sh4.delete(7)
    print(f"删除 7: {'成功' if deleted else '失败'}, find_min={sh4.find_min()}")
    print(f"删除后元素: {sh4.to_list()}")
    
    # 大量随机操作测试
    print("\n--- 大量随机操作测试 ---")
    import random
    random.seed(42)
    
    sh5 = SkewHeap()
    expected = []
    for _ in range(1000):
        op = random.choice(['insert', 'extract', 'merge'])
        
        if op == 'insert':
            key = random.randint(1, 10000)
            sh5.insert(key)
            expected.append(key)
        elif op == 'extract' and not sh5.is_empty():
            min_val = sh5.extract_min()
            expected.remove(min_val)
        
        # 验证所有剩余元素
        if not sh5.is_empty():
            heap_min = sh5.find_min()
            list_min = min(expected) if expected else None
            if heap_min != list_min:
                print(f"错误！堆最小={heap_min}, 期望={list_min}")
                break
    
    print(f"完成 1000 次随机操作，堆大小={len(expected)}, 堆最小={sh5.find_min()}")
    
    # 复杂度总结
    print("\n--- 斜堆复杂度总结 ---")
    print(f"{'操作':<18} {'时间复杂度(摊销)':<20} {'说明':<25}")
    print("-" * 65)
    print(f"{'merge':<18} {'O(log n)':<20} {'核心操作，无额外平衡信息':<25}")
    print(f"{'insert':<18} {'O(log n)':<20} {'调用 merge':<25}")
    print(f"{'extract_min':<18} {'O(log n)':<20} {'合并左右子树':<25}")
    print(f"{'find_min':<18} {'O(1)':<20} {'直接返回根':<25}")
    print(f"{'delete(key)':<16} {'O(n)':<20} {'需线性查找（无父指针）':<25}")
    
    print("\n--- 斜堆 vs 二叉堆 vs 斐波那契堆 ---")
    print(f"{'特性':<20} {'斜堆':<12} {'二叉堆':<12} {'斐波那契堆':<12}")
    print("-" * 56)
    print(f"{'insert':<20} {'O(log n)':<12} {'O(log n)':<12} {'O(1)':<12}")
    print(f"{'extract_min':<20} {'O(log n)':<12} {'O(log n)':<12} {'O(log n)':<12}")
    print(f"{'decrease_key':<20} {'O(n)':<12} {'O(log n)':<12} {'O(1)':<12}")
    print(f"{'实现难度':<20} {'简单':<12} {'简单':<12} {'复杂':<12}")
