# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / mcts_rl

本文件实现 mcts_rl 相关的算法功能。
"""

import numpy as np
import random
import math


class TreeNode:
    """
    MCTS 搜索树节点

    每个节点存储：
    - 状态访问次数 N(s)
    - 动作价值 Q(s,a)
    - 子节点列表
    """

    def __init__(self, state, parent=None, action=None, is_terminal=False):
        """
        初始化树节点

        参数:
            state: 节点对应的状态
            parent: 父节点
            action: 导致该节点的动作
            is_terminal: 是否为终止状态
        """
        self.state = state  # 状态
        self.parent = parent  # 父节点
        self.action = action  # 从父节点到达该节点的动作
        self.is_terminal = is_terminal  # 是否终止

        self.children = {}  # 子节点字典 {action: child_node}
        self.visit_count = 0  # 访问次数 N(s)
        self.value_sum = 0.0  # 价值累积 Q(s) * N(s)

        # 先验概率（用于 PUCT）
        self.prior = 0.0

    def get_value(self, c_param=1.4):
        """
        获取 UCB 值（用于选择最优子节点）

        参数:
            c_param: 探索常数
        返回:
            ucb_value: UCB 值
        """
        if self.visit_count == 0:
            return float('inf')  # 未访问的节点优先探索

        # 平均价值
        q_value = self.value_sum / self.visit_count
        # UCB 探索项
        if self.parent is not None:
            uct_term = c_param * math.sqrt(math.log(self.parent.visit_count) / self.visit_count)
        else:
            uct_term = 0

        return q_value + uct_term

    def expand(self, actions, priors=None):
        """
        扩展子节点

        参数:
            actions: 可用动作列表
            priors: 各动作的先验概率
        """
        if priors is None:
            priors = [1.0 / len(actions)] * len(actions)

        for action, prior in zip(actions, priors):
            if action not in self.children:
                self.children[action] = TreeNode(state=None, parent=self, action=action)

    def is_leaf(self):
        """判断是否为叶节点"""
        return len(self.children) == 0


class MCTS:
    """
    Monte Carlo Tree Search

    核心参数：
    - c_puct：探索常数（控制探索与利用的平衡）
    - n_simulations：每次决策的模拟次数
    - max_depth：最大搜索深度
    """

    def __init__(self, env_model, state_dim, action_dim,
                 c_puct=1.4, n_simulations=100, max_depth=50,
                 gamma=0.99):
        """
        初始化 MCTS

        参数:
            env_model: 环境模型（用于模拟）
            state_dim: 状态维度
            action_dim: 动作维度
            c_puct: PUCT 探索常数
            n_simulations: 模拟次数
            max_depth: 最大搜索深度
            gamma: 折扣因子
        """
        self.env_model = env_model
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.c_puct = c_puct
        self.n_simulations = n_simulations
        self.max_depth = max_depth
        self.gamma = gamma

    def search(self, root_state, legal_actions, prior_probs=None):
        """
        执行 MCTS 搜索

        参数:
            root_state: 根节点状态
            legal_actions: 合法动作列表
            prior_probs: 动作先验概率
        返回:
            root: 更新后的根节点
            best_action: 最优动作
        """
        # 创建根节点
        root = TreeNode(state=root_state, is_terminal=False)
        root.expand(legal_actions, prior_probs)

        # 多次模拟
        for _ in range(self.n_simulations):
            self._run_simulation(root, legal_actions)

        # 选择访问次数最多的子节点
        best_action = max(root.children.keys(),
                          key=lambda a: root.children[a].visit_count)
        return root, best_action

    def _run_simulation(self, node, legal_actions):
        """
        运行一次模拟

        参数:
            node: 起始节点
            legal_actions: 合法动作
        """
        # Selection：从根到叶选择
        current = node
        depth = 0

        while not current.is_leaf() and depth < self.max_depth:
            # 选择 UCB 值最大的子节点
            best_action = None
            best_ucb = -float('inf')

            for action, child in current.children.items():
                # PUCT：结合价值和先验
                ucb = child.get_value(self.c_puct) + child.prior * self.c_puct
                if ucb > best_ucb:
                    best_ucb = ucb
                    best_action = action
                    best_child = child

            current = best_child
            depth += 1

        # Expansion & Simulation
        if not current.is_terminal and depth < self.max_depth:
            # 使用环境模型模拟一步
            if current.state is None:
                # 重建状态
                current.state = self._get_state_from_parent(current)

            next_state = self.env_model.predict_next_state(current.state, current.action)
            reward = self.env_model.predict_reward(current.state, current.action)

            # 检查是否终止
            is_terminal = self._check_terminal(next_state)

            # 扩展
            next_actions = legal_actions
            current.expand(next_actions)

            # 模拟后续（简化为随机 rollout）
            rollout_reward = self._rollout(next_state, legal_actions, depth)

            # 总奖励
            total_reward = reward + self.gamma * rollout_reward

        else:
            # 终止或达到最大深度
            total_reward = 0.0

        # Backpropagation
        self._backpropagate(current, total_reward)

    def _rollout(self, state, actions, start_depth):
        """
        Rollout 模拟（随机策略到终止）

        参数:
            state: 起始状态
            actions: 动作列表
            start_depth: 起始深度
        返回:
            累积折扣奖励
        """
        total_reward = 0.0
        current_state = state.copy()
        discount = 1.0

        for t in range(self.max_depth - start_depth):
            # 随机选择动作
            action = random.choice(actions)
            next_state = self.env_model.predict_next_state(current_state, action)
            reward = self.env_model.predict_reward(current_state, action)

            total_reward += discount * reward
            discount *= self.gamma
            current_state = next_state

            if self._check_terminal(current_state):
                break

        return total_reward

    def _backpropagate(self, node, reward):
        """回传奖励并更新统计量"""
        current = node
        while current is not None:
            current.visit_count += 1
            current.value_sum += reward
            current = current.parent
            reward *= self.gamma  # 折扣

    def _get_state_from_parent(self, node):
        """从父节点重建状态"""
        # 简化：假设状态可从父节点推断
        if node.parent is None or node.parent.state is None:
            return np.zeros(self.state_dim)
        return self.env_model.predict_next_state(
            node.parent.state, node.parent.action
        )

    def _check_terminal(self, state):
        """检查是否为终止状态"""
        # 简化为判断状态是否超出边界
        return np.any(np.abs(state) > 10)


class MCTSAgent:
    """MCTS 强化学习智能体"""

    def __init__(self, state_dim, action_dim, c_puct=1.4,
                 n_simulations=100, gamma=0.99):
        """
        初始化 MCTS Agent

        参数:
            state_dim: 状态维度
            action_dim: 动作维度
            c_puct: 探索常数
            n_simulations: 模拟次数
            gamma: 折扣因子
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.n_simulations = n_simulations
        self.gamma = gamma

        # 简化的环境模型（用于 MCTS）
        self.env_model = SimpleEnvModel(state_dim, action_dim)

        # MCTS 搜索器
        self.mcts = MCTS(
            self.env_model, state_dim, action_dim,
            c_puct=c_puct, n_simulations=n_simulations,
            gamma=gamma
        )

        self.last_root = None

    def select_action(self, state, temperature=0.0):
        """
        选择动作

        参数:
            state: 当前状态
            temperature: 温度参数（0=贪心）
        返回:
            action: 选择的动作
            visit_counts: 各动作的访问次数
        """
        legal_actions = list(range(self.action_dim))

        # 执行 MCTS 搜索
        root, best_action = self.mcts.search(state, legal_actions)
        self.last_root = root

        if temperature == 0:
            # 贪心：选择访问最多的
            return best_action
        else:
            # 概率采样
            counts = np.array([root.children[a].visit_count if a in root.children else 0
                               for a in legal_actions])
            probs = counts ** (1.0 / temperature)
            probs = probs / np.sum(probs)
            return np.random.choice(legal_actions, p=probs)


