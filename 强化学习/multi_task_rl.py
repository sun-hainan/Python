# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / multi_task_rl



本文件实现 multi_task_rl 相关的算法功能。

"""



import numpy as np

import random





class TaskConditionedPolicy:

    """

    任务条件化策略网络



    策略网络结构：

    - 共享特征层（所有任务共享）

    - 任务嵌入层（学习任务特定表示）

    - 策略头（结合共享特征和任务嵌入）

    """



    def __init__(self, state_dim, action_dim, n_tasks, hidden_dim=128):

        """

        初始化任务条件化策略



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            n_tasks: 任务数量

            hidden_dim: 隐藏层维度

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.n_tasks = n_tasks

        self.hidden_dim = hidden_dim



        np.random.seed(42)



        # 共享特征层

        self.shared_weights = {

            'w1': np.random.randn(state_dim, hidden_dim) * np.sqrt(2.0 / state_dim),

            'b1': np.zeros(hidden_dim),

            'w2': np.random.randn(hidden_dim, hidden_dim) * np.sqrt(2.0 / hidden_dim),

            'b2': np.zeros(hidden_dim)

        }



        # 任务嵌入层

        self.task_embedding_dim = 32

        self.task_embeddings = np.random.randn(n_tasks, self.task_embedding_dim) * 0.01



        # 策略头（接收共享特征 + 任务嵌入）

        policy_input_dim = hidden_dim + self.task_embedding_dim

        self.policy_weights = {

            'w_mean': np.random.randn(policy_input_dim, action_dim) * 0.01,

            'b_mean': np.zeros(action_dim),

            'log_std': np.zeros(action_dim)

        }



    def get_shared_features(self, state):

        """

        提取共享特征



        参数:

            state: 输入状态

        返回:

            features: 共享特征

        """

        w = self.shared_weights

        h = np.maximum(0, np.dot(state, w['w1']) + w['b1'])

        h = np.maximum(0, np.dot(h, w['w2']) + w['b2'])

        return h



    def get_action(self, state, task_id):

        """

        获取动作



        参数:

            state: 当前状态

            task_id: 任务 ID

        返回:

            action: 动作

            log_prob: 对数概率

            mean: 动作均值

        """

        state = np.array(state).reshape(1, -1)

        shared_features = self.get_shared_features(state)

        task_emb = self.task_embeddings[task_id:task_id+1]



        # 拼接共享特征和任务嵌入

        combined = np.concatenate([shared_features, task_emb], axis=-1)



        # 策略头

        mean = np.dot(combined, self.policy_weights['w_mean']) + self.policy_weights['b_mean']

        std = np.exp(self.policy_weights['log_std'])



        # 采样

        action = mean + std * np.random.randn(self.action_dim)

        log_prob = -0.5 * np.sum(((action - mean) / std) ** 2)



        return action.squeeze(), log_prob.squeeze(), mean.squeeze()



    def get_value(self, state, task_id):

        """

        获取状态价值



        参数:

            state: 状态

            task_id: 任务 ID

        返回:

            value: 状态价值

        """

        state = np.array(state).reshape(1, -1)

        shared_features = self.get_shared_features(state)

        task_emb = self.task_embeddings[task_id:task_id+1]

        combined = np.concatenate([shared_features, task_emb], axis=-1)

        # 简化的价值估计

        return np.mean(combined)





