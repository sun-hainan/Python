# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / hierarchical_rl



本文件实现 hierarchical_rl 相关的算法功能。

"""



import numpy as np

import random

from collections import defaultdict, deque





class Option:

    """

    Option（子策略）



    一个 Option 包含：

    - init_set: 可启动 Option 的状态集合

    - policy: 子策略

    - termination: 终止条件

    """



    def __init__(self, option_id, goal_dim, state_dim, action_dim,

                 subgoal_range=2.0):

        """

        初始化 Option



        参数:

            option_id: Option 编号

            goal_dim: 目标维度

            state_dim: 状态维度

            action_dim: 动作维度

            subgoal_range: 子目标范围

        """

        self.option_id = option_id

        self.goal_dim = goal_dim

        self.state_dim = state_dim

        self.action_dim = action_dim



        # 子策略网络（简化为线性）

        np.random.seed(42 + option_id)

        self.policy_weights = np.random.randn(state_dim + goal_dim, action_dim) * 0.01

        self.policy_bias = np.zeros(action_dim)



        # 终止条件阈值

        self.termination_threshold = 0.5



    def get_action(self, state, goal):

        """

        获取子策略的动作



        参数:

            state: 当前状态

            goal: 子目标

        返回:

            action: 选择的动作

        """

        state_goal = np.concatenate([state[:self.goal_dim], goal])

        action_logits = np.dot(state_goal, self.policy_weights) + self.policy_bias

        action = np.argmax(action_logits)

        return action



    def should_terminate(self, state, goal):

        """

        检查是否应终止 Option



        参数:

            state: 当前状态

            goal: 目标

        返回:

            should_stop: 是否终止

        """

        distance = np.linalg.norm(state[:self.goal_dim] - goal)

        return distance < self.termination_threshold





class MetaController:

    """

    元控制器（选择子目标）



    元控制器的任务是：

    1. 观察当前状态

    2. 选择一个子目标

    3. 监督子控制器执行

    4. 在子目标达成后选择新的子目标

    """



    def __init__(self, state_dim, goal_dim, n_options,

                 option_exploration_ratio=0.2):

        """

        初始化元控制器



        参数:

            state_dim: 状态维度

            goal_dim: 目标维度

            n_options: Option 数量

            option_exploration_ratio: Option 探索比例

        """

        self.state_dim = state_dim

        self.goal_dim = goal_dim

        self.n_options = n_options

        self.exploration_ratio = option_exploration_ratio



        # 元策略

        np.random.seed(100)

        self.policy_weights = np.random.randn(state_dim, goal_dim) * 0.01



        # 每个 Option 的价值估计

        self.option_values = np.zeros(n_options)



        # 目标空间范围

        self.goal_low = -2.0

        self.goal_high = 2.0



    def select_goal(self, state, epsilon=0.1):

        """

        选择子目标



        参数:

            state: 当前状态

            epsilon: 探索率

        返回:

            goal: 选择的子目标

        """

        if random.random() < epsilon:

            # 随机目标

            goal = np.random.uniform(self.goal_low, self.goal_high, self.goal_dim)

        else:

            # 基于策略选择

            goal = np.dot(state[:self.state_dim], self.policy_weights)

            # 裁剪到范围

            goal = np.clip(goal, self.goal_low, self.goal_high)



        return goal



    def select_option(self, state, epsilon=0.1):

        """

        选择执行的 Option



        参数:

            state: 当前状态

            epsilon: 探索率

        返回:

            option_id: 选择的 Option 编号

        """

        if random.random() < epsilon:

            return random.randint(0, self.n_options - 1)

        return np.argmax(self.option_values)



    def update_option_value(self, option_id, reward, done):

        """

        更新 Option 的价值估计



        参数:

            option_id: Option 编号

            reward: 获得的奖励

            done: 是否完成

        """

        alpha = 0.1

        gamma = 0.99

        td_error = reward + gamma * (1 - done) * 0 - self.option_values[option_id]

        self.option_values[option_id] += alpha * td_error





class HierarchicalRL:

    """

    分层强化学习智能体（Options 框架）



    结合元控制器和多个子 Option 进行分层决策。

    """



    def __init__(self, state_dim, goal_dim, action_dim, n_options=3):

        """

        初始化分层 RL



        参数:

            state_dim: 状态维度

            goal_dim: 目标维度

            action_dim: 动作维度

            n_options: Option 数量

        """

        self.state_dim = state_dim

        self.goal_dim = goal_dim

        self.action_dim = action_dim

        self.n_options = n_options



        # 元控制器

        self.meta = MetaController(state_dim, goal_dim, n_options)



        # 创建 Options

        self.options = []

        for i in range(n_options):

            opt = Option(i, goal_dim, state_dim, action_dim)

            self.options.append(opt)



        # 状态历史（用于追踪）

        self.state_history = deque(maxlen=100)



    def run_option(self, state, goal, option, env):

        """

        执行一个 Option 直到终止



        参数:

            state: 起始状态

            goal: 子目标

            option: 要执行的 Option

            env: 环境

        返回:

            total_reward: 累积奖励

            steps: 执行步数

        """

        current_state = state.copy()

        total_reward = 0.0

        steps = 0

        max_steps = 50



        while steps < max_steps:

            # 检查终止条件

            if option.should_terminate(current_state, goal):

                break



            # 选择动作

            action = option.get_action(current_state, goal)



            # 执行动作

            next_state = env.step(current_state, action)

            reward = env.get_reward(next_state, goal)

            done = env.is_done(next_state, goal)



            total_reward += reward

            steps += 1

            current_state = next_state



            if done:

                break



        return total_reward, steps



    def select_action(self, state):

        """

        元控制器选择动作（用于外部调用）



        参数:

            state: 当前状态

        返回:

            option_id: 选择的 Option

            goal: 子目标

        """

        goal = self.meta.select_goal(state)

        option_id = self.meta.select_option(state)

        return option_id, goal



    def update(self, option_id, reward, done):

        """更新元控制器的价值估计"""

        self.meta.update_option_value(option_id, reward, done)





class SimpleHRLEnv:

    """用于测试 HRL 的简单环境"""



    def __init__(self, state_dim, goal_dim):

        self.state_dim = state_dim

        self.goal_dim = goal_dim

        self.goal_threshold = 0.5



    def step(self, state, action):

        """环境一步转移"""

        action_vec = np.zeros(self.action_dim)

        action_vec[action] = 1.0

        delta = 0.1 * (action_vec[:self.state_dim] if self.state_dim <= self.action_dim

                       else action_vec)

        next_state = state + delta + np.random.randn(self.state_dim) * 0.05

        return next_state



    def get_reward(self, state, goal):

        """计算奖励"""

        return -np.linalg.norm(state[:self.goal_dim] - goal)



    def is_done(self, state, goal):

        """检查是否完成"""

        return np.linalg.norm(state[:self.goal_dim] - goal) < self.goal_threshold



    def reset(self):

        """重置环境"""

        return np.random.randn(self.state_dim) * 0.5





class MAXQDecomposition:

    """

    MAXQ 分层分解



    MAXQ 将任务分解为一个有向无环图（DAG）：

    - 根节点：主任务

    - 中间节点：子任务（可递归分解）

    - 叶节点：原始动作



    每个子任务学习一个策略 π_i(a|s, g)

    """



    def __init__(self, task_graph):

        """

        初始化 MAXQ



        参数:

            task_graph: 任务图 {task_id: [subtask_ids or actions]}

        """

        self.task_graph = task_graph

        self.policies = {}

        self.values = {}



        for task_id in task_graph:

            self.policies[task_id] = {}

            self.values[task_id] = 0.0



    def get_subtask(self, task_id, state):

        """

        获取子任务（在 MAXQ 中是确定性选择）



        实际实现中可以使用学习到的策略

        """

        return self.task_graph[task_id][0]



    def compute_value(self, task_id, state, max_depth=10):

        """

        递归计算任务价值



        参数:

            task_id: 任务编号

            state: 当前状态

            max_depth: 最大递归深度

        返回:

            V: 状态价值

        """

        if max_depth <= 0 or task_id not in self.task_graph:

            return 0.0



        subtasks = self.task_graph[task_id]

        if not subtasks:

            return 0.0



        total_value = 0.0

        for subtask in subtasks:

            if isinstance(subtask, int):

                # 原始动作

                total_value += self.values.get(('value', subtask), 0.0)

            else:

                # 子任务

                total_value += self.compute_value(subtask, state, max_depth - 1)



        return total_value





if __name__ == "__main__":

    state_dim = 4

    goal_dim = 2

    action_dim = 3

    n_options = 3



    # 创建 HRL 智能体

    agent = HierarchicalRL(state_dim, goal_dim, action_dim, n_options)

    env = SimpleHRLEnv(state_dim, goal_dim)



    # 训练循环

    print("=== 分层强化学习训练 ===")

    for episode in range(5):

        state = env.reset()

        episode_reward = 0

        total_steps = 0



        for step in range(100):

            # 元控制器选择 Option 和 Goal

            option_id, goal = agent.select_action(state)



            # 执行 Option

            option = agent.options[option_id]

            reward, steps = agent.run_option(state, goal, option, env)



            # 更新

            agent.update(option_id, reward, steps > 0)



            episode_reward += reward

            total_steps += steps

            state = env.step(state, np.random.randint(action_dim))



            if total_steps > 50:

                break



        print(f"Episode {episode+1}: reward={episode_reward:.2f}, steps={total_steps}, "

              f"option_values={agent.meta.option_values.round(3)}")



    # 测试 MAXQ

    print("\n=== MAXQ 分解测试 ===")

    task_graph = {

        'root': ['approach', 'grasp', 'lift'],

        'approach': [0, 1],  # 原始动作

        'grasp': [2, 3],

        'lift': [4, 5]

    }



    maxq = MAXQDecomposition(task_graph)

    state = np.random.randn(state_dim)

    v = maxq.compute_value('root', state)

    print(f"MAXQ root value: {v:.4f}")



    print("\n分层强化学习测试完成!")

