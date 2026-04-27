# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / kernel_sync

本文件实现 kernel_sync 相关的算法功能。
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum
import threading
import time


class Spinlock:
    """
    自旋锁

    不断轮询直到获取锁。
    适用于临界区非常短的情况。
    """

    def __init__(self, name: str = ""):
        self.name = name
        self.locked = False
        self.owner = -1  # 持有者线程ID
        self.contention_count = 0

    def lock(self):
        """获取锁（忙等待）"""
        while True:
            # 尝试原子交换
            if not self.locked:
                # 简化：在单线程模拟中直接获取
                if not self.locked:
                    self.locked = True
                    self.owner = threading.current_thread().ident
                    return
            self.contention_count += 1
            # 实际会使用 atomic instruction (x86的LOCK CMPXCHG)

    def unlock(self):
        """释放锁"""
        self.locked = False
        self.owner = -1

    def is_locked(self) -> bool:
        """检查锁状态"""
        return self.locked


class Mutex:
    """
    互斥锁

    可以睡眠的锁。
    当锁不可用时，线程进入睡眠状态。
    """

    def __init__(self, name: str = ""):
        self.name = name
        self.locked = False
        self.owner = -1
        self.wait_queue: List[int] = []  # 等待的线程ID
        self.contention_count = 0

    def lock(self):
        """获取锁（可能睡眠）"""
        if not self.locked:
            self.locked = True
            self.owner = threading.current_thread().ident
            return

        self.contention_count += 1
        # 实际会调用schedule()让出CPU
        while self.locked:
            time.sleep(0.001)

        self.locked = True
        self.owner = threading.current_thread().ident

    def unlock(self):
        """释放锁"""
        self.locked = False
        self.owner = -1


class RCUReader:
    """RCU读者上下文"""
    def __init__(self):
        self.read_count = 0


class RCU:
    """
    RCU (Read-Copy-Update)

    读多写少场景下的无锁同步。
    读者：直接访问，无需锁
    写者：复制修改，延迟释放旧数据
    """

    def __init__(self):
        self.data: Any = None
        self.old_data: Any = None

        # 读者计数
        self.active_readers: Set[int] = set()

        # 待删除的数据
        self.pending_free: List[Any] = []

        # grace period计数
        self.grace_period_count = 0

    def read_lock(self) -> RCUReader:
        """读端进入临界区"""
        reader = RCUReader()
        reader.read_count = len(self.active_readers)
        self.active_readers.add(id(reader))
        return reader

    def read_unlock(self, reader: RCUReader):
        """读端离开临界区"""
        self.active_readers.discard(id(reader))

    def write_lock(self):
        """写端进入临界区（实际不需要真正加锁）"""
        pass

    def write_unlock(self):
        """写端离开临界区"""
        pass

    def update(self, new_data: Any):
        """
        更新数据
        写者调用：原子替换，并安排旧数据延迟释放
        """
        self.write_lock()

        # 保存旧数据引用
        self.old_data = self.data

        # 原子替换
        self.data = new_data

        self.write_unlock()

        # 旧数据延迟释放（等待所有读者完成）
        if self.old_data is not None:
            self.pending_free.append(self.old_data)

    def synchronize_rcu(self):
        """
        等待所有正在进行的读者完成
        这是一个grace period
        """
        # 等待所有读者离开临界区
        while len(self.active_readers) > 0:
            time.sleep(0.001)

        # 现在可以安全释放旧数据
        self._free_pending()

        self.grace_period_count += 1

    def _free_pending(self):
        """释放待删除的数据"""
        for data in self.pending_free:
            # 实际会调用kfree
            pass
        self.pending_free.clear()


class PerCPUVariable:
    """
    per-CPU变量

    每个CPU有独立的数据副本。
    访问时使用当前CPU的副本，天然避免同步。
    """

    def __init__(self, name: str, num_cpus: int = 4):
        self.name = name
        self.num_cpus = num_cpus
        # 每个CPU的数据副本
        self.per_cpu_data: Dict[int, Any] = {i: 0 for i in range(num_cpus)}
        self.cpu_local_cache: Dict[int, Any] = {}  # CPU本地缓存

    def get_cpu(self) -> int:
        """获取当前CPU ID（简化）"""
        return 0

    def get_value(self) -> Any:
        """获取当前CPU的值"""
        cpu = self.get_cpu()
        return self.per_cpu_data[cpu]

    def set_value(self, value: Any):
        """设置当前CPU的值"""
        cpu = self.get_cpu()
        self.per_cpu_data[cpu] = value

    def add_value(self, delta: Any):
        """当前CPU值增加"""
        cpu = self.get_cpu()
        self.per_cpu_data[cpu] += delta

    def per_cpu_ptr(self, cpu: int) -> Any:
        """获取指定CPU的数据指针"""
        return self.per_cpu_data[cpu]

    def get_all_values(self) -> Dict[int, Any]:
        """获取所有CPU的值"""
        return self.per_cpu_data.copy()