class MultiTaskBuffer:

    """

    多任务经验回放缓冲区



    为每个任务维护独立的回放缓冲区，支持：

    - 任务平衡采样

    - 跨任务经验复用

    """



    def __init__(self, capacity=10000, n_tasks=1):

        """

        初始化多任务缓冲区



        参数:

            capacity: 总容量

            n_tasks: 任务数量

        """

        self.capacity = capacity

        self.n_tasks = n_tasks

        self.buffers = [[] for _ in range(n_tasks)]

        self.counts = np.zeros(n_tasks, dtype=int)



    def push(self, task_id, state, action, reward, next_state, done):

        """

        添加经验



        参数:

            task_id: 任务 ID

            state: 状态

            action: 动作

            reward: 奖励

            next_state: 下一个状态

            done: 是否结束

        """

        experience = (state, action, reward, next_state, done)

        self.buffers[task_id].append(experience)



        # 容量限制（每个任务独立限制）

        max_per_task = self.capacity // self.n_tasks

        if len(self.buffers[task_id]) > max_per_task:

            self.buffers[task_id].pop(0)



        self.counts[task_id] = len(self.buffers[task_id])



    def sample(self, batch_size, task_sampling='uniform'):

        """

        采样批次



        参数:

            batch_size: 批次大小

            task_sampling: 任务采样策略 ('uniform', 'proportional')

        返回:

            batch: 批次数据列表

            task_ids: 对应的任务 ID

        """

        if task_sampling == 'uniform':

            # 均匀采样任务

            active_tasks = [i for i in range(self.n_tasks) if self.counts[i] > 0]

            if not active_tasks:

                return None, None

            task_ids = np.random.choice(active_tasks, batch_size)

        else:

            # 按比例采样

            probs = self.counts / (np.sum(self.counts) + 1e-8)

            task_ids = np.random.choice(self.n_tasks, batch_size, p=probs)



        batch = []

        for tid in task_ids:

            if self.buffers[tid]:

                exp = random.choice(self.buffers[tid])

                batch.append((tid,) + exp)



        return batch, task_ids if batch else (None, None)



    def get_task_stats(self):

        """获取各任务的经验数量统计"""

        return {i: self.counts[i] for i in range(self.n_tasks)}





