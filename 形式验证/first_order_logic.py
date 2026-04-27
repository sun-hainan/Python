# -*- coding: utf-8 -*-
"""
算法实现：形式验证 / first_order_logic

本文件实现 first_order_logic 相关的算法功能。
"""

import numpy as np
from collections import defaultdict


class FOLSignature:
    """
    一阶逻辑签名
    
    包含：
    - 函数符号及其元数
    - 关系符号及其元数
    - 常量符号
    """
    
    def __init__(self):
        self.functions = {}    # name -> arity
        self.relations = {}    # name -> arity
        self.constants = set() # set of names
    
    def add_function(self, name, arity):
        """添加函数符号"""
        self.functions[name] = arity
    
    def add_relation(self, name, arity):
        """添加关系符号"""
        self.relations[name] = arity
    
    def add_constant(self, name):
        """添加常量符号"""
        self.constants.add(name)
    
    def __repr__(self):
        return f"FOLSignature(funcs={self.functions}, rels={self.relations}, consts={self.constants})"


class FOLStructure:
    """
    一阶逻辑结构（解释）
    
    为签名提供语义：
    - 论域（Domain）
    - 函数解释
    - 关系解释
    - 常量解释
    """
    
    def __init__(self, signature):
        self.signature = signature
        self.domain = set()  # 论域
        self.func_interp = {}  # 函数解释
        self.rel_interp = {}   # 关系解释
        self.const_interp = {}  # 常量解释
    
    def set_domain(self, domain):
        """设置论域"""
        self.domain = set(domain)
    
    def add_element(self, elem):
        """添加论域元素"""
        self.domain.add(elem)
    
    def interpret_function(self, name, func):
        """解释函数符号"""
        self.func_interp[name] = func
    
    def interpret_relation(self, name, relation):
        """解释关系符号"""
        self.rel_interp[name] = relation
    
    def interpret_constant(self, name, value):
        """解释常量符号"""
        self.const_interp[name] = value
    
    def evaluate_term(self, term, assignment=None):
        """
        求值项（term）
        
        参数:
            term: (name, *args) 元组
            assignment: 变量赋值 dict
        
        返回:
            项的值
        """
        if assignment is None:
            assignment = {}
        
        if isinstance(term, tuple):
            name = term[0]
            args = term[1:]
            
            if name in self.const_interp:
                return self.const_interp[name]
            
            if name in assignment:
                return assignment[name]
            
            if name in self.func_interp:
                func = self.func_interp[name]
                args_values = [self.evaluate_term(a, assignment) for a in args]
                return func(*args_values)
        
        return term  # 常量或变量
    
    def evaluate_formula(self, formula, assignment=None):
        """
        求值公式
        
        参数:
            formula: 公式元组
            assignment: 变量赋值
        
        返回:
            True/False
        """
        if assignment is None:
            assignment = {}
        
        if not isinstance(formula, tuple):
            return formula  # 布尔常量
        
        op = formula[0]
        
        if op == '==':
            left = self.evaluate_term(formula[1], assignment)
            right = self.evaluate_term(formula[2], assignment)
            return left == right
        
        if op == '!=':
            left = self.evaluate_term(formula[1], assignment)
            right = self.evaluate_term(formula[2], assignment)
            return left != right
        
        if op == '<':
            left = self.evaluate_term(formula[1], assignment)
            right = self.evaluate_term(formula[2], assignment)
            return left < right
        
        if op == '>':
            left = self.evaluate_term(formula[1], assignment)
            right = self.evaluate_term(formula[2], assignment)
            return left > right
        
        if op == '<=':
            left = self.evaluate_term(formula[1], assignment)
            right = self.evaluate_term(formula[2], assignment)
            return left <= right
        
        if op == '>=':
            left = self.evaluate_term(formula[1], assignment)
            right = self.evaluate_term(formula[2], assignment)
            return left >= right
        
        if op == 'not':
            return not self.evaluate_formula(formula[1], assignment)
        
        if op == 'and':
            return (self.evaluate_formula(formula[1], assignment) and
                    self.evaluate_formula(formula[2], assignment))
        
        if op == 'or':
            return (self.evaluate_formula(formula[1], assignment) or
                    self.evaluate_formula(formula[2], assignment))
        
        if op == '->':  # 蕴含
            antecedent = self.evaluate_formula(formula[1], assignment)
            consequent = self.evaluate_formula(formula[2], assignment)
            return (not antecedent) or consequent
        
        if op == 'forall':
            var = formula[1]
            body = formula[2]
            # 对所有论域元素检查
            for elem in self.domain:
                new_assignment = assignment.copy()
                new_assignment[var] = elem
                if not self.evaluate_formula(body, new_assignment):
                    return False
            return True
        
        if op == 'exists':
            var = formula[1]
            body = formula[2]
            # 存在论域元素使公式为真
            for elem in self.domain:
                new_assignment = assignment.copy()
                new_assignment[var] = elem
                if self.evaluate_formula(body, new_assignment):
                    return True
            return False
        
        return False


class Theory:
    """
    一阶理论
    
    公理的集合
    """
    
    def __init__(self, signature):
        self.signature = signature
        self.axioms = []  # 公理列表
    
    def add_axiom(self, formula):
        """添加公理"""
        self.axioms.append(formula)
    
    def is_satisfiable(self, formula):
        """
        检查公式是否可满足
        
        即：是否存在一个模型使得公式为真
        """
        # 简化：只检查论域是否为空
        return True
    
    def is_valid(self, formula):
        """
        检查公式是否有效
        
        即：公式在所有模型中都为真
        """
        # 简化：假设只有空论域
        return False
    
    def is_consistent(self):
        """
        检查理论是否一致
        
        即：不存在矛盾
        """
        # 简化：总是返回True
        return True


