# -*- coding: utf-8 -*-
"""
算法实现：在线算法 / metrical_task_system

本文件实现 metrical_task_system 相关的算法功能。
"""

import random
import math


class MetricalTaskSystem:
    """Metrical Task System 基类"""

    def __init__(self, states, distances):
        """
        初始化 MTS
        
        参数:
            states: 状态列表
            distances: 距离矩阵 dict[state][state] -> distance
        """
        self.states = states
        self.distances = distances
        self.n_states = len(states)
        self.state_index = {s: i for i, s in enumerate(states)}
        # 当前状态
        self.current_state = states[0]
        # 总代价
        self.total_cost = 0
        # 访问统计
        self.access_count = {s: 0 for s in states}

    def move_to(self, new_state):
        """
        移动到新状态
        
        参数:
            new_state: 目标状态
        返回:
            cost: 移动代价
        """
        cost = self.distances[self.current_state][new_state]
        self.current_state = new_state
        self.total_cost += cost
        return cost

    def get_distance(self, state1, state2):
        """获取两状态间距离"""
        return self.distances[state1][state2]

    def reset(self):
        """重置"""
        self.current_state = self.states[0]
        self.total_cost = 0


class DoubleCoverageMTS(MetricalTaskSystem):
    """
    Double Coverage (DC) 算法
    
    DC 算法维护一个"活动区间"，当请求到来时，
    选择区间内最近的服务器移动。
    """

    def __init__(self, states, distances):
        super().__init__(states, distances)
        # 服务器位置（可以是任意状态）
        self.server_positions = set([states[0]])  # 初始位置
        # 活动区间
        self.active_interval = [states[0], states[0]]

    def handle_request(self, request_state):
        """
        处理请求
        
        参数:
            request_state: 请求所在状态
        """
        self.access_count[request_state] += 1
        
        # 如果请求已经在某个服务器位置
        if request_state in self.server_positions:
            return 0
        
        # 找到请求两边的最近服务器
        left_server = None
        right_server = None
        
        # 简化的左右选择
        for state in self.states:
            if state in self.server_positions:
                if state < request_state:
                    if left_server is None or state > left_server:
                        left_server = state
                elif state > request_state:
                    if right_server is None or state < right_server:
                        right_server = state
        
        # 计算距离
        left_dist = self.get_distance(left_server, request_state) if left_server else float('inf')
        right_dist = self.get_distance(right_server, request_state) if right_server else float('inf')
        
        # 选择最近的
        if left_dist <= right_dist and left_server:
            return self.move_to(left_server)
        elif right_server:
            return self.move_to(right_server)
        
        return 0


class BalanceMTS(MetricalTaskSystem):
    """
    Balance 算法
    
    总是移动到负载最小的状态
    """

    def __init__(self, states, distances):
        super().__init__(states, distances)
        # 负载计数器
        self.loads = {s: 0 for s in states}

    def handle_request(self, request_state):
        """处理请求"""
        self.access_count[request_state] += 1
        
        # 如果当前状态可以服务
        if self.current_state == request_state:
            return 0
        
        # 找到负载最小的相邻状态
        min_load = float('inf')
        best_state = None
        
        for state in self.states:
            load = self.loads[state]
            if load < min_load:
                min_load = load
                best_state = state
        
        # 移动到负载最小的状态
        if best_state != self.current_state:
            return self.move_to(best_state)
        return 0

    def move_to(self, new_state):
        """移动并更新负载"""
        cost = super().move_to(new_state)
        self.loads[new_state] += 1
        return cost


class WorkFunctionMTS(MetricalTaskSystem):
    """
    Work Function Algorithm (WFA) for MTS
    
    最优的 MTS 在线算法，竞争比 = 2k-1
    """

    def __init__(self, states, distances):
        super().__init__(states, distances)
        # 工作函数：state -> cost
        self.work_function = {s: 0 for s in states}
        # 历史
        self.request_history = []
        self.position_history = [states[0]]

    def _compute_work(self, state, new_request):
        """
        计算到某状态的工作函数值
        
        参数:
            state: 状态
            new_request: 新请求
        返回:
            work: 工作函数值
        """
        # W_i(s) = min { W_{i-1}(s') + d(s', s) }
        # 其中 s' 是上一个位置，d 是移动代价
        
        min_work = float('inf')
        last_pos = self.position_history[-1]
        
        for prev_state in self.states:
            # 上一步的代价 + 移动代价
            work = self.work_function[prev_state] + self.get_distance(prev_state, state)
            if work < min_work:
                min_work = work
        
        # 如果请求在当前状态，不需要额外代价
        if state == new_request:
            return min_work
        
        return min_work

    def handle_request(self, request_state):
        """处理请求"""
        self.access_count[request_state] += 1
        self.request_history.append(request_state)
        
        # 更新工作函数
        old_work = dict(self.work_function)
        
        for state in self.states:
            self.work_function[state] = self._compute_work(state, request_state)
        
        # 选择工作函数值最小的状态
        min_work = float('inf')
        best_state = self.current_state
        
        for state in self.states:
            if self.work_function[state] < min_work:
                min_work = self.work_function[state]
                best_state = state
        
        # 移动到最佳状态
        cost = 0
        if best_state != self.current_state:
            cost = self.move_to(best_state)
        
        self.position_history.append(best_state)
        
        return cost


