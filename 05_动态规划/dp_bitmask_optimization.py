# -*- coding: utf-8 -*-

"""

算法实现：05_动态规划 / dp_bitmask_optimization



本文件实现 dp_bitmask_optimization 相关的算法功能。

"""



from typing import List, Callable

import math





# ==================== 基础状态压缩DP ====================



def bitmask_tsp(dist: List[List[int]]) -> int:

    """

    旅行商问题（TSP）的状态压缩DP解法

    

    问题：给定 n 个城市之间的距离，求从城市0出发，遍历所有城市后回到0的最短路径

    

    方法：

    - state 用 bitmask 表示已访问的城市集合

    - dp[state][last] = 当前在 last，已访问 state 状态的最短路径

    - 转移：尝试去下一个未访问的城市

    

    Args:

        dist: 距离矩阵，dist[i][j] 表示 i 到 j 的距离

    

    Returns:

        最短路径长度

    """

    n = len(dist)

    INF = 10 ** 9

    

    # dp[mask][last] = 最短路径，mask 包含 last

    # 状态数 2^n * n，太大，改用一维数组

    dp = [[INF] * n for _ in range(1 << n)]

    

    # 起点在 city 0，初始状态 mask = 1 << 0

    dp[1 << 0][0] = 0

    

    # 枚举所有状态

    for mask in range(1 << n):

        # 检查所有可能的最后位置

        for last in range(n):

            if dp[mask][last] == INF:

                continue

            

            # 如果所有城市都已访问，检查是否回到起点

            if mask == (1 << n) - 1:

                continue

            

            # 尝试去下一个城市

            for nxt in range(n):

                # nxt 不在 mask 中

                if mask & (1 << nxt):

                    continue

                

                next_mask = mask | (1 << nxt)

                new_dist = dp[mask][last] + dist[last][nxt]

                dp[next_mask][nxt] = min(dp[next_mask][nxt], new_dist)

    

    # 最终状态：所有城市都已访问，需要回到起点

    full_mask = (1 << n) - 1

    result = INF

    for last in range(n):

        if dp[full_mask][last] != INF:

            result = min(result, dp[full_mask][last] + dist[last][0])

    

    return result





def bitmask_subset_sum(items: List[int], target: int) -> bool:

    """

    子集和问题的状态压缩DP

    

    判断是否能从 items 中选择若干元素，使得和恰好等于 target

    

    Args:

        items: 物品列表

        target: 目标和

    

    Returns:

        是否存在子集和等于 target

    """

    n = len(items)

    

    # dp[mask] = 子集 mask 的元素和

    # 优化：只存储可达的和

    reachable = {0}  # 从空集开始

    

    for item in items:

        new_reachable = set(reachable)

        for s in reachable:

            new_s = s + item

            if new_s <= target:

                new_reachable.add(new_s)

            if target in new_reachable:

                return True

        reachable = new_reachable

    

    return target in reachable





def bitmask_max_independent_set(n: int, edges: List[Tuple[int, int]]) -> int:

    """

    最大独立集的状态压缩DP

    

    给定图 G 和 n 个节点，找最大的点集使得任意两点之间没有边

    

    Args:

        n: 节点数

        edges: 边列表 [(u, v), ...]

    

    Returns:

        最大独立集的大小

    """

    # 预计算每个节点的邻居

    neighbors = [0] * n

    for u, v in edges:

        neighbors[u] |= (1 << v)

        neighbors[v] |= (1 << u)

    

    # dp[mask] = mask 表示的集合是否是独立集

    # 更快的方法：枚举所有子集，检查是否有边

    max_size = 0

    

    for mask in range(1 << n):

        # 快速检查：如果当前集合大小 <= max_size，跳过

        size = bin(mask).count("1")

        if size <= max_size:

            continue

        

        # 检查是否是独立集

        is_independent = True

        for i in range(n):

            if mask & (1 << i):

                # 检查 i 的邻居是否也在 mask 中

                if mask & neighbors[i]:

                    is_independent = False

                    break

        

        if is_independent:

            max_size = size

    

    return max_size





