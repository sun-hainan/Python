# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / vacuum_garbage



本文件实现 vacuum_garbage 相关的算法功能。

"""



import time

import threading

from dataclasses import dataclass, field

from typing import Dict, List, Set, Tuple, Optional, Callable

from enum import Enum

from heapq import heappush, heappop





class GCPhase(Enum):

    """GC阶段"""

    IDLE = "idle"  # 空闲

    VACUUM_SCAN = "scan"  # 扫描阶段

    VACUUM_CLEAN = "clean"  # 清理阶段

    VACUUM_ANALYZE = "analyze"  # 分析阶段





@dataclass

class HeapPage:

    """堆页结构"""

    page_id: int  # 页ID

    tuples: List['DeadTuple'] = field(default_factory=list)  # 元组列表

    free_space: int = 8192  # 空闲空间(字节)

    is_dirty: bool = False  # 是否脏页





@dataclass

class DeadTuple:

    """死元组"""

    tuple_id: Tuple[int, int]  # (page_id, offset)

    xmin: int  # 插入事务ID

    xmax: Optional[int] = None  # 删除事务ID

    created_at: float = field(default_factory=time.time)  # 创建时间

    deleted_at: Optional[float] = None  # 删除时间

    is_visible: bool = False  # 是否对当前事务可见





@dataclass

class VacuumResult:

    """VACUUM执行结果"""

    pages_scanned: int = 0  # 扫描页数

    dead_tuples_removed: int = 0  # 删除的死元组数

    pages_freed: int = 0  # 释放的页数

    pages_reclaimed: int = 0  # 重用的页数

    analyze_time: float = 0  # 分析耗时

    duration_ms: float = 0  # 总耗时





class VacuumGarbageCollector:

    """

    VACUUM垃圾回收器



    功能:

    1. 标识死元组(Xmax已提交且无活跃事务可见)

    2. 清理过期版本，更新空闲空间

    3. 更新表统计信息

    4. 可选: 重建页面，整理堆

    """



    def __init__(self, autovacuum_threshold: float = 0.1):

        self.pages: Dict[int, HeapPage] = {}  # page_id -> HeapPage

        self.dead_tuples: List[DeadTuple] = []  # 死元组列表(堆)

        self.active_transactions: Set[int] = set()  # 活跃事务ID集合

        self.min_txid: int = 1  # 最小活跃事务ID

        self.autovacuum_threshold = autovacuum_threshold  # 自动VACUUM阈值

        self.phase = GCPhase.IDLE

        self.lock = threading.RLock()

        self.stats = {

            "total_vacuum_runs": 0,

            "total_dead_tuples": 0,

            "total_pages_freed": 0

        }



    def register_page(self, page: HeapPage):

        """注册一个堆页"""

        with self.lock:

            self.pages[page.page_id] = page



    def add_tuple(self, page_id: int, tuple_data: DeadTuple):

        """添加元组到指定页面"""

        with self.lock:

            if page_id not in self.pages:

                self.pages[page_id] = HeapPage(page_id=page_id)

            self.pages[page_id].tuples.append(tuple_data)

            self.pages[page_id].is_dirty = True



    def mark_tuple_deleted(self, tuple_id: Tuple[int, int], deleting_tx: int):

        """标记元组被删除"""

        with self.lock:

            page_id, offset = tuple_id

            if page_id in self.pages:

                for t in self.pages[page_id].tuples:

                    if t.tuple_id == tuple_id:

                        t.xmax = deleting_tx

                        t.deleted_at = time.time()

                        # 加入死元组堆(按删除时间排序)

                        heappush(self.dead_tuples, t)

                        break



    def set_active_transactions(self, tx_ids: Set[int]):

        """设置当前活跃事务集合"""

        with self.lock:

            self.active_transactions = tx_ids

            self.min_txid = min(tx_ids) if tx_ids else 0



    def is_tuple_visible(self, tuple_data: DeadTuple) -> bool:

        """

        判断元组是否对任何活跃事务可见

        可见性规则:

        1. xmax未提交 -> 不可见删除

        2. xmax已提交且xmax对当前事务不可见 -> 可见

        3. xmax已提交且xmax对当前事务可见 -> 不可见删除

        """

        if tuple_data.xmax is None:

            return True  # 未删除，总是可见



        if tuple_data.xmax in self.active_transactions:

            return False  # 删除事务仍活跃



        return False  # xmax已提交,删除生效



    def vacuum_page(self, page: HeapPage) -> Tuple[List[DeadTuple], int]:

        """

        清理单个页面的死元组



        返回:

            (移除的死元组列表, 重用空间字节数)

        """

        dead_removed = []

        space_reclaimed = 0



        # 遍历页面中的所有元组

        alive_tuples = []

        for t in page.tuples:

            if t in self.dead_tuples:

                # 检查是否真正死亡

                if self.is_tuple_dead(t):

                    dead_removed.append(t)

                    space_reclaimed += 100  # 假设每元组100字节

                    self.stats["total_dead_tuples"] += 1

                else:

                    alive_tuples.append(t)

            else:

                alive_tuples.append(t)



        page.tuples = alive_tuples

        page.free_space += space_reclaimed

        page.is_dirty = True

        return dead_removed, space_reclaimed



    def is_tuple_dead(self, tuple_data: DeadTuple) -> bool:

        """判断元组是否已死亡(可回收)"""

        # 条件1: 有删除事务

        if tuple_data.xmax is None:

            return False



        # 条件2: 删除事务已提交

        if tuple_data.xmax in self.active_transactions:

            return False



        # 条件3: 插入事务已提交

        if tuple_data.xmin in self.active_transactions:

            return False



        return True



    def execute_vacuum(self, target_pages: Optional[List[int]] = None) -> VacuumResult:

        """

        执行VACUUM操作



        参数:

            target_pages: 要清理的页面列表, None表示清理所有页面



        返回:

            VacuumResult: 执行结果统计

        """

        start_time = time.time()

        result = VacuumResult()



        with self.lock:

            self.phase = GCPhase.VACUUM_SCAN

            pages_to_vacuum = target_pages or list(self.pages.keys())



            # 阶段1: 扫描标识死元组

            for page_id in pages_to_vacuum:

                if page_id not in self.pages:

                    continue

                result.pages_scanned += 1



                # 清理单个页面

                dead_removed, space = self.vacuum_page(self.pages[page_id])

                result.dead_tuples_removed += len(dead_removed)

                result.pages_reclaimed += 1



            self.phase = GCPhase.VACUUM_CLEAN



            # 阶段2: 释放完全空闲的页面

            for page_id in pages_to_vacuum:

                if page_id in self.pages:

                    page = self.pages[page_id]

                    if len(page.tuples) == 0 and page.free_space >= 8192:

                        # 页面完全空闲,可以释放

                        del self.pages[page_id]

                        result.pages_freed += 1

                        self.stats["total_pages_freed"] += 1



            self.phase = GCPhase.VACUUM_ANALYZE



            # 阶段3: 更新统计信息(简化版)

            result.analyze_time = time.time() - start_time

            result.duration_ms = (time.time() - start_time) * 1000



            self.phase = GCPhase.IDLE

            self.stats["total_vacuum_runs"] += 1



        return result



    def get_fragmentation_ratio(self) -> float:

        """计算表碎片化程度"""

        with self.lock:

            if not self.pages:

                return 0.0



            total_pages = len(self.pages)

            total_free = sum(p.free_space for p in self.pages.values())

            max_free = total_pages * 8192



            # 碎片化 = 1 - (实际空闲 / 最大空闲)

            return 1.0 - (total_free / max_free) if max_free > 0 else 0.0



    def should_autovacuum(self) -> bool:

        """判断是否应该触发自动VACUUM"""

        fragmentation = self.get_fragmentation_ratio()

        return fragmentation > self.autovacuum_threshold



    def print_stats(self):

        """打印VACUUM统计信息"""

        print("=== VACUUM 统计信息 ===")

        print(f"  总运行次数: {self.stats['total_vacuum_runs']}")

        print(f"  清理死元组数: {self.stats['total_dead_tuples']}")

        print(f"  释放页面数: {self.stats['total_pages_freed']}")

        print(f"  碎片化程度: {self.get_fragmentation_ratio():.2%}")

        print(f"  活跃事务数: {len(self.active_transactions)}")

        print(f"  阶段: {self.phase.value}")





if __name__ == "__main__":

    gc = VacuumGarbageCollector(autovacuum_threshold=0.2)



    # 模拟创建页面和元组

    print("=== 初始化数据 ===")

    for i in range(5):

        page = HeapPage(page_id=i, free_space=8192)

        for j in range(10):

            t = DeadTuple(

                tuple_id=(i, j),

                xmin=100 + i * 10 + j,

                xmax=None if j % 3 == 0 else 105 + i * 10

            )

            page.tuples.append(t)

        gc.register_page(page)



    # 打印初始状态

    for pid, page in gc.pages.items():

        print(f"Page {pid}: {len(page.tuples)} tuples, free={page.free_space}B")



    # 设置活跃事务(模拟事务101已提交, 105,106活跃)

    gc.set_active_transactions({105, 106, 107})



    print("\n=== 执行VACUUM ===")

    # 标记一些元组已死亡

    gc.mark_tuple_deleted((0, 1), 101)  # page0 tuple1被事务101删除

    gc.mark_tuple_deleted((1, 2), 103)  # page1 tuple2被事务103删除



    result = gc.execute_vacuum()

    print(f"扫描页数: {result.pages_scanned}")

    print(f"删除死元组: {result.dead_tuples_removed}")

    print(f"释放页数: {result.pages_freed}")

    print(f"耗时: {result.duration_ms:.2f}ms")



    # 打印清理后状态

    print("\n=== VACUUM后状态 ===")

    for pid, page in gc.pages.items():

        print(f"Page {pid}: {len(page.tuples)} tuples, free={page.free_space}B")



    gc.print_stats()



    # 测试碎片化检测

    print(f"\n碎片化程度: {gc.get_fragmentation_ratio():.2%}")

    print(f"需要自动VACUUM: {'是' if gc.should_autovacuum() else '否'}")

