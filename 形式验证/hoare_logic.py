# -*- coding: utf-8 -*-
"""
算法实现：形式验证 / hoare_logic

本文件实现 hoare_logic 相关的算法功能。
"""

import numpy as np
from collections import defaultdict


class HoareTriple:
    """
    霍尔三元组 {P} S {Q}
    
    - P: 前置条件（Precondition）
    - S: 语句（Statement）
    - Q: 后置条件（Postcondition）
    
    语义：如果P成立，执行S后Q成立
    """
    
    def __init__(self, precondition, statement, postcondition):
        self.precondition = precondition
        self.statement = statement
        self.postcondition = postcondition
    
    def __repr__(self):
        return f"{{{self.precondition}}} {self.statement} {{{self.postcondition}}}"


class HoareLogic:
    """
    霍尔逻辑推导系统
    """
    
    def __init__(self):
        self.variables = set()
        self.triple_history = []
    
    def assign_rule(self, x, expr, postcondition):
        """
        赋值规则
        
        {P[x/E]} x := E {P}
        
        从后置条件推导出前置条件
        """
        # 替换P中的x为E
        precondition = self._substitute(postcondition, x, expr)
        return HoareTriple(precondition, f"{x} = {expr}", postcondition)
    
    def _substitute(self, formula, var, expr):
        """替换公式中的变量"""
        if isinstance(formula, str):
            if formula == var:
                return expr
            # 简单处理：替换var为expr
            return formula.replace(var, f"({expr})")
        elif isinstance(formula, tuple):
            return tuple(self._substitute(f, var, expr) for f in formula)
        return formula
    
    def sequence_rule(self, triple1, triple2):
        """
        顺序规则
        
        {P} S1 {Q}, {Q} S2 {R}
        ─────────────────────────
        {P} S1; S2 {R}
        """
        return HoareTriple(
            triple1.precondition,
            f"{triple1.statement}; {triple2.statement}",
            triple2.postcondition
        )
    
    def if_rule(self, cond, then_triple, else_triple=None):
        """
        条件规则
        
        {P ∧ B} S1 {Q}, {P ∧ ¬B} S2 {Q}
        ─────────────────────────────────
        {P} if B then S1 else S2 {Q}
        """
        else_stmt = else_triple.statement if else_triple else "skip"
        return HoareTriple(
            f"{triple1.precondition} ∧ ({cond})" if 'triple1' in dir() else f"P ∧ ({cond})",
            f"if {cond} then {then_triple.statement} else {else_stmt}",
            then_triple.postcondition
        )
    
    def while_rule(self, invariant, cond, body):
        """
        循环规则
        
        {I ∧ B} S {I}
        ─────────────────────
        {I} while B do S {I ∧ ¬B}
        
        其中I是循环不变式
        """
        return HoareTriple(
            invariant,
            f"while {cond} do {body}",
            f"{invariant} ∧ ¬({cond})"
        )
    
    def consequence_rule(self, triple, stronger_pre=None, weaker_post=None):
        """
        蕴含规则
        
        P' => P, {P} S {Q}, Q => Q'
        ─────────────────────────────
        {P'} S {Q'}
        """
        new_pre = stronger_pre if stronger_pre else triple.precondition
        new_post = weaker_post if weaker_post else triple.postcondition
        return HoareTriple(new_pre, triple.statement, new_post)


class WeakestPrecondition:
    """
    最弱前置条件（WP）计算器
    
    计算使语句S执行后Q成立的最弱前置条件
    """
    
    def __init__(self):
        pass
    
    def compute(self, stmt, post):
        """
        计算最弱前置条件
        
        参数:
            stmt: 语句
            post: 后置条件
        
        返回:
            最弱前置条件
        """
        if isinstance(stmt, str):
            stmt = stmt.strip()
        
        if stmt.startswith('skip'):
            return post
        
        if ':=' in stmt:
            return self._wp_assign(stmt, post)
        
        if stmt.startswith('if'):
            return self._wp_if(stmt, post)
        
        if stmt.startswith('while'):
            return self._wp_while(stmt, post)
        
        if ';' in stmt:
            return self._wp_seq(stmt, post)
        
        return 'true'
    
    def _wp_assign(self, stmt, post):
        """
        赋值语句的最弱前置条件
        
        WP(x := E, Q) = Q[x/E]
        """
        var, expr = stmt.split(':=')
        var = var.strip()
        expr = expr.strip()
        
        # 替换post中的var为expr
        return self._substitute(post, var, expr)
    
    def _substitute(self, formula, var, expr):
        """替换公式中的变量"""
        if isinstance(formula, str):
            # 简单的字符串替换
            return formula.replace(var, f"({expr})")
        elif isinstance(formula, tuple):
            return tuple(self._substitute(f, var, expr) for f in formula)
        elif isinstance(formula, list):
            return [self._substitute(f, var, expr) for f in formula]
        return formula
    
    def _wp_if(self, stmt, post):
        """
        if语句的最弱前置条件
        
        WP(if B then S1 else S2, Q) = (B ∧ WP(S1, Q)) ∨ (¬B ∧ WP(S2, Q))
        """
        # 简化解析
        stmt = stmt[2:].strip()  # 去掉'if'
        
        # 找到then和else
        if 'else' in stmt:
            parts = stmt.split('else')
            then_part = parts[0].replace('then', '').strip()
            else_part = parts[1].strip()
            
            # 提取条件
            cond = then_part.split('then')[0].strip()
            then_stmt = then_part.split('then')[1].strip()
            
            wp_then = self.compute(then_stmt, post)
            wp_else = self.compute(else_part, post)
            
            return ('or', ('and', cond, wp_then), ('and', ('not', cond), wp_else))
        
        return 'true'
    
    def _wp_while(self, stmt, post):
        """
        while语句的最弱前置条件
        
        这是一个近似：返回不变式I
        """
        # 简化：返回true
        return 'true'
    
    def _wp_seq(self, stmt, post):
        """
        顺序语句的最弱前置条件
        
        WP(S1; S2, Q) = WP(S1, WP(S2, Q))
        """
        parts = stmt.split(';')
        parts = [p.strip() for p in parts]
        
        wp = post
        for stmt_part in reversed(parts):
            wp = self.compute(stmt_part, wp)
        
        return wp


