# -*- coding: utf-8 -*-
"""
算法实现：并行算法 / work_stealing

本文件实现 work_stealing 相关的算法功能。
"""

import threading
import random
from collections import deque


class WorkStealingQueue:
    """工作窃取队列"""

    def __init__(self, thread_id: int):
        self.thread_id = thread_id
        self.queue = deque()
        self.lock = threading.Lock()

    def push(self, item):
        """本地push（高效）"""
        with self.lock:
            self.queue.append(item)

    def pop_local(self):
        """本地pop（高效）"""
        with self.lock:
            if self.queue:
                return self.queue.pop()
            return None

    def steal(self, victim):
        """
        从victim队列头部偷一个任务

        返回：偷到的任务 或 None
        """
        with victim.lock:
            if victim.queue:
                return victim.queue.popleft()
            return None


class Worker:
    """工作线程"""

    def __init__(self, worker_id: int, queues: list, work_func):
        self.worker_id = worker_id
        self.queues = queues
        self.work_func = work_func
        self.my_queue = queues[worker_id]
        self.processed = 0

    def run(self, tasks_per_worker: int):
        """执行工作"""
        # 每个worker首先获得本地任务
        for _ in range(tasks_per_worker):
            task = self.my_queue.pop_local()

            # 如果本地没有，尝试偷
            if task is None:
                # 随机选择一个victim
                for _ in range(len(self.queues)):
                    victim_id = random.randint(0, len(self.queues) - 1)
                    if victim_id != self.worker_id:
                        task = self.my_queue.steal(self.queues[victim_id])
                        if task is not None:
                            break

            if task is not None:
                self.work_func(task)
                self.processed += 1


def work_stealing_demo(num_workers: int = 4, total_tasks: int = 100):
    """
    工作窃取演示

    参数：
        num_workers: 工作线程数
        total_tasks: 总任务数
    """
    print("=== 工作窃取算法演示 ===\n")
    print(f"工作线程: {num_workers}")
    print(f"总任务数: {total_tasks}\n")

    # 创建队列
    queues = [WorkStealingQueue(i) for i in range(num_workers)]

    # 初始分配任务（不均匀分布，模拟负载不均）
    tasks_per_queue = total_tasks // num_workers
    remainder = total_tasks % num_workers

    for i in range(num_workers):
        n_i = tasks_per_queue + (1 if i < remainder else 0)
        for _ in range(n_i):
            queues[i].push(random.randint(1, 100))

    print("初始任务分布：")
    for i, q in enumerate(queues):
        with q.lock:
            print(f"  队列{i}: {len(q.queue)} 个任务")

    # 工作函数
    def process_task(task):
        pass  # 模拟处理

    results = []

    def worker_run(worker_id):
        q = queues[worker_id]
        processed = 0
        while True:
            task = q.pop_local()
            if task is None:
                # 尝试偷
                stolen = False
                for _ in range(num_workers):
                    victim_id = random.randint(0, num_workers - 1)
                    if victim_id != worker_id:
                        t = q.steal(queues[victim_id])
                        if t is not None:
                            process_task(t)
                            processed += 1
                            stolen = True
                            break
                if not stolen:
                    # 真的没任务了
                    break
            else:
                process_task(task)
                processed += 1
        results.append((worker_id, processed))

    # 启动线程
    threads = []
    for i in range(num_workers):
        t = threading.Thread(target=worker_run, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("\n完成统计：")
    total_processed = 0
    for worker_id, processed in results:
        print(f"  Worker{worker_id}: 处理了 {processed} 个任务")
        total_processed += processed

    print(f"\n总计处理: {total_processed} 个任务")
    print(f"预期: {total_tasks} 个")
    print(f"验证: {'✅ 通过' if total_processed == total_tasks else '❌ 失败'}")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 工作窃取算法测试 ===\n")

    # 演示
    work_stealing_demo(num_workers=4, total_tasks=50)

    print("\n说明：")
    print("  - 任务初始不均匀分配（模拟真实场景）")
    print("  - Worker0有最多任务，Worker3有最少")
    print("  - 通过窃取，负载逐渐均衡")
    print("  - 空闲的Worker会去偷其他人的任务")
