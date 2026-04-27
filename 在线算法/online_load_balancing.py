# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / online_load_balancing



本文件实现 online_load_balancing 相关的算法功能。

"""



import random

from typing import List, Tuple





class LoadBalancer:

    """在线负载均衡器"""



    def __init__(self, servers: List[int]):

        """

        参数：

            servers: 服务器列表，每项是容量或处理能力

        """

        self.servers = servers

        self.current_load = [0] * len(servers)



    def greedy_assign(self, task: int) -> int:

        """

        贪心分配：将任务分配给当前负载最小的服务器



        返回：被分配的服务器索引

        """

        min_load = float('inf')

        best_server = 0



        for i in range(len(self.servers)):

            effective_load = self.current_load[i] / self.servers[i]

            if effective_load < min_load:

                min_load = effective_load

                best_server = i



        self.current_load[best_server] += task

        return best_server



    def round_robin_assign(self, task: int) -> int:

        """

        轮询分配（不感知负载）



        返回：被分配的服务器索引

        """

        idx = self.current_load.index(min(self.current_load))

        self.current_load[idx] += task

        return idx



    def random_assign(self, task: int) -> int:

        """随机分配"""

        idx = random.randint(0, len(self.servers) - 1)

        self.current_load[idx] += task

        return idx



    def get_max_load(self) -> int:

        """获取当前最大负载"""

        return max(self.current_load)



    def get_load_imbalance(self) -> float:

        """获取负载不均衡度"""

        max_load = max(self.current_load)

        avg_load = sum(self.current_load) / len(self.current_load)

        return max_load / avg_load if avg_load > 0 else 1.0





def simulate_load_balancing(n_servers: int, n_tasks: int, task_sizes: List[int]) -> dict:

    """

    模拟负载均衡



    参数：

        n_servers: 服务器数

        n_tasks: 任务数

        task_sizes: 任务大小列表



    返回：各算法的最大负载

    """

    servers = [1] * n_servers  # 服务器处理能力相同



    results = {}



    # Greedy

    lb_greedy = LoadBalancer(servers)

    for task in task_sizes:

        lb_greedy.greedy_assign(task)

    results['Greedy'] = lb_greedy.get_max_load()



    # Round Robin

    lb_rr = LoadBalancer(servers.copy())

    for task in task_sizes:

        lb_rr.round_robin_assign(task)

    results['RoundRobin'] = lb_rr.get_max_load()



    # Random

    lb_rand = LoadBalancer(servers.copy())

    for task in task_sizes:

        lb_rand.random_assign(task)

    results['Random'] = lb_rand.get_max_load()



    # Optimal (offline, 已知所有任务)

    lb_opt = LoadBalancer(servers.copy())

    sorted_tasks = sorted(task_sizes, reverse=True)

    for task in sorted_tasks:

        lb_opt.greedy_assign(task)

    results['Optimal'] = lb_opt.get_max_load()



    return results





def power_of_two_choices():

    """

    Power of Two Choices算法



    思想：随机选2个服务器，分配给负载较小的



    关键结果：使用O(log n)概率保证最大负载接近平均负载

    """

    n_servers = 100

    servers = [0] * n_servers



    tasks = [random.randint(1, 10) for _ in range(1000)]



    for task in tasks:

        # 随机选2个

        i, j = random.sample(range(n_servers), 2)

        if servers[i] < servers[j]:

            servers[i] += task

        else:

            servers[j] += task



    max_load = max(servers)

    avg_load = sum(servers) / n_servers



    return max_load, avg_load





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 在线负载均衡测试 ===\n")



    random.seed(42)



    # 设置

    n_servers = 5

    n_tasks = 20

    task_sizes = [random.randint(1, 10) for _ in range(n_tasks)]



    print(f"服务器数: {n_servers}")

    print(f"任务数: {n_tasks}")

    print(f"任务大小: {task_sizes}")

    print()



    # 模拟

    results = simulate_load_balancing(n_servers, n_tasks, task_sizes)



    print("各算法的最大负载:")

    for algo, max_load in sorted(results.items(), key=lambda x: x[1]):

        ratio = max_load / results['Optimal']

        print(f"  {algo:10s}: {max_load:3d} (vs 最优 {ratio:.2f}x)")



    print()



    # Power of Two Choices

    print("Power of Two Choices (大规模):")

    max_load, avg_load = power_of_two_choices()

    print(f"  服务器数: 100")

    print(f"  任务数: 1000")

    print(f"  最大负载: {max_load}")

    print(f"  平均负载: {avg_load:.1f}")

    print(f"  比值: {max_load/avg_load:.2f}")



    print("\n说明：")

    print("  - Greedy竞争比 O(log n)")

    print("  - Power of Two Choices是实际常用方案")

    print("  - 随机化有助于避免最坏情况")

