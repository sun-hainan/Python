# -*- coding: utf-8 -*-

"""

算法实现：随机算法 / monte_carlo_methods



本文件实现蒙特卡洛（Monte Carlo）方法。

蒙特卡洛方法的核心思想：

    - 用随机采样来估计确定性问题的解

    - 解的精度随采样数量增加而提高（大数定律）

    - 可能返回近似解（概率性保证），是概率型的而非精确型



主要实现：

    - 面积与积分估计

    - 随机游走与模拟

    - 重要采样降低方差

    - Bootstrap 置信区间估计

"""

import random
import math


def estimate_pi(n_samples: int = 100000) -> float:
    """
    用蒙特卡洛方法估计圆周率 π

    原理：在边长为 2 的正方形 [-1,1]×[-1,1] 中随机投点，
    落在单位圆 x² + y² ≤ 1 内的概率 = π/4。

    所以 π ≈ 4 × (圆内点数 / 总点数)

    参数：
        n_samples: 随机投点数量（越多越精确）

    返回：
        π 的估计值
    """
    inside_circle = 0

    for _ in range(n_samples):
        # 在 [-1, 1] × [-1, 1] 正方形内均匀采样
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)

        # 判断点是否在单位圆内
        if x * x + y * y <= 1.0:
            inside_circle += 1

    # 圆内比例 × 4 = π
    return 4.0 * inside_circle / n_samples


def monte_carlo_integration(f, a: float, b: float, n: int = 10000) -> float:
    """
    用蒙特卡洛方法计算定积分

    原理（均值估计器）：
        ∫[a,b] f(x) dx = (b - a) × E[f(X)]
        其中 X 在 [a,b] 上均匀分布

    即：用采样的平均值乘以区间长度来估计积分值。

    参数：
        f: 被积函数（接受单个浮点数输入）
        a: 积分下限
        b: 积分上限
        n: 采样数量

    返回：
        积分的估计值
    """
    total = 0.0

    for _ in range(n):
        # 在 [a, b] 内均匀采样 x
        x = random.uniform(a, b)
        # 累加函数值
        total += f(x)

    # 乘以区间长度并取平均
    return (b - a) * total / n


def stratified_sampling_integration(f, a: float, b: float, n: int = 10000) -> float:
    """
    分层采样蒙特卡洛积分

    将积分区间 [a, b] 划分为 n 个子区间，
    在每个子区间内独立采样。

    相比纯随机采样，分层采样可以降低方差。

    参数：
        f: 被积函数
        a: 积分下限
        b: 积分上限
        n: 总采样数量

    返回：
        积分的估计值
    """
    interval_width = (b - a) / n
    total = 0.0

    for i in range(n):
        # 在第 i 个子区间 [a + i*w, a + (i+1)*w] 内均匀采样
        sub_low = a + i * interval_width
        x = random.uniform(sub_low, sub_low + interval_width)
        total += f(x)

    return interval_width * total


def hit_miss_integration(f, a: float, b: float, y_max: float, n: int = 10000) -> float:
    """
    命中-错过法（Hit-or-Miss）估计积分

    在矩形区域 [a,b] × [0, y_max] 内随机投点，
    统计落在曲线 y = f(x) 下方的比例来估计积分。

    命中率方法比均值估计器效率低（通常需要更多样本）。

    参数：
        f: 被积函数（必须非负）
        a: 积分下限
        b: 积分上限
        y_max: 函数值的最大估计（用于定义采样矩形）
        n: 采样数量

    返回：
        积分的估计值
    """
    hits = 0

    for _ in range(n):
        x = random.uniform(a, b)
        y = random.uniform(0, y_max)

        if y <= f(x):
            hits += 1

    # 命中比例 × 矩形面积
    return (b - a) * y_max * hits / n


def random_walk_simulation(steps: int = 1000, dimension: int = 2) -> list:
    """
    简单随机游走模拟

    从原点出发，每步随机选择一个方向移动一个单位。
    用于模拟扩散、布朗运动等随机过程。

    参数：
        steps: 步数
        dimension: 维度（2 或 3）

    返回：
        随机游走的轨迹坐标列表
    """
    position = [0.0] * dimension
    trajectory = [tuple(position)]

    # 随机游走方向生成器
    for _ in range(steps):
        dim = random.randint(0, dimension - 1)
        direction = 1 if random.random() < 0.5 else -1
        position[dim] += direction
        trajectory.append(tuple(position))

    return trajectory


