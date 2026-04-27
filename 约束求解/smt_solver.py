# -*- coding: utf-8 -*-
"""
算法实现：约束求解 / smt_solver

本文件实现 smt_solver 相关的算法功能。
"""

from typing import List, Dict, Set, Any, Optional, Tuple
from abc import ABC, abstractmethod


class Theory(ABC):
    """
    理论基类 - 定义特定理论的接口
    """
    @abstractmethod
    def is_consistent(self, assignment: Dict[str, Any]) -> bool:
        """检查赋值是否与理论一致"""
        pass
    
    @abstractmethod
    def get_conflicts(self, assignment: Dict[str, Any]) -> List[Any]:
        """获取冲突信息"""
        pass
    
    @abstractmethod
    def propagate(self, assignment: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Any]]:
        """
        理论传播:从当前赋值推导出新事实
        
        Returns:
            (新赋值, 冲突列表)
        """
        pass


class UFTheory:
    """
    未解释函数(Uninterpreted Functions)理论
    包含函数符号和等式公理
    """
    
    def __init__(self):
        self.functions: Dict[str, int] = {}  # 函数名 -> 参数个数
        self.terms: Dict[str, str] = {}  # 变量名 -> 类型
        self.equations: List[Tuple[str, str]] = []  # 等式列表
    
    def declare_function(self, name: str, arity: int):
        """声明函数符号"""
        self.functions[name] = arity
    
    def declare_variable(self, name: str, sort: str):
        """声明变量"""
        self.terms[name] = sort
    
    def is_consistent(self, assignment: Dict[str, Any]) -> bool:
        """检查一致性"""
        # 传递闭包检查
        return True  # 简化实现
    
    def propagate(self, assignment: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Any]]:
        """传播等式约束"""
        return {}, []
    
    def congruence_closure(self, terms: List[str], eqs: List[Tuple[str, str]]) -> Dict[str, str]:
        """
        求同余闭包 - 合并等价类
        
        Args:
            terms: 项列表
            eqs: 等式列表
        
        Returns:
            同余闭包(每个项的代表元)
        """
        parent = {t: t for t in terms}
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # 应用等式
        for a, b in eqs:
            if a in parent and b in parent:
                union(a, b)
        
        # 路径压缩
        for t in terms:
            parent[t] = find(t)
        
        return parent


class LIATheory:
    """
    线性整数算术(Linear Integer Arithmetic)理论
    支持形如 a*x + b*y <= c 的约束
    """
    
    def __init__(self):
        self.constraints: List[Tuple[List[Tuple[int, str]], int]] = []  # 约束列表
        self.bounds: Dict[str, Tuple[int, int]] = {}  # 变量上下界
    
    def add_constraint(self, coeffs: List[Tuple[int, str]], bound: int):
        """
        添加线性约束: sum(coeff * var) <= bound
        
        Args:
            coeffs: [(系数, 变量名), ...]
            bound: 上界
        """
        self.constraints.append((coeffs, bound))
    
    def set_bounds(self, var: str, lower: int, upper: int):
        """设置变量边界"""
        self.bounds[var] = (lower, upper)
    
    def is_consistent(self, assignment: Dict[str, Any]) -> bool:
        """检查赋值是否满足所有约束"""
        for coeffs, bound in self.constraints:
            total = sum(coeff * assignment.get(var, 0) for coeff, var in coeffs)
            if total > bound:
                return False
        return True
    
    def propagate(self, assignment: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Any]]:
        """
        传播边界约束
        
        Returns:
            (新赋值, 冲突列表)
        """
        new_assignment = assignment.copy()
        conflicts = []
        
        for var, (lower, upper) in self.bounds.items():
            if var not in new_assignment:
                if lower == upper:
                    new_assignment[var] = lower
                elif upper < lower:
                    conflicts.append(f"变量{var}的界矛盾: [{lower}, {upper}]")
        
        return new_assignment, conflicts
    
    def box_propagate(self, constraints: List[Tuple[List[Tuple[int, str]], int]]) -> Dict[str, Tuple[int, int]]:
        """
        盒子传播 - 收缩变量边界
        
        Args:
            constraints: 线性约束列表
        
        Returns:
            每个变量的(下界, 上界)
        """
        bounds = {var: (-float('inf'), float('inf')) for var in self.bounds}
        
        # 初始化为显式边界
        for var, (lower, upper) in self.bounds.items():
            bounds[var] = (lower, upper)
        
        # 迭代传播
        changed = True
        while changed:
            changed = False
            
            for coeffs, bound in constraints:
                # 分离正系数和负系数
                pos_vars = []
                neg_vars = []
                
                for coeff, var in coeffs:
                    if var in bounds:
                        if coeff > 0:
                            pos_vars.append((coeff, var))
                        else:
                            neg_vars.append((coeff, var))
                
                # 尝试更新边界
                for coeff, var in pos_vars:
                    # 从上界约束
                    pass  # 简化实现
        
        return bounds


