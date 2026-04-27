# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / vm_mmap



本文件实现 vm_mmap 相关的算法功能。

"""



from typing import Dict, List, Optional, Set, Tuple

from dataclasses import dataclass, field

from enum import Enum





class VMAPermission(Enum):

    """虚拟内存区域权限"""

    READ = 0x1

    WRITE = 0x2

    EXEC = 0x4





@dataclass

class VirtualMemoryArea:

    """虚拟内存区域 (VMA)"""

    start: int          # 起始地址

    end: int            # 结束地址

    vm_flags: int = 0   # 权限标志

    vm_pgoff: int = 0   # 文件内偏移（页对齐）



    # 文件映射

    file_path: Optional[str] = None

    file_offset: int = 0



    # 内存映射类型

    is_anonymous: bool = True  # 匿名映射 vs 文件映射

    is_shared: bool = False     # 共享 vs 私有



    # 页表信息

    page_frames: Dict[int, int] = field(default_factory=dict)  # vpn -> ppn



    def size(self) -> int:

        """区域大小"""

        return self.end - self.start



    def contains(self, addr: int) -> bool:

        """检查地址是否在区域内"""

        return self.start <= addr < self.end





class PageTableEntry:

    """页表条目 (简化)"""

    def __init__(self, present: bool = False, ppn: int = 0, writable: bool = True):

        self.present = present

        self.ppn = ppn

        self.writable = writable

        self.accessed = False

        self.dirty = False





class MemoryMapper:

    """

    内存映射管理器



    管理进程的虚拟内存区域。

    """



    def __init__(self):

        # 虚拟内存区域列表

        self.vmas: List[VirtualMemoryArea] = []



        # 页表：虚拟页号 -> PTE

        self.page_table: Dict[int, PageTableEntry] = {}



        # 物理内存

        self.physical_memory: Dict[int, bytes] = {}

        self.next_pfn = 0



        # 统计

        self.page_faults = 0

        self.pages_loaded = 0



    def _get_vpn(self, addr: int) -> int:

        """虚拟页号"""

        return addr // 4096



    def _get_offset(self, addr: int) -> int:

        """页内偏移"""

        return addr % 4096



    def _find_vma(self, addr: int) -> Optional[VirtualMemoryArea]:

        """查找包含addr的VMA"""

        for vma in self.vmas:

            if vma.contains(addr):

                return vma

        return None



    def mmap(self, start: int, length: int, prot: int,

             flags: int, fd: int = -1, offset: int = 0) -> int:

        """

        创建内存映射

        return: 映射起始地址

        """

        # 对齐地址

        page_size = 4096

        aligned_start = (start + page_size - 1) // page_size * page_size

        aligned_length = (length + page_size - 1) // page_size * page_size



        vma = VirtualMemoryArea(

            start=aligned_start,

            end=aligned_start + aligned_length,

            vm_flags=prot,

            vm_pgoff=offset // page_size,

            is_anonymous=(fd == -1),

            is_shared=(flags & 0x10 != 0),  # MAP_SHARED

        )



        self.vmas.append(vma)

        print(f"  mmap: 0x{aligned_start:08X} - 0x{aligned_start + aligned_length:08X}")

        print(f"    长度: {aligned_length} bytes, prot: {prot}, anonymous: {vma.is_anonymous}")



        return aligned_start



    def munmap(self, start: int, length: int) -> bool:

        """解除映射"""

        page_size = 4096

        end = start + length



        self.vmas = [vma for vma in self.vmas

                     if not (vma.start >= start and vma.end <= end)]



        # 清除页表

        for vpn in list(self.page_table.keys()):

            if vpn * page_size >= start and vpn * page_size < end:

                del self.page_table[vpn]



        return True



    def page_fault_handler(self, addr: int, write: bool = False) -> bool:

        """

        缺页错误处理

        return: 是否成功处理

        """

        self.page_faults += 1



        # 查找VMA

        vma = self._find_vma(addr)

        if vma is None:

            print(f"  [PageFault] 地址 0x{addr:08X} 无VMA，SIGSEGV")

            return False



        # 检查权限

        if write and not (vma.vm_flags & VMAPermission.WRITE.value):

            print(f"  [PageFault] 权限错误，写入只读区域")

            return False



        # 分配物理页

        vpn = self._get_vpn(addr)

        ppn = self._allocate_physical_page()



        # 更新页表

        self.page_table[vpn] = PageTableEntry(present=True, ppn=ppn)



        # 如果是匿名映射，初始化为0

        if vma.is_anonymous:

            self.physical_memory[ppn] = b'\x00' * 4096

        else:

            # 文件映射，从文件加载

            self.physical_memory[ppn] = self._load_from_file(vma, addr)



        self.pages_loaded += 1

        print(f"  [PageFault] 加载页: VPN={vpn} -> PPN={ppn}")



        return True



    def _allocate_physical_page(self) -> int:

        """分配物理页"""

        ppn = self.next_pfn

        self.next_pfn += 1

        return ppn



    def _load_from_file(self, vma: VirtualMemoryArea, addr: int) -> bytes:

        """从文件加载数据（简化）"""

        # 简化：返回填充数据

        return b'File data at ' + str(addr).encode() + b'\x00' * (4096 - 20)



    def read_virtual(self, addr: int) -> Optional[bytes]:

        """读取虚拟内存"""

        vpn = self._get_vpn(addr)

        offset = self._get_offset(addr)



        if vpn not in self.page_table:

            # 缺页

            if not self.page_fault_handler(addr):

                return None



        pte = self.page_table[vpn]

        ppn = pte.ppn

        paddr = ppn * 4096 + offset



        return self.physical_memory.get(ppn, b'\x00')[:32]



    def write_virtual(self, addr: int, data: bytes) -> bool:

        """写入虚拟内存"""

        vpn = self._get_vpn(addr)



        if vpn not in self.page_table:

            if not self.page_fault_handler(addr, write=True):

                return False



        pte = self.page_table[vpn]

        ppn = pte.ppn



        if ppn in self.physical_memory:

            mem = self.physical_memory[ppn]

            self.physical_memory[ppn] = data[:4096] + mem[len(data):]



        pte.dirty = True

        return True





def simulate_mmap_demand_paging():

    """

    模拟内存映射和请求调页

    """

    print("=" * 60)

    print("虚拟内存管理：内存映射与请求调页")

    print("=" * 60)



    mapper = MemoryMapper()



    # mmap匿名内存

    print("\n" + "-" * 50)

    print("1. mmap匿名内存")

    print("-" * 50)



    addr1 = mapper.mmap(

        start=0x10000000,

        length=8192,  # 8KB

        prot=0x3,  # READ|WRITE

        flags=0x2,  # MAP_PRIVATE

        fd=-1  # 匿名映射

    )

    print(f"  映射地址: 0x{addr1:08X}")



    # 首次访问（触发缺页）

    print("\n" + "-" * 50)

    print("2. 首次访问页面（请求调页）")

    print("-" * 50)



    print(f"\n访问地址 0x{addr1:08X} (第一个字节):")

    data = mapper.read_virtual(addr1)

    print(f"  数据: {data}")



    print(f"\n访问地址 0x{addr1 + 4096:08X} (第二页):")

    data = mapper.read_virtual(addr1 + 4096)

    print(f"  数据: {data}")



    # 写入

    print("\n" + "-" * 50)

    print("3. 写入页面")

    print("-" * 50)



    print(f"\n写入 'Hello, mmap!' 到 0x{addr1:08X}:")

    test_data = b'Hello, mmap! Page data here.'

    success = mapper.write_virtual(addr1, test_data)

    print(f"  成功: {success}")



    # 读取验证

    print(f"\n验证写入:")

    data = mapper.read_virtual(addr1)

    print(f"  数据: {data}")



    # mmap文件

    print("\n" + "-" * 50)

    print("4. mmap文件映射")

    print("-" * 50)



    addr2 = mapper.mmap(

        start=0x20000000,

        length=4096,

        prot=0x1,  # READ

        flags=0x1,  # MAP_SHARED

        fd=5,  # 文件描述符

        offset=0

    )

    print(f"  文件映射地址: 0x{addr2:08X}")



    print(f"\n读取文件映射页面:")

    data = mapper.read_virtual(addr2)

    print(f"  数据: {data}")



    # munmap

    print("\n" + "-" * 50)

    print("5. munmap解除映射")

    print("-" * 50)



    print(f"\nmunmap(0x{addr1:08X}, 8192):")

    mapper.munmap(addr1, 8192)

    print(f"  剩余VMA数量: {len(mapper.vmas)}")



    # 统计

    print("\n" + "-" * 50)

    print("统计")

    print("-" * 50)

    print(f"  缺页次数: {mapper.page_faults}")

    print(f"  加载页数: {mapper.pages_loaded}")

    print(f"  页表条目数: {len(mapper.page_table)}")





if __name__ == "__main__":

    simulate_mmap_demand_paging()

