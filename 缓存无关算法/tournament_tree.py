# -*- coding: utf-8 -*-

"""

算法实现：缓存无关算法 / tournament_tree



本文件实现 tournament_tree 相关的算法功能。

"""



import heapq

from typing import List, Tuple





class TournamentTree:

    """

    优超树(败者树变体)

    用于高效合并多个有序序列

    """

    

    def __init__(self, sorted_lists: List[List[int]]):

        """

        初始化

        

        Args:

            sorted_lists: 有序列表列表

        """

        self.lists = sorted_lists

        self.k = len(sorted_lists)

        self.n = sum(len(lst) for lst in sorted_lists)

        

        # 每个列表的当前指针

        self.pointers = [0] * self.k

        

        # 构建优超树

        self._build_tree()

    

    def _build_tree(self):

        """构建优超树"""

        # 计算树的深度和节点数

        self.depth = (self.k - 1).bit_length()

        self.size = 2 * self.k - 1

        

        # 初始化树

        # 叶子节点存储列表索引,内部节点存储"败者"

        # winner=0表示左孩子赢,winner=1表示右孩子赢

        self.tree = [0] * self.size

        

        # 初始化叶子节点

        for i in range(self.k):

            leaf_idx = self._leaf_index(i)

            self.tree[leaf_idx] = i  # 存储列表索引

    

    def _leaf_index(self, list_idx: int) -> int:

        """获取叶子节点的索引"""

        return self.size // 2 + list_idx

    

    def _parent(self, idx: int) -> int:

        """获取父节点索引"""

        return (idx - 1) // 2

    

    def _left_child(self, idx: int) -> int:

        """获取左孩子索引"""

        return 2 * idx + 1

    

    def _right_child(self, idx: int) -> int:

        """获取右孩子索引"""

        return 2 * idx + 2

    

    def get_winner(self) -> Tuple[int, int]:

        """

        获取当前最小元素

        

        Returns:

            (列表索引, 元素值)

        """

        if not self.lists:

            return -1, None

        

        # 从根开始向下比较

        leaf_idx = self._leaf_index(0)

        winner_list = self.tree[leaf_idx]

        

        if self.pointers[winner_list] >= len(self.lists[winner_list]):

            return -1, None

        

        value = self.lists[winner_list][self.pointers[winner_list]]

        return winner_list, value

    

    def advance(self, list_idx: int):

        """

        让指定列表的指针前进

        

        Args:

            list_idx: 列表索引

        """

        self.pointers[list_idx] += 1

        

        # 更新从该叶子到根的路径

        leaf_idx = self._leaf_index(list_idx)

        idx = self._parent(leaf_idx)

        

        while idx >= 0:

            left_leaf = self._leaf_index(self.tree[self._left_child(idx)])

            right_leaf = self._leaf_index(self.tree[self._right_child(idx)])

            

            left_list = self.tree[left_leaf]

            right_list = self.tree[right_leaf]

            

            # 获取两个列表的当前元素(或无穷大)

            left_val = (self.lists[left_list][self.pointers[left_list]] 

                       if self.pointers[left_list] < len(self.lists[left_list]) 

                       else float('inf'))

            right_val = (self.lists[right_list][self.pointers[right_list]] 

                        if self.pointers[right_list] < len(self.lists[right_list]) 

                        else float('inf'))

            

            # 败者进入父节点

            if left_val < right_val:

                self.tree[idx] = right_list

            else:

                self.tree[idx] = left_list

            

            if idx == 0:

                break

            idx = self._parent(idx)





def merge_k_sorted(lists: List[List[int]], m: int) -> List[int]:

    """

    合并k个有序列表,返回前m个最小元素

    

    Args:

        lists: 有序列表列表

        m: 要返回的元素个数

    

    Returns:

        前m个最小元素

    """

    if not lists or m <= 0:

        return []

    

    k = len(lists)

    

    # 过滤空列表

    non_empty = [(i, lists[i]) for i in range(k) if lists[i]]

    if not non_empty:

        return []

    

    k = len(non_empty)

    sorted_lists = [lst for _, lst in non_empty]

    

    # 创建优超树

    tree = TournamentTree(sorted_lists)

    

    result = []

    list_idx_map = {non_empty[i][0]: i for i in range(k)}

    

    for _ in range(min(m, tree.n)):

        winner_original_idx, value = tree.get_winner()

        if winner_original_idx == -1:

            break

        

        result.append(value)

        

        # 找到winner在sorted_lists中的索引

        winner_sorted_idx = list_idx_map[winner_original_idx]

        tree.advance(winner_sorted_idx)

    

    return result