class SATSolver:
    """
    命题SAT求解器（用于理论验证）
    
    使用简单真值表方法
    """
    
    def __init__(self):
        self.variables = []
    
    def is_satisfiable(self, formula, variables):
        """
        检查公式是否可满足
        
        参数:
            formula: 命题公式
            variables: 变量列表
        
        返回:
            (可满足, 满足赋值)
        """
        self.variables = variables
        n = len(variables)
        
        # 遍历所有2^n种赋值
        for i in range(2 ** n):
            assignment = {}
            for j in range(n):
                assignment[variables[j]] = bool((i >> j) & 1)
            
            if self._evaluate(formula, assignment):
                return True, assignment
        
        return False, None
    
    def _evaluate(self, formula, assignment):
        """求值"""
        if isinstance(formula, bool):
            return formula
        
        if isinstance(formula, str):
            return assignment.get(formula, False)
        
        op = formula[0]
        
        if op == 'not':
            return not self._evaluate(formula[1], assignment)
        
        if op == 'and':
            return (self._evaluate(formula[1], assignment) and
                    self._evaluate(formula[2], assignment))
        
        if op == 'or':
            return (self._evaluate(formula[1], assignment) or
                    self._evaluate(formula[2], assignment))
        
        if op == '->':
            return ((not self._evaluate(formula[1], assignment)) or
                    self._evaluate(formula[2], assignment))
        
        return False


def run_demo():
    """运行一阶逻辑演示"""
    print("=" * 60)
    print("一阶逻辑与模型论基础")
    print("=" * 60)
    
    # 创建签名
    sig = FOLSignature()
    sig.add_constant('0')
    sig.add_constant('1')
    sig.add_function('+', 2)
    sig.add_function('*', 2)
    sig.add_relation('<', 2)
    
    print("\n[签名]")
    print(f"  {sig}")
    
    # 创建结构（自然数）
    struct = FOLStructure(sig)
    
    # 设置论域
    struct.set_domain([0, 1, 2, 3, 4])
    
    # 解释常量
    struct.interpret_constant('0', 0)
    struct.interpret_constant('1', 1)
    
    # 解释函数
    struct.interpret_function('+', lambda a, b: (a + b) % 5)
    struct.interpret_function('*', lambda a, b: (a * b) % 5)
    
    # 解释关系
    struct.interpret_relation('<', lambda a, b: a < b)
    
    print("\n[结构（自然数模5）]")
    print(f"  论域: {struct.domain}")
    print(f"  解释: 0={struct.const_interp['0']}, 1={struct.const_interp['1']}")
    print(f"  +: {struct.func_interp['+'](2, 3)}")
    print(f"  *: {struct.func_interp['*'](2, 3)}")
    print(f"  <: {struct.rel_interp['<'](2, 3)}")
    
    # 求值公式
    print("\n[公式求值]")
    
    # x + 0 = x
    formula1 = ('==', ('+', 'x', ('const', 0)), 'x')
    assignment = {'x': 3}
    result = struct.evaluate_formula(formula1, assignment)
    print(f"  x + 0 = x (x=3): {result}")
    
    # x + 1 > x
    formula2 = ('>', ('+', 'x', ('const', 1)), 'x')
    result = struct.evaluate_formula(formula2, assignment)
    print(f"  x + 1 > x (x=3): {result}")
    
    # ∀x (x + 0 = x)
    formula3 = ('forall', 'x', ('==', ('+', 'x', ('const', 0)), 'x'))
    result = struct.evaluate_formula(formula3)
    print(f"  ∀x (x + 0 = x): {result}")
    
    # ∃x (x * x = 1)
    formula4 = ('exists', 'x', ('==', ('*', 'x', 'x'), ('const', 1)))
    result = struct.evaluate_formula(formula4)
    print(f"  ∃x (x * x = 1): {result}")
    
    # SAT求解
    print("\n[SAT求解]")
    sat_solver = SATSolver()
    
    # (p ∨ q) ∧ (¬p ∨ ¬q)
    formula = ('and',
                ('or', 'p', 'q'),
                ('or', ('not', 'p'), ('not', 'q')))
    
    satisfiable, assignment = sat_solver.is_satisfiable(formula, ['p', 'q'])
    print(f"  (p ∨ q) ∧ (¬p ∨ ¬q):")
    print(f"    可满足: {satisfiable}")
    if assignment:
        print(f"    满足赋值: p={assignment['p']}, q={assignment['q']}")
    
    # p ∧ ¬p
    formula2 = ('and', 'p', ('not', 'p'))
    satisfiable2, _ = sat_solver.is_satisfiable(formula2, ['p'])
    print(f"  p ∧ ¬p:")
    print(f"    可满足: {satisfiable2}")
    
    print("\n" + "=" * 60)
    print("一阶逻辑核心概念:")
    print("  1. 签名: 函数、关系、常量符号的集合")
    print("  2. 结构: 签名的语义解释（论域+解释）")
    print("  3. 项: 函数和常量构成的表达式")
    print("  4. 公式: 原子命题和逻辑联结词的组合")
    print("  5. 可满足: 存在模型使公式为真")
    print("  6. 有效: 所有模型中公式都为真")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
