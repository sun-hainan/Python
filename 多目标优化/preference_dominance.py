# -*- coding: utf-8 -*-

"""

算法实现：多目标优化 / preference_dominance



本文件实现 preference_dominance 相关的算法功能。

"""



import random

import math



# ========== 算法参数 ==========

# pop_size: 种群规模

# max_iter: 最大迭代次数

# n_vars: 决策变量数量

# ref_point: 参考点，用于定义决策者偏好区域



pop_size = 100

max_iter = 150

n_vars = 10

ref_point = [0.5, 0.5]  # 双目标参考点





def objective_functions(x):

    """

    目标函数：双目标测试问题（ZDT2）

    :param x: 解向量

    :return: (f1, f2) 两个目标值

    """

    f1 = x[0]

    g = 1 + 9 * sum(x[1:]) / (n_vars - 1)

    h = 1 - (f1 / g) ** 2

    f2 = g * h

    return (f1, f2)





class ReferencePoint:

    """

    参考点类：表示决策者的偏好点

    """

    def __init__(self, point):

        self.point = point  # 参考点坐标

        self.niche = []  # 该参考点的小生境（附近解的索引）

        self.associated = False  # 是否已有解关联



    def distance(self, obj):

        """

        计算目标向量到参考点的归一化欧氏距离

        :param obj: 目标向量

        :return: 距离值

        """

        dist = 0

        for o, r in zip(obj, self.point):

            dist += ((o - r) ** 2)

        return math.sqrt(dist)



    def associate(self, obj, threshold=0.1):

        """

        判断目标向量是否关联到该参考点

        :param obj: 目标向量

        :param threshold: 关联阈值

        :return: True如果关联

        """

        return self.distance(obj) < threshold





def preference_dominance(p_obj, q_obj, ref_point, angle_weight=0.3):

    """

    基于偏好的支配关系判断

    结合距离偏好和角度偏好的支配关系



    :param p_obj: 解p的目标向量

    :param q_obj: 解q的目标向量

    :param ref_point: 参考点（决策者偏好）

    :param angle_weight: 角度权重（0-1之间）

    :return: True如果p偏好支配q

    """

    # 计算到参考点的距离

    p_dist = sum((p - r) ** 2 for p, r in zip(p_obj, ref_point))

    q_dist = sum((q - r) ** 2 for q, r in zip(q_obj, ref_point))

    p_dist = math.sqrt(p_dist)

    q_dist = math.sqrt(q_dist)



    # 计算与参考点连线的角度（简化为与最优方向偏差）

    # 假设目标是最小化，理想方向是朝向原点

    p_angle = math.atan2(p_obj[1], p_obj[0]) if p_obj[0] > 0 else 0

    q_angle = math.atan2(q_obj[1], q_obj[0]) if q_obj[0] > 0 else 0

    ideal_angle = math.atan2(0, 0)  # 原点方向

    p_angle_diff = abs(p_angle - ideal_angle)

    q_angle_diff = abs(q_angle - ideal_angle)



    # 归一化

    max_dist = math.sqrt(sum((1 - r) ** 2 for r in ref_point))

    if max_dist == 0:

        max_dist = 1



    p_pref_score = angle_weight * (p_angle_diff / math.pi) + (1 - angle_weight) * (p_dist / max_dist)

    q_pref_score = angle_weight * (q_angle_diff / math.pi) + (1 - angle_weight) * (q_dist / max_dist)



    # 偏好支配：p在偏好意义上不差于q，且至少一个维度更好

    return p_pref_score <= q_pref_score and (

        p_dist < q_dist or p_angle_diff < q_angle_diff or

        (p_obj[0] <= q_obj[0] and p_obj[1] <= q_obj[1])

    )





def associate_to_reference(objectives, ref_points):

    """

    将解关联到最近的参考点

    :param objectives: 所有解的目标值

    :param ref_points: 参考点列表

    :return: dict，参考点索引到解索引列表的映射

    """

    associations = {i: [] for i in range(len(ref_points))}

    for idx, obj in enumerate(objectives):

        # 找到最近的参考点

        min_dist = float('inf')

        closest_ref = 0

        for ref_idx, ref in enumerate(ref_points):

            dist = ref.distance(obj)

            if dist < min_dist:

                min_dist = dist

                closest_ref = ref_idx

        associations[closest_ref].append(idx)

    return associations





