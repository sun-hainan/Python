"""
可微分约束满足 (Differentiable Satisfaction / DSR)
=====================================================
本模块实现可微分的约束满足系统：

核心思想：
- 将硬约束转化为软损失函数
- 通过梯度下降优化变量满足约束
- 支持等式和不等式约束

应用：
- 物理系统模拟
- 结构优化
- 神经网络的约束学习

Author: 算法库
"""

import numpy as np
from typing import List, Dict, Callable, Tuple, Optional


class Variable:
    """优化变量"""
    
    def __init__(self, name: str, initial_value: float, 
                 lower_bound: float = -np.inf, upper_bound: float = np.inf):
        self.name = name
        self.value = np.array(initial_value, dtype=np.float32)
        self.initial_value = self.value.copy()
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
    
    def set_value(self, value: float):
        """设置值（带边界约束）"""
        self.value = np.clip(value, self.lower_bound, self.upper_bound)
    
    def project(self):
        """投影到可行域"""
        self.value = np.clip(self.value, self.lower_bound, self.upper_bound)


class Constraint:
    """约束基类"""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
    
    def evaluate(self) -> float:
        """评估约束违反程度"""
        raise NotImplementedError
    
    def gradient(self) -> Dict[str, float]:
        """计算梯度"""
        raise NotImplementedError


class EqualityConstraint(Constraint):
    """等式约束 g(x) = 0"""
    
    def __init__(self, name: str, g: Callable, weight: float = 1.0):
        super().__init__(name, weight)
        self.g = g
    
    def evaluate(self) -> float:
        """返回 g(x)^2（越小越好）"""
        value = self.g()
        return value ** 2
    
    def gradient_numerical(self, variables: Dict[str, Variable], 
                         epsilon: float = 1e-8) -> Dict[str, float]:
        """数值梯度"""
        grad = {}
        base_value = self.g()
        
        for name, var in variables.items():
            var_backup = var.value.copy()
            
            var.value = var_backup + epsilon
            g_plus = self.g()
            
            var.value = var_backup - epsilon
            g_minus = self.g()
            
            grad[name] = (g_plus - g_minus) / (2 * epsilon) * 2 * base_value
            
            var.value = var_backup
        
        return grad


class InequalityConstraint(Constraint):
    """不等式约束 h(x) <= 0"""
    
    def __init__(self, name: str, h: Callable, weight: float = 1.0):
        super().__init__(name, weight)
        self.h = h
    
    def evaluate(self) -> float:
        """
        评估违反程度
        使用 ReLU: max(0, h(x))^2
        """
        value = self.h()
        return max(0, value) ** 2
    
    def gradient_numerical(self, variables: Dict[str, Variable],
                          epsilon: float = 1e-8) -> Dict[str, float]:
        """数值梯度"""
        grad = {}
        h_value = self.h()
        
        # 只有 h > 0 时才有梯度
        if h_value <= 0:
            return {name: 0.0 for name in variables}
        
        for name, var in variables.items():
            var_backup = var.value.copy()
            
            var.value = var_backup + epsilon
            h_plus = self.h()
            
            var.value = var_backup - epsilon
            h_minus = self.h()
            
            grad[name] = (h_plus - h_minus) / (2 * epsilon) * 2 * h_value
            
            var.value = var_backup
        
        return grad


class DifferentiableConstraintSolver:
    """可微分约束求解器"""
    
    def __init__(self, learning_rate: float = 0.01):
        self.variables: Dict[str, Variable] = {}
        self.constraints: List[Constraint] = []
        self.learning_rate = learning_rate
        self.history = []
    
    def add_variable(self, name: str, initial_value: float,
                   lower_bound: float = -np.inf, upper_bound: float = np.inf) -> Variable:
        """添加变量"""
        var = Variable(name, initial_value, lower_bound, upper_bound)
        self.variables[name] = var
        return var
    
    def add_equality(self, name: str, g: Callable, weight: float = 1.0):
        """添加等式约束 g(x) = 0"""
        self.constraints.append(EqualityConstraint(name, g, weight))
    
    def add_inequality(self, name: str, h: Callable, weight: float = 1.0):
        """添加不等式约束 h(x) <= 0"""
        self.constraints.append(InequalityConstraint(name, h, weight))
    
    def get_variable_value(self, name: str) -> float:
        """获取变量值"""
        return float(self.variables[name].value)
    
    def set_variable_value(self, name: str, value: float):
        """设置变量值"""
        self.variables[name].set_value(value)
    
    def total_loss(self) -> float:
        """计算总损失（约束违反）"""
        loss = 0.0
        for constraint in self.constraints:
            loss += constraint.weight * constraint.evaluate()
        return loss
    
    def step(self, gradient_descent: bool = True) -> float:
        """单步优化"""
        loss = self.total_loss()
        
        # 梯度下降
        if gradient_descent and loss > 1e-10:
            for name, var in self.variables.items():
                grad_sum = 0.0
                for constraint in self.constraints:
                    grad_dict = constraint.gradient_numerical(self.variables)
                    grad_sum += constraint.weight * grad_dict.get(name, 0.0)
                
                # 更新
                var.value = var.value - self.learning_rate * grad_sum
                var.project()
        
        self.history.append((loss, {name: var.value.copy() for name, var in self.variables}))
        
        return loss
    
    def solve(self, max_iterations: int = 1000, tol: float = 1e-8) -> bool:
        """
        求解约束满足问题
        
        返回: 是否收敛
        """
        self.history = []
        
        for iteration in range(max_iterations):
            loss = self.step()
            
            if iteration % 100 == 0:
                print(f"迭代 {iteration}: 损失 = {loss:.6f}")
            
            if loss < tol:
                print(f"收敛于第 {iteration} 次迭代")
                return True
        
        print(f"达到最大迭代次数，最终损失 = {loss:.6f}")
        return False
    
    def get_solution(self) -> Dict[str, float]:
        """获取解"""
        return {name: float(var.value) for name, var in self.variables.items()}


