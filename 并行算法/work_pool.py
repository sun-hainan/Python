# -*- coding: utf-8 -*-
"""
算法实现：并行算法 / work_pool

本文件实现 work_pool 相关的算法功能。
"""

import threading
import queue
from typing import Callable, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import time


class TaskStatus(Enum):
    """
    任务状态枚举
    """
    PENDING = "pending"     # 等待中
    RUNNING = "running"   # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"      # 执行失败


@dataclass
class Task:
    """
    任务数据类
    """
    task_id: int           # 任务唯一标识
    func: Callable         # 要执行的函数
    args: tuple            # 函数参数
    kwargs: dict          # 函数关键字参数
    status: TaskStatus = TaskStatus.PENDING  # 任务状态
    result: Any = None     # 执行结果
    exception: Exception = None  # 异常信息


class WorkPool:
    """
    工作池类
    
    管理固定数量的工作线程，从任务队列中取任务执行。
    """
    
    def __init__(self, num_workers: int = 4):
        """
        初始化工作池
        
        参数:
            num_workers: 工作线程数量
        """
        self.num_workers = num_workers
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.workers = []
        self.shutdown_flag = threading.Event()
        self.tasks = {}  # task_id -> Task
        self.next_task_id = 0
        self.lock = threading.Lock()
        
        # 创建工作线程
        self._create_workers()
    
    def _create_workers(self):
        """
        创建工作线程
        """
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"Worker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
    
    def _worker_loop(self):
        """
        工作线程的主循环
        """
        while not self.shutdown_flag.is_set():
            try:
                # 从任务队列获取任务，设置超时以便检查shutdown标志
                try:
                    task = self.task_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # 更新任务状态
                task.status = TaskStatus.RUNNING
                
                try:
                    # 执行任务
                    result = task.func(*task.args, **task.kwargs)
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                except Exception as e:
                    task.exception = e
                    task.status = TaskStatus.FAILED
                finally:
                    # 将结果放入结果队列
                    self.result_queue.put(task)
                    self.task_queue.task_done()
            
            except Exception as e:
                # 忽略其他异常
                pass
    
    def submit(self, func: Callable, *args, **kwargs) -> int:
        """
        提交一个任务
        
        参数:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
        
        返回:
            任务ID
        """
        with self.lock:
            task_id = self.next_task_id
            self.next_task_id += 1
        
        task = Task(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs
        )
        
        self.tasks[task_id] = task
        self.task_queue.put(task)
        
        return task_id
    
    def get_result(self, task_id: int, timeout: Optional[float] = None) -> Any:
        """
        获取任务结果
        
        参数:
            task_id: 任务ID
            timeout: 超时时间（秒）
        
        返回:
            任务结果
        
        异常:
            KeyError: 任务不存在
            ValueError: 任务执行失败
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        
        # 等待结果
        while task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            time.sleep(0.01)
            if timeout is not None and timeout <= 0:
                raise TimeoutError(f"Task {task_id} timed out")
        
        if task.status == TaskStatus.FAILED:
            raise task.exception
        
        return task.result
    
    def wait_all(self):
        """
        等待所有任务完成
        """
        self.task_queue.join()
    
    def shutdown(self, wait: bool = True):
        """
        关闭工作池
        
        参数:
            wait: 是否等待任务完成
        """
        if wait:
            self.wait_all()
        
        self.shutdown_flag.set()
        
        if wait:
            for worker in self.workers:
                worker.join(timeout=1.0)
        
        self.workers.clear()
    
    def get_status(self) -> dict:
        """
        获取工作池状态
        
        返回:
            状态字典
        """
        counts = {
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0
        }
        
        for task in self.tasks.values():
            counts[task.status.value] += 1
        
        return {
            'num_workers': self.num_workers,
            'total_tasks': len(self.tasks),
            'status_counts': counts,
            'queue_size': self.task_queue.qsize()
        }


def example_work_function(x: int, y: int) -> int:
    """
    示例工作函数
    
    参数:
        x: 第一个参数
        y: 第二个参数
    
    返回:
        x + y
    """
    # 模拟一些计算
    time.sleep(0.01)
    return x + y


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本使用
    print("=" * 50)
    print("测试1: 基本工作池使用")
    print("=" * 50)
    
    pool = WorkPool(num_workers=4)
    
    # 提交任务
    task_ids = []
    for i in range(10):
        task_id = pool.submit(example_work_function, i, i * 2)
        task_ids.append(task_id)
    
    print(f"提交了 {len(task_ids)} 个任务")
    
    # 获取结果
    pool.wait_all()
    
    for task_id in task_ids:
        result = pool.get_result(task_id)
        print(f"Task {task_id}: result = {result}")
    
    status = pool.get_status()
    print(f"\n工作池状态: {status}")
    
    pool.shutdown()
    
    # 测试用例2：并发执行
    print("\n" + "=" * 50)
    print("测试2: 并发执行演示")
    print("=" * 50)
    
    pool = WorkPool(num_workers=2)
    
    def slow_task(task_id: int):
        time.sleep(0.1)
        return task_id * 2
    
    start = time.time()
    
    task_ids = []
    for i in range(4):
        task_id = pool.submit(slow_task, i)
        task_ids.append(task_id)
    
    pool.wait_all()
    elapsed = time.time() - start
    
    print(f"4个任务(每个0.1秒), 2个工作线程")
    print(f"理论时间: ~0.2秒 (2批), 实际: {elapsed:.3f}秒")
    
    pool.shutdown()
    
    # 测试用例3：异常处理
    print("\n" + "=" * 50)
    print("测试3: 异常处理")
    print("=" * 50)
    
    pool = WorkPool(num_workers=2)
    
    def failing_task():
        raise ValueError("Task failed!")
    
    task_id = pool.submit(failing_task)
    
    try:
        pool.get_result(task_id, timeout=1)
    except ValueError as e:
        print(f"捕获异常: {e}")
    
    pool.shutdown()
    
    # 测试用例4：任务状态追踪
    print("\n" + "=" * 50)
    print("测试4: 任务状态追踪")
    print("=" * 50)
    
    pool = WorkPool(num_workers=2)
    
    def simple_task(x):
        return x * x
    
    task_id = pool.submit(simple_task, 5)
    
    # 短暂等待后检查状态
    time.sleep(0.05)
    
    status = pool.get_status()
    print(f"初始状态: {status}")
    
    pool.wait_all()
    
    status = pool.get_status()
    print(f"完成后状态: {status}")
    
    pool.shutdown()
