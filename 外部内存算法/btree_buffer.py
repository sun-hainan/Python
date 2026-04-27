# -*- coding: utf-8 -*-

"""

算法实现：外部内存算法 / btree_buffer



本文件实现 btree_buffer 相关的算法功能。

"""



import bisect





class BTreeNode:

    """B-树节点。"""



    def __init__(self, leaf=False, t=3):

        self.t = t  # 最小度数

        self.leaf = leaf

        self.keys = []   # 关键字列表

        self.children = []  # 子节点列表





class BTree:

    """B-树实现。"""



    def __init__(self, t=3):

        self.t = t  # 最小度数

        self.root = BTreeNode(leaf=True, t=t)



    def search(self, key):

        """

        在 B-树中搜索关键字。



        参数:

            key: 要搜索的关键字



        返回:

            (node, index) 如果找到，(None, None) 如果未找到

        """

        return self._search_recursive(self.root, key)



    def _search_recursive(self, node, key):

        """递归搜索。"""

        i = 0

        # 在当前节点中找第一个 >= key 的位置

        while i < len(node.keys) and key > node.keys[i]:

            i += 1



        if i < len(node.keys) and key == node.keys[i]:

            return (node, i)

        elif node.leaf:

            return (None, None)

        else:

            return self._search_recursive(node.children[i], key)



    def insert(self, key):

        """

        插入关键字到 B-树。



        如果根节点满了，则分裂根节点（树增高）。

        """

        root = self.root

        if len(root.keys) == 2 * self.t - 1:

            # 根节点满了，需要分裂

            new_root = BTreeNode(leaf=False, t=self.t)

            new_root.children.append(self.root)

            self._split_child(new_root, 0, root)

            self.root = new_root

            self._insert_nonfull(new_root, key)

        else:

            self._insert_nonfull(root, key)



    def _insert_nonfull(self, node, key):

        """在非满节点中插入关键字。"""

        i = len(node.keys) - 1



        if node.leaf:

            # 在叶子节点中插入

            bisect.insort(node.keys, key)

        else:

            # 找到应该插入的子节点

            while i >= 0 and key < node.keys[i]:

                i -= 1

            i += 1



            # 检查子节点是否满了

            if len(node.children[i].keys) == 2 * self.t - 1:

                self._split_child(node, i, node.children[i])

                if key > node.keys[i]:

                    i += 1



            self._insert_nonfull(node.children[i], key)



    def _split_child(self, parent, i, child):

        """

        分裂满子节点。



        将有 2t-1 个关键字的节点分裂为两个各有 t-1 个关键字的节点。

        中间关键字上升到父节点。

        """

        t = self.t

        new_node = BTreeNode(leaf=child.leaf, t=t)



        # 新节点获得后 t-1 个关键字

        new_node.keys = child.keys[t:]



        # 子节点保留前 t-1 个关键字

        child.keys = child.keys[:t - 1]



        # 如果不是叶子，需要移动子节点

        if not child.leaf:

            new_node.children = child.children[t:]

            child.children = child.children[:t]



        # 将中间关键字上升到父节点

        parent.keys.insert(i, child.keys.pop())



        # 将新节点挂为父节点的子节点

        parent.children.insert(i + 1, new_node)



    def range_query(self, lo, hi):

        """

        范围查询：找出 [lo, hi] 内的所有关键字。



        参数:

            lo, hi: 范围边界



        返回:

            关键字列表

        """

        results = []

        self._range_query_recursive(self.root, lo, hi, results)

        return results



    def _range_query_recursive(self, node, lo, hi, results):

        """递归范围查询。"""

        for i, key in enumerate(node.keys):

            if key < lo:

                # key 在范围左边，搜索左子树

                if not node.leaf:

                    self._range_query_recursive(node.children[i], lo, hi, results)

            elif lo <= key <= hi:

                # key 在范围内

                results.append(key)

                # 还需要搜索左右子树

                if not node.leaf:

                    self._range_query_recursive(node.children[i], lo, hi, results)

                    self._range_query_recursive(node.children[i + 1], lo, hi, results)

            else:

                # key > hi，不需要继续

                break



        # 如果不是叶子，检查最后一个子节点

        if not node.leaf and node.children:

            last_child = node.children[-1]

            if node.keys and last_child.keys and last_child.keys[0] <= hi:

                self._range_query_recursive(last_child, lo, hi, results)



    def height(self):

        """计算树的高度。"""

        h = 0

        node = self.root

        while not node.leaf:

            h += 1

            node = node.children[0]

        return h





class BufferTree:

    """缓冲区树（用于批量操作）。"""



    def __init__(self, b=3):

        self.b = b  # 缓冲区大小阈值

        self.root = BTree(t=b)

        self.buffer = []



    def insert(self, key):

        """插入关键字（带缓冲区）。"""

        self.buffer.append(key)

        if len(self.buffer) >= self.b:

            self._flush_buffer()



    def _flush_buffer(self):

        """将缓冲区内容刷新到 B-树。"""

        if self.buffer:

            for key in self.buffer:

                self.root.insert(key)

            self.buffer = []



    def search(self, key):

        """搜索关键字。"""

        self._flush_buffer()

        return self.root.search(key)



    def range_query(self, lo, hi):

        """范围查询。"""

        self._flush_buffer()

        return self.root.range_query(lo, hi)





if __name__ == "__main__":

    print("=== B-树测试 ===")



    # 创建 B-树（最小度数 t=3，即每个节点最多 5 个关键字）

    t = 3

    tree = BTree(t=t)



    # 插入关键字

    keys = [10, 20, 5, 6, 12, 30, 7, 17]

    print(f"插入关键字: {keys}")



    for key in keys:

        tree.insert(key)

        print(f"  插入 {key} 后，树高 = {tree.height()}")



    # 搜索

    print("\n搜索测试:")

    for search_key in [6, 15]:

        result = tree.search(search_key)

        if result[0]:

            print(f"  {search_key}: 找到 (节点, 索引)")

        else:

            print(f"  {search_key}: 未找到")



    # 范围查询

    print(f"\n范围查询 [5, 17]: {tree.range_query(5, 17)}")

    print(f"范围查询 [1, 35]: {tree.range_query(1, 35)}")



    # 缓冲区树测试

    print("\n=== 缓冲区树测试 ===")

    btree = BufferTree(b=4)

    for key in [3, 8, 1, 6, 9, 2, 7]:

        btree.insert(key)

        print(f"插入 {key}, 缓冲区: {btree.buffer}")



    btree._flush_buffer()

    print(f"刷新后搜索 6: {btree.search(6)}")



    print("\nB-树特性:")

    print(f"  高度: O(log_b n)")

    print(f"  每个节点最多 {2*t-1} 个关键字")

    print(f"  每个节点最少 {t-1} 个关键字（根除外）")

    print(f"  搜索: O(log_b n)")

    print(f"  插入/删除: O(log_b n)")

