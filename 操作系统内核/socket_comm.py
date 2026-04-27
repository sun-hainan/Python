# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / socket_comm



本文件实现 socket_comm 相关的算法功能。

"""



from typing import Dict, List, Optional, Set, Tuple

from dataclasses import dataclass

from enum import Enum

import hashlib





class SocketDomain(Enum):

    """套接字域"""

    AF_UNIX = 1

    AF_INET = 2

    AF_INET6 = 3





class SocketType(Enum):

    """套接字类型"""

    SOCK_STREAM = 1

    SOCK_DGRAM = 2

    SOCK_RAW = 3





class SocketState(Enum):

    """套接字状态"""

    UNCONNECTED = "unconnected"

    CONNECTING = "connecting"

    CONNECTED = "connected"

    LISTENING = "listening"

    CLOSED = "closed"





@dataclass

class SocketAddress:

    """套接字地址"""

    family: int = SocketDomain.AF_INET.value

    port: int = 0

    address: str = "0.0.0.0"



    def __repr__(self):

        if self.family == SocketDomain.AF_UNIX.value:

            return self.address

        return f"{self.address}:{self.port}"





class SocketBuffer:

    """套接字缓冲区"""

    def __init__(self, capacity: int = 65536):

        self.capacity = capacity

        self.data = b''

        self.seq = 0  # 序列号





class Socket:

    """套接字"""

    def __init__(self, domain: SocketDomain, type: SocketType, protocol: int = 0):

        self.domain = domain

        self.type = type

        self.protocol = protocol

        self.state = SocketState.UNCONNECTED



        # 文件描述符

        self.fd: Optional[int] = None



        # 地址

        self.local_addr: Optional[SocketAddress] = None

        self.remote_addr: Optional[SocketAddress] = None



        # 缓冲区

        self.recv_buffer = SocketBuffer()

        self.send_buffer = SocketBuffer()



        # 连接

        self.peer: Optional[Socket] = None



        # 监听队列

        self.listen_queue: List[Socket] = []

        self.backlog: int = 0



    def bind(self, addr: SocketAddress) -> bool:

        """绑定地址"""

        self.local_addr = addr

        print(f"  bind: {addr}")

        return True



    def listen(self, backlog: int = 5) -> bool:

        """监听连接"""

        self.state = SocketState.LISTENING

        self.backlog = backlog

        print(f"  listen: backlog={backlog}")

        return True



    def accept(self) -> Optional['Socket']:

        """接受连接"""

        if self.state != SocketState.LISTENING:

            return None



        if not self.listen_queue:

            return None



        client = self.listen_queue.pop(0)

        client.state = SocketState.CONNECTED

        print(f"  accept: 新连接 from {client.remote_addr}")

        return client



    def connect(self, addr: SocketAddress) -> bool:

        """连接"""

        self.state = SocketState.CONNECTING

        self.remote_addr = addr

        print(f"  connect: {addr}")

        self.state = SocketState.CONNECTED

        return True



    def send(self, data: bytes) -> int:

        """发送数据"""

        if self.state != SocketState.CONNECTED:

            return -1



        if self.type == SocketType.SOCK_STREAM:

            # TCP: 添加到发送缓冲区

            self.send_buffer.data += data

        else:

            # UDP: 直接发送

            pass



        print(f"  send: {len(data)} bytes")

        return len(data)



    def recv(self, size: int = 4096) -> Optional[bytes]:

        """接收数据"""

        if self.state != SocketState.CONNECTED:

            return None



        if not self.recv_buffer.data:

            return None



        data = self.recv_buffer.data[:size]

        self.recv_buffer.data = self.recv_buffer.data[size:]

        print(f"  recv: {len(data)} bytes")

        return data



    def close(self):

        """关闭套接字"""

        self.state = SocketState.CLOSED

        print(f"  close: {self}")





class InetHashTable:

    """_INET协议哈希表（简化）"""

    def __init__(self, size: int = 16):

        self.size = size

        self.table: List[List[Socket]] = [[] for _ in range(size)]



    def _hash(self, addr: SocketAddress) -> int:

        """哈希函数"""

        key = f"{addr.address}:{addr.port}"

        return int(hashlib.md5(key.encode()).hexdigest()[:4], 16) % self.size



    def insert(self, sock: Socket):

        """插入"""

        if sock.local_addr:

            idx = self._hash(sock.local_addr)

            self.table[idx].append(sock)



    def remove(self, sock: Socket):

        """移除"""

        if sock.local_addr:

            idx = self._hash(sock.local_addr)

            if sock in self.table[idx]:

                self.table[idx].remove(sock)





class SocketSimulator:

    """套接字模拟器"""



    def __init__(self):

        self.sockets: Dict[int, Socket] = {}

        self.next_fd = 3  # 0,1,2被标准IO占用

        self.inet_table = InetHashTable()



    def socket(self, domain: SocketDomain, type: SocketType, protocol: int = 0) -> Optional[int]:

        """创建套接字"""

        sock = Socket(domain, type, protocol)

        fd = self.next_fd

        self.next_fd += 1

        sock.fd = fd

        self.sockets[fd] = sock

        print(f"  socket(FD={fd}): {domain.name}, {type.name}")

        return fd



    def bind(self, fd: int, addr: SocketAddress) -> bool:

        """绑定"""

        if fd not in self.sockets:

            return False

        return self.sockets[fd].bind(addr)



    def listen(self, fd: int, backlog: int = 5) -> bool:

        """监听"""

        if fd not in self.sockets:

            return False

        return self.sockets[fd].listen(backlog)



    def accept(self, fd: int) -> Optional[int]:

        """接受"""

        if fd not in self.sockets:

            return None

        server = self.sockets[fd]

        client = server.accept()

        if client:

            self.sockets[client.fd] = client

            return client.fd

        return None



    def connect(self, fd: int, addr: SocketAddress) -> bool:

        """连接"""

        if fd not in self.sockets:

            return False

        return self.sockets[fd].connect(addr)



    def send(self, fd: int, data: bytes) -> int:

        """发送"""

        if fd not in self.sockets:

            return -1

        return self.sockets[fd].send(data)



    def recv(self, fd: int, size: int = 4096) -> Optional[bytes]:

        """接收"""

        if fd not in self.sockets:

            return None

        return self.sockets[fd].recv(size)



    def close(self, fd: int):

        """关闭"""

        if fd in self.sockets:

            self.sockets[fd].close()

            del self.sockets[fd]





def simulate_socket():

    """

    模拟套接字通信

    """

    print("=" * 60)

    print("套接字 (Socket) 通信")

    print("=" * 60)



    sim = SocketSimulator()



    # TCP服务器/客户端演示

    print("\n" + "-" * 50)

    print("TCP 服务器/客户端")

    print("-" * 50)



    # 创建服务器套接字

    server_fd = sim.socket(SocketDomain.AF_INET, SocketType.SOCK_STREAM)

    server_addr = SocketAddress(family=SocketDomain.AF_INET.value,

                                address="0.0.0.0", port=8080)

    sim.bind(server_fd, server_addr)

    sim.listen(server_fd, backlog=5)



    # 创建客户端套接字

    client_fd = sim.socket(SocketDomain.AF_INET, SocketType.SOCK_STREAM)

    client_addr = SocketAddress(family=SocketDomain.AF_INET.value,

                                address="127.0.0.1", port=8080)

    sim.connect(client_fd, client_addr)



    # 模拟连接建立

    server = sim.sockets[server_fd]

    client = sim.sockets[client_fd]

    client.peer = server

    server.listen_queue.append(client)



    # 接受连接

    conn_fd = sim.accept(server_fd)



    # 通过连接通信

    print("\n发送/接收数据:")

    data = b"Hello, TCP socket!"

    n = sim.send(conn_fd, data)

    print(f"  发送: {n} bytes")



    # 模拟接收（通过缓冲区）

    if conn_fd and conn_fd in sim.sockets:

        conn = sim.sockets[conn_fd]

        conn.recv_buffer.data = b"Response from server!"

        response = sim.recv(conn_fd, 1024)

        print(f"  接收: {response}")



    # 关闭

    print("\n关闭连接:")

    sim.close(client_fd)

    sim.close(conn_fd)

    sim.close(server_fd)



    # UDP演示

    print("\n" + "-" * 50)

    print("UDP 数据报")

    print("-" * 50)



    # 创建UDP套接字

    udp_fd = sim.socket(SocketDomain.AF_INET, SocketType.SOCK_DGRAM)

    udp_addr = SocketAddress(family=SocketDomain.AF_INET.value,

                              address="0.0.0.0", port=9000)

    sim.bind(udp_fd, udp_addr)



    # 发送数据报

    print("\n发送数据报:")

    sim.send(udp_fd, b"Hello, UDP!")



    # 关闭

    sim.close(udp_fd)



    # 套接字类型总结

    print("\n" + "=" * 60)

    print("套接字类型总结")

    print("=" * 60)

    print("""

    ┌──────────┬──────────────┬─────────────┬──────────────┐

    │ 协议      │ 类型         │ 特性         │ 适用场景      │

    ├──────────┼──────────────┼─────────────┼──────────────┤

    │ TCP      │ SOCK_STREAM  │ 面向连接     │ 文件传输     │

    │          │              │ 可靠        │ HTTP        │

    │          │              │ 字节流      │ 邮件        │

    ├──────────┼──────────────┼─────────────┼──────────────┤

    │ UDP      │ SOCK_DGRAM   │ 无连接      │ DNS         │

    │          │              │ 不可靠      │ 视频流      │

    │          │              │ 数据报      │ 游戏        │

    ├──────────┼──────────────┼─────────────┼──────────────┤

    │ Unix     │ AF_UNIX      │ 本地通信    │ 进程间通信   │

    │          │              │ 高效        │ 守护进程    │

    └──────────┴──────────────┴─────────────┴──────────────┘

    """)





if __name__ == "__main__":

    simulate_socket()

