# -*- coding: utf-8 -*-
"""
算法实现：运筹学 / vrp

本文件实现 vrp 相关的算法功能。
"""

import numpy as np
from itertools import permutations


def vrp_savings_algorithm(demands, distances, capacity, depot=0):
    """
    Clarke-Wright Savings 算法

    核心思想：
    - 计算合并两条路线带来的"节省"
    - savings(i,j) = d(i,0) + d(0,j) - d(i,j)
    - 按节省量降序合并路线
    """
    n = len(demands)
    customers = list(range(1, n))

    # 初始：每个客户单独一条路线
    routes = [[depot, c, depot] for c in customers]

    # 计算节省值
    savings = []
    for i in customers:
        for j in customers:
            if i < j:
                save = distances[depot][i] + distances[depot][j] - distances[i][j]
                savings.append((save, i, j))

    # 按节省值降序
    savings.sort(reverse=True)

    # 合并路线
    def find_route(node, routes):
        for i, route in enumerate(routes):
            if node in route:
                return i
        return -1

    def merge_routes(route1_idx, route2_idx, node1, node2, routes):
        route1 = routes[route1_idx]
        route2 = routes[route2_idx]

        # 找到节点在路线中的位置
        pos1 = route1.index(node1)
        pos2 = route2.index(node2)

        # 确定合并方向
        if pos1 == 1 and pos2 == len(route2) - 2:
            # route1: ... -> node1 -> depot -> ...
            # route2: ... -> depot -> node2 -> ...
            # 合并：直接连接
            new_route = route1[:pos1] + route2[1:pos2+1] + [depot]
        elif pos1 == len(route1) - 2 and pos2 == 1:
            # route1: ... -> depot -> node1 -> ...
            # route2: ... -> node2 -> depot -> ...
            new_route = [depot] + route1[1:pos1+1] + route2[1:-1] + [depot]
        else:
            return None

        return new_route

    for save, i, j in savings:
        route_i = find_route(i, routes)
        route_j = find_route(j, routes)

        if route_i == route_j:
            continue  # 同一路线

        # 检查合并后容量约束
        route_i_cargo = sum(demands[c] for c in routes[route_i] if c != depot)
        route_j_cargo = sum(demands[c] for c in routes[route_j] if c != depot)

        if route_i_cargo + route_j_cargo > capacity:
            continue

        # 尝试合并
        new_route = merge_routes(route_i, route_j, i, j, routes)

        if new_route is not None:
            # 删除旧路线，添加新路线
            routes = [r for idx, r in enumerate(routes) if idx not in [route_i, route_j]]
            routes.append(new_route)

    return routes


def vrp_nearest_neighbor(distances, demands, capacity, depot=0):
    """
    Nearest Neighbor 构造路线

    每次从当前位置选择最近的未访问客户（满足容量约束）
    """
    n = len(distances)
    unvisited = set(range(1, n))
    all_routes = []

    while unvisited:
        route = [depot]
        current = depot
        load = 0

        while unvisited:
            # 找最近的可行客户
            nearest = None
            min_dist = np.inf

            for c in unvisited:
                if load + demands[c] <= capacity:
                    if distances[current][c] < min_dist:
                        min_dist = distances[current][c]
                        nearest = c

            if nearest is None:
                break  # 当前路线结束

            route.append(nearest)
            load += demands[nearest]
            unvisited.remove(nearest)
            current = nearest

        route.append(depot)
        all_routes.append(route)

    return all_routes


def vrp_sweep(distances, demands, capacity, depot=0):
    """
    Sweep 算法

    按角度排序客户，然后贪心分配到路线
    """
    n = len(distances)

    # 计算角度（简化：假设客户在平面上）
    # 这里用索引作为简化
    angles = list(range(1, n))
    angles.sort(key=lambda x: x)  # 简化为按索引

    routes = []
    current_route = [depot]
    load = 0
    current_angle = 0

    for c in angles:
        if load + demands[c] <= capacity:
            current_route.insert(-1, c)
            load += demands[c]
        else:
            current_route.append(depot)
            routes.append(current_route)
            current_route = [depot, c, depot]
            load = demands[c]

    if len(current_route) > 2:
        current_route.append(depot)
        routes.append(current_route)

    return routes


def vrp_insertion(distances, demands, capacity, depot=0):
    """
    插入启发式

    从一条基础路线开始，逐个插入客户
    选择使插入成本最小的位置
    """
    n = len(distances)
    customers = list(range(1, n))

    # 初始化：空路线
    routes = [[depot, depot]]
    loads = [0]

    for c in customers:
        best_route = -1
        best_pos = -1
        best_cost = np.inf

        # 尝试插入到各路线的最佳位置
        for r_idx, route in enumerate(routes):
            for pos in range(1, len(route)):  # 不能在最后的 depot 之前
                # 计算插入成本
                prev = route[pos - 1]
                next_node = route[pos]
                cost_increase = (distances[prev][c] + distances[c][next_node] -
                                distances[prev][next_node])

                if cost_increase < best_cost and loads[r_idx] + demands[c] <= capacity:
                    best_cost = cost_increase
                    best_route = r_idx
                    best_pos = pos

        if best_route == -1:
            # 需要新路线
            routes.append([depot, c, depot])
            loads.append(demands[c])
        else:
            routes[best_route].insert(best_pos, c)
            loads[best_route] += demands[c]

    return routes