def generate_reference_points(n_obj, n_points=5):

    """

    生成均匀分布的参考点

    :param n_obj: 目标数量

    :param n_points: 每个目标维度的点数

    :return: 参考点列表

    """

    if n_obj == 2:

        points = []

        for i in range(n_points):

            for j in range(n_points):

                if i + j < n_points:

                    points.append([i / (n_points - 1), j / (n_points - 1)])

        return [ReferencePoint(p) for p in points]

    return [ReferencePoint([1.0 / n_points] * n_obj)]





def preference_evolutionary_algorithm(pop_size=pop_size, max_iter=max_iter, n_vars=n_vars):

    """

    基于偏好支配的进化算法主流程

    :param pop_size: 种群规模

    :param max_iter: 最大迭代次数

    :param n_vars: 变量维度

    :return: (population, objectives) 最终种群和目标值

    """

    # 生成参考点

    ref_points = generate_reference_points(2, n_points=5)



    # 初始化种群

    population = [[random.random() for _ in range(n_vars)] for _ in range(pop_size)]

    objectives = [objective_functions(x) for x in population]



    # 迭代优化

    for iteration in range(max_iter):

        # 关联到参考点

        associations = associate_to_reference(objectives, ref_points)



        # 基于参考点引导选择和交叉

        new_population = []

        for i in range(pop_size):

            # 选择：优先从有解关联的参考点区域选择

            parent_indices = []

            for ref_idx, members in associations.items():

                if len(members) > 0:

                    parent_indices.extend(members)



            if len(parent_indices) < 2:

                parent_indices = list(range(len(population)))



            # 随机选择两个父代

            p1_idx = random.choice(parent_indices)

            p2_idx = random.choice(parent_indices)

            while p2_idx == p1_idx:

                p2_idx = random.choice(parent_indices)



            # 模拟二进制交叉（SBX）的简化版本

            parent1 = population[p1_idx]

            parent2 = population[p2_idx]

            child = []

            for j in range(n_vars):

                if random.random() < 0.5:

                    child.append(parent1[j])

                else:

                    child.append(parent2[j])



            # 均匀变异

            for j in range(n_vars):

                if random.random() < 1.0 / n_vars:

                    child[j] += random.uniform(-0.1, 0.1)

                    child[j] = max(0, min(1, child[j]))



            new_population.append(child)



        # 评估子代

        new_objectives = [objective_functions(x) for x in new_population]



        # 合并种群

        combined_pop = population + new_population

        combined_obj = objectives + new_objectives



        # 基于偏好支配进行环境选择

        selected = []

        selected_obj = []

        for i in range(len(combined_pop)):

            is_dominated = False

            for j in range(len(combined_pop)):

                if i != j and preference_dominance(

                    combined_obj[j], combined_obj[i], ref_point

                ):

                    is_dominated = True

                    break

            if not is_dominated:

                selected.append(combined_pop[i])

                selected_obj.append(combined_obj[i])



        # 保持种群大小

        if len(selected) > pop_size:

            # 基于参考点拥挤度选择

            associations = associate_to_reference(selected_obj, ref_points)

            selected = selected[:pop_size]

            selected_obj = selected_obj[:pop_size]

        elif len(selected) < pop_size:

            # 补充随机解

            while len(selected) < pop_size:

                idx = random.randint(0, len(selected) - 1) if selected else 0

                selected.append(selected[idx][:])

                selected_obj.append(selected_obj[idx])



        population = selected[:pop_size]

        objectives = selected_obj[:pop_size]



        if iteration % 30 == 0:

            print(f"  迭代 {iteration}: 当前种群大小={len(population)}")



    return population, objectives





if __name__ == "__main__":

    print("=" * 50)

    print("基于偏好的支配关系算法测试")

    print("=" * 50)



    # 运行算法

    population, objectives = preference_evolutionary_algorithm()



    print(f"\n结果:")

    print(f"  获得的解数量: {len(population)}")

    print(f"  参考点数量: 5x5网格")



    # 打印部分结果

    print(f"\n部分Pareto最优解（按偏好距离排序）:")

    ref = ReferencePoint(ref_point)

    sorted_indices = sorted(range(len(objectives)), key=lambda i: ref.distance(objectives[i]))

    for i in sorted_indices[:5]:

        print(f"  解: f1={objectives[i][0]:.4f}, f2={objectives[i][1]:.4f}, "

              f"偏好距离={ref.distance(objectives[i]):.4f}")



    # 分析解在偏好区域的分布

    print(f"\n偏好区域分析:")

    n_near = sum(1 for obj in objectives if ref.distance(obj) < 0.3)

    print(f"  距离参考点<0.3的解数量: {n_near}")