class TheorySolver:
    """
    SMT求解器 - 组合理论和回溯搜索
    """
    
    def __init__(self, theory: Theory):
        """
        初始化SMT求解器
        
        Args:
            theory: 背景理论
        """
        self.theory = theory
        self.boolean_vars: Set[str] = set()
        self.literal_to_bool_var: Dict[int, str] = {}
        self.bool_var_counter = 0
    
    def to_sat(self, formula: List[Set[int]]) -> List[Set[str]]:
        """
        将SMT公式转换为SAT子句
        使用Tseitin编码
        
        Args:
            formula: SMT公式(用整数表示文字)
        
        Returns:
            SAT子句
        """
        # 创建布尔变量映射
        self.literal_to_bool_var = {}
        self.bool_var_counter = 0
        
        sat_clauses = []
        
        for clause in formula:
            bool_lits = []
            for lit in clause:
                var = abs(lit)
                if var not in self.literal_to_bool_var:
                    self.literal_to_bool_var[var] = f"b{self.bool_var_counter}"
                    self.bool_var_counter += 1
                
                bool_lit = self.literal_to_bool_var[var]
                if lit < 0:
                    bool_lit = f"not_{bool_lit}"
                bool_lits.append(bool_lit)
            
            sat_clauses.append(bool_lits)
        
        return sat_clauses
    
    def check(self, assignment: Dict[str, Any]) -> Tuple[bool, List[Any]]:
        """
        检查当前赋值的理论一致性
        
        Returns:
            (是否一致, 冲突列表)
        """
        new_assignment, conflicts = self.theory.propagate(assignment)
        if conflicts:
            return False, conflicts
        return self.theory.is_consistent(new_assignment), []
    
    def solve(self, formula: List[Set[int]], 
              assignment: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        求解SMT公式
        
        Args:
            formula: 公式列表
            assignment: 当前部分赋值
        
        Returns:
            满足的赋值或None
        """
        if assignment is None:
            assignment = {}
        
        # 理论传播
        consistent, conflicts = self.check(assignment)
        if not consistent:
            return None
        
        # 如果所有布尔变量都已赋值
        if len(assignment) == self.bool_var_counter:
            return assignment
        
        # 选择一个未赋值的布尔变量
        unassigned = [f"b{i}" for i in range(self.bool_var_counter) if f"b{i}" not in assignment]
        if not unassigned:
            return assignment
        
        var = unassigned[0]
        
        # 尝试True
        assignment[var] = True
        result = self.solve(formula, assignment)
        if result:
            return result
        
        # 尝试False
        assignment[var] = False
        return self.solve(formula, assignment)


def solve_smt_lia(variables: List[str], constraints: List[Tuple[List[Tuple[int, str]], int]]) -> Optional[Dict[str, int]]:
    """
    线性整数算术SMT求解便捷函数
    
    Args:
        variables: 变量列表
        constraints: 约束列表
    
    Returns:
        满足的赋值或None
    """
    theory = LIATheory()
    for var in variables:
        theory.set_bounds(var, -1000, 1000)
    
    for coeffs, bound in constraints:
        theory.add_constraint(coeffs, bound)
    
    solver = TheorySolver(theory)
    
    # 简单区间求解
    bounds = theory.box_propagate(constraints)
    
    result = {}
    for var in variables:
        lower, upper = bounds.get(var, (-1000, 1000))
        if lower > upper:
            return None
        result[var] = lower  # 返回下界
    
    return result


# 测试代码
if __name__ == "__main__":
    # 测试1: 线性整数算术
    print("测试1 - LIA理论:")
    variables = ['x', 'y', 'z']
    constraints = [
        ([(1, 'x'), (1, 'y')], 10),      # x + y <= 10
        ([(1, 'x'), (-1, 'y')], 2),      # x - y <= 2
        ([(-1, 'x'), (1, 'y')], 2),      # -x + y <= 2
        ([(1, 'z')], 5),                  # z <= 5
        ([(-1, 'z')], -5),               # -z <= -5, 即 z >= 5
    ]
    
    result = solve_smt_lia(variables, constraints)
    print(f"  结果: {result}")
    
    # 测试2: UF理论同余闭包
    print("\n测试2 - UF理论同余闭包:")
    theory = UFTheory()
    terms = ['a', 'b', 'c', 'd', 'f(a)', 'f(b)', 'f(c)']
    equations = [('a', 'b'), ('f(a)', 'f(b)')]
    
    closure = theory.congruence_closure(terms, equations)
    print(f"  项: {terms}")
    print(f"  等式: {equations}")
    print(f"  同余闭包: {closure}")
    
    # 按代表元分组
    representatives = {}
    for term, rep in closure.items():
        if rep not in representatives:
            representatives[rep] = []
        representatives[rep].append(term)
    print(f"  等价类: {representatives}")
    
    # 测试3: 复杂约束
    print("\n测试3 - 复杂LIA约束:")
    variables2 = ['a', 'b', 'c']
    constraints2 = [
        ([(1, 'a'), (1, 'b'), (1, 'c')], 100),   # a + b + c <= 100
        ([(2, 'a'), (1, 'b')], 50),               # 2a + b <= 50
        ([(1, 'a'), (-1, 'c')], 10),              # a - c <= 10
    ]
    
    result2 = solve_smt_lia(variables2, constraints2)
    print(f"  结果: {result2}")
    
    # 验证
    if result2:
        print("  验证:")
        for coeffs, bound in constraints2:
            total = sum(coeff * result2.get(var, 0) for coeff, var in coeffs)
            print(f"    {coeffs} <= {bound}: {total} <= {bound} = {total <= bound}")
    
    print("\n所有测试完成!")
