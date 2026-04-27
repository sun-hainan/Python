# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / pipe_fifo

本文件实现 pipe_fifo 相关的算法功能。
"""

from typing import List, Optional, Dict
from collections import deque
import threading


class PipeBuffer:
    """管道缓冲区"""
    def __init__(self, capacity: int = 4096):
        self.capacity = capacity
        self.data = deque()
        self.readers: int = 0
        self.writers: int = 0
        self.eof: bool = False


class Pipe:
    """
    管道

    环形缓冲区实现。
    """

    PIPE_BUF = 4096  # POSIX定义的保证原子操作的最大字节数

    def __init__(self):
        self.buffer = deque()
        self.capacity = self.PIPE_BUF
        self.read_position = 0
        self.write_position = 0

        # 同步
        self.lock = threading.Lock()
        self.not_empty = threading.Condition(self.lock)
        self.not_full = threading.Condition(self.lock)

        # 状态
        self.readers = 0
        self.writers = 0
        self.eof = False
        self.broken = False

    def set_reader(self):
        """设置读取端"""
        self.readers += 1

    def unset_reader(self):
        """取消读取端"""
        self.readers -= 1
        if self.readers == 0:
            self.eof = True

    def set_writer(self):
        """设置写入端"""
        self.writers += 1

    def unset_writer(self):
        """取消写入端"""
        self.writers -= 1
        if self.writers == 0:
            self.eof = True

    def write(self, data: bytes) -> int:
        """
        写入管道
        return: 写入的字节数
        """
        if self.broken:
            return -1

        with self.not_full:
            while len(self.buffer) >= self.capacity and not self.broken:
                self.not_full.wait()

            if self.broken:
                return -1

            # 写入数据
            available = self.capacity - len(self.buffer)
            to_write = min(len(data), available)

            for i in range(to_write):
                self.buffer.append(data[i])

            self.not_empty.notify()

            return to_write

    def read(self, size: int = 4096) -> Optional[bytes]:
        """
        从管道读取
        return: 读取的数据，None表示EOF
        """
        if self.broken:
            return None

        with self.not_empty:
            while len(self.buffer) == 0 and not self.broken:
                if self.eof:
                    # 所有写者已关闭
                    return None
                self.not_empty.wait()

            if self.broken:
                return None

            # 读取数据
            result = []
            for _ in range(min(size, len(self.buffer))):
                if self.buffer:
                    result.append(self.buffer.popleft())

            self.not_full.notify()

            return bytes(result) if result else None

    def close_read(self):
        """关闭读端"""
        self.unset_reader()
        self.not_empty.notify_all()

    def close_write(self):
        """关闭写端"""
        self.unset_writer()
        self.eof = True
        self.not_empty.notify_all()

    def break_pipe(self):
        """破坏管道"""
        self.broken = True
        self.not_empty.notify_all()
        self.not_full.notify_all()


class FIFONode:
    """FIFO节点"""
    def __init__(self, path: str):
        self.path = path
        self.pipe = Pipe()
        self.mode = 0o644
        self.uid = 0
        self.gid = 0


class FIFOManager:
    """
    FIFO管理器

    管理命名管道。
    """

    def __init__(self):
        self.fifos: Dict[str, FIFONode] = {}

    def mkfifo(self, path: str, mode: int = 0o644) -> bool:
        """
        创建FIFO
        return: 是否成功
        """
        if path in self.fifos:
            return False

        fifo = FIFONode(path)
        fifo.mode = mode
        self.fifos[path] = fifo
        print(f"  mkfifo: 创建 {path}")
        return True

    def open(self, path: str, mode: str = 'r') -> Optional[Pipe]:
        """
        打开FIFO
        mode: 'r' 读, 'w' 写, 'rw' 读写
        return: Pipe对象
        """
        if path not in self.fifos:
            return None

        pipe = self.fifos[path].pipe

        if 'r' in mode:
            pipe.set_reader()
        if 'w' in mode:
            pipe.set_writer()

        return pipe

    def unlink(self, path: str) -> bool:
        """删除FIFO"""
        if path in self.fifos:
            del self.fifos[path]
            print(f"  unlink: 删除 {path}")
            return True
        return False


def simulate_pipe_fifo():
    """
    模拟管道和FIFO
    """
    print("=" * 60)
    print("管道 (Pipe) 与 FIFO")
    print("=" * 60)

    # 匿名管道演示
    print("\n" + "-" * 50)
    print("1. 匿名管道 (Pipe)")
    print("-" * 50)

    pipe = Pipe()
    pipe.set_reader()
    pipe.set_writer()

    print("\n创建管道: read_fd, write_fd")

    # 写入
    print("\n写入数据:")
    data1 = b"Hello, pipe!"
    n = pipe.write(data1)
    print(f"  write({len(data1)} bytes) -> {n} bytes")
    print(f"  缓冲区大小: {len(pipe.buffer)} bytes")

    # 读取
    print("\n读取数据:")
    read_data = pipe.read(100)
    print(f"  read(100) -> {len(read_data)} bytes")
    print(f"  数据: {read_data}")

    # 关闭写端并读取剩余
    print("\n关闭写端:")
    pipe.close_write()

    print("读取剩余数据:")
    read_data = pipe.read(100)
    print(f"  read(100) -> {len(read_data) if read_data else 'EOF'}")

    # FIFO演示
    print("\n" + "-" * 50)
    print("2. 有名管道 (FIFO)")
    print("-" * 50)

    manager = FIFOManager()

    print("\n创建FIFO /tmp/myfifo:")
    manager.mkfifo("/tmp/myfifo", mode=0o644)

    print("\n打开FIFO (读模式):")
    reader = manager.open("/tmp/myfifo", mode='r')

    print("\n打开FIFO (写模式):")
    writer = manager.open("/tmp/myfifo", mode='w')

    # 通过FIFO通信
    print("\n通过FIFO通信:")
    message = b"Message through FIFO"
    n = writer.write(message)
    print(f"  写入: {n} bytes")

    data = reader.read(1024)
    print(f"  读取: {len(data)} bytes - {data}")

    # 删除FIFO
    print("\n删除FIFO:")
    manager.unlink("/tmp/myfifo")

    # 管道特性
    print("\n" + "=" * 60)
    print("管道特性")
    print("=" * 60)
    print("""
    ┌─────────────────┬────────────────────────────────────┐
    │ 特性            │ 说明                               │
    ├─────────────────┼────────────────────────────────────┤
    │ 半双工          │ 数据单向流动                        │
    │ 字节流          │ 无消息边界                          │
    │ 容量有限        │ PIPE_BUF = 4096 bytes              │
    │ 原子性          │ <= PIPE_BUF 的写入保证原子性       │
    │ EOF             │ 所有写者关闭后，读到EOF              │
    └─────────────────┴────────────────────────────────────┘
    """)


if __name__ == "__main__":
    simulate_pipe_fifo()
