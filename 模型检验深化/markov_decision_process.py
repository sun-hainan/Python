"""
马尔可夫决策过程 (Markov Decision Process)
==========================================
功能：对MDP进行建模和分析
支持策略生成、价值迭代、最优性验证

核心概念：
1. MDP五元组: (S, A, P, R, s₀)
2. 策略(Policy): 状态→动作选择
3. 价值函数 V(s): 从状态s开始的期望累计回报
4. Q函数 Q(s,a): 在状态s执行动作a的期望回报

算法：
1. 值迭代(Value Iteration)
2. 策略迭代(Policy Iteration)
3. 线性规划(Linear Programming)
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
import math


@dataclass
class MDP:
    """
    马尔可夫决策过程
    - states: 状态集合
    - actions: 动作集合
    - init_state: 初始状态
    - trans_probs: P(s'|s,a) 转移概率
    - reward_func: R(s,a) 立即回报
    - gamma: 折扣因子
    """
    states: Set[Any]
    actions: Set[Any]
    init_state: Any
    trans_probs: Dict[Tuple[Any, Any], Dict[Any, float]]  # (s,a) → {s': p}
    reward_func: Dict[Tuple[Any, Any], float]              # R(s,a)
    gamma: float = 0.9


@dataclass
class Policy:
    """
    确定性策略
    π(s) = 选择的动作
    """
    action_map: Dict[Any, Any]                   # 状态→动作


@dataclass
class ValueFunction:
    """价值函数"""
    values: Dict[Any, float]                      # V(s)
    q_values: Dict[Tuple[Any, Any], float]        # Q(s,a)


class MDPSolver:
    """
    MDP求解器
    支持值迭代、策略迭代
    """
    
    def __init__(self, mdp: MDP):
        self.mdp = mdp
    
    def value_iteration(
        self,
        epsilon: float = 1e-6,
        max_iterations: int = 1000
    ) -> ValueFunction:
        """
        值迭代算法
        
        迭代公式:
        V_{k+1}(s) = max_a Σ_{s'} P(s'|s,a) [R(s,a) + γV_k(s')]
        
        Args:
            epsilon: 收敛阈值
            max_iterations: 最大迭代次数
        
        Returns:
            ValueFunction: 最优价值函数
        """
        print(f"[值迭代] 开始求解 MDP (γ={self.mdp.gamma})")
        
        # 初始化价值函数
        V = {s: 0.0 for s in self.mdp.states}
        
        for iteration in range(max_iterations):
            delta = 0.0
            V_new = V.copy()
            
            for s in self.mdp.states:
                # 计算每个动作的Q值
                q_values = []
                for a in self.mdp.actions:
                    q = self._compute_q(s, a, V)
                    q_values.append(q)
                
                # 取最大Q值
                if q_values:
                    V_new[s] = max(q_values)
                
                # 更新delta
                delta = max(delta, abs(V_new[s] - V[s]))
            
            V = V_new
            
            if delta < epsilon:
                print(f"[值迭代] 收敛于迭代 {iteration + 1}, δ={delta:.2e}")
                break
        
        # 计算最终的Q值
        Q = {}
        for s in self.mdp.states:
            for a in self.mdp.actions:
                Q[(s, a)] = self._compute_q(s, a, V)
        
        return ValueFunction(values=V, q_values=Q)
    
    def _compute_q(self, s: Any, a: Any, V: Dict[Any, float]) -> float:
        """计算Q(s,a)"""
        key = (s, a)
        
        # 获取转移概率
        trans = self.mdp.trans_probs.get(key, {})
        reward = self.mdp.reward_func.get(key, 0.0)
        
        q = reward
        for sp, prob in trans.items():
            q += prob * self.mdp.gamma * V.get(sp, 0.0)
        
        return q
    
    def policy_iteration(self, initial_policy: Optional[Policy] = None) -> Tuple[Policy, ValueFunction]:
        """
        策略迭代算法
        
        1. 策略评估: 给定π，计算V_π
        2. 策略改进: 更新π(s) = argmax_a Q(s,a)
        3. 重复直到收敛
        
        Args:
            initial_policy: 初始策略
        
        Returns:
            (最优策略, 价值函数)
        """
        print(f"[策略迭代] 开始求解 MDP")
        
        # 初始化策略
        if initial_policy is None:
            policy = Policy(action_map={
                s: list(self.mdp.actions)[0] for s in self.mdp.states
            })
        else:
            policy = initial_policy
        
        for iteration in range(1000):
            print(f"[策略迭代] 迭代 {iteration + 1}")
            
            # 策略评估
            V = self._evaluate_policy(policy)
            
            # 策略改进
            policy_stable = True
            new_action_map = {}
            
            for s in self.mdp.states:
                # 计算当前动作的Q值
                current_a = policy.action_map[s]
                current_q = self._compute_q(s, current_a, V)
                
                # 寻找更好的动作
                best_a = current_a
                best_q = current_q
                
                for a in self.mdp.actions:
                    q = self._compute_q(s, a, V)
                    if q > best_q:
                        best_q = q
                        best_a = a
                        policy_stable = False
                
                new_action_map[s] = best_a
            
            policy = Policy(action_map=new_action_map)
            
            if policy_stable:
                print(f"[策略迭代] 策略收敛于迭代 {iteration + 1}")
                break
        
        # 最终评估
        V = self._evaluate_policy(policy)
        Q = {}
        for s in self.mdp.states:
            for a in self.mdp.actions:
                Q[(s, a)] = self._compute_q(s, a, V)
        
        return policy, ValueFunction(values=V, q_values=Q)
    
    def _evaluate_policy(self, policy: Policy) -> Dict[Any, float]:
        """策略评估：求解线性方程组 V = R_π + γP_π V"""
        n = len(self.mdp.states)
        states_list = list(self.mdp.states)
        V = {s: 0.0 for s in self.mdp.states}
        
        # 迭代评估
        for _ in range(1000):
            delta = 0.0
            V_new = V.copy()
            
            for i, s in enumerate(states_list):
                a = policy.action_map[s]
                q = self._compute_q(s, a, V)
                V_new[s] = q
                delta = max(delta, abs(V_new[s] - V[s]))
            
            V = V_new
            if delta < 1e-8:
                break
        
        return V
    
    def extract_optimal_policy(self, V: ValueFunction) -> Policy:
        """
        从价值函数提取最优策略
        
        Args:
            V: 价值函数
        
        Returns:
            最优策略
        """
        action_map = {}
        
        for s in self.mdp.states:
            best_a = None
            best_q = float('-inf')
            
            for a in self.mdp.actions:
                q = V.q_values.get((s, a), 0.0)
                if q > best_q:
                    best_q = q
                    best_a = a
            
            action_map[s] = best_a
        
        return Policy(action_map=action_map)


class MDPVerifier:
    """
    MDP验证器
    验证概率性质
    """
    
    def __init__(self, mdp: MDP):
        self.mdp = mdp
    
    def verify_probability_bound(
        self,
        target_states: Set[Any],
        threshold: float,
        policy: Policy
    ) -> Tuple[bool, float]:
        """
        验证在给定策略下达到目标的概率是否超过阈值
        
        Args:
            target_states: 目标状态集合
            threshold: 概率下界
            policy: 策略
        
        Returns:
            (是否满足, 实际概率)
        """
        print(f"[MDP验证] 检查 P≥{threshold} [Reach target]")
        
        # 构建诱导的DTMC
        dtmc_trans = {}
        for s in self.mdp.states:
            a = policy.action_map[s]
            key = (s, a)
            dtmc_trans[s] = self.mdp.trans_probs.get(key, {})
        
        # 值迭代计算可达概率
        V = {s: 1.0 if s in target_states else 0.0 for s in self.mdp.states}
        
        for iteration in range(1000):
            delta = 0.0
            V_new = V.copy()
            
            for s in self.mdp.states:
                if s in target_states:
                    V_new[s] = 1.0
                else:
                    a = policy.action_map[s]
                    prob = 0.0
                    for sp, p in dtmc_trans.get(s, {}).items():
                        prob += p * V[sp]
                    V_new[s] = prob
                    delta = max(delta, abs(V_new[s] - V[s]))
            
            V = V_new
            if delta < 1e-8:
                break
        
        actual_prob = V.get(self.mdp.init_state, 0.0)
        satisfies = actual_prob >= threshold
        
        print(f"[MDP验证] 实际概率: {actual_prob:.4f}, 结果: {'满足' if satisfies else '不满足'}")
        
        return satisfies, actual_prob


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("MDP分析测试")
    print("=" * 50)
    
    # 构建简单MDP
    states = {"s0", "s1", "s2", "s3"}
    actions = {"a1", "a2"}
    
    trans_probs = {
        ("s0", "a1"): {"s0": 0.5, "s1": 0.5},
        ("s0", "a2"): {"s0": 0.3, "s2": 0.7},
        ("s1", "a1"): {"s1": 1.0},
        ("s1", "a2"): {"s2": 1.0},
        ("s2", "a1"): {"s3": 1.0},
        ("s2", "a2"): {"s0": 0.5, "s3": 0.5},
        ("s3", "a1"): {"s3": 1.0},
        ("s3", "a2"): {"s3": 1.0},
    }
    
    reward_func = {
        ("s0", "a1"): 1.0,
        ("s0", "a2"): 2.0,
        ("s1", "a1"): 0.0,
        ("s1", "a2"): 5.0,
        ("s2", "a1"): 3.0,
        ("s2", "a2"): 1.0,
        ("s3", "a1"): 10.0,
        ("s3", "a2"): 10.0,
    }
    
    mdp = MDP(
        states=states,
        actions=actions,
        init_state="s0",
        trans_probs=trans_probs,
        reward_func=reward_func,
        gamma=0.9
    )
    
    print(f"\nMDP模型:")
    print(f"  状态数: {len(states)}")
    print(f"  动作数: {len(actions)}")
    
    # 值迭代
    print("\n值迭代:")
    solver = MDPSolver(mdp)
    V = solver.value_iteration()
    print(f"  最优价值:")
    for s, v in V.values.items():
        print(f"    V({s}) = {v:.4f}")
    
    # 提取最优策略
    print("\n最优策略:")
    optimal_policy = solver.extract_optimal_policy(V)
    for s, a in optimal_policy.action_map.items():
        print(f"    π({s}) = {a}")
    
    # 策略迭代
    print("\n策略迭代:")
    policy, V_pi = solver.policy_iteration()
    print(f"  最优策略:")
    for s, a in policy.action_map.items():
        print(f"    π({s}) = {a}")
    
    # 验证
    print("\nMDP验证:")
    verifier = MDPVerifier(mdp)
    verifier.verify_probability_bound({"s3"}, 0.5, optimal_policy)
    
    print("\n✓ MDP分析测试完成")