def heap_merge_k_sorted(lists: List[List[int]], m: int) -> List[int]:

    """

    使用堆合并k个有序列表

    

    Args:

        lists: 有序列表列表

        m: 要返回的元素个数

    

    Returns:

        前m个最小元素

    """

    if not lists or m <= 0:

        return []

    

    # 初始化堆: (值, 列表索引, 元素索引)

    heap = []

    for i, lst in enumerate(lists):

        if lst:

            heapq.heappush(heap, (lst[0], i, 0))

    

    result = []

    

    for _ in range(m):

        if not heap:

            break

        

        val, list_idx, elem_idx = heapq.heappop(heap)

        result.append(val)

        

        # 推入同一个列表的下一个元素

        if elem_idx + 1 < len(lists[list_idx]):

            next_val = lists[list_idx][elem_idx + 1]

            heapq.heappush(heap, (next_val, list_idx, elem_idx + 1))

    

    return result





def tournament_merge_all(lists: List[List[int]]) -> List[int]:

    """

    使用优超树合并所有元素(保持有序)

    

    Args:

        lists: 有序列表列表

    

    Returns:

        合并后的有序列表

    """

    return merge_k_sorted(lists, sum(len(lst) for lst in lists))





# 测试代码

if __name__ == "__main__":

    # 测试1: 基本功能

    print("测试1 - 基本功能:")

    lists1 = [

        [1, 4, 7, 10],

        [2, 5, 8, 11],

        [3, 6, 9, 12]

    ]

    

    print(f"  输入列表: {lists1}")

    

    first5 = merge_k_sorted(lists1, 5)

    print(f"  前5个元素: {first5}")

    

    all_elem = tournament_merge_all(lists1)

    print(f"  全部合并: {all_elem}")

    

    # 测试2: 不同长度列表

    print("\n测试2 - 不同长度列表:")

    lists2 = [

        [1, 3, 5, 7, 9],

        [2, 4],

        [6, 8, 10, 12, 14, 16]

    ]

    

    print(f"  输入: {lists2}")

    first7 = merge_k_sorted(lists2, 7)

    print(f"  前7个: {first7}")

    

    # 测试3: 堆方法对比

    print("\n测试3 - 堆方法对比:")

    lists3 = [

        [1, 5, 9, 13],

        [2, 6, 10, 14],

        [3, 7, 11, 15],

        [4, 8, 12, 16]

    ]

    

    result_tournament = merge_k_sorted(lists3, 10)

    result_heap = heap_merge_k_sorted(lists3, 10)

    

    print(f"  优超树: {result_tournament}")

    print(f"  堆方法: {result_heap}")

    print(f"  一致: {result_tournament == result_heap}")

    

    # 测试4: 性能对比

    print("\n测试4 - 性能对比:")

    import time

    import random

    

    # 生成测试数据

    k = 100  # 100个列表

    n_per_list = 1000  # 每个列表1000个元素

    

    lists_perf = []

    for _ in range(k):

        lst = sorted([random.randint(1, 1000000) for _ in range(n_per_list)])

        lists_perf.append(lst)

    

    m = 5000  # 取前5000个

    

    # 优超树

    start = time.time()

    result_t = merge_k_sorted(lists_perf, m)

    time_t = time.time() - start

    

    # 堆

    start = time.time()

    result_h = heap_merge_k_sorted(lists_perf, m)

    time_h = time.time() - start

    

    print(f"  数据: {k}个列表,每列表{n_per_list}个元素")

    print(f"  取前{m}个:")

    print(f"    优超树: {time_t:.4f}s")

    print(f"    堆方法: {time_h:.4f}s")

    print(f"    结果一致: {result_t == result_h}")

    

    # 测试5: 空列表处理

    print("\n测试5 - 空列表处理:")

    lists5 = [[1, 2], [], [3], [], [4, 5, 6]]

    result5 = merge_k_sorted(lists5, 4)

    print(f"  有空列表: {result5}")

    

    # 测试6: 特殊情况

    print("\n测试6 - 特殊情况:")

    lists6 = [[1], [1], [1], [1]]

    result6 = merge_k_sorted(lists6, 3)

    print(f"  全相同元素: {result6}")

    

    print("\n所有测试完成!")

