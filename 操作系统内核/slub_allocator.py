# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / slub_allocator

本文件实现 slub_allocator 相关的算法功能。
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass


PAGE_SIZE = 4096


@dataclass
class SlubPage:
    """slub分配的页"""
    pfn: int           # 页帧号
    inuse: int = 0     # 已使用对象数
    objects: int = 0    # 总对象数
    freelist: Optional[int] = None  # 空闲对象链表头

    # 调试信息
    name: str = ""
    s_offset: int = 0  # 对象在slab中的偏移


@dataclass
class KmallocCache:
    """kmalloc缓存"""
    name: str
    object_size: int
    size: int           # 对齐后的大小
    offset: int = 0     # 对象偏移
    objects_per_slab: int = 0
    slabs_partial: int = 0
    slabs_full: int = 0
    slabs_free: int = 0

    # per-CPU缓存
    cpu_slab: Optional[SlubPage] = None


class SlubAllocator:
    """
    slub分配器

    管理小内存分配。
    """

    # kmalloc缓存大小
    KMALLOC_SIZES = [32, 64, 128, 192, 256, 512, 1024, 2048, 4096, 8192]

    def __init__(self):
        self.caches: Dict[str, KmallocCache] = {}
        self.total_memory = 0
        self.allocated = 0

        # 初始化缓存
        self._create_caches()

    def _create_caches(self):
        """创建kmalloc缓存"""
        for size in self.KMALLOC_SIZES:
            cache = KmallocCache(
                name=f"kmalloc-{size}",
                object_size=size,
                size=size,
                objects_per_slab=PAGE_SIZE // size
            )
            self.caches[cache.name] = cache

    def _allocate_slab(self, cache: KmallocCache) -> SlubPage:
        """分配一个新的slab页"""
        page = SlubPage(
            pfn=self.total_memory,
            objects=cache.objects_per_slab,
            inuse=0,
            name=cache.name
        )

        # 初始化freelist（简化：每个对象的下一个是偏移量）
        # 最后一个对象的next是-1（NULL）
        page.freelist = 0
        self.total_memory += 1

        return page

    def kmalloc(self, size: int) -> Optional[int]:
        """分配内存"""
        # 找到合适的缓存
        cache = None
        for c in self.caches.values():
            if c.size >= size:
                cache = c
                break

        if cache is None:
            return None

        # 从per-CPU缓存分配
        if cache.cpu_slab is None:
            # 创建新的slab
            cache.cpu_slab = self._allocate_slab(cache)
            cache.slabs_free += 1

        slab = cache.cpu_slab

        if slab.freelist is None:
            # slab满了
            cache.slabs_full += 1
            cache.slabs_free -= 1
            slab = self._allocate_slab(cache)
            cache.cpu_slab = slab
            cache.slabs_partial -= 1
            cache.slabs_free += 1

        # 分配对象
        obj_offset = slab.freelist
        slab.freelist = obj_offset + cache.size  # 简化：下一个对象偏移
        slab.inuse += 1
        cache.slabs_partial += 1

        # 计算对象地址
        addr = slab.pfn * PAGE_SIZE + obj_offset + cache.offset
        self.allocated += cache.size

        return addr

    def kfree(self, addr: int, size: int):
        """释放内存"""
        self.allocated -= size

    def get_stats(self) -> Dict:
        """获取统计"""
        total_slabs = sum(
            c.slabs_partial + c.slabs_full + c.slabs_free
            for c in self.caches.values()
        )
        return {
            'total_memory': self.total_memory * PAGE_SIZE,
            'allocated': self.allocated,
            'total_slabs': total_slabs,
        }


def simulate_slub():
    """
    模拟slub分配器
    """
    print("=" * 60)
    print("slub分配器详解")
    print("=" * 60)

    allocator = SlubAllocator()

    print("\nkmalloc缓存:")
    print("-" * 50)
    print(f"{'名称':<15} {'对象大小':<10} {'每slab对象数':<12}")
    print("-" * 50)
    for cache in allocator.caches.values():
        print(f"{cache.name:<15} {cache.size:<10} {cache.objects_per_slab:<12}")

    # 分配演示
    print("\n分配演示:")
    print("-" * 50)

    allocations = [
        ("kmalloc-32", 25),
        ("kmalloc-64", 50),
        ("kmalloc-128", 100),
    ]

    for cache_name, size in allocations:
        addr = allocator.kmalloc(size)
        print(f"  kmalloc({size}) -> 0x{addr:08X}" if addr else f"  kmalloc({size}) -> 失败")

    # 统计
    stats = allocator.get_stats()
    print(f"\n分配统计:")
    print(f"  总内存: {stats['total_memory']} bytes")
    print(f"  已分配: {stats['allocated']} bytes")
    print(f"  总slab数: {stats['total_slabs']}")


if __name__ == "__main__":
    simulate_slub()
