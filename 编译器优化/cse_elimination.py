# -*- coding: utf-8 -*-
"""
算法实现：编译器优化 / cse_elimination

本文件实现 cse_elimination 相关的算法功能。
"""

from typing import List, Dict, Set, Optional, Tuple
import hashlib


class Expression:
    """表达式"""
    def __init__(self, op: str, args: List):
        self.op = op
        self.args = args
    
    def __hash__(self):
        """哈希表达式用于字典键"""
        return hash((self.op, tuple(hash(a) if isinstance(a, Expression) else a for a in self.args)))
    
    def __eq__(self, other):
        if not isinstance(other, Expression):
            return False
        return self.op == other.op and self.args == other.args
    
    def __repr__(self):
        if not self.args:
            return self.op
        return f"({self.op} {' '.join(str(a) for a in self.args)})"


class Statement:
    """语句"""
    def __init__(self, lhs: str, expr: Expression):
        self.lhs = lhs
        self.expr = expr


class CSOptimizer:
    """
    公共子表达式消除优化器
    """
    
    def __init__(self):
        self.statements = []
        self.available_exprs: Dict[Expression, str] = {}  # 表达式 -> 存储变量
        self.last_def: Dict[str, str] = {}  # 变量 -> 定义的表达式变量
    
    def add_statement(self, stmt: Statement):
        self.statements.append(stmt)
    
    def optimize(self) -> List[Statement]:
        """
        执行CSE优化
        
        Returns:
            优化后的语句列表
        """
        optimized = []
        temp_count = 0
        
        for stmt in self.statements:
            expr = stmt.expr
            
            # 检查表达式是否已经计算过
            if expr in self.available_exprs:
                # 使用已有的结果
                stored_var = self.available_exprs[expr]
                
                # 检查存储变量是否仍然有效
                if self._is_valid(stored_var):
                    # 用已计算的变量替换
                    new_stmt = Statement(stmt.lhs, Expression(stored_var, []))
                    optimized.append(new_stmt)
                else:
                    # 重新计算
                    result_var = self._evaluate_expr(expr, optimized, temp_count)
                    temp_count += 1
                    new_stmt = Statement(stmt.lhs, Expression(result_var, []))
                    optimized.append(new_stmt)
                    self.available_exprs[expr] = result_var
                    self.last_def[result_var] = result_var
            else:
                # 检查表达式中的变量是否被重新定义
                if self._all_args_valid(expr):
                    # 可以安全使用CSE
                    temp_var = f"_t{temp_count}"
                    temp_count += 1
                    
                    # 添加临时赋值
                    temp_stmt = Statement(temp_var, expr)
                    optimized.append(temp_stmt)
                    
                    # 记录可用表达式
                    self.available_exprs[expr] = temp_var
                    self.last_def[temp_var] = temp_var
                    
                    # 原语句使用临时变量
                    new_stmt = Statement(stmt.lhs, Expression(temp_var, []))
                    optimized.append(new_stmt)
                else:
                    # 变量被修改,需要重新计算
                    self._invalidate_using_vars(expr)
                    
                    result_var = self._evaluate_expr(expr, optimized, temp_count)
                    temp_count += 1
                    new_stmt = Statement(stmt.lhs, Expression(result_var, []))
                    optimized.append(new_stmt)
                    
                    # 记录
                    self.available_exprs[expr] = result_var
                    self.last_def[result_var] = result_var
            
            # 更新变量定义
            self.last_def[stmt.lhs] = stmt.lhs
        
        return optimized
    
    def _is_valid(self, var: str) -> bool:
        """检查变量是否仍然有效"""
        return var in self.last_def and self.last_def[var] == var
    
    def _all_args_valid(self, expr: Expression) -> bool:
        """检查表达式所有参数是否有效"""
        for arg in expr.args:
            if isinstance(arg, str):  # 变量
                if not self._is_valid(arg):
                    return False
        return True
    
    def _invalidate_using_vars(self, expr: Expression):
        """使使用某变量的表达式无效"""
        # 简化实现
        to_remove = []
        for exp, stored_var in self.available_exprs.items():
            for arg in exp.args:
                if isinstance(arg, str) and not self._is_valid(arg):
                    to_remove.append(exp)
                    break
        
        for exp in to_remove:
            del self.available_exprs[exp]
    
    def _evaluate_expr(self, expr: Expression, stmts: List, temp_count: int) -> str:
        """评估表达式,返回结果变量"""
        temp_var = f"_t{temp_count}"
        new_stmt = Statement(temp_var, expr)
        stmts.append(new_stmt)
        self.available_exprs[expr] = temp_var
        self.last_def[temp_var] = temp_var
        return temp_var