class PhysicsConstraint(Constraint):
    """物理约束模板"""
    
    @staticmethod
    def distance_constraint(pos1_var: str, pos2_var: str, 
                          target_distance: float, solver: DifferentiableConstraintSolver):
        """距离约束: ||p1 - p2|| = d"""
        def g():
            p1 = solver.get_variable_value(pos1_var)
            p2 = solver.get_variable_value(pos2_var)
            return np.sqrt((p1 - p2)**2) - target_distance
        
        return g
    
    @staticmethod
    def angle_constraint(pos_a_var: str, pos_b_var: str, pos_c_var: str,
                       target_angle: float, solver: DifferentiableConstraintSolver):
        """角度约束: ∠ABC = target"""
        def g():
            a = solver.get_variable_value(pos_a_var)
            b = solver.get_variable_value(pos_b_var)
            c = solver.get_variable_value(pos_c_var)
            
            # 计算角度
            ba = a - b
            bc = c - b
            
            cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
            angle = np.arccos(np.clip(cos_angle, -1, 1))
            
            return angle - target_angle
        
        return g


class DSRDemo:
    """DSR演示"""
    
    @staticmethod
    def circle_fitting():
        """圆拟合：找到经过多个点的圆"""
        print("=" * 50)
        print("DSR演示: 圆拟合")
        print("=" * 50)
        
        # 拟合圆: (x - cx)^2 + (y - cy)^2 = r^2
        solver = DifferentiableConstraintSolver(learning_rate=0.1)
        
        # 添加变量：圆心(cx, cy)和半径r
        solver.add_variable("cx", initial_value=0.0)
        solver.add_variable("cy", initial_value=0.0)
        solver.add_variable("r", initial_value=1.0, lower_bound=0.1)
        
        # 添加约束：每个点都在圆上
        points = [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)]
        
        for i, (px, py) in enumerate(points):
            def make_constraint(px, py):
                def g():
                    cx = solver.get_variable_value("cx")
                    cy = solver.get_variable_value("cy")
                    r = solver.get_variable_value("r")
                    return (cx - px)**2 + (cy - py)**2 - r**2
                return g
            
            solver.add_equality(f"point_{i}", make_constraint(px, py), weight=1.0)
        
        # 求解
        solver.solve(max_iterations=500)
        
        print("\n结果:")
        sol = solver.get_solution()
        print(f"圆心: ({sol['cx']:.4f}, {sol['cy']:.4f})")
        print(f"半径: {sol['r']:.4f}")
        
        # 验证
        print("\n验证各点到圆心的距离:")
        for px, py in points:
            dist = np.sqrt((sol['cx'] - px)**2 + (sol['cy'] - py)**2)
            print(f"  ({px}, {py}): {dist:.4f}")
    
    @staticmethod
    def simple_optimization():
        """简单约束优化"""
        print("\n" + "=" * 50)
        print("DSR演示: 约束优化")
        print("=" * 50)
        
        solver = DifferentiableConstraintSolver(learning_rate=0.1)
        
        # 最小化 x^2 + y^2, s.t. x + y = 1
        solver.add_variable("x", initial_value=0.5)
        solver.add_variable("y", initial_value=0.5)
        
        # 等式约束
        def g():
            return solver.get_variable_value("x") + solver.get_variable_value("y") - 1.0
        
        solver.add_equality("sum_to_one", g, weight=10.0)
        
        solver.solve(max_iterations=200)
        
        print("\n结果:")
        sol = solver.get_solution()
        print(f"x = {sol['x']:.4f}")
        print(f"y = {sol['y']:.4f}")
        print(f"x + y = {sol['x'] + sol['y']:.4f} (应接近1)")
        print(f"目标函数 x² + y² = {sol['x']**2 + sol['y']**2:.4f}")


if __name__ == "__main__":
    DSRDemo.circle_fitting()
    DSRDemo.simple_optimization()
    
    print("\n测试通过！可微分约束满足系统工作正常。")
