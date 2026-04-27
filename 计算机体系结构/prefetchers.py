# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构 / prefetchers

本文件实现 prefetchers 相关的算法功能。
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MemoryAccess:
    """内存访问记录"""
    address: int
    is_load: bool
    instruction_id: int = 0


class StreamPrefetcher:
    """
    流预取器

    检测地址流（连续访问模式），并预取流中后续的数据。
    使用有限状态机(FSM)跟踪每个流的检测状态。

    状态:
    - NONE: 未检测到流
    - STRONG_FORWARD: 强正向流（连续多次正向访问）
    - STRONG_BACKWARD: 强反向流（连续多次反向访问）
    - WEAK_FORWARD: 弱正向流
    - WEAK_BACKWARD: 弱反向流
    """

    # 流检测状态
    STATE_NONE = 0
    STATE_WEAK_FORWARD = 1
    STATE_STRONG_FORWARD = 2
    STATE_WEAK_BACKWARD = 3
    STATE_STRONG_BACKWARD = 4

    def __init__(self, cache_line_size: int = 64, stream_buffer_entries: int = 4):
        self.cache_line_size = cache_line_size
        self.buffer_entries = stream_buffer_entries

        # 流缓冲区：{stream_id: (base_addr, direction, confidence)}
        self.stream_buffers: List[Optional[Tuple[int, int, int]]] = [None] * stream_buffer_entries

        # 预取统计
        self.total_prefetches = 0
        self.useful_prefetches = 0

    def _get_cache_line_addr(self, address: int) -> int:
        """获取缓存行对齐地址"""
        return (address // self.cache_line_size) * self.cache_line_size

    def _find_stream(self, address: int) -> Optional[int]:
        """查找匹配的流缓冲区"""
        line_addr = self._get_cache_line_addr(address)
        for i, entry in enumerate(self.stream_buffers):
            if entry and entry[0] == line_addr:
                return i
        return None

    def _find_free_stream(self) -> Optional[int]:
        """找到空闲流缓冲区"""
        for i, entry in enumerate(self.stream_buffers):
            if entry is None:
                return i
        return None

    def _update_stream(self, stream_id: int, address: int, forward: bool):
        """更新流状态"""
        base_addr, direction, confidence = self.stream_buffers[stream_id]

        if forward:
            new_direction = 1
        else:
            new_direction = -1

        if direction == new_direction:
            # 方向一致，增加置信度
            confidence = min(2, confidence + 1)
        else:
            # 方向改变，降低置信度
            confidence = max(0, confidence - 1)

        # 更新基地址
        new_base = self._get_cache_line_addr(address)
        self.stream_buffers[stream_id] = (new_base, new_direction, confidence)

    def _get_prefetch_addresses(self, stream_id: int) -> List[int]:
        """获取需要预取的地址列表"""
        entry = self.stream_buffers[stream_id]
        if entry is None:
            return []

        base_addr, direction, confidence = entry
        prefetch_addrs = []

        # 根据置信度决定预取距离
        prefetch_distance = confidence + 1

        for i in range(1, prefetch_distance + 1):
            prefetch_addr = base_addr + direction * i * self.cache_line_size
            prefetch_addrs.append(prefetch_addr)

        return prefetch_addrs

    def on_memory_access(self, address: int, is_load: bool = True) -> List[int]:
        """
        记录内存访问并触发预取
        param address: 访问地址
        param is_load: 是否为加载操作
        return: 预取的地址列表
        """
        if not is_load:
            return []

        line_addr = self._get_cache_line_addr(address)
        prefetched = []

        # 检查是否匹配现有流
        stream_id = self._find_stream(line_addr)

        if stream_id is not None:
            # 匹配现有流，更新状态
            self._update_stream(stream_id, address, line_addr >= self.stream_buffers[stream_id][0])
        else:
            # 创建新流
            stream_id = self._find_free_stream()
            if stream_id is not None:
                self.stream_buffers[stream_id] = (line_addr, 0, 0)

        # 如果是STRONG状态，生成预取
        for i, entry in enumerate(self.stream_buffers):
            if entry and entry[2] >= 1:  # 置信度 >= 1
                prefetch_addrs = self._get_prefetch_addresses(i)
                for addr in prefetch_addrs:
                    prefetched.append(addr)
                    self.total_prefetches += 1

        return prefetched


class StridePrefetcher:
    """
    跨步预取器

    为每条 Load 指令维护一个历史记录，检测固定跨步模式。

    跟踪表条目:
    - last_address: 上一次访问地址
    - stride: 检测到的跨步
    - confidence: 置信度
    - state: 条目状态 (无效/有效/待预取)
    """

    # 条目状态
    STATE_INVALID = 0
    STATE_VALID = 1
    STATE_READY = 2

    def __init__(self, num_entries: int = 16, cache_line_size: int = 64):
        self.num_entries = num_entries
        self.cache_line_size = cache_line_size
        self.table_size = num_entries

        # 跨步表：{instruction_id: (last_addr, stride, confidence, state)}
        self.stride_table: Dict[int, Tuple[int, int, int, int]] = {}

        # 预取统计
        self.total_prefetches = 0
        self.useful_prefetches = 0

    def _get_cache_line_addr(self, address: int) -> int:
        return (address // self.cache_line_size) * self.cache_line_size

    def on_memory_access(self, address: int, instruction_id: int) -> List[int]:
        """
        记录内存访问并可能触发预取
        param address: 访问地址
        param instruction_id: 指令标识
        return: 预取地址列表
        """
        line_addr = self._get_cache_line_addr(address)
        prefetched = []

        if instruction_id in self.stride_table:
            last_addr, stride, confidence, state = self.stride_table[instruction_id]

            if state == self.STATE_VALID:
                # 计算新的跨步
                new_stride = line_addr - last_addr

                if new_stride == stride and stride != 0:
                    # 跨步一致，增加置信度
                    confidence = min(3, confidence + 1)
                    if confidence >= 2:
                        # 置信度足够，进入READY状态
                        state = self.STATE_READY
                else:
                    # 跨步改变或首次，重置
                    stride = new_stride
                    confidence = 1
                    state = self.STATE_VALID

                # 更新表项
                self.stride_table[instruction_id] = (line_addr, stride, confidence, state)

                # 如果是READY状态，生成预取
                if state == self.STATE_READY and stride != 0:
                    prefetch_addr = line_addr + stride
                    prefetched.append(prefetch_addr)
                    self.total_prefetches += 1
            elif state == self.STATE_READY:
                # 继续使用相同跨步
                if line_addr - last_addr == stride:
                    prefetch_addr = line_addr + stride
                    prefetched.append(prefetch_addr)
                    self.total_prefetches += 1

                self.stride_table[instruction_id] = (line_addr, stride, confidence, state)
        else:
            # 新条目
            self.stride_table[instruction_id] = (line_addr, 0, 0, self.STATE_VALID)

        return prefetched


class TaggedPrefetcher:
    """
    Tagged Prefetcher（标记预取器）

    使用时间标记来识别 reuse distance 模式。
    当检测到多次访问之间的间距相同时，触发预取。

    工作原理：
    - 为每个缓存块维护一个"标记"（访问计数器）
    - 当块被再次访问时，计算两次访问的间距
    - 如果间距一致，预测下次访问
    """

    def __init__(self, num_entries: int = 64, cache_line_size: int = 64):
        self.num_entries = num_entries
        self.cache_line_size = cache_line_size

        # 标签表：{cache_line_addr: (last_access_time, stride, confidence)}
        self.tag_table: Dict[int, Tuple[int, int, int]] = {}

        # 全局访问计数器
        self.global_counter = 0

        # 统计
        self.total_prefetches = 0

    def _get_cache_line_addr(self, address: int) -> int:
        return (address // self.cache_line_size) * self.cache_line_size

    def on_memory_access(self, address: int) -> List[int]:
        """
        记录访问并可能预取
        return: 预取地址列表
        """
        line_addr = self._get_cache_line_addr(address)
        self.global_counter += 1
        prefetched = []

        if line_addr in self.tag_table:
            last_time, stride, confidence = self.tag_table[line_addr]

            # 计算reuse distance
            reuse_distance = self.global_counter - last_time

            if stride == 0:
                # 首次，重置
                stride = reuse_distance
                confidence = 1
            elif reuse_distance == stride:
                # 一致，增加置信度
                confidence = min(3, confidence + 1)
            else:
                # 不一致，重置
                stride = reuse_distance
                confidence = 1

            # 如果置信度足够，生成预取
            if confidence >= 2:
                prefetch_addr = line_addr + self.cache_line_size
                prefetched.append(prefetch_addr)
                self.total_prefetches += 1

            self.tag_table[line_addr] = (self.global_counter, stride, confidence)
        else:
            # 新条目
            self.tag_table[line_addr] = (self.global_counter, 0, 1)

        return prefetched


def simulate_prefetchers():
    """
    模拟各种预取器
    """
    print("=" * 60)
    print("预取器模拟")
    print("=" * 60)

    # ============ 流预取器模拟 ============
    print("\n" + "=" * 40)
    print("流预取器 (Stream Prefetcher) 模拟")
    print("=" * 40)

    stream = StreamPrefetcher(cache_line_size=64, stream_buffer_entries=4)

    # 模拟流式访问
    access_stream = [0x1000, 0x1040, 0x1080, 0x10C0, 0x1100]

    print("\n正向流访问:")
    for addr in access_stream:
        prefetch = stream.on_memory_access(addr, is_load=True)
        print(f"  访问 0x{addr:04X}", end="")
        if prefetch:
            print(f" -> 预取 0x{prefetch[0]:04X}", end="")
        print()

    print(f"\n流缓冲区状态:")
    for i, entry in enumerate(stream.stream_buffers):
        if entry:
            print(f"  Stream[{i}]: base=0x{entry[0]:04X}, dir={entry[1]}, conf={entry[2]}")

    # ============ 跨步预取器模拟 ============
    print("\n" + "=" * 40)
    print("跨步预取器 (Stride Prefetcher) 模拟")
    print("=" * 40)

    stride = StridePrefetcher(num_entries=16, cache_line_size=64)

    # 模拟固定跨步访问（跨步=3个缓存行，即192字节）
    stride_value = 192
    base = 0x2000

    print("\n固定跨步访问 (stride=192字节):")
    accesses = [base + i * stride_value for i in range(6)]

    for i, addr in enumerate(accesses):
        instr_id = 1  # 同一指令
        prefetch = stride.on_memory_access(addr, instr_id)
        print(f"  访问 0x{addr:04X}", end="")
        if prefetch:
            print(f" -> 预取 0x{prefetch[0]:04X}", end="")
        print()

    print(f"\n跨步表:")
    for iid, entry in stride.stride_table.items():
        print(f"  Instr{iid}: last=0x{entry[0]:04X}, stride={entry[1]}, conf={entry[2]}, state={entry[3]}")

    # ============ Tagged预取器模拟 ============
    print("\n" + "=" * 40)
    print("Tagged Prefetcher 模拟")
    print("=" * 40)

    tagged = TaggedPrefetcher(num_entries=64, cache_line_size=64)

    # 模拟固定reuse distance
    print("\n固定reuse distance访问:")
    addr = 0x3000
    for i in range(5):
        prefetch = tagged.on_memory_access(addr)
        print(f"  访问 0x{addr:04X} (time={tagged.global_counter})", end="")
        if prefetch:
            print(f" -> 预取 0x{prefetch[0]:04X}", end="")
        print()
        addr += 192  # 模拟非连续但有固定间距的访问


if __name__ == "__main__":
    simulate_prefetchers()
