# -*- coding: utf-8 -*-

"""

算法实现：多智能体系统 / cooperative_pathfinding



本文件实现 cooperative_pathfinding 相关的算法功能。

"""



import numpy as np

from collections import defaultdict, deque

import heapq





class GridMap:

    """二维栅格地图"""

    

    def __init__(self, width, height, resolution=1.0):

        # width: 地图宽度（格子数）

        # height: 地图高度（格子数）

        # resolution: 分辨率（米/格子）

        self.width = width

        self.height = height

        self.resolution = resolution

        

        # 障碍物地图（0=可通过，1=障碍）

        self.occupancy = np.zeros((height, width), dtype=int)

    

    def set_obstacle(self, x, y):

        """设置障碍物格子"""

        if 0 <= x < self.width and 0 <= y < self.height:

            self.occupancy[y, x] = 1

    

    def is_free(self, x, y):

        """检查格子是否可通过"""

        if 0 <= x < self.width and 0 <= y < self.height:

            return self.occupancy[y, x] == 0

        return False

    

    def heuristic(self, pos1, pos2):

        """启发式函数（曼哈顿距离）"""

        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    

    def get_neighbors(self, pos):

        """获取邻居格子（四连通）"""

        x, y = pos

        neighbors = []

        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:

            nx, ny = x + dx, y + dy

            if self.is_free(nx, ny):

                neighbors.append((nx, ny))

        return neighbors





class Robot:

    """机器人对象"""

    

    def __init__(self, robot_id, start, goal):

        # robot_id: 机器人ID

        # start: 起始位置 (x, y)

        # goal: 目标位置 (x, y)

        self.robot_id = robot_id

        self.start = tuple(start)

        self.goal = tuple(goal)

        self.current_pos = self.start

        self.path = []

        self.path_index = 0

    

    def set_path(self, path):

        """设置路径"""

        self.path = path

        self.path_index = 0

    

    def move_to_next(self):

        """沿路径移动到下一位置"""

        if self.path_index < len(self.path) - 1:

            self.path_index += 1

            self.current_pos = self.path[self.path_index]

            return True

        return False





class CooperativeAStar:

    """协同A*算法：多机器人路径规划"""

    

    def __init__(self, grid_map, time_limit=100):

        # grid_map: 栅格地图

        # time_limit: 时间步限制

        self.grid_map = grid_map

        self.time_limit = time_limit

        self.robots = []

    

    def add_robot(self, robot):

        """添加机器人"""

        self.robots.append(robot)

    

    def get_state_key(self, pos_list, time):

        """生成状态键（用于冲突检测）"""

        pos_tuple = tuple(sorted([tuple(p) for p in pos_list]))

        return (pos_tuple, time)

    

    def is_valid_state(self, pos_list, time):

        """检查状态是否有效（无冲突）"""

        # 位置唯一性检查（同一格子只能有一个机器人）

        positions = [tuple(p) for p in pos_list]

        if len(positions) != len(set(positions)):

            return False

        

        # 障碍物检查

        for pos in positions:

            if not self.grid_map.is_free(pos[0], pos[1]):

                return False

        

        return True

    

    def compute_heuristic(self, robot_id, pos):

        """计算单个机器人的启发式值"""

        robot = self.robots[robot_id]

        return self.grid_map.heuristic(pos, robot.goal)

    

    def search(self):

        """

        协同A*搜索

        扩展状态：(pos_1, pos_2, ..., pos_n, time)

        """

        print("\n===== 协同A*路径规划 =====")

        

        n_robots = len(self.robots)

        if n_robots == 0:

            return []

        

        # 初始状态

        initial_positions = [r.start for r in self.robots]

        

        # 优先队列：(f_score, state)

        open_set = []

        g_score = defaultdict(lambda: float('inf'))

        initial_key = self.get_state_key(initial_positions, 0)

        g_score[initial_key] = 0

        

        # f_score下界

        h_init = sum(self.compute_heuristic(i, initial_positions[i]) 

                     for i in range(n_robots))

        heapq.heappush(open_set, (h_init, initial_key))

        

        visited = set()

        

        while open_set:

            f, state_key = heapq.heappop(open_set)

            

            if state_key in visited:

                continue

            visited.add(state_key)

            

            positions, time = state_key

            

            # 检查是否所有机器人都到达目标

            all_at_goal = all(

                tuple(positions[i]) == self.robots[i].goal 

                for i in range(n_robots)

            )

            if all_at_goal:

                print(f"  找到解，时间步={time}")

                return state_key

            

            # 超时检测

            if time >= self.time_limit:

                continue

            

            # 生成所有可能的联合动作

            joint_actions = self._generate_joint_actions(positions)

            

            for next_positions in joint_actions:

                if not self.is_valid_state(next_positions, time + 1):

                    continue

                

                # 计算g_score增量

                move_cost = sum(

                    1 if next_positions[i] != positions[i] else 0 

                    for i in range(n_robots)

                )

                

                new_g = g_score[state_key] + move_cost

                new_key = self.get_state_key(next_positions, time + 1)

                

                if new_g < g_score[new_key]:

                    g_score[new_key] = new_g

                    

                    # 计算启发式

                    h = sum(self.compute_heuristic(i, next_positions[i]) 

                            for i in range(n_robots))

                    f = new_g + h

                    heapq.heappush(open_set, (f, new_key))

        

        print("  未找到可行解")

        return None

    

    def _generate_joint_actions(self, current_positions):

        """生成所有可能的联合动作组合"""

        n_robots = len(self.robots)

        joint_actions = []

        

        # 每个机器人可以：保持不动或移动到邻居

        possible_moves = []

        for i, pos in enumerate(current_positions):

            moves = [pos] + list(self.grid_map.get_neighbors(pos))

            possible_moves.append(moves)

        

        # 笛卡尔积生成所有组合

        import itertools

        for moves in itertools.product(*possible_moves):

            joint_actions.append(list(moves))

        

        return joint_actions

    

    def extract_paths(self, final_state_key):

        """从最终状态提取各机器人的路径"""

        # 简化：使用各自的最短路径作为近似

        paths = []

        for robot in self.robots:

            path = self._single_robot_astar(robot.start, robot.goal)

            robot.set_path(path)

            paths.append(path)

        return paths

    

    def _single_robot_astar(self, start, goal):

        """单机器人A*搜索"""

        open_set = [(self.grid_map.heuristic(start, goal), start)]

        came_from = {}

        g_score = {start: 0}

        

        while open_set:

            _, current = heapq.heappop(open_set)

            

            if current == goal:

                # 重建路径

                path = [current]

                while current in came_from:

                    current = came_from[current]

                    path.append(current)

                return path[::-1]

            

            for neighbor in self.grid_map.get_neighbors(current):

                tentative_g = g_score[current] + 1

                if tentative_g < g_score.get(neighbor, float('inf')):

                    came_from[neighbor] = current

                    g_score[neighbor] = tentative_g

                    f = tentative_g + self.grid_map.heuristic(neighbor, goal)

                    heapq.heappush(open_set, (f, neighbor))

        

        return [start, goal]  # 默认路径





