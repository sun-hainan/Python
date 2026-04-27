# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / huge_pages

本文件实现 huge_pages 相关的算法功能。
"""

from dataclasses import dataclass
from typing import Optional


class HugePageSize(Enum):
    """大页尺寸（HugePageSize枚举实际上不存在，这是演示）"""
    # 实际上Linux定义：2MB、1GB
    HUGETLB_2MB = 2 * 1024 * 1024
    HUGETLB_1GB = 1024 * 1024 * 1024


@dataclass
class HugePageRegion:
    """大页内存区域"""
    page_size: int           # 页大小（2MB或1GB）
    base_addr: int           # 起始物理地址
    num_pages: int           # 页数量
    free_pages: int          # 空闲页数
    allocated_to: list[int] = None  # 分配的进程PID列表

    def __post_init__(self):
        self.allocated_to = self.allocated_to or []


@dataclass
class HugePageStats:
    """大页统计"""
    total_pages: int
    free_pages: int
    page_size: int
    alloc_hits: int = 0
    alloc_misses: int = 0


class HugePagesManager:
    """
    大页内存管理器
    功能：
    1. 预分配大页池
    2. 为进程分配大页
    3. 透明大页（THP）支持
    """

    # 标准大页尺寸
    HUGEPAGE_2MB = 2 * 1024 * 1024
    HUGEPAGE_1GB = 1024 * 1024 * 1024

    def __init__(self, hugepagesz_mb: int = 2):
        self.page_size = hugepagesz_mb * 1024 * 1024
        self.regions: list[HugePageRegion] = []
        self.num_pages = 0
        self.free_pages = 0

    def reserve_pages(self, num_pages: int, numa_node: int = -1) -> bool:
        """
        预保留大页（sysctl vm.nr_hugepages）
        """
        region = HugePageRegion(
            page_size=self.page_size,
            base_addr=0x40000000 + len(self.regions) * num_pages * self.page_size,
            num_pages=num_pages,
            free_pages=num_pages
        )
        self.regions.append(region)
        self.num_pages += num_pages
        self.free_pages += num_pages
        return True

    def allocate_to_process(self, pid: int, num_pages: int) -> Optional[int]:
        """
        为进程分配大页
        返回分配的起始虚拟地址
        """
        if num_pages > self.free_pages:
            return None

        # 找到有足够空闲页的区域
        for region in self.regions:
            if region.free_pages >= num_pages:
                base = region.base_addr + (region.num_pages - region.free_pages) * region.page_size
                region.free_pages -= num_pages
                region.allocated_to.append(pid)
                self.free_pages -= num_pages
                return base

        return None

    def release_from_process(self, pid: int) -> int:
        """释放进程分配的大页"""
        released = 0
        for region in self.regions:
            if pid in region.allocated_to:
                # 简化：释放该进程所有大页
                pages_to_release = 1  # 简化：每次释放1页
                region.free_pages += pages_to_release
                released += pages_to_release

        self.free_pages += released
        return released

    def get_stats(self) -> HugePageStats:
        return HugePageStats(
            total_pages=self.num_pages,
            free_pages=self.free_pages,
            page_size=self.page_size
        )


class TransparentHugePage:
    """
    透明大页（THP）
    内核自动将多个4KB页合并为2MB大页
    模式：always / madvise / never
    """

    THP_MODE_ALWAYS = "always"      # 总是尝试合并
    THP_MODE_MADVISE = "madvise"    # 仅madvise区域
    THP_MODE_NEVER = "never"         # 禁用

    def __init__(self, mode: str = "madvise"):
        self.mode = mode
        self.compaction_enabled = True  # 内存规整（支持1GB大页）

    def try_merge_to_hugepage(self, vaddr: int, size: int) -> bool:
        """
        尝试将虚拟地址范围的4KB页合并为透明大页
        触发条件：
        1. vaddr对齐到2MB
        2. 连续的物理页
        3. 进程通过madvise(MADV_HUGEPAGE)声明
        """
        # 检查对齐
        if vaddr % (2 * 1024 * 1024) != 0:
            return False

        # 模拟：合并成功
        if self.mode == self.THP_MODE_ALWAYS or self.mode == self.THP_MODE_MADVISE:
            return True

        return False

    def split_hugepage(self, vaddr: int) -> list[int]:
        """
        拆分大页为4KB页（访问触发、内存压力等）
        返回拆分后的4KB页虚拟地址列表
        """
        if self.mode == self.THP_MODE_NEVER:
            return []

        # 模拟拆分
        num_4kb_pages = self._get_page_size() // 4096
        return [vaddr + i * 4096 for i in range(num_4kb_pages)]

    def _get_page_size(self) -> int:
        return 2 * 1024 * 1024  # 2MB


class HugePagesCalculator:
    """大页计算工具"""

    @staticmethod
    def calc_recommended_hugepages(mem_mb: int, page_size_mb: int = 2) -> int:
        """
        根据内存大小推荐大页数量
        经验：Oracle建议预留内存的50%给大页
        """
        # 建议值：内存的40%用于大页
        recommended_mb = mem_mb * 0.4
        return int(recommended_mb // page_size_mb)

    @staticmethod
    def calc_tlb_entries_saved(page_size_kb: int, region_mb: int) -> int:
        """
        计算TLB条目节省数量
        4KB页：region_mb * 1024 / 4
        2MB页：region_mb * 1024 / 2048 = region_mb / 2
        """
        pages_4kb = region_mb * 1024  # 4KB页数
        pages_huge = region_mb // 2   # 2MB页数
        return pages_4kb - pages_huge


if __name__ == "__main__":
    from enum import Enum

    print("=== 透明大页（HugePages）演示 ===")

    # 创建大页内存管理器（2MB大页）
    hp_mgr = HugePagesManager(hugepagesz_mb=2)

    # 预留大页
    print("\n--- 预留大页 ---")
    hp_mgr.reserve_pages(num_pages=512)  # 512 * 2MB = 1GB
    stats = hp_mgr.get_stats()
    print(f"大页预留：{stats.total_pages} 页 × {stats.page_size / 1024 / 1024:.0f} MB = {stats.total_pages * stats.page_size / 1024 / 1024:.0f} MB")

    # 为进程分配大页
    print("\n--- 为进程分配大页 ---")
    for pid in [1001, 1002, 1003]:
        base = hp_mgr.allocate_to_process(pid, num_pages=64)  # 每个进程64个大页=128MB
        if base:
            print(f"进程 {pid}: 分配大页 @ 0x{base:x}")

    stats = hp_mgr.get_stats()
    print(f"剩余空闲页: {stats.free_pages} / {stats.total_pages}")

    # 透明大页
    print("\n--- 透明大页（THP）模式 ---")
    thp = TransparentHugePage(mode="madvise")

    test_addr = 0x200000  # 2MB对齐地址
    merged = thp.try_merge_to_hugepage(test_addr, 2 * 1024 * 1024)
    print(f"尝试合并地址 0x{test_addr:x}（2MB对齐）: {'成功' if merged else '失败'}")

    # TLB优化计算
    print("\n--- TLB优化计算 ---")
    region_size = 4096  # 4GB
    saved = HugePagesCalculator.calc_tlb_entries_saved(4, region_size)
    print(f"{region_size}MB区域:")
    print(f"  4KB页需要TLB条目: {region_size * 1024 // 4}")
    print(f"  2MB大页需要TLB条目: {region_size // 2}")
    print(f"  节省: {saved} 条 TLB 条目")

    # 大页配置建议
    print("\n--- 大页配置建议 ---")
    for mem_gb in [16, 32, 64, 128]:
        recommended = HugePagesCalculator.calc_recommended_hugepages(mem_gb * 1024)
        print(f"{mem_gb}GB 内存: 建议预留 {recommended} × 2MB hugepages = {recommended * 2}MB")
