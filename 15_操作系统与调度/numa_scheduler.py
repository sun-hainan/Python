# -*- coding: utf-8 -*-

"""

算法实现：15_操作系统与调度 / numa_scheduler



本文件实现 numa_scheduler 相关的算法功能。

"""



from dataclasses import dataclass, field

from typing import Optional, list

import random





@dataclass

class NUMANode:

    """NUMA节点"""

    node_id: int

    cpu_cores: list[int]       # 此节点的CPU核心

    total_memory_mb: int        # 总内存

    free_memory_mb: int        # 空闲内存

    access_latency_ns: dict = field(default_factory=dict)  # 到其他节点的访问延迟



    def __post_init__(self):

        self.access_latency = self.access_latency if self.access_latency else {}

        # 默认：本地访问低延迟，远程访问高延迟

        for nid in range(4):  # 假设最多4个节点

            if nid == self.node_id:

                self.access_latency[nid] = 50  # 本地：50ns

            else:

                self.access_latency[nid] = 150 + nid * 30  # 远程：递增延迟





@dataclass

class TaskMemoryAffinity:

    """任务内存亲和性信息"""

    tid: int

    preferred_node: int = 0      # 首选NUMA节点

    current_node: Optional[int] = None

    memory_usage_mb: int = 0      # 内存使用量

    pages: list[int] = field(default_factory=list)  # 已分配的物理页





class NUMAScheduler:

    """

    NUMA感知调度器

    策略：

    1. 内存分配优先本地节点

    2. 调度时考虑CPU与内存位置

    3. 负载均衡时考虑跨节点迁移成本

    """



    def __init__(self, num_nodes: int = 2):

        self.num_nodes = num_nodes

        self.nodes: list[NUMANode] = []



        # 初始化NUMA拓扑

        self._init_numa_topology()



        self.task_affinity: dict[int, TaskMemoryAffinity] = {}

        self.sched_events: list[dict] = []



    def _init_numa_topology(self):

        """初始化NUMA拓扑（模拟4节点NUMA）"""

        cores_per_node = [0, 1, 2, 3]  # 每节点4核

        mem_per_node = [8192, 8192, 8192, 8192]  # 每节点8GB



        for i in range(self.num_nodes):

            node = NUMANode(

                node_id=i,

                cpu_cores=[i * 4 + c for c in range(4)],

                total_memory_mb=mem_per_node[i],

                free_memory_mb=mem_per_node[i]

            )

            self.nodes.append(node)



    def allocate_memory_local(self, tid: int, size_mb: int) -> Optional[int]:

        """

        在本地节点分配内存

        返回分配的节点ID，失败返回None

        """

        if tid not in self.task_affinity:

            self.task_affinity[tid] = TaskMemoryAffinity(tid=tid)



        affinity = self.task_affinity[tid]

        preferred = affinity.preferred_node



        # 优先尝试首选节点

        if self.nodes[preferred].free_memory_mb >= size_mb:

            self.nodes[preferred].free_memory_mb -= size_mb

            affinity.current_node = preferred

            affinity.memory_usage_mb += size_mb

            return preferred



        # 如果首选节点空间不足，检查其他节点

        for i in range(self.num_nodes):

            if i != preferred and self.nodes[i].free_memory_mb >= size_mb:

                # 分配到其他节点（远程）

                self.nodes[i].free_memory_mb -= size_mb

                affinity.current_node = i

                affinity.memory_usage_mb += size_mb

                return i



        return None



    def get_node_access_latency(self, from_node: int, to_node: int) -> int:

        """获取节点间访问延迟"""

        return self.nodes[from_node].access_latency.get(to_node, 200)



    def schedule_task_to_node(self, tid: int) -> int:

        """

        调度任务到最优NUMA节点

        考虑因素：

        1. 任务内存当前所在节点

        2. 任务首选节点

        3. 节点负载

        """

        affinity = self.task_affinity.get(tid, TaskMemoryAffinity(tid=tid))



        # 如果任务已有内存使用，检查当前节点是否最优

        if affinity.current_node is not None:

            current_node = affinity.current_node

            current_load = len([t for t in self.task_affinity.values() if t.current_node == current_node])

            # 如果当前节点负载可接受，继续使用

            if current_load < 8:  # 每节点最大8个任务

                return current_node



        # 寻找最佳节点

        best_node = affinity.preferred_node

        for i in range(self.num_nodes):

            node_load = len([t for t in self.task_affinity.values() if t.current_node == i])

            if node_load < len(self.nodes[i].cpu_cores) and self.nodes[i].free_memory_mb > 512:

                best_node = i

                break



        return best_node



    def migrate_task(self, tid: int, from_node: int, to_node: int) -> bool:

        """

        将任务内存迁移到另一个节点

        注意：内存迁移开销大，应谨慎使用

        """

        if from_node == to_node:

            return True



        # 检查目标节点是否有足够内存

        if self.nodes[to_node].free_memory_mb < self.task_affinity[tid].memory_usage_mb:

            return False



        # 执行迁移

        self.nodes[from_node].free_memory_mb += self.task_affinity[tid].memory_usage_mb

        self.nodes[to_node].free_memory_mb -= self.task_affinity[tid].memory_usage_mb

        self.task_affinity[tid].current_node = to_node



        self.sched_events.append({

            "type": "migrate",

            "tid": tid,

            "from": from_node,

            "to": to_node

        })



        print(f"任务T{tid}内存从节点{from_node}迁移到节点{to_node}")

        return True



    def get_numa_topology_info(self) -> str:

        """获取NUMA拓扑信息"""

        lines = ["NUMA拓扑:", "+" * 40]

        for node in self.nodes:

            lines.append(

                f"Node {node.node_id}: "

                f"CPU {node.cpu_cores}, "

                f"Mem {node.total_memory_mb - node.free_memory_mb}/{node.total_memory_mb} MB used"

            )

        return "\n".join(lines)