class RandomMTS(MetricalTaskSystem):
    """
    随机 MTS 算法
    
    随机选择移动方向
    """

    def __init__(self, states, distances):
        super().__init__(states, distances)

    def handle_request(self, request_state):
        """处理请求"""
        self.access_count[request_state] += 1
        
        if self.current_state == request_state:
            return 0
        
        # 随机决定是否移动
        if random.random() < 0.5:
            return self.move_to(request_state)
        
        return 0


class MetricalTaskSystemSimulator:
    """MTS 模拟器"""

    def __init__(self, states, distances):
        self.states = states
        self.distances = distances
        self.algorithms = {}

    def add_algorithm(self, name, algo):
        """添加算法"""
        self.algorithms[name] = algo

    def run(self, request_sequence, reset=True):
        """
        运行模拟
        
        参数:
            request_sequence: 请求序列
            reset: 是否在每个算法前重置
        返回:
            results: {algorithm: total_cost}
        """
        results = {}
        
        for name, algo in self.algorithms.items():
            if reset:
                algo.reset()
                algo.total_cost = 0
                algo.current_state = algo.states[0]
            
            for request in request_sequence:
                algo.handle_request(request)
            
            results[name] = algo.total_cost
        
        return results


def create_line_mts(n_points):
    """
    创建线上的 MTS 实例
    
    参数:
        n_points: 点数量
    返回:
        states, distances
    """
    states = list(range(n_points))
    
    # 距离 = 坐标差
    distances = {}
    for s1 in states:
        distances[s1] = {}
        for s2 in states:
            distances[s1][s2] = abs(s1 - s2)
    
    return states, distances


def create_general_mts(n_states, seed=42):
    """
    创建一般度量空间的 MTS
    
    参数:
        n_states: 状态数
        seed: 随机种子
    返回:
        states, distances
    """
    random.seed(seed)
    
    states = list(range(n_states))
    
    # 随机生成坐标
    coords = {s: (random.random(), random.random()) for s in states}
    
    # 计算欧氏距离
    distances = {}
    for s1 in states:
        distances[s1] = {}
        for s2 in states:
            x1, y1 = coords[s1]
            x2, y2 = coords[s2]
            distances[s1][s2] = math.sqrt((x1-x2)**2 + (y1-y2)**2)
    
    return states, distances


if __name__ == "__main__":
    print("=== Metrical Task System 测试 ===\n")

    # 创建线上的 MTS
    print("--- 线上的 MTS ---")
    n_points = 10
    states, distances = create_line_mts(n_points)
    
    # 创建算法
    dc = DoubleCoverageMTS(states, distances)
    balance = BalanceMTS(states, distances)
    wfa = WorkFunctionMTS(states, distances)
    random_algo = RandomMTS(states, distances)
    
    # 模拟器
    sim = MetricalTaskSystemSimulator(states, distances)
    sim.add_algorithm('DC', dc)
    sim.add_algorithm('Balance', balance)
    sim.add_algorithm('WFA', wfa)
    sim.add_algorithm('Random', random_algo)
    
    # 生成请求序列
    random.seed(42)
    requests = [random.randint(0, n_points-1) for _ in range(100)]
    
    print(f"请求序列: {requests[:20]}...")
    
    # 运行模拟
    results = sim.run(requests)
    
    print("\n结果:")
    for algo, cost in sorted(results.items(), key=lambda x: x[1]):
        print(f"  {algo}: {cost}")

    # 离线最优（需要知道所有请求）
    print("\n--- 离线最优比较 ---")
    
    def offline_optimal(states, distances, requests):
        """离线最优算法（简化为总是移动到最近的）"""
        cost = 0
        current = states[0]
        
        for req in requests:
            if current != req:
                cost += distances[current][req]
                current = req
        
        return cost
    
    opt_cost = offline_optimal(states, distances, requests)
    print(f"  离线最优: {opt_cost}")
    
    for name, cost in results.items():
        ratio = cost / opt_cost if opt_cost > 0 else 0
        print(f"  {name} 竞争比: {ratio:.2f}")

    # 一般度量空间
    print("\n--- 一般度量空间 MTS ---")
    n_states = 5
    states, distances = create_general_mts(n_states)
    
    print(f"状态数: {n_states}")
    
    # 创建算法
    algorithms = {
        'DC': DoubleCoverageMTS(states, distances),
        'Balance': BalanceMTS(states, distances),
        'WFA': WorkFunctionMTS(states, distances),
    }
    
    # 生成请求
    requests = [random.randint(0, n_states-1) for _ in range(50)]
    
    print(f"请求序列: {requests}")
    
    # 运行
    results = {}
    for name, algo in algorithms.items():
        for req in requests:
            algo.handle_request(req)
        results[name] = algo.total_cost
    
    print("\n结果:")
    for algo, cost in sorted(results.items(), key=lambda x: x[1]):
        print(f"  {algo}: {cost}")

    # 竞争比分析
    print("\n--- 竞争比分析 ---")
    
    for n_states in [5, 10, 20]:
        states, distances = create_general_mts(n_states)
        
        requests = [random.randint(0, n_states-1) for _ in range(100)]
        opt_cost = offline_optimal(states, distances, requests)
        
        wfa = WorkFunctionMTS(states, distances)
        for req in requests:
            wfa.handle_request(req)
        
        ratio = wfa.total_cost / opt_cost if opt_cost > 0 else 0
        print(f"  n={n_states}: WFA 竞争比 = {ratio:.2f}")
