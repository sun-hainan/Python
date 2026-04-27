# -*- coding: utf-8 -*-

"""

算法实现：操作系统内核 / oom_killer



本文件实现 oom_killer 相关的算法功能。

"""



from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass, field

from enum import Enum

import time





@dataclass

class OOMScore:

    """OOM分数计算结果"""

    points: int              # 总分数

    memory_points: int      # 内存贡献

    cpu_points: int         # CPU时间贡献

    runtime_points: int     # 运行时间贡献

    nice_points: int        # nice值贡献





class ProcessOOMInfo:

    """进程的OOM相关信息"""



    def __init__(self, pid: int, name: str):

        self.pid = pid

        self.name = name



        # 内存使用

        self.rss_kb = 0          # 常驻内存 (KB)

        self.vm_size_kb = 0      # 虚拟内存大小 (KB)

        self.memory_score = 0    # 内存分数



        # 运行时信息

        self.utime = 0           # 用户态时间

        self.stime = 0           # 内核态时间

        self.start_time = 0      # 进程启动时间

        self.runtime_score = 0   # 运行时间分数



        # OOM调整

        self.oom_score_adj = 0   # 分数调整 (-1000到1000)

        self.oom_score = 0       # 最终分数



        # 进程属性

        self.nice = 0            # nice值

        self.threads = 1          # 线程数

        self.is_root = False     # 是否root进程



    def calculate_oom_score(self) -> OOMScore:

        """

        计算OOM分数

        基于多个因素

        """

        # 内存分数（主要因素）

        # 分数 = RSS / 100MB * 基准分

        memory_points = self.rss_kb // (100 * 1024) * 100



        # CPU使用分数

        total_time = self.utime + self.stime

        cpu_points = min(100, total_time // 1000)



        # 运行时间分数（运行越久越不容易被选）

        runtime_points = 0

        if self.start_time > 0:

            uptime = time.time() - self.start_time

            # 每分钟减少一些分数

            runtime_points = max(0, 300 - int(upime / 60))



        # nice值分数

        # nice值越高(-20到19)，越容易被选

        nice_points = self.nice + 20



        # 线程数分数

        threads_points = (self.threads - 1) * 5



        # 总分数

        total = memory_points + cpu_points + runtime_points + nice_points + threads_points



        # 应用oom_score_adj调整

        # adj范围是-1000到1000，对应分数的-10%到+10%

        adj_factor = self.oom_score_adj / 10.0

        total = int(total * (100 + adj_factor) / 100)



        # root进程惩罚

        if self.is_root and self.name in ['init', 'systemd', 'kthreadd']:

            total = int(total * 0.8)  # 降低30%



        self.oom_score = max(0, total)



        return OOMScore(

            points=total,

            memory_points=memory_points,

            cpu_points=cpu_points,

            runtime_points=runtime_points,

            nice_points=nice_points

        )



    def get_oom_score_path(self) -> str:

        """获取oom_score文件路径"""

        return f"/proc/{self.pid}/oom_score"



    def get_oom_score_adj_path(self) -> str:

        """获取oom_score_adj文件路径"""

        return f"/proc/{self.pid}/oom_score_adj"





class OOMKiller:

    """

    OOM Killer



    当内存不足时，选择并终止进程。

    """



    # OOM Killer状态

    STATE_IDLE = "idle"

    STATE_KILLING = "killing"



    def __init__(self):

        # 状态

        self.state = self.STATE_IDLE



        # 系统内存信息

        self.total_memory_kb = 0

        self.free_memory_kb = 0

        self.available_memory_kb = 0

        self.used_memory_kb = 0



        # OOM阈值

        self.oom_score_adj_min = -1000

        self.oom_score_adj_max = 1000



        # 杀死历史

        self.kill_history: List[Dict] = []



        # 统计

        self.total_kills = 0



    def update_memory_info(self, total: int, free: int, available: int):

        """更新系统内存信息"""

        self.total_memory_kb = total

        self.free_memory_kb = free

        self.available_memory_kb = available

        self.used_memory_kb = total - free



    def check_oom_condition(self) -> bool:

        """

        检查是否需要触发OOM Killer

        当available_memory接近0时触发

        """

        # 当可用内存小于总内存的5%时，可能触发OOM

        threshold = self.total_memory_kb * 0.05

        return self.available_memory_kb < threshold



    def select_victim(self, processes: List[ProcessOOMInfo]) -> Optional[ProcessOOMInfo]:

        """

        选择牺牲进程

        选择OOM分数最高的进程

        """

        if not processes:

            return None



        # 计算每个进程的OOM分数

        for proc in processes:

            proc.calculate_oom_score()



        # 选择分数最高的

        # 排除被保护的特殊进程

        protected_names = {'init', 'systemd', 'kthreadd', 'migration', 'watchdog'}



        candidates = [p for p in processes if p.name not in protected_names]



        if not candidates:

            candidates = processes



        # 按分数排序

        candidates.sort(key=lambda p: p.oom_score, reverse=True)



        return candidates[0]



    def kill_process(self, process: ProcessOOMInfo, reason: str = "") -> bool:

        """

        杀死进程

        return: 是否成功

        """

        print(f"\n[OOM Killer] 选择牺牲进程:")

        print(f"  PID: {process.pid}")

        print(f"  名称: {process.name}")

        print(f"  RSS: {process.rss_kb} KB")

        print(f"  OOM分数: {process.oom_score}")

        print(f"  OOM调整: {process.oom_score_adj}")



        if reason:

            print(f"  原因: {reason}")



        # 记录杀死历史

        self.kill_history.append({

            'timestamp': time.time(),

            'pid': process.pid,

            'name': process.name,

            'oom_score': process.oom_score,

            'rss_kb': process.rss_kb,

            'reason': reason

        })



        self.total_kills += 1

        self.state = self.STATE_KILLING



        return True



    def simulate_oom(self, processes: List[ProcessOOMInfo]) -> Optional[ProcessOOMInfo]:

        """

        模拟一次OOM

        return: 被选中的进程

        """

        print("\n" + "=" * 60)

        print("OOM模拟")

        print("=" * 60)



        print(f"\n系统内存状态:")

        print(f"  总内存: {self.total_memory_kb / 1024:.1f} MB")

        print(f"  可用内存: {self.available_memory_kb / 1024:.1f} MB")

        print(f"  使用内存: {self.used_memory_kb / 1024:.1f} MB")



        # 检查是否需要OOM

        if not self.check_oom_condition():

            print("\n内存充足，未触发OOM")

            return None



        print("\n内存不足！触发OOM Killer...")



        # 选择牺牲进程

        victim = self.select_victim(processes)



        if victim:

            self.kill_process(victim, "内存不足，需要释放内存")

            return victim



        return None



    def get_oom_stats(self) -> Dict:

        """获取OOM统计"""

        return {

            'total_kills': self.total_kills,

            'state': self.state,

            'kill_history': self.kill_history

        }





class OOMScoreAdj:

    """

    oom_score_adj调整工具



    允许用户调整进程的OOM分数。

    值范围：-1000 到 +1000

    -1000：进程永远不会被OOM Killer杀死

    +1000：进程优先被杀死

    """



    def __init__(self):

        self.adjustments: Dict[int, int] = {}  # pid -> adj



    def set_oom_score_adj(self, pid: int, adj: int) -> bool:

        """

        设置进程的oom_score_adj

        """

        if adj < -1000 or adj > 1000:

            return False



        self.adjustments[pid] = adj

        print(f"  设置 PID={pid} oom_score_adj={adj}")

        return True



    def get_oom_score_adj(self, pid: int) -> int:

        """获取进程的oom_score_adj"""

        return self.adjustments.get(pid, 0)



    def calculate_adjusted_score(self, base_score: int, adj: int) -> int:

        """

        计算调整后的分数

        """

        # adj范围-1000到1000，对应-10%到+10%的调整

        factor = adj / 10.0

        return int(base_score * (100 + factor) / 100)





def simulate_oom_killer():

    """

    模拟OOM Killer

    """

    print("=" * 60)

    print("OOM Killer (Out-of-Memory Killer)")

    print("=" * 60)



    # 创建OOM Killer

    oom_killer = OOMKiller()



    # 设置内存状态（模拟内存不足）

    oom_killer.update_memory_info(

        total=8 * 1024 * 1024,      # 8GB

        free=100 * 1024,            # 100MB

        available=150 * 1024        # 150MB

    )



    # 创建一些进程

    processes = []



    # 内存占用大的进程

    proc1 = ProcessOOMInfo(1, "nginx_worker")

    proc1.rss_kb = 500 * 1024  # 500MB

    proc1.nice = 0

    proc1.threads = 10

    processes.append(proc1)



    # 普通进程

    proc2 = ProcessOOMInfo(2, "bash")

    proc2.rss_kb = 50 * 1024  # 50MB

    proc2.nice = 0

    processes.append(proc2)



    # 低优先级进程

    proc3 = ProcessOOMInfo(3, "background_task")

    proc3.rss_kb = 200 * 1024  # 200MB

    proc3.nice = 10

    proc3.threads = 2

    processes.append(proc3)



    # root进程（受保护）

    proc4 = ProcessOOMInfo(4, "init")

    proc4.rss_kb = 30 * 1024  # 30MB

    proc4.is_root = True

    processes.append(proc4)



    # 显示进程信息

    print("\n进程列表:")

    print("-" * 60)

    print(f"  {'PID':<6} {'名称':<20} {'RSS':<10} {'Nice':<6} {'线程':<6}")

    print(f"  {'-'*60}")



    for proc in processes:

        print(f"  {proc.pid:<6} {proc.name:<20} {proc.rss_kb:<10} {proc.nice:<6} {proc.threads:<6}")



    # 计算并显示OOM分数

    print("\nOOM分数计算:")

    print("-" * 60)

    print(f"  {'PID':<6} {'名称':<20} {'内存分':<8} {'总分':<8} {'最终分':<8}")

    print(f"  {'-'*60}")



    for proc in processes:

        score = proc.calculate_oom_score()

        print(f"  {proc.pid:<6} {proc.name:<20} {score.memory_points:<8} {score.points:<8} {proc.oom_score:<8}")



    # 触发OOM

    victim = oom_killer.simulate_oom(processes)



    # oom_score_adj演示

    print("\n" + "=" * 60)

    print("oom_score_adj 调整演示")

    print("=" * 60)



    adj_tool = OOMScoreAdj()



    print("\n调整PID=1的oom_score_adj:")

    print("-" * 50)



    # 原始分数

    base_score = proc1.calculate_oom_score().points

    print(f"  原始分数: {base_score}")



    # 降低优先级（减少被杀的概率）

    adj_tool.set_oom_score_adj(proc1.pid, -500)

    adjusted = adj_tool.calculate_adjusted_score(base_score, -500)

    print(f"  调整后分数 (adj=-500): {adjusted}")



    # 恢复

    adj_tool.set_oom_score_adj(proc1.pid, 0)

    adjusted = adj_tool.calculate_adjusted_score(base_score, 0)

    print(f"  恢复分数 (adj=0): {adjusted}")



    # 提高优先级（增加被杀的概率）

    adj_tool.set_oom_score_adj(proc1.pid, 500)

    adjusted = adj_tool.calculate_adjusted_score(base_score, 500)

    print(f"  提高分数 (adj=+500): {adjusted}")



    # 彻底保护（-1000）

    print("\n彻底保护 PID=1 (adj=-1000):")

    adj_tool.set_oom_score_adj(proc1.pid, -1000)

    adjusted = adj_tool.calculate_adjusted_score(base_score, -1000)

    print(f"  最终分数: {adjusted}")

    print(f"  进程不会被OOM Killer杀死")



    # OOM统计

    print("\n" + "=" * 60)

    print("OOM Killer 统计")

    print("=" * 60)



    stats = oom_killer.get_oom_stats()

    print(f"  总杀死次数: {stats['total_kills']}")

    print(f"  当前状态: {stats['state']}")



    if stats['kill_history']:

        print(f"\n杀死历史:")

        for entry in stats['kill_history']:

            print(f"  PID={entry['pid']}, name={entry['name']}, "

                  f"score={entry['oom_score']}, rss={entry['rss_kb']}KB")





if __name__ == "__main__":

    simulate_oom_killer()

