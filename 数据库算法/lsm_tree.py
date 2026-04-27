# -*- coding: utf-8 -*-

"""

算法实现：数据库算法 / lsm_tree



本文件实现 lsm_tree 相关的算法功能。

"""



import time

import hashlib

import os

import struct

from typing import List, Optional, Tuple, Dict, Any

from dataclasses import dataclass, field

from collections import OrderedDict

import bisect





@dataclass

class KVEntry:

    """键值对条目"""

    key: bytes

    value: bytes

    timestamp: float  # 时间戳，用于版本控制

    deleted: bool = False  # 是否删除标记

    

    def is_valid(self) -> bool:

        """是否有效（非删除）"""

        return not self.deleted





class MemTable:

    """

    内存表（MemTable）

    使用有序字典维护，按key排序

    大小达到阈值后刷写成SSTable

    """

    

    def __init__(self, max_size: int = 1024 * 1024):  # 默认1MB

        self.max_size = max_size  # 最大大小

        self.data: OrderedDict[bytes, KVEntry] = OrderedDict()  # 有序键值对

        self.current_size = 0  # 当前大小

    

    def _estimate_size(self, key: bytes, value: bytes) -> int:

        """估算条目大小"""

        return len(key) + len(value) + 24  # 24为元数据开销

    

    def put(self, key: bytes, value: bytes, timestamp: float = None) -> bool:

        """

        插入键值对

        

        返回:

            True: 插入成功

            False: 表已满，需要刷写

        """

        if timestamp is None:

            timestamp = time.time()

        

        entry = KVEntry(key, value, timestamp)

        entry_size = self._estimate_size(key, value)

        

        # 检查是否更新

        if key in self.data:

            self.current_size -= self._estimate_size(key, self.data[key].value)

        

        # 检查容量

        if self.current_size + entry_size > self.max_size:

            return False

        

        self.data[key] = entry

        self.current_size += entry_size

        return True

    

    def delete(self, key: bytes, timestamp: float = None) -> bool:

        """标记删除"""

        if timestamp is None:

            timestamp = time.time()

        

        if key in self.data:

            # 标记删除

            self.data[key].deleted = True

            self.data[key].timestamp = timestamp

            return True

        return False

    

    def get(self, key: bytes) -> Optional[bytes]:

        """获取值（返回最新版本）"""

        if key not in self.data:

            return None

        entry = self.data[key]

        if entry.deleted:

            return None

        return entry.value

    

    def get_entry(self, key: bytes) -> Optional[KVEntry]:

        """获取完整条目"""

        return self.data.get(key)

    

    def get_range(self, start_key: bytes, end_key: bytes) -> List[Tuple[bytes, KVEntry]]:

        """获取范围内的所有键值对"""

        result = []

        for key, entry in self.data.items():

            if key >= start_key and key <= end_key:

                result.append((key, entry))

        return result

    

    def is_full(self) -> bool:

        """是否已满"""

        return self.current_size >= self.max_size

    

    def size(self) -> int:

        """返回条目数"""

        return len(self.data)

    

    def clear(self) -> None:

        """清空表"""

        self.data.clear()

        self.current_size = 0





