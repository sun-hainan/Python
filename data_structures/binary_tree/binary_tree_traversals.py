"""
二叉树遍历 (Binary Tree Traversals) - 中文注释版
==========================================

二叉树基础：
    二叉树是每个节点最多有两个子节点的树结构。
    - 左子节点和右子节点
    - 根节点：树的顶部节点
    - 叶节点：没有子节点的节点

四种基本遍历方式（以这棵树为例）：
        1
       / \
      2   3
     / \
    4   5

前序遍历 (Preorder):  根 -> 左 -> 右 = [1, 2, 4, 5, 3]
中序遍历 (Inorder):   左 -> 根 -> 右 = [4, 2, 5, 1, 3]
后序遍历 (Postorder): 左 -> 右 -> 根 = [4, 5, 2, 3, 1]
层序遍历 (Level Order): 按层遍历 = [1, 2, 3, 4, 5]

应用场景：
    - Preorder：复制树、前缀表达式
    - Inorder：二叉搜索树按序输出
    - Postorder：删除树、后缀表达式
    - Level Order：BFS、按层分析
"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass


@dataclass
class Node:
    """二叉树节点"""
    data: int
    left: Node | None = None
    right: Node | None = None


def make_tree() -> Node | None:
    """
    构建示例二叉树：
        1
       / \
      2   3
     / \
    4   5
    """
    tree = Node(1)
    tree.left = Node(2)
    tree.right = Node(3)
    tree.left.left = Node(4)
    tree.left.right = Node(5)
    return tree


def preorder(root: Node | None):
    """
    前序遍历 (Preorder): 根 -> 左 -> 右

    示例:
        >>> list(preorder(make_tree()))
        [1, 2, 4, 5, 3]
    """
    if not root:
        return
    yield root.data
    yield from preorder(root.left)
    yield from preorder(root.right)


def postorder(root: Node | None):
    """
    后序遍历 (Postorder): 左 -> 右 -> 根

    示例:
        >>> list(postorder(make_tree()))
        [4, 5, 2, 3, 1]
    """
    if not root:
        return
    yield from postorder(root.left)
    yield from postorder(root.right)
    yield root.data


def inorder(root: Node | None):
    """
    中序遍历 (Inorder): 左 -> 根 -> 右

    对于二叉搜索树，中序遍历输出有序序列！

    示例:
        >>> list(inorder(make_tree()))
        [4, 2, 5, 1, 3]
    """
    if not root:
        return
    yield from inorder(root.left)
    yield root.data
    yield from inorder(root.right)


def reverse_inorder(root: Node | None):
    """
    逆中序遍历 (Reverse Inorder): 右 -> 根 -> 左

    从大到小输出（适合找第K大元素）

    示例:
        >>> list(reverse_inorder(make_tree()))
        [3, 1, 5, 2, 4]
    """
    if not root:
        return
    yield from reverse_inorder(root.right)
    yield root.data
    yield from reverse_inorder(root.left)


def height(root: Node | None) -> int:
    """
    计算二叉树的高度（深度）

    示例:
        >>> height(None)
        0
        >>> height(make_tree())
        3
    """
    return (max(height(root.left), height(root.right)) + 1) if root else 0


def level_order(root: Node | None):
    """
    层序遍历 (Level Order): 使用 BFS，按层遍历

    示例:
        >>> list(level_order(make_tree()))
        [1, 2, 3, 4, 5]
    """
    if root is None:
        return

    queue = deque([root])
    while queue:
        node = queue.popleft()
        yield node.data
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)


def zigzag(root: Node | None):
    """
    Z 字形遍历（锯齿形层序遍历）

    第一层从左到右，第二层从右到左，第三层从左到右...

    示例:
        >>> list(zigzag(make_tree()))
        [1, 3, 2, 4, 5]
    """
    if root is None:
        return

    flag = 0  # 0=从左到右, 1=从右到左
    h = height(root)

    for level in range(1, h + 1):
        if not flag:
            yield from get_nodes_from_left_to_right(root, level)
            flag = 1
        else:
            yield from get_nodes_from_right_to_left(root, level)
            flag = 0


def get_nodes_from_left_to_right(root: Node | None, level: int):
    """获取指定层的节点，从左到右"""
    if not root:
        return
    if level == 1:
        yield root.data
    elif level > 1:
        yield from get_nodes_from_left_to_right(root.left, level - 1)
        yield from get_nodes_from_left_to_right(root.right, level - 1)


def get_nodes_from_right_to_left(root: Node | None, level: int):
    """获取指定层的节点，从右到左"""
    if not root:
        return
    if level == 1:
        yield root.data
    elif level > 1:
        yield from get_nodes_from_right_to_left(root.right, level - 1)
        yield from get_nodes_from_right_to_left(root.left, level - 1)


def main():
    root = make_tree()

    print(f"中序遍历: {list(inorder(root))}")          # [4, 2, 5, 1, 3]
    print(f"前序遍历: {list(preorder(root))}")          # [1, 2, 4, 5, 3]
    print(f"后序遍历: {list(postorder(root))}")         # [4, 5, 2, 3, 1]
    print(f"层序遍历: {list(level_order(root))}")       # [1, 2, 3, 4, 5]
    print(f"Z字形遍历: {list(zigzag(root))}")          # [1, 3, 2, 4, 5]
    print(f"树的高度: {height(root)}")                  # 3


if __name__ == "__main__":
    main()
