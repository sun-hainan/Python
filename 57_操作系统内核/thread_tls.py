# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / thread_tls



本文件实现 thread_tls 相关的算法功能。

"""



from typing import Dict, List, Optional, Set, Callable

from dataclasses import dataclass, field

import threading





@dataclass

class ThreadContext:

    """线程上下文"""

    esp: int = 0  # 栈指针

    eip: int = 0  # 程序计数器

    eax: int = 0

    ebx: int = 0

    ecx: int = 0

    edx: int = 0

    esi: int = 0

    edi: int = 0

    ebp: int = 0

    eflags: int = 0





class ThreadLocalStorage:

    """

    线程本地存储



    每个线程有独立的存储区域。

    """



    def __init__(self):

        self.thread_data: Dict[int, Dict[str, any]] = {}

        self.next_index = 0



    def allocate(self) -> int:

        """分配TLS索引"""

        idx = self.next_index

        self.next_index += 1

        return idx



    def set_thread_data(self, thread_id: int, key: str, value: any):

        """设置线程数据"""

        if thread_id not in self.thread_data:

            self.thread_data[thread_id] = {}

        self.thread_data[thread_id][key] = value



    def get_thread_data(self, thread_id: int, key: str) -> any:

        """获取线程数据"""

        if thread_id in self.thread_data:

            return self.thread_data[thread_id].get(key)

        return None



    def get_current_thread_data(self, key: str) -> any:

        """获取当前线程的数据"""

        thread_id = threading.current_thread().ident

        return self.get_thread_data(thread_id, key)



    def set_current_thread_data(self, key: str, value: any):

        """设置当前线程的数据"""

        thread_id = threading.current_thread().ident

        self.set_thread_data(thread_id, key, value)





class Thread:

    """

    线程



    轻量级执行单元。

    """



    def __init__(self, tid: int, name: str):

        self.tid = tid

        self.name = name



        # 状态

        self.state = "RUNNING"  # RUNNING, BLOCKED, TERMINATED

        self.priority = 0



        # 上下文

        self.ctx = ThreadContext()



        # 栈

        self.stack_size = 0

        self.stack_base = 0



        # TLS

        self.tls_data: Dict[int, any] = {}



        # 函数

        self.start_routine: Optional[Callable] = None

        self.arg: any = None



        # 父子线程

        self.process_id: int = 0

        self.parent_tid: int = 0



    def set_tls(self, index: int, value: any):

        """设置TLS"""

        self.tls_data[index] = value



    def get_tls(self, index: int) -> any:

        """获取TLS"""

        return self.tls_data.get(index)





class ThreadManager:

    """

    线程管理器



    管理进程内的线程。

    """



    def __init__(self, process_id: int):

        self.process_id = process_id

        self.threads: Dict[int, Thread] = {}

        self.next_tid = 1



        # TLS

        self.tls = ThreadLocalStorage()

        self.tls_indices: Dict[str, int] = {}



        # 主线程

        self.create_thread("main", None, None)



    def create_thread(self, name: str, routine: Callable, arg: any) -> Thread:

        """创建线程"""

        tid = self.next_tid

        self.next_tid += 1



        thread = Thread(tid, name)

        thread.process_id = self.process_id

        thread.start_routine = routine

        thread.arg = arg

        thread.parent_tid = 1  # 假设主线程



        self.threads[tid] = thread

        return thread



    def get_thread(self, tid: int) -> Optional[Thread]:

        """获取线程"""

        return self.threads.get(tid)



    def exit_thread(self, tid: int, exit_code: int = 0):

        """线程退出"""

        if tid in self.threads:

            self.threads[tid].state = "TERMINATED"

            print(f"  线程 {self.threads[tid].name} (TID={tid}) 退出, exit_code={exit_code}")



    def join_thread(self, tid: int) -> int:

        """等待线程结束"""

        if tid in self.threads:

            thread = self.threads[tid]

            # 简化：直接返回

            return 0

        return -1



    def allocate_tls_key(self, key: str) -> int:

        """分配TLS键"""

        if key not in self.tls_indices:

            self.tls_indices[key] = self.tls.allocate()

        return self.tls_indices[key]



    def set_tls(self, tid: int, key: str, value: any):

        """设置TLS"""

        idx = self.allocate_tls_key(key)

        thread = self.get_thread(tid)

        if thread:

            thread.set_tls(idx, value)



    def get_tls(self, tid: int, key: str) -> any:

        """获取TLS"""

        idx = self.tls_indices.get(key)

        if idx is None:

            return None

        thread = self.get_thread(tid)

        if thread:

            return thread.get_tls(idx)

        return None





def simulate_threads():

    """

    模拟线程和TLS

    """

    print("=" * 60)

    print("线程实现与线程本地存储 (TLS)")

    print("=" * 60)



    # 创建线程管理器

    manager = ThreadManager(process_id=1234)



    print(f"\n进程 PID=1234 创建完成")

    print(f"主线程 TID=1: {manager.threads[1].name}")



    # 创建工作线程

    print("\n" + "-" * 50)

    print("创建线程")

    print("-" * 50)



    def worker(arg):

        print(f"  工作线程运行, 参数={arg}")

        return 42



    worker_thread = manager.create_thread("worker", worker, "hello")

    print(f"创建工作线程:")

    print(f"  TID={worker_thread.tid}, name={worker_thread.name}")

    print(f"  栈大小={worker_thread.stack_size}, 优先级={worker_thread.priority}")



    # TLS演示

    print("\n" + "-" * 50)

    print("线程本地存储 (TLS)")

    print("-" * 50)



    print("\n分配TLS键:")

    errno_idx = manager.allocate_tls_key("errno")

    print(f"  'errno' -> index={errno_idx}")



    thread_idx = manager.allocate_tls_key("thread_local")

    print(f"  'thread_local' -> index={thread_idx}")



    # 设置TLS值

    print("\n设置TLS值:")

    manager.set_tls(1, "errno", 42)

    manager.set_tls(worker_thread.tid, "errno", 100)



    print(f"\n读取TLS值:")

    val1 = manager.get_tls(1, "errno")

    val2 = manager.get_tls(worker_thread.tid, "errno")

    print(f"  主线程 errno: {val1}")

    print(f"  工作线程 errno: {val2}")

    print(f"  (每个线程有独立的值)")



    # 线程状态

    print("\n" + "-" * 50)

    print("线程状态")

    print("-" * 50)



    print("\n线程列表:")

    for tid, thread in manager.threads.items():

        print(f"  TID={tid}: {thread.name} (state={thread.state})")



    # 线程退出

    print("\n线程退出:")

    manager.exit_thread(worker_thread.tid, exit_code=42)



    print("\n退出后线程列表:")

    for tid, thread in manager.threads.items():

        print(f"  TID={tid}: {thread.name} (state={thread.state})")



    # 线程vs进程

    print("\n" + "=" * 60)

    print("线程 vs 进程")

    print("=" * 60)

    print("""

    ┌──────────┬─────────────────────┬─────────────────────┐

    │ 特性      │ 进程                │ 线程                │

    ├──────────┼─────────────────────┼─────────────────────┤

    │ 资源      │ 独立地址空间        │ 共享地址空间        │

    │ 开销      │ 大（fork）          │ 小（clone）         │

    │ 通信      │ IPC复杂             │ 直接读写共享内存    │

    │ 切换      │ 慢（切换页表）      │ 快（不切换页表）    │

    │ 同步      │ 必须（进程间）       │ 必须（线程间）      │

    └──────────┴─────────────────────┴─────────────────────┘

    """)





if __name__ == "__main__":

    simulate_threads()

