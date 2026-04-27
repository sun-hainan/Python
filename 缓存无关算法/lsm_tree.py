# -*- coding: utf-8 -*-
"""
算法实现：缓存无关算法 / lsm_tree

本文件实现 lsm_tree 相关的算法功能。
"""

from typing import List, Tuple, Optional
import random
import bisect


class MemTable:
    """内存中的跳表"""
    
    class Node:
        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.forward = []
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.size = 0
        self.level = 1
        self.header = self.Node(None, None)
        self.header.forward = [None] * 16
    
    def insert(self, key, value):
        """插入键值对"""
        update = [None] * 16
        x = self.header
        
        # 找到插入位置
        for i in range(self.level - 1, -1, -1):
            while x.forward[i] and x.forward[i].key < key:
                x = x.forward[i]
            update[i] = x
        
        x = x.forward[0]
        if x and x.key == key:
            x.value = value
        else:
            new_level = random.randint(1, 16)
            if new_level > self.level:
                for i in range(self.level, new_level):
                    update[i] = self.header
                self.level = new_level
            
            x = self.Node(key, value)
            x.forward = [None] * new_level
            
            for i in range(new_level):
                x.forward[i] = update[i].forward[i]
                update[i].forward[i] = x
            
            self.size += 1
    
    def search(self, key):
        """搜索键"""
        x = self.header
        for i in range(self.level - 1, -1, -1):
            while x.forward[i] and x.forward[i].key < key:
                x = x.forward[i]
        x = x.forward[0]
        if x and x.key == key:
            return x.value
        return None
    
    def get_all(self):
        """获取所有键值对(排序)"""
        result = []
        x = self.header.forward[0]
        while x:
            result.append((x.key, x.value))
            x = x.forward[0]
        return result


class SSTable:
    """Sorted String Table"""
    
    def __init__(self, data: List[Tuple], filename: str):
        self.data = data  # [(key, value), ...] 按key排序
        self.filename = filename
        self.min_key = data[0][0] if data else None
        self.max_key = data[-1][0] if data else None
    
    def search(self, key) -> Optional[bytes]:
        """二分搜索"""
        if not self.data:
            return None
        
        idx = bisect.bisect_left(self.data, (key,))
        
        if idx < len(self.data) and self.data[idx][0] == key:
            return self.data[idx][1]
        return None
    
    def range_query(self, start_key, end_key) -> List[Tuple]:
        """范围查询"""
        start_idx = bisect.bisect_left(self.data, (start_key,))
        end_idx = bisect.bisect_right(self.data, (end_key,))
        return self.data[start_idx:end_idx]


class LSMTree:
    """
    LSM树存储引擎
    层级结构: L0(内存) -> L1 -> L2 -> ... -> Ln
    """
    
    def __init__(self, max_mem_size: int = 1000, num_levels: int = 4):
        self.max_mem_size = max_mem_size
        self.num_levels = num_levels
        
        # 内存表
        self.memtable = MemTable(max_mem_size)
        
        # 每层的SSTable列表
        self.levels: List[List[SSTable]] = [[] for _ in range(num_levels)]
        
        # 每个SSTable的最大键数量
        self.sstable_max_size = 100
    
    def put(self, key, value):
        """写入键值对"""
        self.memtable.insert(key, value)
        
        if self.memtable.size >= self.max_mem_size:
            self._flush_memtable()
    
    def get(self, key):
        """读取键"""
        # 先查内存表
        value = self.memtable.search(key)
        if value is not None:
            return value
        
        # 从最新层到最旧层搜索
        for level in range(len(self.levels)):
            for sstable in reversed(self.levels[level]):
                if sstable.min_key <= key <= sstable.max_key:
                    value = sstable.search(key)
                    if value is not None:
                        return value
        
        return None
    
    def _flush_memtable(self):
        """将内存表刷到磁盘(L0层)"""
        data = self.memtable.get_all()
        if not data:
            return
        
        # 创建SSTable
        filename = f"sst_{random.randint(0, 10000)}.dat"
        sstable = SSTable(data, filename)
        
        # 添加到L0
        self.levels[0].append(sstable)
        
        # 清空内存表
        self.memtable = MemTable(self.max_mem_size)
        
        # 可能需要压缩层级
        self._maybe_compact()
    
    def _maybe_compact(self):
        """检查是否需要压缩"""
        for level in range(len(self.levels) - 1):
            total_size = sum(len(sst.data) for sst in self.levels[level])
            
            if total_size > self.sstable_max_size * (level + 2):
                self._compact_level(level)
    
    def _compact_level(self, level: int):
        """压缩指定层级"""
        if level + 1 >= len(self.levels):
            return
        
        # 合并该层和下一层的所有SSTable
        all_data = []
        for sst in self.levels[level]:
            all_data.extend(sst.data)
        
        for sst in self.levels[level + 1]:
            all_data.extend(sst.data)
        
        # 排序并去重(保留最新的)
        all_data.sort(key=lambda x: x[0])
        deduped = []
        for key, value in reversed(all_data):
            if not deduped or deduped[-1][0] != key:
                deduped.append((key, value))
        deduped.reverse()
        
        # 创建新的SSTable
        new_sstables = []
        for i in range(0, len(deduped), self.sstable_max_size):
            chunk = deduped[i:i + self.sstable_max_size]
            if chunk:
                filename = f"sst_{random.randint(0, 10000)}.dat"
                new_sstables.append(SSTable(chunk, filename))
        
        # 替换
        self.levels[level] = []
        self.levels[level + 1] = new_sstables


# 测试代码
if __name__ == "__main__":
    # 测试1: 基本操作
    print("测试1 - 基本操作:")
    lsm = LSMTree(max_mem_size=10)
    
    for i in range(50):
        lsm.put(f"key_{i}", f"value_{i}")
    
    print(f"  写入50个键值对")
    
    # 搜索
    for key in ["key_0", "key_25", "key_49"]:
        value = lsm.get(key)
        print(f"  get('{key}') = '{value}'")
    
    # 测试2: 内存表刷新
    print("\n测试2 - 内存表刷新:")
    print(f"  内存表大小: {lsm.memtable.size}")
    print(f"  L0层SSTable数: {len(lsm.levels[0])}")
    
    # 测试3: 读取不存在的键
    print("\n测试3 - 不存在的键:")
    value = lsm.get("nonexistent")
    print(f"  get('nonexistent') = {value}")
    
    # 测试4: 大量写入
    print("\n测试4 - 大量写入:")
    lsm2 = LSMTree(max_mem_size=100)
    
    import time
    start = time.time()
    
    for i in range(10000):
        lsm2.put(f"key_{i}", f"value_{i}")
    
    elapsed = time.time() - start
    print(f"  写入10000个键值对: {elapsed:.3f}s")
    print(f"  每秒写入: {10000/elapsed:.0f}")
    
    # 验证
    found = sum(1 for i in range(10000) if lsm2.get(f"key_{i}") == f"value_{i}")
    print(f"  正确读取: {found}/10000")
    
    print("\n所有测试完成!")
