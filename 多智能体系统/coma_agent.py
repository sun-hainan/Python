# -*- coding: utf-8 -*-

"""

算法实现：多智能体系统 / coma_agent



本文件实现 coma_agent 相关的算法功能。

"""



import numpy as np

import random





class CriticNetwork:

    """批评者网络：评估联合动作Q值"""

    

    def __init__(self, state_dim, n_agents, n_actions, hidden_dim=64):

        # state_dim: 全局状态维度

        # n_agents: 智能体数量

        # n_actions: 每个智能体的动作数

        # hidden_dim: 隐藏层维度

        self.state_dim = state_dim

        self.n_agents = n_agents

        self.n_actions = n_actions

        self.hidden_dim = hidden_dim

        

        # 动作编码维度（所有智能体动作的one-hot拼接）

        action_dim = n_agents * n_actions

        

        # 批评者网络权重

        self.w1 = np.random.randn(state_dim + action_dim, hidden_dim) * 0.1

        self.b1 = np.zeros(hidden_dim)

        self.w2 = np.random.randn(hidden_dim, 1) * 0.1

        self.b2 = np.zeros(1)

        

        # 目标网络

        self.target_w1 = self.w1.copy()

        self.target_w2 = self.w2.copy()

        self.target_b1 = self.b1.copy()

        self.target_b2 = self.b2.copy()

    

    def encode_actions(self, actions):

        """将动作列表编码为one-hot向量"""

        # actions: 各智能体动作的列表

        encoded = []

        for i, a in enumerate(actions):

            one_hot = np.zeros(self.n_actions)

            one_hot[a] = 1

            encoded.append(one_hot)

        return np.concatenate(encoded)

    

    def forward(self, state, actions):

        """计算Q值"""

        action_encoded = self.encode_actions(actions)

        inputs = np.concatenate([state, action_encoded])

        

        hidden = np.tanh(np.dot(inputs, self.w1) + self.b1)

        q_value = np.dot(hidden, self.w2) + self.b2

        return q_value.flatten()[0]

    

    def update(self, state, actions, td_error, lr=0.001):

        """更新批评者网络"""

        action_encoded = self.encode_actions(actions)

        inputs = np.concatenate([state, action_encoded])

        

        hidden = np.tanh(np.dot(inputs, self.w1) + self.b1)

        

        # 梯度更新

        grad_output = td_error

        grad_w2 = np.outer(hidden, [grad_output])

        grad_b2 = [grad_output]

        

        grad_hidden = np.dot(self.w2, [grad_output]) * (1 - hidden**2)

        grad_w1 = np.outer(inputs, grad_hidden)

        grad_b1 = grad_hidden

        

        self.w1 -= lr * grad_w1

        self.b1 -= lr * grad_b1

        self.w2 -= lr * grad_w2

        self.b2 -= lr * grad_b2

    

    def update_target(self, tau=0.005):

        """软更新目标网络"""

        self.target_w1 = (1 - tau) * self.target_w1 + tau * self.w1

        self.target_w2 = (1 - tau) * self.target_w2 + tau * self.w2

        self.target_b1 = (1 - tau) * self.target_b1 + tau * self.b1

        self.target_b2 = (1 - tau) * self.target_b2 + tau * self.b2





class ActorNetwork:

    """行动者网络：输出各智能体的策略"""

    

    def __init__(self, obs_dim, n_actions, hidden_dim=64):

        # obs_dim: 观测维度

        # n_actions: 动作空间大小

        # hidden_dim: 隐藏层维度

        self.obs_dim = obs_dim

        self.n_actions = n_actions

        self.hidden_dim = hidden_dim

        

        # 策略网络权重

        self.w1 = np.random.randn(obs_dim, hidden_dim) * 0.1

        self.b1 = np.zeros(hidden_dim)

        self.w2 = np.random.randn(hidden_dim, n_actions) * 0.1

        self.b2 = np.zeros(n_actions)

    

    def forward(self, obs):

        """前向传播，返回动作概率分布"""

        hidden = np.tanh(np.dot(obs, self.w1) + self.b1)

        logits = np.dot(hidden, self.w2) + self.b2

        

        # softmax转换为概率

        exp_logits = np.exp(logits - np.max(logits))  # 数值稳定化

        probs = exp_logits / np.sum(exp_logits)

        return probs

    

    def get_action(self, obs):

        """根据概率分布采样动作"""

        probs = self.forward(obs)

        return np.random.choice(self.n_actions, p=probs)

    

    def update(self, obs, action, advantage, lr=0.001):

        """

        策略梯度更新

        advantage: 来自COMA的基准优势函数

        """

        probs = self.forward(obs)

        

        # 计算策略梯度

        grad_log_prob = np.zeros(self.n_actions)

        grad_log_prob[action] = 1.0 / (probs[action] + 1e-8)

        

        # 简化版更新

        policy_grad = grad_log_prob * advantage

        

        hidden = np.tanh(np.dot(obs, self.w1) + self.b1)

        

        self.w2 -= lr * np.outer(hidden, policy_grad)

        self.b2 -= lr * policy_grad

        

        # 隐藏层梯度

        hidden_grad = np.dot(self.w2, policy_grad) * (1 - hidden**2)

        self.w1 -= lr * np.outer(obs, hidden_grad)

        self.b1 -= lr * hidden_grad





