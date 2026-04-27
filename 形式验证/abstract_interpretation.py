# -*- coding: utf-8 -*-
"""
算法实现：形式验证 / abstract_interpretation

本文件实现 abstract_interpretation 相关的算法功能。
"""

import numpy as np
from collections import defaultdict


class Interval:
    """
    区间抽象域
    
    表示: [a, b] 表示 a <= x <= b
    包含特殊值: [-∞, +∞] 表示未知/任意值
    """
    
    def __init__(self, low=-float('inf'), high=float('inf')):
        self.low = low
        self.high = high
    
    def __repr__(self):
        if self.low == -float('inf') and self.high == float('inf'):
            return "[-∞, +∞]"
        return f"[{self.low}, {self.high}]"
    
    def __eq__(self, other):
        return self.low == other.low and self.high == other.high
    
    def is_top(self):
        """是否是最上界（任意值）"""
        return self.low == -float('inf') and self.high == float('inf')
    
    def is_bottom(self):
        """是否是最下界（空）"""
        return self.low > self.high
    
    def contains(self, val):
        """检查区间是否包含值"""
        return self.low <= val <= self.high
    
    @staticmethod
    def bottom():
        """空区间"""
        return Interval(float('inf'), float('-inf'))
    
    @staticmethod
    def top():
        """任意区间"""
        return Interval()
    
    def lub(self, other):
        """
        最小上界（Least Upper Bound）
        
        合并两个区间，取并集
        """
        if self.is_bottom():
            return other
        if other.is_bottom():
            return self
        
        return Interval(
            min(self.low, other.low),
            max(self.high, other.high)
        )
    
    def glb(self, other):
        """
        最大下界（Greatest Lower Bound）
        
        交集
        """
        new_low = max(self.low, other.low)
        new_high = min(self.high, other.high)
        
        if new_low > new_high:
            return Interval.bottom()
        
        return Interval(new_low, new_high)
    
    def widening(self, other, threshold=100):
        """
        膨胀算子（Widening）
        
        确保迭代终止：从other继承下界，膨胀上界
        """
        new_low = self.low if self.low <= other.low else float('-inf')
        new_high = self.high if self.high >= other.high else float('inf')
        
        # 应用阈值防止溢出
        if new_high > threshold:
            new_high = float('inf')
        
        return Interval(new_low, new_high)
    
    def apply_assign(self, expr, env):
        """
        应用赋值语句的抽象解释
        
        参数:
            expr: 表达式
            env: 当前环境（变量->区间）
        """
        if isinstance(expr, tuple):
            op = expr[0]
            
            if op == 'var':
                return env.get(expr[1], Interval.top())
            
            elif op == 'const':
                val = expr[1]
                return Interval(val, val)
            
            elif op == '+':
                left = self.apply_assign(expr[1], env)
                right = self.apply_assign(expr[2], env)
                return Interval(left.low + right.low, left.high + right.high)
            
            elif op == '-':
                left = self.apply_assign(expr[1], env)
                right = self.apply_assign(expr[2], env)
                return Interval(left.low - right.high, left.high - right.low)
            
            elif op == '*':
                left = self.apply_assign(expr[1], env)
                right = self.apply_assign(expr[2], env)
                # 简化：假设正数
                return Interval(left.low * right.low, left.high * right.high)
            
            elif op == '/':
                left = self.apply_assign(expr[1], env)
                right = self.apply_assign(expr[2], env)
                if right.low <= 0 <= right.high:
                    return Interval.top()  # 除以包含0的区间
                return Interval(left.low / right.high, left.high / right.low)
        
        return Interval.top()
    
    def apply_guard(self, condition, env):
        """
        应用守卫条件（if/assume）的抽象解释
        
        返回满足条件的变量区间更新
        """
        if isinstance(condition, tuple):
            op = condition[0]
            
            if op == '==':
                left = self.apply_assign(condition[1], env)
                right = self.apply_assign(condition[2], env)
                return left.glb(right)
            
            elif op == '!=':
                # 不等式不做精确处理
                return self
            
            elif op == '<':
                left = self.apply_assign(condition[1], env)
                right = self.apply_assign(condition[2], env)
                # x < y 意味着 x.high < y.high
                return Interval(self.low, min(self.high, right.high - 1))
            
            elif op == '<=':
                left = self.apply_assign(condition[1], env)
                right = self.apply_assign(condition[2], env)
                return Interval(self.low, min(self.high, right.high))
            
            elif op == '>':
                left = self.apply_assign(condition[1], env)
                right = self.apply_assign(condition[2], env)
                return Interval(max(self.low, right.low + 1), self.high)
            
            elif op == '>=':
                left = self.apply_assign(condition[1], env)
                right = self.apply_assign(condition[2], env)
                return Interval(max(self.low, right.low), self.high)
            
            elif op == '&&':
                left_env = self.apply_guard(condition[1], env)
                right_env = self.apply_guard(condition[2], env)
                return left_env.glb(right_env)
        
        return self


