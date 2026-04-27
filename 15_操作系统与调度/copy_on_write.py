# -*- coding: utf-8 -*-

"""

算法实现：15_操作系统与调度 / copy_on_write



本文件实现 copy_on_write 相关的算法功能。

"""



from dataclasses import dataclass, field

from typing import Optional





@dataclass

class PhysicalPage:

    """物理页框"""

    page_id: int

    data: bytearray = field(default_factory=lambda: bytearray(4096))  # 4KB数据

    ref_count: int = 1  # 引用计数（共享计数）



    def inc_ref(self):

        self.ref_count += 1



    def dec_ref(self) -> bool:

        """减少引用，返回是否可回收"""

        self.ref_count -= 1

        return self.ref_count <= 0





@dataclass

class VirtualMemoryArea:

    """虚拟内存区域"""

    start_addr: int

    size: int

    page_frames: list[Optional[int]] = field(default_factory=list)  # 物理页ID列表

    is_cow: bool = True  # 是否启用COW





class ProcessAddressSpace:

    """进程地址空间（简化页表）"""



    def __init__(self, pid: int):

        self.pid = pid

        self.vmas: list[VirtualMemoryArea] = []

        self.page_frames: list[Optional[int]] = []  # 虚拟页->物理页ID

        self.parent: Optional["ProcessAddressSpace"] = None





class CopyOnWriteManager:

    """

    COW管理器

    原理：

    1. fork时，子进程继承父进程的物理页（共享，ref_count++）

    2. 所有页标记为只读

    3. 任一进程写入时触发page fault，分配新页并复制内容

    4. 双方各自获得独立的物理页，ref_count变为1

    """



    PAGE_SIZE = 4096



    def __init__(self, num_pages: int = 256):

        self.pages: list[PhysicalPage] = []

        self.free_pages: list[int] = []

        self._init_pages(num_pages)



    def _init_pages(self, num_pages: int):

        """初始化物理页池"""

        for i in range(num_pages):

            self.pages.append(PhysicalPage(page_id=i))

            self.free_pages.append(i)



    def allocate_page(self) -> Optional[int]:

        """分配物理页"""

        if not self.free_pages:

            return None

        return self.free_pages.pop(0)



    def free_page(self, page_id: int):

        """释放物理页"""

        if 0 <= page_id < len(self.pages):

            self.free_pages.append(page_id)



    def share_page(self, page_id: int) -> int:

        """共享页：ref_count++"""

        if 0 <= page_id < len(self.pages):

            self.pages[page_id].inc_ref()

        return page_id



    def unshare_page(self, page_id: int) -> int:

        """

        解除共享（触发COW复制）

        返回新的物理页ID

        """

        page = self.pages[page_id]

        if page.ref_count == 1:

            # 只有当前进程使用，无需复制

            return page_id



        # 需要复制

        new_page_id = self.allocate_page()

        if new_page_id is None:

            return None



        # 复制内容

        new_page = self.pages[new_page_id]

        new_page.data[:] = page.data[:]  # 内容复制

        new_page.ref_count = 1



        # 减少原页引用

        page.dec_ref()



        return new_page_id



    def write_page(self, page_id: int, offset: int, value: bytes) -> bool:

        """写入物理页（触发COW检查）"""

        if page_id < 0 or page_id >= len(self.pages):

            return False

        page = self.pages[page_id]

        page.data[offset:offset + len(value)] = value

        return True





class COWProcess:

    """支持COW的进程"""



    def __init__(self, pid: int, vm: VirtualMemoryArea, cow_manager: CopyOnWriteManager):

        self.pid = pid

        self.vm = vm

        self.cow = cow_manager

        self.writable = False  # 默认只读（COW模式）



    def fork_from(self, parent: "COWProcess") -> "COWProcess":

        """fork：子进程共享父进程的物理页"""

        child_vm = VirtualMemoryArea(

            start_addr=parent.vm.start_addr,

            size=parent.vm.size,

            page_frames=parent.vm.page_frames[:],  # 共享页帧列表

            is_cow=True

        )



        # 增加引用计数

        for page_id in child_vm.page_frames:

            if page_id is not None:

                self.cow.share_page(page_id)



        child = COWProcess(pid=self.pid + 1, vm=child_vm, cow_manager=self.cow)

        return child



    def write_byte(self, va_offset: int, value: int) -> bool:

        """

        写入虚拟地址（模拟page fault触发COW）

        """

        if va_offset >= self.vm.size:

            return False



        # 找到对应的物理页

        page_index = va_offset // self.cow.PAGE_SIZE

        if page_index >= len(self.vm.page_frames):

            return False



        page_id = self.vm.page_frames[page_index]

        if page_id is None:

            # 页未分配

            page_id = self.cow.allocate_page()

            if page_id is None:

                return False

            self.vm.page_frames[page_index] = page_id



        # 检查是否需要COW

        page = self.cow.pages[page_id]

        if self.vm.is_cow and page.ref_count > 1:

            # 触发COW复制

            new_page_id = self.cow.unshare_page(page_id)

            if new_page_id is None:

                return False

            self.vm.page_frames[page_index] = new_page_id

            page_id = new_page_id



        # 执行写入

        page_offset = va_offset % self.cow.PAGE_SIZE

        return self.cow.write_page(page_id, page_offset, bytes([value]))





if __name__ == "__main__":

    print("=== Copy-On-Write 演示 ===")



    cow_manager = CopyOnWriteManager(num_pages=32)



    # 创建初始进程

    vm = VirtualMemoryArea(

        start_addr=0x1000,

        size=8192,  # 2个页

        page_frames=[None, None]

    )

    parent = COWProcess(pid=1, vm=vm, cow_manager=cow_manager)



    # 写入初始化数据

    print("=== 父进程写入初始化数据 ===")

    parent.write_byte(0, ord('H'))

    parent.write_byte(1, ord('i'))

    parent.write_byte(4096, ord('P'))

    print("父进程写入: 'H', 'i', 'P'")



    # 查看物理页状态

    print(f"页面0 ref_count: {cow_manager.pages[vm.page_frames[0]].ref_count}")

    print(f"页面1 ref_count: {cow_manager.pages[vm.page_frames[1]].ref_count}")



    # fork子进程

    print("\n=== Fork子进程 ===")

    child = parent.fork_from(parent)

    print(f"子进程PID: {child.pid}")



    # 检查引用计数（应为2）

    print(f"\nfork后页面ref_count: {cow_manager.pages[vm.page_frames[0]].ref_count}")



    # 子进程读取（不触发COW）

    print("\n=== 子进程读取 ===")

    print(f"子进程读取页面0: {chr(cow_manager.pages[child.vm.page_frames[0]].data[0])}")



    # 子进程写入（触发COW）

    print("\n=== 子进程写入（触发COW）===")

    child.write_byte(0, ord('C'))

    print(f"写入'C'到页面0偏移0")



    # 检查结果

    print(f"\n页面0状态:")

    print(f"  父进程页面: {chr(cow_manager.pages[vm.page_frames[0]].data[0])}")

    if child.vm.page_frames[0] != vm.page_frames[0]:

        print(f"  子进程独立页面: {chr(cow_manager.pages[child.vm.page_frames[0]].data[0])}")



    # 验证COW

    parent_page = cow_manager.pages[vm.page_frames[0]]

    child_page = cow_manager.pages[child.vm.page_frames[0]]

    print(f"\n验证COW:")

    print(f"  父进程页面ref={parent_page.ref_count}, 内容='{chr(parent_page.data[0])}'")

    print(f"  子进程页面ref={child_page.ref_count}, 内容='{chr(child_page.data[0])}'")

