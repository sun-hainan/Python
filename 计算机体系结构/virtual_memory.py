# -*- coding: utf-8 -*-
"""
算法实现：计算机体系结构 / virtual_memory

本文件实现 virtual_memory 相关的算法功能。
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


# 页大小（4KB）
PAGE_SIZE = 4096
PAGE_BITS = 12  # 2^12 = 4096

# 地址宽度
VIRTUAL_ADDRESS_BITS = 32
PHYSICAL_ADDRESS_BITS = 32

# VPN和PPN位数
VPN_BITS_PER_LEVEL = 10  # 每级页表索引10位
NUM_LEVELS = 2           # 2级页表


@dataclass
class PageTableEntry:
    """页表条目 (PTE)"""
    present: bool = False        # 是否在内存中
    physical_page: int = 0       # 物理页号
    read_only: bool = False      # 只读标志
    kernel_only: bool = False    # 仅内核可访问
    accessed: bool = False       # 是否被访问过
    dirty: bool = False          # 是否被修改（脏页）
    user_defined: int = 0        # 用户定义位


class PageTableNode:
    """页表节点（页目录或页表）"""
    def __init__(self, is_leaf: bool = False):
        self.is_leaf = is_leaf  # 是否是叶子节点（指向物理页）
        self.entries: List[Optional[PageTableEntry]] = [None] * 1024  # 1024个条目


class MultiLevelPageTable:
    """
    多级页表

    32位虚拟地址划分（2级页表，每级10位）：
    [VPN1 (10 bits) | VPN2 (10 bits) | Offset (12 bits)]

    结构：
    - 第1级页表（页目录）：1024个条目，每个指向一个第2级页表
    - 第2级页表：1024个条目，每个指向一个物理页
    - 每个物理页：4KB
    """

    def __init__(self):
        # 第1级页表（根页目录）
        self.root = PageTableNode(is_leaf=False)

        # TLB（Translation Lookaside Buffer）
        self.tlb: Dict[int, int] = {}  # {vpn: ppn}
        self.tlb_hits = 0
        self.tlb_misses = 0

        # 统计
        self.page_walks = 0

    def _get_vpn_parts(self, virtual_address: int) -> Tuple[int, int]:
        """分解虚拟页号"""
        # [VPN1 | VPN2]
        vpn1 = (virtual_address >> (PAGE_BITS + VPN_BITS_PER_LEVEL)) & ((1 << VPN_BITS_PER_LEVEL) - 1)
        vpn2 = (virtual_address >> PAGE_BITS) & ((1 << VPN_BITS_PER_LEVEL) - 1)
        return vpn1, vpn2

    def _allocate_pte(self, pde: PageTableEntry) -> PageTableNode:
        """分配一个新的第2级页表"""
        node = PageTableNode(is_leaf=True)
        pde.present = True
        return node

    def translate(self, virtual_address: int) -> Optional[int]:
        """
        地址翻译：虚拟地址 -> 物理地址
        return: 物理地址，失败返回None
        """
        if virtual_address < 0 or virtual_address >= (1 << VIRTUAL_ADDRESS_BITS):
            return None

        # 尝试TLB
        vpn = virtual_address >> PAGE_BITS
        if vpn in self.tlb:
            self.tlb_hits += 1
            ppn = self.tlb[vpn]
            offset = virtual_address & (PAGE_SIZE - 1)
            return (ppn << PAGE_BITS) | offset

        self.tlb_misses += 1
        self.page_walks += 1

        # 多级页表遍历
        vpn1, vpn2 = self._get_vpn_parts(virtual_address)

        # 第1级查找
        pde = self.root.entries[vpn1]
        if pde is None or not pde.present:
            return None

        # 获取第2级页表
        # 实际实现中，pde应该指向一个物理页
        # 这里简化：直接使用pde.physical_page作为页表基址
        # pde.physical_page 存储的是第2级页表的物理页号
        level2_table_offset = pde.physical_page << PAGE_BITS

        # 构建第2级页表条目索引（简化：直接在root中模拟）
        # 实际硬件会使用pde.physical_page作为基址访问内存
        pte_index = vpn2

        # 模拟：从第2级页表获取PTE
        # 这里简化处理，实际需要内存访问
        pte = self._get_or_create_pte(vpn1, vpn2)

        if pte is None or not pte.present:
            return None

        # 构造物理地址
        offset = virtual_address & (PAGE_SIZE - 1)
        physical_address = (pte.physical_page << PAGE_BITS) | offset

        # 更新TLB
        self.tlb[vpn] = pte.physical_page

        # 更新访问统计
        pte.accessed = True

        return physical_address

    def _get_or_create_pte(self, vpn1: int, vpn2: int) -> Optional[PageTableEntry]:
        """获取或创建页表条目"""
        # 确保第1级页表条目存在
        if self.root.entries[vpn1] is None:
            self.root.entries[vpn1] = PageTableEntry()

        pde = self.root.entries[vpn1]

        # 如果第2级页表不存在且is_leaf
        if not hasattr(self, '_level2_tables'):
            self._level2_tables: Dict[int, PageTableNode] = {}

        level2_key = vpn1
        if level2_key not in self._level2_tables:
            if not pde.present:
                return None
            self._level2_tables[level2_key] = PageTableNode(is_leaf=True)

        level2_table = self._level2_tables[level2_key]

        if level2_table.entries[vpn2] is None:
            level2_table.entries[vpn2] = PageTableEntry()

        return level2_table.entries[vpn2]

    def map(self, virtual_page: int, physical_page: int, flags: dict = None):
        """
        建立虚拟页到物理页的映射
        param virtual_page: 虚拟页号
        param physical_page: 物理页号
        param flags: 映射标志
        """
        vpn1 = (virtual_page >> VPN_BITS_PER_LEVEL) & ((1 << VPN_BITS_PER_LEVEL) - 1)
        vpn2 = virtual_page & ((1 << VPN_BITS_PER_LEVEL) - 1)

        pte = self._get_or_create_pte(vpn1, vpn2)
        if pte:
            pte.present = True
            pte.physical_page = physical_page
            if flags:
                pte.read_only = flags.get('read_only', False)
                pte.kernel_only = flags.get('kernel_only', False)

            # 更新TLB
            self.tlb[virtual_page] = physical_page

    def unmap(self, virtual_page: int):
        """解除映射"""
        vpn1 = (virtual_page >> VPN_BITS_PER_LEVEL) & ((1 << VPN_BITS_PER_LEVEL) - 1)
        vpn2 = virtual_page & ((1 << VPN_BITS_PER_LEVEL) - 1)

        pte = self._get_or_create_pte(vpn1, vpn2)
        if pte:
            pte.present = False

        # 从TLB删除
        if virtual_page in self.tlb:
            del self.tlb[virtual_page]


class TLBEntry:
    """TLB条目"""
    def __init__(self, vpn: int, ppn: int, valid: bool = True):
        self.vpn = vpn
        self.ppn = ppn
        self.valid = valid
        self.lru_counter = 0


class TLB:
    """
    TLB (Translation Lookaside Buffer)

    是CPU中的一个硬件缓存，用于加速虚拟地址到物理地址的转换。
    通常使用组相联或全相联映射。
    """

    def __init__(self, num_entries: int = 64, associativity: int = 4):
        self.num_entries = num_entries
        self.associativity = associativity
        self.num_sets = num_entries // associativity

        # TLB存储：[set][way] = TLBEntry
        self.entries: List[List[Optional[TLBEntry]]] = [
            [None] * associativity for _ in range(self.num_sets)
        ]
        self.lru_counters: List[List[int]] = [
            [0] * associativity for _ in range(self.num_sets)
        ]

        # 统计
        self.hits = 0
        self.misses = 0

    def _get_set(self, vpn: int) -> int:
        """获取set索引"""
        return vpn % self.num_sets

    def lookup(self, vpn: int) -> Optional[int]:
        """查找TLB"""
        set_idx = self._get_set(vpn)

        for way in range(self.associativity):
            entry = self.entries[set_idx][way]
            if entry and entry.valid and entry.vpn == vpn:
                # 命中
                self.hits += 1
                # 更新LRU
                self.lru_counters[set_idx][way] = self._get_global_counter(set_idx)
                return entry.ppn

        self.misses += 1
        return None

    def insert(self, vpn: int, ppn: int):
        """插入TLB条目"""
        set_idx = self._get_set(vpn)

        # 找一个空位或LRU位置
        victim_way = 0
        min_lru = float('inf')

        for way in range(self.associativity):
            if self.entries[set_idx][way] is None:
                # 找到空位
                victim_way = way
                break
            if self.lru_counters[set_idx][way] < min_lru:
                min_lru = self.lru_counters[set_idx][way]
                victim_way = way
        else:
            # 所有路都满了，用LRU
            pass

        self.entries[set_idx][victim_way] = TLBEntry(vpn, ppn)
        self.lru_counters[set_idx][victim_way] = self._get_global_counter(set_idx)

    def _get_global_counter(self, set_idx: int) -> int:
        """获取全局计数器（模拟）"""
        return sum(self.lru_counters[set_idx])

    def invalidate(self, vpn: int):
        """使某个VPN的条目无效"""
        set_idx = self._get_set(vpn)
        for way in range(self.associativity):
            entry = self.entries[set_idx][way]
            if entry and entry.vpn == vpn:
                entry.valid = False

    def flush(self):
        """刷新整个TLB"""
        self.entries = [[None] * self.associativity for _ in range(self.num_sets)]


def simulate_virtual_memory():
    """
    模拟虚拟内存和TLB
    """
    print("=" * 60)
    print("虚拟内存：多级页表与TLB")
    print("=" * 60)

    # 创建2级页表
    page_table = MultiLevelPageTable()

    # 建立一些映射
    mappings = [
        (0x0000, 0x10000),  # 虚拟页0 -> 物理页0x10
        (0x0001, 0x10001),  # 虚拟页1 -> 物理页0x10001
        (0x0040, 0x20000),  # 虚拟页0x40 -> 物理页0x20000
    ]

    print("\n建立页表映射:")
    for vpage, ppage in mappings:
        page_table.map(vpage, ppage)
        print(f"  VPN 0x{vpage:03X} -> PPN 0x{ppage:05X}")

    # 测试地址翻译
    print("\n地址翻译测试:")
    test_addresses = [
        0x0000_1000,  # 虚拟页0，偏移0x1000
        0x0001_2000,  # 虚拟页1，偏移0x2000
        0x0040_3000,  # 虚拟页0x40，偏移0x3000
        0x0020_0000,  # 未映射的页
    ]

    for va in test_addresses:
        pa = page_table.translate(va)
        vpn = va >> PAGE_BITS
        offset = va & (PAGE_SIZE - 1)
        if pa:
            ppn = pa >> PAGE_BITS
            poffset = pa & (PAGE_SIZE - 1)
            print(f"  VA 0x{va:08X} -> PA 0x{pa:08X} (VPN=0x{vpn:03X}, Offset=0x{offset:03X})")
        else:
            print(f"  VA 0x{va:08X} -> [页面故障]")

    # TLB统计
    total = page_table.tlb_hits + page_table.tlb_misses
    if total > 0:
        hit_rate = page_table.tlb_hits / total * 100
        print(f"\nTLB命中率: {hit_rate:.1f}% ({page_table.tlb_hits}/{total})")

    # 模拟独立TLB
    print("\n" + "-" * 40)
    print("独立TLB模拟:")
    print("-" * 40)

    tlb = TLB(num_entries=16, associativity=4)

    # TLB操作
    tlb.insert(0x123, 0x45678)
    tlb.insert(0x124, 0x45679)
    tlb.insert(0x125, 0x4567A)

    print("\n查找测试:")
    results = [
        tlb.lookup(0x123),  # 命中
        tlb.lookup(0x124),  # 命中
        tlb.lookup(0x200),  # 未命中
    ]

    for i, result in enumerate(results):
        print(f"  lookup(0x{['123', '124', '200'][i]}) -> {f'0x{result:05X}' if result else 'None'}")

    print(f"\nTLB统计: 命中={tlb.hits}, 未命中={tlb.misses}")


if __name__ == "__main__":
    simulate_virtual_memory()
