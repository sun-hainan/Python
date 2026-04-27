# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / cfs_scheduler



本文件实现 cfs_scheduler 相关的算法功能。

"""



from typing import Optional, List, Callable

from dataclasses import dataclass





@dataclass

class RBNode:

    """红黑树节点"""

    key: int                    # 键（vruntime）

    value: any = None          # 值（任务信息）

    color: int = 1             # 1=红色, 0=黑色

    left: Optional['RBNode'] = None

    right: Optional['RBNode'] = None

    parent: Optional['RBNode'] = None





class RBColor:

    """节点颜色"""

    BLACK = 0

    RED = 1





class RedBlackTree:

    """

    红黑树



    用于CFS调度器中按vruntime排序任务。

    """



    def __init__(self):

        self.NIL = RBNode(key=0, color=RBColor.BLACK)  # 哨兵节点

        self.root = self.NIL



    def _left_rotate(self, x: RBNode):

        """左旋"""

        y = x.right

        x.right = y.left

        if y.left != self.NIL:

            y.left.parent = x

        y.parent = x.parent

        if x.parent is None:

            self.root = y

        elif x == x.parent.left:

            x.parent.left = y

        else:

            x.parent.right = y

        y.left = x

        x.parent = y



    def _right_rotate(self, y: RBNode):

        """右旋"""

        x = y.left

        y.left = x.right

        if x.right != self.NIL:

            x.right.parent = y

        x.parent = y.parent

        if y.parent is None:

            self.root = x

        elif y == y.parent.right:

            y.parent.right = x

        else:

            y.parent.left = x

        x.right = y

        y.parent = x



    def insert(self, key: int, value: any = None):

        """

        插入节点

        param key: 键值（vruntime）

        param value: 关联的值（任务信息）

        """

        z = RBNode(key=key, value=value, color=RBColor.RED)

        z.left = self.NIL

        z.right = self.NIL

        z.parent = None



        y = None

        x = self.root



        # BST插入

        while x != self.NIL:

            y = x

            if z.key < x.key:

                x = x.left

            else:

                x = x.right



        z.parent = y

        if y is None:

            self.root = z

        elif z.key < y.key:

            y.left = z

        else:

            y.right = z



        z.left = self.NIL

        z.right = self.NIL

        z.color = RBColor.RED



        self._insert_fixup(z)



    def _insert_fixup(self, z: RBNode):

        """插入修复"""

        while z.parent and z.parent.color == RBColor.RED:

            if z.parent == z.parent.parent.left:

                y = z.parent.parent.right

                if y and y.color == RBColor.RED:

                    z.parent.color = RBColor.BLACK

                    y.color = RBColor.BLACK

                    z.parent.parent.color = RBColor.RED

                    z = z.parent.parent

                else:

                    if z == z.parent.right:

                        z = z.parent

                        self._left_rotate(z)

                    z.parent.color = RBColor.BLACK

                    z.parent.parent.color = RBColor.RED

                    self._right_rotate(z.parent.parent)

            else:

                y = z.parent.parent.left

                if y and y.color == RBColor.RED:

                    z.parent.color = RBColor.BLACK

                    y.color = RBColor.BLACK

                    z.parent.parent.color = RBColor.RED

                    z = z.parent.parent

                else:

                    if z == z.parent.left:

                        z = z.parent

                        self._right_rotate(z)

                    z.parent.color = RBColor.BLACK

                    z.parent.parent.color = RBColor.RED

                    self._left_rotate(z.parent.parent)



        self.root.color = RBColor.BLACK



    def delete(self, key: int):

        """删除键为key的节点"""

        z = self._search(key)

        if z != self.NIL:

            self._delete_node(z)



    def _delete_node(self, z: RBNode):

        """删除节点"""

        y = z

        y_original_color = y.color



        if z.left == self.NIL:

            x = z.right

            self._transplant(z, z.right)

        elif z.right == self.NIL:

            x = z.left

            self._transplant(z, z.left)

        else:

            y = self._minimum(z.right)

            y_original_color = y.color

            x = y.right

            if y.parent == z:

                x.parent = y

            else:

                self._transplant(y, y.right)

                y.right = z.right

                y.right.parent = y

            self._transplant(z, y)

            y.left = z.left

            y.left.parent = y

            y.color = z.color



        if y_original_color == RBColor.BLACK:

            self._delete_fixup(x)



    def _delete_fixup(self, x: RBNode):

        """删除修复"""

        while x != self.root and (x is None or x.color == RBColor.BLACK):

            if x == x.parent.left:

                w = x.parent.right

                if w and w.color == RBColor.RED:

                    w.color = RBColor.BLACK

                    x.parent.color = RBColor.RED

                    self._left_rotate(x.parent)

                    w = x.parent.right

                if (w.left is None or w.left.color == RBColor.BLACK) and \

                   (w.right is None or w.right.color == RBColor.BLACK):

                    w.color = RBColor.RED

                    x = x.parent

                else:

                    if w.right is None or w.right.color == RBColor.BLACK:

                        if w.left:

                            w.left.color = RBColor.BLACK

                        w.color = RBColor.RED

                        self._right_rotate(w)

                        w = x.parent.right

                    w.color = x.parent.color

                    x.parent.color = RBColor.BLACK

                    if w.right:

                        w.right.color = RBColor.BLACK

                    self._left_rotate(x.parent)

                    x = self.root

            else:

                w = x.parent.left

                if w and w.color == RBColor.RED:

                    w.color = RBColor.BLACK

                    x.parent.color = RBColor.RED

                    self._right_rotate(x.parent)

                    w = x.parent.left

                if (w.right is None or w.right.color == RBColor.BLACK) and \

                   (w.left is None or w.left.color == RBColor.BLACK):

                    w.color = RBColor.RED

                    x = x.parent

                else:

                    if w.left is None or w.left.color == RBColor.BLACK:

                        if w.right:

                            w.right.color = RBColor.BLACK

                        w.color = RBColor.RED

                        self._left_rotate(w)

                        w = x.parent.left

                    w.color = x.parent.color

                    x.parent.color = RBColor.BLACK

                    if w.left:

                        w.left.color = RBColor.BLACK

                    self._right_rotate(x.parent)

                    x = self.root



        if x:

            x.color = RBColor.BLACK



    def _transplant(self, u: RBNode, v: RBNode):

        """移植节点"""

        if u.parent is None:

            self.root = v

        elif u == u.parent.left:

            u.parent.left = v

        else:

            u.parent.right = v

        v.parent = u.parent



    def _search(self, key: int) -> RBNode:

        """搜索节点"""

        x = self.root

        while x != self.NIL and key != x.key:

            if key < x.key:

                x = x.left

            else:

                x = x.right

        return x



    def _minimum(self, node: RBNode) -> RBNode:

        """查找最小节点"""

        while node.left != self.NIL:

            node = node.left

        return node



    def minimum(self) -> Optional[RBNode]:

        """获取最小节点（最左节点）"""

        if self.root == self.NIL:

            return None

        return self._minimum(self.root)



    def maximum(self) -> Optional[RBNode]:

        """获取最大节点（最右节点）"""

        if self.root == self.NIL:

            return None

        node = self.root

        while node.right != self.NIL:

            node = node.right

        return node



    def inorder_traversal(self, callback: Callable[[RBNode], None]):

        """中序遍历"""

        def _inorder(node: RBNode):

            if node != self.NIL:

                _inorder(node.left)

                callback(node)

                _inorder(node.right)



        _inorder(self.root)



    def get_height(self) -> int:

        """获取树高度"""

        def _height(node: RBNode) -> int:

            if node == self.NIL:

                return 0

            return 1 + max(_height(node.left), _height(node.right))



        return _height(self.root)



    def get_all_keys(self) -> List[int]:

        """获取所有键（按顺序）"""

        keys = []



        def collect(node: RBNode):

            if node != self.NIL:

                collect(node.left)

                keys.append(node.key)

                collect(node.right)



        collect(self.root)

        return keys





def simulate_rbtree():

    """

    模拟红黑树

    """

    print("=" * 60)

    print("红黑树 (Red-Black Tree) 模拟")

    print("=" * 60)



    rbtree = RedBlackTree()



    # 插入一系列vruntime值

    vruntime_sequence = [1000, 500, 1500, 300, 800, 1200, 600, 900]



    print("\n插入vruntime序列:", vruntime_sequence)

    print("-" * 50)



    for vruntime in vruntime_sequence:

        rbtree.insert(vruntime, {"task_name": f"task_{vruntime}"})

        print(f"插入 vruntime={vruntime}, 树高度={rbtree.get_height()}")



    print(f"\n最终树高度: {rbtree.get_height()}")

    print(f"树中所有键(按顺序): {rbtree.get_all_keys()}")



    # 获取最小vruntime（最左节点）

    min_node = rbtree.minimum()

    print(f"\n最小vruntime (CFS下一个调度): {min_node.key if min_node else 'N/A'}")



    # 中序遍历

    print("\n中序遍历 (按vruntime排序):")

    print("-" * 30)



    def print_node(node: RBNode):

        color_str = "红" if node.color == RBColor.RED else "黑"

        print(f"  vruntime={node.key} [{color_str}色], value={node.value}")



    rbtree.inorder_traversal(print_node)



    # 删除最小节点（模拟调度）

    print("\n模拟调度 - 删除最小vruntime:")

    for _ in range(3):

        min_node = rbtree.minimum()

        if min_node:

            print(f"  调度任务 vruntime={min_node.key}")

            rbtree.delete(min_node.key)

            print(f"  删除后剩余: {rbtree.get_all_keys()}")





if __name__ == "__main__":

    simulate_rbtree()