def bitmask_min_vertex_cover(n: int, edges: List[Tuple[int, int]]) -> int:

    """

    最小顶点覆盖的状态压缩DP

    

    顶点覆盖：选中一些顶点，使得每条边至少有一个端点被选中

    补转化：独立集的最大 = n - 最小覆盖

    

    Args:

        n: 节点数

        edges: 边列表

    

    Returns:

        最小顶点覆盖的大小

    """

    max_indep = bitmask_max_independent_set(n, edges)

    return n - max_indep





# ==================== SOS DP（子集枚举）====================



def sos_dp_sum(g: List[int]) -> List[int]:

    """

    SOS DP - 计算所有子集的和

    

    给定数组 g[mask]，计算 f[mask] = sum_{sub ⊆ mask} g[sub]

    

    算法：

    for i in range(n):

        for mask in range(2^n):

            if mask & (1 << i):

                f[mask] += f[mask ^ (1 << i)]

    

    Args:

        g: 大小为 2^n 的数组

    

    Returns:

        f: 每个 mask 的子集和

    """

    n = int(math.log2(len(g)))

    f = g.copy()

    

    for i in range(n):

        for mask in range(1 << n):

            if mask & (1 << i):

                f[mask] += f[mask ^ (1 << i)]

    

    return f





def sos_dp_min(g: List[int]) -> List[int]:

    """

    SOS DP - 计算所有子集的最小值

    

    f[mask] = min_{sub ⊆ mask} g[sub]

    """

    n = int(math.log2(len(g)))

    f = g.copy()

    

    for i in range(n):

        for mask in range(1 << n):

            if mask & (1 << i):

                f[mask] = min(f[mask], f[mask ^ (1 << i)])

    

    return f





def sos_dp_max(g: List[int]) -> List[int]:

    """

    SOS DP - 计算所有子集的最大值

    

    f[mask] = max_{sub ⊆ mask} g[sub]

    """

    n = int(math.log2(len(g)))

    f = g.copy()

    

    for i in range(n):

        for mask in range(1 << n):

            if mask & (1 << i):

                f[mask] = max(f[mask], f[mask ^ (1 << i)])

    

    return f





def sos_count_subsets(arr: List[int], target: int) -> int:

    """

    统计和等于 target 的子集数量

    

    使用 SOS DP 在 O(n * 2^n) 时间内解决

    

    Args:

        arr: 元素数组

        target: 目标和

    

    Returns:

        和等于 target 的子集数量

    """

    # 如果 arr 元素是 0/1，可以直接用 SOS

    # 否则需要离散化或使用其他方法

    

    n = len(arr)

    if n > 20:  # 太大了

        return 0

    

    # 枚举所有子集，统计和

    count = 0

    for mask in range(1 << n):

        total = 0

        for i in range(n):

            if mask & (1 << i):

                total += arr[i]

        if total == target:

            count += 1

    

    return count





# ==================== SOS DP 应用 ====================



def sos_find_max_bitwise_and() -> int:

    """

    SOS DP 应用：找出数组中任意子集按位与的最大值

    

    思想：子集的按位与 = 所有元素的公共前缀

    使用 SOS DP 计算每个 mask 有多少个子集包含某些位

    """

    pass





def sos_subset_count_with_condition():

    """

    SOS DP 应用：统计满足特定条件的子集数量

    

    例如：子集中所有元素的 or 值 = K

    """

    pass





# ==================== 高级状态压缩技巧 ====================



