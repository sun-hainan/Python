# -*- coding: utf-8 -*-

"""

算法实现：数据库算法 / buffer_pool



本文件实现 buffer_pool 相关的算法功能。

"""



import time

from typing import Dict, Optional, List, Set, Tuple

from collections import OrderedDict

from dataclasses import dataclass, field

import threading





@dataclass

class Page:

    """数据页"""

    page_id: int  # 页ID

    data: bytes = b''  # 页数据

    pin_count: int = 0  # 被钉住（pin）的次数

    dirty: bool = False  # 是否脏页（被修改）

    ref_count: int = 0  # 访问计数

    last_access: float = 0.0  # 上次访问时间

    first_access: float = 0.0  # 首次访问时间

    



class BufferPool:

    """

    缓冲池管理器

    

    参数:

        pool_size: 缓冲池大小（页数）

        page_size: 页大小（字节）

        algorithm: 置换算法 ('LRU', 'CLOCK', 'LRU-K')

    """

    

    def __init__(self, pool_size: int = 100, page_size: int = 4096, algorithm: str = 'LRU'):

        self.pool_size = pool_size  # 最大页数

        self.page_size = page_size  # 页大小

        self.algorithm = algorithm  # 置换算法

        

        # 页表：page_id -> page对象

        self.page_table: Dict[int, Page] = {}

        

        # 空闲页列表

        self.free_pages: List[int] = []

        

        # 脏页列表（需要写回的页）

        self.dirty_pages: Set[int] = set()

        

        # 统计

        self.hits = 0

        self.misses = 0

        self.writes = 0

        self.reads = 0

        

        # 线程锁

        self.lock = threading.Lock()

        

        # LRU链表（OrderedDict实现）

        self.lru_list: OrderedDict[int, None] = OrderedDict()

        

        # Clock算法状态

        self.clock_hand = 0  # 时钟指针

        self.page_refs: Dict[int, bool] = {}  # 引用位

    

    def _allocate_page_id(self) -> int:

        """分配页ID"""

        return len(self.page_table)

    

    def fetch_page(self, page_id: int) -> Optional[Page]:

        """

        获取页面

        

        步骤：

        1. 检查页表

        2. 如果命中，更新LRU，返回页面

        3. 如果未命中，选择牺牲页，加载新页

        """

        with self.lock:

            # 1. 页表命中

            if page_id in self.page_table:

                self.hits += 1

                page = self.page_table[page_id]

                page.pin_count += 1

                page.last_access = time.time()

                

                # 更新LRU位置

                if self.algorithm == 'LRU':

                    if page_id in self.lru_list:

                        del self.lru_list[page_id]

                    self.lru_list[page_id] = None

                

                return page

            

            # 2. 页表未命中

            self.misses += 1

            

            # 检查缓冲池是否已满

            if len(self.page_table) >= self.pool_size:

                # 需要置换

                victim_id = self._select_victim()

                if victim_id is not None:

                    self._evict_page(victim_id)

            

            # 分配新页

            page = self._load_page(page_id)

            if page is not None:

                self.page_table[page_id] = page

                

                # 添加到LRU

                if self.algorithm == 'LRU':

                    self.lru_list[page_id] = None

                

                # 更新引用位

                self.page_refs[page_id] = True

            

            return page

    

    def _select_victim(self) -> Optional[int]:

        """

        选择牺牲页

        

        返回:

            牺牲页ID，或None（无可置换页）

        """

        if self.algorithm == 'LRU':

            return self._select_victim_lru()

        elif self.algorithm == 'CLOCK':

            return self._select_victim_clock()

        else:

            return self._select_victim_lru()

    

    def _select_victim_lru(self) -> Optional[int]:

        """LRU置换：选择最久未使用的页"""

        while self.lru_list:

            page_id, _ = self.lru_list.popitem(last=False)  # 最旧的

            page = self.page_table.get(page_id)

            

            if page is None:

                continue

            

            # 如果页被pin住，不能置换

            if page.pin_count > 0:

                # 放回，继续找下一个

                self.lru_list[page_id] = None

                continue

            

            return page_id

        

        return None

    

    def _select_victim_clock(self) -> Optional[int]:

        """

        Clock置换算法（Second Chance）

        """

        n = len(self.page_table)

        if n == 0:

            return None

        

        attempts = 0

        while attempts < n * 2:  # 防止无限循环

            page_id = list(self.page_table.keys())[self.clock_hand % n]

            self.clock_hand += 1

            

            page = self.page_table[page_id]

            

            if page.pin_count > 0:

                # 被pin住，跳过

                attempts += 1

                continue

            

            if self.page_refs.get(page_id, False):

                # 引用位为1，清除并跳过

                self.page_refs[page_id] = False

                attempts += 1

                continue

            

            # 引用位为0，选择为牺牲页

            return page_id

        

        return None

    

    def _evict_page(self, page_id: int) -> bool:

        """

        驱逐页面

        如果是脏页，先写回磁盘

        """

        page = self.page_table.get(page_id)

        if page is None:

            return True

        

        # 如果是脏页，需要写回

        if page.dirty:

            self._write_page_to_disk(page)

            self.writes += 1

        

        # 从页表移除

        del self.page_table[page_id]

        self.dirty_pages.discard(page_id)

        self.page_refs.pop(page_id, None)

        

        return True

    

    def _load_page(self, page_id: int) -> Optional[Page]:

        """

        从磁盘加载页面

        简化实现：生成模拟数据

        """

        self.reads += 1

        

        # 模拟从磁盘读取

        page = Page(

            page_id=page_id,

            data=b'0' * self.page_size,  # 模拟数据

            pin_count=1,

            dirty=False,

            ref_count=1,

            last_access=time.time(),

            first_access=time.time()

        )

        

        return page

    

    def _write_page_to_disk(self, page: Page) -> None:

        """写页面到磁盘（简化实现）"""

        # 实际应该调用存储引擎的写入接口

        page.dirty = False

    

    def unpin_page(self, page_id: int, dirty: bool = False) -> bool:

        """

        解除页面的pin

        dirty=True表示页面被修改

        """

        with self.lock:

            page = self.page_table.get(page_id)

            if page is None:

                return False

            

            page.pin_count = max(0, page.pin_count - 1)

            

            if dirty:

                page.dirty = True

                self.dirty_pages.add(page_id)

            

            # 更新引用位

            self.page_refs[page_id] = True

            

            return True

    

    def mark_dirty(self, page_id: int) -> bool:

        """标记页面为脏"""

        with self.lock:

            page = self.page_table.get(page_id)

            if page is None:

                return False

            page.dirty = True

            self.dirty_pages.add(page_id)

            return True

    

    def flush_page(self, page_id: int) -> bool:

        """强制将页面写回磁盘"""

        with self.lock:

            page = self.page_table.get(page_id)

            if page is None:

                return False

            

            if page.dirty:

                self._write_page_to_disk(page)

                self.writes += 1

                page.dirty = False

                self.dirty_pages.discard(page_id)

            

            return True

    

    def flush_all(self) -> int:

        """将所有脏页写回磁盘"""

        with self.lock:

            count = 0

            for page_id in list(self.dirty_pages):

                page = self.page_table.get(page_id)

                if page and page.dirty:

                    self._write_page_to_disk(page)

                    page.dirty = False

                    count += 1

            

            self.writes += count

            self.dirty_pages.clear()

            return count

    

    def get_buffer_stats(self) -> dict:

        """获取缓冲池统计"""

        total = self.hits + self.misses

        hit_rate = self.hits / total if total > 0 else 0.0

        

        return {

            'pool_size': self.pool_size,

            'pages_used': len(self.page_table),

            'hits': self.hits,

            'misses': self.misses,

            'hit_rate': hit_rate,

            'reads': self.reads,

            'writes': self.writes,

            'dirty_pages': len(self.dirty_pages)

        }

    

    def reset_stats(self) -> None:

        """重置统计"""

        self.hits = 0

        self.misses = 0

        self.reads = 0

        self.writes = 0





