# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / distributed_rl



本文件实现 distributed_rl 相关的算法功能。

"""



import numpy as np

import random

import threading

import queue

import time

from collections import deque





class ReplayQueue:

    """线程安全的经验回放队列"""



    def __init__(self, maxsize=10000):

        """

        初始化经验队列



        参数:

            maxsize: 队列最大容量

        """

        self.queue = queue.Queue(maxsize=maxsize)

        self.lock = threading.Lock()

        self.maxsize = maxsize

        self.dropped_count = 0



    def put(self, item, timeout=1):

        """

        添加经验到队列



        参数:

            item: (state, action, reward, next_state, done) 元组

            timeout: 超时时间

        """

        try:

            self.queue.put(item, timeout=timeout)

        except queue.Full:

            # 队列满时丢弃最老的经验

            self.dropped_count += 1



    def get(self, batch_size=32, timeout=1):

        """

        从队列获取批次经验



        参数:

            batch_size: 批次大小

            timeout: 超时时间

        返回:

            批次数据或 None

        """

        batch = []

        for _ in range(batch_size):

            try:

                item = self.queue.get(timeout=timeout)

                batch.append(item)

            except queue.Empty:

                break

        if not batch:

            return None

        return zip(*batch)





class Actor:

    """

    分布式 RL 中的 Actor（执行器）



    负责：

    1. 运行环境收集经验

    2. 使用当前策略网络选择动作

    3. 将经验发送到经验队列

    """



    def __init__(self, actor_id, env_fn, policy_network, replay_queue,

                 update_freq=20, n_steps=1):

        """

        初始化 Actor



        参数:

            actor_id: Actor 编号

            env_fn: 环境创建函数

            policy_network: 策略网络（用于动作选择）

            replay_queue: 经验回放队列

            update_freq: 发送经验的频率（步数）

            n_steps: n步回报步数

        """

        self.actor_id = actor_id

        self.env = env_fn()  # 创建环境实例

        self.policy = policy_network

        self.queue = replay_queue

        self.update_freq = update_freq

        self.n_steps = n_steps

        self.running = True



        # N步缓冲

        self.nstep_buffer = deque(maxlen=n_steps)



    def run_episode(self):

        """

        运行一个 episode



        返回:

            episode_reward: 总奖励

            episode_steps: 总步数

        """

        state = self.env.reset()

        total_reward = 0

        total_steps = 0

        episode_history = []



        while self.running:

            # 选择动作

            action = self.policy.select_action(state)



            # 与环境交互

            next_state, reward, done, _ = self.env.step(action)



            # 存储到 N 步缓冲

            self.nstep_buffer.append((state, action, reward, done))



            total_reward += reward

            total_steps += 1

            state = next_state



            # 当 buffer 满或 episode 结束时，发送经验

            if (len(self.nstep_buffer) >= self.n_steps) or done:

                # 计算 n 步回报

                R = 0

                for i, (_, _, r, d) in enumerate(self.nstep_buffer):

                    R += (0.99 ** i) * r

                    if d:

                        break



                first_state = self.nstep_buffer[0][0]

                first_action = self.nstep_buffer[0][1]

                last_state = next_state



                # 发送到队列

                self.queue.put((first_state, first_action, R, last_state, done))



                if done:

                    break



        return total_reward, total_steps



    def run(self, num_episodes=10):

        """

        运行 Actor（阻塞直到完成）



        参数:

            num_episodes: 运行 episode 数量

        """

        rewards = []

        for ep in range(num_episodes):

            reward, steps = self.run_episode()

            rewards.append(reward)

            print(f"Actor {self.actor_id} | Episode {ep+1}: reward={reward:.2f}, steps={steps}")



        return rewards





class DistributedLearner:

    """

    分布式学习器（从队列学习）



    负责：

    1. 从经验队列读取数据

    2. 执行梯度更新

    3. 定期同步参数给 Actors

    """



    def __init__(self, state_dim, action_dim, hidden_dim=128,

                 lr=0.001, gamma=0.99, batch_size=64,

                 target_update_freq=200):

        """

        初始化学习器



        参数:

            state_dim: 状态维度

            action_dim: 动作维度

            hidden_dim: 隐藏层维度

            lr: 学习率

            gamma: 折扣因子

            batch_size: 批次大小

            target_update_freq: 目标网络更新频率

        """

        self.state_dim = state_dim

        self.action_dim = action_dim

        self.gamma = gamma

        self.batch_size = batch_size

        self.target_update_freq = target_update_freq

        self.train_step = 0



        # 经验队列

        self.replay_queue = ReplayQueue(maxsize=50000)



        # 在线网络和目标网络

        self.q_network = self._init_network()

        self.target_network = self._init_network()

        self._sync_target()



        # 锁

        self.lock = threading.Lock()



    def _init_network(self):

        """初始化 Q 网络"""

        np.random.seed(42)

        return {

            'w1': np.random.randn(self.state_dim, hidden_dim) * np.sqrt(2.0 / self.state_dim),

            'b1': np.zeros(hidden_dim),

            'w2': np.random.randn(hidden_dim, self.action_dim) * 0.01,

            'b2': np.zeros(self.action_dim)

        }



    def _forward(self, state, network):

        """前向传播"""

        h = np.maximum(0, np.dot(state, network['w1']) + network['b1'])

        q = np.dot(h, network['w2']) + network['b2']

        return q



    def _sync_target(self):

        """同步目标网络"""

        self.target_network = {k: v.copy() for k, v in self.q_network.items()}



    def select_action(self, state):

        """选择动作"""

        state = np.array(state).reshape(1, -1)

        q = self._forward(state, self.q_network)

        return np.argmax(q)



    def get_weights(self):

        """获取当前网络权重"""

        with self.lock:

            return {k: v.copy() for k, v in self.q_network.items()}



    def train(self):

        """从队列学习"""

        data = self.replay_queue.get(batch_size=self.batch_size, timeout=0.1)

        if data is None:

            return 0.0



        states, actions, rewards, next_states, dones = data

        states = np.array(states)

        actions = np.array(actions)

        rewards = np.array(rewards)

        next_states = np.array(next_states)

        dones = np.array(dones)



        # 计算目标 Q 值

        current_q = self._forward(states, self.q_network)

        current_q_selected = np.sum(current_q * np.eye(self.action_dim)[actions], axis=1)



        next_q = self._forward(next_states, self.target_network)

        next_q_max = np.max(next_q, axis=1)

        td_target = rewards + self.gamma * next_q_max * (1 - dones)



        loss = np.mean((current_q_selected - td_target) ** 2)



        self.train_step += 1

        if self.train_step % self.target_update_freq == 0:

            self._sync_target()



        return loss



    def learning_loop(self, num_updates=100):

        """

        持续学习循环



        参数:

            num_updates: 学习更新的次数

        """

        losses = []

        for step in range(num_updates):

            loss = self.train()

            if loss > 0:

                losses.append(loss)

            if step % 20 == 0:

                print(f"Learner | Step {step+1}/{num_updates}: loss={np.mean(losses[-20:]) if losses else 0:.4f}")



        return losses





if __name__ == "__main__":

    hidden_dim = 128



    # 模拟环境

    class DummyEnv:

        def __init__(self):

            self.state_dim = 4

            self.action_dim = 2



        def reset(self):

            return np.random.randn(self.state_dim)



        def step(self, action):

            next_state = np.random.randn(self.state_dim)

            reward = random.uniform(-1, 1)

            done = random.random() < 0.1

            return next_state, reward, done, {}



    class SimplePolicy:

        def __init__(self, state_dim, action_dim):

            self.state_dim = state_dim

            self.action_dim = action_dim



        def select_action(self, state):

            return random.randint(0, self.action_dim - 1)



    # 创建学习器

    learner = DistributedLearner(state_dim=4, action_dim=2)



    # 创建 Actor

    policy = SimplePolicy(4, 2)

    actor = Actor(actor_id=0, env_fn=DummyEnv, policy_network=policy,

                  replay_queue=learner.replay_queue)



    # 并行运行（模拟）

    print("启动经验收集...")

    for _ in range(3):

        actor.run_episode()



    print("\n启动学习器...")

    learner.learning_loop(num_updates=50)



    print("\n分布式 RL 测试完成!")

