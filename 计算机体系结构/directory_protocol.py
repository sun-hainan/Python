# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构 / directory_protocol

本文件实现 directory_protocol 相关的算法功能。
"""

from typing import Dict, List, Set, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field


class DirectoryState(Enum):
    """目录协议状态"""
    UNCACHED = "U"      # 没有缓存持有此块
    SHARED = "S"        # 一个或多个缓存共享此块
    EXCLUSIVE = "E"     # 只有一个缓存独占此块


@dataclass
class DirectoryEntry:
    """目录条目"""
    state: DirectoryState
    owner: Optional[int] = None  # 独占所有者（缓存ID）
    sharers: Set[int] = field(default_factory=set)  # 共享者集合


class DirectoryController:
    """
    目录控制器

    维护每个内存块的目录信息。
    在真实系统中，目录通常位于内存控制器中或独立模块。
    """

    def __init__(self, memory_size: int, block_size: int = 64):
        self.block_size = block_size
        self.num_blocks = memory_size // block_size
        # 目录表
        self.directory: Dict[int, DirectoryEntry] = {}
        # 初始化所有块为Uncached
        for i in range(self.num_blocks):
            self.directory[i] = DirectoryEntry(state=DirectoryState.UNCACHED)

    def _get_block_index(self, address: int) -> int:
        """获取块索引"""
        return address // self.block_size

    def get_entry(self, address: int) -> DirectoryEntry:
        """获取目录条目"""
        index = self._get_block_index(address)
        return self.directory[index]

    def set_shared(self, address: int, sharers: Set[int]):
        """设置块为共享状态"""
        index = self._get_block_index(address)
        self.directory[index].state = DirectoryState.SHARED
        self.directory[index].sharers = sharers.copy()
        self.directory[index].owner = None

    def set_exclusive(self, address: int, owner: int):
        """设置块为独占状态"""
        index = self._get_block_index(address)
        self.directory[index].state = DirectoryState.EXCLUSIVE
        self.directory[index].owner = owner
        self.directory[index].sharers.clear()

    def set_uncached(self, address: int):
        """设置块为未缓存状态"""
        index = self._get_block_index(address)
        self.directory[index].state = DirectoryState.UNCACHED
        self.directory[index].owner = None
        self.directory[index].sharers.clear()

    def add_sharer(self, address: int, cache_id: int):
        """添加共享者"""
        index = self._get_block_index(address)
        entry = self.directory[index]
        entry.sharers.add(cache_id)
        if entry.state == DirectoryState.EXCLUSIVE and entry.owner == cache_id:
            return  # 已在独占状态
        entry.state = DirectoryState.SHARED

    def remove_sharer(self, address: int, cache_id: int):
        """移除共享者"""
        index = self._get_block_index(address)
        entry = self.directory[index]
        entry.sharers.discard(cache_id)
        if not entry.sharers and entry.state == DirectoryState.SHARED:
            entry.state = DirectoryState.UNCACHED

    def to_string(self, address: int) -> str:
        """获取状态字符串"""
        entry = self.get_entry(address)
        if entry.state == DirectoryState.UNCACHED:
            return "Uncached"
        elif entry.state == DirectoryState.EXCLUSIVE:
            return f"Exclusive (Owner=C{entry.owner})"
        else:
            return f"Shared (Sharers={entry.sharers})"


class Message:
    """协议消息"""
    def __init__(self, msg_type: str, address: int, src: int, dst: int = -1):
        self.type = msg_type
        self.address = address
        self.src = src
        self.dst = dst


class CacheWithDirectory:
    """支持目录协议的缓存"""

    def __init__(self, cache_id: int, cache_size: int, block_size: int = 64):
        self.cache_id = cache_id
        self.block_size = block_size
        self.num_lines = cache_size // block_size
        # 缓存行状态：{index: state}
        self.lines: Dict[int, str] = {}
        # 缓存行数据：{index: data}
        self.data: Dict[int, bytes] = {}

    def _get_index(self, address: int) -> int:
        return (address // self.block_size) % self.num_lines

    def has_line(self, address: int) -> bool:
        """检查是否有所需行"""
        index = self._get_index(address)
        return index in self.lines

    def get_state(self, address: int) -> Optional[str]:
        """获取行状态"""
        index = self._get_index(address)
        return self.lines.get(index)


class DirectoryProtocol:
    """
    基于目录的缓存一致性协议

    工作流程：
    1. 读未命中：向目录发送请求，目录查找所有者或共享者
    2. 写未命中：向目录请求独占权，目录发送失效到所有共享者
    3. 写命中：如果不是独占，需要先获取独占权
    """

    def __init__(self, num_caches: int, memory_size: int, block_size: int = 64):
        self.num_caches = num_caches
        self.block_size = block_size
        self.memory_size = memory_size

        # 目录控制器
        self.directory = DirectoryController(memory_size, block_size)

        # 各缓存的目录视图（跟踪自己持有的块）
        self.caches: List[CacheWithDirectory] = []
        for i in range(num_caches):
            self.caches.append(CacheWithDirectory(i, cache_size=1024, block_size=block_size))

        # 模拟内存
        self.memory: Dict[int, bytes] = {}

        # 事件日志
        self.events: List[str] = []

    def log(self, msg: str):
        """记录事件"""
        self.events.append(msg)

    def handle_read_miss(self, cache_id: int, address: int):
        """
        处理读未命中
        """
        cache = self.caches[cache_id]
        index = cache._get_index(address)

        dir_entry = self.directory.get_entry(address)

        if dir_entry.state == DirectoryState.UNCACHED:
            # 内存中没有有效副本，需要从内存读取
            self.log(f"C{cache_id}: ReadMiss @ 0x{address:X} - 从内存获取")
            # 更新目录
            self.directory.set_shared(address, {cache_id})
            cache.lines[index] = "S"
            cache.data[index] = self.memory.get(address, b"\x00" * self.block_size)

        elif dir_entry.state == DirectoryState.EXCLUSIVE:
            # 另一个缓存独占，需要获取共享副本
            owner = dir_entry.owner
            self.log(f"C{cache_id}: ReadMiss @ 0x{address:X} - 从C{owner}获取 (Exclusive->Shared)")
            # 所有者降级为Shared
            owner_cache = self.caches[owner]
            owner_index = owner_cache._get_index(address)
            owner_cache.lines[owner_index] = "S"

            # 更新目录
            dir_entry.sharers.add(owner)
            dir_entry.sharers.add(cache_id)
            dir_entry.state = DirectoryState.SHARED
            dir_entry.owner = None

            # 当前缓存获得数据
            cache.lines[index] = "S"
            cache.data[index] = owner_cache.data.get(owner_index, b"\x00" * self.block_size)

        elif dir_entry.state == DirectoryState.SHARED:
            # 已经是共享状态，只需添加到共享者列表
            self.log(f"C{cache_id}: ReadMiss @ 0x{address:X} - 从Shared获取")
            self.directory.add_sharer(address, cache_id)
            cache.lines[index] = "S"
            # 从任意共享者获取数据（简化：从第一个）
            for sharer_id in dir_entry.sharers:
                if sharer_id != cache_id:
                    sharer_data = self.caches[sharer_id].data.get(index)
                    if sharer_data:
                        cache.data[index] = sharer_data
                        break

    def handle_write_miss(self, cache_id: int, address: int):
        """
        处理写未命中
        """
        cache = self.caches[cache_id]
        index = cache._get_index(address)

        dir_entry = self.directory.get_entry(address)

        if dir_entry.state == DirectoryState.UNCACHED:
            # 直接获取独占权
            self.log(f"C{cache_id}: WriteMiss @ 0x{address:X} - 获取独占权 (Uncached->Exclusive)")
            self.directory.set_exclusive(address, cache_id)
            cache.lines[index] = "M"
            cache.data[index] = self.memory.get(address, b"\x00" * self.block_size)

        elif dir_entry.state == DirectoryState.EXCLUSIVE:
            # 另一个缓存独占，需要先获取数据
            owner = dir_entry.owner
            self.log(f"C{cache_id}: WriteMiss @ 0x{address:X} - 从C{owner}获取 (Exclusive转移)")
            # 旧所有者失效
            old_owner_cache = self.caches[owner]
            old_index = old_owner_cache._get_index(address)
            old_owner_cache.lines[old_index] = None

            # 更新目录
            self.directory.set_exclusive(address, cache_id)
            cache.lines[index] = "M"
            cache.data[index] = old_owner_cache.data.get(old_index, b"\x00" * self.block_size)

        elif dir_entry.state == DirectoryState.SHARED:
            # 需要先Invalidate所有共享者
            self.log(f"C{cache_id}: WriteMiss @ 0x{address:X} - Invalidate所有共享者")
            for sharer_id in list(dir_entry.sharers):
                if sharer_id != cache_id:
                    sharer_cache = self.caches[sharer_id]
                    sharer_index = sharer_cache._get_index(address)
                    sharer_cache.lines[sharer_index] = None

            # 更新目录
            self.directory.set_exclusive(address, cache_id)
            cache.lines[index] = "M"
            cache.data[index] = self.memory.get(address, b"\x00" * self.block_size)

    def handle_write_hit(self, cache_id: int, address: int):
        """
        处理写命中
        """
        cache = self.caches[cache_id]
        index = cache._get_index(address)
        state = cache.get_state(address)

        if state == "M":
            # 已经是Modified，直接写
            self.log(f"C{cache_id}: WriteHit @ 0x{address:X} - 已是Modified")
        elif state == "E":
            # 独占但未修改 -> Modified
            self.log(f"C{cache_id}: WriteHit @ 0x{address:X} - Exclusive->Modified")
            cache.lines[index] = "M"
        elif state == "S":
            # Shared，需要Invalidate其他缓存
            self.log(f"C{cache_id}: WriteHit @ 0x{address:X} - Shared->Modified (Invalidate)")
            dir_entry = self.directory.get_entry(address)
            for sharer_id in list(dir_entry.sharers):
                if sharer_id != cache_id:
                    sharer_cache = self.caches[sharer_id]
                    sharer_index = sharer_cache._get_index(address)
                    sharer_cache.lines[sharer_index] = None

            # 更新目录
            self.directory.set_exclusive(address, cache_id)
            cache.lines[index] = "M"

    def get_cache_states(self, address: int) -> Dict[int, str]:
        """获取所有缓存中某地址的状态"""
        result = {}
        for i, cache in enumerate(self.caches):
            state = cache.get_state(address)
            if state:
                result[i] = state
        return result

    def print_directory_state(self, address: int):
        """打印目录状态"""
        print(f"  目录: {self.directory.to_string(address)}")
        cache_states = self.get_cache_states(address)
        for cid, state in cache_states.items():
            print(f"  C{cid}: {state}")


def simulate_directory_protocol():
    """
    模拟目录协议
    """
    print("=" * 60)
    print("目录协议 (Directory Protocol) 模拟")
    print("=" * 60)

    # 创建2核系统，内存大小4KB
    protocol = DirectoryProtocol(num_caches=2, memory_size=4096, block_size=64)

    address = 0x100

    print(f"\n初始状态 (地址 0x{address:X}):")
    protocol.print_directory_state(address)

    print("\n" + "-" * 50)
    print("场景1: CPU0 读地址 0x{address:X}".format(address=address))
    protocol.handle_read_miss(0, address)
    protocol.print_directory_state(address)

    print("\n场景2: CPU1 读相同地址")
    protocol.handle_read_miss(1, address)
    protocol.print_directory_state(address)

    print("\n场景3: CPU0 写地址 0x{address:X}".format(address=address))
    protocol.handle_write_hit(0, address)
    protocol.print_directory_state(address)

    print("\n场景4: CPU1 尝试写相同地址 (Write Miss)")
    protocol.handle_write_miss(1, address)
    protocol.print_directory_state(address)

    print("\n场景5: CPU1 再次读取")
    protocol.handle_read_miss(1, address)
    protocol.print_directory_state(address)

    print("\n" + "-" * 50)
    print("协议事件日志:")
    for event in protocol.events:
        print(f"  {event}")


if __name__ == "__main__":
    simulate_directory_protocol()
