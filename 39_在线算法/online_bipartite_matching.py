# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / online_bipartite_matching



本文件实现 online_bipartite_matching 相关的算法功能。

"""



import random

from collections import defaultdict, deque





class OnlineBipartiteMatcher:

    """在线二分图匹配器"""



    def __init__(self, left_vertices, right_vertices=None):

        """

        初始化匹配器

        

        参数:

            left_vertices: 左侧顶点列表（如服务器）

            right_vertices: 右侧顶点列表（如请求），可选

        """

        self.left_vertices = set(left_vertices)

        # 右侧顶点可以是动态的

        if right_vertices:

            self.right_vertices = set(right_vertices)

        else:

            self.right_vertices = set()

        

        # 匹配结果：{左侧: 右侧}

        self.match_left = {}

        # 反向匹配：{右侧: 左侧}

        self.match_right = {}

        # 未匹配的右侧顶点队列

        self.pending_right = deque()

        # 统计

        self.matches = 0

        self.total_arrivals = 0



    def add_left_vertex(self, v):

        """添加左侧顶点"""

        self.left_vertices.add(v)



    def add_right_vertex(self, v):

        """添加右侧顶点"""

        self.right_vertices.add(v)



    def _is_available(self, left_v):

        """检查左侧顶点是否可用"""

        return left_v not in self.match_left



    def _has_match(self, right_v):

        """检查右侧顶点是否已匹配"""

        return right_v in self.match_right



    def greedy_match(self, right_v, score_func=None):

        """

        贪婪匹配

        

        参数:

            right_v: 右侧顶点

            score_func: 评分函数 (left, right) -> score，可选

        返回:

            matched: 是否成功匹配

        """

        self.total_arrivals += 1

        

        # 获取所有可用的左侧顶点

        available = [v for v in self.left_vertices if self._is_available(v)]

        

        if not available:

            # 没有可用顶点，加入待处理队列

            self.pending_right.append(right_v)

            return False

        

        # 如果有评分函数，选择分数最高的

        if score_func:

            best = max(available, key=lambda l: score_func(l, right_v))

        else:

            best = random.choice(available)

        

        # 执行匹配

        self.match_left[best] = right_v

        self.match_right[right_v] = best

        self.matches += 1

        return True



    def ranked_match(self, right_v, ranking):

        """

        排名匹配

        

        参数:

            right_v: 右侧顶点

            ranking: 排名函数 (left_v) -> rank，越小越优先

        返回:

            matched: 是否成功匹配

        """

        self.total_arrivals += 1

        

        # 按排名排序可用顶点

        available = [v for v in self.left_vertices if self._is_available(v)]

        

        if not available:

            self.pending_right.append(right_v)

            return False

        

        # 选择排名最高的（数字最小的）

        best = min(available, key=ranking)

        

        self.match_left[best] = right_v

        self.match_right[right_v] = best

        self.matches += 1

        return True



    def process_pending(self):

        """

        处理待处理的右侧顶点

        

        当新的左侧顶点可用时调用

        """

        matched = 0

        while self.pending_right:

            right_v = self.pending_right.popleft()

            # 尝试重新匹配

            available = [v for v in self.left_vertices if self._is_available(v)]

            if available:

                best = random.choice(available)

                self.match_left[best] = right_v

                self.match_right[right_v] = best

                matched += 1

                self.matches += 1

        return matched



    def get_match(self, left_v):

        """获取左侧顶点的匹配"""

        return self.match_left.get(left_v)



    def is_matched(self, v):

        """检查顶点是否已匹配"""

        return v in self.match_left or v in self.match_right



    def get_stats(self):

        """获取统计信息"""

        return {

            'matches': self.matches,

            'arrivals': self.total_arrivals,

            'match_rate': self.matches / self.total_arrivals if self.total_arrivals > 0 else 0,

            'pending': len(self.pending_right)

        }





class OnlineBipartiteMatchingWithEdgeWeights:

    """带权重的在线二分图匹配"""



    def __init__(self, left_vertices):

        self.left_vertices = set(left_vertices)

        self.match_left = {}

        self.match_right = {}

        self.matches = 0

        self.total_weight = 0

        self.total_arrivals = 0



    def greedy_match_weighted(self, right_v, edge_weights):

        """

        带权重的贪婪匹配

        

        参数:

            right_v: 右侧顶点

            edge_weights: {左侧: 权重} 字典

        返回:

            matched: 是否成功匹配

        """

        self.total_arrivals += 1

        

        # 获取可用的左侧顶点及其权重

        available = {l: edge_weights.get(l, 0) 

                     for l in self.left_vertices 

                     if l not in self.match_left}

        

        if not available:

            return False

        

        # 选择权重最高的

        best = max(available, key=available.get)

        weight = available[best]

        

        self.match_left[best] = right_v

        self.match_right[right_v] = best

        self.matches += 1

        self.total_weight += weight

        return True



    def get_stats(self):

        total = self.total_arrivals

        return {

            'matches': self.matches,

            'arrivals': total,

            'match_rate': self.matches / total if total > 0 else 0,

            'total_weight': self.total_weight,

            'avg_weight': self.total_weight / self.matches if self.matches > 0 else 0

        }





class RandomizedMatcher:

    """随机化在线匹配"""



    def __init__(self, left_vertices, seed=None):

        self.left_vertices = set(left_vertices)

        self.match_left = {}

        self.match_right = {}

        self.matches = 0

        self.total_arrivals = 0

        self.rng = random.Random(seed)



    def random_match(self, right_v):

        """随机匹配"""

        self.total_arrivals += 1

        

        available = [v for v in self.left_vertices if v not in self.match_left]

        

        if not available:

            return False

        

        best = self.rng.choice(available)

        self.match_left[best] = right_v

        self.match_right[right_v] = best

        self.matches += 1

        return True



    def get_stats(self):

        total = self.total_arrivals

        return {

            'matches': self.matches,

            'arrivals': total,

            'match_rate': self.matches / total if total > 0 else 0

        }





if __name__ == "__main__":

    print("=== 在线二分图匹配测试 ===\n")



    # 简单示例

    print("--- 简单贪婪匹配 ---")

    servers = ['S1', 'S2', 'S3']

    matcher = OnlineBipartiteMatcher(servers)

    

    requests = ['R1', 'R2', 'R3', 'R4', 'R5']

    for req in requests:

        matched = matcher.greedy_match(req)

        print(f"  请求 {req}: {'匹配' if matched else '等待'}")

    

    stats = matcher.get_stats()

    print(f"  统计: 匹配={stats['matches']}, 到达={stats['arrivals']}, "

          f"匹配率={stats['match_rate']:.1%}, 待处理={stats['pending']}")



    # 带排名的匹配

    print("\n--- 带排名匹配 ---")

    servers2 = ['S1', 'S2', 'S3']

    matcher2 = OnlineBipartiteMatcher(servers2)

    

    # 服务器排名（数字越小越好）

    def server_rank(s):

        ranks = {'S1': 1, 'S2': 2, 'S3': 3}

        return ranks.get(s, 999)

    

    requests = ['R1', 'R2', 'R3']

    for req in requests:

        matched = matcher2.ranked_match(req, server_rank)

        print(f"  请求 {req}: {'匹配' if matched else '等待'}")

    

    print(f"  匹配结果: {matcher2.match_left}")



    # 带权重匹配

    print("\n--- 带权重匹配 ---")

    servers3 = ['S1', 'S2', 'S3']

    weighted_matcher = OnlineBipartiteMatchingWithEdgeWeights(servers3)

    

    requests = ['R1', 'R2', 'R3']

    for req in requests:

        # 随机生成权重

        weights = {s: random.randint(1, 10) for s in servers3}

        matched = weighted_matcher.greedy_match_weighted(req, weights)

        print(f"  请求 {req}: 权重={weights}, {'匹配' if matched else '等待'}")

    

    stats = weighted_matcher.get_stats()

    print(f"  统计: 总权重={stats['total_weight']}, "

          f"平均权重={stats['avg_weight']:.1f}")



    # 动态添加服务器

    print("\n--- 动态添加服务器 ---")

    matcher3 = OnlineBipartiteMatcher(['S1', 'S2'])

    

    requests = ['R1', 'R2', 'R3']

    for req in requests:

        matcher3.greedy_match(req)

    

    print(f"  初始匹配: {matcher3.match_left}")

    print(f"  匹配率: {matcher3.get_stats()['match_rate']:.1%}")

    

    # 添加新服务器

    matcher3.add_left_vertex('S3')

    matched = matcher3.process_pending()

    print(f"  添加 S3 后重新匹配: {matched} 个")

    print(f"  最终匹配: {matcher3.match_left}")

    print(f"  匹配率: {matcher3.get_stats()['match_rate']:.1%}")



    # 竞争分析

    print("\n--- 竞争分析 ---")

    

    def run_simulation(algorithm, requests, servers):

        """运行模拟"""

        if algorithm == 'greedy':

            m = OnlineBipartiteMatcher(servers)

            for r in requests:

                m.greedy_match(r)

        elif algorithm == 'random':

            m = RandomizedMatcher(servers)

            for r in requests:

                m.random_match(r)

        

        return m.get_stats()['matches']

    

    # 离线最优（需要知道所有请求）

    def offline_optimal(requests, servers):

        """离线最优匹配"""

        available = list(servers)

        matches = 0

        for r in requests:

            if available:

                available.pop(0)

                matches += 1

        return matches

    

    requests = list(range(100))

    servers = list(range(10))

    

    opt = offline_optimal(requests, servers)

    greedy = run_simulation('greedy', requests, servers)

    random_sim = run_simulation('random', requests, servers)

    

    print(f"离线最优: {opt}")

    print(f"贪婪算法: {greedy} (竞争比 {greedy/opt:.2%})")

    print(f"随机算法: {random_sim} (竞争比 {random_sim/opt:.2%})")

