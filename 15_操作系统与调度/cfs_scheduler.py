# -*- coding: utf-8 -*-

"""

算法实现：15_操作系统与调度 / cfs_scheduler



本文件实现 cfs_scheduler 相关的算法功能。

"""



from dataclasses import dataclass, field

from typing import Optional

import bisect



@dataclass

class Task:

    """任务控制块"""

    tid: int

    weight: int = 1024  # 调度权重（nice值转换，1024为默认）

    vruntime: float = 0.0  # 虚拟运行时间

    actual_runtime: float = 0.0  # 实际运行时间

    is_running: bool = False





class RBNode:

    """红黑树节点（简化版）"""

    __slots__ = ['key', 'value', 'left', 'right', 'color']



    def __init__(self, key, value, color='RED'):

        self.key = key

        self.value = value

        self.left: Optional['RBNode'] = None

        self.right: Optional['RBNode'] = None

        self.color = color





class RedBlackTree:

    """简化红黑树实现（按key排序）"""



    def __init__(self):

        self.NIL = RBNode(None, None, 'BLACK')

        self.NIL.left = self.NIL

        self.NIL.right = self.NIL

        self.root = self.NIL



    def _rotate_left(self, x: RBNode):

        y = x.right

        x.right = y.left

        if y.left != self.NIL:

            y.left.parent = x

        y.parent = x.parent

        if x.parent == self.NIL:

            self.root = y

        elif x == x.parent.left:

            x.parent.left = y

        else:

            x.parent.right = y

        y.left = x

        x.parent = y



    def _rotate_right(self, y: RBNode):

        x = y.left

        y.left = x.right

        if x.right != self.NIL:

            x.right.parent = y

        x.parent = y.parent

        if y.parent == self.NIL:

            self.root = x

        elif y == y.parent.right:

            y.parent.right = x

        else:

            y.parent.left = x

        x.right = y

        y.parent = x



    def insert(self, key, value):

        z = RBNode(key, value)

        z.left = self.NIL

        z.right = self.NIL



        y = self.NIL

        x = self.root



        while x != self.NIL:

            y = x

            if z.key < x.key:

                x = x.left

            else:

                x = x.right



        z.parent = y

        if y == self.NIL:

            self.root = z

        elif z.key < y.key:

            y.left = z

        else:

            y.right = z



        self._insert_fixup(z)



    def _insert_fixup(self, z: RBNode):

        while z.parent.color == 'RED':

            if z.parent == z.parent.parent.left:

                y = z.parent.parent.right

                if y.color == 'RED':

                    z.parent.color = 'BLACK'

                    y.color = 'BLACK'

                    z.parent.parent.color = 'RED'

                    z = z.parent.parent

                else:

                    if z == z.parent.right:

                        z = z.parent

                        self._rotate_left(z)

                    z.parent.color = 'BLACK'

                    z.parent.parent.color = 'RED'

                    self._rotate_right(z.parent.parent)

            else:

                y = z.parent.parent.left

                if y.color == 'RED':

                    z.parent.color = 'BLACK'

                    y.color = 'BLACK'

                    z.parent.parent.color = 'RED'

                    z = z.parent.parent

                else:

                    if z == z.parent.left:

                        z = z.parent

                        self._rotate_right(z)

                    z.parent.color = 'BLACK'

                    z.parent.parent.color = 'RED'

                    self._rotate_left(z.parent.parent)



        self.root.color = 'BLACK'



    def minimum(self, x: RBNode) -> RBNode:

        while x.left != self.NIL:

            x = x.left

        return x



    def successor(self, x: RBNode) -> Optional[RBNode]:

        if x.right != self.NIL:

            return self.minimum(x.right)

        y = x.parent

        while y != self.NIL and x == y.right:

            x = y

            y = y.parent

        return y if y != self.NIL else None



    def find_min(self) -> Optional[RBNode]:

        if self.root == self.NIL:

            return None

        return self.minimum(self.root)



    def delete(self, key):

        self._delete(self.root, key)



    def _delete(self, root: RBNode, key):

        z = self.NIL

        x = root

        while x != self.NIL:

            if x.key == key and x.value is not None:

                z = x

                break

            elif key < x.key:

                x = x.left

            else:

                x = x.right



        if z == self.NIL:

            return



        self._transplant(z, z.right)

        if z.right != self.NIL and z.left != self.NIL:

            y = self.minimum(z.left)

            self._transplant(z, y)

            y.left = z.left

            y.left.parent = y





