# -*- coding: utf-8 -*-
"""
算法实现：并行算法 / thread_pool

本文件实现 thread_pool 相关的算法功能。
"""

import threading
import queue
from typing import Callable, Any, Optional, List
from dataclasses import dataclass
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ThreadPoolStats:
    """
    线程池统计信息
    """
    total_tasks_submitted: int = 0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    total_execution_time: float = 0.0
    current_queue_size: int = 0
    active_threads: int = 0


class ThreadPool:
    """
    线程池类
    
    提供一个可配置的线程池，支持任务提交、结果获取和优雅关闭。
    """
    
    def __init__(self, min_threads: int = 2, max_threads: int = 8,
                 queue_size: int = 100, idle_timeout: float = 60.0):
        """
        初始化线程池
        
        参数:
            min_threads: 最小线程数
            max_threads: 最大线程数
            queue_size: 任务队列大小
            idle_timeout: 空闲线程超时时间（秒）
        """
        self.min_threads = min_threads
        self.max_threads = max_threads
        self.idle_timeout = idle_timeout
        
        # 任务队列
        self.task_queue = queue.Queue(maxsize=queue_size)
        
        # 线程管理
        self.threads: List[threading.Thread] = []
        self.active_count = 0
        self.lock = threading.Lock()
        
        # 控制标志
        self.shutdown = False
        self.pause = False
        
        # 统计信息
        self.stats = ThreadPoolStats()
        
        # 空闲线程事件
        self.idle_event = threading.Event()
        
        # 启动最小数量的线程
        self._ensure_min_threads()
    
    def _ensure_min_threads(self):
        """
        确保线程池中至少有min_threads个线程
        """
        with self.lock:
            while len(self.threads) < self.min_threads:
                thread = self._create_worker()
                thread.start()
    
    def _create_worker(self) -> threading.Thread:
        """
        创建一个工作线程
        
        返回:
            工作线程对象
        """
        thread = threading.Thread(target=self._worker, daemon=True)
        self.threads.append(thread)
        return thread
    
    def _worker(self):
        """
        工作线程的主函数
        """
        thread_name = threading.current_thread().name
        logger.debug(f"Worker {thread_name} started")
        
        while not self.shutdown:
            try:
                # 尝试获取任务，设置超时以便定期检查shutdown
                try:
                    task = self.task_queue.get(timeout=0.5)
                except queue.Empty:
                    # 检查是否需要减少线程数
                    with self.lock:
                        if (len(self.threads) > self.min_threads and 
                            self.active_count == 0):
                            self.threads.remove(threading.current_thread())
                            logger.debug(f"Worker {thread_name} exiting (idle timeout)")
                            break
                    continue
                
                # 检查暂停标志
                while self.pause and not self.shutdown:
                    time.sleep(0.1)
                
                if self.shutdown:
                    self.task_queue.task_done()
                    break
                
                # 执行任务
                with self.lock:
                    self.active_count += 1
                
                start_time = time.time()
                
                try:
                    task['function'](*task['args'], **task['kwargs'])
                    with self.lock:
                        self.stats.total_tasks_completed += 1
                except Exception as e:
                    logger.error(f"Task execution error: {e}")
                    with self.lock:
                        self.stats.total_tasks_failed += 1
                    if task.get('error_callback'):
                        task['error_callback'](e)
                finally:
                    with self.lock:
                        self.active_count -= 1
                        self.stats.total_execution_time += time.time() - start_time
                    
                    self.task_queue.task_done()
            
            except Exception as e:
                logger.error(f"Worker error: {e}")
        
        logger.debug(f"Worker {thread_name} stopped")
    
    def submit(self, func: Callable, *args, 
               error_callback: Optional[Callable] = None, **kwargs) -> bool:
        """
        提交一个任务
        
        参数:
            func: 要执行的函数
            *args: 位置参数
            error_callback: 错误回调函数
            **kwargs: 关键字参数
        
        返回:
            True如果成功提交
        """
        if self.shutdown:
            return False
        
        # 检查是否需要增加线程
        with self.lock:
            if (self.active_count >= len(self.threads) and 
                len(self.threads) < self.max_threads and
                self.task_queue.qsize() > len(self.threads) * 2):
                thread = self._create_worker()
                thread.start()
        
        try:
            self.task_queue.put({
                'function': func,
                'args': args,
                'kwargs': kwargs,
                'error_callback': error_callback
            }, timeout=1.0)
            
            with self.lock:
                self.stats.total_tasks_submitted += 1
            
            return True
        
        except queue.Full:
            logger.warning("Task queue full, rejecting task")
            return False
    
    def map(self, func: Callable, iterable, chunksize: int = 1):
        """
        批量提交任务（类似multiprocessing.Pool.map）
        
        参数:
            func: 要应用的函数
            iterable: 可迭代参数
            chunksize: 每个任务处理的参数数量
        """
        results = []
        
        for item in iterable:
            result_holder = [None]
            error_holder = [None]
            
            def task_wrapper(x, result, error):
                try:
                    result[0] = func(x)
                except Exception as e:
                    error[0] = e
            
            self.submit(task_wrapper, item, result_holder, error_holder)
        
        self.wait_completion()
        
        return results
    
    def wait_completion(self):
        """
        等待所有任务完成
        """
        self.task_queue.join()
    
    def shutdown_wait(self, timeout: Optional[float] = None):
        """
        优雅关闭线程池，等待所有任务完成
        
        参数:
            timeout: 超时时间
        """
        self.shutdown = True
        
        # 等待所有任务完成
        deadline = time.time() + timeout if timeout else None
        
        for thread in self.threads:
            remaining = deadline - time.time() if deadline else None
            if remaining and remaining <= 0:
                break
            thread.join(timeout=remaining)
        
        self.threads.clear()
    
    def get_stats(self) -> ThreadPoolStats:
        """
        获取线程池统计信息
        
        返回:
            统计信息对象
        """
        with self.lock:
            self.stats.current_queue_size = self.task_queue.qsize()
            self.stats.active_threads = self.active_count
        
        return self.stats
    
    def pause_pool(self):
        """
        暂停任务执行
        """
        self.pause = True
    
    def resume_pool(self):
        """
        恢复任务执行
        """
        self.pause = False


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本使用
    print("=" * 50)
    print("测试1: 线程池基本使用")
    print("=" * 50)
    
    pool = ThreadPool(min_threads=2, max_threads=4)
    
    results = []
    
    def task(x):
        time.sleep(0.1)
        results.append(x * x)
        return x * x
    
    for i in range(8):
        pool.submit(task, i)
    
    print("已提交8个任务")
    pool.wait_completion()
    
    stats = pool.get_stats()
    print(f"完成的任务: {stats.total_tasks_completed}")
    print(f"结果: {sorted(results)}")
    
    pool.shutdown_wait()
    
    # 测试用例2：并发性能
    print("\n" + "=" * 50)
    print("测试2: 并发性能对比")
    print("=" * 50)
    
    def cpu_task(n):
        # 模拟CPU密集型任务
        total = 0
        for i in range(1000000):
            total += i
        return total
    
    # 顺序执行
    start = time.time()
    for i in range(4):
        cpu_task(i)
    sequential_time = time.time() - start
    print(f"顺序执行(4任务): {sequential_time:.3f}秒")
    
    # 并行执行
    pool = ThreadPool(min_threads=4, max_threads=4)
    
    start = time.time()
    for i in range(4):
        pool.submit(cpu_task, i)
    pool.wait_completion()
    parallel_time = time.time() - start
    
    print(f"并行执行(4线程): {parallel_time:.3f}秒")
    print(f"加速比: {sequential_time/parallel_time:.2f}x")
    
    pool.shutdown_wait()
    
    # 测试用例3：错误处理
    print("\n" + "=" * 50)
    print("测试3: 错误回调处理")
    print("=" * 50)
    
    pool = ThreadPool(min_threads=2)
    
    errors = []
    
    def failing_task():
        raise ValueError("Simulated error")
    
    def error_handler(e):
        errors.append(str(e))
        print(f"捕获错误: {e}")
    
    for i in range(3):
        pool.submit(failing_task, error_callback=error_handler)
    
    pool.wait_completion()
    
    stats = pool.get_stats()
    print(f"失败任务数: {stats.total_tasks_failed}")
    print(f"捕获的错误: {errors}")
    
    pool.shutdown_wait()
    
    # 测试用例4：线程池状态
    print("\n" + "=" * 50)
    print("测试4: 线程池状态监控")
    print("=" * 50)
    
    pool = ThreadPool(min_threads=2, max_threads=8)
    
    def simple_task(x):
        return x + 1
    
    for i in range(10):
        pool.submit(simple_task, i)
        stats = pool.get_stats()
        print(f"队列大小: {stats.current_queue_size}, 活跃线程: {stats.active_threads}")
    
    pool.wait_completion()
    
    final_stats = pool.get_stats()
    print(f"\n最终统计:")
    print(f"  总提交: {final_stats.total_tasks_submitted}")
    print(f"  总完成: {final_stats.total_tasks_completed}")
    print(f"  总失败: {final_stats.total_tasks_failed}")
    
    pool.shutdown_wait()
