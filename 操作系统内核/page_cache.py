# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / page_cache

本文件实现 page_cache 相关的算法功能。
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import threading


class PageState(Enum):
    """页状态"""
    CLEAN = "clean"
    DIRTY = "dirty"
    LOCKED = "locked"
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass
class PageCacheEntry:
    """页缓存条目"""
    page_addr: int           # 页的虚拟地址
    file_inode: int          # 所属inode
    file_offset: int         # 文件内偏移
    state: PageState = PageState.CLEAN
    reference_count: int = 1 # 引用计数
    last_access: float = 0   # 上次访问时间
    dirty_time: float = 0   # 变脏时间
    writeback_index: int = 0  # 回写批次索引


class Inode:
    """inode（简化）"""
    def __init__(self, ino: int):
        self.i_ino = ino
        self.i_size = 0
        self.i_blocks = 0
        self.i_mode = 0
        self.i_mtime = 0
        self.i_ctime = 0

        # 指向页缓存的页
        self.i_pages: Dict[int, PageCacheEntry] = {}  # offset -> page

        # inode标记
        self.i_state = 0  # I_DIRTY, I_DIRTY_DATASYNC, etc.

    def add_page(self, offset: int, page: PageCacheEntry):
        """添加页到inode"""
        self.i_pages[offset] = page


class AddressSpace:
    """
    地址空间对象

    管理一个inode的页缓存。
    """

    def __init__(self, inode: Inode):
        self.inode = inode
        self.pages: Dict[int, PageCacheEntry] = {}  # page_addr -> entry
        self.nrpages = 0

        # 回写控制
        self.writeback_index = 0

    def add_to_page_cache(self, page: PageCacheEntry) -> bool:
        """添加页到页缓存"""
        offset = page.file_offset

        if offset in self.pages:
            return False

        self.pages[page.page_addr] = page
        self.nrpages += 1
        self.inode.add_page(offset, page)

        return True

    def remove_from_page_cache(self, page: PageCacheEntry):
        """从页缓存移除页"""
        if page.page_addr in self.pages:
            del self.pages[page.page_addr]
            self.nrpages -= 1


class PageCache:
    """
    页缓存

    管理所有文件的页缓存。
    使用基数树(radix tree)快速查找。
    """

    def __init__(self, max_pages: int = 1024):
        self.max_pages = max_pages
        self.pages: Dict[int, PageCacheEntry] = {}  # 全局页缓存
        self.page_tree: Dict[Tuple[int, int], int] = {}  # (inode, offset) -> page_addr

        # 统计
        self.total_pages = 0
        self.hit_count = 0
        self.miss_count = 0

        # LRU链表
        self.active_list: List[int] = []  # 活跃页链表
        self.inactive_list: List[int] = []  # 非活跃页链表

    def find_get_page(self, inode: int, offset: int) -> Optional[PageCacheEntry]:
        """查找页（如果不存在返回None）"""
        key = (inode, offset)
        if key in self.page_tree:
            page_addr = self.page_tree[key]
            if page_addr in self.pages:
                page = self.pages[page_addr]
                page.last_access = time.time()
                self.hit_count += 1
                return page

        self.miss_count += 1
        return None

    def add_to_page_cache(self, inode: int, offset: int, page: PageCacheEntry) -> bool:
        """添加页到缓存"""
        key = (inode, offset)

        if key in self.page_tree:
            return False

        self.pages[page.page_addr] = page
        self.page_tree[key] = page.page_addr
        self.total_pages += 1

        # 添加到活跃链表
        self.active_list.append(page.page_addr)

        return True

    def mark_page_dirty(self, page: PageCacheEntry):
        """标记页为脏"""
        page.state = PageState.DIRTY
        page.dirty_time = time.time()
        self.inode_i_state_set(page.file_inode)

    def inode_i_state_set(self, inode_ino: int, state: int = 1):
        """设置inode的脏状态"""
        # 简化
        pass


class DirtyPageWriteback:
    """
    脏页回写

    模拟Linux的pdflush/flush线程的脏页回写机制。
    """

    # 回写模式
    WB_MODE_NONE = 0
    WB_MODE_PERIODIC = 1  # 周期性回写
    WB_MODE_SYNC = 2      # 同步回写
    WB_MODE_BACKGROUND = 3  # 后台回写

    def __init__(self, page_cache: PageCache):
        self.page_cache = page_cache

        # 回写阈值
        self.dirty_ratio = 10  # 脏页比例阈值
        self.dirty_background_ratio = 5  # 后台回写阈值

        # 回写统计
        self.pages_written = 0
        self.writeback_count = 0

        # 脏页计数
        self.nr_dirty = 0
        self.nr_writeback = 0

        # 回写线程
        self.flush_thread_active = False

    def calculate_dirty_ratio(self) -> float:
        """计算脏页比例"""
        if self.page_cache.total_pages == 0:
            return 0.0
        return self.nr_dirty / self.page_cache.total_pages * 100

    def need_writeback(self) -> bool:
        """检查是否需要回写"""
        return self.nr_dirty > self.page_cache.max_pages * self.dirty_ratio / 100

    def writeback_pages(self, mode: int = WB_MODE_BACKGROUND) -> int:
        """
        回写脏页
        return: 回写的页数
        """
        pages_written = 0

        # 查找所有脏页
        dirty_pages = []
        for page_addr, page in self.page_cache.pages.items():
            if page.state == PageState.DIRTY:
                dirty_pages.append(page)

        # 按脏时间排序（先写最老的）
        dirty_pages.sort(key=lambda p: p.dirty_time)

        # 回写
        limit = len(dirty_pages) if mode == WB_MODE_SYNC else 10

        for page in dirty_pages[:limit]:
            # 模拟回写到磁盘
            pages_written += 1
            page.state = PageState.CLEAN
            self.nr_dirty -= 1
            self.nr_writeback += 1

        self.pages_written += pages_written
        self.writeback_count += 1

        return pages_written

    def write_inode(self, inode: Inode, sync: bool = False) -> int:
        """
        写回指定inode的脏页
        """
        pages_written = 0

        for offset, page in inode.i_pages.items():
            if page.state == PageState.DIRTY:
                # 模拟写回
                page.state = PageState.CLEAN
                pages_written += 1
                self.nr_dirty -= 1

        return pages_written

    def start_flush_thread(self):
        """启动回写线程（模拟）"""
        self.flush_thread_active = True
        print("  脏页回写线程已启动")

    def stop_flush_thread(self):
        """停止回写线程"""
        self.flush_thread_active = False
        print("  脏页回写线程已停止")