class AbstractInterpretation:
    """
    抽象解释框架
    
    分析程序的不变量
    """
    
    def __init__(self):
        self.program = None
        self.variables = set()
    
    def analyze(self, program, max_iter=20):
        """
        分析程序并计算不变量
        
        参数:
            program: 程序语句列表
            max_iter: 最大迭代次数
        
        返回:
            不变量映射（变量名 -> 区间）
        """
        # 初始化：所有变量为top（任意值）
        inv = {var: Interval.top() for var in self.variables}
        inv['⊤'] = Interval.top()  # 控制流顶
        
        for iteration in range(max_iter):
            new_inv = inv.copy()
            
            for stmt in program:
                new_inv = self._transfer(stmt, new_inv)
            
            # 检测收敛
            converged = True
            for var in new_inv:
                if var in inv and new_inv[var] != inv[var]:
                    converged = False
                    break
            
            if converged:
                print(f"  迭代{iteration + 1}次后收敛")
                return new_inv
            
            inv = new_inv
        
        print(f"  达到最大迭代次数{max_iter}")
        return inv
    
    def _transfer(self, stmt, inv):
        """
        转移函数
        
        应用一条语句，更新不变量
        """
        stmt_type = stmt[0]
        
        if stmt_type == 'assign':
            var, expr = stmt[1], stmt[2]
            new_interval = Interval.top().apply_assign(expr, inv)
            inv = inv.copy()
            inv[var] = new_interval
        
        elif stmt_type == 'if':
            cond = stmt[1]
            then_stmts = stmt[2] if len(stmt) > 2 else []
            else_stmts = stmt[3] if len(stmt) > 3 else []
            
            # 分别分析两个分支
            then_inv = inv.copy()
            for s in then_stmts:
                then_inv = self._transfer(s, then_inv)
            
            else_inv = inv.copy()
            for s in else_stmts:
                else_inv = self._transfer(s, else_inv)
            
            # 合并结果
            for var in set(list(then_inv.keys()) + list(else_inv.keys())):
                t_val = then_inv.get(var, Interval.top())
                e_val = else_inv.get(var, Interval.top())
                inv[var] = t_val.lub(e_val)
        
        elif stmt_type == 'while':
            cond = stmt[1]
            body = stmt[2]
            
            # 初始化循环不变量为top
            loop_inv = {var: Interval.top() for var in inv}
            
            # 迭代计算循环不变量
            for _ in range(10):  # 简化：固定迭代
                # 应用循环体
                body_inv = loop_inv.copy()
                for s in body:
                    body_inv = self._transfer(s, body_inv)
                
                # 应用守卫条件
                for var in body_inv:
                    body_inv[var] = body_inv[var].apply_guard(cond, body_inv)
                
                # 膨胀
                old_inv = loop_inv
                loop_inv = {
                    var: old_inv.get(var, Interval.top()).widening(
                        body_inv.get(var, Interval.top())
                    )
                    for var in set(list(old_inv.keys()) + list(body_inv.keys()))
                }
                
                # 检查收敛
                if all(
                    loop_inv.get(var, Interval.top()) == old_inv.get(var, Interval.top())
                    for var in set(list(old_inv.keys()) + list(loop_inv.keys()))
                ):
                    break
            
            inv = loop_inv
        
        return inv


