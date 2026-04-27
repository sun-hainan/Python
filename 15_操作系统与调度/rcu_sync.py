# -*- coding: utf-8 -*-

"""

算法实现：15_操作系统与调度 / rcu_sync



本文件实现 rcu_sync 相关的算法功能。

"""



from dataclasses import dataclass, field

from typing import Optional, Callable, Any

import threading

import time





@dataclass

class RCUReader:

    """RCU读者（读取临界区）"""

    id: int

    critical_section: Callable  # 读取操作回调

    grace_period_completed: bool = False





class RCUGracPeriod:

    """RCU宽限期（grace period）"""

    gp_id: int

    start_time: float

    end_time: Optional[float] = None

    registered_readers: list[int] = field(default_factory=list)





class RCUSynchronize:

    """RCU同步机制（简化实现）"""



    def __init__(self):

        self.readers: list[RCUReader] = []

        self. grace_periods: list[RCUGracPeriod] = []

        self.gp_counter = 0

        self.lock = threading.Lock()



    def register_reader(self, reader_id: int):

        """读者注册（进入读取临界区）"""

        with self.lock:

            reader = RCUReader(id=reader_id, critical_section=lambda: None)

            self.readers.append(reader)



    def unregister_reader(self, reader_id: int):

        """读者注销（退出读取临界区）"""

        with self.lock:

            self.readers = [r for r in self.readers if r.id != reader_id]



    def synchronize(self):

        """

        synchronize_rcu() 实现

        等待所有在调用之前开始的读者完成

        原理：

        1. 注册一个reader

        2. 等待所有旧reader完成

        3. 注销自己

        """

        # 获取当前活跃的读者快照

        with self.lock:

            active_readers = self.readers.copy()



        # 注册为新的"等待点"

        wait_reader_id = -1

        with self.lock:

            wait_reader_id = max((r.id for r in self.readers), default=0) + 1

            wait_reader = RCUReader(id=wait_reader_id, critical_section=lambda: None)

            self.readers.append(wait_reader)



        # 等待所有旧读者完成（通过检查grac_period）

        # 简化：直接等待所有读者完成

        max_wait = 100  # 最大等待次数

        waited = 0

        while waited < max_wait:

            time.sleep(0.001)  # 模拟等待

            with self.lock:

                # 等待直到只有wait_reader存在

                other_readers = [r for r in self.readers if r.id != wait_reader_id]

                if not other_readers:

                    break

            waited += 1



        # 注销等待读者

        with self.lock:

            self.readers = [r for r in self.readers if r.id != wait_reader_id]



        # 记录宽限期完成

        gp = RCUGracPeriod(gp_id=self.gp_counter, start_time=time.time())

        gp.end_time = time.time()

        self.grace_periods.append(gp)

        self.gp_counter += 1





class RCULinkedListNode:

    """RCU保护的链表节点"""

    def __init__(self, key: int, value: Any):

        self.key = key

        self.value = value

        self.next: Optional["RCULinkedListNode"] = None





class RCULinkedList:

    """

    RCU保护的链表

    读者：直接遍历，无锁

    写者：创建新节点，原子替换指针

    """



    def __init__(self):

        self.head: Optional[RCULinkedListNode] = None

        self.rcu = RCUSynchronize()



    def read_find(self, key: int) -> Optional[Any]:

        """

        读取操作（无锁）

        """

        # 读者临界区开始

        self.rcu.register_reader(threading.current_thread().ident or 0)



        current = self.head

        result = None

        while current:

            if current.key == key:

                result = current.value

                break

            current = current.next



        # 读者临界区结束

        self.rcu.unregister_reader(threading.current_thread().ident or 0)



        return result



    def read_traverse(self) -> list:

        """遍历整个链表"""

        self.rcu.register_reader(threading.current_thread().ident or 0)



        result = []

        current = self.head

        while current:

            result.append((current.key, current.value))

            current = current.next



        self.rcu.unregister_reader(threading.current_thread().ident or 0)

        return result



    def insert(self, key: int, value: Any):

        """

        插入操作（Copy-Update）

        1. 创建新节点

        2. 新节点.next = 旧head

        3. 原子替换head

        """

        new_node = RCULinkedListNode(key, value)

        new_node.next = self.head

        self.head = new_node  # 简化：非原子替换



    def delete(self, key: int) -> bool:

        """

        删除操作（延迟删除）

        1. 找到前驱节点

        2. 修改next指针

        3. 调用synchronize_rcu()

        4. 释放旧节点

        """

        # 简化实现

        if self.head is None:

            return False



        if self.head.key == key:

            old_head = self.head

            self.head = self.head.next

            # 等待宽限期后释放

            self.rcu.synchronize()

            return True



        current = self.head

        while current.next:

            if current.next.key == key:

                current.next = current.next.next

                self.rcu.synchronize()

                return True

            current = current.next



        return False





if __name__ == "__main__":

    print("=== RCU同步原语演示 ===")



    rcu_list = RCULinkedList()



    # 并发读测试

    print("\n--- 插入数据 ---")

    for i in range(10):

        rcu_list.insert(i, f"value_{i}")

    print(f"链表内容: {rcu_list.read_traverse()}")



    # 读取测试（无锁）

    print("\n--- 读取操作（无锁） ---")

    for key in [3, 7, 15]:

        val = rcu_list.read_find(key)

        print(f"查找key={key}: {val if val else '未找到'}")



    # 模拟并发读写

    print("\n--- 模拟并发读写 ---")

    import threading



    read_count = [0]

    write_count = [0]

    lock = threading.Lock()



    def reader_thread():

        for _ in range(100):

            rcu_list.read_find(5)

            with lock:

                read_count[0] += 1



    def writer_thread():

        for i in range(20, 30):

            rcu_list.insert(i, f"new_value_{i}")

            with lock:

                write_count[0] += 1



    threads = []

    for _ in range(5):

        t = threading.Thread(target=reader_thread)

        threads.append(t)

    for _ in range(2):

        t = threading.Thread(target=writer_thread)

        threads.append(t)



    for t in threads:

        t.start()

    for t in threads:

        t.join()



    print(f"读操作完成: {read_count[0]}")

    print(f"写操作完成: {write_count[0]}")

    print(f"链表长度: {len(rcu_list.read_traverse())}")



    # 删除测试

    print("\n--- 删除操作 ---")

    print(f"删除key=5: {rcu_list.delete(5)}")

    print(f"链表内容: {rcu_list.read_traverse()}")



    # RCU优势说明

    print("\n=== RCU vs 传统锁 ===")

    print("| 特性       | RCU          | Mutex/RWLock |")

    print("|------------|--------------|--------------|")

    print("| 读延迟     | 无锁（极低）  | 加锁开销     |")

    print("| 读吞吐量   | 高（无竞争）  | 有限         |")

    print("| 写延迟     | 较高（复制）  | 中等         |")

    print("| 内存开销   | 延迟释放     | 立即释放     |")

    print("| 适用场景   | 高读低写     | 写多读少     |")

