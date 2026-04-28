"""
蚁群优化算法 (Ant Colony Optimization, ACO)
============================================

模拟蚂蚁觅食行为的优化算法,通过信息素引导搜索。
蚂蚁在路径上遗留信息素,其他蚂蚁倾向于选择信息素多的路径。

参考: Dorigo, M. (1992). Optimization, Learning and Natural Algorithms.
"""

import numpy as np
import random

# ============================================================
# ACO参数配置
# ============================================================

class ACOConfig:
    """蚁群算法配置参数"""

    def __init__(self):
        # 蚂蚁数量
        self.num_ants = 30
        # 信息素重要程度(alpha)
        self.alpha = 1.0
        # 启发式信息重要程度(beta)
        self.beta = 2.0
        # 信息素挥发系数(\rho)
        self.rho = 0.5
        # 信息素强度(Q)
        self.q = 100.0
        # 最大迭代次数
        self.max_iterations = 200


# ============================================================
# TSP问题数据
# ============================================================

class TSPLib:
    """TSP问题数据管理"""

    def __init__(self, cities=None):
        """
        初始化TSP数据

        参数:
            cities: 城市坐标列表,每项为(x, y)
        """
        if cities is None:
            # 默认生成若干城市
            self.cities = self._generate_random_cities(20)
        else:
            self.cities = cities

        self.n_cities = len(self.cities)

    def _generate_random_cities(self, n, seed=42):
        """生成随机城市坐标"""
        rng = np.random.default_rng(seed)
        return rng.uniform(0, 100, (n, 2)).tolist()

    def distance(self, i, j):
        """
        计算两城市间的欧氏距离

        参数:
            i: 城市i索引
            j: 城市j索引

        返回:
            两城市间的距离
        """
        x1, y1 = self.cities[i]
        x2, y2 = self.cities[j]
        return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def total_distance(self, tour):
        """
        计算给定路线的总长度

        参数:
            tour: 城市访问顺序列表

        返回:
            路线总长度
        """
        total = 0.0
        n = len(tour)
        for i in range(n):
            # 从当前城市到下一个城市
            total += self.distance(tour[i], tour[(i + 1) % n])
        return total


# ============================================================
# 蚁群算法主类
# ============================================================

class Ant:
    """
    单只蚂蚁类

    属性:
        tour: 访问城市顺序
        visited: 已访问城市集合
        tour_length: 当前路线总长度
    """

    def __init__(self, n_cities):
        """
        初始化蚂蚁

        参数:
            n_cities: 城市总数
        """
        self.n_cities = n_cities
        self.tour = []          # 访问顺序
        self.visited = set()    # 已访问城市集合
        self.tour_length = 0.0  # 路线长度

    def start_from(self, city):
        """
        从指定城市开始旅行

        参数:
            city: 起始城市索引
        """
        self.tour = [city]
        self.visited = {city}
        self.tour_length = 0.0

    def visit_next(self, city, distance):
        """
        移动到下一个城市

        参数:
            city: 目标城市索引
            distance: 从上一个城市到目标城市的距离
        """
        self.tour.append(city)
        self.visited.add(city)
        self.tour_length += distance

    def get_current_city(self):
        """获取当前位置(最后一个访问的城市)"""
        return self.tour[-1]

    def has_visited(self, city):
        """检查城市是否已访问"""
        return city in self.visited

    def can_visit(self, city):
        """检查是否可以访问该城市"""
        return city not in self.visited

    def complete_tour(self, tsp):
        """
        完成环游,返回起点

        参数:
            tsp: TSPLib实例
        """
        # 形成完整环游:从终点返回起点
        self.tour_length += tsp.distance(self.tour[-1], self.tour[0])