if __name__ == "__main__":

    print("=== NUMA感知调度演示 ===")



    scheduler = NUMAScheduler(num_nodes=4)



    # 显示NUMA拓扑

    print(scheduler.get_numa_topology_info())



    # 分配内存到不同任务

    print("\n--- 内存分配（优先本地节点）---")

    tasks = [

        (101, 500),  # tid, size_mb

        (102, 300),

        (103, 1000),

        (104, 200),

        (105, 600),

    ]



    for tid, size in tasks:

        node = scheduler.allocate_memory_local(tid, size)

        if node is not None:

            latency = scheduler.get_node_access_latency(node, node)

            print(f"任务T{tid}: 分配{size}MB -> 节点{node} (本地延迟 {latency}ns)")

        else:

            print(f"任务T{tid}: 分配{size}MB -> 失败（内存不足）")



    # 调度任务

    print("\n--- 任务调度 ---")

    for tid in [101, 102, 103]:

        node = scheduler.schedule_task_to_node(tid)

        task = scheduler.task_affinity[tid]

        if task.current_node:

            latency = scheduler.get_node_access_latency(node, task.current_node)

            print(f"任务T{tid}: 调度到CPU node={node}, 内存访问延迟={latency}ns")

        else:

            print(f"任务T{tid}: 新任务，调度到node={node}")



    # 跨节点访问延迟演示

    print("\n--- NUMA访问延迟矩阵 ---")

    print(f"{'From\\To':<10}" + "".join(f"{'Node'+str(i):<10}" for i in range(4)))

    for i in range(4):

        row = f"Node {i}   "

        for j in range(4):

            lat = scheduler.get_node_access_latency(i, j)

            row += f"{lat}ns    "

        print(row)



    print("\n关键观察:")

    print("  - 本地访问（对角线）: ~50ns")

    print("  - 远程访问: ~150-240ns（3-5倍延迟）")

    print("  - 调度决策应尽量让任务访问本地内存")