class SSTable:

    """

    Sorted String Table (SSTable)

    存储在磁盘上的有序键值对文件

    """

    

    def __init__(self, file_path: str, level: int = 0):

        self.file_path = file_path

        self.level = level

        self.entries: List[KVEntry] = []  # 加载到内存的索引

        self.data_offset: Dict[bytes, int] = {}  # key -> 文件偏移

        self.min_key: Optional[bytes] = None

        self.max_key: Optional[bytes] = None

        self.size: int = 0

    

    def write(self, entries: List[KVEntry]) -> None:

        """写入SSTable文件"""

        # 创建目录

        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        

        with open(self.file_path, 'wb') as f:

            for entry in entries:

                # 记录偏移

                self.data_offset[entry.key] = f.tell()

                

                # 写入key, value, timestamp, deleted flag

                key_len = len(entry.key)

                value_len = len(entry.value)

                

                f.write(struct.pack('I', key_len))

                f.write(entry.key)

                f.write(struct.pack('I', value_len))

                f.write(entry.value)

                f.write(struct.pack('d', entry.timestamp))

                f.write(struct.pack('?', entry.deleted))

                

                self.size += 1

                

                # 更新范围

                if self.min_key is None or entry.key < self.min_key:

                    self.min_key = entry.key

                if self.max_key is None or entry.key > self.max_key:

                    self.max_key = entry.key

        

        self.entries = entries

    

    def read(self) -> None:

        """从文件读取SSTable"""

        if not os.path.exists(self.file_path):

            return

        

        self.entries = []

        self.data_offset = {}

        

        with open(self.file_path, 'rb') as f:

            while True:

                try:

                    # 读取key

                    key_len_bytes = f.read(4)

                    if not key_len_bytes:

                        break

                    key_len = struct.unpack('I', key_len_bytes)[0]

                    key = f.read(key_len)

                    

                    # 读取value

                    value_len = struct.unpack('I', f.read(4))[0]

                    value = f.read(value_len)

                    

                    # 读取元数据

                    timestamp = struct.unpack('d', f.read(8))[0]

                    deleted = struct.unpack('?', f.read(1))[0]

                    

                    entry = KVEntry(key, value, timestamp, deleted)

                    self.entries.append(entry)

                    self.data_offset[key] = len(key) + len(value) + 13

                    

                    if self.min_key is None or key < self.min_key:

                        self.min_key = key

                    if self.max_key is None or key > self.max_key:

                        self.max_key = key

                        

                except:

                    break

    

    def get(self, key: bytes) -> Optional[bytes]:

        """二分搜索获取值"""

        if self.min_key is None or self.max_key is None:

            return None

        

        if key < self.min_key or key > self.max_key:

            return None

        

        # 二分搜索

        keys = [e.key for e in self.entries]

        idx = bisect.bisect_left(keys, key)

        

        if idx < len(keys) and keys[idx] == key:

            entry = self.entries[idx]

            if entry.deleted:

                return None

            return entry.value

        

        return None

    

    def get_entry(self, key: bytes) -> Optional[KVEntry]:

        """获取完整条目"""

        keys = [e.key for e in self.entries]

        idx = bisect.bisect_left(keys, key)

        

        if idx < len(keys) and keys[idx] == key:

            return self.entries[idx]

        return None

    

    def overlaps(self, start_key: bytes, end_key: bytes) -> bool:

        """检查是否与给定范围重叠"""

        if self.min_key is None or self.max_key is None:

            return False

        return not (end_key < self.min_key or start_key > self.max_key)





class LSMTree:

    """

    LSM树

    

    参数:

        base_path: 存储基础路径

        mem_size: MemTable大小

        level_size: 每层SSTable倍数

    """

    

    def __init__(self, base_path: str = "./lsm_data", mem_size: int = 1024 * 1024, level_size: int = 10):

        self.base_path = base_path

        self.mem_size = mem_size

        self.level_size = level_size  # 每层文件数限制倍数

        

        # 当前活跃的MemTable

        self.active_mem: MemTable = MemTable(max_size=mem_size)

        

        # Immutable MemTables（等待刷写）

        self.immutable_mems: List[MemTable] = []

        

        # SSTable文件列表（按层组织）

        # sstables[level] = [SSTable列表]

        self.sstables: Dict[int, List[SSTable]] = {0: []}

        

        # 文件编号

        self.file_counter = 0

        

        # WAL (Write-Ahead Log)

        self.wal_path = os.path.join(base_path, "wal.log")

        self.wal_enabled = True

    

    def _new_file_path(self, level: int) -> str:

        """生成新文件路径"""

        self.file_counter += 1

        return os.path.join(self.base_path, f"L{level}_{self.file_counter}.sst")

    

    def _write_wal(self, key: bytes, value: bytes, deleted: bool = False) -> None:

        """写WAL"""

        if not self.wal_enabled:

            return

        

        os.makedirs(self.base_path, exist_ok=True)

        with open(self.wal_path, 'ab') as f:

            timestamp = time.time()

            key_len = len(key)

            value_len = len(value)

            f.write(struct.pack('I', key_len))

            f.write(key)

            f.write(struct.pack('I', value_len))

            f.write(value)

            f.write(struct.pack('d', timestamp))

            f.write(struct.pack('?', deleted))

    

    def put(self, key: bytes, value: bytes) -> None:

        """

        插入键值对

        1. 写WAL

        2. 写MemTable

        3. 如果MemTable满，触发刷写

        """

        # 写WAL

        self._write_wal(key, value)

        

        # 写MemTable

        if not self.active_mem.put(key, value):

            # MemTable已满，切换

            self.immutable_mems.append(self.active_mem)

            self.active_mem = MemTable(max_size=self.mem_size)

            self.active_mem.put(key, value)

        

        # 检查是否需要刷写immutable MemTables

        self._maybe_compact()

    

    def delete(self, key: bytes) -> None:

        """删除键值对"""

        self._write_wal(key, b'', deleted=True)

        self.active_mem.delete(key)

    

    def get(self, key: bytes) -> Optional[bytes]:

        """

        获取值

        按以下顺序查找:

        1. MemTable (最新)

        2. Immutable MemTables

        3. SSTable (从新到旧)

        """

        # 1. 检查MemTable

        result = self.active_mem.get(key)

        if result is not None:

            return result

        

        # 2. 检查Immutable MemTables

        for mem in reversed(self.immutable_mems):

            entry = mem.get_entry(key)

            if entry is not None:

                if entry.deleted:

                    return None

                return entry.value

        

        # 3. 检查SSTable (从新到旧)

        for level in sorted(self.sstables.keys(), reverse=True):

            for sst in reversed(self.sstables[level]):

                if sst.overlaps(key, key):

                    result = sst.get(key)

                    if result is not None:

                        return result

        

        return None

    

    def _maybe_compact(self) -> None:

        """检查并执行compaction"""

        # 如果有immutable MemTables，刷写到磁盘

        while self.immutable_mems:

            mem = self.immutable_mems.pop(0)

            self._flush_memtable(mem)

    

    def _flush_memtable(self, mem: MemTable) -> None:

        """将MemTable刷写到SSTable"""

        if mem.size() == 0:

            return

        

        # 收集所有有效条目

        entries = []

        for key, entry in mem.data.items():

            entries.append(entry)

        

        # 按key排序

        entries.sort(key=lambda e: e.key)

        

        # 创建SSTable

        sst = SSTable(self._new_file_path(0), level=0)

        sst.write(entries)

        

        self.sstables.setdefault(0, []).append(sst)

        

        # 检查是否需要level 0 compaction

        self._maybe_level_compact(0)

    

    def _maybe_level_compact(self, level: int) -> None:

        """检查指定层是否需要compact"""

        target_size = self.level_size ** (level + 1)

        

        if len(self.sstables.get(level, [])) > target_size:

            self._compact_level(level)

    

    def _compact_level(self, level: int) -> None:

        """合并指定层的SSTable"""

        if level not in self.sstables or not self.sstables[level]:

            return

        

        # 选择要合并的SSTable

        ssts = self.sstables[level]

        

        # 合并所有条目

        all_entries = []

        for sst in ssts:

            sst.read()

            all_entries.extend(sst.entries)

        

        # 按key排序，去重（保留最新）

        all_entries.sort(key=lambda e: (e.key, -e.timestamp))

        deduplicated = []

        seen_keys = set()

        for entry in all_entries:

            if entry.key not in seen_keys:

                deduplicated.append(entry)

                seen_keys.add(entry.key)

        

        # 写入新层

        new_level = level + 1

        new_sst = SSTable(self._new_file_path(new_level), level=new_level)

        new_sst.write(deduplicated)

        

        # 更新层级

        self.sstables.setdefault(new_level, []).append(new_sst)

        self.sstables[level] = []

    

    def get_stats(self) -> dict:

        """获取统计信息"""

        return {

            'active_mem_size': self.active_mem.size(),

            'immutable_count': len(self.immutable_mems),

            'levels': {level: len(ssts) for level, ssts in self.sstables.items()},

            'total_files': sum(len(ssts) for ssts in self.sstables.values())

        }





