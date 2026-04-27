# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / slab_allocator

本文件实现 slab_allocator 相关的算法功能。
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import random


@dataclass
class SlabPage:
    """Slab页"""
    page_addr: int
    inuse: int = 0      # 已使用对象数
    objects: int = 0    # 总对象数
    free_objects: List[int] = None  # 空闲对象链表

    def __post_init__(self):
        if self.free_objects is None:
            self.free_objects = []


@dataclass
class KmallocCache:
    """kmalloc缓存（通用缓存）"""
    name: str
    object_size: int       # 对象大小
    buffer_size: int        # 实际分配大小（对齐后）
    alignment: int = 8      # 对齐要求

    # 对象统计
    objects_allocated: int = 0
    objects_total: int = 0
    objects_per_slab: int = 0

    # per-CPU缓存
    cpu_caches: Dict[int, List[int]] = None  # per-CPU空闲对象列表

    def __post_init__(self):
        self.cpu_caches = {i: [] for i in range(4)}  # 假设4个CPU


class CacheColoring:
    """
    缓存着色

    通过偏移对象在缓存行中的位置来减少缓存冲突。
    同一缓存中的对象使用不同偏移，避免相互驱逐。
    """

    def __init__(self, cache_size: int, line_size: int = 64):
        self.cache_size = cache_size
        self.line_size = line_size
        self.color_count = cache_size // line_size

    def get_color_offset(self, color: int) -> int:
        """获取颜色对应的偏移"""
        return color * self.line_size

    def get_total_size(self) -> int:
        """获取着色后的总大小"""
        return self.cache_size + self.color_count * self.line_size


