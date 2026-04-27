# -*- coding: utf-8 -*-

"""

算法实现：运筹学 / job_shop_scheduling



本文件实现 job_shop_scheduling 相关的算法功能。

"""



import numpy as np

from itertools import permutations





def johnson_algorithm(jobs):

    """

    Johnson 算法：求解 2 台机器的 Flow Shop



    假设：

    - 所有工件按相同顺序经过机器 1 和机器 2

    - 最小化 makespan



    规则：

    - 若 min(A_i, B_i) = A_i，将工件 i 排在前

    - 若 min(A_i, B_i) = B_i，将工件 j 排在后



    Parameters

    ----------

    jobs : list of tuples

        [(machine1_time, machine2_time), ...]

    """

    n = len(jobs)

    queue1 = []  # A_i <= B_i

    queue2 = []  # A_i > B_i



    for i, (a, b) in enumerate(jobs):

        if a <= b:

            queue1.append((i, a, b))

        else:

            queue2.append((i, a, b))



    # 队列 1 按 A_i 升序，队列 2 按 B_i 降序

    queue1.sort(key=lambda x: x[1])

    queue2.sort(key=lambda x: x[2], reverse=True)



    order = queue1 + queue2



    # 计算 makespan

    m1_time = 0

    m2_time = 0

    makespan = 0



    schedule = []

    for idx, a, b in order:

        m1_time += a

        m2_time = max(m1_time, m2_time) + b

        makespan = m2_time

        schedule.append((idx, a, b, m1_time, m2_time))



    return {

        'order': [x[0] for x in order],

        'makespan': makespan,

        'schedule': schedule

    }





def neh_heuristic(jobs_data):

    """

    NEH 启发式（用于 m 台机器 Flow Shop）



    步骤：

    1. 按总加工时间降序排列工件

    2. 取前两个工件，尝试两种顺序，选择 makespan 小的

    3. 依次加入新工件，尝试所有插入位置，选择最优

    """

    pass





def gantt_chart_schedule(schedule, machines, jobs_data):

    """

    生成甘特图数据

    """

    gantt = []

    for op in schedule:

        job_id, machine_id, start, duration = op

        gantt.append({

            'job': job_id,

            'machine': machine_id,

            'start': start,

            'end': start + duration

        })

    return gantt





def job_shop_bruteforce(jobs, machines, max_schedules=10000):

    """

    暴力搜索（仅适用于小规模）

    枚举所有可能的工序顺序组合

    """

    # jobs: list of lists, 每个子列表是工序 [(machine, time), ...]



    # 简化：假设每 job 2 工序，2 machines

    n_jobs = len(jobs)



    best_makespan = np.inf

    best_schedule = None



    job_perms = list(permutations(range(n_jobs)))



    count = 0

    for perm in job_perms:

        if count >= max_schedules:

            break



        schedule = []

        machine_times = [0, 0]  # 每台机器的当前时间



        for job_idx in perm:

            for machine, duration in jobs[job_idx]:

                start = machine_times[machine]

                machine_times[machine] = start + duration

                schedule.append((job_idx, machine, start, duration))



        makespan = max(machine_times)

        if makespan < best_makespan:

            best_makespan = makespan

            best_schedule = schedule



        count += 1



    return {

        'makespan': best_makespan,

        'schedule': best_schedule

    }





def job_shop_dispatch(jobs, machines, rule=' shortest_processing_time'):

    """

    调度规则（Dispatch Rules）



    常见规则：

    - SPT: 最短加工时间优先

    - EDD: 最早交货期优先

    - LPT: 最长加工时间优先

    - FCFS: 先到先服务

    """

    from collections import deque



    # 简化：每 job 2 工序

    n_jobs = len(jobs)



    # 队列

    queue = list(range(n_jobs))

    machine_queue = {m: [] for m in machines}



    # 工序索引

    op_idx = {j: 0 for j in range(n_jobs)}



    schedule = []

    time = 0

    completed = 0



    while completed < n_jobs:

        # 分配工件到机器

        for m in machines:

            if not machine_queue[m] and queue:

                # 根据规则选择

                if rule == 'SPT':

                    # 选择总加工时间最短的

                    best_job = min(queue, key=lambda j: sum(jobs[j][k][1] for k in range(len(jobs[j]))))



                else:

                    best_job = queue[0]



                queue.remove(best_job)

                machine_queue[m].append(best_job)



        # 执行一步

        # 简化实现



        time += 1



    return schedule





