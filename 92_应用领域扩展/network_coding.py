# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / network_coding



本文件实现 network_coding 相关的算法功能。

"""



import numpy as np

import random

from typing import List, Dict, Tuple, Optional

from dataclasses import dataclass, field

import json





@dataclass

class EncodedPacket:

    """编码数据包"""

    vector: np.ndarray  # 编码向量

    data: np.ndarray  # 编码后的数据

    generation_id: int  # 代号（用于区分不同代的包）

    node_id: str  # 来源节点

    

    def to_bytes(self) -> bytes:

        """序列化为字节"""

        return json.dumps({

            'vector': self.vector.tolist(),

            'generation_id': self.generation_id,

            'node_id': self.node_id

        }).encode() + self.data.tobytes()

    

    @classmethod

    def from_bytes(cls, data: bytes) -> 'EncodedPacket':

        """从字节反序列化"""

        json_size = int.from_bytes(data[:4], 'big')

        meta = json.loads(data[:4+json_size].decode())

        arr_size = len(data) - 4 - json_size

        arr = np.frombuffer(data[4+json_size:], dtype=np.float64)

        return cls(

            vector=np.array(meta['vector']),

            data=arr,

            generation_id=meta['generation_id'],

            node_id=meta['node_id']

        )





class LinearNetworkCoding:

    """

    线性网络编码实现

    

    核心思想：

    - 源节点生成原始数据包 D1, D2, ..., Dm

    - 中间节点对收到的包进行线性组合

    - 目的节点收集足够多的线性无关包，解出原始数据

    """

    

    def __init__(self, field_size: int = 256, max_generation_size: int = 4):

        """

        初始化

        

        Args:

            field_size: 有限域大小（通常为2^8=256）

            max_generation_size: 每个代的最大包数

        """

        self.field_size = field_size

        self.max_generation_size = max_generation_size

        self.prime = self._find_prime(field_size)  # 使用素数域

    

    def _find_prime(self, n: int) -> int:

        """找到小于n的最大素数"""

        for p in range(n - 1, 1, -1):

            if all(p % i != 0 for i in range(2, int(p**0.5) + 1)):

                return p

        return 2

    

    def random_coefficients(self, length: int) -> np.ndarray:

        """

        生成随机编码系数

        

        Args:

            length: 系数数量

        

        Returns:

            随机系数向量

        """

        return np.array([random.randint(0, self.prime - 1) for _ in range(length)])

    

    def encode(self, packets: List[np.ndarray]) -> List[EncodedPacket]:

        """

        源节点编码

        

        Args:

            packets: 原始数据包列表

        

        Returns:

            编码包列表

        """

        m = len(packets)

        encoded = []

        

        # 生成n个线性组合（n > m以提供冗余）

        n = m + 2  # 冗余因子

        

        for i in range(n):

            coeffs = self.random_coefficients(m)

            encoded_data = np.zeros_like(packets[0])

            

            for j in range(m):

                encoded_data += coeffs[j] * packets[j]

            

            encoded.append(EncodedPacket(

                vector=coeffs,

                data=encoded_data,

                generation_id=0,

                node_id="source"

            ))

        

        return encoded

    

    def recombine(self, received: List[EncodedPacket]) -> EncodedPacket:

        """

        中间节点重新编码

        

        Args:

            received: 接收到的编码包

        

        Returns:

            新的编码包

        """

        if not received:

            return None

        

        # 简化：随机选择一个包

        coeffs = self.random_coefficients(len(received))

        

        new_vector = np.zeros(received[0].vector.shape)

        new_data = np.zeros_like(received[0].data)

        

        for i, pkt in enumerate(received):

            new_vector += coeffs[i] * pkt.vector

            new_data += coeffs[i] * pkt.data

        

        return EncodedPacket(

            vector=new_vector,

            data=new_data,

            generation_id=received[0].generation_id,

            node_id="intermediate"

        )

    

    def decode(self, encoded_packets: List[EncodedPacket], 

               original_count: int) -> List[np.ndarray]:

        """

        解码（高斯消元）

        

        Args:

            encoded_packets: 编码包列表

            original_count: 原始包数量

        

        Returns:

            原始数据包列表

        """

        if len(encoded_packets) < original_count:

            return None  # 包不足，无法解码

        

        # 构造矩阵 [vector | data]

        # 使用前original_count个线性无关的包

        n = min(len(encoded_packets), original_count + 2)

        

        vectors = []

        datas = []

        

        for pkt in encoded_packets[:n]:

            vectors.append(pkt.vector)

            datas.append(pkt.data)

        

        # 构建增广矩阵

        V = np.array(vectors, dtype=np.float64)

        D = np.array(datas, dtype=np.float64)

        

        # 简化：假设V是方阵且可逆

        try:

            V_inv = np.linalg.inv(V)

            original = V_inv @ D

            return [original[i] for i in range(original_count)]

        except np.linalg.LinAlgError:

            return None  # 矩阵奇异，解码失败





class RandomLinearNetworkCoding:

    """

    随机线性网络编码 (RLNC)

    

    每个节点使用随机系数进行编码，

    无需知道全局网络拓扑。

    """

    

    def __init__(self, field_size: int = 256, symbol_size: int = 1000):

        self.field_size = field_size

        self.symbol_size = symbol_size

        # 简化：使用0-255的整数

    

    def encode_symbols(self, symbols: List[np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:

        """

        编码符号

        

        Args:

            symbols: 原始符号列表

        

        Returns:

            (coding_vector, encoded_symbol)

        """

        m = len(symbols)

        coeffs = np.array([random.randint(0, 255) for _ in range(m)], dtype=np.uint8)

        

        # 编码

        encoded = np.zeros_like(symbols[0], dtype=np.uint8)

        for i, s in enumerate(symbols):

            encoded = (encoded + coeffs[i] * s) % 256

        

        return coeffs, encoded

    

    def decode_symbols(self, received: List[Tuple[np.ndarray, np.ndarray]], 

                       original_count: int) -> Optional[List[np.ndarray]]:

        """

        解码符号

        

        Args:

            received: [(coding_vector, encoded_symbol), ...]

            original_count: 原始符号数量

        

        Returns:

            原始符号列表

        """

        # 收集足够的编码向量

        if len(received) < original_count:

            return None

        

        # 构建解码矩阵

        # A @ x = b

        # 其中A是编码向量组成的矩阵，b是编码后的符号

        A = np.array([r[0] for r in received[:original_count]], dtype=np.float64)

        B = np.array([r[1].astype(np.float64) for r in received[:original_count]], dtype=np.float64)

        

        try:

            # 高斯消元

            result = np.linalg.solve(A, B)

            return [result[i].astype(np.uint8) for i in range(original_count)]

        except np.linalg.LinAlgError:

            return None





def simulate_butterfly_network():

    """

    模拟蝴蝶网络中的网络编码

    

    蝴蝶网络是展示网络编码优势的标准例子：

    - 两个源节点各发送一个包

    - 共享链路只够传输一个包

    - 但通过编码，两个目的节点都能收到两个包

    """

    print("=== 蝴蝶网络编码演示 ===\n")

    

    print("网络拓扑:")

    print("  S1 --R1-- W --R3-- T1")

    print("   \\      |      /")

    print("    \\     |     /")

    print("     \\    |    /")

    print("      R2--X--R4")

    print("     /    |    \\")

    print("   /      |      \\")

    print("  S2 --R5-- W2 --R6-- T2")

    print()

    print("传统路由: W到T1/T2的链路只有一条，需要发送2次")

    print("网络编码: W将S1和S2的包XOR后发送一次，两个T都能恢复")

    

    # 模拟

    l_n_c = LinearNetworkCoding()

    

    # 源数据

    s1_data = np.array([1, 0, 0, 0], dtype=np.float64)  # S1的包

    s2_data = np.array([0, 1, 0, 0], dtype=np.float64)  # S2的包

    

    print(f"\n源数据:")

    print(f"  S1 发送: {s1_data}")

    print(f"  S2 发送: {s2_data}")

    

    # 节点W进行XOR编码

    w_encoded = s1_data + s2_data  # 简单XOR（实际上是模2加）

    

    print(f"\n节点W编码 (S1 XOR S2):")

    print(f"  编码后: {w_encoded}")

    

    # T1接收

    # T1直接从S1收到s1_data

    # T1从W收到w_encoded

    # T1计算: w_encoded - s1_data = s2_data

    t1_recovered = w_encoded - s1_data

    

    print(f"\n目的节点T1:")

    print(f"  收到S1: {s1_data}")

    print(f"  收到W: {w_encoded}")

    print(f"  恢复S2: {t1_recovered}")

    print(f"  T1最终拥有: {s1_data} 和 {t1_recovered} ✓")

    

    # T2同理

    t2_recovered = w_encoded - s2_data

    

    print(f"\n目的节点T2:")

    print(f"  收到S2: {s2_data}")

    print(f"  收到W: {w_encoded}")

    print(f"  恢复S1: {t2_recovered}")

    print(f"  T2最终拥有: {s2_data} 和 {t2_recovered} ✓")





def demo_multicast_throughput():

    """

    演示多播场景的吞吐率提升

    """

    print("\n=== 多播吞吐率提升演示 ===\n")

    

    print("场景: 1个源，3个目的，共享链路容量=1")

    print()

    

    print("传统路由:")

    print("  - 需要3次传输共享链路")

    print("  - 吞吐率 = 1/3")

    

    print("\n网络编码:")

    print("  - 只需1次传输共享链路")

    print("  - 吞吐率 = 1")

    

    print("\n吞吐率提升: 3倍")





def demo_reliability():

    """

    演示网络编码的抗丢包能力

    """

    print("\n=== 网络编码可靠性演示 ===\n")

    

    l_n_c = LinearNetworkCoding(max_generation_size=4)

    

    # 生成4个原始包

    original = [np.array([i], dtype=np.float64) for i in range(1, 5)]

    print(f"原始包数: {len(original)}")

    

    # 生成6个编码包（提供冗余）

    encoded = []

    for i in range(6):

        coeffs = np.random.randint(0, 256, size=4)

        enc_data = sum(c * o for c, o in zip(coeffs, original))

        encoded.append((coeffs, enc_data))

    

    print(f"编码包数: {len(encoded)} (含冗余)")

    

    # 模拟丢包（丢失2个）

    lost_indices = random.sample(range(6), 2)

    received = [e for i, e in enumerate(encoded) if i not in lost_indices]

    

    print(f"模拟丢包: 丢失{len(lost_indices)}个包")

    print(f"接收包数: {len(received)}")

    

    # 解码

    result = ln c.decode_symbols(received, 4)

    

    if result:

        print("\n解码成功！")

        print(f"恢复的数据: {[int(r[0]) for r in result]}")

    else:

        print("\n解码失败（包不足）")





def demo_implementation():

    """

    演示实际实现

    """

    print("\n=== 线性网络编码实现演示 ===\n")

    

    l_n_c = LinearNetworkCoding(field_size=257)

    

    # 模拟消息传输

    message = [np.array([ord(c) + i], dtype=np.float64) for i, c in enumerate("HELLO")]

    

    print(f"原始消息: {[chr(int(m[0])-i) for i, m in enumerate(message)]}")

    

    # 编码

    encoded_packets = ln c.encode(message)

    

    print(f"\n编码生成 {len(encoded_packets)} 个包")

    print(f"每个包包含: 编码向量 + 编码数据")

    

    # 模拟传输（丢失1个包）

    transmitted = encoded_packets[:-1]

    

    print(f"\n传输中丢失1个包")

    print(f"接收 {len(transmitted)} 个包")

    

    # 解码

    decoded = ln c.decode(transmitted, len(message))

    

    if decoded:

        print(f"\n解码成功!")

        result = ''.join(chr(int(d[0])) for d in decoded)

        print(f"恢复消息: {result}")

    else:

        print("\n解码失败: 需要更多包")





if __name__ == "__main__":

    print("=" * 60)

    print("网络编码算法实现")

    print("=" * 60)

    

    # 蝴蝶网络演示

    simulate_butterfly_network()

    

    # 多播吞吐率

    demo_multicast_throughput()

    

    # 可靠性

    demo_reliability()

    

    # 实际实现

    demo_implementation()

    

    print("\n" + "=" * 60)

    print("网络编码关键概念:")

    print("=" * 60)

    print("""

1. 线性网络编码:

   - 有限域上的线性组合

   - 代数结构保证编解码

   - 实用：使用GF(2^8)



2. 随机线性网络编码(RLNC):

   - 节点使用随机系数

   - 无需知道全局拓扑

   - 高概率线性无关



3. 应用场景:

   - 多播路由（如P2P流媒体）

   - 数据分发（CDN）

   - 分布式存储

   - 容错传输



4. 理论极限（Min-cut Max-flow）:

   - 网络容量 = 源到每个汇的最小割容量之和

   - 网络编码可以达到这个极限

   - 传统路由无法达到

""")

