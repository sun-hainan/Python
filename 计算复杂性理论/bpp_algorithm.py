# -*- coding: utf-8 -*-
"""
算法实现：计算复杂性理论 / bpp_algorithm

本文件实现 bpp_algorithm 相关的算法功能。
"""

import random
import math
from typing import Callable, Any, List, Tuple


class BPPAlgorithm:
    """
    BPP算法基类
    """
    
    def __init__(self, error_probability: float = 1/3):
        """
        初始化
        
        参数:
            error_probability: 目标错误概率
        """
        self.error_probability = error_probability
    
    def amplify(self, num_iterations: int) -> float:
        """
        计算放大后的错误概率
        
        如果一次错误概率为p，则k次独立运行后：
        P(至少一次错误) = 1 - (1-p)^k
        
        参数:
            num_iterations: 运行次数
        
        返回:
            放大后的错误概率
        """
        p = self.error_probability
        return 1 - (1 - p) ** num_iterations
    
    def required_iterations(self, target_error: float) -> int:
        """
        计算达到目标错误概率需要的迭代次数
        
        参数:
            target_error: 目标错误概率
        
        返回:
            需要的迭代次数
        """
        p = self.error_probability
        # 1 - (1-p)^k <= target_error
        # (1-p)^k >= 1 - target_error
        # k >= log(1-target_error) / log(1-p)
        k = math.log(target_error) / math.log(1 - p)
        return math.ceil(k)


def miller_rabin_test(n: int, iterations: int = 5) -> Tuple[bool, str]:
    """
    Miller-Rabin素数性测试
    
    这是一个BPP算法：运行多次，错误概率可控制在任意小
    
    参数:
        n: 要测试的数
        iterations: 测试迭代次数
    
    返回:
        (可能是素数, 判定原因)
    """
    if n < 2:
        return False, "小于2"
    
    if n == 2 or n == 3:
        return True, "小素数"
    
    if n % 2 == 0:
        return False, "偶数"
    
    # 分解 n-1 = 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    
    # 进行 iterations 次测试
    for _ in range(iterations):
        a = random.randint(2, n - 2)
        
        # 计算 a^d mod n
        x = pow(a, d, n)
        
        if x == 1 or x == n - 1:
            continue
        
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False, "Miller-Rabin失败"
    
    return True, "通过Miller-Rabin测试"


def polynomial_identity_check(poly_coeffs1: List[int], 
                            poly_coeffs2: List[int],
                            num_vars: int,
                            iterations: int = 10) -> bool:
    """
    多项式恒等检验
    
    给定两个多变量多项式，检验它们是否相等
    
    使用Schwartz-Zippel引理：
    P(随机赋值使多项式为0 | 多项式非零) <= d/|S|
    
    参数:
        poly_coeffs1: 第一个多项式系数
        poly_coeffs2: 第二个多项式系数
        num_vars: 变量数
        iterations: 迭代次数
    
    返回:
        是否可能相等
    """
    # 简化为单变量情况
    # 检查两个多项式的系数差
    diff = [a - b for a, b in zip(poly_coeffs1, poly_coeffs2)]
    
    # 选择一个大的有限域
    p = 10**9 + 7  # 大素数
    
    for _ in range(iterations):
        # 随机赋值
        values = [random.randint(0, p - 1) for _ in range(num_vars)]
        
        # 评估（简化版本：单变量）
        val1 = sum(c * values[0] ** i for i, c in enumerate(poly_coeffs1))
        val2 = sum(c * values[0] ** i for i, c in enumerate(poly_coeffs2))
        
        if (val1 - val2) % p != 0:
            return False
    
    return True


def graph_connectivity(adjacency_matrix: List[List[int]], 
                       iterations: int = 10) -> Tuple[bool, str]:
    """
    图连通性测试（使用随机游走）
    
    参数:
        adjacency_matrix: 邻接矩阵
        iterations: 迭代次数
    
    返回:
        (是否连通, 判定原因)
    """
    n = len(adjacency_matrix)
    
    if n <= 1:
        return True, "单节点"
    
    # 随机选择一个起点
    start = random.randint(0, n - 1)
    
    # 随机游走
    visited = set()
    current = start
    
    for _ in range(n * n):  # n²步足够访问所有可达节点
        visited.add(current)
        
        # 找到邻居
        neighbors = [j for j in range(n) if adjacency_matrix[current][j]]
        
        if not neighbors:
            # 孤立节点
            break
        
        current = random.choice(neighbors)
    
    # 检查是否访问了所有节点
    if len(visited) == n:
        return True, "所有节点可达"
    else:
        return False, f"只访问了{len(visited)}个节点"


def random_polynomial_time_verifier(spec: dict) -> dict:
    """
    BPP验证器模板
    
    参数:
        spec: 验证器规格
    
    返回:
        验证结果
    """
    verifier = {
        'type': 'BPP Verifier',
        'running_time': 'O(poly(n))',
        'error_probability': spec.get('error_prob', 1/3),
        'amplifiable': True,
        'description': 'BPP验证器使用随机比特进行验证'
    }
    
    return verifier


