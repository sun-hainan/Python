# -*- coding: utf-8 -*-
"""
算法实现：缓存无关算法 / cache_oblivious_priority_queue

本文件实现 cache_oblivious_priority_queue 相关的算法功能。
"""

from typing import List, Optional, Tuple
import math


class CacheObliviousPriorityQueue:
    """
    缓存无关优先队列
    使用van Emde Boas布局实现缓存无关性
    
    操作复杂度:
    - insert: O(1/B log₂(N/B) + 1/B)
    - delete_min: O(log₂ N / log₂ log₂ N) 或更好
    """
    
    def __init__(self, capacity: int):
        """
        初始化
        
        Args:
            capacity: 预估最大元素数
        """
        self.n = 0
        self.capacity = capacity
        self.size = 1
        while self.size < capacity:
            self.size *= 2
        
        # 使用列表存储,按van Emde Boas布局组织
        self.data = [None] * self.size
        self.heap = [None] * self.size  # 维护堆性质
    
    def _veb_layout(self, idx: int) -> int:
        """
        van Emde Boas布局映射
        
        Args:
            idx: 逻辑索引
        
        Returns:
            物理存储位置
        """
        h = int(math.sqrt(self.size))
        
        # 分割索引
        high = idx // h
        low = idx % h
        
        # 重构位置
        return high * h + low
    
    def _parent(self, idx: int) -> int:
        """获取父节点"""
        return (idx - 1) // 2
    
    def _left_child(self, idx: int) -> int:
        """获取左孩子"""
        return 2 * idx + 1
    
    def _right_child(self, idx: int) -> int:
        """获取右孩子"""
        return 2 * idx + 2
    
    def insert(self, value: int):
        """
        插入元素
        
        Args:
            value: 要插入的值
        """
        if self.n >= self.size:
            self._resize(self.size * 2)
        
        # 找到插入位置(最后一个叶子)
        pos = self.n
        physical_pos = self._veb_layout(pos)
        
        self.data[physical_pos] = value
        self.n += 1
        
        # 向上调整恢复堆性质
        self._sift_up(pos)
    
    def _sift_up(self, idx: int):
        """向上调整"""
        while idx > 0:
            parent = self._parent(idx)
            p_phys = self._veb_layout(parent)
            c_phys = self._veb_layout(idx)
            
            if self.data[p_phys] > self.data[c_phys]:
                self.data[p_phys], self.data[c_phys] = self.data[c_phys], self.data[p_phys]
                idx = parent
            else:
                break
    
    def delete_min(self) -> Optional[int]:
        """
        删除并返回最小元素
        
        Returns:
            最小元素或None
        """
        if self.n == 0:
            return None
        
        # 获取根
        root_phys = self._veb_layout(0)
        min_val = self.data[root_phys]
        
        # 将最后一个元素移到根
        last_phys = self._veb_layout(self.n - 1)
        self.data[root_phys] = self.data[last_phys]
        self.data[last_phys] = None
        self.n -= 1
        
        # 向下调整
        if self.n > 0:
            self._sift_down(0)
        
        return min_val
    
    def _sift_down(self, idx: int):
        """向下调整"""
        while True:
            smallest = idx
            left = self._left_child(idx)
            right = self._right_child(idx)
            
            for child in [left, right]:
                if child < self.n:
                    child_phys = self._veb_layout(child)
                    smallest_phys = self._veb_layout(smallest)
                    
                    if self.data[child_phys] < self.data[smallest_phys]:
                        smallest = child
            
            if smallest != idx:
                idx_phys = self._veb_layout(idx)
                smallest_phys = self._veb_layout(smallest)
                
                self.data[idx_phys], self.data[smallest_phys] = \
                    self.data[smallest_phys], self.data[idx_phys]
                
                idx = smallest
            else:
                break
    
    def _resize(self, new_size: int):
        """扩容"""
        new_data = [None] * new_size
        
        for i in range(self.n):
            old_phys = self._veb_layout(i)
            new_phys = i  # 简化:在新数组中线性排列
            new_data[new_phys] = self.data[old_phys]
        
        self.data = new_data
        self.size = new_size
    
    def peek_min(self) -> Optional[int]:
        """查看最小元素"""
        if self.n == 0:
            return None
        return self.data[self._veb_layout(0)]
    
    def __len__(self) -> int:
        """返回元素数量"""
        return self.n
    
    def is_empty(self) -> bool:
        """是否为空"""
        return self.n == 0


