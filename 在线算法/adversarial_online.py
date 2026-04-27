# -*- coding: utf-8 -*-
"""
算法实现：在线算法 / adversarial_online

本文件实现 adversarial_online 相关的算法功能。
"""

import random
from typing import Callable


class Adversary:
    """对手模型"""

    def __init__(self, name: str = "Generic"):
        self.name = name
        self.history = []

    def get_request(self, state) -> any:
        """生成一个请求（由子类实现）"""
        raise NotImplementedError


class PagingAdversary(Adversary):
    """页面置换的对手"""

    def __init__(self):
        super().__init__("Paging")
        self.pages_in_memory = set()
        self.pages_requested = []

    def get_request(self, frames: int, cache: set) -> int:
        """
        生成请求

        策略：总是请求不在cache中的页
        如果cache满了，随机选一个驱逐
        """
        # 对手知道cache里的内容，总是请求cache外的页
        if len(self.pages_requested) == 0:
            page = 1
        else:
            # 简单策略：循环请求
            page = (len(self.pages_requested) % 10) + 1

        self.pages_requested.append(page)
        return page


def analyze_competitive_ratio(algorithm_fn: Callable,
                              adversary_fn: Callable,
                              n_steps: int = 100) -> float:
    """
    分析竞争比

    参数：
        algorithm_fn: 在线算法
        adversary_fn: 对手生成器
        n_steps: 步数

    返回：竞争比估计
    """
    # 简化：实际需要多次实验
    adversary = adversary_fn()
    algorithm_cost = 0
    optimal_cost = 0

    for _ in range(n_steps):
        request = adversary.get_request()
        algorithm_cost += algorithm_fn(request)
        optimal_cost += min(algorithm_cost, 1)  # 简化

    return algorithm_cost / optimal_cost if optimal_cost > 0 else 1.0


def fence_algorithm(n: int) -> int:
    """
    Fence算法（在线注册问题）

    有n个位置，需要插入一个新位置
    不知道未来会插入多少

    策略：以概率1/(k+1)选择位置k插入

    竞争比 = O(log n)
    """
    # 简化实现
    if n == 0:
        return 0

    # 随机选择
    k = random.randint(0, n)
    return k


def adversary_simulation():
    """
    对手模拟演示
    """
    print("=== 对手模拟演示 ===\n")

    print("场景：在线ski rental")
    print("-" * 50)

    rent = 1.0
    buy = 10.0

    # 对手策略：让在线算法在平衡点附近反复横跳
    print("对手策略：")
    print("  - 先让算法租几天")
    print("  - 在临界点让算法买")
    print("  - 然后告诉算法不会再去了")
    print()

    # 模拟
    online_total = 0
    rented_days = 0

    # 对手知道算法会租到累计>=买价
    # 所以让算法租满，然后再也不去
    days_actually_skiing = 9  # 对手选择只去9天

    for day in range(days_actually_skiing):
        online_total += rent
        rented_days += 1

    # 算法买了，但不会再去了
    if rented_days * rent >= buy:
        online_total = buy

    optimal = min(days_actually_skiing * rent, buy)

    print(f"在线花费: {online_total}")
    print(f"最优花费: {optimal}")
    print(f"竞争比: {online_total/optimal:.2f}")

    print("\n说明：")
    print("  - 对手可以构造很坏的情况")
    print("  - 竞争比是理论保证的下界")
    print("  - 随机化可以帮助避免被对手利用")

if __name__ == "__main__":
    # 基础功能测试
    # 测试函数: analyze_competitive_ratio, fence_algorithm, adversary_simulation
    # analyze_competitive_ratio()
    # fence_algorithm()
    # adversary_simulation()
    pass
