# -*- coding: utf-8 -*-
"""
算法实现：数据库算法 / btree

本文件实现 btree 相关的算法功能。
"""

from typing import List, Optional, Tuple, Generic, TypeVar
from dataclasses import dataclass

T = TypeVar('T')  # 键类型


@dataclass
class BTreeNode:
    """B树节点"""
    keys: List[int]                    # 键列表（有序）
    values: List[T]                    # 值列表
    children: List['BTreeNode']         # 子节点列表
    is_leaf: bool                      # 是否为叶子节点
    n: int                              # 当前键的数量

    def __init__(self, is_leaf: bool = True, order: int = 3):
        self.keys = []                  # 键
        self.values = []                # 值（与键一一对应）
        self.children = []              # 子节点指针
        self.is_leaf = is_leaf
        self.n = 0                      # 当前键的数量
        self.order = order               # B树的阶（最大子节点数）


class BTree:
    """B树实现"""

    def __init__(self, order: int = 3):
        """
        初始化B树
        
        Args:
            order: 阶数，表示每个节点最多有order个子节点
        """
        self.order = order              # 阶数
        self.root = BTreeNode(is_leaf=True, order=order)  # 根节点
        self.size = 0                   # 键值对总数

    def search(self, key: int) -> Optional[Tuple[int, T]]:
        """
        搜索键对应的值
        
        Args:
            key: 要搜索的键
            
        Returns:
            (key, value) 或 None
        """
        return self._search_node(self.root, key)

    def _search_node(self, node: BTreeNode, key: int) -> Optional[Tuple[int, T]]:
        """
        在指定节点中搜索
        
        Args:
            node: 要搜索的节点
            key: 键
            
        Returns:
            (key, value) 或 None
        """
        i = 0
        # 找到第一个 >= key 的位置
        while i < node.n and key > node.keys[i]:
            i += 1
        
        # 如果找到匹配的键
        if i < node.n and key == node.keys[i]:
            return (key, node.values[i])
        
        # 如果是叶子节点，搜索失败
        if node.is_leaf:
            return None
        
        # 否则递归搜索子节点
        return self._search_node(node.children[i], key)

    def insert(self, key: int, value: T):
        """
        插入键值对
        
        Args:
            key: 键
            value: 值
        """
        # 如果根节点已满，需要分裂
        if self.root.n == self.order - 1:
            old_root = self.root
            self.root = BTreeNode(is_leaf=False, order=self.order)
            self.root.children.append(old_root)
            self._split_child(self.root, 0)
            self._insert_non_full(self.root, key, value)
        else:
            self._insert_non_full(self.root, key, value)
        
        self.size += 1

    def _insert_non_full(self, node: BTreeNode, key: int, value: T):
        """
        向非满节点插入
        
        Args:
            node: 非满节点
            key: 键
            value: 值
        """
        i = node.n - 1
        
        if node.is_leaf:
            # 叶子节点：直接插入
            node.keys.append(None)
            node.values.append(None)
            
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            
            node.keys[i + 1] = key
            node.values[i + 1] = value
            node.n += 1
        else:
            # 内部节点：找到合适的子节点
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            
            # 如果子节点已满，先分裂
            if node.children[i].n == self.order - 1:
                self._split_child(node, i)
                
                # 分裂后，中间键上移，比较以确定正确的子节点
                if key > node.keys[i]:
                    i += 1
            
            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent: BTreeNode, child_index: int):
        """
        分裂已满的子节点
        
        Args:
            parent: 父节点
            child_index: 子节点在父节点中的索引
        """
        order = self.order
        child = parent.children[child_index]
        new_child = BTreeNode(is_leaf=child.is_leaf, order=order)
        
        # 分裂位置
        mid = order // 2
        
        # 新节点获得右半部分的键和值
        new_child.keys = child.keys[mid:]
        new_child.values = child.values[mid:]
        new_child.n = len(new_child.keys)
        
        # 原节点保留左半部分
        child.keys = child.keys[:mid]
        child.values = child.values[:mid]
        child.n = len(child.keys)
        
        # 如果不是叶子节点，还需要处理子节点
        if not child.is_leaf:
            new_child.children = child.children[mid:]
            child.children = child.children[:mid]
        
        # 将中间键上移到父节点
        parent.keys.insert(child_index, child.keys.pop())
        parent.values.insert(child_index, child.values.pop())
        parent.children.insert(child_index + 1, new_child)
        parent.n += 1

    def delete(self, key: int) -> bool:
        """
        删除键
        
        Args:
            key: 要删除的键
            
        Returns:
            是否成功删除
        """
        result = self._delete_node(self.root, key)
        self.size -= 1 if result else 0
        return result

    def _delete_node(self, node: BTreeNode, key: int) -> bool:
        """
        从节点中删除键
        
        Args:
            node: 要操作的节点
            key: 要删除的键
            
        Returns:
            是否成功删除
        """
        idx = self._find_key_index(node, key)
        
        if idx < node.n and node.keys[idx] == key:
            # 找到要删除的键
            if node.is_leaf:
                self._delete_from_leaf(node, idx)
            else:
                self._delete_from_internal(node, idx)
            return True
        else:
            # 键不在当前节点
            if node.is_leaf:
                return False
            
            # 递归删除
            flag = (idx == node.n)
            
            if node.children[idx].n < (self.order + 1) // 2:
                self._fill_child(node, idx)
            
            if flag and idx > node.n:
                return self._delete_node(node.children[idx - 1], key)
            else:
                return self._delete_node(node.children[idx], key)

    def _find_key_index(self, node: BTreeNode, key: int) -> int:
        """找到键应该存在的位置或索引"""
        idx = 0
        while idx < node.n and node.keys[idx] < key:
            idx += 1
        return idx

    def _delete_from_leaf(self, node: BTreeNode, idx: int):
        """从叶子节点删除"""
        node.keys.pop(idx)
        node.values.pop(idx)
        node.n -= 1

    def _delete_from_internal(self, node: BTreeNode, idx: int):
        """从内部节点删除"""
        key = node.keys[idx]
        
        # 使用前驱或后继键替换
        if node.children[idx].n >= (self.order + 1) // 2:
            predecessor = self._get_predecessor(node.children[idx])
            node.keys[idx] = predecessor[0]
            node.values[idx] = predecessor[1]
            self._delete_node(node.children[idx], predecessor[0])
        elif node.children[idx + 1].n >= (self.order + 1) // 2:
            successor = self._get_successor(node.children[idx + 1])
            node.keys[idx] = successor[0]
            node.values[idx] = successor[1]
            self._delete_node(node.children[idx + 1], successor[0])
        else:
            # 合并两个子节点
            self._merge(node, idx)
            self._delete_node(node.children[idx], key)

    def _get_predecessor(self, node: BTreeNode) -> Tuple[int, T]:
        """获取前驱（最右叶子）"""
        current = node
        while not current.is_leaf:
            current = current.children[-1]
        return (current.keys[-1], current.values[-1])

    def _get_successor(self, node: BTreeNode) -> Tuple[int, T]:
        """获取后继（最左叶子）"""
        current = node
        while not current.is_leaf:
            current = current.children[0]
        return (current.keys[0], current.values[0])

    def _fill_child(self, parent: BTreeNode, idx: int):
        """填充子节点（保证至少有半满的键）"""
        order = self.order
        
        if idx != 0 and parent.children[idx - 1].n >= (order + 1) // 2:
            self._borrow_from_prev(parent, idx)
        elif idx != parent.n and parent.children[idx + 1].n >= (order + 1) // 2:
            self._borrow_from_next(parent, idx)
        else:
            if idx == parent.n:
                idx -= 1
            self._merge(parent, idx)

    def _borrow_from_prev(self, parent: BTreeNode, idx: int):
        """从左兄弟借键"""
        child = parent.children[idx]
        sibling = parent.children[idx - 1]
        
        # 子节点键前移，空位给父节点的键
        child.keys.insert(0, parent.keys[idx - 1])
        child.values.insert(0, parent.values[idx - 1])
        child.n += 1
        
        # 父节点的键被兄弟节点的最后一个键替换
        parent.keys[idx - 1] = sibling.keys.pop()
        parent.values[idx - 1] = sibling.values.pop()
        sibling.n -= 1
        
        if not child.is_leaf:
            child.children.insert(0, sibling.children.pop())
            sibling.children.pop()

    def _borrow_from_next(self, parent: BTreeNode, idx: int):
        """从右兄弟借键"""
        child = parent.children[idx]
        sibling = parent.children[idx + 1]
        
        # 子节点键追加父节点的键
        child.keys.append(parent.keys[idx])
        child.values.append(parent.values[idx])
        child.n += 1
        
        # 父节点的键被兄弟节点的第一个键替换
        parent.keys[idx] = sibling.keys.pop(0)
        parent.values[idx] = sibling.values.pop(0)
        sibling.n -= 1
        
        if not child.is_leaf:
            child.children.append(sibling.children.pop(0))
            sibling.children.pop(0)

    def _merge(self, parent: BTreeNode, idx: int):
        """合并两个子节点"""
        child = parent.children[idx]
        sibling = parent.children[idx + 1]
        
        # 将父节点的键下移到子节点
        child.keys.append(parent.keys[idx])
        child.values.append(parent.values[idx])
        
        # 将兄弟节点的键和子节点合并
        child.keys.extend(sibling.keys)
        child.values.extend(sibling.values)
        
        if not child.is_leaf:
            child.children.extend(sibling.children)
        
        # 从父节点删除兄弟节点的键和指针
        parent.keys.pop(idx)
        parent.values.pop(idx)
        parent.children.pop(idx + 1)
        parent.n -= 1
        
        # 更新子节点键数量
        child.n = len(child.keys)
        
        # 删除兄弟节点（Python GC处理）

    def range_query(self, low: int, high: int) -> List[Tuple[int, T]]:
        """
        范围查询
        
        Args:
            low: 下界
            high: 上界
            
        Returns:
            在范围内的所有 (key, value) 对
        """
        results = []
        self._range_query_node(self.root, low, high, results)
        return results

    def _range_query_node(self, node: BTreeNode, low: int, high: int, results: List):
        """递归范围查询"""
        i = 0
        while i < node.n:
            if not node.is_leaf:
                self._range_query_node(node.children[i], low, high, results)
            
            if low <= node.keys[i] <= high:
                results.append((node.keys[i], node.values[i]))
            elif node.keys[i] > high:
                return  # 已超过上界，可以提前终止
            
            i += 1
        
        if not node.is_leaf:
            self._range_query_node(node.children[i], low, high, results)

    def traverse(self) -> List[Tuple[int, T]]:
        """中序遍历（返回所有键值对有序列表）"""
        results = []
        self._inorder_traverse(self.root, results)
        return results

    def _inorder_traverse(self, node: BTreeNode, results: List):
        """中序遍历"""
        for i in range(node.n):
            if not node.is_leaf:
                self._inorder_traverse(node.children[i], results)
            results.append((node.keys[i], node.values[i]))
        
        if not node.is_leaf:
            self._inorder_traverse(node.children[node.n], results)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("B树索引测试")
    print("=" * 60)

    # 创建一棵3阶B树
    btree = BTree(order=3)
    
    # 插入测试
    print("\n--- 插入测试 ---")
    test_data = [
        (10, "value_10"),
        (20, "value_20"),
        (5, "value_5"),
        (15, "value_15"),
        (25, "value_25"),
        (30, "value_30"),
        (7, "value_7"),
        (35, "value_35"),
        (40, "value_40"),
        (50, "value_50"),
    ]
    
    for key, value in test_data:
        btree.insert(key, value)
        print(f"  插入 ({key}, '{value}') - 树大小: {btree.size}")
    
    print(f"\n中序遍历: {btree.traverse()}")

    # 搜索测试
    print("\n--- 搜索测试 ---")
    search_keys = [15, 25, 100]
    for key in search_keys:
        result = btree.search(key)
        if result:
            print(f"  搜索 {key}: 找到 '{result[1]}'")
        else:
            print(f"  搜索 {key}: 未找到")

    # 范围查询
    print("\n--- 范围查询 [10, 30] ---")
    results = btree.range_query(10, 30)
    for key, value in results:
        print(f"  {key}: '{value}'")

    # 删除测试
    print("\n--- 删除测试 ---")
    delete_keys = [15, 20, 10]
    for key in delete_keys:
        result = btree.delete(key)
        status = "成功" if result else "失败"
        print(f"  删除 {key}: {status} - 树大小: {btree.size}")
    
    print(f"\n中序遍历: {btree.traverse()}")

    # 边界测试
    print("\n--- 边界测试：1阶B树（实际最小阶数） ---")
    btree2 = BTree(order=3)  # 实际最小阶数是3
    for i in range(1, 11):
        btree2.insert(i * 10, f"val_{i * 10}")
    print(f"  插入10个元素后: {btree2.traverse()}")

    print("\n" + "=" * 60)
    print("复杂度: 查找/插入/删除 O(log_m N) ≈ O(log N)")
    print("=" * 60)
