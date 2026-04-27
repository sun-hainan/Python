# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构 / cache_write_policies



本文件实现 cache_write_policies 相关的算法功能。

"""



from typing import Dict, List, Optional, Set

from dataclasses import dataclass





@dataclass

class CacheLineData:

    """缓存行数据"""

    tag: int

    data: bytes

    valid: bool = False

    dirty: bool = False  # 是否被修改（用于Write-back）

    last_used: int = 0   # 上次使用时间（用于LRU）





class CacheWritePolicy:

    """缓存写策略基类"""



    def __init__(self, num_sets: int, associativity: int, line_size: int = 64):

        self.num_sets = num_sets

        self.associativity = associativity

        self.line_size = line_size

        self.cache: Dict[int, List[Optional[CacheLineData]]] = {

            i: [None] * associativity for i in range(num_sets)

        }

        self.hits = 0

        self.misses = 0

        self.memory_writes = 0  # 写回内存的次数

        self.total_memory_traffic = 0



    def _get_set_index(self, address: int) -> int:

        return (address // self.line_size) % self.num_sets



    def _get_tag(self, address: int) -> int:

        return address // (self.line_size * self.num_sets)



    def _find_in_cache(self, address: int) -> tuple:

        """查找缓存中是否有此地址"""

        set_idx = self._get_set_index(address)

        tag = self._get_tag(address)



        for way_idx, line in enumerate(self.cache[set_idx]):

            if line and line.tag == tag and line.valid:

                return (set_idx, way_idx, line)

        return (set_idx, -1, None)



    def _find_victim(self, set_idx: int) -> int:

        """找替换候选（简单LRU）"""

        lines = self.cache[set_idx]

        # 找无效行或使用LRU

        for way_idx, line in enumerate(lines):

            if line is None or not line.valid:

                return way_idx

        # 所有行都有效，使用LRU（第一个）

        return 0



    def read(self, address: int) -> bool:

        """读缓存"""

        set_idx, way_idx, line = self._find_in_cache(address)

        if way_idx >= 0:

            self.hits += 1

            line.last_used += 1

            return True

        self.misses += 1

        return False



    def write(self, address: int, data: bytes) -> bool:

        """写缓存"""

        raise NotImplementedError



    def get_stats(self) -> Dict:

        return {

            'hits': self.hits,

            'misses': self.misses,

            'hit_rate': self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0,

            'memory_writes': self.memory_writes,

            'total_traffic': self.total_memory_traffic

        }





class WriteThroughNoAllocate(CacheWritePolicy):

    """

    Write-through + No-write-allocate



    特点：

    - 每次写同时更新缓存和内存

    - 写未命中直接写内存，不加载到缓存

    - 简单但内存流量大

    """



    def __init__(self, num_sets: int, associativity: int, line_size: int = 64):

        super().__init__(num_sets, associativity, line_size)



    def write(self, address: int, data: bytes) -> bool:

        """写操作"""

        set_idx, way_idx, line = self._find_in_cache(address)



        if way_idx >= 0:

            # 写命中：更新缓存和内存

            line.data = data

            line.dirty = False  # WT不需要跟踪脏

            line.last_used += 1

            self.hits += 1

        else:

            # 写未命中：直接写内存（No-write-allocate）

            self.misses += 1



        # 每次写都写内存

        self.memory_writes += 1

        self.total_memory_traffic += 1



        return way_idx >= 0





class WriteThroughWriteAllocate(CacheWritePolicy):

    """

    Write-through + Write-allocate



    特点：

    - 每次写同时更新缓存和内存

    - 写未命中时，先加载到缓存，再写入

    - 减少后续对同一位置的写内存流量

    """



    def __init__(self, num_sets: int, associativity: int, line_size: int = 64):

        super().__init__(num_sets, associativity, line_size)



    def write(self, address: int, data: bytes) -> bool:

        """写操作"""

        set_idx, way_idx, line = self._find_in_cache(address)



        if way_idx >= 0:

            # 写命中

            line.data = data

            line.dirty = False

            line.last_used += 1

            self.hits += 1

        else:

            # 写未命中：分配新行

            self.misses += 1

            victim_way = self._find_victim(set_idx)



            # 如果被替换的行是脏的，需要写回

            old_line = self.cache[set_idx][victim_way]

            if old_line and old_line.dirty:

                self.memory_writes += 1

                self.total_memory_traffic += 1



            # 加载新行（实际应从内存读，这里简化）

            new_line = CacheLineData(

                tag=self._get_tag(address),

                data=data,

                valid=True,

                dirty=False,

                last_used=1

            )

            self.cache[set_idx][victim_way] = new_line



        # 写内存

        self.memory_writes += 1

        self.total_memory_traffic += 1



        return way_idx >= 0





class WriteBackWriteAllocate(CacheWritePolicy):

    """

    Write-back + Write-allocate (这是现代CPU最常用的组合)



    特点：

    - 写只更新缓存，不立即写内存

    - 脏行在被替换时才写回内存

    - 减少内存流量，提高性能

    """



    def __init__(self, num_sets: int, associativity: int, line_size: int = 64):

        super().__init__(num_sets, associativity, line_size)



    def write(self, address: int, data: bytes) -> bool:

        """写操作"""

        set_idx, way_idx, line = self._find_in_cache(address)



        if way_idx >= 0:

            # 写命中：只更新缓存，标记脏

            line.data = data

            line.dirty = True

            line.last_used += 1

            self.hits += 1

            # 不写内存

        else:

            # 写未命中：分配新行

            self.misses += 1

            victim_way = self._find_victim(set_idx)



            # 如果被替换的行是脏的，需要写回

            old_line = self.cache[set_idx][victim_way]

            if old_line and old_line.dirty:

                self.memory_writes += 1

                self.total_memory_traffic += 1



            # 分配新行

            new_line = CacheLineData(

                tag=self._get_tag(address),

                data=data,

                valid=True,

                dirty=True,  # 新写入的数据是脏的

                last_used=1

            )

            self.cache[set_idx][victim_way] = new_line



        return way_idx >= 0





class WriteBackNoAllocate(CacheWritePolicy):

    """

    Write-back + No-write-allocate



    特点：

    - 写未命中直接写内存

    - 理论上存在但实际很少用

    - 浪费已加载的缓存行（如果后续读）

    """



    def __init__(self, num_sets: int, associativity: int, line_size: int = 64):

        super().__init__(num_sets, associativity, line_size)



    def write(self, address: int, data: bytes) -> bool:

        """写操作"""

        set_idx, way_idx, line = self._find_in_cache(address)



        if way_idx >= 0:

            # 写命中：只更新缓存

            line.data = data

            line.dirty = True

            line.last_used += 1

            self.hits += 1

        else:

            # 写未命中：直接写内存，不分配

            self.misses += 1

            self.memory_writes += 1

            self.total_memory_traffic += 1



        return way_idx >= 0





class MemorySystem:

    """

    完整内存系统模拟



    追踪缓存和内存之间的数据传输，

    包括读分配、写回等操作。

    """



    def __init__(self, cache: CacheWritePolicy, memory_size: int = 4096):

        self.cache = cache

        self.memory_size = memory_size

        self.memory: Dict[int, bytes] = {}

        self.memory_writes = 0

        self.memory_reads = 0



    def memory_read(self, address: int, size: int = 64) -> bytes:

        """从内存读取"""

        self.memory_reads += 1

        if address not in self.memory:

            self.memory[address] = b'\x00' * size

        return self.memory[address]



    def memory_write(self, address: int, data: bytes):

        """写内存"""

        self.memory_writes += 1

        self.cache.memory_writes += 1

        self.cache.total_memory_traffic += 1

        self.memory[address] = data



    def read_with_allocation(self, address: int) -> bool:

        """

        读操作（带读分配）

        如果未命中，从内存加载

        """

        hit = self.cache.read(address)

        if not hit:

            # 读分配：从内存加载

            set_idx = self.cache._get_set_index(address)

            tag = self.cache._get_tag(address)

            victim_way = self.cache._find_victim(set_idx)



            old_line = self.cache.cache[set_idx][victim_way]

            if old_line and old_line.dirty:

                self.memory_write(0, old_line.data)  # 写回旧数据



            data = self.memory_read(address)

            self.cache.cache[set_idx][victim_way] = CacheLineData(

                tag=tag, data=data, valid=True, dirty=False

            )

            self.memory_reads += 1

        return hit





def simulate_write_policies():

    """

    模拟各种写策略

    """

    print("=" * 60)

    print("缓存写策略模拟")

    print("=" * 60)



    # 测试序列

    operations = [

        ('R', 0x1000),

        ('R', 0x1000),

        ('W', 0x1000, b'DATA'),

        ('W', 0x1000, b'DATA2'),

        ('R', 0x1000),

        ('W', 0x2000, b'NEWDATA'),

        ('R', 0x2000),

    ]



    policies = [

        ("Write-through + No-allocate", WriteThroughNoAllocate),

        ("Write-through + Write-allocate", WriteThroughWriteAllocate),

        ("Write-back + Write-allocate", WriteBackWriteAllocate),

        ("Write-back + No-allocate", WriteBackNoAllocate),

    ]



    print("\n操作序列:")

    for op in operations:

        if op[0] == 'R':

            print(f"  READ  0x{op[1]:04X}")

        else:

            print(f"  WRITE 0x{op[1]:04X} = {op[2]}")



    print("-" * 60)



    for name, PolicyClass in policies:

        cache = PolicyClass(num_sets=4, associativity=2, line_size=64)

        memory = MemorySystem(cache)



        print(f"\n{name}:")

        for op in operations:

            if op[0] == 'R':

                cache.read(op[1])

                print(f"  READ  0x{op[1]:04X} -> {'命中' if cache.hits else '未命中'}")

            else:

                cache.write(op[1], op[2])

                print(f"  WRITE 0x{op[1]:04X}")



        stats = cache.get_stats()

        print(f"  命中率: {stats['hit_rate']*100:.1f}%")

        print(f"  内存写次数: {stats['memory_writes']}")





if __name__ == "__main__":

    simulate_write_policies()