def gambler_ruin_simulation(
    initial_capital: int,
    target_capital: int,
    win_prob: float,
    n_simulations: int = 10000
) -> float:
    """
    赌徒破产问题的蒙特卡洛模拟

    赌徒从初始资本出发，每次以概率 win_prob 赢得 1 元，
    否则输掉 1 元，直到达到目标资本或破产。

    参数：
        initial_capital: 初始资本
        target_capital: 目标资本
        win_prob: 每局获胜概率
        n_simulations: 模拟次数

    返回：
        达到目标资本的概率
    """
    successes = 0

    for _ in range(n_simulations):
        capital = initial_capital

        while 0 < capital < target_capital:
            if random.random() < win_prob:
                capital += 1
            else:
                capital -= 1

        if capital >= target_capital:
            successes += 1

    return successes / n_simulations


def bootstrap_confidence_interval(
    data: list,
    statistic_fn=None,
    n_bootstrap: int = 5000,
    confidence_level: float = 0.95
) -> tuple:
    """
    Bootstrap 自助采样估计置信区间

    思想：从原始数据中有放回地随机抽取与原数据等大的样本，
    计算每次抽样的统计量，从而估计统计量的分布。

    参数：
        data: 原始数据列表
        statistic_fn: 统计量函数（默认为均值）
        n_bootstrap: Bootstrap 抽样次数
        confidence_level: 置信水平（默认 95%）

    返回：
        (统计量的 Bootstrap 均值, 下界, 上界)
    """
    n = len(data)
    if statistic_fn is None:
        statistic_fn = lambda x: sum(x) / len(x)

    # 存储每次 Bootstrap 抽样的统计量
    bootstrap_stats = []

    for _ in range(n_bootstrap):
        # 有放回随机抽样（从 data 中随机选择 n 个元素）
        sample = [random.choice(data) for _ in range(n)]
        stat = statistic_fn(sample)
        bootstrap_stats.append(stat)

    # 计算置信区间
    alpha = 1 - confidence_level
    lower_percentile = bootstrap_stats[int(n_bootstrap * alpha / 2)]
    upper_percentile = bootstrap_stats[int(n_bootstrap * (1 - alpha / 2))]
    bootstrap_mean = sum(bootstrap_stats) / len(bootstrap_stats)

    return bootstrap_mean, lower_percentile, upper_percentile


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 蒙特卡洛方法测试 ===\n")

    random.seed(42)

    # 测试 1: 估计 π
    print("--- 1. 估计 π ---")
    for n in [100, 1000, 10000, 100000]:
        pi_est = estimate_pi(n)
        error = abs(pi_est - math.pi)
        print(f"  n={n:6d}: π ≈ {pi_est:.6f}, 误差: {error:.6f}")

    # 测试 2: 定积分估计
    print("\n--- 2. 定积分估计 ∫x² dx (0 → 1) ---")
    exact = 1.0 / 3.0

    def f(x):
        return x * x

    for n in [100, 1000, 10000, 100000]:
        result = monte_carlo_integration(f, 0, 1, n)
        error = abs(result - exact)
        print(f"  n={n:6d}: ∫ = {result:.6f}, 误差: {error:.6f}")

    # 分层采样对比
    print("\n  分层采样对比:")
    for n in [1000, 10000]:
        stratified = stratified_sampling_integration(f, 0, 1, n)
        simple = monte_carlo_integration(f, 0, 1, n)
        print(f"  n={n}: 分层 {stratified:.6f}, 简单 {simple:.6f}")

    # 测试 3: 赌徒破产模拟
    print("\n--- 3. 赌徒破产模拟 ---")
    # 公平游戏：初始 10，目标 20，胜率 0.5
    prob = gambler_ruin_simulation(10, 20, 0.5, 20000)
    theoretical = 10 / 20  # 理论值 = initial / target
    print(f"  初始资本 10, 目标 20, 胜率 50%")
    print(f"  模拟达到目标概率: {prob:.4f}")
    print(f"  理论概率: {theoretical:.4f}")

    # 测试 4: Bootstrap 置信区间
    print("\n--- 4. Bootstrap 置信区间 ---")
    # 生成一些正态分布数据
    data = [random.gauss(100, 15) for _ in range(100)]
    sample_mean = sum(data) / len(data)

    boot_mean, lower, upper = bootstrap_confidence_interval(data, confidence_level=0.95)
    print(f"  样本均值: {sample_mean:.2f}")
    print(f"  Bootstrap 均值: {boot_mean:.2f}")
    print(f"  95% 置信区间: [{lower:.2f}, {upper:.2f}]")

    print("\n说明：")
    print("  - MC 核心：大数定律，样本量越大精度越高")
    print("  - 分层采样：降低方差，加速收敛")
    print("  - 命中-错过法：直观但效率低（只判断是否命中）")
    print("  - Bootstrap：用数据自身的随机重采样估计统计量分布")
