# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / huge_pages



本文件实现 huge_pages 相关的算法功能。

"""



from typing import Dict, List, Optional, Set

from dataclasses import dataclass





# 标准页大小

PAGE_SIZE_4KB = 4096

PAGE_SIZE_2MB = 2 * 1024 * 1024

PAGE_SIZE_1GB = 1024 * 1024 * 1024





@dataclass

class HugePage:

    """大页"""

    pfn: int               # 物理页帧号

    size: int             # 页大小

    order: int            # 阶（order=10表示2^10 * 4KB = 4MB... 实际使用不同）

    free: bool = True

    virtual_addr: int = 0





class HugeTLB:

    """

    HugeTLB大页池管理



    管理预留给hugetlbfs使用的大页。

    """



    def __init__(self):

        # 大页池

        self.huge_pages_2mb: List[HugePage] = []

        self.huge_pages_1gb: List[HugePage] = []



        # 统计

        self.free_pages_2mb = 0

        self.free_pages_1gb = 0

        self.reserved_pages = 0



    def alloc_hugepage_2mb(self) -> Optional[int]:

        """分配2MB大页"""

        for page in self.huge_pages_2mb:

            if page.free:

                page.free = False

                self.free_pages_2mb -= 1

                return page.pfn

        return None



    def free_hugepage_2mb(self, pfn: int):

        """释放2MB大页"""

        for page in self.huge_pages_2mb:

            if page.pfn == pfn:

                page.free = True

                self.free_pages_2mb += 1

                return



    def get_stats(self) -> Dict:

        """获取大页池统计"""

        total_2mb = len(self.huge_pages_2mb)

        free_2mb = self.free_pages_2mb

        return {

            '2mb_total': total_2mb,

            '2mb_free': free_2mb,

            '2mb_used': total_2mb - free_2mb,

            '1gb_total': len(self.huge_pages_1gb),

            '1gb_free': self.free_pages_1gb,

        }





class TransparentHugePage:

    """

    透明大页 (THP)



    内核自动将4KB页合并成2MB大页。

    """



    # 合并状态

    class MergeState:

        NONE = "none"      # 未合并

        WORKING = "working"  # 合并中

        MERGED = "merged"    # 已合并

        SPLIT = "split"      # 已拆分



    def __init__(self):

        # 普通页（4KB）

        self.small_pages: Set[int] = set()



        # 大页

        self.huge_pages: List[HugePage] = []



        # 页大小

        self.small_page_size = PAGE_SIZE_4KB

        self.huge_page_size = PAGE_SIZE_2MB



        # 合并阈值

        self.compaction_threshold = 0.8



        # 统计

        self.allocations_small = 0

        self.allocations_huge = 0

        self.merges = 0

        self.splits = 0



    def _can_merge(self, pages: List[int]) -> bool:

        """检查是否可以合并"""

        if len(pages) != self.huge_page_size // self.small_page_size:

            return False



        # 检查页是否连续且空闲

        for i, pfn in enumerate(pages[:-1]):

            if pages[i + 1] != pfn + 1:

                return False

        return True



    def _try_merge_pages(self) -> bool:

        """

        尝试合并小页成大页

        return: 是否成功合并

        """

        if len(self.small_pages) < self.huge_page_size // self.small_page_size:

            return False



        # 找连续的512个页

        sorted_pages = sorted(self.small_pages)

        for i in range(len(sorted_pages) - 511):

            chunk = sorted_pages[i:i + 512]

            if self._can_merge(chunk):

                # 合并

                base_pfn = chunk[0]

                huge_page = HugePage(

                    pfn=base_pfn,

                    size=self.huge_page_size,

                    order=9,  # 2MB = 2^9 * 4KB

                    free=False

                )

                self.huge_pages.append(huge_page)



                # 移除小页

                for pfn in chunk:

                    self.small_pages.discard(pfn)



                self.merges += 1

                return True



        return False



    def allocate_small(self, size: int) -> Optional[int]:

        """分配小页"""

        # 简化：直接分配

        pfn = self.allocations_small + 0x1000

        self.small_pages.add(pfn)

        self.allocations_small += 1

        return pfn



    def allocate_huge(self, size: int) -> Optional[HugePage]:

        """分配大页"""

        if size > self.huge_page_size:

            return None



        # 尝试合并

        if len(self.small_pages) >= self.huge_page_size // self.small_page_size:

            self._try_merge_pages()



        # 分配大页

        if self.huge_pages:

            for page in self.huge_pages:

                if page.free and page.size >= size:

                    page.free = False

                    self.allocations_huge += 1

                    return page



        return None



    def free_huge(self, pfn: int):

        """释放大页"""

        for page in self.huge_pages:

            if page.pfn == pfn:

                page.free = True

                # 触发拆分

                self.splits += 1

                # 简化为小页

                for i in range(page.size // self.small_page_size):

                    self.small_pages.add(pfn + i)

                break





class Hugetlbfs:

    """

    hugetlbfs文件系统



    提供大页的文件系统接口。

    """



    def __init__(self, huge_pages_pool: HugeTLB):

        self.pool = huge_pages_pool

        self.mappings: Dict[int, int] = {}  # vaddr -> pfn



        # 文件系统参数

        self.page_size = PAGE_SIZE_2MB

        self.max_huge_pages = 100



    def mmap(self, size: int) -> Optional[int]:

        """

        映射大页

        return: 虚拟地址

        """

        # 对齐到页大小

        aligned_size = ((size + self.page_size - 1) // self.page_size) * self.page_size



        # 分配大页

        pfn = self.pool.alloc_hugepage_2mb()

        if pfn is None:

            return None



        # 创建映射

        vaddr = self.allocations_small * self.page_size + 0x10000000

        self.mappings[vaddr] = pfn

        return vaddr



    def munmap(self, vaddr: int):

        """解除映射"""

        if vaddr in self.mappings:

            pfn = self.mappings[vaddr]

            self.pool.free_hugepage_2mb(pfn)

            del self.mappings[vaddr]



    def get_stats(self) -> Dict:

        """获取统计"""

        return {

            'total_mappings': len(self.mappings),

            'pool_stats': self.pool.get_stats(),

        }





def simulate_huge_pages():

    """

    模拟大页内存

    """

    print("=" * 60)

    print("大页内存 (HugePages)")

    print("=" * 60)



    # HugeTLB演示

    print("\n" + "-" * 50)

    print("HugeTLB (预留大页池)")

    print("-" * 50)



    huge_tlb = HugeTLB()



    # 初始化大页池

    for i in range(16):

        page = HugePage(pfn=i * 512, size=PAGE_SIZE_2MB, order=9, free=True)

        huge_tlb.huge_pages_2mb.append(page)

    huge_tlb.free_pages_2mb = 16



    print(f"初始状态:")

    print(f"  2MB大页: 总数={len(huge_tlb.huge_pages_2mb)}, 空闲={huge_tlb.free_pages_2mb}")



    # 分配大页

    print("\n分配大页:")

    for i in range(3):

        pfn = huge_tlb.alloc_hugepage_2mb()

        if pfn:

            print(f"  分配: PFN={pfn}, 大小=2MB")

        else:

            print(f"  分配失败")



    print(f"\n分配后状态: 空闲={huge_tlb.free_pages_2mb}")



    # 释放

    print("\n释放:")

    huge_tlb.free_hugepage_2mb(0)

    print(f"  释放PFN=0, 空闲={huge_tlb.free_pages_2mb}")



    # THP演示

    print("\n" + "-" * 50)

    print("Transparent HugePage (THP)")

    print("-" * 50)



    thp = TransparentHugePage()



    print(f"页大小: 小页={thp.small_page_size}B, 大页={thp.huge_page_size // 1024}KB")



    # 分配一些小页

    print("\n分配小页:")

    for i in range(10):

        pfn = thp.allocate_small(4096)

        print(f"  分配 PFN={pfn}")



    print(f"\n小页数: {len(thp.small_pages)}, 大页数: {len(thp.huge_pages)}")

    print(f"合并次数: {thp.merges}, 拆分次数: {thp.splits}")



    # hugetlbfs演示

    print("\n" + "-" * 50)

    print("hugetlbfs")

    print("-" * 50)



    huge_tlb2 = HugeTLB()

    for i in range(8):

        page = HugePage(pfn=i * 512, size=PAGE_SIZE_2MB, order=9, free=True)

        huge_tlb2.huge_pages_2mb.append(page)

    huge_tlb2.free_pages_2mb = 8



    hugetlbfs = Hugetlbfs(huge_tlb2)



    print("\n映射大页:")

    vaddr1 = hugetlbfs.mmap(2 * 1024 * 1024)

    print(f"  mmap(2MB) -> vaddr=0x{vaddr1:08X}" if vaddr1 else "  mmap 失败")



    vaddr2 = hugetlbfs.mmap(4 * 1024 * 1024)

    print(f"  mmap(4MB) -> vaddr=0x{vaddr2:08X}" if vaddr2 else "  mmap 失败")



    stats = hugetlbfs.get_stats()

    print(f"\n映射统计: {stats['total_mappings']} 个映射")





if __name__ == "__main__":

    simulate_huge_pages()

