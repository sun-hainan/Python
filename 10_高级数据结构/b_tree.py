"""
B-Tree（B树）
==========================================

【算法原理】
一种自平衡的多路搜索树，每个节点有多个键。
所有叶子节点在同一层，保持平衡。

【时间复杂度】
- 查找: O(log n)
- 插入: O(log n)
- 删除: O(log n)

【与BST的区别】
- BST是二叉，每个节点最多2个子节点
- B树多路，每个节点最多m个子节点
- B树更矮，磁盘IO次数少

【应用场景】
- 数据库索引（InnoDB使用B+树，但B树也是经典）
- 文件系统
- 磁盘数据结构
"""

from typing import List, Optional, Tuple


class BTreeNode:
    """B树节点"""
    def __init__(self, leaf: bool = False):
        # 是否为叶子节点
        self.leaf = leaf
        # 键列表（有序）
        self.keys = []
        # 子节点列表（长度为len(keys)+1）
        self.children = []


class BTree:
    """
    B树

    【参数】
    - degree: 度，表示每个节点最多有degree个子节点
    - 每个节点最多有2*degree-1个键
    - 每个节点最少有degree-1个键（根除外）
    """

    def __init__(self, degree: int = 3):
        if degree < 2:
            raise ValueError("degree must be >= 2")
        self.degree = degree
        self.min_keys = degree - 1
        self.max_keys = 2 * degree - 1
        self.root = BTreeNode(leaf=True)

    def search(self, key) -> Optional[Tuple[BTreeNode, int]]:
        """
        查找键所在节点及索引

        【返回】(node, index) 或 None
        """
        return self._search(self.root, key)

    def _search(self, node: BTreeNode, key) -> Optional[Tuple[BTreeNode, int]]:
        """
        递归查找

        【思路】
        1. 在当前节点keys中二分查找key
        2. 找到了返回
        3. 未找到，递归到对应子节点
        """
        i = 0
        # 二分查找第一个 >= key 的位置
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        # 在当前节点找到
        if i < len(node.keys) and key == node.keys[i]:
            return (node, i)

        # 叶子节点未找到
        if node.leaf:
            return None

        # 递归到子节点
        return self._search(node.children[i], key)

    def insert(self, key) -> None:
        """
        插入键

        【步骤】
        1. 如果根节点满，先分裂根
        2. 递归找到合适的叶子节点
        3. 插入键（可能触发分裂向上传播）
        """
        root = self.root

        # 根节点满，需要分裂
        if len(root.keys) == self.max_keys:
            new_root = BTreeNode(leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0, self.root)
            self.root = new_root
            # 分裂后，根节点有2个子节点，现在要找到新键该插入的子节点
            self._insert_non_full(self.root, key)
        else:
            self._insert_non_full(root, key)

    def _insert_non_full(self, node: BTreeNode, key) -> None:
        """
        向非满节点插入键

        【实现】从右向左查找插入位置，保持有序
        """
        if node.leaf:
            # 叶子节点：直接插入
            i = len(node.keys) - 1
            while i >= 0 and node.keys[i] > key:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys.insert(i + 1, key)
        else:
            # 非叶子节点：找到合适的子节点
            i = len(node.keys) - 1
            while i >= 0 and node.keys[i] > key:
                i -= 1
            i += 1

            child = node.children[i]
            if len(child.keys) == self.max_keys:
                # 子节点满了，先分裂
                self._split_child(node, i, child)
                # 分裂后，中间键上移
                # 判断新键应该插入哪个子节点
                if key > node.keys[i]:
                    i += 1

            self._insert_non_full(node.children[i], key)

    def _split_child(self, parent: BTreeNode, index: int, child: BTreeNode) -> None:
        """
        分裂满子节点

        【分裂规则】
        - 节点有2d-1个键，满了
        - 分裂成两个节点，各d-1个键
        - 中间键上移到父节点
        """
        new_node = BTreeNode(leaf=child.leaf)

        # 分裂点：索引 d-1（中间键）
        mid = self.degree - 1

        # 新节点获得右半部分（mid+1 到 2d-2）
        new_node.keys = child.keys[mid + 1:]
        # 如果是非叶子，分裂子节点
        if not child.leaf:
            new_node.children = child.children[mid + 1:]
            child.children = child.children[:mid + 1]

        # 中间键上移到父节点
        parent.keys.insert(index, child.keys[mid])

        # 原节点保留左半部分
        child.keys = child.keys[:mid]

        # 父节点插入新子节点指针
        parent.children.insert(index + 1, new_node)

    def delete(self, key) -> bool:
        """删除键"""
        result = self._delete(self.root, key)
        # 如果根变成空树，调整
        if not self.root.keys and not self.root.leaf:
            self.root = self.root.children[0]
        return result

    def _delete(self, node: BTreeNode, key) -> bool:
        """
        删除键

        【三种情况】
        1. 键在叶子节点：直接删除
        2. 键在内部节点：用前驱/后继替换后删除
        3. 键不在当前节点：递归，找到合适的子节点
           - 如果子节点键数 == min_keys，需要借或合并
        """
        if node.leaf:
            # 情况1：叶子节点直接删除
            if key in node.keys:
                node.keys.remove(key)
                return True
            return False
        else:
            i = 0
            while i < len(node.keys) and key > node.keys[i]:
                i += 1

            if i < len(node.keys) and node.keys[i] == key:
                # 情况2：在内部节点找到
                # 用前驱替换后删除
                if len(node.children[i].keys) >= self.degree:
                    # 左子节点有足够的键，用前驱
                    predecessor = self._get_predecessor(node.children[i])
                    node.keys[i] = predecessor
                    return self._delete(node.children[i], predecessor)
                elif len(node.children[i + 1].keys) >= self.degree:
                    # 右子节点有足够的键，用后继
                    successor = self._get_successor(node.children[i + 1])
                    node.keys[i] = successor
                    return self._delete(node.children[i + 1], successor)
                else:
                    # 两个子节点都不够，需要合并
                    self._merge_children(node, i)
                    return self._delete(node.children[i], key)
            else:
                # 情况3：在子节点中递归删除
                child = node.children[i]

                if len(child.keys) < self.degree:
                    # 键数不够，需要借或合并
                    self._fix_child(node, i)

                # 重新确认子节点位置（合并后可能变化）
                if i < len(node.keys) and key == node.keys[i]:
                    return self._delete(node.children[i + 1], key)
                else:
                    # 重新定位
                    i = 0
                    while i < len(node.keys) and key > node.keys[i]:
                        i += 1
                    return self._delete(node.children[i], key)

    def _get_predecessor(self, node: BTreeNode) -> any:
        """获取前驱（最右叶子）"""
        current = node
        while not current.leaf:
            current = current.children[-1]
        return current.keys[-1]

    def _get_successor(self, node: BTreeNode) -> any:
        """获取后继（最左叶子）"""
        current = node
        while not current.leaf:
            current = current.children[0]
        return current.keys[0]

    def _merge_children(self, parent: BTreeNode, index: int) -> None:
        """合并两个子节点"""
        child = parent.children[index]
        sibling = parent.children[index + 1]

        # 将父节点的键下移
        child.keys.append(parent.keys[index])

        # 将兄弟节点的键和子节点合并
        child.keys.extend(sibling.keys)

        # 如果非叶子，合并子节点
        if not child.leaf:
            child.children.extend(sibling.children)

        # 从父节点删除兄弟节点的键
        parent.keys.pop(index)
        parent.children.pop(index + 1)

    def _fix_child(self, parent: BTreeNode, index: int) -> None:
        """
        修复子节点（当子节点键数不足时）

        【三种策略】
        1. 从左兄弟借键
        2. 从右兄弟借键
        3. 与兄弟合并
        """
        if index > 0 and len(parent.children[index - 1].keys) > self.min_keys:
            # 从左兄弟借
            sibling = parent.children[index - 1]
            child = parent.children[index]

            # 父节点的键下移，左兄弟的最大键上移
            child.keys.insert(0, parent.keys[index - 1])
            parent.keys[index - 1] = sibling.keys.pop()

            # 如果非叶子，子节点也要移动
            if not child.leaf:
                child.children.insert(0, sibling.children.pop())

        elif index < len(parent.children) - 1 and \
             len(parent.children[index + 1].keys) > self.min_keys:
            # 从右兄弟借
            sibling = parent.children[index + 1]
            child = parent.children[index]

            # 父节点的键下移，右兄弟的最小键上移
            child.keys.append(parent.keys[index])
            parent.keys[index] = sibling.keys.pop(0)

            if not child.leaf:
                child.children.append(sibling.children.pop(0))

        else:
            # 与兄弟合并
            if index == len(parent.children) - 1:
                index -= 1
            self._merge_children(parent, index)

    def display(self) -> List[Tuple[int, List]]:
        """返回树的层级结构"""
        result = []

        def traverse(node: BTreeNode, level: int):
            result.append((level, node.keys))
            if not node.leaf:
                for child in node.children:
                    traverse(child, level + 1)

        traverse(self.root, 0)
        return result


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("B树 - 测试")
    print("=" * 50)

    tree = BTree(degree=3)

    # 测试插入
    print("\n【测试1】插入")
    keys = [7, 4, 9, 1, 6, 8, 3, 5, 2]
    for k in keys:
        tree.insert(k)
        print(f"  插入 {k}")

    # 测试树的层级结构
    print("\n【测试2】树的层级结构")
    for level, keys_level in tree.display():
        print(f"  Level {level}: {keys_level}")

    # 测试查找
    print("\n【测试3】查找")
    for k in [5, 10, 1]:
        result = tree.search(k)
        if result:
            print(f"  找到 {k} 在 Level {result[0]}")
        else:
            print(f"  未找到 {k}")

    # 测试删除
    print("\n【测试4】删除")
    tree.delete(4)
    print(f"  删除 4 后搜索 4: {tree.search(4)}")
    tree.delete(7)
    print(f"  删除 7 后搜索 7: {tree.search(7)}")

    print("\n【测试5】删除后树结构")
    for level, keys_level in tree.display():
        print(f"  Level {level}: {keys_level}")

    print("\n" + "=" * 50)
    print("B树测试完成！")
    print("=" * 50)
