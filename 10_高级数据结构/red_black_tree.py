"""
Red-Black Tree（红黑树）
==========================================

【原理】
近似平衡的二叉搜索树，保证任意路径不超过其他路径2倍。
通过着色规则实现自平衡。

【性质】
1. 节点非红即黑
2. 根节点为黑
3. 叶节点(NIL)为黑
4. 红节点子节点必为黑
5. 任一节点到叶节点路径黑高相同

【时间复杂度】O(log n)

【应用场景】
- C++ STL map/set
- Linux内核调度
- 进程管理
"""


class RBNode:
    def __init__(self, key, color='red'):
        self.key = key
        self.color = color
        self.left = None
        self.right = None
        self.parent = None


class RedBlackTree:
    """红黑树"""

    def __init__(self):
        self.NIL = RBNode(None, 'black')
        self.root = self.NIL

    def left_rotate(self, x):
        """左旋"""
        y = x.right
        x.right = y.left
        if y.left != self.NIL:
            y.left.parent = x
        y.parent = x.parent
        if x.parent == self.NIL:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y

    def right_rotate(self, y):
        """右旋"""
        x = y.left
        y.left = x.right
        if x.right != self.NIL:
            x.right.parent = y
        x.parent = y.parent
        if y.parent == self.NIL:
            self.root = x
        elif y == y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x
        x.right = y
        y.parent = x

    def insert(self, key):
        """插入"""
        node = RBNode(key, 'red')
        node.left = node.right = self.NIL

        parent = self.NIL
        current = self.root
        while current != self.NIL:
            parent = current
            if node.key < current.key:
                current = current.left
            else:
                current = current.right

        node.parent = parent
        if parent == self.NIL:
            self.root = node
        elif node.key < parent.key:
            parent.left = node
        else:
            parent.right = node

        self._insert_fixup(node)

    def _insert_fixup(self, node):
        """插入修复"""
        while node.parent.color == 'red':
            if node.parent == node.parent.parent.left:
                uncle = node.parent.parent.right
                if uncle.color == 'red':
                    node.parent.color = 'black'
                    uncle.color = 'black'
                    node.parent.parent.color = 'red'
                    node = node.parent.parent
                else:
                    if node == node.parent.right:
                        node = node.parent
                        self.left_rotate(node)
                    node.parent.color = 'black'
                    node.parent.parent.color = 'red'
                    self.right_rotate(node.parent.parent)
            else:
                uncle = node.parent.parent.left
                if uncle.color == 'red':
                    node.parent.color = 'black'
                    uncle.color = 'black'
                    node.parent.parent.color = 'red'
                    node = node.parent.parent
                else:
                    if node == node.parent.left:
                        node = node.parent
                        self.right_rotate(node)
                    node.parent.color = 'black'
                    node.parent.parent.color = 'red'
                    self.left_rotate(node.parent.parent)
        self.root.color = 'black'


if __name__ == "__main__":
    print("Red-Black Tree测试")
    rbt = RedBlackTree()
    for x in [7, 3, 18, 10, 22, 8, 11]:
        rbt.insert(x)
    print("插入完成，红黑树高度~O(log n)")
