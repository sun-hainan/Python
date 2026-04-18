"""
Binary Tree - 二叉树遍历
==========================================

【四种遍历方式】
1. 前序 Preorder:  根 -> 左 -> 右
2. 中序 Inorder:   左 -> 根 -> 右
3. 后序 Postorder: 左 -> 右 -> 根
4. 层序 Level:     按层遍历

【应用场景】
- 表达式树遍历
- 文件系统遍历
- DOM树遍历
"""

from collections import deque

class TreeNode:
    """二叉树节点"""
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def preorder(root):
    """前序遍历: 根 -> 左 -> 右"""
    if not root:
        return []
    return [root.val] + preorder(root.left) + preorder(root.right)


def inorder(root):
    """中序遍历: 左 -> 根 -> 右"""
    if not root:
        return []
    return inorder(root.left) + [root.val] + inorder(root.right)


def postorder(root):
    """后序遍历: 左 -> 右 -> 根"""
    if not root:
        return []
    return postorder(root.left) + postorder(root.right) + [root.val]


def level_order(root):
    """层序遍历: 按层从左到右"""
    if not root:
        return []
    queue = deque([root])
    result = []
    while queue:
        node = queue.popleft()
        result.append(node.val)
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)
    return result


# ---------- Linked List ----------
FILES['Chinese Algorithms/Structure/02_Linked_List.py'] = 
Linked List - 链表
==========================================

【数据结构】
每个节点包含数据和指向下一个节点的指针。
最后一个节点的next指向None。

【特点】
- 插入/删除: O(1)（已知位置）
- 查找: O(n)
- 不需要连续内存空间

【应用场景】
- 火车车厢连接
- 历史记录/Undo功能
- 任务队列管理
