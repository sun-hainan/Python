# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构_2 / load_store_queue



本文件实现 load_store_queue 相关的算法功能。

"""



import random

from typing import List, Optional, Dict, Set

from dataclasses import dataclass, field

from enum import Enum, auto





class LSQ_Entry_State(Enum):

    """LSQ条目状态"""

    PENDING = auto()     # 等待地址计算

    ADDR_CALC = auto()   # 地址计算完成，等待执行

    EXECUTING = auto()   # 正在执行内存操作

    COMPLETED = auto()   # 操作完成

    SQUASHED = auto()    # 被 squash（分支预测失败等）





class Memory_Operation(Enum):

    """内存操作类型"""

    LOAD = auto()

    STORE = auto()





@dataclass

class LSQ_Entry:

    """LSQ条目"""

    id: int = 0                    # 唯一标识

    op_type: Memory_Operation = Memory_Operation.LOAD  # 操作类型

    virtual_addr: int = 0          # 虚拟地址

    physical_addr: int = 0         # 物理地址

    data: Optional[int] = None     # 存储数据（STORE时）

    state: LSQ_Entry_State = LSQ_Entry_State.PENDING

    rob_id: int = -1               # 关联的ROB ID

    pc: int = 0                    # 指令PC

    age: int = 0                   # 年龄（进入顺序）





class Load_Store_Queue:

    """加载/存储队列"""

    def __init__(self, size: int = 16):

        self.size = size                       # LSQ容量

        self.entries: List[Optional[LSQ_Entry]] = [None] * size

        self.head: int = 0                     # 最老条目指针

        self.tail: int = 0                     # 最新条目指针

        self.count: int = 0                    # 当前条目数

        self.next_id: int = 0                   # 下一个分配ID

        # 数据缓存（模拟L1 Dcache）

        self.data_cache: Dict[int, int] = {}

        # 统计

        self.store_forward_count: int = 0      # 存储转发次数

        self.ld_lu_count: int = 0              # Load-Load冲突次数

        self.ld_st_count: int = 0             # Load-Store冲突次数





    def is_full(self) -> bool:

        """判断LSQ是否已满"""

        return self.count >= self.size





    def is_empty(self) -> bool:

        """判断LSQ是否为空"""

        return self.count == 0





    def _advance(self, idx: int) -> int:

        """环形缓冲索引前进"""

        return (idx + 1) % self.size





    def enqueue_load(self, virtual_addr: int, rob_id: int, pc: int) -> Optional[int]:

        """入队一条LOAD指令"""

        if self.is_full():

            return None

        entry = LSQ_Entry(

            id=self.next_id,

            op_type=Memory_Operation.LOAD,

            virtual_addr=virtual_addr,

            rob_id=rob_id,

            pc=pc,

            age=self.count

        )

        self.next_id += 1

        self.entries[self.tail] = entry

        self.tail = self._advance(self.tail)

        self.count += 1

        return entry.id





    def enqueue_store(self, virtual_addr: int, data: int, rob_id: int, pc: int) -> Optional[int]:

        """入队一条STORE指令"""

        if self.is_full():

            return None

        entry = LSQ_Entry(

            id=self.next_id,

            op_type=Memory_Operation.STORE,

            virtual_addr=virtual_addr,

            data=data,

            rob_id=rob_id,

            pc=pc,

            age=self.count

        )

        self.next_id += 1

        self.entries[self.tail] = entry

        self.tail = self._advance(self.tail)

        self.count += 1

        return entry.id





    def get_older_loads(self, entry_id: int) -> List[LSQ_Entry]:

        """获取比给定条目更老的所有LOAD（用于消歧检查）"""

        result = []

        idx = self.head

        while idx != self.tail:

            e = self.entries[idx]

            if e is not None and e.id != entry_id and e.op_type == Memory_Operation.LOAD and e.age < entry_id if hasattr(entry_id, 'age') else True:

                # 注意：这里entry_id是整数的简单比较，实际应比较age

                result.append(e)

            idx = self._advance(idx)

        return result





    def check_store_to_load_forwarding(self, load_entry: LSQ_Entry) -> Optional[int]:

        """

        检查是否能进行存储转发（Store-to-Load Forwarding）

        如果LSQ中更早的STORE已经计算出地址且匹配，则直接转发其数据

        """

        idx = self.head

        while idx != self.tail:

            e = self.entries[idx]

            if e is not None:

                if e.op_type == Memory_Operation.STORE:

                    if e.state == LSQ_Entry_State.PENDING:

                        # STORE还未计算地址，无法转发

                        pass

                    elif e.virtual_addr == load_entry.virtual_addr:

                        # 地址匹配，可以转发

                        if e.data is not None:

                            self.store_forward_count += 1

                            return e.data

                        elif e.state == LSQ_Entry_State.COMPLETED:

                            # STORE已写入缓存

                            self.store_forward_count += 1

                            return self.data_cache.get(e.virtual_addr)

                elif e.op_type == Memory_Operation.LOAD and e.id != load_entry.id:

                    if e.age < load_entry.age:

                        self.ld_ld_check(e, load_entry)

            idx = self._advance(idx)

        return None





    def ld_ld_check(self, older: LSQ_Entry, younger: LSQ_Entry):

        """Load-Load冲突检测"""

        if older.virtual_addr == younger.virtual_addr:

            self.ld_lu_count += 1

            # 检测到乱序执行

            return True

        return False





    def execute_load(self, entry_id: int) -> Optional[int]:

        """执行LOAD：查找数据或转发"""

        idx = self.head

        while idx != self.tail:

            e = self.entries[idx]

            if e is not None and e.id == entry_id:

                # 尝试存储转发

                data = self.check_store_to_load_forwarding(e)

                if data is None:

                    # 从缓存读取

                    data = self.data_cache.get(e.virtual_addr, 0)

                e.state = LSQ_Entry_State.COMPLETED

                return data

            idx = self._advance(idx)

        return None





    def execute_store(self, entry_id: int) -> bool:

        """执行STORE：将数据写入缓存"""

        idx = self.head

        while idx != self.tail:

            e = self.entries[idx]

            if e is not None and e.id == entry_id:

                if e.data is not None:

                    self.data_cache[e.virtual_addr] = e.data

                    e.state = LSQ_Entry_State.COMPLETED

                    return True

            idx = self._advance(idx)

        return False





    def dequeue(self) -> Optional[LSQ_Entry]:

        """按顺序退役（只退役已完成的最老指令）"""

        while self.count > 0:

            e = self.entries[self.head]

            if e is not None and e.state == LSQ_Entry_State.COMPLETED:

                self.entries[self.head] = None

                self.head = self._advance(self.head)

                self.count -= 1

                return e

            elif e is not None and e.state == LSQ_Entry_State.SQUASHED:

                # 跳过已squash的条目

                self.entries[self.head] = None

                self.head = self._advance(self.head)

                self.count -= 1

            else:

                break

        return None





    def squash(self, rob_id: int):

        """Squash所有 rob_id 之后的条目"""

        idx = self.head

        while idx != self.tail:

            e = self.entries[idx]

            if e is not None and e.rob_id >= rob_id:

                e.state = LSQ_Entry_State.SQUASHED

            idx = self._advance(idx)





def basic_test():

    """基本功能测试"""

    print("=== LSQ模拟器测试 ===")

    lsq = Load_Store_Queue(size=16)

    print(f"LSQ容量: {lsq.size}")

    # 入队一些内存操作

    print("\n入队操作:")

    ld1 = lsq.enqueue_load(virtual_addr=0x1000, rob_id=1, pc=0x100)

    st1 = lsq.enqueue_store(virtual_addr=0x1000, data=42, rob_id=2, pc=0x104)

    ld2 = lsq.enqueue_load(virtual_addr=0x1000, rob_id=3, pc=0x108)

    st2 = lsq.enqueue_store(virtual_addr=0x2000, data=100, rob_id=4, pc=0x10C)

    ld3 = lsq.enqueue_load(virtual_addr=0x2000, rob_id=5, pc=0x110)

    print(f"  LD1(id={ld1}): addr=0x1000")

    print(f"  ST1(id={st1}): addr=0x1000, data=42")

    print(f"  LD2(id={ld2}): addr=0x1000")

    print(f"  ST2(id={st2}): addr=0x2000, data=100")

    print(f"  LD3(id={ld3}): addr=0x2000")

    # 执行STORE

    print("\n执行STORE:")

    lsq.execute_store(st1)

    lsq.execute_store(st2)

    # 执行LOAD（测试存储转发）

    print("\n执行LOAD（测试存储转发）:")

    data_ld2 = lsq.execute_load(ld2)

    print(f"  LD2执行: 收到转发数据 {data_ld2}")

    # 执行LD1（已完成的STORE转发）

    data_ld1 = lsq.execute_load(ld1)

    print(f"  LD1执行: 收到转发数据 {data_ld1}")

    # 执行LD3

    data_ld3 = lsq.execute_load(ld3)

    print(f"  LD3执行: 收到转发数据 {data_ld3}")

    print(f"\n统计:")

    print(f"  存储转发次数: {lsq.store_forward_count}")

    print(f"  Load-Load冲突: {lsq.ld_lu_count}")

    print(f"  Load-Store冲突: {lsq.ld_st_count}")





if __name__ == "__main__":

    basic_test()