def calculate_vrp_total_distance(routes, distances):
    """计算 VRP 总距离"""
    total = 0
    for route in routes:
        for i in range(len(route) - 1):
            total += distances[route[i]][route[i + 1]]
    return total


def vrp_2opt(routes, distances, capacity, demands, depot=0):
    """
    对 VRP 的每条路线应用 2-opt
    """
    def two_opt_single(route, distances):
        n = len(route)
        improved = True
        while improved:
            improved = False
            for i in range(n - 1):
                for j in range(i + 2, n):
                    if j == n - 1 and i == 0:
                        continue
                    current = (distances[route[i]][route[i + 1]] +
                              distances[route[j]][route[(j + 1) % n]])
                    new = (distances[route[i]][route[j]] +
                          distances[route[i + 1]][route[(j + 1) % n]])
                    if new < current - 1e-10:
                        route[i + 1:j + 1] = reversed(route[i + 1:j + 1])
                        improved = True
        return route

    improved_routes = []
    for route in routes:
        new_route = two_opt_single(route.copy(), distances)
        # 验证容量约束
        load = sum(demands[c] for c in route if c != depot)
        if load <= capacity:
            improved_routes.append(new_route)
        else:
            improved_routes.append(route)

    return improved_routes


def vrp_capacitated(demands, distances, capacity, depot=0):
    """
    综合求解 CVRP
    使用多种启发式并选择最好的
    """
    results = {}

    # Clarke-Wright
    routes_cw = vrp_savings_algorithm(demands, distances, capacity, depot)
    dist_cw = calculate_vrp_total_distance(routes_cw, distances)
    results['savings'] = (routes_cw, dist_cw)

    # Nearest Neighbor
    routes_nn = vrp_nearest_neighbor(distances, demands, capacity, depot)
    dist_nn = calculate_vrp_total_distance(routes_nn, distances)
    results['nearest_neighbor'] = (routes_nn, dist_nn)

    # Sweep
    routes_sw = vrp_sweep(distances, demands, capacity, depot)
    dist_sw = calculate_vrp_total_distance(routes_sw, distances)
    results['sweep'] = (routes_sw, dist_sw)

    # Insertion
    routes_ins = vrp_insertion(distances, demands, capacity, depot)
    dist_ins = calculate_vrp_total_distance(routes_ins, distances)
    results['insertion'] = (routes_ins, dist_ins)

    # 2-opt 改进最好的
    best_name = min(results, key=lambda k: results[k][1])
    best_routes = results[best_name][0]
    improved = vrp_2opt(best_routes, distances, capacity, demands, depot)
    dist_improved = calculate_vrp_total_distance(improved, distances)

    return {
        'best_method': best_name,
        'routes': improved,
        'distance': dist_improved,
        'n_vehicles': len(improved),
        'all_results': {k: v[1] for k, v in results.items()}
    }


if __name__ == "__main__":
    print("=" * 60)
    print("车辆路径问题 (VRP)")
    print("=" * 60)

    # 测试数据：6个客户
    n = 7  # 包括 depot
    depot = 0

    distances = np.array([
        [0, 10, 15, 20, 25, 30, 12],
        [10, 0, 35, 25, 30, 15, 8],
        [15, 35, 0, 30, 10, 20, 18],
        [20, 25, 30, 0, 15, 25, 14],
        [25, 30, 10, 15, 0, 35, 22],
        [30, 15, 20, 25, 35, 0, 10],
        [12, 8, 18, 14, 22, 10, 0]
    ])

    demands = [0, 15, 20, 10, 25, 18, 12]  # 客户 1-6 的需求量
    capacity = 50

    print(f"客户数量: {len(demands) - 1}")
    print(f"车辆容量: {capacity}")
    print(f"需求量: {demands[1:]}")

    # 综合求解
    result = vrp_capacitated(demands, distances, capacity, depot)

    print(f"\n最优方法: {result['best_method']}")
    print(f"使用车辆数: {result['n_vehicles']}")
    print(f"总距离: {result['distance']}")

    print("\n各方法比较:")
    for method, dist in result['all_results'].items():
        print(f"  {method}: {dist:.2f}")

    print("\n路线详情:")
    for i, route in enumerate(result['routes']):
        route_demands = sum(demands[c] for c in route)
        route_dist = sum(distances[route[j]][route[j+1]] for j in range(len(route)-1))
        print(f"  路线 {i+1}: {route} (载货量={route_demands}, 距离={route_dist:.2f})")

    # 大规模测试
    print("\n--- 大规模测试 (n=20) ---")
    np.random.seed(42)
    n_large = 21
    dist_large = np.random.randint(1, 100, (n_large, n_large))
    np.fill_diagonal(dist_large, 0)
    dist_large = (dist_large + dist_large.T) / 2
    demands_large = np.random.randint(5, 30, n_large)
    demands_large[0] = 0  # depot

    result_large = vrp_capacitated(demands_large.tolist(), dist_large.tolist(), capacity=80, depot=0)

    print(f"客户数量: {n_large - 1}")
    print(f"最优方法: {result_large['best_method']}")
    print(f"使用车辆数: {result_large['n_vehicles']}")
    print(f"总距离: {result_large['distance']:.2f}")
