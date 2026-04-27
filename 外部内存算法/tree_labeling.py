# -*- coding: utf-8 -*-

"""

算法实现：外部内存算法 / tree_labeling



本文件实现 tree_labeling 相关的算法功能。

"""



from typing import List, Optional





class TreeNode:

    """树节点"""



    def __init__(self, val: int):

        self.val = val

        self.children: List[TreeNode] = []

        self.pre = 0   # 前序编号

        self.post = 0  # 后序编号

        self.size = 0 # 子树大小





class TreeLabeler:

    """树标记器"""



    def __init__(self):

        self.time = 0



    def euler_tour_labeling(self, root: Optional[TreeNode]) -> None:

        """

        欧拉tour标记



        参数：

            root: 根节点

        """

        if root is None:

            return



        self.time = 0

        self._dfs_preorder(root)

        self.time = 0

        self._dfs_postorder(root)

        self._compute_subtree_size(root)



    def _dfs_preorder(self, node: Optional[TreeNode]) -> None:

        """前序DFS"""

        if node is None:

            return



        self.time += 1

        node.pre = self.time



        for child in node.children:

            self._dfs_preorder(child)



    def _dfs_postorder(self, node: Optional[TreeNode]) -> None:

        """后序DFS"""

        if node is None:

            return



        for child in node.children:

            self._dfs_postorder(child)



        self.time += 1

        node.post = self.time



    def _compute_subtree_size(self, node: Optional[TreeNode]) -> int:

        """计算子树大小"""

        if node is None:

            return 0



        size = 1

        for child in node.children:

            size += self._compute_subtree_size(child)



        node.size = size

        return size



    def is_ancestor(self, u: TreeNode, v: TreeNode) -> bool:

        """

        检查u是否是v的祖先



        返回：是否祖先

        """

        # u是v的祖先当且仅当 u.pre <= v.pre <= u.pre + u.size - 1

        return (u.pre <= v.pre <= u.pre + u.size - 1)



    def subtree_range(self, node: TreeNode) -> tuple:

        """

        获取子树的区间



        返回：(start, end)

        """

        return (node.pre, node.pre + node.size - 1)





def tree_labeling_applications():

    """树标记应用"""

    print("=== 树标记应用 ===")

    print()

    print("1. XML/HTML解析")

    print("   - DOM树的区间表示")

    print("   - 快速查找子元素")

    print()

    print("2. 文件系统")

    print("   - 目录结构标记")

    print("   - 快速子树查询")

    print()

    print("3. 组织架构")

    print("   - 部门层级编号")

    print("   - 快速查找下属")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 树的外部内存标记测试 ===\n")



    # 构建测试树

    root = TreeNode(1)



    node2 = TreeNode(2)

    node3 = TreeNode(3)

    node4 = TreeNode(4)



    root.children = [node2, node3]



    node2.children = [TreeNode(5), TreeNode(6)]

    node3.children = [node4]

    node4.children = [TreeNode(7), TreeNode(8)]



    # 标记

    labeler = TreeLabeler()

    labeler.euler_tour_labeling(root)



    print("树结构：")

    print("       1")

    print("      / \\")

    print("     2   3")

    print("    / \\   \\")

    print("   5   6   4")

    print("          / \\")

    print("         7   8")

    print()



    # 显示标记

    print("前序标记和子树大小：")

    def show(node):

        if node:

            print(f"  节点 {node.val}: pre={node.pre}, size={node.size}, range={labeler.subtree_range(node)}")

            for c in node.children:

                show(c)



    show(root)

    print()



    # 祖先查询

    print("祖先查询：")

    print(f"  2 是 7 的祖先: {labeler.is_ancestor(node2, node4.children[0])}")

    print(f"  3 是 7 的祖先: {labeler.is_ancestor(node3, node4.children[0])}")

    print(f"  1 是 7 的祖先: {labeler.is_ancestor(root, node4.children[0])}")



    print()

    tree_labeling_applications()



    print()

    print("说明：")

    print("  - 树标记用于快速层次查询")

    print("  - 区间表示支持O(1)祖先检查")

    print("  - 广泛应用于XML和文件系统")