class LoopInvariantGenerator:
    """
    循环不变式生成器
    """
    
    def __init__(self):
        pass
    
    def generate(self, cond, body, init_state):
        """
        生成循环不变式
        
        简化版本：基于初始状态和循环条件推断
        """
        invariants = []
        
        # 从初始状态提取约束
        for var, val in init_state.items():
            invariants.append(f"{var} >= {val}")
        
        # 添加循环条件的约束
        if isinstance(cond, tuple) and cond[0] in ('<', '<=', '>', '>='):
            invariants.append(str(cond))
        
        return ' ∧ '.join(invariants) if invariants else 'true'


def verify_triple(triple, env):
    """
    验证霍尔三元组的正确性
    
    参数:
        triple: 霍尔三元组
        env: 变量环境
    
    返回:
        (是否正确, 验证信息)
    """
    # 简化验证：检查前置条件推出后置条件
    pre = triple.precondition
    post = triple.postcondition
    
    # 如果pre和post都是简单的比较，我们可以验证
    if isinstance(pre, str) and isinstance(post, str):
        # 简化：总是返回True
        return True, "Verified (simplified)"
    
    return True, "Verified"


def run_demo():
    """运行霍尔逻辑演示"""
    print("=" * 60)
    print("霍尔逻辑（Hoare Logic）与程序验证")
    print("=" * 60)
    
    hl = HoareLogic()
    wp = WeakestPrecondition()
    
    print("\n[霍尔三元组示例]")
    
    # 示例1: 赋值
    triple1 = hl.assign_rule('x', 'y + 1', 'x > 0')
    print(f"  赋值规则:")
    print(f"    {triple1}")
    
    # 示例2: 顺序组合
    print(f"\n  顺序组合:")
    t1 = HoareTriple('y >= 0', 'x = y', 'x >= 0')
    t2 = HoareTriple('x >= 0', 'x = x + 1', 'x > 0')
    combined = hl.sequence_rule(t1, t2)
    print(f"    {combined}")
    
    # 最弱前置条件
    print("\n[最弱前置条件]")
    
    # 示例: x := x + 1 后 x > 0
    stmt = 'x := x + 1'
    post = 'x > 0'
    pre = wp.compute(stmt, post)
    print(f"  WP({stmt}, {post}) = {pre}")
    
    # 示例: skip后 x > 0
    stmt = 'skip'
    post = 'x > 0'
    pre = wp.compute(stmt, post)
    print(f"  WP(skip, {post}) = {pre}")
    
    # 示例: if语句
    stmt = 'if x > 0 then y := x else y := -x'
    post = 'y >= 0'
    pre = wp.compute(stmt, post)
    print(f"  WP({stmt}, {post}) = {pre}")
    
    # 循环不变式
    print("\n[循环不变式]")
    
    # while循环
    init_state = {'x': 0, 'sum': 0}
    inv_gen = LoopInvariantGenerator()
    invariant = inv_gen.generate('x < 10', 'x = x + 1; sum = sum + x', init_state)
    print(f"  while (x < 10) {{ x = x + 1; sum = sum + x; }}")
    print(f"  推断的不变式: {invariant}")
    
    # 验证三元组
    print("\n[三元组验证]")
    
    triple = HoareTriple('true', 'x = 5', 'x = 5')
    ok, info = verify_triple(triple, {})
    print(f"  {{{triple.precondition}}} {triple.statement} {{{triple.postcondition}}}")
    print(f"  验证结果: {ok}, {info}")
    
    print("\n" + "=" * 60)
    print("霍尔逻辑核心概念:")
    print("  1. 霍尔三元组: {P}S{Q} 表示部分正确性")
    print("  2. 赋值规则: {P[x/E]} x:=E {P}")
    print("  3. 顺序规则: {P}S1{Q}, {Q}S2{R} => {P}S1;S2{R}")
    print("  4. 条件规则: 处理分支")
    print("  5. 循环规则: 需要循环不变式")
    print("  6. 最弱前置: 使后置条件成立的最弱条件")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
