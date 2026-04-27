# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / copy_on_write



本文件实现 copy_on_write 相关的算法功能。

"""



from typing import Dict, List, Optional, Set

from dataclasses import dataclass, field





@dataclass

class Page:

    """物理页"""

    pfn: int              # 页帧号

    data: bytes = None    # 页数据

    ref_count: int = 1   # 引用计数

    cow: bool = False    # 是否是COW页



    def __post_init__(self):

        if self.data is None:

            self.data = b'\x00' * 4096





class VMPage:

    """虚拟内存页"""

    def __init__(self, vaddr: int, pfn: Optional[int] = None):

        self.vaddr = vaddr

        self.pfn = pfn          # 映射的物理页PFN

        self.present = pfn is not None

        self.readonly = False   # 只读标志（COW相关）

        self.cow = False        # COW标志





class Process:

    """进程（简化）"""



    def __init__(self, pid: int, name: str):

        self.pid = pid

        self.name = name



        # 虚拟内存区域

        self.vm_areas: List[VMArea] = []



        # 页表（虚拟地址 -> VMPage）

        self.page_table: Dict[int, VMPage] = {}



        # 父子关系

        self.parent: Optional[Process] = None

        self.children: List[Process] = []



    def add_vma(self, start: int, end: int, flags: Dict):

        """添加虚拟内存区域"""

        vma = VMArea(start=start, end=end, flags=flags)

        self.vm_areas.append(vma)





@dataclass

class VMArea:

    """虚拟内存区域"""

    start: int

    end: int

    flags: Dict = field(default_factory=dict)

    # 权限标志

    # 'read': bool

    # 'write': bool

    # 'exec': bool

    # 'shared': bool

    # 'cow': bool





class PageFrameAllocator:

    """物理页帧分配器"""

    def __init__(self, num_pages: int = 1024):

        self.num_pages = num_pages

        self.pages: Dict[int, Page] = {i: Page(pfn=i) for i in range(num_pages)}

        self.free_list: List[int] = list(range(num_pages))



    def allocate(self) -> Optional[int]:

        """分配一页"""

        if not self.free_list:

            return None

        return self.free_list.pop(0)



    def free(self, pfn: int):

        """释放一页"""

        if 0 <= pfn < self.num_pages:

            self.free_list.append(pfn)





class COWManager:

    """

    COW管理器



    管理fork后的写时复制。

    """



    def __init__(self, allocator: PageFrameAllocator):

        self.allocator = allocator

        self.cow_pages: Set[int] = set()  # 标记为COW的物理页



    def mark_page_cow(self, pfn: int):

        """标记页为COW"""

        if pfn in self.pages:

            self.pages[pfn].cow = True

            self.pages[pfn].ref_count = 1

            self.cow_pages.add(pfn)



    def handle_write_fault(self, process: Process, vaddr: int) -> bool:

        """

        处理写错误（COW）

        return: 是否成功处理

        """

        if vaddr not in process.page_table:

            return False



        vpage = process.page_table[vaddr]

        if not vpage.present or vpage.pfn is None:

            return False



        pfn = vpage.pfn

        page = self.allocator.pages[pfn]



        if page.cow and page.ref_count > 1:

            # 需要复制页

            new_pfn = self.allocator.allocate()

            if new_pfn is None:

                return False



            # 复制内容

            self.allocator.pages[new_pfn].data = page.data[:]

            self.allocator.pages[new_pfn].ref_count = 1

            self.allocator.pages[new_pfn].cow = False



            # 更新原页引用计数

            page.ref_count -= 1



            # 更新进程的页表

            vpage.pfn = new_pfn

            vpage.cow = False



            return True



        elif page.cow and page.ref_count == 1:

            # 唯一引用，直接清除COW标志

            page.cow = False

            vpage.cow = False

            return True



        return False



    @property

    def pages(self):

        return self.allocator.pages





class COWFork:

    """

    COW fork实现



    模拟fork时的COW行为。

    """



    def __init__(self):

        self.allocator = PageFrameAllocator(num_pages=256)

        self.cow_manager = COWManager(self.allocator)



        # 所有进程

        self.processes: Dict[int, Process] = {}

        self.next_pid = 1



    def do_fork(self, parent: Process) -> Process:

        """

        执行fork

        返回新进程

        """

        child = Process(self.next_pid, f"{parent.name}_copy")

        self.next_pid += 1



        child.parent = parent

        parent.children.append(child)



        # 复制VMA

        for vma in parent.vm_areas:

            new_vma = VMArea(start=vma.start, end=vma.end, flags=vma.flags.copy())

            child.vm_areas.append(new_vma)



        # 复制页表（共享物理页，标记COW）

        for vaddr, vpage in parent.page_table.items():

            if vpage.present and vpage.pfn is not None:

                # 共享物理页

                child_vpage = VMPage(vaddr, vpage.pfn)

                child_vpage.present = True

                child_vpage.cow = True

                child_vpage.readonly = True  # 设为只读



                child.page_table[vaddr] = child_vpage



                # 增加物理页引用计数

                pfn = vpage.pfn

                if pfn in self.allocator.pages:

                    self.allocator.pages[pfn].ref_count += 1

                    self.allocator.pages[pfn].cow = True



        return child



    def handle_page_fault(self, process: Process, vaddr: int, is_write: bool) -> bool:

        """

        处理页错误

        """

        if vaddr not in process.page_table:

            return False



        vpage = process.page_table[vaddr]



        if not vpage.present:

            return False



        if is_write and vpage.cow:

            # COW写错误

            return self.cow_manager.handle_write_fault(process, vaddr)



        return True





def simulate_cow():

    """

    模拟COW fork

    """

    print("=" * 60)

    print("写时复制 (Copy-On-Write)")

    print("=" * 60)



    cow_fork = COWFork()



    # 创建父进程

    parent = Process(1, "parent")

    cow_fork.processes[1] = parent



    # 模拟父进程的内存

    print("\n创建父进程:")

    print("-" * 50)



    # 添加一些虚拟内存区域

    parent.add_vma(0x1000, 0x2000, {'read': True, 'write': True, 'cow': True})

    parent.add_vma(0x2000, 0x3000, {'read': True, 'write': True, 'cow': True})



    # 分配一些物理页

    print("分配物理页:")

    for i in range(4):

        pfn = cow_fork.allocator.allocate()

        if pfn is not None:

            # 填充一些数据

            cow_fork.allocator.pages[pfn].data = f"Page {pfn} data".encode() + b'\x00' * (4096 - 15)

            print(f"  PFN={pfn} 分配给父进程")



            vaddr = 0x1000 + i * 4096

            vpage = VMPage(vaddr, pfn)

            vpage.cow = True

            parent.page_table[vaddr] = vpage



    # fork

    print("\n执行fork:")

    print("-" * 50)



    child = cow_fork.do_fork(parent)

    print(f"  父进程 PID={parent.pid} (名称={parent.name})")

    print(f"  子进程 PID={child.pid} (名称={child.name})")

    print(f"  子进程页表与父进程共享物理页")



    # 显示物理页引用计数

    print("\nfork后物理页状态:")

    print(f"  {'PFN':<6} {'RefCount':<10} {'COW':<6} {'数据预览':<20}")

    print(f"  {'-'*50}")



    for pfn in [0, 1, 2, 3]:

        page = cow_fork.allocator.pages[pfn]

        data_preview = page.data[:15].decode('utf-8', errors='ignore') if page.data else ''

        print(f"  {pfn:<6} {page.ref_count:<10} {'是' if page.cow else '否':<6} {data_preview:<20}")



    # 模拟子进程读取（不触发COW）

    print("\n子进程读取页面 (不触发COW):")

    print("-" * 50)



    for vaddr in [0x1000, 0x2000]:

        if vaddr in child.page_table:

            pfn = child.page_table[vaddr].pfn

            page = cow_fork.allocator.pages[pfn]

            print(f"  虚拟地址 0x{vaddr:08X} -> PFN={pfn}, ref_count={page.ref_count}")



    # 模拟子进程写入（触发COW）

    print("\n子进程写入页面 (触发COW):")

    print("-" * 50)



    vaddr = 0x2000  # 尝试写入第二个页



    print(f"  尝试写入虚拟地址 0x{vaddr:08X}")

    print(f"  页错误! 该页是COW页且ref_count={cow_fork.allocator.pages[1].ref_count}")



    # 触发COW处理

    success = cow_fork.handle_page_fault(child, vaddr, is_write=True)



    if success:

        print(f"  COW处理成功!")

        print(f"  分配新物理页给子进程")

        print(f"  原页ref_count减1")



        # 显示处理后的状态

        print(f"\n处理后物理页状态:")

        for pfn in [0, 1, 2, 3]:

            page = cow_fork.allocator.pages[pfn]

            data_preview = page.data[:15].decode('utf-8', errors='ignore') if page.data else ''

            print(f"  PFN={pfn}: ref_count={page.ref_count}, cow={'是' if page.cow else '否'}, 数据={data_preview}")





if __name__ == "__main__":

    simulate_cow()

