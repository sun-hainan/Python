# -*- coding: utf-8 -*-
"""
算法实现：binary_tree / binary_search_tree

本文件实现 binary_search_tree 相关的算法功能。
"""

from dataclasses import dataclass


@dataclass
class Node:
    """BST 节点"""
    value: int
    left: Node | None = None
    right: Node | None = None
    parent: Node | None = None  # 父节点引用（便于删除操作）

    @property
    def is_right(self) -> bool:
        return bool(self.parent and self is self.parent.right)


@dataclass
class BinarySearchTree:
    root: Node | None = None

    def empty(self) -> bool:
        """检查树是否为空"""
        return not self.root

    def insert(self, *values) -> "BinarySearchTree":
        """插入一个或多个节点"""
        for value in values:
            new_node = Node(value)
            if self.empty():
                self.root = new_node
            else:
                parent_node = self.root
                while True:
                    if value < parent_node.value:
                        if parent_node.left is None:
                            parent_node.left = new_node
                            new_node.parent = parent_node
                            break
                        parent_node = parent_node.left
                    else:
                        if parent_node.right is None:
                            parent_node.right = new_node
                            new_node.parent = parent_node
                            break
                        parent_node = parent_node.right
        return self

    def search(self, value) -> Node | None:
        """查找值为 value 的节点"""
        if self.empty():
            raise IndexError("树为空！")
        node = self.root
        while node is not None and node.value != value:
            node = node.left if value < node.value else node.right
        return node

    def get_max(self, node: Node | None = None) -> Node | None:
        """获取子树最大值（最右节点）"""
        if node is None:
            node = self.root
        if node:
            while node.right is not None:
                node = node.right
        return node

    def get_min(self, node: Node | None = None) -> Node | None:
        """获取子树最小值（最左节点）"""
        if node is None:
            node = self.root
        if node:
            while node.left is not None:
                node = node.left
        return node

    def remove(self, value: int) -> None:
        """删除值为 value 的节点"""
        node = self.search(value)
        if node is None:
            raise ValueError(f"值 {value} 不存在")

        # 三种情况：叶子节点、有一个子节点、有两个子节点
        if node.left is None and node.right is None:
            self._reassign(node, None)
        elif node.left is None:
            self._reassign(node, node.right)
        elif node.right is None:
            self._reassign(node, node.left)
        else:
            # 用前驱（左子树最大）替换
            predecessor = self.get_max(node.left)
            self.remove(predecessor.value)
            node.value = predecessor.value

    def _reassign(self, node: Node, new_children: Node | None) -> None:
        """重新连接父子关系"""
        if new_children is not None:
            new_children.parent = node.parent
        if node.parent is not None:
            if node.is_right:
                node.parent.right = new_children
            else:
                node.parent.left = new_children
        else:
            self.root = new_children

    def inorder(self, node: Node | None = None, arr: list = None) -> list:
        """中序遍历（返回有序列表）"""
        if arr is None:
            arr = []
        if node:
            self.inorder(node.left, arr)
            arr.append(node.value)
            self.inorder(node.right, arr)
        return arr

    def find_kth_smallest(self, k: int, node: Node | None = None) -> int:
        """查找第 K 小的元素"""
        if node is None:
            node = self.root
        arr = self.inorder(node)
        return arr[k - 1]


if __name__ == "__main__":
    # 构建 BST
    #           8
    #         /   \
    #        3     10
    #       / \      \
    #      1   6      14
    #         / \    /
    #        4   7  13
    t = BinarySearchTree()
    t.insert(8, 3, 6, 1, 10, 14, 13, 4, 7)

    print(f"中序遍历（有序）: {t.inorder()}")
    print(f"最大值: {t.get_max().value}")
    print(f"最小值: {t.get_min().value}")
    print(f"搜索6: {'找到了' if t.search(6) else '没找到'}")
    print(f"第3小元素: {t.find_kth_smallest(3)}")