class MultiTaskRL:

    """

    多任务强化学习智能体



    使用任务条件化策略和共享表示进行多任务学习。

    """



    def __init__(self, state_dim, action_dim, n_tasks, hidden_dim=128,

                 lr=0.001, gamma=0.99, batch_size=32):

        """

        初始化多任务 RL



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            n_tasks: 任务数量

            hidden_dim: 隐藏层维度

            lr: 学习率

            gamma: 折扣因子

            batch_size: 批次大小

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.n_tasks = n_tasks

        self.gamma = gamma

        self.batch_size = batch_size



        # 策略网络

        self.policy = TaskConditionedPolicy(state_dim, action_dim, n_tasks, hidden_dim)



        # 经验回放

        self.buffer = MultiTaskBuffer(capacity=10000, n_tasks=n_tasks)



        # 学习率

        self.lr = lr



    def select_action(self, state, task_id, deterministic=False):

        """

        选择动作



        参数:

            state: 当前状态

            task_id: 任务 ID

            deterministic: 是否确定性策略

        返回:

            action: 动作

        """

        state = np.array(state).reshape(1, -1)

        shared_features = self.policy.get_shared_features(state)

        task_emb = self.policy.task_embeddings[task_id:task_id+1]

        combined = np.concatenate([shared_features, task_emb], axis=-1)



        mean = np.dot(combined, self.policy.policy_weights['w_mean']) + \

               self.policy.policy_weights['b_mean']



        if deterministic:

            return mean.squeeze()



        std = np.exp(self.policy.policy_weights['log_std'])

        action = mean + std * np.random.randn(self.action_dim)

        return action.squeeze()



    def store(self, task_id, state, action, reward, next_state, done):

        """存储经验"""

        self.buffer.push(task_id, state, action, reward, next_state, done)



    def train(self):

        """

        执行一步训练



        返回:

            loss: 训练损失

        """

        batch, task_ids = self.buffer.sample(self.batch_size)

        if batch is None:

            return 0.0



        # 简化的训练（策略梯度估计）

        loss = 0.0

        for tid, state, action, reward, next_state, done in batch:

            # 简化的价值更新

            v_s = self.policy.get_value(state, tid)

            v_next = self.policy.get_value(next_state, tid)

            td_target = reward + self.gamma * v_next * (1 - done)

            td_error = td_target - v_s



            # 简化的梯度更新

            grad_scale = self.lr * td_error

            for key in self.policy.policy_weights:

                if 'w' in key:

                    self.policy.policy_weights[key] += \

                        grad_scale * np.random.randn(*self.policy.policy_weights[key].shape) * 0.01



            loss += td_error ** 2



        return loss / len(batch)



    def adapt_to_task(self, task_id, env, n_episodes=5):

        """

        快速适配到新任务（Few-shot adaptation）



        参数:

            task_id: 目标任务 ID

            env: 环境

            n_episodes: 适配 episode 数

        """

        print(f"快速适配任务 {task_id}...")

        for ep in range(n_episodes):

            state = env.reset()

            episode_reward = 0



            for step in range(50):

                action = self.select_action(state, task_id, deterministic=False)

                next_state = env.step(state, action)

                reward = env.get_reward(state, action, task_id)

                done = env.is_done(next_state)



                self.store(task_id, state, action, reward, next_state, done)

                episode_reward += reward

                state = next_state



                if len(self.buffer.buffers[task_id]) > 10:

                    self.train()



                if done:

                    break



            print(f"  Episode {ep+1}: reward={episode_reward:.2f}")





class MultiTaskEnvWrapper:

    """多任务环境包装器"""



    def __init__(self, n_tasks, state_dim, action_dim):

        self.n_tasks = n_tasks

        self.state_dim = state_dim

        self.action_dim = action_dim



        # 每个任务的奖励权重不同

        self.task_rewards = [np.random.randn(state_dim) for _ in range(n_tasks)]



    def reset(self):

        """重置环境"""

        return np.random.randn(self.state_dim) * 0.5



    def step(self, state, action):

        """环境一步"""

        action_vec = np.zeros(self.action_dim)

        action_vec[action] = 1.0

        delta = 0.1 * action_vec[:self.state_dim]

        next_state = state + delta + np.random.randn(self.state_dim) * 0.05

        return next_state



    def get_reward(self, state, action, task_id):

        """计算奖励"""

        reward_weights = self.task_rewards[task_id]

        return -np.sum(state * reward_weights)



    def is_done(self, state):

        """检查是否终止"""

        return np.linalg.norm(state) > 5.0





if __name__ == "__main__":

    state_dim = 4

    action_dim = 2

    n_tasks = 3



    # 创建多任务智能体

    agent = MultiTaskRL(state_dim, action_dim, n_tasks, hidden_dim=64)

    env_wrapper = MultiTaskEnvWrapper(n_tasks, state_dim, action_dim)



    # 多任务训练

    print("=== 多任务强化学习训练 ===")

    for episode in range(5):

        # 随机选择训练任务

        task_id = random.randint(0, n_tasks - 1)

        state = env_wrapper.reset()

        episode_reward = 0



        for step in range(30):

            action = agent.select_action(state, task_id)

            next_state = env_wrapper.step(state, action)

            reward = env_wrapper.get_reward(state, action, task_id)

            done = env_wrapper.is_done(next_state)



            agent.store(task_id, state, action, reward, next_state, done)

            episode_reward += reward

            state = next_state



            if step % 5 == 0:

                agent.train()



            if done:

                break



        stats = agent.buffer.get_task_stats()

        print(f"Episode {episode+1} | Task {task_id}: reward={episode_reward:.2f}, "

              f"buffer_sizes={stats}")



    # 快速适配

    print("\n=== 快速适配测试 ===")

    new_task_id = n_tasks  # 新任务

    # 扩展嵌入

    new_emb = np.random.randn(1, agent.policy.task_embedding_dim) * 0.01

    agent.policy.task_embeddings = np.vstack([agent.policy.task_embeddings, new_emb])

    agent.n_tasks = new_task_id + 1

    agent.buffer.buffers.append([])

    agent.buffer.n_tasks += 1

    agent.buffer.counts = np.append(agent.buffer.counts, 0)



    class SimpleAdaptEnv:

        def reset(self):

            return np.random.randn(state_dim) * 0.5



        def step(self, state, action):

            return state + 0.1 * np.eye(action_dim)[action] + np.random.randn(state_dim) * 0.05



        def get_reward(self, state, action, task_id):

            return -np.sum(state ** 2)



        def is_done(self, state):

            return np.linalg.norm(state) > 5.0



    agent.adapt_to_task(new_task_id, SimpleAdaptEnv(), n_episodes=3)



    print("\n多任务强化学习测试完成!")

