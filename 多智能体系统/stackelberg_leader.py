# -*- coding: utf-8 -*-
"""
算法实现：多智能体系统 / stackelberg_leader

本文件实现 stackelberg_leader 相关的算法功能。
"""

import numpy as np
from scipy.optimize import minimize


class StackelbergLeader:
    """斯塔克尔伯格领导者"""
    
    def __init__(self, leader_id, strategy_bounds):
        # leader_id: 领导者ID
        # strategy_bounds: 策略边界 [(min1, max1), (min2, max2), ...]
        self.leader_id = leader_id
        self.strategy_bounds = strategy_bounds
        self.strategy = None
        self.payoff = 0.0
    
    def set_strategy(self, strategy):
        """设置领导者的策略"""
        self.strategy = np.array(strategy)
        # 限制在边界内
        for i, (s, (low, high)) in enumerate(zip(self.strategy, self.strategy_bounds)):
            self.strategy[i] = np.clip(s, low, high)
    
    def get_strategy(self):
        """获取当前策略"""
        return self.strategy.copy() if self.strategy is not None else None


class StackelbergFollower:
    """斯塔克尔伯格追随者"""
    
    def __init__(self, follower_id, strategy_bounds, leader_strategy_dim):
        # follower_id: 追随者ID
        # strategy_bounds: 策略边界
        # leader_strategy_dim: 领导者策略维度（用于构造响应函数）
        self.follower_id = follower_id
        self.strategy_bounds = strategy_bounds
        self.leader_strategy_dim = leader_strategy_dim
        self.strategy = None
        self.payoff = 0.0
    
    def best_response(self, leader_strategy):
        """
        计算对领导者策略的最佳响应
        leader_strategy: 领导者的策略
        """
        leader_strategy = np.array(leader_strategy)
        
        def objective(follower_strategy):
            follower_strategy = np.array(follower_strategy)
            # 限制在边界内
            for i, (s, (low, high)) in enumerate(zip(follower_strategy, self.strategy_bounds)):
                follower_strategy[i] = np.clip(s, low, high)
            
            self.strategy = follower_strategy
            # 计算追随者收益（简化：追随者收益与领导者策略负相关）
            payoff = -np.sum(follower_strategy ** 2) - np.sum(leader_strategy * follower_strategy)
            self.payoff = payoff
            return -payoff  # 最小化负收益
        
        # 初始化追随者策略
        x0 = [0.5 * (b[0] + b[1]) for b in self.strategy_bounds]
        
        result = minimize(objective, x0=x0, method='L-BFGS-B',
                         bounds=self.strategy_bounds)
        
        self.strategy = np.array(result.x)
        self.payoff = -result.fun
        
        return self.strategy.copy()
    
    def get_strategy(self):
        """获取当前策略"""
        return self.strategy.copy() if self.strategy is not None else None


class StackelbergGame:
    """斯塔克尔伯格博弈主类"""
    
    def __init__(self):
        # 领导者
        self.leader = None
        # 追随者列表
        self.followers = []
        # 收益函数参数
        self.alpha = 1.0  # 领导者收益系数
        self.beta = 0.5  # 追随者对领导者收益的影响
    
    def set_leader(self, leader):
        """设置领导者"""
        self.leader = leader
    
    def add_follower(self, follower):
        """添加追随者"""
        self.followers.append(follower)
    
    def leader_payoff(self, leader_strategy, follower_strategies):
        """
        计算领导者收益
        leader_strategy: 领导者策略
        follower_strategies: 追随者策略列表
        """
        leader_strategy = np.array(leader_strategy)
        follower_strategies = np.array(follower_strategies)
        
        # 简化收益函数：L = a*L^2 - b*sum(F_i)
        payoff = -self.alpha * np.sum(leader_strategy ** 2)
        payoff -= self.beta * np.sum(follower_strategies ** 2)
        # 追随者策略对领导者有害
        payoff -= np.sum(leader_strategy * np.sum(follower_strategies, axis=0))
        
        return payoff
    
    def solve(self, method='backward_induction'):
        """
        求解斯塔克尔伯格均衡
        method: 'backward_induction' 或 'mathematical_programming'
        """
        print("\n===== 斯塔克尔伯格博弈求解 =====")
        
        if method == 'backward_induction':
            return self._backward_induction()
        else:
            return self._mathematical_programming()
    
    def _backward_induction(self):
        """逆向归纳法求解"""
        print("  使用逆向归纳法...")
        
        # 对每个可能的领导者策略，计算追随者的最佳响应
        # 然后选择领导者最优的策略
        
        # 简化：离散化领导者策略空间
        n_points = 20
        best_leader_payoff = -np.inf
        best_leader_strategy = None
        best_follower_strategies = None
        
        # 遍历领导者策略空间
        for i in range(n_points):
            for j in range(n_points):
                # 生成领导者策略
                leader_strategy = np.array([
                    self.leader.strategy_bounds[0][0] + 
                    (self.leader.strategy_bounds[0][1] - self.leader.strategy_bounds[0][0]) * i / n_points,
                    self.leader.strategy_bounds[1][0] + 
                    (self.leader.strategy_bounds[1][1] - self.leader.strategy_bounds[1][0]) * j / n_points
                ])
                
                # 计算每个追随者的最佳响应
                follower_strategies = []
                for follower in self.followers:
                    fs = follower.best_response(leader_strategy)
                    follower_strategies.append(fs)
                
                # 计算领导者收益
                leader_payoff = self.leader_payoff(leader_strategy, follower_strategies)
                
                if leader_payoff > best_leader_payoff:
                    best_leader_payoff = leader_payoff
                    best_leader_strategy = leader_strategy.copy()
                    best_follower_strategies = [fs.copy() for fs in follower_strategies]
        
        # 设置最优策略
        self.leader.set_strategy(best_leader_strategy)
        self.leader.payoff = best_leader_payoff
        
        for follower, fs in zip(self.followers, best_follower_strategies):
            follower.strategy = fs
        
        return self._extract_equilibrium()
    
    def _mathematical_programming(self):
        """数学规划法求解"""
        print("  使用数学规划法...")
        
        # 将斯塔克尔伯格问题转化为非线性规划
        # 目标：最大化领导者收益
        # 约束：追随者的KKT条件
        
        n_followers = len(self.followers)
        n_leader_vars = len(self.leader.strategy_bounds)
        
        # 简化方法：网格搜索
        return self._backward_induction()
    
    def _extract_equilibrium(self):
        """提取均衡结果"""
        return {
            'leader_strategy': self.leader.get_strategy(),
            'leader_payoff': self.leader.payoff,
            'follower_strategies': [f.get_strategy() for f in self.followers],
            'follower_payoffs': [f.payoff for f in self.followers],
            'n_followers': len(self.followers)
        }