class LRU_K_BufferPool(BufferPool):

    """

    LRU-K缓冲池

    

    LRU-K跟踪每个页面的最后K次访问时间，

    选择倒数第K次访问时间最远的页面作为牺牲页。

    对循环访问模式更鲁棒。

    """

    

    def __init__(self, pool_size: int = 100, page_size: int = 4096, k: int = 2):

        super().__init__(pool_size, page_size, algorithm='LRU-K')

        self.k = k  # K值

        self.access_history: Dict[int, List[float]] = {}  # 访问历史

    

    def _select_victim_lru_k(self) -> Optional[int]:

        """LRU-K置换：选择倒数第K次访问时间最远的页"""

        candidates = []

        

        for page_id, history in self.access_history.items():

            if len(history) >= self.k:

                # 有K次访问历史，使用倒数第K次

                candidates.append((history[-self.k], page_id))

            elif len(history) > 0:

                # 不足K次，使用首次访问

                candidates.append((history[0], page_id))

        

        if not candidates:

            # 没有足够的访问历史，使用LRU

            return super()._select_victim_lru()

        

        # 选择最久远的

        candidates.sort()

        return candidates[0][1]

    

    def fetch_page(self, page_id: int) -> Optional[Page]:

        """获取页面并记录访问历史"""

        page = super().fetch_page(page_id)

        

        if page is not None:

            # 记录访问时间

            if page_id not in self.access_history:

                self.access_history[page_id] = []

            

            self.access_history[page_id].append(time.time())

            

            # 只保留最近K次

            if len(self.access_history[page_id]) > self.k:

                self.access_history[page_id] = self.access_history[page_id][-self.k:]

        

        return page