class RandomWalk:
    """
    随机游走模拟器
    """
    
    def __init__(self, graph: List[List[int]]):
        """
        初始化
        
        参数:
            graph: 图的邻接表
        """
        self.graph = graph
        self.n = len(graph)
    
    def walk(self, start: int, steps: int) -> List[int]:
        """
        执行随机游走
        
        参数:
            start: 起始节点
            steps: 步数
        
        返回:
            访问的节点序列
        """
        path = [start]
        current = start
        
        for _ in range(steps):
            neighbors = self.graph[current]
            if not neighbors:
                break
            current = random.choice(neighbors)
            path.append(current)
        
        return path
    
    def hitting_time(self, start: int, target: int, max_steps: int = 10000) -> int:
        """
        计算从start到target的期望 hitting time
        
        参数:
            start: 起始节点
            target: 目标节点
            max_steps: 最大步数
        
        返回:
            到达目标的步数（如果超时返回-1）
        """
        current = start
        steps = 0
        
        while steps < max_steps:
            if current == target:
                return steps
            
            neighbors = self.graph[current]
            if not neighbors:
                return -1
            
            current = random.choice(neighbors)
            steps += 1
        
        return -1


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：Miller-Rabin素数性测试
    print("=" * 50)
    print("测试1: Miller-Rabin素数性测试")
    print("=" * 50)
    
    test_numbers = [2, 3, 17, 100, 127, 1000, 104729, 2305843009213693951]
    
    for n in test_numbers:
        is_prime, reason = miller_rabin_test(n)
        print(f"  {n}: {'可能是素数' if is_prime else '不是素数'} ({reason})")
    
    # 测试用例2：错误概率放大
    print("\n" + "=" * 50)
    print("测试2: 错误概率放大")
    print("=" * 50)
    
    bpp = BPPAlgorithm(error_probability=1/3)
    
    print(f"原始错误概率: {bpp.error_probability}")
    
    for target_error in [0.1, 0.01, 0.001, 1e-6]:
        required = bpp.required_iterations(target_error)
        actual_error = bpp.amplify(required)
        print(f"  目标错误率 {target_error}: 需要{required}次迭代, 实际错误率≈{actual_error}")
    
    # 测试用例3：图连通性测试
    print("\n" + "=" * 50)
    print("测试3: 图连通性测试")
    print("=" * 50)
    
    # 连通图
    connected_graph = [
        [0, 1, 1, 0],
        [1, 0, 1, 1],
        [1, 1, 0, 1],
        [0, 1, 1, 0]
    ]
    
    # 非连通图
    disconnected_graph = [
        [0, 1, 0, 0],
        [1, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 0]
    ]
    
    for name, graph in [("连通图", connected_graph), ("非连通图", disconnected_graph)]:
        is_connected, reason = graph_connectivity(graph)
        print(f"  {name}: {'连通' if is_connected else '不连通'} ({reason})")
    
    # 测试用例4：随机游走
    print("\n" + "=" * 50)
    print("测试4: 随机游走")
    print("=" * 50)
    
    graph = [
        [1, 2],      # 节点0连接1,2
        [0, 2, 3],   # 节点1连接0,2,3
        [0, 1],      # 节点2连接0,1
        [1]          # 节点3连接1
    ]
    
    walker = RandomWalk(graph)
    
    print("执行5次随机游走（从节点0开始，10步）:")
    for i in range(5):
        path = walker.walk(0, 10)
        print(f"  第{i+1}次: {' -> '.join(map(str, path))}")
    
    # 测试用例5：多项式恒等检验
    print("\n" + "=" * 50)
    print("测试5: 多项式恒等检验")
    print("=" * 50)
    
    # (x + 1)² = x² + 2x + 1
    poly1 = [1, 2, 1]  # x² + 2x + 1
    poly2 = [1, 2, 1]  # x² + 2x + 1
    
    result = polynomial_identity_check(poly1, poly2, num_vars=1, iterations=20)
    print(f"  (x+1)² vs x²+2x+1: {'可能相等' if result else '不相等'}")
    
    poly3 = [1, 0, 1]  # x² + 1
    result = polynomial_identity_check(poly1, poly3, num_vars=1, iterations=20)
    print(f"  (x+1)² vs x²+1: {'可能相等' if result else '不相等'}")
    
    # 测试用例6：BPP算法分析
    print("\n" + "=" * 50)
    print("测试6: BPP算法分析")
    print("=" * 50)
    
    algorithms = [
        {'name': '素数性测试', 'error': 1/4, 'iterations': 5},
        {'name': '多边形恒等', 'error': 1/3, 'iterations': 10},
        {'name': '图连通性', 'error': 1/3, 'iterations': 10},
    ]
    
    for algo in algorithms:
        bpp = BPPAlgorithm(error_probability=algo['error'])
        new_error = bpp.amplify(algo['iterations'])
        print(f"  {algo['name']}:")
        print(f"    原始错误率: {algo['error']:.4f}")
        print(f"    放大后错误率: {new_error:.6f}")