class ACO:
    """
    蚁群优化器

    用于解决TSP等组合优化问题
    """

    def __init__(self, tsp, config=None):
        """
        初始化ACO

        参数:
            tsp: TSPLib实例(问题数据)
            config: ACOConfig配置对象
        """
        self.tsp = tsp
        self.config = config if config else ACOConfig()

        # 初始化信息素矩阵(所有路径初始信息素相同)
        self.n = tsp.n_cities
        self.pheromone = np.ones((self.n, self.n))

        # 距离矩阵(预计算,加速查询)
        self.distances = np.zeros((self.n, self.n))
        for i in range(self.n):
            for j in range(self.n):
                self.distances[i, j] = tsp.distance(i, j)

        # 启发式信息矩阵(距离的倒数,避免除零)
        self.eta = np.zeros((self.n, self.n))
        for i in range(self.n):
            for j in range(self.n):
                if i != j and self.distances[i, j] > 0:
                    self.eta[i, j] = 1.0 / self.distances[i, j]
                else:
                    self.eta[i, j] = 0.0

    def _transition_probability(self, current, next_city, visited):
        """
        计算状态转移概率

        公式: P_ij = (tau_ij^alpha * eta_ij^beta) / sum(tau_ik^alpha * eta_ik^beta)

        参数:
            current: 当前城市索引
            next_city: 候选下一城市
            visited: 已访问城市集合(用于计算分母)

        返回:
            转移概率
        """
        # 计算分子:信息素^alpha * 启发式^beta
        numerator = (self.pheromone[current, next_city] ** self.config.alpha) * \
                    (self.eta[current, next_city] ** self.config.beta)

        # 计算分母:所有可能选择的总和
        denominator = 0.0
        for j in range(self.n):
            if j not in visited:
                denominator += (self.pheromone[current, j] ** self.config.alpha) * \
                               (self.eta[current, j] ** self.config.beta)

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _select_next_city(self, current, visited):
        """
        基于概率选择下一个城市(轮盘赌选择)

        参数:
            current: 当前城市索引
            visited: 已访问城市集合

        返回:
            选中的下一城市索引
        """
        # 获取所有未访问城市
        unvisited = [j for j in range(self.n) if j not in visited]

        if not unvisited:
            return None

        # 计算每个未访问城市的转移概率
        probs = []
        for j in unvisited:
            prob = self._transition_probability(current, j, visited)
            probs.append((j, prob))

        # 如果所有概率都很低,随机选择
        total_prob = sum(p for _, p in probs)
        if total_prob < 1e-10:
            return random.choice(unvisited)

        # 轮盘赌选择
        rand = random.random() * total_prob
        cumulative = 0.0
        for city, prob in probs:
            cumulative += prob
            if cumulative >= rand:
                return city

        return probs[-1][0]  # 保底返回最后一个

    def _construct_solutions(self):
        """
        所有蚂蚁构建路线

        返回:
            ants: 蚂蚁列表
        """
        cfg = self.config
        ants = []

        for _ in range(cfg.num_ants):
            ant = Ant(self.n)

            # 随机选择起始城市
            start_city = random.randint(0, self.n - 1)
            ant.start_from(start_city)

            # 依次选择下一个城市直到访问完所有城市
            current = start_city
            while len(ant.visited) < self.n:
                next_city = self._select_next_city(current, ant.visited)
                if next_city is not None:
                    distance = self.distances[current, next_city]
                    ant.visit_next(next_city, distance)
                    current = next_city

            # 完成环游
            ant.complete_tour(self.tsp)
            ants.append(ant)

        return ants

    def _update_pheromone(self, ants):
        """
        更新信息素矩阵

        信息素挥发 + 信息素增加

        参数:
            ants: 蚂蚁列表(携带路线信息)
        """
        cfg = self.config

        # 1. 信息素挥发(所有路径按比例衰减)
        self.pheromone *= (1.0 - cfg.rho)

        # 2. 信息素增加(根据蚂蚁路线)
        for ant in ants:
            # 每只蚂蚁在其走过的路径上释放信息素
            # 释放量与路线长度成反比(越短越好)
            delta_pheromone = cfg.q / ant.tour_length if ant.tour_length > 0 else 0

            for i in range(len(ant.tour)):
                from_city = ant.tour[i]
                to_city = ant.tour[(i + 1) % len(ant.tour)]
                # 双向更新
                self.pheromone[from_city, to_city] += delta_pheromone
                self.pheromone[to_city, from_city] += delta_pheromone

    def optimize(self, verbose=True):
        """
        执行ACO优化求解TSP

        参数:
            verbose: 是否输出迭代信息

        返回:
            best_tour: 最佳路线
            best_length: 最佳路线长度
            history: 迭代历史
        """
        cfg = self.config

        # 记录历史
        history = {
            'best_length': [],
            'avg_length': []
        }

        # 全局最佳
        best_tour = None
        best_length = float('inf')

        for iteration in range(cfg.max_iterations):
            # 1. 所有蚂蚁构建路线
            ants = self._construct_solutions()

            # 2. 评估当前代最佳
            current_best_ant = min(ants, key=lambda a: a.tour_length)
            current_best_length = current_best_ant.tour_length

            # 更新全局最佳
            if current_best_length < best_length:
                best_length = current_best_length
                best_tour = current_best_ant.tour.copy()

            # 记录历史
            avg_length = np.mean([a.tour_length for a in ants])
            history['best_length'].append(best_length)
            history['avg_length'].append(avg_length)

            if verbose and iteration % 30 == 0:
                print(f"Iter {iteration:4d}: Best = {best_length:.2f}, "
                      f"Avg = {avg_length:.2f}, "
                      f"Best Tour = {best_tour[:5]}...")

            # 3. 更新信息素
            self._update_pheromone(ants)

        return best_tour, best_length, history


