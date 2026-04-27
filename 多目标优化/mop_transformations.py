# -*- coding: utf-8 -*-
"""
算法实现：多目标优化 / mop_transformations

本文件实现 mop_transformations 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Callable, Optional
from scipy.optimize import minimize


class WeightedSumMethod:
    """
    加权求和法
    
    将多个目标通过加权求和转化为单目标：
    min Σ w_i * f_i(x)
    s.t. w_i >= 0, Σ w_i = 1
    """
    
    def __init__(self, n_objectives: int):
        self.n_objectives = n_objectives
    
    def optimize(self, evaluate_func: Callable, 
                 weights: np.ndarray,
                 bounds: List[Tuple[float, float]],
                 x0: Optional[np.ndarray] = None) -> Tuple[np.ndarray, float]:
        """
        优化
        
        参数:
            evaluate_func: 评估函数
            weights: 权重向量
            bounds: 变量边界
            x0: 初始解
        
        返回:
            (最优解, 目标值)
        """
        weights = np.array(weights)
        weights = weights / np.sum(weights)  # 归一化
        
        def objective(x):
            obj = np.array(evaluate_func(x))
            return np.sum(weights * obj)
        
        if x0 is None:
            x0 = np.random.uniform([b[0] for b in bounds], [b[1] for b in bounds])
        
        result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
        
        return result.x, result.fun


class EpsilonConstraintMethod:
    """
    ε-约束法
    
    将部分目标转化为约束：
    min f_r(x)
    s.t. f_i(x) <= ε_i, i ≠ r
         x ∈ feasible region
    """
    
    def __init__(self, n_objectives: int):
        self.n_objectives = n_objectives
    
    def optimize(self, evaluate_func: Callable,
                 minimize_objective: int,  # 要最小化的目标索引
                 epsilon_constraints: List[Tuple[int, float]],  # (目标索引, ε值)
                 bounds: List[Tuple[float, float]],
                 x0: Optional[np.ndarray] = None) -> Tuple[np.ndarray, float]:
        """
        优化
        
        参数:
            evaluate_func: 评估函数
            minimize_objective: 要最小化的目标索引
            epsilon_constraints: 约束列表 [(目标索引, ε值), ...]
            bounds: 变量边界
        
        返回:
            (最优解, 目标值)
        """
        constraints = []
        
        for obj_idx, epsilon in epsilon_constraints:
            # 创建不等式约束：f_i(x) <= ε_i
            def make_constraint(idx, eps):
                def constraint(x):
                    obj = np.array(evaluate_func(x))
                    return obj[idx] - eps
                return {'type': 'ineq', 'fun': constraint}
            
            constraints.append(make_constraint(obj_idx, epsilon))
        
        def objective(x):
            obj = np.array(evaluate_func(x))
            return obj[minimize_objective]
        
        if x0 is None:
            x0 = np.random.uniform([b[0] for b in bounds], [b[1] for b in bounds])
        
        result = minimize(objective, x0, bounds=bounds, 
                         constraints=constraints, method='SLSQP')
        
        return result.x, result.fun


class GoalProgramming:
    """
    目标规划法
    
    设定目标值，找到最接近目标的解：
    min Σ |f_i(x) - g_i|^p
    
    p=1: Chebyshev (minimax)
    p=2: Euclidean
    """
    
    def __init__(self, n_objectives: int, p: float = 2.0):
        self.n_objectives = n_objectives
        self.p = p
    
    def optimize(self, evaluate_func: Callable,
                 goals: np.ndarray,
                 bounds: List[Tuple[float, float]],
                 x0: Optional[np.ndarray] = None,
                 weights: Optional[np.ndarray] = None) -> Tuple[np.ndarray, float]:
        """
        优化
        
        参数:
            evaluate_func: 评估函数
            goals: 目标值向量
            bounds: 变量边界
            x0: 初始解
            weights: 目标权重（可选）
        
        返回:
            (最优解, 目标值)
        """
        goals = np.array(goals)
        weights = np.array(weights) if weights is not None else np.ones(self.n_objectives)
        
        def objective(x):
            obj = np.array(evaluate_func(x))
            deviations = np.abs(obj - goals)
            
            if self.p == 1:
                return np.sum(weights * deviations)
            elif self.p == 2:
                return np.sum(weights * deviations ** 2)
            else:
                return np.sum(weights * deviations ** self.p)
        
        if x0 is None:
            x0 = np.random.uniform([b[0] for b in bounds], [b[1] for b in bounds])
        
        result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
        
        return result.x, result.fun


class HybridMethod:
    """
    混合方法：结合加权求和和目标规划
    
    策略迭代：
    1. 加权求和找到初始解
    2. 目标规划微调
    """
    
    def __init__(self, n_objectives: int):
        self.n_objectives = n_objectives
        self.weighted_sum = WeightedSumMethod(n_objectives)
        self.goal_prog = GoalProgramming(n_objectives, p=1)
    
    def optimize(self, evaluate_func: Callable,
                 bounds: List[Tuple[float, float]],
                 n_weights: int = 20,
                 n_refinements: int = 3) -> np.ndarray:
        """
        混合优化
        
        参数:
            evaluate_func: 评估函数
            bounds: 变量边界
            n_weights: 权重采样数
            n_refinements: 细化次数
        
        返回:
            Pareto近似解集
        """
        all_solutions = []
        
        # 1. 加权求和采样
        for i in range(n_weights):
            weights = np.random.dirichlet(np.ones(self.n_objectives))
            
            try:
                sol, _ = self.weighted_sum.optimize(evaluate_func, weights, bounds)
                all_solutions.append(sol)
            except:
                continue
        
        # 2. 目标规划细化
        objectives_array = np.array([evaluate_func(sol) for sol in all_solutions])
        
        for _ in range(n_refinements):
            # 从当前解集估计目标
            goals = np.min(objectives_array, axis=0)
            
            for sol in all_solutions[:5]:  # 只细化前5个
                try:
                    refined_sol, _ = self.goal_prog.optimize(evaluate_func, goals, bounds, sol)
                    all_solutions.append(refined_sol)
                except:
                    continue
        
        # 过滤重复解
        unique_solutions = []
        for sol in all_solutions:
            is_duplicate = False
            for existing in unique_solutions:
                if np.linalg.norm(sol - existing) < 1e-4:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_solutions.append(sol)
        
        return np.array(unique_solutions)


class AdaptiveWeightMethod:
    """
    自适应权重法
    
    根据当前Pareto前沿调整权重：
    - 理想点方向
    - 边界距离
    """
    
    def __init__(self, n_objectives: int):
        self.n_objectives = n_objectives
    
    def compute_weights(self, pareto_front: np.ndarray, 
                        ideal_point: np.ndarray,
                        nadir_point: np.ndarray) -> np.ndarray:
        """
        基于当前前沿计算权重向量
        
        参数:
            pareto_front: 当前Pareto前沿
            ideal_point: 理想点
            nadir_point: 最差点
        
        返回:
            权重向量数组
        """
        # 归一化方向
        range_obj = nadir_point - ideal_point
        range_obj = np.maximum(range_obj, 1e-10)
        
        # 为每个Pareto点计算权重
        n = len(pareto_front)
        weights = np.zeros((n, self.n_objectives))
        
        for i, point in enumerate(pareto_front):
            # 归一化目标
            normalized = (point - ideal_point) / range_obj
            
            # 计算权重（基于到理想点的距离）
            distances = np.zeros(self.n_objectives)
            for m in range(self.n_objectives):
                if normalized[m] > 1e-10:
                    distances[m] = 1.0 / normalized[m]
            
            weights[i] = distances / np.sum(distances)
        
        return weights


def pareto_weight_sampling(n_objectives: int, n_samples: int) -> np.ndarray:
    """
    均匀采样Pareto权重向量
    
    参数:
        n_objectives: 目标数量
        n_samples: 采样数
    
    返回:
        权重矩阵 (n_samples, n_objectives)
    """
    # 简单方法：随机Dirichlet采样
    weights = np.random.dirichlet(np.ones(n_objectives), size=n_samples)
    
    return weights


def compromise_programming(fronts: np.ndarray, ideal_point: np.ndarray,
                           nadir_point: np.ndarray) -> int:
    """
    妥协解选择（基于到理想点的最小距离）
    
    参数:
        fronts: Pareto前沿
        ideal_point: 理想点
        nadir_point: 最差点
    
    返回:
        最佳解的索引
    """
    # 归一化
    range_obj = nadir_point - ideal_point
    range_obj = np.maximum(range_obj, 1e-10)
    
    # 计算每个解到理想点的归一化距离
    normalized_fronts = (fronts - ideal_point) / range_obj
    distances = np.linalg.norm(normalized_fronts, axis=1)
    
    return np.argmin(distances)


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("多目标优化问题变换方法测试")
    print("=" * 50)
    
    np.random.seed(42)
    
    # 测试函数
    def test_func(x):
        f1 = x[0] ** 2
        f2 = (x[0] - 2) ** 2
        return [f1, f2]
    
    bounds = [(-10, 10)]
    
    print("\n--- 加权求和法 ---")
    ws = WeightedSumMethod(n_objectives=2)
    
    for w in [[0.5, 0.5], [0.2, 0.8], [0.8, 0.2]]:
        sol, val = ws.optimize(test_func, np.array(w), bounds)
        obj = test_func(sol)
        print(f"权重{w}: 解={sol[0]:.3f}, f=[{obj[0]:.3f}, {obj[1]:.3f}]")
    
    print("\n--- ε-约束法 ---")
    ec = EpsilonConstraintMethod(n_objectives=2)
    
    sol, val = ec.optimize(test_func, minimize_objective=0,
                          epsilon_constraints=[(1, 1.0)],
                          bounds=bounds)
    print(f"约束f2 <= 1.0, 最小化f1: 解={sol[0]:.3f}, f={test_func(sol)}")
    
    print("\n--- 目标规划法 ---")
    gp = GoalProgramming(n_objectives=2, p=2)
    
    goals = np.array([0.5, 0.5])
    sol, val = gp.optimize(test_func, goals, bounds)
    print(f"目标{goals}: 解={sol[0]:.3f}, f={test_func(sol)}")
    
    print("\n--- 妥协解选择 ---")
    fronts = np.array([
        [0.1, 2.0],
        [0.5, 0.5],
        [1.0, 0.1],
        [2.0, 0.0]
    ])
    ideal = np.array([0, 0])
    nadir = np.array([2, 2])
    
    best_idx = compromise_programming(fronts, ideal, nadir)
    print(f"Pareto前沿: {fronts}")
    print(f"妥协解索引: {best_idx}, 解: {fronts[best_idx]}")
    
    print("\n--- 自适应权重 ---")
    aw = AdaptiveWeightMethod(n_objectives=2)
    
    pareto = np.array([[0.1, 1.9], [0.5, 0.5], [1.0, 1.0]])
    ideal = np.array([0, 0])
    nadir = np.array([2, 2])
    
    weights = aw.compute_weights(pareto, ideal, nadir)
    print(f"Pareto前沿:\n{pareto}")
    print(f"计算权重:\n{weights}")
    
    print("\n" + "=" * 50)
    print("测试完成")