class Polyhedron:
    """
    多面体抽象域（简化版）
    
    使用线性不等式表示区域
    """
    
    def __init__(self, constraints=None):
        """
        初始化多面体
        
        constraints: [(coeffs, bound), ...]
                     表示 sum(coeffs[i] * x[i]) <= bound
        """
        self.constraints = constraints if constraints else []
    
    def __repr__(self):
        if not self.constraints:
            return "Polyhedron(top)"
        return f"Polyhedron({len(self.constraints)} constraints)"
    
    @staticmethod
    def top():
        return Polyhedron()
    
    @staticmethod
    def bottom():
        return Polyhedron([(0, -1)])  # 0 <= -1 (矛盾)
    
    def add_constraint(self, coeffs, bound):
        """添加线性约束"""
        self.constraints.append((coeffs, bound))
    
    def is_bottom(self):
        """是否为空多面体"""
        # 检查是否矛盾
        return any(
            all(c == 0 for c in coeffs) and bound < 0
            for coeffs, bound in self.constraints
        )
    
    def lub(self, other):
        """最小上界：添加所有约束"""
        result = Polyhedron(self.constraints + other.constraints)
        return result
    
    def apply_assign(self, var_idx, expr, env):
        """
        应用赋值 x = expr
        
        简化版本：假设expr是变量或常数
        """
        new_constraints = []
        
        for coeffs, bound in self.constraints:
            new_coeffs = list(coeffs)
            if isinstance(expr, tuple) and expr[0] == 'var':
                src_idx = expr[1]
                new_coeffs[var_idx] = coeffs[src_idx]
                new_coeffs[src_idx] = 0  # 消除源变量
            
            new_constraints.append((new_coeffs, bound))
        
        return Polyhedron(new_constraints)


def run_demo():
    """运行抽象解释演示"""
    print("=" * 60)
    print("抽象解释 - 区间域与不动点计算")
    print("=" * 60)
    
    # 区间演示
    print("\n[区间域演示]")
    
    i1 = Interval(0, 10)
    i2 = Interval(5, 15)
    i3 = Interval(8, 12)
    
    print(f"  i1 = {i1}")
    print(f"  i2 = {i2}")
    print(f"  i3 = {i3}")
    
    print(f"  i1 lub i2 = {i1.lub(i2)}")  # 并
    print(f"  i1 glb i2 = {i1.glb(i2)}")  # 交
    print(f"  i1 glb i3 = {i1.glb(i3)}")
    
    print(f"  i1 contains 5: {i1.contains(5)}")
    print(f"  i1 contains 15: {i1.contains(15)}")
    
    # 膨胀算子
    print(f"\n[膨胀算子演示]")
    i4 = Interval(0, 10)
    i5 = Interval(2, 12)
    widened = i4.widening(i5)
    print(f"  i4 = {i4}")
    print(f"  i5 = {i5}")
    print(f"  i4 widen i5 = {widened}")
    
    # 抽象解释程序分析
    print("\n[程序不变量分析]")
    
    ai = AbstractInterpretation()
    ai.variables = {'x', 'y'}
    
    # 程序: x = 0; y = 0; while (x < 10) { x = x + 1; y = y + x; }
    program = [
        ('assign', 'x', ('const', 0)),
        ('assign', 'y', ('const', 0)),
        ('while', ('<', ('var', 'x'), ('const', 10)),
          [
            ('assign', 'x', ('+', ('var', 'x'), ('const', 1))),
            ('assign', 'y', ('+', ('var', 'y'), ('var', 'x'))),
          ]
        )
    ]
    
    print("  程序:")
    print("    x = 0;")
    print("    y = 0;")
    print("    while (x < 10) {")
    print("      x = x + 1;")
    print("      y = y + x;")
    print("    }")
    
    inv = ai.analyze(program)
    print(f"\n  分析结果:")
    print(f"    x ∈ {inv.get('x', Interval.top())}")
    print(f"    y ∈ {inv.get('y', Interval.top())}")
    
    # 多面体演示
    print("\n[多面体域演示]")
    
    p1 = Polyhedron()
    p1.add_constraint([1, 0], 10)   # x <= 10
    p1.add_constraint([0, 1], 10)   # y <= 10
    p1.add_constraint([-1, 0], 0)   # x >= 0
    p1.add_constraint([0, -1], 0)  # y >= 0
    
    print(f"  p1: {p1}")
    print(f"  p1 is_bottom: {p1.is_bottom()}")
    
    print("\n" + "=" * 60)
    print("抽象解释核心概念:")
    print("  1. 抽象域: 状态空间的过度近似")
    print("  2. 区间域: 追踪变量上下界")
    print("  3. 多面体域: 使用线性不等式表示区域")
    print("  4. 膨胀(Widening): 保证迭代终止")
    print("  5. 伽罗瓦连接: 抽象与具体的伴随关系")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
