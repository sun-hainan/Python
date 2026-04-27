# -*- coding: utf-8 -*-
"""
算法实现：缓存无关算法 / bplus_tree

本文件实现 bplus_tree 相关的算法功能。
"""

from typing import List, Tuple, Optional


class BPlusNode:
    """B+树节点"""
    def __init__(self, max_degree: int, is_leaf: bool = False):
        self.max_degree = max_degree
        self.is_leaf = is_leaf
        self.keys: List = []
        self.children: List = []  # 子节点或数据指针
        self.next: 'BPlusNode' = None  # 叶子节点链表
    
    def is_full(self) -> bool:
        return len(self.keys) >= self.max_degree


class BPlusTree:
    """
    B+树
    所有数据存储在叶子节点,内部节点只存储键
    """
    
    def __init__(self, max_degree: int = 4):
        self.root = BPlusNode(max_degree, is_leaf=True)
        self.max_degree = max_degree
        self.min_keys = (max_degree - 1) // 2
    
    def insert(self, key, value):
        """插入键值对"""
        root = self.root
        
        if root.is_full():
            # 分裂根节点
            new_root = BPlusNode(self.max_degree)
            new_root.children.append(self.root)
            self._split_child(new_root, 0, self.root)
            self.root = new_root
        
        self._insert_non_full(self.root, key, value)
    
    def _insert_non_full(self, node: BPlusNode, key, value):
        """向非满节点插入"""
        if node.is_leaf:
            # 叶子节点:找到插入位置
            i = len(node.keys) - 1
            node.keys.append(None)
            node.children.append(None)  # 对应数据
            
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.children[i + 1] = node.children[i]
                i -= 1
            
            node.keys[i + 1] = key
            node.children[i + 1] = value
        
        else:
            # 内部节点:找到合适的子节点
            i = len(node.keys) - 1
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            
            if node.children[i].is_full():
                self._split_child(node, i, node.children[i])
                
                if key > node.keys[i]:
                    i += 1
            
            self._insert_non_full(node.children[i], key, value)
    
    def _split_child(self, parent: BPlusNode, index: int, child: BPlusNode):
        """分裂子节点"""
        new_child = BPlusNode(self.max_degree, is_leaf=child.is_leaf)
        
        mid = self.max_degree // 2
        
        if child.is_leaf:
            # 叶子节点分裂
            new_child.keys = child.keys[mid:]
            new_child.children = child.children[mid:]
            child.keys = child.keys[:mid]
            child.children = child.children[:mid]
            
            # 更新叶子链表
            new_child.next = child.next
            child.next = new_child
        else:
            # 内部节点分裂
            new_child.keys = child.keys[mid + 1:]
            new_child.children = child.children[mid + 1:]
            child.keys = child.keys[:mid]
            child.children = child.children[:mid + 1]
        
        # 父节点插入新键
        parent.keys.insert(index, new_child.keys[0] if new_child.keys else child.keys[-1])
        parent.children.insert(index + 1, new_child)
    
    def search(self, key) -> Optional:
        """搜索键"""
        return self._search(self.root, key)
    
    def _search(self, node: BPlusNode, key):
        """递归搜索"""
        if node.is_leaf:
            for i, k in enumerate(node.keys):
                if k == key:
                    return node.children[i]
            return None
        
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1
        
        return self._search(node.children[i], key)
    
    def range_query(self, start_key, end_key) -> List:
        """范围查询"""
        results = []
        
        # 找到起始叶子节点
        leaf = self._find_leaf(start_key)
        
        while leaf:
            for i, key in enumerate(leaf.keys):
                if start_key <= key <= end_key:
                    results.append((key, leaf.children[i]))
                elif key > end_key:
                    return results
            
            leaf = leaf.next
        
        return results
    
    def _find_leaf(self, key) -> BPlusNode:
        """找到包含键的叶子节点"""
        node = self.root
        
        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]
        
        return node
    
    def delete(self, key):
        """删除键"""
        self._delete(self.root, key)
    
    def _delete(self, node: BPlusNode, key):
        """递归删除"""
        if node.is_leaf:
            if key in node.keys:
                idx = node.keys.index(key)
                node.keys.pop(idx)
                node.children.pop(idx)
            return
        
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1
        
        self._delete(node.children[i], key)
        
        # 检查是否需要合并
        if len(node.children[i].keys) < self.min_keys:
            self._redistribute_or_merge(node, i)


class BStarTree:
    """
    B*树
    在B+树基础上,节点利用率更高(2/3而不是1/2)
    """
    
    def __init__(self, max_degree: int = 4):
        self.max_degree = max_degree
        self.root = BPlusNode(max_degree, is_leaf=True)
        self.min_keys = int(2 * (max_degree - 1) / 3)


# 测试代码
if __name__ == "__main__":
    # 测试1: B+树基本操作
    print("测试1 - B+树基本操作:")
    bpt = BPlusTree(max_degree=4)
    
    # 插入
    for i in range(20):
        bpt.insert(i, f"value_{i}")
    
    print("  插入20个键值对")
    
    # 搜索
    for key in [5, 10, 15, 25]:
        result = bpt.search(key)
        print(f"  search({key}) = {result}")
    
    # 测试2: 范围查询
    print("\n测试2 - 范围查询:")
    results = bpt.range_query(5, 12)
    print(f"  range_query(5, 12): {results}")
    
    # 测试3: 删除
    print("\n测试3 - 删除:")
    bpt.delete(10)
    bpt.delete(15)
    
    result = bpt.search(10)
    print(f"  删除10后search(10) = {result}")
    
    # 测试4: 更大规模
    print("\n测试4 - 大规模插入:")
    import random
    
    random.seed(42)
    bpt_large = BPlusTree(max_degree=32)
    
    import time
    start = time.time()
    
    for i in range(10000):
        bpt_large.insert(i, f"value_{i}")
    
    elapsed = time.time() - start
    print(f"  插入10000个元素: {elapsed:.3f}s")
    
    # 搜索测试
    start = time.time()
    found = 0
    for i in range(0, 10000, 100):
        if bpt_large.search(i):
            found += 1
    elapsed = time.time() - start
    
    print(f"  搜索100个元素: {elapsed:.4f}s")
    print(f"  找到: {found}/100")
    
    # 测试5: B*树
    print("\n测试5 - B*树:")
    bst = BStarTree(max_degree=4)
    
    for i in range(30):
        bst.insert(i, f"val_{i}")
    
    print("  插入30个元素到B*树")
    print(f"  搜索10: {bst.search(10)}")
    
    print("\n所有测试完成!")
