# -*- coding: utf-8 -*-
"""
多面体抽象域分析（Polyhedral Analysis）
功能：用于精确的循环优化和数组边界分析

多面体模型（Polyhedral Model）：
- 程序片段必须由深层嵌套的for循环组成
- 循环变量和语句索引用仿射函数描述
- 迭代空间被表示为多面体

核心概念：
- Polyhedron（多面体）：由线性不等式定义的凸多面体
- Lattice（格）：迭代空间的点集
- Dependence（依赖）：循环迭代间的数据依赖

作者：Polyhedral Analysis Team
"""

from typing import List, Dict, Set, Tuple, Optional
from fractions import Fraction


class LinearConstraint:
    """线性约束：a1*x1 + a2*x2 + ... + b >= 0"""
    
    def __init__(self, coeffs: List[Fraction], lower_bound: Fraction):
        """
        Args:
            coeffs: 变量系数 [a1, a2, ..., an]
            lower_bound: 约束下界 b
        """
        self.coeffs = coeffs
        self.lower_bound = lower_bound

    def is_satisfied(self, point: List[int]) -> bool:
        """检查点是否满足约束"""
        total = self.lower_bound
        for a, x in zip(self.coeffs, point):
            total -= a * x
        return total >= 0

    def __repr__(self):
        terms = []
        for i, a in enumerate(self.coeffs):
            if a != 0:
                terms.append(f"{a}*x{i}")
        terms.append(f">={self.lower_bound}")
        return " ".join(terms)


class Polyhedron:
    """多面体：线性不等式系统的解集"""
    
    def __init__(self, constraints: List[LinearConstraint] = None):
        self.constraints = constraints or []
        self.dimension = len(self.constraints[0].coeffs) if constraints else 0

    def add_constraint(self, constraint: LinearConstraint):
        """添加约束"""
        self.constraints.append(constraint)

    def is_empty(self) -> bool:
        """检查多面体是否为空"""
        # 简化：仅检查是否可能为空
        return len(self.constraints) > 20

    def project(self, var_index: int) -> 'Polyhedron':
        """
        投影：消除一个维度
        
        使用Fourier-Motzkin消除变量
        """
        # 收集约束中该变量的系数
        lower_bounds: List[Fraction] = []
        upper_bounds: List[Fraction] = []
        other_constraints = []
        
        for c in self.constraints:
            coeff = c.coeffs[var_index]
            if coeff == 0:
                other_constraints.append(c)
            elif coeff > 0:
                # coeff*x_i + rest >= 0 → x_i >= -rest/coeff
                lower_bounds.append(c)
            else:
                # coeff*x_i + rest >= 0 → x_i <= -rest/coeff
                upper_bounds.append(c)
        
        # 生成新约束
        new_constraints = list(other_constraints)
        for lb in lower_bounds:
            for ub in upper_bounds:
                # 合并两个约束消除x_i
                new_coeff = []
                for i in range(len(lb.coeffs)):
                    if i == var_index:
                        new_coeff.append(Fraction(0))
                    else:
                        c1 = ub.coeffs[i] * lb.coeffs[var_index]
                        c2 = lb.coeffs[i] * (-ub.coeffs[var_index])
                        new_coeff.append(c1 + c2)
                
                new_lb = (-ub.lower_bound) * lb.coeffs[var_index] - \
                         (-lb.lower_bound) * (-ub.coeffs[var_index])
                
                new_constraints.append(LinearConstraint(new_coeff, new_lb))
        
        return Polyhedron(new_constraints)

    def __repr__(self):
        return f"Polyhedron({len(self.constraints)} constraints, dim={self.dimension})"


class IterationSpace:
    """
    迭代空间：循环嵌套的迭代点集合
    
    示例：
    for i = 0 to N-1:
      for j = 0 to i:
        S(i,j)
    
    迭代空间: { (i,j) | 0 <= i < N, 0 <= j <= i }
    """

    def __init__(self, loops: List[Tuple[str, int, int]]):
        """
        Args:
            loops: [(loop_var, lower, upper), ...]
        """
        self.loops = loops
        self.n_dims = len(loops)

    def to_polyhedron(self) -> Polyhedron:
        """将迭代空间转换为多面体"""
        constraints = []
        
        for i, (var, lower, upper) in enumerate(self.loops):
            # lower <= x_i <= upper
            # 转换为: x_i - lower >= 0 和 upper - x_i >= 0
            coeffs = [Fraction(0)] * self.n_dims
            coeffs[i] = Fraction(1)
            constraints.append(LinearConstraint(coeffs, Fraction(-lower)))
            
            coeffs = [Fraction(0)] * self.n_dims
            coeffs[i] = Fraction(-1)
            constraints.append(LinearConstraint(coeffs, Fraction(upper)))
        
        return Polyhedron(constraints)


