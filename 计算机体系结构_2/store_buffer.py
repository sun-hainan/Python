# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构_2 / store_buffer



本文件实现 store_buffer 相关的算法功能。

"""



import random

from typing import List, Optional, Dict, Set

from dataclasses import dataclass, field

from enum import Enum, auto





class Store_Buffer_Entry_State(Enum):

    """存储缓冲条目状态"""

    PENDING = auto()      # 等待地址和数据就绪

    ADDR_READY = auto()   # 地址就绪，等待数据

    READY = auto()        # 地址和数据都就绪，等待提交

    COMMITTED = auto()    # 已提交到内存

    SQUASHED = auto()     # 被取消





@dataclass

class Store_Buffer_Entry:

    """存储缓冲条目"""

    id: int = 0                       # 唯一标识

    virtual_addr: int = 0            # 虚拟地址

    physical_addr: int = 0           # 物理地址

    data: Optional[int] = None       # 存储数据

    state: Store_Buffer_Entry_State = Store_Buffer_Entry_State.PENDING

    rob_id: int = -1                 # 关联的ROB ID

    pc: int = 0                      # 指令PC

    age: int = 0                     # 年龄（程序顺序）





class Store_Buffer:

    """存储缓冲（Store Buffer）"""

    def __init__(self, size: int = 16):

        self.size = size                       # 缓冲容量

        self.entries: List[Optional[Store_Buffer_Entry]] = [None] * size

        self.head: int = 0                     # 头部（最早提交）

        self.tail: int = 0                     # 尾部（最新入队）

        self.count: int = 0

        self.next_id: int = 0

        # 内存（模拟主存）

        self.memory: Dict[int, int] = {}

        # 统计

        self.store_count: int = 0

        self.forward_count: int = 0

        self.memory_write_count: int = 0





    def is_full(self) -> bool:

        """存储缓冲是否已满"""

        return self.count >= self.size





    def is_empty(self) -> bool:

        """存储缓冲是否为空"""

        return self.count == 0





    def _advance(self, idx: int) -> int:

        """环形索引前进"""

        return (idx + 1) % self.size





    def enqueue(self, virtual_addr: int, data: int, rob_id: int, pc: int) -> Optional[int]:

        """入队一条STORE指令"""

        if self.is_full():

            return None

        entry = Store_Buffer_Entry(

            id=self.next_id,

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

        self.store_count += 1

        return entry.id





    def update_addr(self, entry_id: int, physical_addr: int):

        """更新STORE的物理地址"""

        for i in range(self.size):

            e = self.entries[i]

            if e is not None and e.id == entry_id:

                e.physical_addr = physical_addr

                if e.data is not None:

                    e.state = Store_Buffer_Entry_State.READY

                else:

                    e.state = Store_Buffer_Entry_State.ADDR_READY

                break





    def update_data(self, entry_id: int, data: int):

        """更新STORE的数据"""

        for i in range(self.size):

            e = self.entries[i]

            if e is not None and e.id == entry_id:

                e.data = data

                if e.physical_addr != 0:

                    e.state = Store_Buffer_Entry_State.READY

                break





    def find_forwarding(self, load_addr: int) -> Optional[int]:

        """

        查找是否有STORE可以转发给这个LOAD

        存储转发规则：找到地址匹配的最老的STORE

        """

        # 从最老的开始查找

        idx = self.head

        found_entry: Optional[Store_Buffer_Entry] = None

        while idx != self.tail:

            e = self.entries[idx]

            if e is not None and e.state == Store_Buffer_Entry_State.READY:

                if e.virtual_addr == load_addr:

                    # 找到匹配的STORE

                    if found_entry is None or e.age < found_entry.age:

                        found_entry = e

            idx = self._advance(idx)

        if found_entry is not None:

            self.forward_count += 1

            return found_entry.data

        return None





    def commit_ready(self) -> List[Store_Buffer_Entry]:

        """返回所有准备好提交的STORE（按顺序）"""

        ready = []

        idx = self.head

        while idx != self.tail:

            e = self.entries[idx]

            if e is not None and e.state == Store_Buffer_Entry_State.READY:

                ready.append(e)

            idx = self._advance(idx)

        return ready





    def commit(self, entry_id: int) -> bool:

        """提交一条STORE到内存"""

        for i in range(self.size):

            e = self.entries[i]

            if e is not None and e.id == entry_id:

                # 写入内存

                self.memory[e.physical_addr] = e.data

                e.state = Store_Buffer_Entry_State.COMMITTED

                self.memory_write_count += 1

                # 从缓冲移除

                self.entries[i] = None

                self.count -= 1

                return True

        return False





    def squash_from(self, rob_id: int):

        """Squash所有 rob_id 之后的STORE"""

        idx = self.head

        while idx != self.tail:

            e = self.entries[idx]

            if e is not None and e.rob_id >= rob_id:

                e.state = Store_Buffer_Entry_State.SQUASHED

            idx = self._advance(idx)





class Load_Unit:

    """加载单元（与Store Buffer配合）"""

    def __init__(self, store_buffer: Store_Buffer):

        self.store_buffer = store_buffer

        self.l1_dcache_hit_count: int = 0

        self.l1_dcache_miss_count: int = 0





    def execute_load(self, load_addr: int) -> int:

        """执行LOAD：先尝试存储转发，再访问缓存/内存"""

        # 1. 尝试从Store Buffer转发

        forwarded_data = self.store_buffer.find_forwarding(load_addr)

        if forwarded_data is not None:

            return forwarded_data

        # 2. 检查L1 DCache（模拟）

        if random.random() < 0.8:  # 80%命中率

            self.l1_dcache_hit_count += 1

            return self.store_buffer.memory.get(load_addr, random.randint(1, 100))

        else:

            self.l1_dcache_miss_count += 1

            # 模拟从内存加载

            mem_value = self.store_buffer.memory.get(load_addr, random.randint(1, 100))

            self.store_buffer.memory[load_addr] = mem_value

            return mem_value





def basic_test():

    """基本功能测试"""

    print("=== Store Buffer 模拟器测试 ===")

    sb = Store_Buffer(size=16)

    print(f"Store Buffer容量: {sb.size}")

    # 入队一些STORE

    print("\n入队STORE:")

    stores = [

        (0x1000, 42),

        (0x1004, 100),

        (0x2000, 200),

        (0x1000, 999),  # 覆盖0x1000

    ]

    store_ids = []

    for i, (addr, data) in enumerate(stores):

        sid = sb.enqueue(addr, data, rob_id=i+1, pc=0x1000 + i*4)

        store_ids.append(sid)

        sb.update_addr(sid, addr)  # 假设地址已计算

        print(f"  STORE_{sid}: addr=0x{addr:x}, data={data}")

    # 提交第一个STORE

    print("\n提交STORE:")

    if store_ids:

        sb.commit(store_ids[0])

        print(f"  提交 STORE_{store_ids[0]}")

    # 模拟LOAD（测试存储转发）

    print("\n执行LOAD（测试存储转发）:")

    lu = Load_Unit(sb)

    load_tests = [0x1000, 0x1004, 0x2000, 0x3000]

    for addr in load_tests:

        data = lu.execute_load(addr)

        print(f"  LOAD addr=0x{addr:x}: data={data}")

    print(f"\n统计:")

    print(f"  STORE总数: {sb.store_count}")

    print(f"  存储转发次数: {sb.forward_count}")

    print(f"  内存写次数: {sb.memory_write_count}")

    print(f"  L1 DCache命中: {lu.l1_dcache_hit_count}")

    print(f"  L1 DCache未命中: {lu.l1_dcache_miss_count}")





if __name__ == "__main__":

    basic_test()