def disjunctive_graph(jobs, machines):

    """

    将 Job Shop 建模为不相交图 (Disjunctive Graph)



    节点：

    - 源节点 S，汇节点 T

    - 每个工序一个节点



    边：

    - 合取边：同一工件的工序之间（有向）

    - 不相交的边：同一机器的工序之间（无向，选一组构成有向）

    """

    # 构图的简化实现

    pass





def simulated_annealing_jobshop(jobs, machines, initial_temp=1000, cooling=0.995, iterations=1000):

    """

    模拟退火求解 Job Shop



    邻域移动：交换同一机器上相邻的两个工序

    """

    n_jobs = len(jobs)



    # 初始化：随机顺序

    np.random.seed(42)

    schedule = []

    for job_idx in range(n_jobs):

        for machine, duration in jobs[job_idx]:

            schedule.append({

                'job': job_idx,

                'machine': machine,

                'duration': duration

            })



    # 计算 makespan

    def calc_makespan(sched):

        machine_times = {m: 0 for m in machines}

        job_times = {j: 0 for j in range(n_jobs)}



        # 按时间顺序模拟

        # 简化：使用拓扑排序



        # 按工件顺序分组

        job_sched = {j: [op for op in sched if op['job'] == j] for j in range(n_jobs)}

        machine_ops = {m: [op for op in sched if op['machine'] == m] for m in machines}



        # 计算

        ready = []

        for j in range(n_jobs):

            ready.append((job_times[j], job_sched[j][0] if job_sched[j] else None))



        # 简化

        return 100



    current_makespan = calc_makespan(schedule)

    best_makespan = current_makespan

    best_schedule = schedule.copy()



    temp = initial_temp



    for i in range(iterations):

        # 邻域移动：随机交换两个工序

        new_schedule = schedule.copy()

        idx1, idx2 = np.random.choice(len(schedule), 2, replace=False)

        new_schedule[idx1], new_schedule[idx2] = new_schedule[idx2], new_schedule[idx1]



        new_makespan = calc_makespan(new_schedule)



        # 接受准则

        delta = new_makespan - current_makespan

        if delta < 0 or np.random.random() < np.exp(-delta / temp):

            schedule = new_schedule

            current_makespan = new_makespan



            if new_makespan < best_makespan:

                best_makespan = new_makespan

                best_schedule = schedule.copy()



        temp *= cooling



    return {

        'makespan': best_makespan,

        'schedule': best_schedule

    }





if __name__ == "__main__":

    print("=" * 60)

    print("Job Shop 调度问题")

    print("=" * 60)



    # 示例：5 个工件，2 台机器

    # jobs[job_id] = [(machine_id, processing_time), ...]

    jobs = [

        [(0, 3), (1, 2)],  # 工件 0

        [(0, 2), (1, 4)],  # 工件 1

        [(1, 3), (0, 2)],  # 工件 2

        [(1, 2), (0, 3)],  # 工件 3

        [(0, 4), (1, 1)],  # 工件 4

    ]



    machines = [0, 1]



    print("\n工件数据 (machine, time):")

    for i, job in enumerate(jobs):

        print(f"  工件 {i}: {job}")



    # Johnson 算法（需要调整，因为顺序可能不同）

    print("\n--- Johnson 算法 (2-machine Flow Shop) ---")

    # 转换为标准格式

    jobs_johnson = [(3, 2), (2, 4), (3, 2), (2, 3), (4, 1)]

    result_johnson = johnson_algorithm(jobs_johnson)



    print(f"最优顺序: {result_johnson['order']}")

    print(f"Makespan: {result_johnson['makespan']}")



    # 暴力搜索

    print("\n--- 暴力搜索 ---")

    result_brute = job_shop_bruteforce(jobs, machines)

    print(f"Makespan: {result_brute['makespan']}")

    print(f"调度方案: {len(result_brute['schedule'])} 个操作")



    # 显示调度

    print("\n调度详情:")

    for op in result_brute['schedule']:

        job, machine, start, duration = op

        print(f"  工件 {job} 在机器 {machine}: {start}-{start+duration}")



    # 模拟退火

    print("\n--- 模拟退火 ---")

    result_sa = simulated_annealing_jobshop(jobs, machines, iterations=500)

    print(f"Makespan: {result_sa['makespan']}")



    # 简单的甘特图文本输出

    print("\n--- 甘特图 ---")

    print("时间:    0    5    10   15   20   25")

    print("-" * 40)



    for m in machines:

        print(f"机器 {m}: ", end="")

        for op in result_brute['schedule']:

            if op[1] == m:

                start, duration = op[2], op[3]

                bar = "█" * duration

                print(f"{' ' * start}{bar}", end="")

        print()

