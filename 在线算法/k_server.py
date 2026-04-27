# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / k_server



本文件实现 k_server 相关的算法功能。

"""



import random

import math





class MetricSpace:

    """度量空间"""



    def __init__(self, space_type='euclidean'):

        """

        初始化度量空间

        

        参数:

            space_type: 空间类型 - 'euclidean', 'line', 'tree'

        """

        self.space_type = space_type

        self.points = []



    def distance(self, p1, p2):

        """

        计算两点间距离

        

        参数:

            p1: 点1

            p2: 点2

        返回:

            dist: 距离

        """

        if self.space_type == 'euclidean':

            return math.sqrt(sum((a - b) ** 2 for a, b in zip(p1, p2)))

        elif self.space_type == 'line':

            return abs(p1 - p2)

        return 0



    def add_point(self, point):

        """添加点"""

        self.points.append(point)





class Server:

    """服务器"""



    def __init__(self, server_id, position):

        """

        初始化服务器

        

        参数:

            server_id: 服务器 ID

            position: 位置

        """

        self.server_id = server_id

        self.position = position



    def move_to(self, new_position):

        """移动到新位置"""

        self.position = new_position



    def distance_to(self, point, metric):

        """计算到请求点的距离"""

        return metric.distance(self.position, point)





class KServerAlgorithm:

    """K-Server 算法基类"""



    def __init__(self, servers, metric):

        """

        初始化算法

        

        参数:

            servers: 服务器列表

            metric: 度量空间

        """

        self.servers = servers

        self.metric = metric

        self.total_cost = 0



    def find_nearest_server(self, request_point):

        """

        找到最近的服务器

        

        参数:

            request_point: 请求点

        返回:

            server: 最近的服务器

        """

        min_dist = float('inf')

        nearest = None

        

        for server in self.servers:

            dist = server.distance_to(request_point, self.metric)

            if dist < min_dist:

                min_dist = dist

                nearest = server

        

        return nearest, min_dist



    def move_server(self, server, new_position):

        """

        移动服务器

        

        参数:

            server: 服务器

            new_position: 新位置

        """

        dist = self.metric.distance(server.position, new_position)

        server.move_to(new_position)

        self.total_cost += dist



    def handle_request(self, request_point):

        """

        处理请求（子类实现）

        

        参数:

            request_point: 请求点

        """

        raise NotImplementedError





class HarmonicKServer(KServerAlgorithm):

    """

    Harmonic 算法

    

    每个服务器以概率 1/(1+dist) 响应请求

    概率化的方法，避免知道未来请求

    """



    def __init__(self, servers, metric):

        super().__init__(servers, metric)



    def handle_request(self, request_point):

        """处理请求"""

        # 计算每个服务器的距离

        distances = []

        for server in self.servers:

            dist = server.distance_to(request_point, self.metric)

            distances.append((dist, server))

        

        # 计算选择概率

        total_weight = sum(1.0 / (1 + d) for d, _ in distances)

        

        # 轮盘赌选择

        r = random.random() * total_weight

        cumsum = 0

        

        for dist, server in distances:

            cumsum += 1.0 / (1 + dist)

            if r <= cumsum:

                # 移动此服务器

                if dist > 0:

                    self.move_server(server, request_point)

                return

        

        # 默认选择最近的

        nearest, min_dist = distances[0][1], distances[0][0]

        if min_dist > 0:

            self.move_server(nearest, request_point)





class BalanceKServer(KServerAlgorithm):

    """

    BALANCE 算法

    

    总是使用负载最少的服务器

    简单的贪婪策略

    """



    def __init__(self, servers, metric):

        super().__init__(servers, metric)

        # 每个服务器的负载（移动成本）

        self.loads = {s.server_id: 0 for s in servers}



    def handle_request(self, request_point):

        """处理请求"""

        # 找到负载最小的服务器

        min_load = float('inf')

        target_server = None

        

        for server in self.servers:

            if self.loads[server.server_id] < min_load:

                min_load = self.loads[server.server_id]

                target_server = server

        

        # 移动该服务器

        dist = server.distance_to(request_point, self.metric)

        if dist > 0:

            self.move_server(server, request_point)

            self.loads[server.server_id] += dist





class WorkFunctionAlgorithm(KServerAlgorithm):

    """

    Work Function Algorithm (WFA)

    

    最优的 K-Server 在线算法（竞争比 = 2K-1）

    但实现较复杂

    """



    def __init__(self, servers, metric):

        super().__init__(servers, metric)

        # 工作函数：记录每个配置的总成本

        self.work_function = {}

        # 服务器位置历史

        self.server_positions = [s.position for s in servers]



    def _generate_configurations(self):

        """生成所有可能的服务器配置"""

        # 简化：只考虑移动一个服务器的情况

        configs = []

        # 基准配置

        configs.append(tuple(self.server_positions))

        return configs



    def handle_request(self, request_point):

        """处理请求"""

        # 简化的 WFA：移动成本最低的服务器

        min_cost = float('inf')

        best_server = None

        

        for i, server in enumerate(self.servers):

            # 计算移动成本

            move_cost = self.metric.distance(server.position, request_point)

            

            # 计算间接成本（其他服务器不动）

            indirect_cost = 0

            for j, other_server in enumerate(self.servers):

                if i != j:

                    indirect_cost += self.metric.distance(

                        self.server_positions[j],

                        request_point if j == i else self.server_positions[j]

                    )

            

            total_cost = move_cost + indirect_cost

            

            if total_cost < min_cost:

                min_cost = total_cost

                best_server = i

        

        # 移动选中的服务器

        if best_server is not None:

            server = self.servers[best_server]

            self.move_server(server, request_point)

            self.server_positions[best_server] = request_point





class KServerSimulator:

    """K-Server 模拟器"""



    def __init__(self, servers, metric, algorithm):

        """

        初始化模拟器

        

        参数:

            servers: 服务器列表

            metric: 度量空间

            algorithm: 算法名称

        """

        self.servers = servers

        self.metric = metric

        

        if algorithm == 'harmonic':

            self.algo = HarmonicKServer(servers, metric)

        elif algorithm == 'balance':

            self.algo = BalanceKServer(servers, metric)

        elif algorithm == 'wfa':

            self.algo = WorkFunctionAlgorithm(servers, metric)

        else:

            self.algo = KServerAlgorithm(servers, metric)

        

        self.requests = []



    def add_request(self, point):

        """添加请求"""

        self.requests.append(point)



    def run(self):

        """运行所有请求"""

        for request in self.requests:

            self.algo.handle_request(request)



    def get_total_cost(self):

        """获取总成本"""

        return self.algo.total_cost



    def get_server_positions(self):

        """获取服务器位置"""

        return [s.position for s in self.servers]





if __name__ == "__main__":

    print("=== K-Server 问题测试 ===\n")



    # 创建度量空间（一维直线）

    metric = MetricSpace(space_type='line')

    

    # 创建服务器

    servers = [

        Server(0, 0),

        Server(1, 10),

        Server(2, 20),

    ]

    

    print(f"初始服务器位置: {[s.position for s in servers]}")



    # 测试 Harmonic 算法

    print("\n--- Harmonic 算法 ---")

    harmonic_servers = [Server(i, [0, 10, 20][i]) for i in range(3)]

    harmonic = HarmonicKServer(harmonic_servers, metric)

    

    requests = [5, 15, 25, 3, 12, 22, 8]

    for req in requests:

        harmonic.handle_request(req)

        print(f"  请求 {req}: 成本累计 = {harmonic.total_cost}")

    

    print(f"  总成本: {harmonic.total_cost}")

    print(f"  服务器位置: {[s.position for s in harmonic_servers]}")



    # 测试 BALANCE 算法

    print("\n--- BALANCE 算法 ---")

    balance_servers = [Server(i, [0, 10, 20][i]) for i in range(3)]

    balance = BalanceKServer(balance_servers, metric)

    

    for req in requests:

        balance.handle_request(req)

        print(f"  请求 {req}: 成本累计 = {balance.total_cost}")

    

    print(f"  总成本: {balance.total_cost}")



    # 对比测试

    print("\n--- 算法对比 ---")

    import random

    

    # 随机请求序列

    random.seed(42)

    test_requests = [random.randint(0, 100) for _ in range(100)]

    

    algorithms = ['harmonic', 'balance', 'wfa']

    

    for algo_name in algorithms:

        # 创建新服务器

        test_servers = [Server(i, [0, 30, 60][i]) for i in range(3)]

        metric_test = MetricSpace(space_type='line')

        

        # 创建模拟器

        if algo_name == 'harmonic':

            algo = HarmonicKServer(test_servers, metric_test)

        elif algo_name == 'balance':

            algo = BalanceKServer(test_servers, metric_test)

        else:

            algo = WorkFunctionAlgorithm(test_servers, metric_test)

        

        # 运行

        for req in test_requests:

            algo.handle_request(req)

        

        print(f"  {algo_name}: 总成本 = {algo.total_cost}")



    # 竞争比分析（与最优离线算法比较）

    print("\n--- 竞争比分析 ---")

    

    # 简单的"最优"离线算法：知道所有请求后，每次移动最近的服务器

    def offline_optimal(requests, initial_positions):

        """离线最优算法（仅用于对比）"""

        servers = list(initial_positions)

        cost = 0

        

        for req in requests:

            # 找到最近的服务器

            min_dist = float('inf')

            best_server = 0

            

            for i, pos in enumerate(servers):

                dist = abs(pos - req)

                if dist < min_dist:

                    min_dist = dist

                    best_server = i

            

            # 移动

            if min_dist > 0:

                servers[best_server] = req

                cost += min_dist

        

        return cost

    

    # 比较

    test_requests = [random.randint(0, 100) for _ in range(50)]

    

    print("请求序列长度:", len(test_requests))

    print(f"请求: {test_requests[:10]}...")

    

    # 离线最优

    opt_cost = offline_optimal(test_requests, [0, 30, 60])

    print(f"\n离线最优成本: {opt_cost}")

    

    # 各在线算法

    for algo_name in ['harmonic', 'balance', 'wfa']:

        test_servers = [Server(i, [0, 30, 60][i]) for i in range(3)]

        metric_test = MetricSpace(space_type='line')

        

        if algo_name == 'harmonic':

            algo = HarmonicKServer(test_servers, metric_test)

        elif algo_name == 'balance':

            algo = BalanceKServer(test_servers, metric_test)

        else:

            algo = WorkFunctionAlgorithm(test_servers, metric_test)

        

        for req in test_requests:

            algo.handle_request(req)

        

        ratio = algo.total_cost / opt_cost if opt_cost > 0 else 0

        print(f"{algo_name}: 成本={algo.total_cost}, 竞争比={ratio:.2f}")

