# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构 / cache_coherence_mesi



本文件实现 cache_coherence_mesi 相关的算法功能。

"""



from enum import Enum

from typing import Dict, Optional, List, Set

from dataclasses import dataclass, field





class MESICacheLineState(Enum):

    """MESI缓存行状态"""

    MODIFIED = "M"  # 已修改（脏）

    EXCLUSIVE = "E"  # 独占

    SHARED = "S"  # 共享

    INVALID = "I"  # 无效





class MOESICacheLineState(Enum):

    """MOESI缓存行状态"""

    MODIFIED = "M"

    EXCLUSIVE = "E"

    SHARED = "S"

    INVALID = "I"

    OWNED = "O"  # Owned：当前缓存拥有此行，已脏，其他缓存可能有共享副本





@dataclass

class CacheLine:

    """缓存行"""

    state: MESICacheLineState

    tag: int

    data: Optional[bytes] = None

    address: int = 0





class CacheController:

    """

    缓存一致性控制器

    处理MESI协议的消息和状态转换

    """



    def __init__(self, cache_id: int, cache_size: int, line_size: int = 64):

        self.cache_id = cache_id

        self.cache_size = cache_size

        self.line_size = line_size

        self.num_lines = cache_size // line_size



        # 缓存数组（简化：直接映射）

        self.cache: Dict[int, CacheLine] = {}



        # 事件日志

        self.events: List[str] = []



    def _get_index(self, address: int) -> int:

        """获取缓存索引"""

        return (address // self.line_size) % self.num_lines



    def _get_tag(self, address: int) -> int:

        """获取缓存标签"""

        return address // self.line_size



    def _get_line_addr(self, address: int) -> int:

        """获取缓存行地址（对齐后）"""

        return (address // self.line_size) * self.line_size



    def read(self, address: int) -> Optional[bytes]:

        """

        读取缓存行

        return: 数据或None（缓存未命中）

        """

        tag = self._get_tag(address)

        index = self._get_index(address)



        if index in self.cache:

            line = self.cache[index]

            if line.tag == tag and line.state != MESICacheLineState.INVALID:

                self.events.append(f"C{self.cache_id}: 命中 0x{address:X}")

                return line.data

            elif line.state == MESICacheLineState.MODIFIED:

                # 需要写回内存（模拟）

                self.events.append(f"C{self.cache_id}: 写回 0x{address:X} (Modified)")

        return None



    def write(self, address: int, data: bytes) -> bool:

        """

        写缓存行

        return: 是否成功

        """

        tag = self._get_tag(address)

        index = self._get_index(address)



        if index in self.cache:

            line = self.cache[index]

            if line.state != MESICacheLineState.INVALID:

                # 如果是Shared，需要发送Invalidate到其他缓存

                self.events.append(f"C{self.cache_id}: Invalidate 0x{address:X}")

        return True



    def invalidate(self, address: int):

        """使缓存行无效"""

        tag = self._get_tag(address)

        index = self._get_index(address)



        if index in self.cache:

            line = self.cache[index]

            if line.tag == tag:

                line.state = MESICacheLineState.INVALID

                self.events.append(f"C{self.cache_id}: Invalidate 0x{address:X}")



    def update_line(self, address: int, data: bytes, state: MESICacheLineState):

        """更新缓存行"""

        tag = self._get_tag(address)

        index = self._get_index(address)

        self.cache[index] = CacheLine(state=state, tag=tag, data=data, address=self._get_line_addr(address))

        self.events.append(f"C{self.cache_id}: 更新行 0x{address:X} -> {state.value}")



    def get_state(self, address: int) -> Optional[str]:

        """获取缓存行状态"""

        tag = self._get_tag(address)

        index = self._get_index(address)

        if index in self.cache:

            line = self.cache[index]

            if line.tag == tag:

                return line.state.value

        return None





class MESICoherenceController:

    """

    MESI一致性控制器



    处理来自CPU和总线的一致性请求。

    在真实系统中，这些消息通过侦听总线(snooping)传递。

    """



    def __init__(self, cache: CacheController):

        self.cache = cache

        self.pending_requests: List[Dict] = []



    def handle_read_miss(self, address: int) -> str:

        """

        处理读未命中

        需要从内存或其他缓存获取数据

        return: 状态转换描述

        """

        current_state = self.cache.get_state(address)

        if current_state is None:

            # 缓存行不存在（无效）

            return f"ReadMiss -> GetS (从内存/其他缓存获取Shared行)"



        # 当前有有效行

        if current_state == "M":

            # Modified状态：需要先写回，然后提供数据

            return f"ReadMiss (Modified) -> WriteBack + GetS"

        elif current_state == "E":

            # Exclusive -> Shared

            self.cache.invalidate(address)

            return f"ReadMiss (Exclusive) -> Shared"

        elif current_state == "S":

            return f"ReadMiss (Shared) -> 保持Shared"

        return "ReadMiss -> GetS"



    def handle_write_miss(self, address: int) -> str:

        """

        处理写未命中

        return: 状态转换描述

        """

        current_state = self.cache.get_state(address)

        if current_state is None:

            return f"WriteMiss -> GetM (获取独占行)"

        return f"WriteMiss -> GetM"



    def handle_write_hit(self, address: int) -> str:

        """

        处理写命中

        return: 状态转换描述

        """

        current_state = self.cache.get_state(address)

        if current_state == "M":

            return f"WriteHit (Modified) -> 保持Modified"

        elif current_state == "E":

            # Exclusive -> Modified（无需总线操作）

            return f"WriteHit (Exclusive) -> Modified"

        elif current_state == "S":

            # Shared -> Modified（需要Invalidate其他缓存）

            self.cache.invalidate(address)

            return f"WriteHit (Shared) -> Modified (Invalidate其他缓存)"





class SnoopyBus:

    """

    侦听总线 (Snoopy Bus)

    所有缓存控制器连接到此总线，侦听所有总线事务

    """



    def __init__(self):

        self.caches: List[CacheController] = []

        self.memory: Dict[int, bytes] = {}  # 模拟内存

        self.transactions: List[Dict] = []



    def add_cache(self, cache: CacheController):

        """添加缓存到总线"""

        self.caches.append(cache)



    def broadcast_read_miss(self, requester_id: int, address: int):

        """广播读未命中请求"""

        self.transactions.append({

            'type': 'ReadMiss',

            'requester': requester_id,

            'address': address

        })



    def broadcast_write_miss(self, requester_id: int, address: int):

        """广播写未命中请求"""

        self.transactions.append({

            'type': 'WriteMiss',

            'requester': requester_id,

            'address': address

        })



    def snoop(self, address: int) -> List[Dict]:

        """

        侦听指定地址的事务

        返回所有持有该地址有效副本的缓存

        """

        holders = []

        for cache in self.caches:

            state = cache.get_state(address)

            if state and state != "I":

                holders.append({

                    'cache_id': cache.cache_id,

                    'state': state

                })

        return holders





class MOESICacheLine:

    """MOESI缓存行"""

    def __init__(self):

        self.state = MOESICacheLineState.INVALID

        self.tag = 0

        self.data: Optional[bytes] = None

        self.address = 0

        self.dirty = False





class MOESICoherenceController:

    """

    MOESI一致性控制器



    相比MESI，Owned状态允许在提供数据时保留本地副本，

    减少写回内存的次数。

    """



    def __init__(self, cache_id: int):

        self.cache_id = cache_id

        self.cache: Dict[int, MOESICacheLine] = {}

        self.events: List[str] = []



    def _get_index(self, address: int, num_lines: int, line_size: int = 64) -> int:

        return (address // line_size) % num_lines



    def get_line(self, address: int, num_lines: int = 16) -> Optional[MOESICacheLine]:

        """获取缓存行"""

        index = self._get_index(address, num_lines)

        return self.cache.get(index)



    def set_line(self, address: int, state: MOESICacheLineState, data: bytes = None, num_lines: int = 16):

        """设置缓存行"""

        index = self._get_index(address, num_lines)

        if index not in self.cache:

            self.cache[index] = MOESICacheLine()

        self.cache[index].state = state

        self.cache[index].tag = address // 64

        self.cache[index].address = (address // 64) * 64

        if data:

            self.cache[index].data = data

        self.events.append(f"C{self.cache_id}: 行0x{address:X} -> {state.value}")



    def handle_bus_read(self, address: int) -> str:

        """处理总线读请求"""

        line = self.get_line(address)

        if line is None:

            return "Miss -> 从内存获取"



        state = line.state

        if state == MOESICacheLineState.MODIFIED:

            # Modified: 切换到Owned状态，提供数据

            line.state = MOESICacheLineState.OWNED

            line.dirty = True

            return f"Modified -> Owned (提供数据给总线)"

        elif state == MOESICacheLineState.EXCLUSIVE:

            # Exclusive -> Shared

            line.state = MOESICacheLineState.SHARED

            return "Exclusive -> Shared"

        elif state == MOESICacheLineState.SHARED:

            return "保持Shared"

        elif state == MOESICacheLineState.OWNED:

            return "保持Owned (提供数据给总线)"

        return "Invalid -> Miss"



    def handle_bus_write(self, address: int) -> str:

        """处理总线写请求（写无效）"""

        line = self.get_line(address)

        if line is None:

            return "Miss"



        if line.state != MOESICacheLineState.INVALID:

            line.state = MOESICacheLineState.INVALID

            return f"Invalidate (状态={line.state.value} -> Invalid)"

        return "保持Invalid"



    def read(self, address: int) -> bool:

        """本地读，返回是否命中"""

        line = self.get_line(address)

        if line and line.state != MOESICacheLineState.INVALID:

            return True

        return False



    def write(self, address: int) -> bool:

        """本地写，返回是否需要获取独占权"""

        line = self.get_line(address)

        if line and line.state == MOESICacheLineState.EXCLUSIVE:

            line.state = MOESICacheLineState.MODIFIED

            return True

        elif line and line.state == MOESICacheLineState.SHARED:

            # 需要发送Invalidate

            return False

        return False





def simulate_mesi_protocol():

    """

    模拟MESI缓存一致性协议

    """

    print("=" * 60)

    print("MESI 缓存一致性协议模拟")

    print("=" * 60)



    # 创建两个缓存控制器

    cache0 = CacheController(cache_id=0, cache_size=1024)

    cache1 = CacheController(cache_id=1, cache_size=1024)



    # 创建总线

    bus = SnoopyBus()

    bus.add_cache(cache0)

    bus.add_cache(cache1)



    # 创建MESI控制器

    mesi0 = MESICoherenceController(cache0)

    mesi1 = MESICoherenceController(cache1)



    address = 0x1000



    print("\n初始状态:")

    print(f"  地址 0x{address:X} 在两个缓存中都不存在")



    print("\n场景1: CPU0 读取地址 0x{address:X}".format(address=address))

    result = mesi0.handle_read_miss(address)

    print(f"  -> {result}")

    cache0.update_line(address, b"data0", MESICacheLineState.EXCLUSIVE)

    print(f"  -> CPU0缓存行状态: {cache0.get_state(address)}")



    print("\n场景2: CPU1 读取相同地址")

    result = mesi1.handle_read_miss(address)

    print(f"  -> {result}")

    print(f"  -> CPU0: {cache0.get_state(address)}")

    print(f"  -> CPU1: {cache1.get_state(address)}")



    print("\n场景3: CPU0 写入地址 0x{address:X}".format(address=address))

    result = mesi0.handle_write_hit(address)

    print(f"  -> {result}")

    print(f"  -> CPU0: {cache0.get_state(address)}")

    print(f"  -> CPU1: {cache1.get_state(address)}")



    print("\n场景4: CPU1 读取被修改的地址")

    result = mesi1.handle_read_miss(address)

    print(f"  -> {result}")

    print(f"  -> CPU0: {cache0.get_state(address)}")

    print(f"  -> CPU1: {cache1.get_state(address)}")



    print("\n" + "=" * 60)

    print("MOESI 状态转换")

    print("=" * 60)



    moesi = MOESICoherenceController(cache_id=0)



    print("\nMOESI状态转换演示:")

    print("-" * 50)



    addr = 0x2000

    transitions = [

        ("CPU读未命中", lambda: moesi.handle_bus_read(addr)),

        ("CPU写命中(Exclusive)", lambda: (moesi.set_line(addr, MOESICacheLineState.EXCLUSIVE), moesi.handle_bus_write(addr))),

        ("另一个CPU总线读", lambda: moesi.handle_bus_read(addr)),

    ]



    for name, action in transitions:

        result = action()

        if isinstance(result, tuple):

            result = result[1]

        print(f"  {name}: {result}")





if __name__ == "__main__":

    simulate_mesi_protocol()