# ==================== 测试代码 ====================

if __name__ == "__main__":

    import random

    

    print("=" * 50)

    print("缓冲池管理测试")

    print("=" * 50)

    

    # 创建缓冲池

    pool = BufferPool(pool_size=10, algorithm='LRU')

    

    # 测试基本功能

    print("\n--- 基本功能测试 ---")

    

    # 访问页面

    for i in range(15):

        page = pool.fetch_page(i)

        if page:

            print(f"fetch_page({i}): page_id={page.page_id}, pin_count={page.pin_count}")

            pool.unpin_page(i)

    

    stats = pool.get_buffer_stats()

    print(f"\n缓冲池统计: {stats}")

    print(f"命中率: {stats['hit_rate']:.2%}")

    

    # 测试脏页

    print("\n--- 脏页测试 ---")

    

    page = pool.fetch_page(5)

    if page:

        pool.mark_dirty(5)

        pool.unpin_page(5, dirty=True)

    

    print(f"脏页列表: {pool.dirty_pages}")

    

    # 测试置换

    print("\n--- 页面置换测试 ---")

    

    pool.reset_stats()

    

    # 顺序访问，触发置换

    for i in range(20):

        page = pool.fetch_page(i * 2)  # 偶数页

        if page:

            pool.unpin_page(i * 2)

    

    stats = pool.get_buffer_stats()

    print(f"置换后统计: {stats}")

    print(f"命中页: {list(pool.page_table.keys())}")

    

    # Clock算法测试

    print("\n--- Clock算法测试 ---")

    

    clock_pool = BufferPool(pool_size=5, algorithm='CLOCK')

    

    for i in range(10):

        page = clock_pool.fetch_page(i)

        if page:

            clock_pool.unpin_page(i)

    

    stats = clock_pool.get_buffer_stats()

    print(f"Clock算法统计: {stats}")

    

    # LRU-K测试

    print("\n--- LRU-K测试 ---")

    

    lru_k_pool = LRU_K_BufferPool(pool_size=5, k=2)

    

    # 循环访问模式

    for _ in range(3):

        for i in range(5):

            page = lru_k_pool.fetch_page(i)

            if page:

                lru_k_pool.unpin_page(i)

    

    stats = lru_k_pool.get_buffer_stats()

    print(f"LRU-K统计: {stats}")

    print(f"保留页: {list(lru_k_pool.page_table.keys())}")

    

    # 性能测试

    print("\n--- 性能测试 ---")

    

    import time

    

    large_pool = BufferPool(pool_size=1000, algorithm='LRU')

    n_ops = 100000

    

    start = time.time()

    for i in range(n_ops):

        page_id = random.randint(0, 10000)

        page = large_pool.fetch_page(page_id)

        if page:

            large_pool.unpin_page(page_id, dirty=random.random() < 0.1)

    elapsed = time.time() - start

    

    print(f"操作数: {n_ops}")

    print(f"耗时: {elapsed:.3f}秒")

    print(f"吞吐: {n_ops/elapsed:.0f} ops/s")

    

    stats = large_pool.get_buffer_stats()

    print(f"命中率: {stats['hit_rate']:.2%}")