# ============================================================
# 可视化辅助函数
# ============================================================

def plot_tsp_tour(cities, tour, title="TSP Solution"):
    """
    可视化TSP路线

    参数:
        cities: 城市坐标列表
        tour: 访问顺序
        title: 图表标题
    """
    try:
        import matplotlib.pyplot as plt

        # 绘制城市点
        x = [c[0] for c in cities]
        y = [c[1] for c in cities]
        plt.scatter(x, y, c='red', s=100, zorder=5)

        # 绘制路线
        tour_cities = [cities[tour[i]] for i in range(len(tour))]
        tour_cities.append(tour_cities[0])  # 闭合回路

        tour_x = [c[0] for c in tour_cities]
        tour_y = [c[1] for c in tour_cities]

        plt.plot(tour_x, tour_y, 'b-', linewidth=2)
        plt.title(title)
        plt.xlabel('X')
        plt.ylabel('Y')
        plt.grid(True)
        plt.show()
    except ImportError:
        print("(matplotlib not available, skipping plot)")


# ============================================================
# 程序入口:测试ACO
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("蚁群优化算法 (ACO) 测试 - TSP求解")
    print("=" * 60)

    # 创建TSP问题:20个随机城市
    print("\n【测试1】20个城市TSP")
    rng = np.random.default_rng(42)
    cities_20 = rng.uniform(0, 100, (20, 2)).tolist()

    tsp = TSPLib(cities_20)
    print(f"城市数量: {tsp.n_cities}")

    # 配置ACO
    config = ACOConfig()
    config.num_ants = 30
    config.max_iterations = 200
    config.alpha = 1.0
    config.beta = 2.0
    config.rho = 0.5

    # 运行ACO
    aco = ACO(tsp, config)
    best_tour, best_length, history = aco.optimize(verbose=True)

    print(f"\n最优路线长度: {best_length:.2f}")
    print(f"最优路线: {best_tour}")

    # 绘制结果
    print("\n绘制TSP路线...")
    plot_tsp_tour(cities_20, best_tour, f"ACO Solution: Length={best_length:.2f}")

    # 对比贪心算法
    print("\n" + "-" * 60)
    print("\n【测试2】对比最近邻贪心算法")

    def greedy_tsp(cities):
        """最近邻贪心算法"""
        n = len(cities)
        visited = [False] * n
        tour = [0]
        visited[0] = True

        current = 0
        for _ in range(n - 1):
            # 找最近的未访问城市
            distances = []
            for j in range(n):
                if not visited[j]:
                    d = np.sqrt((cities[current][0] - cities[j][0]) ** 2 +
                                (cities[current][1] - cities[j][1]) ** 2)
                    distances.append((j, d))
            distances.sort(key=lambda x: x[1])
            next_city = distances[0][0]
            tour.append(next_city)
            visited[next_city] = True
            current = next_city

        # 计算总长度
        total = sum(np.sqrt((cities[tour[i]][0] - cities[tour[(i+1) % n]][0]) ** 2 +
                           (cities[tour[i]][1] - cities[tour[(i+1) % n]][1]) ** 2)
                    for i in range(n))
        return tour, total

    greedy_tour, greedy_length = greedy_tsp(cities_20)
    print(f"贪心算法路线长度: {greedy_length:.2f}")
    print(f"ACO算法路线长度:  {best_length:.2f}")
    print(f"改进比例: {(greedy_length - best_length) / greedy_length * 100:.2f}%")

    print("\n" + "=" * 60)
    print("ACO算法测试完成")
    print("=" * 60)