class CFSScheduler:

    """

    CFS完全公平调度器

    核心数据结构：红黑树按vruntime排序

    调度原则：取vruntime最小的任务执行

    """



    def __init__(self, target_latency: float = 6.0, min_granularity: float = 0.4):

        self.target_latency = target_latency  # 目标调度延迟（ms）

        self.min_granularity = min_granularity  # 最小时间粒度

        self.rbtree = RedBlackTree()  # 红黑树存储就绪任务

        self.task_map: dict[int, Task] = {}  # tid -> Task

        self.current_task: Optional[Task] = None

        self.current_time: float = 0.0



    def _calc_timeslice(self, task: Task) -> float:

        """根据权重计算时间片"""

        total_weight = sum(t.weight for t in self.task_map.values())

        if total_weight == 0:

            return self.target_latency

        share = task.weight / total_weight

        timeslice = self.target_latency * share

        return max(timeslice, self.min_granularity)



    def add_task(self, task: Task):

        """添加新任务"""

        task.vruntime = self.rbtree.find_min().key if self.rbtree.find_min() else 0.0

        self.task_map[task.tid] = task

        self.rbtree.insert(task.vruntime, task.tid)



    def remove_task(self, tid: int):

        """移除任务"""

        if tid in self.task_map:

            del self.task_map[tid]



    def pick_next(self) -> Optional[int]:

        """选择vruntime最小的任务（最左节点）"""

        min_node = self.rbtree.find_min()

        if min_node is None:

            return None

        return min_node.value  # 返回tid



    def enqueue(self, tid: int):

        """任务入队（重新计算vruntime）"""

        if tid not in self.task_map:

            return

        task = self.task_map[tid]

        self.rbtree.insert(task.vruntime, tid)



    def dequeue(self, tid: int):

        """任务出队"""

        if tid in self.task_map:

            self.rbtree.delete(self.task_map[tid].vruntime)



    def update_vruntime(self, tid: int, delta: float, weight: int):

        """更新任务的vruntime（考虑权重）"""

        if tid not in self.task_map:

            return

        task = self.task_map[tid]

        # vruntime增量 = 实际时间 * (NICE_0_WEIGHT / task.weight)

        weight_ratio = 1024 / weight

        task.vruntime += delta * weight_ratio



    def schedule(self) -> Optional[int]:

        """调度决策：返回下一个运行的任务tid"""

        next_tid = self.pick_next()

        if next_tid is None:

            return None



        if self.current_task and self.current_task.tid != next_tid:

            # 切换任务

            self.current_task.is_running = False



        self.current_task = self.task_map.get(next_tid)

        if self.current_task:

            self.current_task.is_running = True



        return next_tid





if __name__ == "__main__":

    scheduler = CFSScheduler()



    # 创建测试任务

    tasks = [

        Task(tid=1, weight=1024),    # 默认nice

        Task(tid=2, weight=2073),    # nice=-5 (更高权重)

        Task(tid=3, weight=512),     # nice=+5 (更低权重)

    ]



    print("=== CFS调度器初始化 ===")

    print(f"目标延迟: {scheduler.target_latency}ms")

    print(f"最小粒度: {scheduler.min_granularity}ms")

    print()



    for task in tasks:

        scheduler.add_task(task)



    print("=== 任务入队 ===")

    for tid, task in scheduler.task_map.items():

        ts = scheduler._calc_timeslice(task)

        print(f"T{tid}: weight={task.weight}, vruntime={task.vruntime:.2f}, timeslice={ts:.4f}ms")



    print("\n=== 调度决策 ===")

    for _ in range(5):

        next_tid = scheduler.schedule()

        if next_tid is None:

            print("无任务可调度")

            break



        task = scheduler.task_map[next_tid]

        ts = scheduler._calc_timeslice(task)

        print(f"调度 T{next_tid}: vruntime={task.vruntime:.4f}, 执行{ts:.4f}ms")



        # 更新vruntime并重新入队

        scheduler.update_vruntime(next_tid, ts, task.weight)

        scheduler.dequeue(next_tid)

        scheduler.enqueue(next_tid)



    print("\n=== 最终状态 ===")

    for tid, task in scheduler.task_map.items():

        print(f"T{tid}: vruntime={task.vruntime:.4f}, is_running={task.is_running}")