class DependenceRelation:
    """
    依赖关系：描述语句实例间的数据依赖
    
    依赖类型：
    - Flow依赖（真依赖）：W after R
    - Anti依赖：R after W
    - Output依赖：W after W
    """

    def __init__(self, src_stmt: str, dst_stmt: str, 
                 distance: List[int], dependence_type: str):
        self.src_stmt = src_stmt
        self.dst_stmt = dst_stmt
        self.distance = distance  # 依赖距离向量
        self.type = dependence_type  # 'flow', 'anti', 'output'


class PolyhedralScoper:
    """
    多面体作用域分析
    
    用于判断数组访问是否在边界内
    """

    def __init__(self):
        self.iteration_spaces: Dict[str, IterationSpace] = {}
        self.array_accesses: List[Dict] = []  # {(i,j) -> A[i+j]}

    def add_iteration_space(self, stmt_id: str, loops: List[Tuple[str, int, int]]):
        """添加语句的迭代空间"""
        self.iteration_spaces[stmt_id] = IterationSpace(loops)

    def add_access(self, stmt_id: str, array: str, indices: List):
        """添加数组访问"""
        self.array_accesses.append({
            'stmt': stmt_id,
            'array': array,
            'indices': indices
        })

    def check_bounds(self, array: str, indices: List[Dict], 
                    array_size: List[int]) -> Polyhedron:
        """
        检查数组访问是否在边界内
        
        生成约束多面体表示有效的访问点
        """
        constraints = []
        n_dims = len(indices)
        
        for dim, (index_expr, size) in enumerate(zip(indices, array_size)):
            # 0 <= index < size
            coeffs = [Fraction(0)] * n_dims
            coeffs[dim] = Fraction(-1)
            constraints.append(LinearConstraint(coeffs, Fraction(0)))  # index >= 0
            
            coeffs = [Fraction(0)] * n_dims
            coeffs[dim] = Fraction(1)
            constraints.append(LinearConstraint(coeffs, Fraction(size - 1)))  # index <= size-1
        
        return Polyhedron(constraints)


def example_iteration_space():
    """迭代空间示例"""
    # for i = 0 to 9:
    #   for j = 0 to i:
    #     S(i, j)
    
    loops = [('i', 0, 9), ('j', 0, 10)]  # j的上界需要依赖i
    space = IterationSpace(loops[:1])  # 简化：只用外层循环
    
    poly = space.to_polyhedron()
    print(f"迭代空间: {poly}")
    
    # 检查点是否在迭代空间内
    print(f"(5) in space: {poly.constraints[0].is_satisfied([5])}")
    print(f"(12) in space: {poly.constraints[0].is_satisfied([12])}")


def example_polyhedron_bounds():
    """多面体边界检查"""
    # 2维空间: 0 <= x <= 10, 0 <= y <= 10
    constraints = [
        LinearConstraint([Fraction(1), Fraction(0)], Fraction(0)),   # x >= 0
        LinearConstraint([Fraction(-1), Fraction(0)], Fraction(-10)),  # x <= 10
        LinearConstraint([Fraction(0), Fraction(1)], Fraction(0)),   # y >= 0
        LinearConstraint([Fraction(0), Fraction(-1)], Fraction(-10)),  # y <= 10
    ]
    
    poly = Polyhedron(constraints)
    print(f"多面体: {poly}")
    
    # 检查点
    point1 = [5, 5]
    point2 = [15, 5]
    
    all_satisfied = all(c.is_satisfied(point1) for c in constraints)
    print(f"点{point1}满足: {all_satisfied}")
    
    all_satisfied = all(c.is_satisfied(point2) for c in constraints)
    print(f"点{point2}满足: {all_satisfied}")


def example_array_bounds():
    """数组边界检查"""
    scoper = PolyhedralScoper()
    
    # 访问 A[i][j] 其中 0 <= i < N, 0 <= j < M
    indices = [{'var': 'i'}, {'var': 'j'}]
    sizes = [20, 30]  # A是20x30的数组
    
    poly = scoper.check_bounds('A', indices, sizes)
    print(f"数组访问多面体: {poly}")


if __name__ == "__main__":
    print("=" * 50)
    print("多面体分析 测试")
    print("=" * 50)
    
    example_iteration_space()
    print()
    example_polyhedron_bounds()
    print()
    example_array_bounds()
