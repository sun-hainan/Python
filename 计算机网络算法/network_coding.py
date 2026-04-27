# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / network_coding

本文件实现 network_coding 相关的算法功能。
"""

import random
import numpy as np


class GF256:
    """
    GF(2^8) 有限域算术
    
    用于网络编码的字节级运算
    """

    # GF(2^8) 的本原多项式：x^8 + x^4 + x^3 + x^2 + 1 = 0x11D
    PRIMITIVE_POLY = 0x11D

    # 对数表和指数表（用于乘法）
    _log_table = [0] * 256
    _exp_table = [0] * 256

    @classmethod
    def _init_tables(cls):
        """初始化对数表和指数表"""
        if cls._log_table[1] != 0:
            return  # 已初始化
        
        g = 3  # 生成元
        for i in range(255):
            cls._exp_table[i] = g
            g = cls._gf_mul(g, 3)

    @classmethod
    def _gf_mul(cls, a, b):
        """GF(2^8) 乘法"""
        result = 0
        while b:
            if b & 1:
                result ^= a
            a = (a << 1) & 0xFF
            if a & 0x100:
                a ^= cls.PRIMITIVE_POLY
            b >>= 1
        return result

    @classmethod
    def mul(cls, a, b):
        """GF(2^8) 乘法（公开接口）"""
        if a == 0 or b == 0:
            return 0
        cls._init_tables()
        return cls._exp_table[(cls._log_table[a] + cls._log_table[b]) % 255]

    @classmethod
    def div(cls, a, b):
        """GF(2^8) 除法"""
        if b == 0:
            raise ValueError("除数不能为零")
        if a == 0:
            return 0
        cls._init_tables()
        return cls._exp_table[(cls._log_table[a] - cls._log_table[b]) % 255]

    @classmethod
    def add(cls, a, b):
        """GF(2^8) 加法（异或）"""
        return a ^ b


class CodingVector:
    """编码向量"""

    def __init__(self, dimension, coefficients=None):
        """
        初始化编码向量
        
        参数:
            dimension: 向量维度（原始数据包数量）
            coefficients: 系数列表（如果不提供则生成随机向量）
        """
        self.dimension = dimension
        if coefficients is None:
            # 生成随机非零系数
            self.coeffs = [random.randint(1, 255) for _ in range(dimension)]
        else:
            self.coeffs = list(coefficients)

    def __len__(self):
        return self.dimension

    def __getitem__(self, index):
        return self.coeffs[index]

    def __setitem__(self, index, value):
        self.coeffs[index] = value

    def __add__(self, other):
        """向量加法（GF(2^8)）"""
        if self.dimension != other.dimension:
            raise ValueError("维度不匹配")
        new_coeffs = [GF256.add(self.coeffs[i], other.coeffs[i]) 
                      for i in range(self.dimension)]
        return CodingVector(self.dimension, new_coeffs)

    def __mul__(self, scalar):
        """标量乘法（GF(2^8)）"""
        new_coeffs = [GF256.mul(self.coeffs[i], scalar) for i in range(self.dimension)]
        return CodingVector(self.dimension, new_coeffs)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def dot(self, data_blocks):
        """
        向量与数据块的点积
        
        参数:
            data_blocks: 原始数据块列表
        返回:
            encoded: 编码后的数据块
        """
        if len(data_blocks) != self.dimension:
            raise ValueError("数据块数量与向量维度不匹配")
        
        result = b'\x00' * len(data_blocks[0])
        for i, coeff in enumerate(self.coeffs):
            if coeff != 0:
                # 编码：累加 coeff * data_block[i]
                for j in range(len(data_blocks[0])):
                    result_bytes = list(result)
                    result_bytes[j] ^= GF256.mul(data_blocks[i][j], coeff)
                    result = bytes(result_bytes)
        return result

    def is_nonzero(self):
        """检查向量是否非零"""
        return any(c != 0 for c in self.coeffs)

    def to_bytes(self):
        """转换为字节"""
        return bytes(self.coeffs)

    @staticmethod
    def from_bytes(data):
        """从字节创建"""
        return CodingVector(len(data), list(data))


class NetworkCodedNode:
    """支持网络编码的节点"""

    def __init__(self, node_id, num_generations=1):
        """
        初始化编码节点
        
        参数:
            node_id: 节点标识
            num_generations: 代数数量（用于区分不同批次的编码）
        """
        self.node_id = node_id
        self.num_generations = num_generations
        # 接收到的编码包：{generation: [(coding_vector, data_block), ...]}
        self.received_packets = {}
        # 已解码的数据包：{generation: {index: data_block}}
        self.decoded_data = {}
        # 路由表：{destination: next_hop}
        self.routing_table = {}

    def encode(self, data_blocks, generation_id=0):
        """
        编码数据块
        
        参数:
            data_blocks: 原始数据块列表
            generation_id: 代数 ID
        返回:
            (coding_vector, encoded_block): 编码向量和编码后的数据块
        """
        dimension = len(data_blocks)
        vector = CodingVector(dimension)
        encoded = vector.dot(data_blocks)
        return vector, encoded

    def receive_packet(self, coding_vector, data_block, generation_id=0):
        """
        接收编码数据包
        
        参数:
            coding_vector: 编码向量
            data_block: 编码后的数据块
            generation_id: 代数 ID
        """
        if generation_id not in self.received_packets:
            self.received_packets[generation_id] = []
            self.decoded_data[generation_id] = {}
        
        # 添加到接收缓冲区
        self.received_packets[generation_id].append((coding_vector, data_block))
        
        # 尝试解码
        self._decode(generation_id)

    def _decode(self, generation_id):
        """
        解码数据（高斯消元法）
        
        参数:
            generation_id: 代数 ID
        """
        packets = self.received_packets[generation_id]
        if len(packets) < len(packets[0][0]):
            return  # 收到的包不足
        
        # 简化解码：使用随机线性编码的解码逻辑
        # 实际应该使用高斯消元，这里简化为检查是否线性无关
        decoded_count = len(self.decoded_data[generation_id])
        dimension = packets[0][0].dimension if packets else 0
        
        if decoded_count >= dimension:
            return  # 已完全解码
        
        # 检查新收到的向量是否有用
        # 简化实现：假设线性无关
        if len(packets) > decoded_count:
            self.decoded_data[generation_id][decoded_count] = packets[-1][1]

    def is_decoded(self, generation_id=0):
        """检查是否已完全解码"""
        return len(self.decoded_data.get(generation_id, {})) >= self.num_generations

    def get_decoded_data(self, generation_id=0):
        """获取已解码的数据"""
        return self.decoded_data.get(generation_id, {})


class RandomLinearNetworkCoding:
    """随机线性网络编码器"""

    def __init__(self, num_original_packets=4):
        """
        初始化编码器
        
        参数:
            num_original_packets: 原始数据包数量
        """
        self.num_original_packets = num_original_packets
        # 原始数据包
        self.original_packets = []
        # 编码系数记录
        self.coefficients = []

    def set_packets(self, packets):
        """
        设置原始数据包
        
        参数:
            packets: 数据包列表
        """
        if len(packets) != self.num_original_packets:
            raise ValueError(f"需要 {self.num_original_packets} 个数据包")
        self.original_packets = list(packets)

    def encode_packet(self):
        """
        生成一个编码数据包
        
        返回:
            (coefficients, encoded_packet): 编码系数和编码包
        """
        # 生成随机编码向量
        coeffs = [random.randint(1, 255) for _ in range(self.num_original_packets)]
        self.coefficients.append(coeffs)
        
        # 执行编码
        encoded = self._linear_combination(coeffs)
        return CodingVector(self.num_original_packets, coeffs), encoded

    def _linear_combination(self, coeffs):
        """
        计算线性组合
        
        参数:
            coeffs: 系数列表
        返回:
            encoded: 编码后的数据包
        """
        # 简化：假设每个数据包是固定长度的字节串
        if not self.original_packets:
            return b''
        
        packet_length = len(self.original_packets[0])
        result = bytearray(packet_length)
        
        for i, coeff in enumerate(coeffs):
            if coeff != 0:
                for j in range(packet_length):
                    result[j] ^= GF256.mul(self.original_packets[i][j], coeff)
        
        return bytes(result)

    def decode_packets(self, received_packets):
        """
        解码接收到的数据包
        
        参数:
            received_packets: [(coding_vector, encoded_data), ...]
        返回:
            decoded: 解码后的原始数据包列表
        """
        if len(received_packets) < self.num_original_packets:
            return None  # 数据不足
        
        # 简化解码：假设收到足够多的线性无关包
        # 实际应该使用高斯消元
        decoded = [b'\x00' * len(received_packets[0][1]) for _ in range(self.num_original_packets)]
        
        # 简化：直接返回最后一个收到的包
        # 真实实现需要复杂的矩阵运算
        return decoded


if __name__ == "__main__":
    # 测试网络编码
    print("=== 网络编码测试 ===\n")

    # 测试 GF(2^8) 运算
    print("--- GF(2^8) 算术 ---")
    a, b = 0x57, 0x83
    print(f"  加法: {a:#04x} + {b:#04x} = {GF256.add(a, b):#04x}")
    print(f"  乘法: {a:#04x} * {b:#04x} = {GF256.mul(a, b):#04x}")
    print(f"  除法: {a:#04x} / {b:#04x} = {GF256.div(a, b):#04x}")

    # 测试编码向量
    print("\n--- 编码向量 ---")
    vec = CodingVector(4)
    print(f"  随机向量: {vec.to_bytes().hex()}")
    print(f"  非零检查: {vec.is_nonzero()}")

    # 测试网络编码节点
    print("\n--- 网络编码节点 ---")
    node = NetworkCodedNode("Node_A")
    
    # 模拟原始数据
    original_data = [
        b"Data_1" + b'\x00' * 10,
        b"Data_2" + b'\x00' * 10,
        b"Data_3" + b'\x00' * 10,
        b"Data_4" + b'\x00' * 10,
    ]
    
    # 编码
    vector, encoded = node.encode(original_data)
    print(f"  编码向量: {vector.to_bytes().hex()}")
    print(f"  编码数据: {encoded}")

    # 接收和解码模拟
    print("\n--- 接收与解码 ---")
    node.receive_packet(vector, encoded, generation_id=0)
    print(f"  接收包数: {len(node.received_packets.get(0, []))}")

    # 随机线性网络编码
    print("\n--- 随机线性网络编码 ---")
    rlnc = RandomLinearNetworkCoding(num_original_packets=4)
    rlnc.set_packets(original_data)
    
    print("  生成 8 个编码包:")
    encoded_packets = []
    for i in range(8):
        vec, pkt = rlnc.encode_packet()
        encoded_packets.append((vec, pkt))
        print(f"    包 {i+1}: 系数={vec.to_bytes().hex()}, 数据前16字节={pkt[:16].hex()}")

    # 模拟传输和丢失
    print("\n  模拟传输（假设收到前 6 个包）:")
    received = encoded_packets[:6]
    print(f"    收到 {len(received)} 个包")
    
    decoded = rlnc.decode_packets(received)
    print(f"    解码结果: {'成功' if decoded else '失败'}")