def eliminate_common_subexpressions(statements: List[Tuple[str, str, List]]) -> List[Tuple[str, str, List]]:
    """
    公共子表达式消除便捷函数
    
    Args:
        statements: [(lhs, op, [args]), ...]
    
    Returns:
        优化后的语句
    """
    stmts = [Statement(lhs, Expression(op, args)) for lhs, op, args in statements]
    
    optimizer = CSOptimizer()
    for s in stmts:
        optimizer.add_statement(s)
    
    optimized = optimizer.optimize()
    
    return [(s.lhs, s.expr.op, s.expr.args) for s in optimized]


# 测试代码
if __name__ == "__main__":
    # 测试1: 简单CSE
    print("测试1 - 简单公共子表达式:")
    
    # a = b + c
    # d = b + c + 1  # 重复计算 b + c
    # e = a + d      # 使用之前的计算
    
    stmts1 = [
        ('a', '+', ['b', 'c']),
        ('d', '+', ['b', 'c', '1']),  # 实际上是 b + c + 1
        ('e', '+', ['a', 'd']),
    ]
    
    optimized1 = eliminate_common_subexpressions(stmts1)
    
    print("  原始:")
    for lhs, op, args in stmts1:
        print(f"    {lhs} = {' '.join(args)}")
    
    print("  优化后:")
    for lhs, op, args in optimized1:
        print(f"    {lhs} = {' '.join(args)}")
    
    # 测试2: 复杂情况
    print("\n测试2 - 复杂CSE:")
    
    # a = x + y
    # b = x + y
    # c = a + b
    # d = x + y  # 重复
    
    stmts2 = [
        ('a', '+', ['x', 'y']),
        ('b', '+', ['x', 'y']),
        ('c', '+', ['a', 'b']),
        ('d', '+', ['x', 'y']),
    ]
    
    optimized2 = eliminate_common_subexpressions(stmts2)
    
    print("  原始:")
    for lhs, op, args in stmts2:
        print(f"    {lhs} = {' '.join(args)}")
    
    print("  优化后:")
    for lhs, op, args in optimized2:
        print(f"    {lhs} = {' '.join(args)}")
    
    # 测试3: 变量重新定义导致CSE无效
    print("\n测试3 - 变量重新定义:")
    
    # a = x + y
    # x = z + 1  # x被重新定义
    # b = x + y  # CSE无效,需要重新计算
    
    stmts3 = [
        ('a', '+', ['x', 'y']),
        ('x', '+', ['z', '1']),
        ('b', '+', ['x', 'y']),
    ]
    
    optimized3 = eliminate_common_subexpressions(stmts3)
    
    print("  原始:")
    for lhs, op, args in stmts3:
        print(f"    {lhs} = {' '.join(args)}")
    
    print("  优化后:")
    for lhs, op, args in optimized3:
        print(f"    {lhs} = {' '.join(args)}")
    
    # 测试4: 嵌套表达式
    print("\n测试4 - 嵌套表达式:")
    
    # a = (x + y) * (x + y)
    # b = (x + y) * 2
    # c = a + b
    
    stmts4 = [
        ('t1', '+', ['x', 'y']),
        ('a', '*', ['t1', 't1']),
        ('b', '*', ['t1', '2']),
        ('c', '+', ['a', 'b']),
    ]
    
    print("  原始(展开后):")
    for lhs, op, args in stmts4:
        print(f"    {lhs} = {' '.join(args)}")
    
    optimized4 = eliminate_common_subexpressions(stmts4)
    
    print("  优化后:")
    for lhs, op, args in optimized4:
        print(f"    {lhs} = {' '.join(args)}")
    
    # 测试5: 验证CSE
    print("\n测试5 - 验证CSE:")
    
    # 模拟执行原始和优化后的程序
    def simulate(stmts):
        env = {'x': 2, 'y': 3, 'z': 1}
        for lhs, op, args in stmts:
            vals = [env.get(a, 0) for a in args]
            if op == '+':
                result = sum(vals)
            elif op == '*':
                result = 1
                for v in vals:
                    result *= v
            env[lhs] = result
        return env
    
    env_orig = simulate(stmts4)
    env_opt = simulate(optimized4)
    
    print(f"  原始结果: {env_orig}")
    print(f"  优化结果: {env_opt}")
    print(f"  一致: {env_orig.get('c') == env_opt.get('c')}")
    
    print("\n所有测试完成!")
