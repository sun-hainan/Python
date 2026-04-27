# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / online_bipartite_matching



本文件实现 online_bipartite_matching 相关的算法功能。

"""



import random

from collections import defaultdict

from typing import List, Dict, Tuple, Set, Optional

from dataclasses import dataclass





@dataclass

class BipartiteGraph:

    """二分图"""

    left_vertices: Set[str]  # 左侧顶点

    right_vertices: Set[str]  # 右侧顶点

    edges: Dict[str, List[str]]  # 左侧顶点 -> 右侧邻居





class OnlineBipartiteMatching:

    """

    在线二分图匹配基类

    """

    

    def __init__(self, left_vertices: Set[str]):

        self.left_vertices = left_vertices

        self.matched: Dict[str, str] = {}  # left -> right

        self.right_matched: Dict[str, str] = {}  # right -> left

        self.total_matches = 0

    

    def match(self, left_vertex: str, right_candidates: List[str]) -> Optional[str]:

        """

        尝试匹配

        

        Args:

            left_vertex: 左侧顶点

            right_candidates: 可用的右侧顶点列表

        

        Returns:

            匹配的右侧顶点或None

        """

        raise NotImplementedError

    

    def get_matching(self) -> Dict[str, str]:

        """获取当前匹配"""

        return self.matched.copy()

    

    def get_matching_size(self) -> int:

        """获取匹配大小"""

        return self.total_matches





class GreedyMatching(OnlineBipartiteMatching):

    """

    贪心匹配

    

    策略：尽可能匹配（不考虑最优性）

    """

    

    def match(self, left_vertex: str, right_candidates: List[str]) -> Optional[str]:

        """贪心匹配"""

        if left_vertex in self.matched:

            return self.matched[left_vertex]

        

        # 选择第一个未匹配的右侧顶点

        for right in right_candidates:

            if right not in self.right_matched:

                self.matched[left_vertex] = right

                self.right_matched[right] = left_vertex

                self.total_matches += 1

                return right

        

        return None





class RankingMatching(OnlineBipartiteMatching):

    """

    Ranking算法（ Karp, Kleinberg 等 1990）

    

    核心思想：

    - 预先随机排列右侧顶点

    - 按排列顺序决定优先级

    - 可以达到 O(log n) 竞争比

    

    是已知最好的确定性在线算法之一

    """

    

    def __init__(self, left_vertices: Set[str]):

        super().__init__(left_vertices)

        self.right_order: List[str] = []  # 右侧顶点排列

        self.right_rank: Dict[str, int] = {}  # 右侧顶点的排名

    

    def set_right_vertices(self, right_vertices: Set[str]):

        """设置右侧顶点并生成随机排列"""

        self.right_vertices = right_vertices

        self.right_order = list(right_vertices)

        random.shuffle(self.right_order)

        

        for i, r in enumerate(self.right_order):

            self.right_rank[r] = i

    

    def match(self, left_vertex: str, right_candidates: List[str]) -> Optional[str]:

        """Ranking匹配"""

        if left_vertex in self.matched:

            return self.matched[left_vertex]

        

        if not right_candidates:

            return None

        

        # 选择排名最高的（数值最小的）可用右侧顶点

        available = [r for r in right_candidates if r not in self.right_matched]

        

        if not available:

            return None

        

        # 选择排名最高的

        best = min(available, key=lambda r: self.right_rank.get(r, float('inf')))

        

        self.matched[left_vertex] = best

        self.right_matched[best] = left_vertex

        self.total_matches += 1

        

        return best





class WassersteinMatching(OnlineBipartiteMatching):

    """

    Wasserstein匹配（带顶点权重的在线匹配）

    

    使用哈希技术实现

    """

    

    def __init__(self, left_vertices: Set[str], seed: int = 42):

        super().__init__(left_vertices)

        self.seed = seed

        random.seed(seed)

        self.hashes: Dict[str, float] = {}

    

    def set_right_vertices(self, right_vertices: Set[str]):

        """设置右侧顶点并生成随机哈希"""

        self.right_vertices = right_vertices

        

        # 为每个右侧顶点分配随机哈希值

        for r in right_vertices:

            self.hashes[r] = random.random()

    

    def match(self, left_vertex: str, right_candidates: List[str]) -> Optional[str]:

        """基于哈希的匹配"""

        if left_vertex in self.matched:

            return self.matched[left_vertex]

        

        if not right_candidates:

            return None

        

        # 选择哈希值最大的

        best = max(right_candidates, key=lambda r: self.hashes.get(r, 0))

        

        if best in self.right_matched:

            return None

        

        self.matched[left_vertex] = best

        self.right_matched[best] = left_vertex

        self.total_matches += 1

        

        return best





class BudgetedMatching(OnlineBipartiteMatching):

    """

    带预算的在线匹配

    

    每次匹配消耗预算

    """

    

    def __init__(self, left_vertices: Set[str], budget: int):

        super().__init__(left_vertices)

        self.budget = budget

        self.used_budget = 0

    

    def match(self, left_vertex: str, right_candidates: List[str], 

              cost: int = 1) -> Optional[str]:

        """带预算检查的匹配"""

        if left_vertex in self.matched:

            return self.matched[left_vertex]

        

        if self.used_budget + cost > self.budget:

            return None

        

        # 贪心选择

        for right in right_candidates:

            if right not in self.right_matched:

                self.matched[left_vertex] = right

                self.right_matched[right] = left_vertex

                self.used_budget += cost

                self.total_matches += 1

                return right

        

        return None





def compute_optimal_matching(graph: BipartiteGraph) -> Dict[str, str]:

    """

    计算离线最优匹配（匈牙利算法简化版）

    

    Args:

        graph: 二分图

    

    Returns:

        最优匹配

    """

    # 使用简单贪心作为近似

    matched = {}

    right_used = set()

    

    for left in graph.left_vertices:

        for right in graph.edges.get(left, []):

            if right not in right_used:

                matched[left] = right

                right_used.add(right)

                break

    

    return matched





def simulate_online_matching():

    """模拟在线匹配"""

    print("=== 在线二分图匹配模拟 ===\n")

    

    # 创建二分图

    left_vertices = {'L1', 'L2', 'L3', 'L4', 'L5'}

    right_vertices = {'R1', 'R2', 'R3', 'R4'}

    

    edges = {

        'L1': ['R1', 'R2'],

        'L2': ['R2', 'R3'],

        'L3': ['R1', 'R3', 'R4'],

        'L4': ['R2', 'R4'],

        'L5': ['R1', 'R2', 'R3'],

    }

    

    graph = BipartiteGraph(left_vertices, right_vertices, edges)

    

    # 请求序列

    requests = [

        ('L1', ['R1', 'R2']),

        ('L2', ['R2', 'R3']),

        ('L3', ['R1', 'R3', 'R4']),

        ('L4', ['R2', 'R4']),

        ('L5', ['R1', 'R2', 'R3']),

        ('L1', ['R1', 'R2']),  # 重复请求

    ]

    

    print("请求序列:")

    for left, rights in requests:

        print(f"  {left}: {rights}")

    print()

    

    # 贪心算法

    greedy = GreedyMatching(left_vertices.copy())

    greedy_results = []

    

    for left, rights in requests:

        result = greedy.match(left, rights)

        greedy_results.append(result)

    

    print(f"贪心匹配: {greedy.get_matching()}")

    print(f"匹配数: {greedy.get_matching_size()}")

    

    # Ranking算法

    ranking = RankingMatching(left_vertices.copy())

    ranking.set_right_vertices(right_vertices)

    ranking_results = []

    

    for left, rights in requests:

        result = ranking.match(left, rights)

        ranking_results.append(result)

    

    print(f"\nRanking匹配: {ranking.get_matching()}")

    print(f"匹配数: {ranking.get_matching_size()}")





def analyze_competitive_ratio():

    """竞争比分析"""

    print("\n=== 竞争比分析 ===\n")

    

    print("竞争比定义:")

    print("  Online算法的竞争比 = ALG / OPT")

    print("  其中 OPT 是离线最优解")

    print()

    

    print("各算法竞争比:")

    print("| 算法           | 竞争比    | 备注           |")

    print("|----------------|-----------|----------------|")

    print("| 贪心           | O(n)      | 最差           |")

    print("| Ranking        | O(log n)  | 经典结果       |")

    print("| Wasserstein     | O(log n)  | 随机化         |")

    print("| 确定性Weighted | O(log n)  | 利用权重       |")

    print("| 随机化算法     | O(1)      | 某些假设下     |")

    

    print("\n关键结论:")

    print("  - Ranking算法是在线匹配的最佳确定性算法")

    print("  - 竞争比 O(log n) 在理论和实践上都接近最优")

    print("  - 随机化可以进一步改善竞争比")





def demo_hospital_分配():

    """

    医院实习生分配问题演示

    

    这是在线二分图匹配的经典应用

    """

    print("\n=== 医院实习生分配演示 ===\n")

    

    # 医院（右侧，有固定容量）

    hospitals = ['H1', 'H2', 'H3', 'H4']

    

    # 实习生在线到达时的偏好

    # 格式: (实习生, 愿意去的医院列表)

    intern_requests = [

        ('Intern_A', ['H1', 'H2']),

        ('Intern_B', ['H2', 'H3']),

        ('Intern_C', ['H1', 'H3', 'H4']),

        ('Intern_D', ['H2', 'H4']),

        ('Intern_E', ['H1', 'H2', 'H3']),

    ]

    

    print("实习生请求:")

    for intern, prefs in intern_requests:

        print(f"  {intern}: {prefs}")

    print()

    

    # Ranking匹配

    ranking = RankingMatching({'Intern_A', 'Intern_B', 'Intern_C', 'Intern_D', 'Intern_E'})

    ranking.set_right_vertices(set(hospitals))

    

    print("Ranking算法分配:")

    for intern, prefs in intern_requests:

        result = ranking.match(intern, prefs)

        print(f"  {intern} -> {result}")





def demo_ad_allocation():

    """

    在线广告投放演示

    """

    print("\n=== 在线广告投放演示 ===\n")

    

    # 广告位（右侧）

    ad_slots = [f'Slot_{i}' for i in range(5)]

    

    # 用户到达时的广告请求

    user_requests = [

        ('User_1', ['Slot_0', 'Slot_1']),

        ('User_2', ['Slot_1', 'Slot_2']),

        ('User_3', ['Slot_0', 'Slot_2', 'Slot_3']),

        ('User_4', ['Slot_2', 'Slot_3', 'Slot_4']),

        ('User_5', ['Slot_0', 'Slot_1', 'Slot_4']),

        ('User_6', ['Slot_1', 'Slot_3']),

    ]

    

    print("用户请求:")

    for user, slots in user_requests:

        print(f"  {user}: {slots}")

    print()

    

    # 贪心

    greedy = GreedyMatching({u for u, _ in user_requests})

    

    print("贪心算法分配:")

    for user, slots in user_requests:

        result = greedy.match(user, slots)

        print(f"  {user} -> {result}")

    

    print(f"\n总匹配: {greedy.get_matching_size()}")





if __name__ == "__main__":

    print("=" * 60)

    print("在线二分图匹配算法")

    print("=" * 60)

    

    # 模拟

    simulate_online_matching()

    

    # 竞争比分析

    analyze_competitive_ratio()

    

    # 应用场景

    demo_hospital_分配()

    demo_ad_allocation()

    

    print("\n" + "=" * 60)

    print("在线匹配的核心挑战:")

    print("=" * 60)

    print("""

1. 离线 vs 在线:

   - 离线：可以看全部图结构

   - 在线：只能看到当前请求

   

2. 竞争比分析:

   - 对比在线算法与离线最优

   - 越小越好

   

3. Ranking算法:

   - 随机排列右侧顶点

   - 选择排名最高的可用顶点

   - O(log n) 竞争比

   

4. 应用场景:

   - 在线广告投放

   - 医院实习生分配

   - 云计算资源调度

   - 搜索引擎竞价排名

""")

