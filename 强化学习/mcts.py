# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / mcts

本文件实现 mcts 相关的算法功能。
"""

import math
import random
import copy


class MCTSNode:
    """MCTS 树节点"""

    def __init__(self, state, parent=None, action=None, prior=0.0):
        self.state = state  # 当前游戏状态
        self.parent = parent  # 父节点
        self.action = action  # 从父状态执行的动作到达此节点
        self.children = {}  # 子节点字典 {action: child_node}
        self.visits = 0  # 访问次数
        self.value_sum = 0.0  # 累积价值（Win=1, Loss=0, Draw=0.5）
        self.prior = prior  # 先验概率（用于 PUCT）

    def is_expanded(self):
        """检查节点是否已完全扩展"""
        return len(self.children) > 0

    def expand(self, legal_actions, prior_probs=None):
        """扩展节点：为每个合法动作创建子节点"""
        if prior_probs is None:
            prior_probs = [1.0 / len(legal_actions)] * len(legal_actions)
        for action, prior in zip(legal_actions, prior_probs):
            if action not in self.children:
                self.children[action] = MCTSNode(
                    state=None, parent=self, action=action, prior=prior
                )

    def backpropagate(self, reward):
        """回溯：更新此节点及所有祖先节点的统计信息"""
        self.visits += 1
        self.value_sum += reward
        if self.parent is not None:
            # 下一玩家视角的奖励（零和游戏）
            self.parent.backpropagate(1 - reward)


class MCTS:
    """Monte Carlo Tree Search 算法"""

    def __init__(self, c_puct=1.41, n_simulations=1000, rollout_depth=20):
        """
        c_puct: UCB1/PUCT 的探索常数
        n_simulations: 每步执行的模拟次数
        rollout_depth: 随机 rollout 的最大深度
        """
        self.c_puct = c_puct
        self.n_simulations = n_simulations
        self.rollout_depth = rollout_depth
        self.root = None

    def ucb_score(self, node):
        """计算 UCB1/PUCT 分数，平衡探索与利用"""
        if node.visits == 0:
            return float('inf')  # 未访问过，优先探索
        exploitation = node.value_sum / node.visits
        exploration = self.c_puct * node.prior * math.sqrt(node.parent.visits) / (1 + node.visits)
        return exploitation + exploration

    def select(self, node):
        """选择：从根节点沿 UCB 分数最高的子节点下降到叶节点"""
        while node.is_expanded():
            best_action = None
            best_score = -float('inf')
            for action, child in node.children.items():
                score = self.ucb_score(child)
                if score > best_score:
                    best_score = score
                    best_action = action
            node = node.children[best_action]
        return node

    def simulate(self, node, game):
        """模拟：随机 rollout 返回奖励"""
        state = copy.deepcopy(node.state) if node.state is not None else game.get_state()
        for _ in range(self.rollout_depth):
            if game.is_terminal(state):
                break
            legal = game.get_legal_actions(state)
            if not legal:
                break
            action = random.choice(legal)
            state = game.apply_action(state, action)
        reward = game.get_reward(state)  # 假设返回当前玩家视角的奖励
        return reward

    def backpropagate(self, node, reward):
        """回溯更新"""
        node.backpropagate(reward)

    def search(self, game, state, prior_probs=None):
        """执行 MCTS 搜索，返回最优动作及访问次数分布"""
        # 初始化或重置根节点
        if self.root is None or self.root.state is None:
            self.root = MCTSNode(state=state)
        else:
            # 检查是否复用现有根节点
            if state != self.root.state:
                self.root = MCTSNode(state=state)

        legal_actions = game.get_legal_actions(state)
        if not legal_actions:
            return None

        # 为根节点设置先验概率
        if prior_probs is None:
            prior_probs = [1.0 / len(legal_actions)] * len(legal_actions)
        self.root.expand(legal_actions, prior_probs)

        # 执行多次模拟
        for _ in range(self.n_simulations):
            # 选择
            node = self.select(self.root)
            # 扩展 + 模拟
            if not game.is_terminal(node.state):
                if not node.is_expanded():
                    # 扩展
                    node.expand(legal_actions, prior_probs)
                # 从随机子节点模拟
                if node.is_expanded():
                    child = random.choice(list(node.children.values()))
                    node = child
                reward = self.simulate(node, game)
            else:
                reward = game.get_reward(node.state)
            # 回溯
            self.backpropagate(node, reward)

        # 选择访问次数最多的动作
        best_action = None
        best_visits = -1
        for action, child in self.root.children.items():
            if child.visits > best_visits:
                best_visits = child.visits
                best_action = action
        return best_action


class SimpleGame:
    """简单棋盘游戏（吃子游戏）用于测试 MCTS"""

    def __init__(self):
        self.board_size = 3
        self.current_player = 1  # 1 或 -1

    def get_state(self):
        """返回当前状态元组"""
        return (self.current_player, tuple(range(self.board_size)))

    def get_legal_actions(self, state):
        """返回合法动作列表"""
        player = state[0]
        pieces = set(state[1])
        actions = []
        for pos in pieces:
            for d in [-1, 1]:
                new_pos = pos + d
                if 0 <= new_pos < self.board_size and new_pos not in pieces:
                    actions.append((pos, d))
        return actions

    def apply_action(self, state, action):
        """执行动作，返回新状态"""
        player = state[0]
        pieces = list(state[1])
        pos, d = action
        idx = pieces.index(pos)
        pieces[idx] = pos + d
        return (-player, tuple(sorted(pieces)))

    def is_terminal(self, state):
        """检查是否终局"""
        pieces = set(state[1])
        return len(pieces) == 0

    def get_reward(self, state):
        """返回当前玩家视角的奖励 1=赢, 0=输, 0.5=平"""
        if self.is_terminal(state):
            pieces = set(state[1])
            if len(pieces) == 0:
                return 0.5  # Draw
        return 0.5  # 简化


if __name__ == "__main__":
    # 测试 MCTS
    game = SimpleGame()
    mcts = MCTS(n_simulations=200, rollout_depth=10)
    state = game.get_state()

    print("MCTS 搜索演示:")
    for step in range(3):
        best_action = mcts.search(game, state)
        if best_action is None:
            print(f"Step {step}: 无合法动作")
            break
        print(f"Step {step}: 选择动作 {best_action}, 访问次数 {mcts.root.children[best_action].visits}")
        state = game.apply_action(state, best_action)
        game.current_player = -game.current_player
        if game.is_terminal(state):
            print("游戏结束")
            break
    print("MCTS 测试完成")