class BilevelOptimizer:
    """双层优化器：处理斯塔克尔伯格结构的通用框架"""
    
    def __init__(self, upper_dim, lower_dim):
        # upper_dim: 上层（领导者）决策维度
        # lower_dim: 下层（追随者）决策维度
        self.upper_dim = upper_dim
        self.lower_dim = lower_dim
    
    def upper_level_objective(self, upper_vars, lower_solution):
        """上层目标函数"""
        upper_vars = np.array(upper_vars)
        lower_solution = np.array(lower_solution)
        return -np.sum(upper_vars ** 2) - np.sum(upper_vars * lower_solution)
    
    def lower_level_problem(self, upper_vars):
        """下层问题：追随者的最佳响应"""
        upper_vars = np.array(upper_vars)
        
        def objective(lower_vars):
            lower_vars = np.array(lower_vars)
            return np.sum(lower_vars ** 2) + np.sum(upper_vars * lower_vars)
        
        # 简化的解析解
        lower_solution = -0.5 * upper_vars
        return lower_solution
    
    def solve(self, n_iterations=100):
        """求解双层优化问题"""
        print("\n===== 双层优化求解 =====")
        
        upper_vars = np.random.randn(self.upper_dim) * 0.5
        
        for iteration in range(n_iterations):
            # 下层：计算最佳响应
            lower_solution = self.lower_level_problem(upper_vars)
            
            # 上层：梯度上升
            gradient = -2 * upper_vars - np.sum(lower_solution)
            step_size = 0.1 / (1 + iteration * 0.1)
            upper_vars += step_size * gradient
            
            if iteration % 20 == 0:
                upper_obj = self.upper_level_objective(upper_vars, lower_solution)
                print(f"  迭代{iteration}: upper_obj={upper_obj:.4f}")
        
        return {
            'upper_solution': upper_vars,
            'lower_solution': lower_solution,
            'upper_objective': self.upper_level_objective(upper_vars, lower_solution)
        }


if __name__ == "__main__":
    # 测试斯塔克尔伯格博弈
    print("=" * 50)
    print("斯塔克尔伯格博弈测试")
    print("=" * 50)
    
    # 创建博弈
    game = StackelbergGame()
    
    # 设置领导者（策略空间[0,5] x [0,5]）
    leader = StackelbergLeader(0, [(0, 5), (0, 5)])
    game.set_leader(leader)
    
    # 添加追随者
    follower1 = StackelbergFollower(0, [(0, 3), (0, 3)], leader_strategy_dim=2)
    follower2 = StackelbergFollower(1, [(0, 4), (0, 4)], leader_strategy_dim=2)
    game.add_follower(follower1)
    game.add_follower(follower2)
    
    print(f"\n博弈结构:")
    print(f"  领导者: 策略维度={len(leader.strategy_bounds)}, 策略空间={leader.strategy_bounds}")
    print(f"  追随者数量: {len(game.followers)}")
    
    # 求解
    equilibrium = game.solve(method='backward_induction')
    
    print(f"\n===== 均衡结果 =====")
    print(f"  领导者策略: {equilibrium['leader_strategy']}")
    print(f"  领导者收益: {equilibrium['leader_payoff']:.4f}")
    for i, (fs, fp) in enumerate(zip(
            equilibrium['follower_strategies'], equilibrium['follower_payoffs'])):
        print(f"  追随者{i}策略: {fs}, 收益: {fp:.4f}")
    
    # 测试双层优化器
    print("\n--- 双层优化器测试 ---")
    bilevel = BilevelOptimizer(upper_dim=3, lower_dim=3)
    result = bilevel.solve(n_iterations=50)
    
    print(f"  上层解: {result['upper_solution']}")
    print(f"  下层解: {result['lower_solution']}")
    print(f"  上层目标: {result['upper_objective']:.4f}")
    
    print("\n✓ 斯塔克尔伯格博弈测试完成")
