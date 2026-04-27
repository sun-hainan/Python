# -*- coding: utf-8 -*-

"""

算法实现：多目标优化 / MOPSO



本文件实现 MOPSO 相关的算法功能。

"""



import random

import math



# ========== 算法参数 ==========

# pop_size: 种群规模，每一代的粒子数量

# max_iter: 最大迭代次数

# w: 惯性权重，控制粒子保持原有速度的倾向

# c1: 个体学习因子，引导粒子向自身最优位置移动

# c2: 社会学习因子，引导粒子向全局最优位置移动



pop_size = 100

max_iter = 200

w = 0.4

c1 = 1.5

c2 = 1.5





def objective_functions(x):

    """

    目标函数：双目标测试函数（ZDT1）

    :param x: 解向量，list类型

    :return: (f1, f2) 两个目标值

    """

    f1 = x[0]  # 第一个目标：直接取第一个变量

    g = 1 + 9 * sum(x[1:]) / (len(x) - 1)  # 归一化的约束函数

    h = 1 - math.sqrt(f1 / g)  # 约束函数

    f2 = g * h  # 第二个目标

    return (f1, f2)





def dominates(p, q):

    """

    判断解p是否支配解q（Pareto支配）

    :param p: 解p的目标向量 (f1, f2)

    :param q: 解q的目标向量 (f1, f2)

    :return: True如果p支配q，否则False

    """

    return p[0] <= q[0] and p[1] <= q[1] and (p[0] < q[0] or p[1] < q[1])





def fast_non_dominated_sort(population, objectives):

    """

    快速非支配排序，将种群分为多个前沿层

    :param population: 解的列表

    :param objectives: 对应的目标值列表

    :return: fronts: list of list，每层前沿的解索引

    """

    n = len(population)  # 种群大小

    domination_count = [0] * n  # 支配该解的其他解的数量

    dominated_set = [[] for _ in range(n)]  # 该解支配的解集合

    fronts = [[]]  # 前沿层列表



    for i in range(n):  # 遍历每个解

        for j in range(n):  # 与其他解比较

            if i == j:

                continue

            if dominates(objectives[i], objectives[j]):

                # 如果解i支配解j，将j加入i的支配集合

                dominated_set[i].append(j)

            elif dominates(objectives[j], objectives[i]):

                # 如果解j支配解i，增加i的被支配计数

                domination_count[i] += 1



        if domination_count[i] == 0:  # 如果没有被任何解支配

            fronts[0].append(i)  # 加入第一前沿



    # 逐层构建前沿

    i = 0

    while i < len(fronts) and len(fronts[i]) > 0:

        next_front = []  # 下一前沿

        for idx in fronts[i]:

            for dominated in dominated_set[idx]:

                domination_count[dominated] -= 1

                if domination_count[dominated] == 0:

                    next_front.append(dominated)

        i += 1

        if len(next_front) > 0:

            fronts.append(next_front)



    return fronts[:-1] if len(fronts[-1]) == 0 else fronts





def calculate_crowding_distance(objectives, front):

    """

    计算某个前沿内解的拥挤度距离

    :param objectives: 所有解的目标值

    :param front: 该前沿的解索引列表

    :return: dict，索引到拥挤度距离的映射

    """

    if len(front) <= 2:

        return {idx: float('inf') for idx in front}



    distance = {idx: 0.0 for idx in front}  # 初始化距离为0

    n_obj = len(objectives[0])  # 目标数量



    for m in range(n_obj):  # 对每个目标维度

        # 按该目标值排序

        sorted_front = sorted(front, key=lambda x: objectives[x][m])

        distance[sorted_front[0]] = float('inf')  # 边界解

        distance[sorted_front[-1]] = float('inf')



        # 计算该目标的范围用于归一化

        obj_range = objectives[sorted_front[-1]][m] - objectives[sorted_front[0]][m]

        if obj_range == 0:

            obj_range = 1



        # 计算中间解的拥挤度

        for i in range(1, len(sorted_front) - 1):

            distance[sorted_front[i]] += (

                (objectives[sorted_front[i + 1]][m] - objectives[sorted_front[i - 1]][m]) / obj_range

            )



    return distance





class Particle:

    """

    粒子类：表示种群中的一个粒子

    """

    def __init__(self, dim):

        self.position = [random.random() for _ in range(dim)]  # 当前位置

        self.velocity = [random.uniform(-0.1, 0.1) for _ in range(dim)]  # 速度

        self.best_position = self.position[:]  # 个体最优位置

        self.best_objective = None  # 个体最优目标值





def update_velocity(particle, global_best, dim):

    """

    更新粒子的速度

    :param particle: Particle对象

    :param global_best: 全局最优位置

    :param dim: 维度

    :return: 更新后的速度列表

    """

    new_velocity = []

    for i in range(dim):

        # 速度更新公式：w*v + c1*r1*(pbest-x) + c2*r2*(gbest-x)

        v = w * particle.velocity[i]

        v += c1 * random.random() * (particle.best_position[i] - particle.position[i])

        v += c2 * random.random() * (global_best[i] - particle.position[i])

        new_velocity.append(v)

    return new_velocity





