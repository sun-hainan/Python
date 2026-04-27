# -*- coding: utf-8 -*-

"""

算法实现：15_操作系统与调度 / oom_killer



本文件实现 oom_killer 相关的算法功能。

"""



from dataclasses import dataclass, field

from typing import Optional

import time





@dataclass

class ProcessMemoryInfo:

    """进程内存信息"""

    pid: int

    name: str

    rss_kb: int      # 驻留内存

    vms_kb: int      # 虚拟内存

    oom_score: int = 0  # OOM评分

    oom_adj: int = 0    # OOM调节值（-17到+15）

    last_access: float = 0.0





class OOMScoreCalculator:

    """

    OOM评分计算器

    评分因子：

    1. 内存占用量（越多越可能被杀）

    2. oom_adj值（越高越容易被杀）

    3. 进程类型（root进程分数较低）

    4. 存活时间（越长越可能被杀）

    """



    def __init__(self):

        self.base_score = 0

        self.adj_weight = 10  # adj每升高1，score加10



    def calculate_score(self, proc: ProcessMemoryInfo, uptime: float) -> int:

        """计算OOM score"""

        # 基础分：内存占用（MB为单位，每MB加1分）

        mem_mb = proc.rss_kb // 1024

        base = mem_mb



        # 调整因子（oom_adj）

        # 范围：-17（永不杀）到 +15（优先杀）

        adj_score = proc.oom_adj * self.adj_weight

        if proc.oom_adj == -17:

            return 0  # 永不杀死



        # 类型调整：init/systemd等关键进程加分更低

        critical_names = {"init", "systemd", "kthreadd", "migration"}

        if proc.name in critical_names:

            adj_score -= 200



        # 进程年龄因子（越老越容易被杀）

        age_minutes = (time.time() - proc.last_access) / 60

        age_factor = min(age_minutes / 10, 50)  # 最多加50分



        # 计算最终分数

        score = max(0, base + adj_score + int(age_factor))

        return min(score, 1000)  # 最高1000分





@dataclass

class OOMKillEvent:

    """OOM击杀事件"""

    timestamp: float

    victim_pid: int

    victim_name: str

    victim_score: int

    memory_freed_kb: int

    reason: str





