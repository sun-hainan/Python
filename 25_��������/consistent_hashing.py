# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / consistent_hashing



本文件实现 consistent_hashing 相关的算法功能。

"""



import hashlib

import bisect

from typing import List, Dict, Tuple, Optional





class KetamaHash:

    """

    Ketama一致性哈希实现

    

    特点：

    - 使用MD5哈希（均匀分布）

    - 每物理节点对应160虚拟节点

    - 环上有2^32个槽点

    """

    

    def __init__(self, nodes: List[str] = None, virtual_nodes: int = 160):

        """

        初始化Ketama哈希

        

        Args:

            nodes: 初始节点列表

            virtual_nodes: 每个物理节点的虚拟节点数

        """

        self.virtual_nodes = virtual_nodes  # 每个物理节点的虚拟节点数

        self.ring = []  # 排序后的环：[(hash_value, node_name), ...]

        self.ring_hash = []  # 环上的哈希值列表，用于二分查找

        self.node_vnodes = {}  # node_name -> [vnode_hashes]

        

        if nodes:

            for node in nodes:

                self.add_node(node)

    

    def _compute_hash(self, key: str) -> int:

        """

        计算MD5哈希值

        

        Args:

            key: 要哈希的字符串

        

        Returns:

            32位无符号整数

        """

        md5 = hashlib.md5(key.encode('utf-8')).digest()

        return int.from_bytes(md5[:4], byteorder='big')

    

    def add_node(self, node: str):

        """

        添加物理节点

        

        Args:

            node: 节点标识符

        """

        if node in self.node_vnodes:

            return  # 节点已存在

        

        # 为该节点创建虚拟节点

        self.node_vnodes[node] = []

        

        for i in range(self.virtual_nodes):

            # 虚拟节点名称 = "node-name:vnoder-index"

            vnode_name = f"{node}:{i}"

            vnode_hash = self._compute_hash(vnode_name)

            

            # 添加到环上

            bisect.insort(self.ring, (vnode_hash, node))

            self.ring_hash.append(vnode_hash)

            self.node_vnodes[node].append(vnode_hash)

    

    def remove_node(self, node: str):

        """

        移除物理节点

        

        Args:

            node: 节点标识符

        """

        if node not in self.node_vnodes:

            return

        

        # 移除该节点所有虚拟节点

        for vnode_hash in self.node_vnodes[node]:

            idx = bisect.bisect_left(self.ring, (vnode_hash, node))

            if idx < len(self.ring):

                self.ring.pop(idx)

            

            hash_idx = bisect.bisect_left(self.ring_hash, vnode_hash)

            if hash_idx < len(self.ring_hash):

                self.ring_hash.pop(hash_idx)

        

        del self.node_vnodes[node]

    

    def get_node(self, key: str) -> Optional[str]:

        """

        根据key获取负责的节点

        

        Args:

            key: 数据键

        

        Returns:

            节点标识符

        """

        if not self.ring:

            return None

        

        key_hash = self._compute_hash(key)

        

        # 二分查找：找到第一个 >= key_hash 的位置

        idx = bisect.bisect_left(self.ring_hash, key_hash)

        

        # 如果超过环尾，循环到环首

        if idx >= len(self.ring_hash):

            idx = 0

        

        return self.ring[idx][1]

    

    def get_nodes(self, key: str, replicas: int = 1) -> List[str]:

        """

        根据key获取多个节点（用于备份）

        

        Args:

            key: 数据键

            replicas: 副本数量

        

        Returns:

            节点列表

        """

        if not self.ring:

            return []

        

        key_hash = self._compute_hash(key)

        idx = bisect.bisect_left(self.ring_hash, key_hash)

        

        nodes = []

        seen_nodes = set()

        

        while len(nodes) < replicas and len(seen_nodes) < len(self.ring):

            if idx >= len(self.ring):

                idx = 0

            

            node = self.ring[idx][1]

            if node not in seen_nodes:

                nodes.append(node)

                seen_nodes.add(node)

            

            idx += 1

        

        return nodes

    

    def get_distribution(self) -> Dict[str, float]:

        """

        获取节点数据分布统计

        

        Returns:

            node_name -> 百分比

        """

        if not self.ring:

            return {}

        

        total = len(self.ring)

        distribution = {}

        

        for node in self.node_vnodes:

            count = len(self.node_vnodes[node])

            distribution[node] = (count / total) * 100

        

        return distribution





class MaglevHash:

    """

    Maglev一致性哈希实现

    

    特点：

    - 使用查找表实现O(1)查找

    - 更适合高并发场景

    - 论文"Maglev: A Fast and Reliable Software Network Load Balancer"

    """

    

    def __init__(self, nodes: List[str] = None, m: int = 65537):

        """

        初始化Maglev哈希

        

        Args:

            nodes: 节点列表

            m: 查找表大小（应选大素数）

        """

        self.m = m  # 查找表大小

        self.nodes = []  # 节点列表

        self.lookup = [None] * m  # 查找表

        self.perturbation = {}  # 节点扰动值

        

        if nodes:

            for node in nodes:

                self.add_node(node)

    

    def _hash1(self, node: str) -> int:

        """第一个哈希函数"""

        return int(hashlib.md5(node.encode()).hexdigest()[:8], 16) % self.m

    

    def _hash2(self, node: str) -> int:

        """第二个哈希函数"""

        return int(hashlib.md5(node.encode('utf-8') + b'salt').hexdigest()[:8], 16) % (self.m - 1) + 1

    

    def add_node(self, node: str):

        """

        添加节点并重建查找表

        

        Args:

            node: 节点标识符

        """

        if node in self.nodes:

            return

        

        self.nodes.append(node)

        self._rebuild_lookup()

    

    def remove_node(self, node: str):

        """

        移除节点并重建查找表

        

        Args:

            node: 节点标识符

        """

        if node not in self.nodes:

            return

        

        self.nodes.remove(node)

        self._rebuild_lookup()

    

    def _rebuild_lookup(self):

        """

        重建查找表（核心算法）

        

        算法：

        1. 初始化所有槽为None

        2. 每个节点依次尝试占据槽位

        3. 使用skip跳过已占槽位

        """

        n = len(self.nodes)

        if n == 0:

            self.lookup = [None] * self.m

            return

        

        # 初始化

        next_entry = list(range(n))  # [0, 1, 2, ..., n-1]

        entry = 0

        

        # 槽位状态：-1表示空

        slots = [-1] * self.m

        offset = 0

        

        while entry < n:

            node_idx = next_entry[entry]

            node = self.nodes[node_idx]

            

            h1 = self._hash1(node)

            h2 = self._hash2(node)

            

            for i in range(self.m):

                slot = (h1 + i * h2) % self.m

                

                if slots[slot] == -1:

                    # 找到空槽

                    slots[slot] = node_idx

                    entry += 1

                    break

        

        # 转换为节点名

        self.lookup = [self.nodes[idx] if idx >= 0 else None for idx in slots]

    

    def get_node(self, key: str) -> Optional[str]:

        """

        O(1)查找节点

        

        Args:

            key: 数据键

        

        Returns:

            节点标识符

        """

        if not self.lookup:

            return None

        

        key_hash = int(hashlib.md5(key.encode()).hexdigest()[:8], 16) % self.m

        return self.lookup[key_hash]





def simulate_distribution(num_keys: int = 100000, 

                         num_nodes: int = 10,

                         virtual_nodes: int = 160) -> Dict[str, float]:

    """

    模拟数据分布

    

    Args:

        num_keys: 模拟的key数量

        num_nodes: 节点数量

        virtual_nodes: 虚拟节点数

    

    Returns:

        节点分布统计

    """

    nodes = [f"node-{i}" for i in range(num_nodes)]

    

    ketama = KetamaHash(nodes, virtual_nodes)

    

    # 统计每个节点的key数量

    key_counts = {node: 0 for node in nodes}

    

    for i in range(num_keys):

        key = f"key-{i}-{secrets.token_hex(8)}"

        node = ketama.get_node(key)

        if node:

            key_counts[node] += 1

    

    # 计算百分比

    total = num_keys

    distribution = {node: (count / total) * 100 for node, count in key_counts.items()}

    

    return distribution





def benchmark_lookup():

    """

    基准测试：Ketama vs Maglev 查找性能

    """

    import time

    import secrets

    

    num_nodes = 50

    num_keys = 1000000

    

    nodes = [f"node-{i}" for i in range(num_nodes)]

    

    # 初始化

    ketama = KetamaHash(nodes, 100)

    maglev = MaglevHash(nodes, 65537)

    

    keys = [f"key-{i}-{secrets.token_hex(8)}" for i in range(num_keys)]

    

    # Ketama查找

    start = time.time()

    for key in keys:

        ketama.get_node(key)

    ketama_time = time.time() - start

    

    # Maglev查找

    start = time.time()

    for key in keys:

        maglev.get_node(key)

    maglev_time = time.time() - start

    

    print(f"\n查找性能对比 ({num_keys:,} keys, {num_nodes} nodes):")

    print(f"  Ketama: {ketama_time:.3f}s ({num_keys/ketama_time:,.0f} ops/s)")

    print(f"  Maglev: {maglev_time:.3f}s ({num_keys/maglev_time:,.0f} ops/s)")





def demo_ketama():

    """

    演示Ketama一致性哈希

    """

    print("=== Ketama一致性哈希演示 ===\n")

    

    # 创建哈希环

    nodes = ["cache-1", "cache-2", "cache-3", "cache-4"]

    ketama = KetamaHash(nodes, virtual_nodes=100)

    

    print(f"1. 初始节点: {nodes}")

    print(f"   虚拟节点/物理节点: {ketama.virtual_nodes}")

    print(f"   环上总虚拟节点: {len(ketama.ring)}")

    

    # 测试key分布

    print("\n2. Key分布测试:")

    test_keys = ["user:1000", "user:2000", "session:abc123", "token:xyz789", "data:001"]

    for key in test_keys:

        node = ketama.get_node(key)

        print(f"   key '{key}' -> {node}")

    

    # 节点增减影响

    print("\n3. 节点增减影响:")

    ketama.add_node("cache-5")

    print(f"   添加cache-5后:")

    for key in test_keys:

        old_node = ketama.get_node(key)  # 重新查找（会变化）

        print(f"     {key} -> {old_node}")

    

    # 分布统计

    print("\n4. 分布统计:")

    dist = ketama.get_distribution()

    for node, pct in sorted(dist.items()):

        print(f"   {node}: {pct:.2f}%")





def demo_maglev():

    """

    演示Maglev一致性哈希

    """

    print("\n=== Maglev一致性哈希演示 ===\n")

    

    nodes = ["server-1", "server-2", "server-3"]

    m = 11  # 小size便于展示

    

    maglev = MaglevHash(nodes, m)

    

    print(f"1. 节点: {nodes}")

    print(f"   查找表大小: {maglev.m}")

    

    print("\n2. 查找表示例（表大小=11）:")

    for i, slot in enumerate(maglev.lookup):

        print(f"   [{i:2d}]: {slot}")

    

    print("\n3. Key查找:")

    test_keys = ["request-1", "request-2", "request-3"]

    for key in test_keys:

        node = maglev.get_node(key)

        key_hash = int(hashlib.md5(key.encode()).hexdigest()[:8], 16) % m

        print(f"   {key} (hash%11={key_hash}) -> {node}")





def demo_node_failover():

    """

    演示节点故障转移

    """

    print("\n=== 节点故障转移演示 ===\n")

    

    nodes = ["primary", "secondary", "tertiary"]

    ketama = KetamaHash(nodes, 100)

    

    print("1. 正常状态:")

    for key in ["data-1", "data-2", "data-3", "data-4", "data-5"]:

        replicas = ketama.get_nodes(key, replicas=3)

        print(f"   {key}: {replicas}")

    

    print("\n2. primary节点故障，移除后:")

    ketama.remove_node("primary")

    

    for key in ["data-1", "data-2", "data-3", "data-4", "data-5"]:

        replicas = ketama.get_nodes(key, replicas=2)

        print(f"   {key}: {replicas}")

    

    print("\n   注意：只有primary故障的数据需要重新路由，其他节点不受影响")





if __name__ == "__main__":

    import secrets

    

    print("=" * 60)

    print("一致性哈希算法实现")

    print("=" * 60)

    

    # Ketama演示

    demo_ketama()

    

    # Maglev演示

    demo_maglev()

    

    # 节点故障转移演示

    demo_node_failover()

    

    # 性能基准测试

    benchmark_lookup()

    

    # 分布模拟

    print("\n=== 数据分布模拟 ===\n")

    dist = simulate_distribution(num_keys=100000, num_nodes=10)

    print("10个节点，100000个key的分布:")

    for node, pct in sorted(dist.items()):

        bar = '█' * int(pct / 2)

        print(f"  {node}: {pct:5.2f}% {bar}")

    

    print("\n" + "=" * 60)

    print("算法对比:")

    print("=" * 60)

    print("""

| 特性         | Ketama          | Maglev           |

|-------------|-----------------|------------------|

| 查找复杂度   | O(log N)        | O(1)             |

| 内存占用     | O(N*V)          | O(M)             |

| 重建开销     | 全部重建        | 全部重建         |

| 适用场景     | 缓存系统        | 负载均衡器       |

| 负载均衡性   | 优秀            | 优秀             |



其中 N=物理节点数, V=虚拟节点数, M=查找表大小

""")