# ==================== 测试代码 ====================

if __name__ == "__main__":

    import shutil

    import random

    

    print("=" * 50)

    print("LSM树测试")

    print("=" * 50)

    

    # 清理旧数据

    test_path = "./test_lsm"

    if os.path.exists(test_path):

        shutil.rmtree(test_path)

    

    # 创建LSM树

    lsm = LSMTree(base_path=test_path, mem_size=4096, level_size=3)

    

    # 测试基本操作

    print("\n--- 基础操作测试 ---")

    

    # 插入

    test_data = [(f"key_{i}".encode(), f"value_{i}".encode()) for i in range(100)]

    for key, value in test_data:

        lsm.put(key, value)

    

    print(f"插入100条记录后统计: {lsm.get_stats()}")

    

    # 搜索

    print("\n搜索测试:")

    for i in [0, 50, 99, 100]:

        key = f"key_{i}".encode()

        result = lsm.get(key)

        print(f"  key_{i}: {result.decode() if result else 'None'}")

    

    # 测试删除

    print("\n删除测试:")

    lsm.delete(b"key_50")

    result = lsm.get(b"key_50")

    print(f"删除key_50后: {result}")

    

    # 大量数据测试

    print("\n--- 大量数据测试 ---")

    

    n_insert = 10000

    start = __import__('time').time()

    

    for i in range(1000, 1000 + n_insert):

        key = f"large_key_{i}".encode()

        value = f"large_value_{i}".encode()

        lsm.put(key, value)

    

    elapsed = __import__('time').time() - start

    print(f"插入 {n_insert} 条记录耗时: {elapsed:.3f}秒")

    print(f"吞吐: {n_insert/elapsed:.0f} ops/s")

    print(f"统计: {lsm.get_stats()}")

    

    # 读取测试

    print("\n--- 读取性能测试 ---")

    

    start = __import__('time').time()

    found = 0

    for i in range(1000, 2000):

        key = f"large_key_{i}".encode()

        if lsm.get(key) is not None:

            found += 1

    elapsed = __import__('time').time() - start

    

    print(f"1000次读取: {elapsed:.3f}秒")

    print(f"找到记录数: {found}")

    

    # 清理

    if os.path.exists(test_path):

        shutil.rmtree(test_path)