def update_position(particle, dim):

    """

    更新粒子的位置，并进行边界约束

    :param particle: Particle对象

    :param dim: 维度

    """

    particle.velocity = update_velocity(particle, None, dim)

    for i in range(dim):

        particle.position[i] += particle.velocity[i]

        # 约束到[0, 1]区间

        if particle.position[i] < 0:

            particle.position[i] = 0

        elif particle.position[i] > 1:

            particle.position[i] = 1





def select_global_best(archive, objectives, archive_fitness):

    """

    从外部存档中选择全局最优位置（基于拥挤度）

    :param archive: 存档中的解列表

    :param objectives: 存档的目标值

    :param archive_fitness: 存档的适应度值

    :return: 选择的全局最优位置

    """

    # 从第一前沿选择

    fronts = fast_non_dominated_sort(archive, objectives)

    if len(fronts) == 0 or len(fronts[0]) == 0:

        return archive[0] if archive else [random.random() for _ in range(len(archive[0]))]



    # 从第一前沿选择拥挤度最大的（多样性最好）

    crowding = calculate_crowding_distance(objectives, fronts[0])

    best_idx = max(fronts[0], key=lambda x: crowding[x])

    return archive[best_idx]





def mopso(dim=30):

    """

    多目标粒子群优化主算法

    :param dim: 问题维度

    :return: (archive, objectives) 最终存档和解的目标值

    """

    # 初始化种群

    particles = [Particle(dim) for _ in range(pop_size)]

    archive = []  # 外部存档，存储非支配解

    archive_objectives = []



    # 计算初始种群的目标值

    for p in particles:

        obj = objective_functions(p.position)

        p.best_objective = obj

        p.best_position = p.position[:]

        archive.append(p.position[:])

        archive_objectives.append(obj)



    # 迭代优化

    for iteration in range(max_iter):

        # 更新外部存档（非支配解）

        new_archive = []

        new_objectives = []

        for i, (pos, obj) in enumerate(zip(archive, archive_objectives)):

            is_dominated = False

            to_remove = []

            for j, (apos, aobj) in enumerate(zip(new_archive, new_objectives)):

                if dominates(obj, aobj):

                    to_remove.append(j)

                elif dominates(aobj, obj):

                    is_dominated = True

            if not is_dominated:

                for idx in reversed(to_remove):

                    new_archive.pop(idx)

                    new_objectives.pop(idx)

                new_archive.append(pos[:])

                new_objectives.append(obj)



        archive = new_archive

        archive_objectives = new_objectives



        # 如果存档满了，基于拥挤度删减

        if len(archive) > pop_size:

            fronts = fast_non_dominated_sort(archive, archive_objectives)

            remaining = pop_size

            for front in fronts:

                if len(front) <= remaining:

                    remaining -= len(front)

                else:

                    crowding = calculate_crowding_distance(archive_objectives, front)

                    sorted_front = sorted(front, key=lambda x: crowding[x])

                    keep = sorted_front[:remaining]

                    for idx in front:

                        if idx in keep:

                            keep_idx = keep.index(idx)

                            pass

                    break



        # 选择全局最优

        if len(archive) > 0:

            global_best = select_global_best(archive, archive_objectives, None)

        else:

            global_best = particles[0].position[:]



        # 更新粒子

        for p in particles:

            update_position(p, dim)

            obj = objective_functions(p.position)

            if dominates(obj, p.best_objective):

                p.best_objective = obj

                p.best_position = p.position[:]



    return archive, archive_objectives





if __name__ == "__main__":

    print("=" * 50)

    print("多目标粒子群优化算法（MOPSO）测试")

    print("=" * 50)



    # 运行MOPSO算法

    dim = 30  # 问题维度

    archive, objectives = mopso(dim)



    print(f"\n算法参数:")

    print(f"  种群规模: {pop_size}")

    print(f"  最大迭代: {max_iter}")

    print(f"  问题维度: {dim}")



    print(f"\n结果:")

    print(f"  获得的Pareto最优解数量: {len(archive)}")



    # 打印部分Pareto前沿解

    print(f"\n前5个Pareto最优解:")

    for i, (pos, obj) in enumerate(zip(archive[:5], objectives[:5])):

        print(f"  解{i + 1}: f1={obj[0]:.4f}, f2={obj[1]:.4f}")



    # 验证解的质量

    dominated_count = 0

    for i in range(len(objectives)):

        for j in range(len(objectives)):

            if i != j and dominates(objectives[i], objectives[j]):

                dominated_count += 1

                break



    print(f"\n解的质量评估:")

    print(f"  非支配解数量: {len(objectives) - dominated_count // 2}")

    print(f"  （非支配解互相不支配）")