class FlushDaemon:
    """
    flush守护进程（模拟pdflush）

    Linux使用pdflush线程或更现代的flush线程
    来定期唤醒并回写脏页。
    """

    def __init__(self, writeback: DirtyPageWriteback):
        self.writeback = writeback
        self.daemon_running = False

        # 周期性唤醒间隔（秒）
        self.flush_interval = 5

    def daemon_loop(self):
        """守护进程主循环"""
        print(f"  Flush守护进程启动，回写间隔={self.flush_interval}秒")

        while self.daemon_running:
            # 检查脏页
            if self.writeback.need_writeback():
                pages = self.writeback.writeback_pages(DirtyPageWriteback.WB_MODE_BACKGROUND)
                if pages > 0:
                    print(f"  后台回写: {pages} 页")

            time.sleep(self.flush_interval)

        print("  Flush守护进程退出")

    def start(self):
        """启动守护进程"""
        self.daemon_running = True

    def stop(self):
        """停止守护进程"""
        self.daemon_running = False


def simulate_page_cache():
    """
    模拟页缓存和脏页回写
    """
    print("=" * 60)
    print("页缓存 (Page Cache) 与脏页回写")
    print("=" * 60)

    # 创建页缓存
    page_cache = PageCache(max_pages=100)

    # 创建inode
    inode = Inode(ino=12345)
    inode.i_size = 1024 * 1024  # 1MB

    # 创建地址空间
    address_space = AddressSpace(inode)

    # 创建回写管理器
    writeback = DirtyPageWriteback(page_cache)

    # 模拟文件读取
    print("\n" + "-" * 50)
    print("文件读取（页缓存命中）")
    print("-" * 50)

    # 创建一些页
    for offset in [0, 4096, 8192]:
        page = PageCacheEntry(
            page_addr=0x100000 + offset,
            file_inode=inode.i_ino,
            file_offset=offset,
            state=PageState.CLEAN
        )
        page_cache.add_to_page_cache(inode.i_ino, offset, page)
        address_space.add_to_page_cache(page)

    # 读取（缓存命中）
    print("\n读取文件offset=4096:")
    page = page_cache.find_get_page(inode.i_ino, 4096)
    if page:
        print(f"  缓存命中! page_addr=0x{page.page_addr:08X}")
    else:
        print("  缓存未命中")

    # 模拟文件写入
    print("\n" + "-" * 50)
    print("文件写入（产生脏页）")
    print("-" * 50)

    # 修改页（产生脏页）
    page = page_cache.find_get_page(inode.i_ino, 4096)
    if page:
        page_cache.mark_page_dirty(page)
        writeback.nr_dirty += 1
        print(f"  标记页为脏: offset=4096")
        print(f"  当前脏页数: {writeback.nr_dirty}")

    # 再写入几页
    for offset in [8192, 12288]:
        page = page_cache.find_get_page(inode.i_ino, offset)
        if page:
            page_cache.mark_page_dirty(page)
            writeback.nr_dirty += 1

    print(f"  当前脏页数: {writeback.nr_dirty}")
    print(f"  脏页比例: {writeback.calculate_dirty_ratio():.1f}%")

    # 脏页回写
    print("\n" + "-" * 50)
    print("脏页回写")
    print("-" * 50)

    print(f"\n触发回写: need_writeback={writeback.need_writeback()}")
    pages_written = writeback.writeback_pages(DirtyPageWriteback.WB_MODE_SYNC)
    print(f"  同步回写: {pages_written} 页已写回")
    print(f"  剩余脏页数: {writeback.nr_dirty}")

    # 缓存统计
    print("\n" + "-" * 50)
    print("页缓存统计")
    print("-" * 50)

    total = page_cache.hit_count + page_cache.miss_count
    hit_rate = page_cache.hit_count / total * 100 if total > 0 else 0

    print(f"  总页数: {page_cache.total_pages}")
    print(f"  命中: {page_cache.hit_count}")
    print(f"  未命中: {page_cache.miss_count}")
    print(f"  命中率: {hit_rate:.1f}%")
    print(f"  回写次数: {writeback.writeback_count}")
    print(f"  回写页数: {writeback.pages_written}")

    # LRU链表演示
    print("\n" + "-" * 50)
    print("LRU链表状态")
    print("-" * 50)

    print(f"  活跃链表: {len(page_cache.active_list)} 页")
    print(f"  非活跃链表: {len(page_cache.inactive_list)} 页")


if __name__ == "__main__":
    simulate_page_cache()
