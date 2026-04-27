# -*- coding: utf-8 -*-
"""
算法实现：多智能体系统 / graph_game

本文件实现 graph_game 相关的算法功能。
"""

import numpy as np
from collections import defaultdict


class GraphGame:
    """图博弈基类"""
    
    def __init__(self, adjacency_matrix):
        # adjacency_matrix: 邻接矩阵
        self.adjacency = np.array(adjacency_matrix)
        self.n_agents = len(adjacency_matrix)
        
        # 参与者策略
        self.strategies = np.zeros(self.n_agents, dtype=int)  # 0 or 1
        self.payoffs = np.zeros(self.n_agents)
    
    def get_neighbors(self, agent_id):
        """获取邻居列表"""
        return np.where(self.adjacency[agent_id] > 0)[0]
    
    def set_strategy(self, agent_id, strategy):
        """设置策略"""
        self.strategies[agent_id] = strategy
    
    def get_payoff(self, agent_id):
        """计算单个智能体的收益"""
        raise NotImplementedError


class CoordinationGame(GraphGame):
    """网络协调博弈
    
    收益矩阵:
           C      D
    C    1, 1   -1, 0
    D    0, -1  -1, -1
    
    参与者倾向于与邻居协调（选择相同策略）
    """
    
    def __init__(self, adjacency_matrix, payoff_coordination=1.0, payoff_defect=-1.0):
        super().__init__(adjacency_matrix)
        self.payoff_C = payoff_coordination  # 协调收益
        self.payoff_D = payoff_defect         # 背叛损失
    
    def get_payoff(self, agent_id):
        """计算智能体收益"""
        my_strategy = self.strategies[agent_id]
        neighbors = self.get_neighbors(agent_id)
        
        total_payoff = 0.0
        for neighbor in neighbors:
            neighbor_strategy = self.strategies[neighbor]
            
            # 双人协调博弈收益
            if my_strategy == neighbor_strategy:
                # 都选C或都选D
                if my_strategy == 1:
                    total_payoff += self.payoff_C  # 双方协调，收益为正
                else:
                    total_payoff += 0  # 双方都背叛，无收益
            else:
                if my_strategy == 1:
                    total_payoff -= 1  # 选C但邻居选D
                else:
                    total_payoff += self.payoff_D  # 选D，损失较少
        
        return total_payoff
    
    def update_all_payoffs(self):
        """更新所有智能体的收益"""
        for i in range(self.n_agents):
            self.payoffs[i] = self.get_payoff(i)
    
    def replicator_dynamics_step(self, dt=0.1):
        """
        复制动态更新
        dx_i/dt = x_i * (f_i - f_mean)
        其中f_i是策略1的收益，f_mean是平均收益
        """
        # 计算选择策略1的比例
        p = np.mean(self.strategies)
        
        # 计算采用策略1和策略0的收益
        f_1 = 0.0
        f_0 = 0.0
        
        for i in range(self.n_agents):
            payoff = self.get_payoff(i)
            if self.strategies[i] == 1:
                f_1 += payoff
            else:
                f_0 += payoff
        
        n_1 = np.sum(self.strategies)
        n_0 = self.n_agents - n_1
        
        f_mean = (f_1 + f_0) / self.n_agents
        f_1 = f_1 / n_1 if n_1 > 0 else 0
        f_0 = f_0 / n_0 if n_0 > 0 else 0
        
        # 策略1比例的变化率
        dp = p * (f_1 - f_mean) * dt
        
        # 随机更新一些智能体策略
        if np.random.random() < abs(dp) * 10:
            change_count = max(1, int(abs(dp) * self.n_agents))
            indices = np.random.choice(self.n_agents, change_count, replace=False)
            
            for idx in indices:
                if dp > 0:
                    self.strategies[idx] = 1  # 向策略1演化
                else:
                    self.strategies[idx] = 0  # 向策略0演化
        
        return p


