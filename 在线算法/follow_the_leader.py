# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / follow_the_leader



本文件实现 follow_the_leader 相关的算法功能。

"""



import random

import math

from collections import defaultdict





class FollowTheLeader:

    """

    Follow-The-Leader（跟随领导者）算法

    核心：选择历史表现最好的行动

    """



    def __init__(self, num_actions):

        self.num_actions = num_actions

        self.cumulative_loss = [0.0] * num_actions  # 每个行动的累积损失

        self.action_counts = [0] * num_actions      # 每个行动的选用次数

        self.total_rounds = 0



    def predict(self):

        """

        预测：选择到目前为止累积损失最小的行动

        返回: action_id

        """

        min_loss = min(self.cumulative_loss)

        # 有多个最小值时，随机选择

        candidates = [i for i, l in enumerate(self.cumulative_loss)

                     if l == min_loss]

        return random.choice(candidates)



    def update(self, action, loss):

        """更新损失"""

        self.cumulative_loss[action] += loss

        self.action_counts[action] += 1

        self.total_rounds += 1



    def get_regret(self, best_fixed_action):

        """

        计算遗憾（Regret）

        Regret(T) = Σ L_t(a_t) - min_a Σ L_t(a)

        """

        total_loss = sum(self.cumulative_loss)

        best_loss = self.total_rounds * self.cumulative_loss[best_fixed_action] / \

                    max(self.action_counts[best_fixed_action], 1)

        return total_loss - best_loss





class FTLJittered:

    """

    FTL with Jitter：在 FTL 选择后添加随机扰动

    目的：打破 FTL 的"锁定"现象（在对手 Adversarial 时）

    Jitter 可以是正态分布或均匀分布

    """



    def __init__(self, num_actions, jitter_scale=0.01):

        self.num_actions = num_actions

        self.cumulative_loss = [0.0] * num_actions

        self.jitter_scale = jitter_scale

        self.total_rounds = 0



    def predict(self):

        """预测：FTL + Jitter"""

        min_loss = min(self.cumulative_loss)

        candidates = [i for i, l in enumerate(self.cumulative_loss)

                     if l == min_loss]



        if random.random() < 0.1:  # 10% 概率随机探索

            return random.randint(0, self.num_actions - 1)

        return random.choice(candidates)



    def update(self, action, loss):

        self.cumulative_loss[action] += loss

        self.total_rounds += 1





class FTLForLoadBalancing:

    """

    FTL 用于负载均衡

    策略：选择当前连接数最少（或负载最低）的服务器

    """



    def __init__(self, servers):

        self.servers = servers

        self.server_loads = {s: 0.0 for s in servers}

        self.server_counts = {s: 0 for s in servers}

        self.total_requests = 0



    def select_server(self):

        """FTL：选择当前负载最低的服务器"""

        min_load = min(self.server_loads.values())

        candidates = [s for s, l in self.server_loads.items() if l == min_load]

        return random.choice(candidates)



    def dispatch_request(self, server, load=1.0):

        """分配请求到服务器"""

        self.server_loads[server] += load

        self.server_counts[server] += 1

        self.total_requests += 1



    def release_request(self, server, load=1.0):

        """释放请求"""

        self.server_loads[server] = max(0, self.server_loads[server] - load)



    def get_load_stats(self):

        return {

            'min_load': min(self.server_loads.values()),

            'max_load': max(self.server_loads.values()),

            'avg_load': sum(self.server_loads.values()) / len(self.servers),

            'total_requests': self.total_requests,

        }





class OnlineConvexOptimization:

    """

    在线凸优化（Online Convex Optimization, OCO）

    FTL 在 OCO 中的应用：每轮选择梯度最小的参数

    """



    def __init__(self, dim, learning_rate=0.1):

        self.dim = dim

        self.lr = learning_rate

        self.weights = [0.0] * dim

        self.cumulative_loss = 0.0

        self.total_rounds = 0



    def predict(self):

        """预测当前参数"""

        return self.weights[:]



    def update(self, gradient):

        """

        使用梯度更新参数（梯度下降）

        类似于 FTL：向损失减少的方向移动

        """

        for i in range(self.dim):

            self.weights[i] -= self.lr * gradient[i]



    def add_loss(self, loss):

        self.cumulative_loss += loss

        self.total_rounds += 1





if __name__ == '__main__':

    print("Follow-The-Leader（FTL）在线算法演示")

    print("=" * 60)



    # 模拟：在线选择服务器进行负载均衡

    import random

    random.seed(42)



    servers = ['S1', 'S2', 'S3', 'S4']



    print("\n【FTL 负载均衡模拟】")

    print(f"服务器: {servers}")

    print(f"策略: 选择当前负载最低的服务器（FTL 原则）")



    ftl = FTLForLoadBalancing(servers)

    lb_random = {'S1': 0, 'S2': 0, 'S3': 0, 'S4': 0}



    # 模拟 100 次请求分配

    n_requests = 100

    for i in range(n_requests):

        # FTL 选择

        chosen = ftl.select_server()

        ftl.dispatch_request(chosen, load=1.0)



        # 随机选择（基线）

        lb_random[random.choice(servers)] += 1



    stats = ftl.get_load_stats()

    print(f"\n{n_requests} 次请求后：")

    print(f"  FTL 策略:")

    print(f"    各服务器负载: {ftl.server_counts}")

    print(f"    负载标准差: ", end='')

    loads = list(ftl.server_counts.values())

    mean_load = sum(loads) / len(loads)

    std = math.sqrt(sum((l - mean_load) ** 2 for l in loads) / len(loads))

    print(f"{std:.2f}")



    random_loads = list(lb_random.values())

    random_std = math.sqrt(sum((l - mean_load) ** 2 for l in random_loads) / len(random_loads))

    print(f"  随机策略:")

    print(f"    负载标准差: {random_std:.2f}")



    print(f"  FTL 负载方差改善: {(random_std - std) / random_std * 100:.1f}%")



    print("\n" + "=" * 60)

    print("【FTL 在线学习演示】")



    num_actions = 5

    ftl = FollowTheLeader(num_actions)



    # 模拟对抗性损失序列

    random.seed(100)

    best_action = 2  # 假设 action=2 长期最优



    print(f"\n行动数: {num_actions}, 最佳行动: {best_action}")

    print(f"{'轮次':<8} {'选择行动':<12} {'损失':<10} {'累计损失'}")

    print("-" * 40)



    cumulative = [0] * num_actions

    for t in range(20):

        action = ftl.predict()

        # 对抗性损失：给被选中的行动较高损失

        if action == best_action:

            loss = 10  # 最佳行动被惩罚

        else:

            loss = random.randint(1, 5)



        ftl.update(action, loss)

        cumulative[action] += loss



        if t < 10 or t == 19:

            print(f"  {t+1:<8} {action:<12} {loss:<10} {cumulative}")



    print(f"\n最终累积损失: {ftl.cumulative_loss}")

    print(f"最少损失的行动: {min(range(num_actions), key=lambda i: ftl.cumulative_loss[i])}")

    print(f"  注：对抗性对手故意惩罚最优行动，FTL 被欺骗")



    print("\n" + "=" * 60)

    print("FTL 算法的关键性质：")

    print("  优点: 简单、直观、历史最优行动会胜出")

    print("  缺点: 对抗性对手可以轻松欺骗（引导算法选错）")

    print("  改进: FTL-Jittered（添加随机扰动避免锁定）")

    print("  改进: FTL-Regularized（正则化使策略更平滑）")

    print("\n应用：")

    print("  负载均衡、调度、推荐系统、在线广告投放")

    print("  FTL 是 Multiplicative Weights Update (MWU) 的前身")

