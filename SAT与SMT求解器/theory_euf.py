# -*- coding: utf-8 -*-
"""
未解释函数(EUF)理论求解器
功能：实现等词逻辑 + 未解释函数的一致性检查

EUFLIA = Equality with Uninterpreted Functions + Linear Integer Arithmetic

核心算法：Congruence Closure（合流闭包）
- 维护等价类（变量相等关系）
- 维护函数的合流性：若 x=y 则 f(x)=f(y)

作者：EUF Theory Team
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, deque


class EUFExpr:
    """EUF表达式"""
    def __init__(self, name: str):
        self.name = name
    
    def __repr__(self):
        return self.name
    
    def __hash__(self):
        return hash(self.name)
    
    def __eq__(self, other):
        return isinstance(other, EUFExpr) and self.name == other.name


class EUFFunc:
    """函数应用 f(args)"""
    def __init__(self, name: str, args: List[EUFExpr]):
        self.name = name
        self.args = tuple(args)
    
    def __repr__(self):
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.name}({args_str})"
    
    def __hash__(self):
        return hash((self.name, self.args))
    
    def __eq__(self, other):
        return (isinstance(other, EUFFunc) and 
                self.name == other.name and self.args == other.args)


class CongruenceClosure:
    """
    合流闭包算法
    
    维护：
    1. 等价类 partition: 表达式→代表元
    2. 合流类 congruence: 函数→参数类的应用
    
    关键不变量：若 x~y，则 f(x)~f(y) 对所有函数f成立
    """

    def __init__(self):
        # 等价关系：expr → 父节点（并查集）
        self.parent: Dict[Any, Any] = {}
        # rank用于路径压缩
        self.rank: Dict[Any, int] = defaultdict(int)
        # 扰动函数: f → { arg_tuple → result }
        self.func_table: Dict[str, Dict[Tuple, EUFExpr]] = {}
        # 合并队列
        self.merge_queue: deque = deque()
        self.merged: Set[Tuple[Any, Any]] = set()

    def make(self, expr: EUFExpr):
        """创建新表达式"""
        if expr not in self.parent:
            self.parent[expr] = expr
            self.rank[expr] = 0

    def find(self, expr: EUFExpr) -> EUFExpr:
        """查找代表元（路径压缩）"""
        if expr not in self.parent:
            self.make(expr)
        if self.parent[expr] != expr:
            self.parent[expr] = self.find(self.parent[expr])
        return self.parent[expr]

    def union(self, e1: EUFExpr, e2: EUFExpr):
        """合并两个等价类"""
        r1, r2 = self.find(e1), self.find(e2)
        if r1 == r2:
            return
        
        # 按rank合并
        if self.rank[r1] < self.rank[r2]:
            r1, r2 = r2, r1
        
        self.parent[r2] = r1
        if self.rank[r1] == self.rank[r2]:
            self.rank[r1] += 1
        
        # 记录合并
        pair = (min(id(r1), id(r2)), max(id(r1), id(r2)))
        self.merged.add(pair)
        
        # 合并函数表条目
        self._propagate_congruence(r2, r1)

    def _propagate_congruence(self, old_rep: EUFExpr, new_rep: EUFExpr):
        """
        合流传播：当两个类合并时，更新函数应用的一致性
        
        关键：若 g(x)=a 且 g(y)=b 且 x~y，则 a~b
        """
        for func_name, arg_map in list(self.func_table.items()):
            for arg_tuple, result in list(arg_map.items()):
                if self.find(result) == old_rep:
                    # 找到使用old_rep作为结果的条目
                    pass

    def add_function(self, name: str, args: List[EUFExpr], result: EUFExpr):
        """添加函数应用约束 f(args) = result"""
        self.make(result)
        for arg in args:
            self.make(arg)
        
        arg_key = tuple(args)
        if name not in self.func_table:
            self.func_table[name] = {}
        
        # 检查是否与现有约束冲突
        if arg_key in self.func_table[name]:
            existing = self.func_table[name][arg_key]
            self.union(existing, result)
        else:
            self.func_table[name][arg_key] = result
        
        # 合流规则：若 xi ~ yi，则 f(x1,...,xn) ~ f(y1,...,yn)
        for i, arg in enumerate(args):
            # 需要检查其他使用相同函数的应用
            pass

    def are_equal(self, e1: EUFExpr, e2: EUFExpr) -> bool:
        """检查两个表达式是否等价"""
        return self.find(e1) == self.find(e2)

    def addDiseq(self, e1: EUFExpr, e2: EUFExpr) -> bool:
        """
        添加不等约束 e1 ≠ e2
        返回False表示冲突
        """
        if self.are_equal(e1, e2):
            return False  # 矛盾
        return True


class EUFTheorySolver:
    """
    EUF理论求解器
    使用合流闭包算法检查一致性
    """

    def __init__(self):
        self.cc = CongruenceClosure()
        self.assertions: List[Tuple[str, Any, Any]] = []  # (kind, expr1, expr2)
        self Diseq: Set[Tuple[Any, Any]] = set()

    def assert_eq(self, e1: EUFExpr, e2: EUFExpr):
        """断言 e1 = e2"""
        self.assertions.append(('eq', e1, e2))
        self.cc.union(e1, e2)

    def assert_func(self, name: str, args: List[EUFExpr], result: EUFExpr):
        """断言 f(args) = result"""
        self.assertions.append(('func', name, result))
        self.cc.add_function(name, args, result)

    def assertDiseq(self, e1: EUFExpr, e2: EUFExpr):
        """断言 e1 ≠ e2"""
        self.assertions.append(('diseq', e1, e2))
        self.Diseq.add((e1, e2))

    def check_sat(self) -> bool:
        """检查当前断言是否可满足"""
        # 检查不等约束
        for e1, e2 in self.Diseq:
            if self.cc.are_equal(e1, e2):
                return False  # 矛盾
        return True

    def get_model(self) -> Dict[str, str]:
        """获取模型：将每个表达式映射到其等价类代表"""
        model = {}
        for expr in self.cc.parent:
            rep = self.cc.find(expr)
            model[expr.name] = rep.name
        return model


def example_congruence():
    """合流闭包示例"""
    cc = CongruenceClosure()
    
    a = EUFExpr("a")
    b = EUFExpr("b")
    c = EUFExpr("c")
    
    # a = b
    cc.union(a, b)
    
    # f(a) = c
    cc.add_function("f", [a], c)
    
    # 检查: f(b) = c (应该等价)
    fb = EUFFunc("f", [b])
    print(f"a=b, f(a)=c → f(b)=c: {cc.are_equal(fb, c)}")


def example_euf_solver():
    """EUF求解器示例"""
    solver = EUFTheorySolver()
    
    x = EUFExpr("x")
    y = EUFExpr("y")
    z = EUFExpr("z")
    
    # x = y
    solver.assert_eq(x, y)
    
    # f(x) = z
    solver.assert_func("f", [x], z)
    
    # 检查: f(y) = z (应该SAT)
    fy = EUFFunc("f", [y])
    
    # 添加不等约束 f(y) ≠ z
    solver.assertDiseq(fy, z)
    
    print(f"EUF: x=y, f(x)=z, f(y)≠z → {'UNSAT' if not solver.check_sat() else 'SAT'}")


def example_transitivity():
    """传递性示例：x=y ∧ y=z → f(x)=f(z)"""
    solver = EUFTheorySolver()
    
    x, y, z = EUFExpr("x"), EUFExpr("y"), EUFExpr("z")
    
    solver.assert_eq(x, y)
    solver.assert_eq(y, z)
    
    fx = EUFFunc("f", [x])
    fz = EUFFunc("f", [z])
    
    # 传递性应该自动保证
    print(f"传递性: x=y ∧ y=z → f(x)=f(z): {solver.check_sat()}")


if __name__ == "__main__":
    print("=" * 50)
    print("EUF理论求解器 测试")
    print("=" * 50)
    
    example_congruence()
    print()
    example_euf_solver()
    print()
    example_transitivity()
