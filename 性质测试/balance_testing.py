# -*- coding: utf-8 -*-
"""
算法实现：性质测试 / balance_testing

本文件实现 balance_testing 相关的算法功能。
"""

from typing import Optional


class TreeNode:
    """树节点"""

    def __init__(self, val: int):
        self.val = val
        self.left: Optional[TreeNode] = None
        self.right: Optional[TreeNode] = None


class BalanceTester:
    """平衡性测试器"""

    def __init__(self):
        pass

    def get_height(self, root: Optional[TreeNode]) -> int:
        """
        获取树的高度

        返回：高度（-1如果为空）
        """
        if root is None:
            return -1

        left_height = self.get_height(root.left)
        right_height = self.get_height(root.right)

        return 1 + max(left_height, right_height)

    def is_balanced_avl(self, root: Optional[TreeNode]) -> bool:
        """
        检查AVL平衡性

        AVL: |height(left) - height(right)| ≤ 1 对所有节点成立
        """
        if root is None:
            return True

        left_height = self.get_height(root.left)
        right_height = self.get_height(root.right)

        if abs(left_height - right_height) > 1:
            return False

        return (self.is_balanced_avl(root.left) and
                self.is_balanced_avl(root.right))

    def is_balanced_recursive(self, root: Optional[TreeNode]) -> bool:
        """
        高效的平衡检查（一次遍历）

        返回：是否平衡
        """
        def check(node: Optional[TreeNode]) -> tuple:
            """
            返回 (is_balanced, height)
            """
            if node is None:
                return True, -1

            left_bal, left_h = check(node.left)
            right_bal, right_h = check(node.right)

            if not left_bal or not right_bal:
                return False, 0

            if abs(left_h - right_h) > 1:
                return False, 0

            return True, 1 + max(left_h, right_h)

        balanced, _ = check(root)
        return balanced

    def approximate_balance(self, root: Optional[TreeNode]) -> dict:
        """
        近似平衡检查（高度 O(log n)）

        返回：检查结果
        """
        n = self._count_nodes(root)

        if n == 0:
            return {'is_approximate_balanced': True, 'height': -1, 'n_nodes': 0}

        height = self.get_height(root)

        # 近似平衡：height ≤ c * log(n)
        c = 2.0  # 宽松的常数

        is_balanced = height <= c * (n ** 0.5)  # 更宽松的标准

        return {
            'is_approximate_balanced': is_balanced,
            'height': height,
            'n_nodes': n,
            'log_bound': c * (n ** 0.5)
        }

    def _count_nodes(self, root: Optional[TreeNode]) -> int:
        """统计节点数"""
        if root is None:
            return 0
        return 1 + self._count_nodes(root.left) + self._count_nodes(root.right)


def balance_tree_types():
    """平衡树类型"""
    print("=== 平衡树类型 ===")
    print()
    print("1. AVL树")
    print("  - 高度差 ≤ 1")
    print("  - 插入/删除需要旋转")
    print()
    print("2. 红黑树")
    print("  - 路径长度最多差2倍")
    print("  - 旋转较少，性能稳定")
    print()
    print("3. 近似平衡")
    print("  - 高度 O(log n)")
    print("  - 更宽松的定义")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 二叉树平衡性测试 ===\n")

    # 构建测试树
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3)
    root.left.left = TreeNode(4)
    root.left.right = TreeNode(5)

    tester = BalanceTester()

    print("测试树:")
    print("       1")
    print("      / \\")
    print("     2   3")
    print("    / \\")
    print("   4   5")
    print()

    # AVL平衡检查
    is_avl = tester.is_balanced_avl(root)
    print(f"AVL平衡: {'是' if is_avl else '否'}")

    # 高效检查
    is_bal = tester.is_balanced_recursive(root)
    print(f"高效平衡检查: {'是' if is_bal else '否'}")

    # 近似平衡
    result = tester.approximate_balance(root)
    print(f"\n近似平衡检查:")
    print(f"  节点数: {result['n_nodes']}")
    print(f"  高度: {result['height']}")
    print(f"  近似平衡: {'是' if result['is_approximate_balanced'] else '否'}")

    print()

    # 测试不平衡的树
    print("测试不平衡的树:")
    unbalanced = TreeNode(1)
    unbalanced.left = TreeNode(2)
    unbalanced.left.left = TreeNode(3)
    unbalanced.left.left.left = TreeNode(4)

    is_avl = tester.is_balanced_avl(unbalanced)
    is_bal = tester.is_balanced_recursive(unbalanced)

    print(f"  AVL平衡: {'是' if is_avl else '否'}")
    print(f"  高效检查: {'是' if is_bal else '否'}")

    print()
    balance_tree_types()

    print()
    print("说明：")
    print("  - 平衡性测试用于验证树结构")
    print("  - AVL定义最严格")
    print("  - 近似平衡更实用")
