# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / producer_consumer

本文件实现 producer_consumer 相关的算法功能。
"""

import threading
import queue
import time
import random


class Producer:
    """生产者线程"""

    def __init__(self, name: str, buffer: queue.Queue, max_size: int,
                 empty_sem: threading.Semaphore, full_sem: threading.Semaphore,
                 mutex: threading.Lock):
        self.name = name
        self.buffer = buffer
        self.max_size = max_size
        self.empty = empty_sem
        self.full = full_sem
        self.mutex = mutex
        self.items_produced = 0

    def run(self, num_items: int):
        for i in range(num_items):
            item = f"{self.name}-Item-{i+1}"
            self.empty.acquire()  # 等待有空位
            self.mutex.acquire()  # 进入临界区
            self.buffer.put(item)
            self.items_produced += 1
            print(f"[{self.name}] 生产: {item} | 缓冲区: {self.buffer.qsize()}")
            self.mutex.release()  # 离开临界区
            self.full.release()  # 增加已占用空间
            time.sleep(random.uniform(0.1, 0.5))


class Consumer:
    """消费者线程"""

    def __init__(self, name: str, buffer: queue.Queue,
                 empty_sem: threading.Semaphore, full_sem: threading.Semaphore,
                 mutex: threading.Lock):
        self.name = name
        self.buffer = buffer
        self.empty = empty_sem
        self.full = full_sem
        self.mutex = mutex
        self.items_consumed = 0

    def run(self, num_items: int):
        for i in range(num_items):
            self.full.acquire()  # 等待有数据
            self.mutex.acquire()  # 进入临界区
            item = self.buffer.get()
            self.items_consumed += 1
            print(f"[{self.name}] 消费: {item} | 缓冲区: {self.buffer.qsize()}")
            self.mutex.release()  # 离开临界区
            self.empty.release()  # 增加空位
            time.sleep(random.uniform(0.2, 0.6))


def simulate(num_producers: int, num_consumers: int, buffer_size: int,
             items_per_producer: int, items_per_consumer: int):
    """
    模拟生产者-消费者问题

    参数：
        num_producers: 生产者数量
        num_consumers: 消费者数量
        buffer_size: 缓冲区大小
        items_per_producer: 每个生产者生产的数量
        items_per_consumer: 每个消费者消费的数量
    """
    buffer = queue.Queue(maxsize=buffer_size)

    # 信号量
    empty = threading.Semaphore(buffer_size)  # 空位数量
    full = threading.Semaphore(0)             # 占用数量
    mutex = threading.Lock()                  # 互斥锁

    producers = []
    consumers = []

    # 创建生产者
    for i in range(num_producers):
        p = Producer(f"P{i+1}", buffer, buffer_size, empty, full, mutex)
        producers.append(p)

    # 创建消费者
    for i in range(num_consumers):
        c = Consumer(f"C{i+1}", buffer, empty, full, mutex)
        consumers.append(c)

    # 启动线程
    threads = []
    for p in producers:
        t = threading.Thread(target=p.run, args=(items_per_producer,))
        threads.append(t)
        t.start()

    for c in consumers:
        t = threading.Thread(target=c.run, args=(items_per_consumer,))
        threads.append(t)
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

    # 统计
    print("\n=== 统计 ===")
    total_produced = sum(p.items_produced for p in producers)
    total_consumed = sum(c.items_consumed for c in consumers)
    print(f"总生产: {total_produced}")
    print(f"总消费: {total_consumed}")
    print(f"最终缓冲区大小: {buffer.qsize()}")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 生产者-消费者问题模拟 ===\n")

    print("场景设置:")
    print("  生产者: 2 个")
    print("  消费者: 3 个")
    print("  缓冲区大小: 5")
    print("  每个生产者生产: 5 个")
    print("  每个消费者消费: 3 个\n")

    simulate(
        num_producers=2,
        num_consumers=3,
        buffer_size=5,
        items_per_producer=5,
        items_per_consumer=3
    )

    print("\n注意：总生产(10) >= 总消费(9)，部分数据留在缓冲区")
