# -*- coding: utf-8 -*-
"""
算法实现：外部内存算法 / external_btree

本文件实现 external_btree 相关的算法功能。
"""

from typing import List, Optional


class BTreeNode:
    """B树节点"""

    def __init__(self, leaf: bool = True, order: int = 64):
        """
        参数：
            leaf: 是否叶子节点
            order: B树的阶（最大子节点数）
        """
        self.leaf = leaf
        self.order = order
        self.keys = []      # 键
        self.children = []  # 子节点引用

    def is_full(self) -> bool:
        """检查是否满了"""
        return len(self.keys) >= self.order - 1

    def insert_key(self, key) -> None:
        """插入键"""
        self.keys.append(key)
        self.keys.sort()


class ExternalBTree:
    """外部内存B树"""

    def __init__(self, order: int = 64):
        """
        参数：
            order: B树阶
        """
        self.order = order
        self.root = BTreeNode(leaf=True, order=order)
        self.height = 1
        self.size = 0

    def search(self, key) -> bool:
        """
        搜索键

        返回：是否找到
        """
        return self._search_node(self.root, key)

    def _search_node(self, node: BTreeNode, key) -> bool:
        """在节点中搜索"""
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        if i < len(node.keys) and key == node.keys[i]:
            return True

        if node.leaf:
            return False

        # 递归到子节点（简化：假设子节点存在）
        return False

    def insert(self, key) -> None:
        """插入键"""
        if self.root.is_full():
            # 分裂根节点
            new_root = BTreeNode(leaf=False, order=self.order)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
            self.height += 1

        self._insert_nonfull(self.root, key)
        self.size += 1

    def _split_child(self, parent: BTreeNode, child_index: int) -> None:
        """分裂子节点"""
        # 简化：创建新节点
        pass

    def _insert_nonfull(self, node: BTreeNode, key) -> None:
        """插入到非满节点"""
        node.insert_key(key)


def btree_vs_bplus():
    """B树 vs B+树"""
    print("=== B树 vs B+树 ===")
    print()
    print("B树：")
    print("  - 所有节点都存储数据")
    print("  - 查找可能停在任意节点")
    print()
    print("B+树：")
    print("  - 数据只在叶子节点")
    print("  - 叶子节点链表连接")
    print("  - 数据库索引常用")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 外部内存B树测试 ===\n")

    # 创建B树
    order = 8
    btree = ExternalBTree(order=order)

    # 插入键
    keys = [5, 3, 7, 1, 4, 6, 2, 8, 9, 10]

    print(f"插入键: {keys}")
    print(f"B树阶: {order}")
    print()

    for key in keys:
        btree.insert(key)
        print(f"插入 {key}: 大小={btree.size}, 高度={btree.height}")

    print()

    # 搜索
    search_keys = [5, 10, 15]
    print("搜索：")
    for key in search_keys:
        found = btree.search(key)
        print(f"  {key}: {'找到' if found else '未找到'}")

    print()
    btree_vs_bplus()

    print()
    print("说明：")
    print("  - B树是多路平衡树")
    print("  - 外部B树减少I/O次数")
    print("  - 数据库系统广泛使用")