class CBSNode:

    """CBS冲突搜索树节点"""

    

    def __init__(self, constraints, paths, cost):

        # constraints: 约束列表

        # paths: 路径字典 {robot_id: path}

        # cost: 总成本

        self.constraints = constraints

        self.paths = paths

        self.cost = cost





class ConflictBasedSearch:

    """冲突型搜索(CBS)算法"""

    

    def __init__(self, grid_map):

        self.grid_map = grid_map

        self.robots = []

    

    def add_robot(self, robot):

        self.robots.append(robot)

    

    def find_conflicts(self, paths):

        """检测路径间的冲突"""

        conflicts = []

        

        for t in range(max(len(p) for p in paths.values())):

            positions_at_t = {}

            for robot_id, path in paths.items():

                if t < len(path):

                    pos = tuple(path[t])

                    if pos in positions_at_t:

                        # 同一时间同一位置冲突

                        conflicts.append({

                            'type': 'vertex',

                            'time': t,

                            'position': pos,

                            'robots': [positions_at_t[pos], robot_id]

                        })

                    positions_at_t[pos] = robot_id

            

            # 边冲突检测（两机器人交换位置）

            for robot1, robot2 in itertools.combinations(paths.keys(), 2):

                if t < len(paths[robot1]) - 1 and t < len(paths[robot2]) - 1:

                    if paths[robot1][t] == paths[robot2][t+1] and \

                       paths[robot1][t+1] == paths[robot2][t]:

                        conflicts.append({

                            'type': 'edge',

                            'time': t,

                            'robots': [robot1, robot2],

                            'positions': [paths[robot1][t], paths[robot1][t+1]]

                        })

        

        return conflicts

    

    def solve(self):

        """求解CBS"""

        print("\n===== CBS冲突搜索 =====")

        

        # 初始化：每个机器人独立规划最短路径

        paths = {}

        for robot in self.robots:

            astar = CooperativeAStar(self.grid_map)

            # 简化：用单机器人A*

            path = self._single_astar(robot.start, robot.goal)

            paths[robot.robot_id] = path

            robot.set_path(path)

        

        # 检测冲突

        conflicts = self.find_conflicts(paths)

        print(f"  初始规划完成，检测到{len(conflicts)}个冲突")

        

        return paths





if __name__ == "__main__":

    import itertools

    

    # 测试多机器人协同路径规划

    print("=" * 50)

    print("多机器人协同路径规划测试")

    print("=" * 50)

    

    # 创建地图

    grid_map = GridMap(width=10, height=10)

    

    # 添加障碍物

    for x in [3, 4, 5]:

        for y in [3, 4, 5]:

            grid_map.set_obstacle(x, y)

    

    print(f"\n地图大小: {grid_map.width} x {grid_map.height}")

    print("  障碍物: 中心3x3区域")

    

    # 创建机器人

    robots = [

        Robot(0, start=(0, 0), goal=(9, 9)),

        Robot(1, start=(9, 0), goal=(0, 9)),

        Robot(2, start=(0, 9), goal=(9, 0))

    ]

    

    print(f"\n机器人数量: {len(robots)}")

    for r in robots:

        print(f"  Robot {r.robot_id}: {r.start} -> {r.goal}")

    

    # 使用协同A*

    print("\n--- 协同A*算法 ---")

    coop_astar = CooperativeAStar(grid_map, time_limit=50)

    for robot in robots:

        coop_astar.add_robot(robot)

    

    result = coop_astar.search()

    

    if result:

        paths = coop_astar.extract_paths(result)

        print(f"\n规划路径:")

        for i, path in enumerate(paths):

            print(f"  Robot {i}: 长度={len(path)}")

    else:

        # 回退到独立规划

        print("\n使用独立A*规划...")

        paths = []

        for robot in robots:

            path = coop_astar._single_robot_astar(robot.start, robot.goal)

            robot.set_path(path)

            paths.append(path)

            print(f"  Robot {robot.robot_id}: 长度={len(path)}")

    

    # 使用CBS

    print("\n--- CBS冲突搜索 ---")

    cbs = ConflictBasedSearch(grid_map)

    for robot in robots:

        cbs.add_robot(robot)

    

    cbs_paths = cbs.solve()

    

    print("\n✓ 多机器人协同路径规划测试完成")

