# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / buddy_allocator

本文件实现 buddy_allocator 相关的算法功能。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MemoryBlock:
    """内存块描述"""
    order: int              # 阶（0=4KB, 1=8KB, 2=16KB...）
    base_addr: int          # 起始地址
    size: int               # 大小=2^order * PAGE_SIZE
    is_free: bool = True
    next: Optional["MemoryBlock"] = None


class BuddyAllocator:
    """
    Buddy伙伴分配器
    初始化：2^MAX_ORDER个连续页框
    分配：找到最小满足的阶，递归分裂
    释放：尝试合并伙伴（地址/2原则）
    """

    PAGE_SIZE = 4096  # 4KB页大小
    MAX_ORDER = 10   # 最大阶（4KB * 2^10 = 4MB）

    def __init__(self, total_pages: int = 1024):
        self.total_pages = total_pages
        self.total_size = total_pages * self.PAGE_SIZE

        # 每阶的空闲链表
        self.free_lists: list[list[MemoryBlock]] = [[] for _ in range(self.MAX_ORDER + 1)]

        # 初始：一大块（最大阶）
        initial_order = self._find_max_order(total_pages)
        initial_block = MemoryBlock(
            order=initial_order,
            base_addr=0,
            size=initial_order * self.PAGE_SIZE
        )
        self.free_lists[initial_order].append(initial_block)

    def _find_max_order(self, pages: int) -> int:
        """找到能容纳pages的最小阶"""
        size_needed = pages * self.PAGE_SIZE
        order = 0
        while (1 << order) * self.PAGE_SIZE < size_needed:
            order += 1
        return min(order, self.MAX_ORDER)

    def _split_block(self, block: MemoryBlock) -> tuple[MemoryBlock, MemoryBlock]:
        """
        分裂内存块为两个伙伴
        左伙伴：base_addr不变
        右伙伴：base_addr + new_size
        """
        new_order = block.order - 1
        new_size = (1 << new_order) * self.PAGE_SIZE

        left = MemoryBlock(order=new_order, base_addr=block.base_addr, size=new_size)
        right = MemoryBlock(order=new_order, base_addr=block.base_addr + new_size, size=new_size)

        return left, right

    def _is_buddy(self, block1: MemoryBlock, block2: MemoryBlock) -> bool:
        """判断两个块是否是伙伴（同一阶且地址符合伙伴关系）"""
        if block1.order != block2.order:
            return False
        # 伙伴关系：地址低位mask后相加为0，或地址差等于块大小
        combined_addr = block1.base_addr ^ block2.base_addr
        size_sum = block1.size + block2.size
        return combined_addr == size_sum

    def allocate(self, size_bytes: int) -> Optional[int]:
        """
        分配内存
        返回起始地址，失败返回None
        """
        # 找到最小满足的阶
        pages_needed = (size_bytes + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        required_order = 0
        while (1 << required_order) < pages_needed:
            required_order += 1

        if required_order > self.MAX_ORDER:
            return None

        # 搜索空闲链表
        for order in range(required_order, self.MAX_ORDER + 1):
            if self.free_lists[order]:
                block = self.free_lists[order].pop(0)
                break
        else:
            return None  # 无可用内存

        # 递归分裂到所需阶
        while block.order > required_order:
            left, right = self._split_block(block)
            # 将右半部分放回对应阶的空闲链表
            self.free_lists[right.order].append(right)
            block = left  # 使用左半部分继续分裂

        block.is_free = False
        return block.base_addr

    def free(self, addr: int, size_bytes: int) -> bool:
        """
        释放内存
        尝试合并伙伴块
        """
        pages_freed = (size_bytes + self.PAGE_SIZE - 1) // self.PAGE_SIZE
        order = 0
        while (1 << order) < pages_freed:
            order += 1

        block = MemoryBlock(order=order, base_addr=addr, size=pages_freed * self.PAGE_SIZE)
        self.free_lists[order].append(block)

        # 尝试合并
        self._coalesce(order)

        return True

    def _coalesce(self, order: int):
        """合并相邻的伙伴块"""
        if order >= self.MAX_ORDER:
            return

        freelist = self.free_lists[order]
        merged = []
        i = 0

        while i < len(freelist):
            block1 = freelist[i]
            j = i + 1
            while j < len(freelist):
                block2 = freelist[j]
                if self._is_buddy(block1, block2):
                    # 合并：地址较小的为新块基址
                    new_addr = min(block1.base_addr, block2.base_addr)
                    new_block = MemoryBlock(
                        order=order + 1,
                        base_addr=new_addr,
                        size=block1.size * 2
                    )
                    merged.append((i, j, new_block))
                    break
                j += 1
            i += 1

        # 处理合并结果（简化版）
        for i, j, new_block in merged:
            # 从链表中移除这两个块
            self.free_lists[order] = [b for idx, b in enumerate(freelist) if idx not in (i, j)]
            # 添加合并后的块到高阶链表
            self.free_lists[new_block.order].append(new_block)
            # 递归尝试继续合并
            self._coalesce(order + 1)

    def get_free_pages(self) -> int:
        """统计空闲页数"""
        total = 0
        for order in range(self.MAX_ORDER + 1):
            total += len(self.free_lists[order]) * (1 << order)
        return total

    def print_state(self):
        """打印分配器状态"""
        print(f"Buddy Allocator: Total={self.total_pages} pages ({self.total_size / 1024:.0f} KB)")
        for order in range(self.MAX_ORDER + 1):
            count = len(self.free_lists[order])
            if count > 0:
                size = (1 << order) * self.PAGE_SIZE
                print(f"  Order {order}: {count} blocks × {size} bytes = {count * size} bytes")


if __name__ == "__main__":
    buddy = BuddyAllocator(total_pages=64)

    print("=== 初始状态 ===")
    buddy.print_state()

    # 分配测试
    print("\n=== 分配请求 ===")
    allocations = []
    for size in [4096, 8192, 16384, 4096, 8192]:
        addr = buddy.allocate(size)
        allocations.append((addr, size))
        print(f"分配 {size} bytes: {'成功 @ ' + str(addr) if addr else '失败'}")

    print(f"\n空闲页剩余: {buddy.get_free_pages()}")
    buddy.print_state()

    print("\n=== 释放测试 ===")
    # 释放部分内存
    for addr, size in allocations[:2]:
        buddy.free(addr, size)
        print(f"释放 {size} bytes @ {addr}")

    buddy.print_state()
    print(f"空闲页: {buddy.get_free_pages()}")

    # 碎片测试
    print("\n=== 碎片模拟 ===")
    buddy2 = BuddyAllocator(total_pages=32)
    addrs = []
    for i in range(8):
        a = buddy2.allocate(4096)
        addrs.append(a)
    buddy2.print_state()

    # 释放奇数块
    for i in range(0, 8, 2):
        buddy2.free(addrs[i], 4096)
    buddy2.print_state()

    # 尝试分配大块
    large_addr = buddy2.allocate(16384)
    print(f"分配16KB: {'成功 @ ' + str(large_addr) if large_addr else '失败'}")