class OOMKiller:

    """

    OOM Killer模拟器

    流程：

    1. 监控系统内存

    2. 当内存压力时计算所有进程OOM score

    3. 选择最高分进程发送SIGKILL

    """



    def __init__(self, available_memory_kb: int = 4 * 1024 * 1024):

        self.available_memory_kb = available_memory_kb  # 4GB

        self.watermark_low = int(available_memory_kb * 0.1)   # 10%

        self.watermark_high = int(available_memory_kb * 0.05)  # 5%



        self.processes: dict[int, ProcessMemoryInfo] = {}

        self.kill_log: list[OOMKillEvent] = []



    def register_process(self, pid: int, name: str, rss_kb: int, vms_kb: int):

        """注册进程"""

        proc = ProcessMemoryInfo(

            pid=pid,

            name=name,

            rss_kb=rss_kb,

            vms_kb=vms_kb,

            last_access=time.time()

        )

        self.processes[pid] = proc



    def set_oom_adj(self, pid: int, adj: int):

        """设置oom_adj（范围-17到+15）"""

        adj = max(-17, min(15, adj))

        if pid in self.processes:

            self.processes[pid].oom_adj = adj



    def check_memory_pressure(self) -> bool:

        """检查是否内存不足"""

        total_rss = sum(p.rss_kb for p in self.processes.values())

        free_memory = self.available_memory_kb - total_rss

        return free_memory < self.watermark_high



    def select_victim(self) -> Optional[ProcessMemoryInfo]:

        """选择要被杀死的进程"""

        uptime = time.time()  # 模拟系统运行时间

        calculator = OOMScoreCalculator()



        for proc in self.processes.values():

            proc.oom_score = calculator.calculate_score(proc, uptime)



        # 选择得分最高的进程

        if not self.processes:

            return None



        victim = max(self.processes.values(), key=lambda p: p.oom_score)

        return victim if victim.oom_score > 0 else None



    def kill_process(self, proc: ProcessMemoryInfo) -> OOMKillEvent:

        """执行杀死进程"""

        event = OOMKillEvent(

            timestamp=time.time(),

            victim_pid=proc.pid,

            victim_name=proc.name,

            victim_score=proc.oom_score,

            memory_freed_kb=proc.rss_kb,

            reason="Out of memory"

        )

        self.kill_log.append(event)



        # 从进程列表移除

        del self.processes[proc.pid]



        return event



    def run_oom_check(self) -> list[OOMKillEvent]:

        """执行OOM检查，返回被杀死的进程列表"""

        events = []

        while self.check_memory_pressure():

            victim = self.select_victim()

            if victim is None:

                break



            # 检查是否是受保护进程

            if victim.oom_adj == -17:

                print(f"警告：内存压力高但无法杀死受保护进程")

                break



            event = self.kill_process(victim)

            events.append(event)

            print(f"OOM Killer: 杀死进程 {victim.pid} ({victim.name}), "

                  f"score={victim.oom_score}, 释放 {event.memory_freed_kb}KB")



        return events



    def get_process_scores(self) -> list[tuple]:

        """获取所有进程的OOM评分（排序）"""

        uptime = time.time()

        calculator = OOMScoreCalculator()



        scores = []

        for proc in self.processes.values():

            score = calculator.calculate_score(proc, uptime)

            scores.append((proc.pid, proc.name, score, proc.rss_kb // 1024))



        scores.sort(key=lambda x: -x[2])  # 按分数降序

        return scores





if __name__ == "__main__":

    print("=== OOM Killer 演示 ===")



    # 创建OOM Killer（4GB内存）

    oom = OOMKiller(available_memory_kb=4 * 1024 * 1024)



    # 模拟运行中的进程

    print("\n--- 模拟进程注册 ---")

    processes = [

        (1001, "nginx", 50000, 120000),

        (1002, "python-app", 800000, 2000000),

        (1003, "redis-server", 150000, 500000),

        (1004, "mysql", 300000, 1500000),

        (1005, "init", 8000, 20000),  # init进程，低优先级

    ]



    for pid, name, rss, vms in processes:

        oom.register_process(pid, name, rss, vms)



    # 调整oom_adj

    oom.set_oom_adj(1005, -17)  # init永不被杀



    # 查看进程OOM评分

    print("\n--- OOM评分（按分数降序）---")

    print(f"{'PID':<8} {'名称':<15} {'评分':<8} {'RSS(MB)':<10}")

    for pid, name, score, rss_mb in oom.get_process_scores():

        print(f"{pid:<8} {name:<15} {score:<8} {rss_mb:<10}")



    # 模拟内存压力

    print("\n--- 模拟内存压力 ---")

    # 添加更多内存消耗进程

    for i in range(10):

        oom.register_process(2000 + i, f"memory-hog-{i}", 400000, 1000000)



    print(f"总进程数: {len(oom.processes)}")

    print(f"内存压力: {'是' if oom.check_memory_pressure() else '否'}")



    # 执行OOM检查

    print("\n--- 执行OOM检查 ---")

    killed = oom.run_oom_check()



    print(f"\n共杀死 {len(killed)} 个进程")

    if killed:

        print("击杀日志:")

        for e in killed:

            print(f"  [{time.strftime('%H:%M:%S', time.localtime(e.timestamp))}] "

                  f"P{e.victim_pid} ({e.victim_name}) score={e.victim_score}, "

                  f"释放{e.memory_freed_kb // 1024}MB")



    print("\n--- 最终状态 ---")

    print(f"剩余进程数: {len(oom.processes)}")

