# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / quic_protocol

本文件实现 quic_protocol 相关的算法功能。
"""

import struct
import hashlib
import secrets
from enum import Enum
from dataclasses import dataclass


class QUICVersion(Enum):
    """QUIC协议版本"""
    V1 = 1  # RFC 9000
    DRAFT_29 = 0xff00001d


class QUICFrameType(Enum):
    """QUIC帧类型"""
    PADDING = 0x00
    PING = 0x01
    ACK = 0x02
    ACK_MORE = 0x03
    DATA = 0x06
    HEADERS = 0x07
    GOAWAY = 0x08
    NEW_TOKEN = 0x09
    HANDSHAKE_DONE = 0x0e


@dataclass
class QUICConnectionId:
    """QUIC连接ID"""
    connection_id: bytes
    
    def __bytes__(self):
        return bytes([len(self.connection_id)]) + self.connection_id
    
    @classmethod
    def from_bytes(cls, data, offset=0):
        length = data[offset]
        cid = data[offset+1:offset+1+length]
        return cls(cid), offset + 1 + length


@dataclass
class QUICHeader:
    """QUIC数据包头"""
    version: int
    connection_id: QUICConnectionId
    packet_number: int
    payload_length: int
    is_long_header: bool = True


class QUICCrypto:
    """
    QUIC加密层核心
    
    QUIC使用AEAD加密（AES-GCM/ChaCha20-Poly1305）
    密钥派生：HKDF
    """
    
    @staticmethod
    def derive_keys(client_secret, server_secret, connection_id):
        """
        密钥派生（简化版HKDF）
        
        Args:
            client_secret: 客户端初始密钥材料
            server_secret: 服务器初始密钥材料
            connection_id: 连接ID（盐值）
        
        Returns:
            (client_key, server_key, client_iv, server_iv)
        """
        # 简化：使用SHA256派生密钥
        def hkdf_extract_expand(secret, salt, info, length):
            h = hashlib.sha256(salt + secret + info).digest()
            return h[:length]
        
        client_key = hkdf_extract_expand(client_secret, connection_id, b"quic key", 32)
        server_key = hkdf_extract_expand(server_secret, connection_id, b"quic key", 32)
        client_iv = hkdf_extract_expand(client_secret, connection_id, b"quic iv", 12)
        server_iv = hkdf_extract_expand(server_secret, connection_id, b"quic iv", 12)
        
        return client_key, server_key, client_iv, server_iv
    
    @staticmethod
    def encrypt_payload(payload, key, iv, associated_data=b""):
        """
        加密载荷（简化版AEAD）
        
        Args:
            payload: 明文数据
            key: 加密密钥
            iv: 初始化向量
            associated_data: 关联数据
        
        Returns:
            加密后的密文（含认证标签）
        """
        # 简化实现：实际应使用AES-GCM或ChaCha20-Poly1305
        import hmac
        import os
        
        # 生成随机nonce
        nonce = bytes([a ^ b for a, b in zip(iv, os.urandom(len(iv)))])
        
        # 简化XOR加密（演示用）
        ciphertext = bytes([p ^ k for p, k in zip(payload, key * (len(payload) // 32 + 1))])
        
        # 简化认证标签
        tag = hmac.new(key, associated_data + ciphertext, hashlib.sha256).digest()[:16]
        
        return ciphertext + tag
    
    @staticmethod
    def decrypt_payload(ciphertext, key, iv, associated_data=b""):
        """
        解密载荷
        """
        # 分离密文和标签
        tag = ciphertext[-16:]
        payload = ciphertext[:-16]
        
        # 简化XOR解密
        plain = bytes([c ^ k for c, k in zip(payload, key * (len(payload) // 32 + 1))])
        return plain


class QUICStream:
    """
    QUIC流抽象
    
    每个流有唯一的stream_id，支持：
    - 单向/双向流
    - 可靠/不可靠传输（可配置）
    """
    
    STREAM_TYPE_SEND = 0
    STREAM_TYPE_RECV = 1
    
    def __init__(self, stream_id, is_bidirectional=True):
        """
        初始化流
        
        Args:
            stream_id: 流ID（唯一标识）
            is_bidirectional: 是否为双向流
        """
        self.stream_id = stream_id
        self.is_bidirectional = is_bidirectional
        
        # 发送侧状态
        self.send_offset = 0  # 已发送字节偏移
        self.send_data = b""  # 待发送数据
        self.send_fin = False  # 是否已发送FIN
        
        # 接收侧状态
        self.recv_offset = 0  # 已接收字节偏移
        self.recv_data = b""  # 已接收数据
        self.recv_fin = False  # 是否已接收FIN
        
        # 流量控制
        self.max_send_offset = float('inf')
        self.max_recv_offset = float('inf')
    
    def send(self, data):
        """
        发送数据
        
        Args:
            data: 要发送的字节数据
        
        Returns:
            可发送的字节数
        """
        available = self.max_send_offset - self.send_offset
        to_send = data[:available]
        self.send_data += to_send
        return len(to_send)
    
    def receive(self, data, offset):
        """
        接收数据
        
        Args:
            data: 接收到的数据
            offset: 数据在流中的起始偏移
        
        Returns:
            成功接收的字节数
        """
        if offset == self.recv_offset:
            self.recv_data += data
            self.recv_offset += len(data)
            return len(data)
        elif offset > self.recv_offset:
            # 数据丢失，等待重传
            return 0
        else:
            # 重复数据，忽略
            return 0


class QUICConnection:
    """
    QUIC连接状态机
    
    状态：
    - 0-RTT: 客户端直接发送数据（无需等待）
    - 1-RTT: 完整握手后传输数据
    - Handshake: 密钥交换中
    """
    
    def __init__(self, is_client=True, version=QUICVersion.V1):
        self.is_client = is_client
        self.version = version
        
        # 连接ID
        self.dcid = QUICConnectionId(secrets.token_bytes(8))  # 目标连接ID
        self.scid = QUICConnectionId(secrets.token_bytes(8))  # 源连接ID
        
        # 加密上下文
        self.crypto = QUICCrypto()
        self.client_secret = secrets.token_bytes(32)
        self.server_secret = secrets.token_bytes(32)
        
        # 密钥
        self.client_key = self.server_key = None
        self.client_iv = self.server_iv = None
        
        # 连接状态
        self.state = "initial"  # initial/handshake/connected/closing/closed
        self.zero_rtt_ready = False  # 0-RTT是否就绪
        
        # 流管理
        self.streams = {}  # stream_id -> QUICStream
        self.next_stream_id = 0 if is_client else 1
        
        # 包号
        self.packet_number = 0
        
        # ACK管理
        self.ack_queue = []
        self.ack_delay = 25e-3  # 25ms ACK延迟
    
    def open_stream(self, is_bidirectional=True):
        """
        打开新流
        
        Returns:
            新建的流对象
        """
        stream_id = self.next_stream_id
        self.next_stream_id += 4  # 双向流ID间隔为4
        
        stream = QUICStream(stream_id, is_bidirectional)
        self.streams[stream_id] = stream
        return stream
    
    def handle_handshake(self, packet):
        """
        处理握手过程
        
        Args:
            packet: 接收到的数据包
        """
        if self.state == "initial":
            if self.is_client:
                # 客户端：生成0-RTT密钥
                self._derive_zero_rtt_keys()
                self.zero_rtt_ready = True
                self.state = "handshake"
            else:
                # 服务器：等待客户端握手
                self.state = "handshake"
        
        elif self.state == "handshake":
            # 交换加密参数
            self._complete_handshake()
            self.state = "connected"
    
    def _derive_zero_rtt_keys(self):
        """派生0-RTT密钥（提前发送数据的密钥）"""
        self.client_key, self.server_key, self.client_iv, self.server_iv = \
            self.crypto.derive_keys(self.client_secret, self.server_secret, 
                                   bytes(self.dcid.connection_id))
    
    def _complete_handshake(self):
        """完成1-RTT密钥交换"""
        # 实际应该解析握手消息
        self.client_key, self.server_key, self.client_iv, self.server_iv = \
            self.crypto.derive_keys(self.client_secret, self.server_secret,
                                   bytes(self.scid.connection_id) + bytes(self.dcid.connection_id))
    
    def send_data_0rtt(self, stream_id, data):
        """
        使用0-RTT发送数据（连接建立前）
        
        Args:
            stream_id: 流ID
            data: 要发送的数据
        
        Returns:
            发送的数据包
        """
        if not self.zero_rtt_ready:
            return None
        
        stream = self.streams.get(stream_id)
        if not stream:
            stream = self.open_stream()
        
        sent = stream.send(data)
        self.send_offset = stream.send_offset
        
        # 构造0-RTT数据包
        packet = self._build_packet(stream_id, data[:sent], use_0rtt=True)
        return packet
    
    def _build_packet(self, stream_id, data, use_0rtt=False):
        """
        构造QUIC数据包
        
        Args:
            stream_id: 流ID
            data: 应用数据
            use_0rtt: 是否使用0-RTT加密
        
        Returns:
            构造的数据包字节
        """
        # 选择密钥
        if use_0rtt:
            key, iv = self.client_key, self.client_iv
        else:
            key, iv = self.client_key, self.client_iv
        
        # 帧数据
        stream_frame = bytes([0x08])  # STREAM帧类型
        stream_frame += varint(stream_id)
        stream_frame += varint(0)  # offset
        stream_frame += varint(len(data))
        stream_frame += data
        
        # 加密
        pn_len = 1  # 包号长度
        header = bytes([0x40 if use_0rtt else 0x43])  # 固定位
        header += bytes(self.dcid)
        header += varint(self.version)
        header += bytes([pn_len])  # 包号长度
        header += varint(self.packet_number)
        
        ciphertext = self.crypto.encrypt_payload(stream_frame, key, iv, header)
        
        return header + ciphertext


def varint(value):
    """
    QUIC可变长度整数编码
    
    Args:
        value: 要编码的整数
    
    Returns:
        编码后的字节
    """
    if value < 64:
        return bytes([value])
    elif value < 16384:
        return struct.pack("!H", 0x4000 | value)
    elif value < 1073741824:
        return struct.pack("!I", 0x80000000 | value)
    else:
        return struct.pack("!Q", 0xC000000000000000 | value)


def simulate_0rtt_handshake():
    """
    模拟0-RTT连接建立过程
    """
    print("=== QUIC 0-RTT 连接建立模拟 ===\n")
    
    # 创建连接
    client = QUICConnection(is_client=True)
    server = QUICConnection(is_client=False)
    
    # 交换连接ID
    client.dcid = server.scid
    server.dcid = client.scid
    
    print("1. 初始状态:")
    print(f"   客户端状态: {client.state}")
    print(f"   服务器状态: {server.state}")
    
    # 客户端派生0-RTT密钥
    client._derive_zero_rtt_keys()
    print(f"\n2. 客户端派生0-RTT密钥:")
    print(f"   0-RTT就绪: {client.zero_rtt_ready}")
    
    # 客户端直接发送数据（0-RTT）
    stream = client.open_stream()
    data = b"Hello, QUIC 0-RTT!"
    packet = client.send_data_0rtt(stream.stream_id, data)
    print(f"\n3. 客户端发送0-RTT数据:")
    print(f"   数据: {data}")
    print(f"   数据包长度: {len(packet)} bytes")
    
    # 服务器处理
    server.state = "handshake"
    server._derive_zero_rtt_keys()
    print(f"\n4. 服务器处理:")
    print(f"   服务器状态: {server.state}")
    
    # 完成握手
    server._complete_handshake()
    client._complete_handshake()
    print(f"\n5. 握手完成:")
    print(f"   客户端状态: {client.state}")
    print(f"   服务器状态: {server.state}")


def demo_multiplexing():
    """
    演示QUIC多路复用
    """
    print("\n=== QUIC 多路复用演示 ===\n")
    
    conn = QUICConnection()
    
    # 打开多个流
    streams = []
    for i in range(3):
        s = conn.open_stream()
        streams.append(s)
        print(f"打开流 {i}: stream_id={s.stream_id}")
    
    print(f"\n总流数: {len(conn.streams)}")
    
    # 模拟并发发送
    for i, s in enumerate(streams):
        data = f"Data for stream {i}".encode()
        sent = s.send(data)
        print(f"流 {i} 发送: {sent} bytes")


def demo_packet_structure():
    """
    演示QUIC数据包结构
    """
    print("\n=== QUIC 数据包结构演示 ===\n")
    
    conn = QUICConnection()
    
    # 构造不同类型的包
    print("1. Long Header包（握手包）:")
    header = bytes([0x43])  # Long header, 0x40固定位
    header += bytes(conn.dcid)
    header += varint(conn.version)
    header += bytes([0x00])  # 包号长度=1
    header += varint(0)  # 包号=0
    print(f"   头部长度: {len(header)} bytes")
    
    print("\n2. Short Header包（1-RTT数据）:")
    header = bytes([0x40])  # Short header
    header += bytes(conn.dcid)
    header += bytes([0x01])  # 包号长度=1
    header += varint(1)  # 包号=1
    print(f"   头部长度: {len(header)} bytes")


if __name__ == "__main__":
    print("=" * 60)
    print("QUIC 协议核心机制实现")
    print("=" * 60)
    
    # 0-RTT握手模拟
    simulate_0rtt_handshake()
    
    # 多路复用演示
    demo_multiplexing()
    
    # 数据包结构演示
    demo_packet_structure()
    
    # 关键特性总结
    print("\n" + "=" * 60)
    print("QUIC 关键特性总结:")
    print("=" * 60)
    print("""
1. 连接建立:
   - 1-RTT: 首次连接需要1个RTT建立
   - 0-RTT: 使用0-RTT直接发送数据（可能重放攻击）
   
2. 多路复用:
   - 流ID唯一标识每个流
   - 独立流控，互不干扰
   - 解决了TCP head-of-line blocking问题
   
3. 加密安全:
   - 全连接加密（0-RTT部分加密）
   - 使用AEAD（AES-GCM/ChaCha20）
   - 密钥派生使用HKDF
   
4. 连接迁移:
   - 连接ID支持连接迁移
   - 网络切换时保持连接
""")
