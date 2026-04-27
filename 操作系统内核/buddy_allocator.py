# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / buddy_allocator

本文件实现 buddy_allocator 相关的算法功能。
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass


# 页大小（4KB）
PAGE_SIZE = 4096
MAX_ORDER = 10  # 最大阶：2^10 * 4KB = 4MB


@dataclass
class Page:
    """物理页"""
    pfn: int           # Page Frame Number
    order: int = 0     # 所属块的阶
    buddy_pfn: int = 0 # 伙伴的PFN
    free: bool = True  # 是否空闲

    def __repr__(self):
        return f"Page(PFN={self.pfn}, order={self.order}, free={self.free})"


class BuddyAllocator:
    """
    Buddy伙伴分配器

    管理物理页帧的分配和释放。
    """

    def __init__(self, total_pages: int = 1024):
        """
        初始化Buddy分配器
        param total_pages: 总页数
        """
        self.total_pages = total_pages
        self.max_order = MAX_ORDER

        # 自由链表数组：free_lists[order] 是该阶的所有空闲块
        self.free_lists: List[List[int]] = [[] for _ in range(self.max_order + 1)]

        # 页数组：所有物理页
        self.pages: List[Page] = [Page(pfn=i) for i in range(total_pages)]

        # 初始化：将所有页作为一个2^max_order大小的块
        self._init_memory()

    def _init_memory(self):
        """初始化内存，将所有页作为一个连续块"""
        # 从最大的阶开始分配
        # 找到能容纳所有页的最大阶
        total_size = self.total_pages
        order = 0
        while (1 << order) < total_size:
            order += 1
        order = min(order, self.max_order)

        # 从最大阶开始分配
        self._split_block(0, order)

    def _get_buddy_pfn(self, pfn: int, order: int) -> int:
        """
        计算伙伴的PFN
        对于阶为order的块，其伙伴是pfn ^ (1 << order)
        """
        return pfn ^ (1 << order)

    def _is_valid_pfn(self, pfn: int) -> bool:
        """检查PFN是否有效"""
        return 0 <= pfn < self.total_pages

    def _split_block(self, pfn: int, order: int):
        """
        拆分块直到得到阶为0的块
        param pfn: 起始页帧号
        param order: 目标阶
        """
        current_order = self.max_order

        while current_order > order:
            # 找到包含pfn的阶为current_order的块
            # 通过对齐计算
            block_size = 1 << current_order
            block_start = (pfn // block_size) * block_size

            # 拆分成两个阶为current_order-1的块
            mid = block_start + (1 << (current_order - 1))

            # 将前半部分放入对应阶的自由链表
            # 这里简化处理，直接放入目标阶
            current_order -= 1

        # 放入目标阶的自由链表
        if pfn not in self.free_lists[order]:
            self.free_lists[order].append(pfn)

    def alloc_pages(self, order: int = 0) -> Optional[int]:
        """
        分配2^order个连续页
        param order: 阶（0 = 1页, 1 = 2页, 2 = 4页...）
        return: 起始PFN，失败返回None
        """
        if order < 0 or order > self.max_order:
            return None

        # 找最小的满足大小的阶
        for alloc_order in range(order, self.max_order + 1):
            if self.free_lists[alloc_order]:
                pfn = self.free_lists[alloc_order].pop(0)
                # 标记页为已分配
                for i in range(1 << alloc_order):
                    if self._is_valid_pfn(pfn + i):
                        self.pages[pfn + i].free = False
                        self.pages[pfn + i].order = alloc_order

                # 如果分配的阶大于请求的阶，需要拆分
                if alloc_order > order:
                    self._split_remaining(pfn, alloc_order, order)

                return pfn

        return None

    def _split_remaining(self, pfn: int, from_order: int, to_order: int):
        """将大块拆分成需要的阶"""
        current = pfn
        remaining = from_order

        while remaining > to_order:
            remaining -= 1
            buddy = self._get_buddy_pfn(current, remaining)
            # 将伙伴加入自由链表
            if buddy not in self.free_lists[remaining]:
                self.free_lists[remaining].append(buddy)
            self.pages[current].order = remaining

    def free_pages(self, pfn: int, order: int):
        """
        释放2^order个连续页
        param pfn: 起始页帧号
        param order: 阶
        """
        if not self._is_valid_pfn(pfn):
            return

        # 标记为已释放
        for i in range(1 << order):
            if self._is_valid_pfn(pfn + i):
                self.pages[pfn + i].free = True

        # 尝试与伙伴合并
        self._merge(pfn, order)

    def _merge(self, pfn: int, order: int):
        """
        尝试与伙伴合并
        param pfn: 起始页帧号
        param order: 当前阶
        """
        if order >= self.max_order:
            return

        buddy = self._get_buddy_pfn(pfn, order)

        # 检查伙伴是否有效且空闲
        if not self._is_valid_pfn(buddy):
            return

        # 检查伙伴是否在对应阶的自由链表中
        if buddy not in self.free_lists[order]:
            return

        # 可以合并
        self.free_lists[order].remove(buddy)

        # 计算合并后的起始地址
        merged_pfn = min(pfn, buddy)

        # 递归合并更高阶
        self._merge(merged_pfn, order + 1)

        # 加入高一阶的自由链表
        if merged_pfn not in self.free_lists[order + 1]:
            self.free_lists[order + 1].append(merged_pfn)

    def get_free_pages(self, order: int) -> int:
        """获取指定阶的空闲页数"""
        if 0 <= order <= self.max_order:
            count = 0
            for pfn in self.free_lists[order]:
                count += (1 << order)
            return count
        return 0

    def get_total_free_pages(self) -> int:
        """获取总空闲页数"""
        total = 0
        for order in range(self.max_order + 1):
            total += len(self.free_lists[order]) * (1 << order)
        return total

    def print_status(self):
        """打印分配器状态"""
        print(f"\nBuddy分配器状态 (总页数={self.total_pages}):")
        print("-" * 50)
        print(f"{'阶':<6} {'块大小':<12} {'空闲块数':<10} {'空闲页数':<10}")
        print("-" * 50)

        for order in range(self.max_order + 1):
            block_size = (1 << order) * PAGE_SIZE
            free_blocks = len(self.free_lists[order])
            free_pages = free_blocks * (1 << order)

            if free_pages > 0 or order <= 4:  # 显示前几个阶
                size_str = f"{block_size // 1024}KB" if block_size >= 1024 else f"{block_size}B"
                print(f"{order:<6} {size_str:<12} {free_blocks:<10} {free_pages:<10}")

        print("-" * 50)
        print(f"总空闲页数: {self.get_total_free_pages()}")


def simulate_buddy_allocator():
    """
    模拟Buddy伙伴分配器
    """
    print("=" * 60)
    print("Buddy伙伴分配器")
    print("=" * 60)

    # 创建分配器
    buddy = BuddyAllocator(total_pages=64)

    buddy.print_status()

    # 分配测试
    print("\n" + "-" * 50)
    print("分配测试:")
    print("-" * 50)

    # 分配几个不同大小的块
    alloc1 = buddy.alloc_pages(order=0)  # 1页
    print(f"分配 order=0 (4KB): PFN={alloc1}")
    buddy.print_status()

    alloc2 = buddy.alloc_pages(order=2)  # 4页
    print(f"\n分配 order=2 (16KB): PFN={alloc2}")
    buddy.print_status()

    alloc3 = buddy.alloc_pages(order=1)  # 2页
    print(f"\n分配 order=1 (8KB): PFN={alloc3}")
    buddy.print_status()

    # 释放
    print("\n" + "-" * 50)
    print("释放测试:")
    print("-" * 50)

    print(f"释放 PFN={alloc1} (order=0)")
    buddy.free_pages(alloc1, 0)
    buddy.print_status()

    print(f"\n释放 PFN={alloc2} (order=2)")
    buddy.free_pages(alloc2, 2)
    buddy.print_status()

    # 伙伴合并测试
    print("\n" + "-" * 50)
    print("伙伴合并测试:")
    print("-" * 50)

    # 分配两个相邻的order=0块
    a1 = buddy.alloc_pages(order=0)
    a2 = buddy.alloc_pages(order=0)
    print(f"分配两个order=0: PFN={a1}, {a2}")

    print(f"释放 PFN={a1} (触发与PFN={a1^1}合并)")
    buddy.free_pages(a1, 0)
    buddy.print_status()

    print(f"\n释放 PFN={a2} (触发合并成order=1)")
    buddy.free_pages(a2, 0)
    buddy.print_status()


if __name__ == "__main__":
    simulate_buddy_allocator()