class PublicGoodsGame(GraphGame):
    """公共品博弈
    
    每个参与者决定是否投资，公共品收益按投资比例分配
    投资成本为c，收益分配系数为r > 1
    """
    
    def __init__(self, adjacency_matrix, investment_cost=1.0, return_rate=1.5):
        super().__init__(adjacency_matrix)
        self.cost = investment_cost
        self.r = return_rate  # 回报率
    
    def get_payoff(self, agent_id):
        """计算收益"""
        my_strategy = self.strategies[agent_id]
        neighbors = self.get_neighbors(agent_id)
        
        # 计算总贡献
        total_contribution = 0.0
        if my_strategy == 1:
            total_contribution += self.cost
        
        for neighbor in neighbors:
            if self.strategies[neighbor] == 1:
                total_contribution += self.cost
        
        # 公共品收益分配（所有人平均分配）
        n_players = len(neighbors) + 1
        public_goods = total_contribution * self.r / n_players
        
        # 个人收益 = 公共品收益 - 投资成本
        if my_strategy == 1:
            return public_goods - self.cost
        else:
            return public_goods
    
    def imitation_update(self, beta=1.0):
        """
        模仿更新：智能体以概率选择邻居策略
        P(adopt) = 1 / (1 + exp(-beta * (f_j - f_i)))
        """
        new_strategies = self.strategies.copy()
        
        for i in range(self.n_agents):
            neighbors = self.get_neighbors(i)
            if len(neighbors) == 0:
                continue
            
            # 随机选择一个邻居
            j = np.random.choice(neighbors)
            
            payoff_i = self.get_payoff(i)
            payoff_j = self.get_payoff(j)
            
            # 概率采用邻居策略
            prob = 1 / (1 + np.exp(-beta * (payoff_j - payoff_i)))
            
            if np.random.random() < prob:
                new_strategies[i] = self.strategies[j]
        
        self.strategies = new_strategies


class HawkDoveGame(GraphGame):
    """鹰鸽博弈（也称斗鸡博弈）
    
    收益矩阵:
           H      D
    H    (V-C)/2  V
    D     0       V/2
    其中V是资源价值，C是冲突成本
    """
    
    def __init__(self, adjacency_matrix, resource_value=1.0, conflict_cost=2.0):
        super().__init__(adjacency_matrix)
        self.V = resource_value
        self.C = conflict_cost
    
    def get_payoff(self, agent_id):
        """计算收益"""
        my_strategy = self.strategies[agent_id]
        neighbors = self.get_neighbors(agent_id)
        
        total_payoff = 0.0
        for neighbor in neighbors:
            neighbor_strategy = self.strategies[neighbor]
            
            # Hawk-Dove收益
            if my_strategy == 1 and neighbor_strategy == 1:  # H vs H
                total_payoff += (self.V - self.C) / 2
            elif my_strategy == 1 and neighbor_strategy == 0:  # H vs D
                total_payoff += self.V
            elif my_strategy == 0 and neighbor_strategy == 1:  # D vs H
                total_payoff += 0
            else:  # D vs D
                total_payoff += self.V / 2
        
        return total_payoff


class ZDStrategyGame:
    """零行列式(ZD)策略博弈
    
    ZD策略确保即使在背叛环境下也能获得一定比例的收益
    适用于多次博弈场景
    """
    
    def __init__(self, T=1.5, R=1.0, P=0.0, S=-0.5):
        # T: 诱惑奖励
        # R: 奖励（双方合作）
        # P: 惩罚（双方背叛）
        # S: 损失（被欺骗）
        self.T = T
        self.R = R
        self.P = P
        self.S = S
    
    def expected_payoff(self, strategy_profile, n_steps=100):
        """
        计算期望收益
        strategy_profile: (my_strategy, opp_strategy) 其中strategy是概率向量 [P_C, P_D]
        """
        my_prob_coop = strategy_profile[0]
        opp_prob_coop = strategy_profile[1]
        
        # 期望收益
        # P_cc * R + P_cd * S + P_dc * T + P_dd * P
        p_cc = my_prob_coop[0] * opp_prob_coop[0]
        p_cd = my_prob_coop[0] * opp_prob_coop[1]
        p_dc = my_prob_coop[1] * opp_prob_coop[0]
        p_dd = my_prob_coop[1] * opp_prob_coop[1]
        
        expected = p_cc * self.R + p_cd * self.S + p_dc * self.T + p_dd * self.P
        
        return expected
    
    def computeZDThreshold(self, target_rate):
        """
        计算ZD策略的阈值
        使得我方获得至少target_rate比例的收益
        """
        # 简化的ZD策略计算
        # 合作概率随对手合作率线性变化
        slope = 1.0 - 2 * target_rate  # ZD控制斜率
        intercept = target_rate
        
        return slope, intercept
    
    def get_ZD_action(self, opponent_history, target_rate=0.75):
        """基于对手历史决定是否合作"""
        if len(opponent_history) == 0:
            return 1  # 初始合作
        
        # 估计对手合作概率
        coop_prob = np.mean(opponent_history)
        
        # 计算合作概率
        slope, intercept = self.computeZDThreshold(target_rate)
        cooperation_prob = max(0, min(1, intercept + slope * coop_prob))
        
        return 1 if np.random.random() < cooperation_prob else 0