class SlabAllocator:
    """
    Slab分配器

    管理特定大小对象的分配。
    """

    # kmalloc缓存预设（各种大小）
    KMALLOC_CACHES = {
        'kmalloc-8': 8,
        'kmalloc-16': 16,
        'kmalloc-32': 32,
        'kmalloc-64': 64,
        'kmalloc-128': 128,
        'kmalloc-256': 256,
        'kmalloc-512': 512,
        'kmalloc-1024': 1024,
    }

    def __init__(self, num_cpus: int = 4):
        self.num_cpus = num_cpus
        self.caches: Dict[str, KmallocCache] = {}
        self.memory: Dict[int, bytes] = {}  # 模拟内存
        self.next_addr = 0x100000

        # 初始化kmalloc缓存
        self._init_caches()

    def _init_caches(self):
        """初始化缓存"""
        for name, size in self.KMALLOC_CACHES.items():
            # 计算对齐后的大小
            aligned_size = self._align_size(size, 8)
            objects_per_slab = 4096 // aligned_size  # 每页能容纳的对象数

            cache = KmallocCache(
                name=name,
                object_size=size,
                buffer_size=aligned_size,
                objects_per_slab=objects_per_slab
            )
            self.caches[name] = cache

    def _align_size(self, size: int, alignment: int) -> int:
        """对齐大小"""
        return ((size + alignment - 1) // alignment) * alignment

    def _alloc_from_memory(self, size: int) -> int:
        """从模拟内存分配"""
        addr = self.next_addr
        self.next_addr += size
        return addr

    def kmalloc(self, size: int) -> Optional[int]:
        """
        分配内存
        param size: 请求的大小
        return: 分配地址
        """
        # 找到合适的缓存
        cache_name = None
        for name, cached_size in self.KMALLOC_CACHES.items():
            if cached_size >= size:
                cache_name = name
                break

        if cache_name is None:
            # 太大，直接分配
            return self._alloc_from_memory(size)

        cache = self.caches[cache_name]

        # 尝试从per-CPU缓存分配
        cpu_id = 0  # 简化：使用CPU 0
        if cache.cpu_caches[cpu_id]:
            obj_addr = cache.cpu_caches[cpu_id].pop()
            cache.objects_allocated += 1
            return obj_addr

        # per-CPU缓存为空，分配新的slab
        slab_size = 4096  # 一个页
        slab_addr = self._alloc_from_memory(slab_size + cache.buffer_size * cache.objects_per_slab)

        # 分割成对象
        for i in range(cache.objects_per_slab):
            obj_addr = slab_addr + i * cache.buffer_size
            # 第一个对象给当前请求
            if i == 0:
                cache.objects_allocated += 1
                return obj_addr
            else:
                # 其他对象放入per-CPU缓存
                cache.cpu_caches[cpu_id].append(obj_addr)

        return None

    def kfree(self, addr: int, size: int):
        """释放内存"""
        # 简化：直接回收
        pass

    def get_cache_stats(self, cache_name: str) -> Dict:
        """获取缓存统计"""
        if cache_name not in self.caches:
            return {}

        cache = self.caches[cache_name]
        total_objects = len(cache.cpu_caches[0]) + cache.objects_allocated

        return {
            'name': cache.name,
            'object_size': cache.object_size,
            'buffer_size': cache.buffer_size,
            'objects_allocated': cache.objects_allocated,
            'per_cpu_free': sum(len(v) for v in cache.cpu_caches.values()),
            'total': total_objects + cache.objects_allocated,
        }


class SlubAllocator:
    """
    Slub分配器（简化版）

    Slub是Linux 2.6.23之后使用的分配器，比Slab更简单。
    """

    def __init__(self):
        # 页面管理
        self.pages: Dict[int, SlabPage] = {}

        # 分配统计
        self.total_allocated = 0
        self.total_free = 0

    def allocate(self, size: int) -> Optional[int]:
        """分配对象"""
        # 简化：直接分配
        addr = self.total_allocated * 64 + 0x1000
        self.total_allocated += 1
        return addr

    def free(self, addr: int):
        """释放对象"""
        self.total_free += 1


def simulate_slab_allocator():
    """
    模拟Slab/Slub分配器
    """
    print("=" * 60)
    print("Slab/Slub分配器")
    print("=" * 60)

    allocator = SlabAllocator(num_cpus=4)

    # 缓存着色演示
    print("\n缓存着色 (Cache Coloring) 演示:")
    print("-" * 50)

    coloring = CacheColoring(cache_size=256, line_size=64)
    print(f"缓存大小: 256 bytes")
    print(f"缓存行大小: 64 bytes")
    print(f"颜色数量: {coloring.color_count}")
    print(f"着色后总大小: {coloring.get_total_size()} bytes")

    print("\n颜色偏移表:")
    for color in range(min(coloring.color_count, 4)):
        offset = coloring.get_color_offset(color)
        print(f"  颜色{color}: 偏移={offset} bytes")

    # kmalloc演示
    print("\n" + "-" * 50)
    print("kmalloc缓存演示:")
    print("-" * 50)

    print("\n可用缓存:")
    for name, size in allocator.KMALLOC_CACHES.items():
        cache = allocator.caches.get(name)
        if cache:
            print(f"  {name}: 对象大小={cache.object_size}, "
                  f"buffer_size={cache.buffer_size}, "
                  f"每slab对象数={cache.objects_per_slab}")

    print("\n分配测试:")
    print("-" * 50)

    # 分配各种大小的对象
    sizes = [8, 16, 32, 64, 128, 256, 500, 1024]

    for size in sizes:
        addr = allocator.kmalloc(size)
        print(f"  分配 {size} bytes -> 地址 0x{addr:08X}" if addr else f"  分配 {size} bytes -> 失败")

    # per-CPU缓存演示
    print("\nper-CPU缓存状态:")
    print("-" * 50)

    for name, cache in allocator.caches.items():
        if cache.objects_allocated > 0:
            print(f"\n{name}:")
            for cpu_id, free_list in cache.cpu_caches.items():
                if free_list:
                    print(f"  CPU{cpu_id}: {len(free_list)} 个空闲对象")

    # Slub演示
    print("\n" + "=" * 60)
    print("Slub分配器")
    print("=" * 60)

    slub = SlubAllocator()

    print("\n分配/释放模拟:")
    print("-" * 50)

    addrs = []
    for i in range(5):
        addr = slub.allocate(64)
        addrs.append(addr)
        print(f"  allocate() -> 0x{addr:08X}")

    print(f"\n总分配: {slub.total_allocated}")

    for addr in addrs:
        slub.free(addr)
        print(f"  free(0x{addr:08X})")

    print(f"总释放: {slub.total_free}")


if __name__ == "__main__":
    simulate_slab_allocator()
