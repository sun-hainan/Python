# -*- coding: utf-8 -*-

"""

算法实现：随机算法 / monte_carlo



本文件实现 monte_carlo 相关的算法功能。

"""



import random

import math





def estimate_pi(n_samples: int = 100000) -> float:

    """

    用蒙特卡洛方法估计π



    原理：在单位正方形内随机投点，

    落在单位圆内的比例 ≈ π/4



    参数：

        n_samples: 采样数量



    返回：π的估计值

    """

    inside_circle = 0



    for _ in range(n_samples):

        x = random.random()

        y = random.random()



        if x*x + y*y <= 1.0:

            inside_circle += 1



    return 4.0 * inside_circle / n_samples





def monte_carlo_integration(f, a: float, b: float, n: int = 10000) -> float:

    """

    用蒙特卡洛计算定积分



    ∫f(x)dx from a to b ≈ (b-a) * mean(f(x_i))



    参数：

        f: 被积函数

        a, b: 积分区间

        n: 采样数量

    """

    total = 0.0

    for _ in range(n):

        x = random.uniform(a, b)

        total += f(x)



    return (b - a) * total / n





def importance_sampling(f, a: float, b: float, g_samples, n: int = 10000) -> float:

    """

    重要采样（减少方差）



    思想：从更重要的分布采样

    """

    total = 0.0

    for _ in range(n):

        x = random.uniform(a, b)

        weight = f(x) / 1.0  # 假设均匀分布密度为1

        total += weight



    return (b - a) * total / n





def simulated_annealing(objective, neighbor_fn, initial_state, temperature: float = 1000.0,

                       cooling_rate: float = 0.995, min_temp: float = 1.0) -> tuple:

    """

    模拟退火（蒙特卡洛优化）



    参数：

        objective: 目标函数（最小化）

        neighbor_fn: 邻居状态生成函数

        initial_state: 初始状态

        temperature: 初始温度

        cooling_rate: 冷却率

        min_temp: 最低温度

    """

    current_state = initial_state

    current_value = objective(current_state)

    best_state = current_state

    best_value = current_value



    while temperature > min_temp:

        # 生成邻居状态

        next_state = neighbor_fn(current_state)

        next_value = objective(next_state)



        # 计算接受概率

        delta = next_value - current_value



        if delta < 0:

            # 接受更优解

            current_state = next_state

            current_value = next_value

        else:

            # 以概率 exp(-delta/T) 接受劣解

            prob = math.exp(-delta / temperature)

            if random.random() < prob:

                current_state = next_state

                current_value = next_value



        # 更新最优

        if current_value < best_value:

            best_state = current_state

            best_value = current_value



        # 降温

        temperature *= cooling_rate



    return best_state, best_value





def bootstrap_sampling(data, n_bootstrap: int = 1000, statistic_fn=None) -> list:

    """

    Bootstrap自助采样



    思想：从数据中有放回地随机采样，

    用来估计统计量的分布和置信区间

    """

    n = len(data)

    statistics = []



    for _ in range(n_bootstrap):

        # 有放回采样

        sample = [random.choice(data) for _ in range(n)]

        if statistic_fn:

            stat = statistic_fn(sample)

        else:

            stat = sum(sample) / n

        statistics.append(stat)



    return statistics





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 蒙特卡洛方法测试 ===\n")



    random.seed(42)



    # 1. 估计π

    print("1. 估计π")

    for n in [100, 1000, 10000, 100000]:

        pi_est = estimate_pi(n)

        error = abs(pi_est - math.pi)

        print(f"  n={n:6d}: π ≈ {pi_est:.6f} (误差: {error:.6f})")



    print()



    # 2. 数值积分

    print("2. 计算定积分 ∫x²dx from 0 to 1")



    def f(x):

        return x * x



    exact = 1.0 / 3.0

    for n in [100, 1000, 10000]:

        result = monte_carlo_integration(f, 0, 1, n)

        error = abs(result - exact)

        print(f"  n={n:6d}: ∫ = {result:.6f} (误差: {error:.6f})")



    print()



    # 3. Bootstrap

    print("3. Bootstrap置信区间")

    data = [random.gauss(50, 10) for _ in range(100)]

    stats = bootstrap_sampling(data, n_bootstrap=1000)



    mean = sum(stats) / len(stats)

    stats.sort()

    lower = stats[int(len(stats) * 0.025)]

    upper = stats[int(len(stats) * 0.975)]



    print(f"  数据均值: {sum(data)/len(data):.2f}")

    print(f"  Bootstrap均值: {mean:.2f}")

    print(f"  95%置信区间: [{lower:.2f}, {upper:.2f}]")



    print("\n说明：")

    print("  - MC方法的核心：大数定律")

    print("  - 方差是关键：重要采样可降低方差")

    print("  - 应用：物理、金融、机器学习")