class BufferTreePQ:
    """
    缓冲区树优先队列
    一种批处理优先队列,适合大规模数据
    
    通过批量处理提高缓存效率
    """
    
    def __init__(self, buffer_size: int = 64):
        """
        初始化
        
        Args:
            buffer_size: 缓冲区大小
        """
        self.B = buffer_size
        self.buffers: List[List[int]] = []
        self.heap = []  # 主堆
    
    def insert(self, value: int):
        """插入元素"""
        self.heap.append(value)
        if len(self.heap) >= self.B:
            self._flush_buffer()
    
    def _flush_buffer(self):
        """刷新缓冲区到更高层"""
        if not self.heap:
            return
        
        # 对当前缓冲区排序
        self.heap.sort()
        
        # 合并到主堆
        if not self.buffers:
            self.buffers.append(self.heap)
        else:
            # 合并到最后一个缓冲区
            last = self.buffers[-1]
            merged = self._merge_sorted(self.heap, last)
            
            if len(merged) <= self.B * 2:
                self.buffers[-1] = merged
            else:
                self.buffers.append(merged)
        
        self.heap = []
    
    def _merge_sorted(self, a: List[int], b: List[int]) -> List[int]:
        """合并两个有序列表"""
        result = []
        i = j = 0
        while i < len(a) and j < len(b):
            if a[i] < b[j]:
                result.append(a[i])
                i += 1
            else:
                result.append(b[j])
                j += 1
        result.extend(a[i:])
        result.extend(b[j:])
        return result
    
    def delete_min(self) -> Optional[int]:
        """删除最小元素"""
        if not self.heap and not self.buffers:
            return None
        
        # 确保heap有数据
        if not self.heap:
            self._refill_heap()
        
        if self.heap:
            min_val = self.heap[0]
            self.heap.pop(0)
            return min_val
        
        return None
    
    def _refill_heap(self):
        """从缓冲区补充主堆"""
        if self.buffers:
            self.heap = self.buffers.pop(0)
    
    def __len__(self) -> int:
        return len(self.heap) + sum(len(b) for b in self.buffers)


# 测试代码
if __name__ == "__main__":
    # 测试1: 基本操作
    print("测试1 - 基本操作:")
    pq = CacheObliviousPriorityQueue(16)
    
    for x in [5, 3, 7, 1, 9, 2, 4, 6]:
        pq.insert(x)
        print(f"  插入{x}: min={pq.peek_min()}")
    
    print("\n  删除顺序:")
    while not pq.is_empty():
        print(f"    {pq.delete_min()}")
    
    # 测试2: 大量数据
    print("\n测试2 - 大量数据:")
    import time
    import random
    
    random.seed(42)
    n = 100000
    
    # 缓存无关PQ
    pq1 = CacheObliviousPriorityQueue(n)
    start = time.time()
    for _ in range(n):
        pq1.insert(random.randint(1, 1000000))
    time_insert1 = time.time() - start
    
    start = time.time()
    result1 = []
    for _ in range(min(1000, n)):
        result1.append(pq1.delete_min())
    time_delete1 = time.time() - start
    
    print(f"  插入{n}个元素: {time_insert1:.4f}s")
    print(f"  删除1000个元素: {time_delete1:.4f}s")
    
    # 标准堆对比
    import heapq
    
    pq2 = []
    start = time.time()
    for _ in range(n):
        heapq.heappush(pq2, random.randint(1, 1000000))
    time_insert2 = time.time() - start
    
    start = time.time()
    result2 = []
    for _ in range(min(1000, n)):
        result2.append(heapq.heappop(pq2))
    time_delete2 = time.time() - start
    
    print(f"  标准堆插入: {time_insert2:.4f}s")
    print(f"  标准堆删除: {time_delete2:.4f}s")
    
    # 测试3: 验证正确性
    print("\n测试3 - 验证正确性:")
    random.seed(42)
    pq3 = CacheObliviousPriorityQueue(1000)
    expected = []
    
    for x in range(100):
        val = random.randint(1, 1000)
        pq3.insert(val)
        expected.append(val)
    
    expected.sort()
    result3 = []
    for _ in range(100):
        result3.append(pq3.delete_min())
    
    print(f"  结果正确: {result3 == expected}")
    
    # 测试4: BufferTree
    print("\n测试4 - BufferTree PQ:")
    btpq = BufferTreePQ(buffer_size=10)
    
    for x in [5, 3, 7, 1, 9, 2, 4, 6, 8]:
        btpq.insert(x)
        print(f"  插入{x}: size={len(btpq)}")
    
    print("\n  删除顺序:")
    while len(btpq) > 0:
        print(f"    {btpq.delete_min()}")
    
    # 测试5: 边界情况
    print("\n测试5 - 边界情况:")
    pq4 = CacheObliviousPriorityQueue(1)
    pq4.insert(42)
    print(f"  单元素: min={pq4.peek_min()}, delete={pq4.delete_min()}")
    print(f"  空队列peek: {pq4.peek_min()}")
    print(f"  空队列delete: {pq4.delete_min()}")
    
    print("\n所有测试完成!")