class SchedulerStats:
    """
    per-CPU调度统计（per-CPU变量的典型应用）
    """
    def __init__(self, num_cpus: int = 4):
        self.num_cpus = num_cpus

        # per-CPU变量
        self.runqueue_length = PerCPUVariable("runqueue_length", num_cpus)
        self.context_switch_count = PerCPUVariable("context_switch_count", num_cpus)
        self.idle_time = PerCPUVariable("idle_time", num_cpus)

        # 初始化
        for cpu in range(num_cpus):
            # 使用cpu_local_ptr直接设置
            pass

    def inc_runqueue(self, cpu: int, delta: int = 1):
        """增加运行队列长度"""
        # 简化
        pass

    def inc_switches(self, cpu: int):
        """增加上下文切换计数"""
        pass


def simulate_synchronization():
    """
    模拟内核同步原语
    """
    print("=" * 60)
    print("内核同步原语")
    print("=" * 60)

    # 自旋锁演示
    print("\n" + "-" * 50)
    print("1. 自旋锁 (Spinlock)")
    print("-" * 50)

    spinlock = Spinlock("test_lock")

    print(f"\n初始状态: locked={spinlock.is_locked()}")
    print("获取锁...")
    spinlock.lock()
    print(f"获取后状态: locked={spinlock.is_locked()}, owner={spinlock.owner}")
    print("释放锁...")
    spinlock.unlock()
    print(f"释放后状态: locked={spinlock.is_locked()}")

    # 互斥锁演示
    print("\n" + "-" * 50)
    print("2. 互斥锁 (Mutex)")
    print("-" * 50)

    mutex = Mutex("test_mutex")

    print(f"\n初始状态: locked={mutex.locked}")
    print("获取锁...")
    mutex.lock()
    print(f"获取后状态: locked={mutex.locked}, owner={mutex.owner}")
    print("释放锁...")
    mutex.unlock()
    print(f"释放后状态: locked={mutex.locked}")

    # RCU演示
    print("\n" + "-" * 50)
    print("3. RCU (Read-Copy-Update)")
    print("-" * 50)

    rcu = RCU()

    # 初始化数据
    initial_data = {"value": 100}
    rcu.data = initial_data
    print(f"\n初始数据: {rcu.data}")

    # 读者
    print("\n多个读者同时读取（无需锁）:")
    readers = []
    for i in range(3):
        reader = rcu.read_lock()
        readers.append(reader)
        print(f"  读者{i} 进入临界区, 读取数据: {rcu.data}")
        print(f"  当前活跃读者数: {len(rcu.active_readers)}")

    # 写者更新
    print("\n写者更新数据:")
    new_data = {"value": 200}
    rcu.update(new_data)
    print(f"  新数据: {rcu.data}")

    # 释放读者
    print("\n所有读者离开临界区:")
    for i, reader in enumerate(readers):
        rcu.read_unlock(reader)
        print(f"  读者{i} 离开, 活跃读者数: {len(rcu.active_readers)}")

    # 等待grace period
    print("\n调用 synchronize_rcu() 等待grace period完成:")
    rcu.synchronize_rcu()
    print(f"  grace period {rcu.grace_period_count} 完成")
    print(f"  旧数据已安全释放")

    # per-CPU变量演示
    print("\n" + "-" * 50)
    print("4. per-CPU变量")
    print("-" * 50)

    per_cpu_var = PerCPUVariable("test_counter", num_cpus=4)

    print("\n设置各CPU的值:")
    for cpu in range(4):
        per_cpu_var.per_cpu_data[cpu] = cpu * 10
        print(f"  CPU{cpu}: value={per_cpu_var.per_cpu_data[cpu]}")

    print(f"\n当前CPU的值: {per_cpu_var.get_value()}")
    print(f"所有CPU的值: {per_cpu_var.get_all_values()}")

    # 调度统计示例
    print("\nper-CPU调度统计:")
    print("-" * 50)

    stats = SchedulerStats(num_cpus=4)

    # 模拟各CPU的调度统计
    for cpu in range(4):
        stats.runqueue_length.per_cpu_data[cpu] = 5 + cpu
        stats.context_switch_count.per_cpu_data[cpu] = 1000 + cpu * 100

    print("\n运行队列长度:")
    for cpu, length in stats.runqueue_length.get_all_values().items():
        print(f"  CPU{cpu}: {length} 个任务")

    print("\n上下文切换次数:")
    for cpu, count in stats.context_switch_count.get_all_values().items():
        print(f"  CPU{cpu}: {count} 次")


if __name__ == "__main__":
    simulate_synchronization()
