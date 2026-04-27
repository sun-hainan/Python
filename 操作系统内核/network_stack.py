# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / network_stack

本文件实现 network_stack 相关的算法功能。
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib


class Protocol(Enum):
    """协议类型"""
    TCP = 6
    UDP = 17
    ICMP = 1


@dataclass
class IPHeader:
    """IP头"""
    version: int = 4
    ihl: int = 5
    tos: int = 0
    total_length: int = 0
    identification: int = 0
    flags: int = 0
    fragment_offset: int = 0
    ttl: int = 64
    protocol: int = Protocol.TCP.value
    checksum: int = 0
    src_ip: str = "0.0.0.0"
    dst_ip: str = "0.0.0.0"

    def calculate_checksum(self) -> int:
        """计算校验和"""
        data = f"{self.src_ip}{self.dst_ip}{self.total_length}"
        return int(hashlib.md5(data.encode()).hexdigest()[:4], 16) & 0xFFFF


@dataclass
class TCPHeader:
    """TCP头"""
    src_port: int = 0
    dst_port: int = 0
    seq: int = 0
    ack: int = 0
    data_offset: int = 5
    flags: int = 0  # SYN, ACK, FIN, RST
    window: int = 65535
    checksum: int = 0
    urgent_ptr: int = 0

    # 标志位
    SYN_FLAG = 0x02
    ACK_FLAG = 0x10
    FIN_FLAG = 0x01
    RST_FLAG = 0x04


@dataclass
class UDPHeader:
    """UDP头"""
    src_port: int = 0
    dst_port: int = 0
    length: int = 0
    checksum: int = 0


class TCPSocket:
    """TCP套接字状态机"""
    def __init__(self, local_ip: str, local_port: int):
        self.local_ip = local_ip
        self.local_port = local_port
        self.remote_ip: Optional[str] = None
        self.remote_port: int = 0

        self.state = "CLOSED"
        self.seq = 0
        self.ack = 0

        # 缓冲区
        self.send_buffer = b''
        self.recv_buffer = b''


class TCPSocketTable:
    """TCP套接字表"""
    def __init__(self):
        self.sockets: Dict[Tuple[str, int], TCPSocket] = {}
        self.listen_queue: List[TCPSocket] = []

    def bind(self, sock: TCPSocket) -> bool:
        """绑定"""
        key = (sock.local_ip, sock.local_port)
        if key in self.sockets:
            return False
        self.sockets[key] = sock
        return True

    def listen(self, sock: TCPSocket, backlog: int = 5):
        """监听"""
        sock.state = "LISTEN"
        print(f"  TCP LISTEN on {sock.local_ip}:{sock.local_port}")

    def accept(self, sock: TCPSocket) -> Optional[TCPSocket]:
        """接受连接"""
        if self.listen_queue:
            client = self.listen_queue.pop(0)
            client.state = "ESTABLISHED"
            return client
        return None

    def connect(self, sock: TCPSocket, remote_ip: str, remote_port: int) -> bool:
        """连接"""
        sock.state = "SYN_SENT"
        sock.remote_ip = remote_ip
        sock.remote_port = remote_port
        print(f"  TCP SYN_SENT -> {remote_ip}:{remote_port}")
        sock.state = "ESTABLISHED"
        return True


class IPStack:
    """IP协议栈"""
    def __init__(self):
        self.tcp_sockets = TCPSocketTable()
        self.routes: Dict[str, str] = {}  # 目的网络 -> 下一跳

    def process_ip_packet(self, packet: bytes) -> bool:
        """处理IP包"""
        # 解析IP头（简化）
        print(f"  处理IP包: 长度={len(packet)}")
        return True

    def send_ip_packet(self, dst_ip: str, protocol: int, payload: bytes) -> bool:
        """发送IP包"""
        print(f"  发送IP包: dst={dst_ip}, proto={protocol}, len={len(payload)}")
        return True


def simulate_tcp_ip():
    """
    模拟TCP/IP协议栈
    """
    print("=" * 60)
    print("TCP/IP 协议栈")
    print("=" * 60)

    stack = IPStack()

    # TCP连接
    print("\n" + "-" * 50)
    print("TCP连接过程")
    print("-" * 50)

    # 服务器
    server = TCPSocket("0.0.0.0", 8080)
    stack.tcp_sockets.bind(server)
    stack.tcp_sockets.listen(server)

    # 客户端
    client = TCPSocket("192.168.1.100", 50000)
    print("\n客户端发起连接:")
    stack.tcp_sockets.connect(client, "192.168.1.1", 8080)

    # 接受
    print("\n服务器接受连接:")
    conn = stack.tcp_sockets.accept(server)
    if conn:
        print(f"  连接建立: {conn.local_ip}:{conn.local_port} <-> {conn.remote_ip}:{conn.remote_port}")

    # IP包处理
    print("\n" + "-" * 50)
    print("IP包处理")
    print("-" * 50)

    packet = b'\x00' * 20 + b'Data'
    stack.send_ip_packet("192.168.1.1", Protocol.TCP.value, packet)


if __name__ == "__main__":
    simulate_tcp_ip()
