# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / readers_writers

本文件实现 readers_writers 相关的算法功能。
"""

import threading
import time
import random


class Reader:
    """读者线程"""

    def __init__(self, name: str, db_mutex: threading.Lock, read_count_mutex: threading.Lock,
                 read_count_ref: list):
        self.name = name
        self.db = db_mutex
        self.read_count_lock = read_count_mutex
        self.read_count = read_count_ref

    def run(self, num_reads: int):
        for i in range(num_reads):
            # 获取读计数器的锁
            self.read_count_lock.acquire()
            self.read_count[0] += 1
            if self.read_count[0] == 1:
                # 第一个读者，等待数据库
                self.db.acquire()
            self.read_count_lock.release()

            # 读取数据库
            print(f"[{self.name}] 正在读取... (第{i+1}次)")
            time.sleep(random.uniform(0.1, 0.3))

            # 释放读计数器的锁
            self.read_count_lock.acquire()
            self.read_count[0] -= 1
            if self.read_count[0] == 0:
                # 最后一个读者，释放数据库
                self.db.release()
            self.read_count_lock.release()


class Writer:
    """写者线程"""

    def __init__(self, name: str, db_mutex: threading.Lock):
        self.name = name
        self.db = db_mutex

    def run(self, num_writes: int):
        for i in range(num_writes):
            # 等待数据库独占
            self.db.acquire()

            # 写入数据库
            print(f"[{self.name}] 正在写入... (第{i+1}次)")
            time.sleep(random.uniform(0.3, 0.6))

            # 释放数据库
            self.db.release()


def simulate_readers_preference(num_readers: int, num_writers: int,
                               reads_per_reader: int, writes_per_writer: int):
    """
    读者优先策略模拟

    读者优先可能导致写者饥饿
    """
    print("=== 读者优先策略 ===\n")

    db_mutex = threading.Lock()          # 数据库互斥锁
    read_count_mutex = threading.Lock()  # 读计数器互斥锁
    read_count = [0]                     # 当前读者数量

    readers = []
    writers = []

    # 创建读者线程
    for i in range(num_readers):
        r = Reader(f"Reader{i+1}", db_mutex, read_count_mutex, read_count)
        readers.append(r)

    # 创建写者线程
    for i in range(num_writers):
        w = Writer(f"Writer{i+1}", db_mutex)
        writers.append(w)

    # 启动所有线程
    threads = []
    for r in readers:
        t = threading.Thread(target=r.run, args=(reads_per_reader,))
        threads.append(t)
        t.start()

    for w in writers:
        t = threading.Thread(target=w.run, args=(writes_per_writer,))
        threads.append(t)
        t.start()

    # 等待完成
    for t in threads:
        t.join()

    print("\n所有线程完成")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 读者-写者问题模拟 ===\n")

    print("场景设置:")
    print("  读者: 3 个，各读 5 次")
    print("  写者: 2 个，各写 3 次\n")

    simulate_readers_preference(
        num_readers=3,
        num_writers=2,
        reads_per_reader=5,
        writes_per_writer=3
    )

    print("\n说明：")
    print("  - 多个读者可以同时读取")
    print("  - 写者需要独占访问")
    print("  - 读者优先可能导致写者饥饿（写者长时间等待）")