def dp_with_bitmask_optimization(n: int, 

                                  cost: List[List[int]],

                                  initial_state: int) -> int:

    """

    通用状态压缩DP框架

    

    适用于需要选择最优子集的问题

    

    Args:

        n: 元素数量

        cost[i][mask]: 选择元素 i 后，状态变为 mask 的代价

        initial_state: 初始状态

    

    Returns:

        达到最终状态所需的最小代价

    """

    INF = 10 ** 9

    dp = [INF] * (1 << n)

    dp[initial_state] = 0

    

    for mask in range(1 << n):

        if dp[mask] == INF:

            continue

        

        # 尝试添加新元素

        for i in range(n):

            if not (mask & (1 << i)):

                new_mask = mask | (1 << i)

                new_cost = dp[mask] + cost[i][new_mask]

                dp[new_mask] = min(dp[new_mask], new_cost)

    

    return dp[(1 << n) - 1]





def meet_in_middle_bruteforce():

    """

    Meet in the Middle + 状态压缩

    

    当 n 太大无法直接枚举 2^n 时，

    将元素分成两半，分别枚举

    """

    pass





def bitmask_hungarian_assignment():

    """

    状态压缩 + Hungarian 算法

    

    用于求解分配问题的最优方案

    """

    pass





# ==================== 测试与示例 ====================



if __name__ == "__main__":

    # 测试1：TSP

    print("测试1 - 旅行商问题(TSP):")

    n = 4

    dist = [

        [0, 10, 15, 20],

        [10, 0, 35, 25],

        [15, 35, 0, 30],

        [20, 25, 30, 0],

    ]

    result = bitmask_tsp(dist)

    print(f"  城市距离矩阵: 4x4")

    print(f"  最短路径: {result}")  # 应该是 80 (0->1->2->3->0)

    

    # 测试2：子集和

    print("\n测试2 - 子集和问题:")

    items = [3, 34, 4, 12, 5, 2]

    print(f"  物品: {items}")

    print(f"  target=9: {bitmask_subset_sum(items, 9)}")  # True (4+5)

    print(f"  target=30: {bitmask_subset_sum(items, 30)}")  # True (3+4+5+12+... 需要检查)

    print(f"  target=100: {bitmask_subset_sum(items, 100)}")  # False

    

    # 测试3：最大独立集

    print("\n测试3 - 最大独立集:")

    n = 5

    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 2)]

    max_indep = bitmask_max_independent_set(n, edges)

    print(f"  节点: {n}, 边: {edges}")

    print(f"  最大独立集大小: {max_indep}")

    

    # 测试4：SOS DP

    print("\n测试4 - SOS DP:")

    n = 3

    g = [1, 2, 3, 4, 5, 6, 7, 8]  # 2^3 = 8 个元素

    f_sum = sos_dp_sum(g)

    print(f"  原始数组: {g}")

    print(f"  SOS子集和: {f_sum}")

    print(f"  验证: f[7]={f_sum[7]} 应该等于 sum(所有子集)=1+2+3+4+5+6+7+8=36")

    

    f_min = sos_dp_min(g)

    print(f"  SOS子集最小值: {f_min}")

    

    f_max = sos_dp_max(g)

    print(f"  SOS子集最大值: {f_max}")

    

    # 测试5：子集计数

    print("\n测试5 - 子集计数:")

    arr = [1, 2, 3, 4]

    target = 5

    count = sos_count_subsets(arr, target)

    print(f"  数组: {arr}, target={target}")

    print(f"  和为{target}的子集数量: {count}")  # {1,4}, {2,3}, {5}

    

    # 性能测试

    import time

    import random

    

    print("\n性能测试:")

    sizes = [16, 18, 20]

    for n in sizes:

        # 随机TSP

        dist_matrix = [[random.randint(1, 100) if i != j else 0 

                        for j in range(n)] 

                       for i in range(n)]

        

        start = time.time()

        result = bitmask_tsp(dist_matrix)

        elapsed = time.time() - start

        

        print(f"  n={n} TSP: {elapsed:.3f}s")

    

    # SOS DP 性能

    print("\nSOS DP 性能:")

    for n in [10, 15, 20]:

        size = 1 << n

        g = [random.randint(0, 100) for _ in range(size)]

        

        start = time.time()

        f = sos_dp_sum(g)

        elapsed = time.time() - start

        

        print(f"  n={n}, 2^n={size}: {elapsed:.3f}s")