class SimpleEnvModel:
    """简化的环境模型（用于 MCTS 模拟）"""

    def __init__(self, state_dim, action_dim):
        self.state_dim = state_dim
        self.action_dim = action_dim
        # 简化为恒等 + 噪声
        self.transition_noise = 0.1
        self.reward_noise = 0.1

    def predict_next_state(self, state, action):
        """预测下一个状态"""
        action_vec = np.zeros(self.action_dim)
        action_vec[action % self.action_dim] = 1.0
        delta = 0.2 * action_vec
        next_state = state + delta + np.random.randn(self.state_dim) * self.transition_noise
        return next_state

    def predict_reward(self, state, action):
        """预测奖励"""
        action_vec = np.zeros(self.action_dim)
        action_vec[action % self.action_dim] = 1.0
        reward = -np.sum(state ** 2) - 0.1 * np.sum(action_vec ** 2)
        return reward + np.random.randn() * self.reward_noise


if __name__ == "__main__":
    state_dim = 4
    action_dim = 2

    agent = MCTSAgent(state_dim, action_dim, n_simulations=50)

    # 模拟运行
    for episode in range(5):
        state = np.random.randn(state_dim)
        total_reward = 0

        for step in range(20):
            action = agent.select_action(state)
            next_state = state + 0.2 * np.eye(action_dim)[action % action_dim] + \
                        np.random.randn(state_dim) * 0.1
            reward = -np.sum(state ** 2)
            total_reward += reward
            state = next_state

            if np.any(np.abs(state) > 10):
                break

        # 显示根节点统计
        if agent.last_root:
            counts = {a: agent.last_root.children[a].visit_count
                      for a in agent.last_root.children}
            print(f"Episode {episode+1}: reward={total_reward:.2f}, "
                  f"visits={counts}")

    print("\nMCTS RL 测试完成!")