class NetworkEpidemicGame:
    """网络病毒传播博弈
    
    研究如何在网络中激励节点采取防护措施
    """
    
    def __init__(self, adjacency_matrix, infection_prob=0.3, recovery_prob=0.1):
        # adjacency_matrix: 社交网络邻接矩阵
        super().__init__(adjacency_matrix)
        self.infection_prob = infection_prob
        self.recovery_prob = recovery_prob
        
        # 节点状态: 0=易感, 1=感染, 2=康复(免疫)
        self.states = np.zeros(self.n_agents, dtype=int)
        
        # 防护措施（0=无，1=防护）
        self.protection = np.zeros(self.n_agents, dtype=int)
        
        # 防护成本和效果
        self.protection_cost = 0.2
        self.protection_effect = 0.7  # 减少感染概率
    
    def set_initial_infection(self, infected_nodes):
        """设置初始感染节点"""
        for node in infected_nodes:
            self.states[node] = 1
    
    def get_payoff(self, agent_id):
        """计算收益（负的感染损失）"""
        state = self.states[agent_id]
        protected = self.protection[agent_id]
        
        if state == 2:  # 已康复
            return 0.5 - self.protection_cost * protected
        
        if state == 1:  # 感染
            return -1.0
        
        # 易感状态
        if protected:
            return -self.protection_cost
        else:
            neighbors = self.get_neighbors(agent_id)
            infected_neighbors = sum(1 for n in neighbors if self.states[n] == 1)
            
            # 感染概率
            actual_infection_prob = self.infection_prob * (1 - self.protection_effect * protected)
            infection_risk = 1 - (1 - actual_infection_prob) ** infected_neighbors
            
            return -infection_risk
    
    def step_infection(self):
        """模拟一步感染传播"""
        new_infections = []
        
        for i in range(self.n_agents):
            if self.states[i] == 0:  # 易感
                neighbors = self.get_neighbors(i)
                infected_neighbors = [n for n in neighbors if self.states[n] == 1]
                
                if infected_neighbors:
                    actual_prob = self.infection_prob
                    if self.protection[i]:
                        actual_prob *= (1 - self.protection_effect)
                    
                    if np.random.random() < actual_prob:
                        new_infections.append(i)
        
        # 应用感染
        for node in new_infections:
            self.states[node] = 1
        
        # 恢复（随机）
        for i in range(self.n_agents):
            if self.states[i] == 1 and np.random.random() < self.recovery_prob:
                self.states[i] = 2


class EvolutionaryGraphGame:
    """演化图博弈"""
    
    def __init__(self, adjacency_matrix, game_type='coordination'):
        self.graph = GraphGame(adjacency_matrix)
        self.game_type = game_type
        
        if game_type == 'coordination':
            self.game = CoordinationGame(adjacency_matrix)
        elif game_type == 'hawk_dove':
            self.game = HawkDoveGame(adjacency_matrix)
        elif game_type == 'public_goods':
            self.game = PublicGoodsGame(adjacency_matrix)
    
    def mutate_strategy(self, mutation_rate=0.01):
        """随机变异策略"""
        for i in range(self.graph.n_agents):
            if np.random.random() < mutation_rate:
                self.graph.strategies[i] = 1 - self.graph.strategies[i]
    
    def run_evolution(self, n_steps=100, verbose=True):
        """运行演化动力学"""
        print(f"\n===== 演化图博弈 ({self.game_type}) =====")
        
        for step in range(n_steps):
            self.graph.update_all_payoffs()
            
            # 复制动态更新
            if self.game_type == 'coordination':
                self.game.replicator_dynamics_step(dt=0.1)
            elif self.game_type == 'public_goods':
                self.game.imitation_update(beta=0.5)
            
            # 随机变异
            self.mutate_strategy(mutation_rate=0.01)
            
            if verbose and step % 20 == 0:
                n_cooperators = np.sum(self.graph.strategies)
                avg_payoff = np.mean(self.graph.payoffs)
                print(f"  Step {step}: 合作者={n_cooperators}/{self.graph.n_agents}, "
                      f"平均收益={avg_payoff:.3f}")
        
        return self.graph.strategies.copy()


