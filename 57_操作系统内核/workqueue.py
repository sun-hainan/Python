# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / workqueue



本文件实现 workqueue 相关的算法功能。

"""



from typing import Dict, List, Optional, Callable, Set

from dataclasses import dataclass, field

import time

import threading





@dataclass

class WorkItem:

    """工作项"""

    func: Callable           # 工作函数

    args: tuple = ()        # 参数

    pending: bool = False   # 是否在队列中

    scheduled_time: float = 0  # 计划执行时间



    def run(self):

        """执行工作"""

        if self.func:

            self.func(*self.args)





class DelayedWork:

    """延迟工作"""

    def __init__(self, func: Callable, args: tuple = (), delay_ms: int = 0):

        self.work = WorkItem(func, args)

        self.delay_ms = delay_ms

        self.scheduled = False



    def schedule(self):

        """调度延迟工作"""

        self.work.scheduled_time = time.time() + self.delay_ms / 1000.0

        self.work.pending = True

        self.scheduled = True



    def cancel(self):

        """取消延迟工作"""

        self.work.pending = False

        self.scheduled = False





class WorkQueue:

    """

    工作队列



    维护待执行的工作项。

    """



    def __init__(self, name: str, num_workers: int = 2):

        self.name = name

        self.num_workers = num_workers



        # 待执行的工作

        self.pending_works: List[WorkItem] = []



        # 延迟工作

        self.delayed_works: List[DelayedWork] = []



        # 状态

        self.running = False

        self.worker_threads: List[threading.Thread] = []



        # 统计

        self.processed = 0



    def schedule_work(self, work: WorkItem):

        """调度工作项"""

        work.pending = True

        self.pending_works.append(work)

        print(f"  [Workqueue:{self.name}] 调度工作, 待处理: {len(self.pending_works)}")



    def schedule_delayed_work(self, delayed: DelayedWork):

        """调度延迟工作"""

        delayed.schedule()

        self.delayed_works.append(delayed)



    def _process_works(self):

        """处理工作（工作线程函数）"""

        while self.running:

            # 处理延迟工作

            current_time = time.time()

            ready_delayed = []

            for dw in self.delayed_works:

                if dw.work.scheduled_time <= current_time:

                    ready_delayed.append(dw)



            for dw in ready_delayed:

                self.delayed_works.remove(dw)

                self.pending_works.append(dw.work)



            # 处理待执行工作

            while self.pending_works:

                work = self.pending_works.pop(0)

                work.pending = False

                work.run()

                self.processed += 1



            time.sleep(0.01)



    def start(self):

        """启动工作队列"""

        self.running = True

        for i in range(self.num_workers):

            t = threading.Thread(target=self._process_works, name=f"kworker/{self.name}/{i}")

            t.daemon = True

            t.start()

            self.worker_threads.append(t)

        print(f"  [Workqueue:{self.name}] 启动 {self.num_workers} 个工作线程")



    def stop(self):

        """停止工作队列"""

        self.running = False

        for t in self.worker_threads:

            t.join(timeout=1)

        print(f"  [Workqueue:{self.name}] 停止, 处理了 {self.processed} 个工作")





class SystemWorkqueue:

    """

    系统工作队列



    全局工作队列。

    """



    def __init__(self):

        # 内核线程工作队列 (events)

        self.events_wq = WorkQueue("events", num_workers=2)



        # 系统工作队列 (kworker)

        self.system_wq = WorkQueue("system", num_workers=1)



        self.wqs = [self.events_wq, self.system_wq]



    def init(self):

        """初始化"""

        for wq in self.wqs:

            wq.start()



    def destroy(self):

        """销毁"""

        for wq in self.wqs:

            wq.stop()





class Tasklet:

    """

    Tasklet



    基于软中断的小任务机制。

    在软中断上下文中执行。

    """



    # 全局tasklet向量

    tasklet_vec: List[Optional['Tasklet']] = [None] * 2  # TASKLET_SOFTIRQ



    def __init__(self, func: Callable, args: tuple = ()):

        self.func = func

        self.args = args

        self.state = "READY"  # READY, RUNNING, SCHEDULED



    def schedule(self):

        """调度tasklet"""

        if self.state == "READY":

            self.state = "SCHEDULED"

            # 加入全局tasklet向量

            Tasklet.tasklet_vec.append(self)

            print(f"  [Tasklet] 调度 tasklet")



    def run(self):

        """执行tasklet"""

        if self.state == "SCHEDULED":

            self.state = "RUNNING"

            self.func(*self.args)

            self.state = "READY"





class Timer:

    """

    内核定时器



    在指定时间后执行函数。

    """



    def __init__(self):

        self.timer_list_wheel: Dict[int, List['TimerEvent']] = {}

        self.pending_timers: List['TimerEvent'] = []



    def mod_timer(self, timer: 'TimerEvent', expires_ms: int):

        """修改定时器"""

        timer.expires = time.time() + expires_ms / 1000.0

        timer.pending = True

        print(f"  [Timer] 设置定时器 {expires_ms}ms 后触发")



    def del_timer(self, timer: 'TimerEvent'):

        """删除定时器"""

        timer.pending = False



    def run_timers(self):

        """运行到期的定时器"""

        current = time.time()

        expired = [t for t in self.pending_timers if t.expires <= current]

        for t in expired:

            t.pending = False

            t.function(t.data)





@dataclass

class TimerEvent:

    """定时器事件"""

    function: Callable

    data: any = None

    expires: float = 0

    pending: bool = False





def simulate_workqueue():

    """

    模拟工作队列和延迟函数

    """

    print("=" * 60)

    print("工作队列 (Workqueue) 与延迟函数")

    print("=" * 60)



    # 创建工作队列

    print("\n创建工作队列:")

    print("-" * 50)



    wq = WorkQueue("test", num_workers=2)

    wq.start()



    # 定义工作函数

    def work_func(name: str):

        print(f"  [Work] 执行: {name}")



    # 调度工作

    print("\n调度工作项:")

    print("-" * 50)



    for i in range(3):

        work = WorkItem(work_func, (f"任务{i+1}",))

        wq.schedule_work(work)

        time.sleep(0.05)



    # 延迟工作

    print("\n调度延迟工作:")

    print("-" * 50)



    def delayed_func(msg: str):

        print(f"  [DelayedWork] 执行: {msg}")



    for i in range(2):

        delayed = DelayedWork(delayed_func, (f"延迟任务{i+1}",), delay_ms=100)

        wq.schedule_delayed_work(delayed)



    # 等待处理

    print("\n等待工作处理...")

    time.sleep(0.5)



    # Tasklet演示

    print("\n" + "-" * 50)

    print("Tasklet")

    print("-" * 50)



    def tasklet_func():

        print(f"  [Tasklet] 执行软中断处理")



    tasklet = Tasklet(tasklet_func)

    tasklet.schedule()

    tasklet.run()



    # 定时器演示

    print("\n" + "-" * 50)

    print("内核定时器")

    print("-" * 50)



    timer_system = Timer()



    def timer_callback(data: str):

        print(f"  [Timer] 定时器触发: {data}")



    timer_event = TimerEvent(function=timer_callback, data="定时任务")

    timer_system.mod_timer(timer_event, expires_ms=50)



    # 模拟定时器处理

    print("\n等待定时器...")

    time.sleep(0.1)

    timer_system.run_timers()



    # 停止工作队列

    print("\n停止工作队列:")

    wq.stop()



    # 总结

    print("\n" + "=" * 60)

    print("异步机制总结")

    print("=" * 60)

    print("""

    ┌──────────────┬──────────────────┬──────────────────────────┐

    │ 机制          │ 执行上下文        │ 特点                     │

    ├──────────────┼──────────────────┼──────────────────────────┤

    │ Workqueue    │ 进程上下文        │ 可以睡眠                 │

    │              │ (kworker线程)     │ 适合长时间任务           │

    ├──────────────┼──────────────────┼──────────────────────────┤

    │ Tasklet      │ 软中断上下文      │ 不能睡眠                 │

    │              │                  │ 适合短小快速任务         │

    ├──────────────┼──────────────────┼──────────────────────────┤

    │ Timer        │ 中断/进程上下文   │ 定时触发                 │

    │              │                  │ 广泛用于超时检测         │

    └──────────────┴──────────────────┴──────────────────────────┘

    """)





if __name__ == "__main__":

    simulate_workqueue()

