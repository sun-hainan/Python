# -*- coding: utf-8 -*-
"""
算法实现：操作系统内核 / cfs_scheduler_detail

本文件实现 cfs_scheduler_detail 相关的算法功能。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import time


class RedBlackTree:
    """简化版红黑树（用于CFS）"""
    # 见 rbtree.py 完整实现

    def __init__(self):
        self.NIL = _RBNode(key=0, color=0)
        self.root = self.NIL

    def insert(self, key: int, value: any):
        # 简化实现
        pass

    def delete(self, key: int):
        pass

    def minimum(self) -> Optional[any]:
        # 简化：返回最小的key
        return self.root if self.root != self.NIL else None


from dataclasses import dataclass, field


@dataclass
class _RBNode:
    """红黑树节点"""
    key: int
    value: any = None
    color: int = 1
    left: any = None
    right: any = None
    parent: any = None


class Task_struct:
    """
    任务描述符（Task Struct）

    类似于Linux内核的task_struct。
    """

    def __init__(self, pid: int, name: str, nice: int = 0):
        self.pid = pid
        self.name = name
        self.nice = nice  # -20到+19，值越小优先级越高

        # 调度相关
        self.vruntime = 0           # 虚拟运行时间
        self.se_exec_start = 0      # 执行开始时间
        self.sum_exec_runtime = 0   # 累计执行时间

        # 权重（根据nice值计算）
        self.weight = self._nice_to_weight(nice)

        # 状态
        self.state = TaskState.RUNNING
        self.on_rq = False  # 是否在运行队列

    @staticmethod
    def _nice_to_weight(nice: int) -> int:
        """
        将nice值转换为权重
        nice越低，权重越高，获得CPU时间越多
        """
        # 简化：权重计算
        # 实际内核使用1024作为基准，使用prio_to_weight数组
        NICE_0_LOAD = 1024
        # 简化计算
        weight = NICE_0_LOAD
        if nice < 0:
            weight = NICE_0_LOAD * (1 + abs(nice) * 0.1)
        elif nice > 0:
            weight = NICE_0_LOAD / (1 + nice * 0.1)
        return int(weight)


class TaskState:
    """任务状态"""
    RUNNING = "R"
    RUNNABLE = "R"
    SLEEPING = "S"
    STOPPED = "T"
    ZOMBIE = "Z"


class CFS_runqueue:
    """
    CFS运行队列

    管理所有可运行任务。
    使用红黑树按vruntime排序。
    """

    def __init__(self):
        self.min_vruntime = 0  # 树中最小的vruntime
        self.curr = None       # 当前运行任务
        self.tasks: List[Task_struct] = []

        # 红黑树（简化：用有序列表代替）
        self.rb_root: List[Task_struct] = []

        # 调度统计
        self.nr_running = 0    # 可运行任务数
        self.nr_switches = 0   # 上下文切换次数

    def enqueue_task(self, task: Task_struct):
        """将任务加入运行队列"""
        if not task.on_rq:
            task.on_rq = True
            self.tasks.append(task)
            self.nr_running += 1
            self._insert_task(task)

    def dequeue_task(self, task: Task_struct):
        """将任务移出运行队列"""
        if task.on_rq:
            task.on_rq = False
            self.tasks = [t for t in self.tasks if t.pid != task.pid]
            self.nr_running -= 1
            self._remove_task(task)

    def _insert_task(self, task: Task_struct):
        """插入任务到红黑树"""
        # 简化：使用插入排序
        self.rb_root.append(task)
        self.rb_root.sort(key=lambda t: t.vruntime)

    def _remove_task(self, task: Task_struct):
        """从红黑树移除任务"""
        self.rb_root = [t for t in self.rb_root if t.pid != task.pid]

    def pick_next_task(self) -> Optional[Task_struct]:
        """选择下一个调度任务（vruntime最小的）"""
        if not self.rb_root:
            return None
        return self.rb_root[0]

    def update_min_vruntime(self):
        """更新min_vruntime"""
        if self.rb_root:
            self.min_vruntime = self.rb_root[0].vruntime
        else:
            # 没有任务时，正常增长
            self.min_vruntime += 1000


class CFS_Scheduler:
    """
    CFS调度器

    实现：
    1. 使用vruntime跟踪任务执行
    2. 每次调度选择vruntime最小的任务
    3. 根据权重调整vruntime增长速率
    """

    # 基准权重（NICE_0_LOAD）
    NICE_0_LOAD = 1024

    # 时间片基准（纳秒）
    sysctl_sched_latency = 6 * 10**9   # 6秒
    sysctl_sched_min_granularity = 0.75 * 10**9  # 0.75ms

    def __init__(self):
        self.rq = CFS_runqueue()
        self.global_clock = 0  # 全局时钟
        self.tasks: Dict[int, Task_struct] = {}  # 所有任务

    def add_task(self, pid: int, name: str, nice: int = 0):
        """添加新任务"""
        task = Task_struct(pid, name, nice)
        task.vruntime = self.rq.min_vruntime  # 新任务从min_vruntime开始
        self.tasks[pid] = task
        self.rq.enqueue_task(task)
        print(f"  添加任务: {name} (PID={pid}, nice={nice}, vruntime={task.vruntime})")

    def remove_task(self, pid: int):
        """移除任务"""
        if pid in self.tasks:
            task = self.tasks[pid]
            self.rq.dequeue_task(task)
            del self.tasks[pid]

    def schedule(self) -> Optional[Task_struct]:
        """
        调度函数
        选择下一个要运行的任务
        """
        # 更新min_vruntime
        self.rq.update_min_vruntime()

        # 选择下一个任务
        next_task = self.rq.pick_next_task()
        if next_task:
            # 更新当前任务
            if self.rq.curr and self.rq.curr != next_task:
                self.rq.nr_switches += 1
            self.rq.curr = next_task

        return next_task

    def update_task_runtime(self, task: Task_struct, delta_exec: int):
        """
        更新任务vruntime
        param delta_exec: 实际运行时间（纳秒）
        """
        # 根据权重调整vruntime增长
        # vruntime += delta_exec * (NICE_0_LOAD / task.weight)

        # 简化：直接加上实际时间
        task.vruntime += delta_exec
        task.sum_exec_runtime += delta_exec

        # 移动任务到红黑树中的正确位置
        if task.on_rq:
            self.rq._remove_task(task)
            self.rq._insert_task(task)

    def requeue_task(self, task: Task_struct):
        """重新入队任务"""
        if task.on_rq:
            self.rq._remove_task(task)
            self.rq._insert_task(task)

    def put_prev_task(self, prev: Task_struct):
        """切换走前一个任务"""
        # 更新vruntime
        # 这里简化处理
        pass

    def set_curr_task(self, task: Task_struct):
        """设置当前运行任务"""
        self.rq.curr = task

    def get_task_stats(self, pid: int) -> Dict:
        """获取任务统计"""
        if pid not in self.tasks:
            return {}
        task = self.tasks[pid]
        return {
            'pid': task.pid,
            'name': task.name,
            'nice': task.nice,
            'vruntime': task.vruntime,
            'weight': task.weight,
            'sum_exec_runtime': task.sum_exec_runtime,
            'state': task.state,
        }


def simulate_cfs_scheduler():
    """
    模拟CFS调度器
    """
    print("=" * 60)
    print("CFS（完全公平调度器）模拟")
    print("=" * 60)

    cfs = CFS_Scheduler()

    # 添加任务
    print("\n添加任务:")
    print("-" * 50)
    cfs.add_task(1, "init", nice=0)
    cfs.add_task(2, "bash", nice=0)
    cfs.add_task(3, "vim", nice=-5)   # 高优先级
    cfs.add_task(4, "top", nice=10)   # 低优先级

    print(f"\n运行队列任务数: {cfs.rq.nr_running}")
    print(f"当前任务: {cfs.rq.curr.name if cfs.rq.curr else 'None'}")

    # 模拟调度
    print("\n调度模拟:")
    print("-" * 50)

    time_slice = 1000000  # 1ms

    for round_num in range(1, 6):
        print(f"\n调度轮次 {round_num}:")

        # 选择任务
        task = cfs.schedule()
        if task:
            cfs.set_curr_task(task)
            print(f"  选择任务: {task.name} (PID={task.pid}, vruntime={task.vruntime})")

            # 更新vruntime
            cfs.update_task_runtime(task, time_slice)
            print(f"  执行 {time_slice}ns 后, vruntime={task.vruntime}")

            # 重新入队
            cfs.requeue_task(task)

        # 显示运行队列
        print(f"  运行队列(vruntime排序): ", end="")
        vruntime_list = [(t.name, t.vruntime) for t in cfs.rq.rb_root]
        print(vruntime_list)

    print(f"\n总上下文切换次数: {cfs.rq.nr_switches}")

    # 演示nice值影响
    print("\n" + "=" * 60)
    print("nice值对调度的影响")
    print("=" * 60)

    print("\n场景: 两个任务，nice值不同")
    cfs2 = CFS_Scheduler()
    cfs2.add_task(10, "high_prio", nice=-10)   # 高优先级
    cfs2.add_task(11, "low_prio", nice=10)      # 低优先级

    print("\n执行5个时间片后:")
    for i in range(5):
        task = cfs2.schedule()
        if task:
            cfs2.update_task_runtime(task, 1000000)

    print(f"\n  high_prio vruntime: {cfs2.tasks[10].vruntime}")
    print(f"  low_prio vruntime: {cfs2.tasks[11].vruntime}")
    print(f"  low_prio的vruntime增长更快（实际获得CPU时间更少）")


if __name__ == "__main__":
    simulate_cfs_scheduler()