class COMA:

    """COMA主算法类"""

    

    def __init__(self, n_agents, obs_dim, n_actions, state_dim):

        # n_agents: 智能体数量

        # obs_dim: 每个智能体观测维度

        # n_actions: 动作空间大小

        # state_dim: 全局状态维度

        self.n_agents = n_agents

        self.obs_dim = obs_dim

        self.n_actions = n_actions

        self.state_dim = state_dim

        

        # 创建各智能体的行动者网络

        self.actors = [

            ActorNetwork(obs_dim, n_actions) 

            for _ in range(n_agents)

        ]

        

        # 创建全局批评者网络

        self.critic = CriticNetwork(state_dim, n_agents, n_actions)

        

        # 训练参数

        self.gamma = 0.99  # 折扣因子

    

    def select_actions(self, obs_list):

        """为所有智能体选择动作"""

        actions = []

        for i, obs in enumerate(obs_list):

            action = self.actors[i].get_action(obs)

            actions.append(action)

        return actions

    

    def compute_baseline(self, state, actions, focus_agent):

        """

        计算反事实基准（COMA核心）

        focus_agent: 关注的智能体索引

        actions: 当前联合动作

        """

        # 当前联合动作的Q值

        q_current = self.critic.forward(state, actions)

        

        # 计算该智能体采取其他动作时的Q值

        q_alternatives = []

        for a in range(self.n_actions):

            if a == actions[focus_agent]:

                q_alternatives.append(q_current)  # 当前动作保持不变

            else:

                alt_actions = actions.copy()

                alt_actions[focus_agent] = a

                q_alt = self.critic.forward(state, alt_actions)

                q_alternatives.append(q_alt)

        

        # 反事实基准：该智能体采取其他动作时Q值的期望

        probs = self.actors[focus_agent].forward(

            np.zeros(self.obs_dim)  # 简化：用零观测代替

        )

        baseline = np.sum(np.array(q_alternatives) * probs)

        

        return baseline

    

    def compute_advantage(self, state, actions, focus_agent):

        """计算优势函数"""

        q_value = self.critic.forward(state, actions)

        baseline = self.compute_baseline(state, actions, focus_agent)

        return q_value - baseline

    

    def train_step(self, obs_list, actions, reward, next_obs_list, done):

        """单步训练"""

        # 构建全局状态（简化处理）

        state = np.zeros(self.state_dim)

        next_state = np.zeros(self.state_dim)

        for i in range(min(len(obs_list), self.state_dim)):

            state[i] = np.mean(obs_list[i])

            next_state[i] = np.mean(next_obs_list[i])

        

        # 计算TD目标

        q_next = self.critic.forward(next_state, actions) if not done else 0

        td_target = reward + self.gamma * q_next

        

        # 更新批评者

        q_current = self.critic.forward(state, actions)

        td_error = td_target - q_current

        self.critic.update(state, actions, td_error)

        self.critic.update_target()

        

        # 为每个智能体计算优势并更新策略

        for i in range(self.n_agents):

            advantage = self.compute_advantage(state, actions, i)

            self.actors[i].update(obs_list[i], actions[i], advantage)

    

    def store_transition(self, obs_list, actions, reward, next_obs_list, done):

        """存储转移样本（简化版，在train_step中直接使用）"""

        self.last_transition = {

            'obs_list': obs_list,

            'actions': actions,

            'reward': reward,

            'next_obs_list': next_obs_list,

            'done': done

        }





if __name__ == "__main__":

    # 测试COMA算法

    print("=" * 50)

    print("COMA协同多智能体算法测试")

    print("=" * 50)

    

    # 参数设置

    n_agents = 3  # 3个智能体

    obs_dim = 8  # 观测维度8

    n_actions = 4  # 动作空间大小4

    state_dim = 12  # 全局状态维度12

    

    # 初始化COMA

    coma = COMA(n_agents, obs_dim, n_actions, state_dim)

    

    # 模拟环境交互与训练

    print("\n模拟环境交互与训练...")

    for episode in range(5):

        # 随机初始化观测

        obs_list = [np.random.randn(obs_dim) for _ in range(n_agents)]

        next_obs_list = [np.random.randn(obs_dim) for _ in range(n_agents)]

        

        # 选择动作

        actions = coma.select_actions(obs_list)

        

        # 计算奖励

        reward = sum(actions) / n_agents

        

        # 训练

        done = (episode == 4)

        coma.train_step(obs_list, actions, reward, next_obs_list, done)

        

        # 打印各智能体策略

        policy_info = []

        for i in range(n_agents):

            probs = coma.actors[i].forward(obs_list[i])

            policy_info.append(f"A{i}:{probs.round(2)}")

        print(f"  Episode {episode+1}: actions={actions}, reward={reward:.2f}")

        print(f"    策略分布: {policy_info}")

    

    print("\n✓ COMA算法测试完成")

    print(f"  智能体数量: {n_agents}")

    print(f"  动作空间: {n_actions}")

    print(f"  折扣因子: {coma.gamma}")

