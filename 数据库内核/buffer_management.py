# -*- coding: utf-8 -*-
"""
算法实现：数据库内核 / buffer_management

本文件实现 buffer_management 相关的算法功能。
"""

from typing import Dict, List, Optional, Any, Tuple
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
import time

@dataclass
class Page:
    """缓冲区页"""
    page_id: int           # 页ID
    table_name: str = ""   # 所属表
    data: Any = None       # 页数据
    is_dirty: bool = False  # 是否脏页（被修改）
    pin_count: int = 0     # 钉住计数（正在被使用的页不能驱逐）
    ref_count: int = 0     # 访问次数（用于LFU）
    last_access_time: float = field(default_factory=time.time)  # 上次访问时间
    
    def __repr__(self):
        status = "DIRTY" if self.is_dirty else "CLEAN"
        return f"Page(id={self.page_id}, pin={self.pin_count}, {status})"


class BufferPool:
    """缓冲区池基础类"""
    def __init__(self, pool_size: int):
        self.pool_size = pool_size          # 缓冲池大小（页数）
        self.pages: Dict[int, Page] = {}    # 页ID -> Page对象
        self.hit_count = 0                   # 命中次数
        self.miss_count = 0                  # 未命中次数
    
    def access(self, page_id: int) -> Optional[Page]:
        """访问页"""
        if page_id in self.pages:
            self.hit_count += 1
            return self.pages[page_id]
        else:
            self.miss_count += 1
            return None
    
    def hit_rate(self) -> float:
        """命中率"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0


class LRU_KBuffer(BufferPool):
    """
    LRU-K缓冲区管理算法
    记录每页最近K次访问时间，驱逐最久未被访问K次的页
    LRU-1就是经典LRU
    """
    
    def __init__(self, pool_size: int, k: int = 2):
        super().__init__(pool_size)
        self.k = k                              # K值
        self.access_history: Dict[int, List[float]] = {}  # 每页的访问历史
    
    def record_access(self, page_id: int) -> Page:
        """记录页的访问"""
        current_time = time.time()
        
        if page_id not in self.pages:
            # 页不在缓冲池中，需要加载
            page = self._load_page(page_id)
            self.pages[page_id] = page
            self.access_history[page_id] = []
        
        page = self.pages[page_id]
        
        # 记录访问时间
        if page_id not in self.access_history:
            self.access_history[page_id] = []
        
        self.access_history[page_id].append(current_time)
        
        # 只保留最近K次访问
        if len(self.access_history[page_id]) > self.k:
            self.access_history[page_id].pop(0)
        
        page.last_access_time = current_time
        return page
    
    def _load_page(self, page_id: int) -> Page:
        """模拟从磁盘加载页"""
        # 找到牺牲页
        if len(self.pages) >= self.pool_size:
            self._evict_page()
        
        page = Page(page_id=page_id, data=f"data_for_page_{page_id}")
        return page
    
    def _evict_page(self) -> Optional[Page]:
        """驱逐LRU-K页"""
        # 找到K次访问中最旧的页
        best_page_id = None
        oldest_time = float('inf')
        
        for pid, history in self.access_history.items():
            if pid in self.pages:
                page = self.pages[pid]
                if page.pin_count == 0 and len(history) > 0:
                    # 该页有K次访问记录，取最早的
                    if history[0] < oldest_time:
                        oldest_time = history[0]
                        best_page_id = pid
        
        # 如果没有找到有K次访问的页，fallback到LRU-1
        if best_page_id is None:
            for pid in self.pages:
                page = self.pages[pid]
                if page.pin_count == 0:
                    if page.last_access_time < oldest_time:
                        oldest_time = page.last_access_time
                        best_page_id = pid
        
        if best_page_id:
            return self._remove_page(best_page_id)
        
        return None
    
    def _remove_page(self, page_id: int) -> Optional[Page]:
        """移除页"""
        if page_id in self.pages:
            page = self.pages.pop(page_id)
            self.access_history.pop(page_id, None)
            return page
        return None
    
    def pin_page(self, page_id: int) -> Optional[Page]:
        """钉住页（增加pin_count）"""
        page = self.record_access(page_id)
        page.pin_count += 1
        return page
    
    def unpin_page(self, page_id: int):
        """解除钉住"""
        if page_id in self.pages:
            self.pages[page_id].pin_count = max(0, self.pages[page_id].pin_count - 1)


class CLOCKBuffer(BufferPool):
    """
    CLOCK算法（Second-Chance二次机会）
    环形链表+引用位，模拟LRU但更低开销
    """
    
    def __init__(self, pool_size: int):
        super().__init__(pool_size)
        self.pages_list: List[Page] = []      # 所有页的列表（顺序即为环形）
        self.ref_bits: Dict[int, bool] = {}   # 引用位
        self.clock_hand: int = 0               # 时钟指针
    
    def record_access(self, page_id: int) -> Page:
        """记录页的访问，设置引用位"""
        if page_id not in self.pages:
            page = self._load_page(page_id)
            self.pages[page_id] = page
            self.pages_list.append(page)
            self.ref_bits[page_id] = True
        
        self.ref_bits[page_id] = True
        self.pages[page_id].last_access_time = time.time()
        
        return self.pages[page_id]
    
    def _load_page(self, page_id: int) -> Page:
        """加载页"""
        if len(self.pages) >= self.pool_size:
            self._evict_with_clock()
        
        page = Page(page_id=page_id, data=f"data_{page_id}")
        return page
    
    def _evict_with_clock(self) -> Optional[Page]:
        """使用CLOCK算法驱逐页"""
        checked = 0
        max_checks = len(self.pages_list) * 2  # 最多检查两轮
        
        while checked < max_checks:
            current = self.pages_list[self.clock_hand]
            
            # 检查引用位
            if self.ref_bits.get(current.page_id, False):
                # 有引用，清除引用位，给二次机会
                self.ref_bits[current.page_id] = False
            else:
                # 无引用，可以驱逐（如果没有被钉住）
                if current.pin_count == 0:
                    self.pages.pop(current.page_id)
                    self.pages_list[self.clock_hand] = Page(
                        page_id=-1  # 标记为空槽
                    )
                    self.clock_hand = (self.clock_hand + 1) % len(self.pages_list)
                    return current
            
            # 时钟指针前进
            self.clock_hand = (self.clock_hand + 1) % len(self.pages_list)
            checked += 1
        
        return None  # 无法驱逐（所有页都被钉住）
    
    def pin_page(self, page_id: int) -> Optional[Page]:
        page = self.record_access(page_id)
        page.pin_count += 1
        return page
    
    def unpin_page(self, page_id: int):
        if page_id in self.pages:
            self.pages[page_id].pin_count = max(0, 
                                                self.pages[page_id].pin_count - 1)


class LFUBuffer(BufferPool):
    """
    LFU（Least Frequently Used）缓冲区管理
    驱逐访问频率最低的页
    """
    
    def __init__(self, pool_size: int):
        super().__init__(pool_size)
        self.frequency: Dict[int, int] = {}  # 页ID -> 访问频率
    
    def record_access(self, page_id: int) -> Page:
        """记录页的访问，增加频率计数"""
        if page_id not in self.pages:
            page = self._load_page(page_id)
            self.pages[page_id] = page
            self.frequency[page_id] = 0
        
        page = self.pages[page_id]
        self.frequency[page_id] += 1
        page.ref_count = self.frequency[page_id]
        page.last_access_time = time.time()
        
        return page
    
    def _load_page(self, page_id: int) -> Page:
        if len(self.pages) >= self.pool_size:
            self._evict_lfu_page()
        
        return Page(page_id=page_id, data=f"data_{page_id}")
    
    def _evict_lfu_page(self) -> Optional[Page]:
        """驱逐频率最低的页"""
        if not self.frequency:
            return None
        
        # 找到频率最低的页
        min_freq_pid = min(self.frequency, key=self.frequency.get)
        page = self.pages.get(min_freq_pid)
        
        if page and page.pin_count == 0:
            self.pages.pop(min_freq_pid)
            self.frequency.pop(min_freq_pid)
            return page
        
        return None
    
    def pin_page(self, page_id: int) -> Optional[Page]:
        page = self.record_access(page_id)
        page.pin_count += 1
        return page


if __name__ == "__main__":
    import random
    
    # 测试数据
    page_ids = [1, 2, 3, 4, 5, 1, 2, 6, 1, 3, 7, 1, 8, 2, 9]
    
    print("=" * 60)
    print("缓冲区管理算法演示")
    print("=" * 60)
    
    for name, cls in [("LRU-2", lambda: LRU_KBuffer(4, k=2)),
                       ("CLOCK", lambda: CLOCKBuffer(4)),
                       ("LFU", lambda: LFUBuffer(4))]:
        print(f"\n--- {name} 算法 ---")
        buffer = cls()
        
        for page_id in page_ids[:10]:
            page = buffer.access(page_id)
            if page is None:
                # 页不在缓冲池，模拟加载
                buffer.pages[page_id] = Page(page_id=page_id)
            buffer.record_access(page_id)
            print(f"访问页 {page_id}, 缓冲池状态: {[p.page_id for p in buffer.pages.values()]}")
        
        print(f"命中率: {buffer.hit_rate():.2%}")