if __name__ == "__main__":
    # 测试图博弈与网络博弈
    print("=" * 50)
    print("图博弈与网络博弈测试")
    print("=" * 50)
    
    # 创建网络拓扑（环形，10个节点）
    n = 10
    adj = np.zeros((n, n))
    for i in range(n):
        adj[i, (i + 1) % n] = 1
        adj[i, (i - 1) % n] = 1
    
    print(f"\n网络拓扑: {n}个节点环形连接")
    
    # 测试1: 协调博弈
    print("\n--- 协调博弈测试 ---")
    coord_game = CoordinationGame(adj)
    
    # 随机初始策略
    coord_game.strategies = np.random.randint(0, 2, n)
    print(f"  初始合作者数量: {np.sum(coord_game.strategies)}")
    
    # 运行演化
    for step in range(50):
        coord_game.update_all_payoffs()
        coord_game.replicator_dynamics_step(dt=0.1)
    
    print(f"  最终合作者数量: {np.sum(coord_game.strategies)}")
    
    # 测试2: 公共品博弈
    print("\n--- 公共品博弈测试 ---")
    pg_game = PublicGoodsGame(adj, investment_cost=1.0, return_rate=1.5)
    
    # 随机初始策略
    pg_game.strategies = np.random.randint(0, 2, n)
    print(f"  初始投资者数量: {np.sum(pg_game.strategies)}")
    
    # 运行演化
    for step in range(50):
        pg_game.update_all_payoffs()
        pg_game.imitation_update(beta=0.5)
    
    print(f"  最终投资者数量: {np.sum(pg_game.strategies)}")
    
    # 测试3: 演化图博弈
    print("\n--- 演化图博弈测试 ---")
    evo_game = EvolutionaryGraphGame(adj, game_type='coordination')
    final_strategies = evo_game.run_evolution(n_steps=100)
    
    print(f"  最终策略分布: 合作者={np.sum(final_strategies)}/{n}")
    
    # 测试4: ZD策略
    print("\n--- 零行列式(ZD)策略测试 ---")
    zd_game = ZDStrategyGame(T=1.5, R=1.0, P=0.0, S=-0.5)
    
    # 测试不同策略组合的收益
    profiles = [
        ([1, 0], [1, 0]),  # CC
        ([1, 0], [0, 1]),  # CD
        ([0, 1], [1, 0]),  # DC
        ([0, 1], [0, 1]),  # DD
    ]
    
    print("  期望收益:")
    for profile in profiles:
        payoff = zd_game.expected_payoff(profile)
        print(f"    {profile[0]} vs {profile[1]}: {payoff:.3f}")
    
    # 测试5: 网络流行病博弈
    print("\n--- 网络流行病博弈测试 ---")
    epidemic = NetworkEpidemicGame(adj, infection_prob=0.3, recovery_prob=0.1)
    
    # 设置初始感染
    epidemic.set_initial_infection([0, 5])
    print(f"  初始感染节点: [0, 5]")
    
    # 初始防护决策
    epidemic.protection = np.random.randint(0, 2, n)
    print(f"  初始防护节点数: {np.sum(epidemic.protection)}")
    
    # 运行传播
    for step in range(20):
        epidemic.step_infection()
        if step % 5 == 0:
            states = np.bincount(epidemic.states, minlength=3)
            print(f"  Step {step}: 易感={states[0]}, 感染={states[1]}, 康复={states[2]}")
    
    print("\n✓ 图博弈与网络博弈测试完成")
