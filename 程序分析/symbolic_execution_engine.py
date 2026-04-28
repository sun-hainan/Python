# -*- coding: utf-8 -*-
"""
符号执行引擎
功能：对程序进行符号执行，探索所有可能路径，收集路径条件

核心概念：
- Symbolic Value（符号值）：表示未知输入的符号表达式
- Path Condition（路径条件）：当前路径上所有分支条件的合取
- State（状态）：变量映射到符号值的映射 + 路径条件

应用：
1. 自动化测试生成
2. 漏洞发现
3. 程序验证

作者：Symbolic Execution Team
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from enum import Enum


class ExprKind(Enum):
    """表达式类型"""
    CONST = "const"
    VAR = "var"
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    AND = "and"
    OR = "or"
    NOT = "not"
    LT = "lt"
    LE = "le"
    GT = "gt"
    GE = "ge"
    EQ = "eq"
    NE = "ne"


class SymExpr:
    """符号表达式"""
    
    def __init__(self, kind: ExprKind, args: List['SymExpr'] = None, value: Any = None):
        self.kind = kind
        self.args = args or []
        self.value = value  # 常量值或变量名
    
    def __repr__(self):
        if self.kind == ExprKind.CONST:
            return str(self.value)
        if self.kind == ExprKind.VAR:
            return f"${self.value}"
        if self.kind == ExprKind.ADD:
            return f"({self.args[0]} + {self.args[1]})"
        if self.kind == ExprKind.SUB:
            return f"({self.args[0]} - {self.args[1]})"
        if self.kind == ExprKind.MUL:
            return f"({self.args[0]} * {self.args[1]})"
        if self.kind == ExprKind.LT:
            return f"({self.args[0]} < {self.args[1]})"
        if self.kind == ExprKind.EQ:
            return f"({self.args[0]} == {self.args[1]})"
        return f"{self.kind.name}"


class SymState:
    """符号执行状态"""
    
    def __init__(self):
        self.env: Dict[str, SymExpr] = {}  # 变量→符号表达式
        self.path_cond: List[SymExpr] = []  # 路径条件
        self.pc_index = 0  # 程序计数器

    def copy(self) -> 'SymState':
        """复制状态"""
        new_state = SymState()
        new_state.env = dict(self.env)
        new_state.path_cond = list(self.path_cond)
        new_state.pc_index = self.pc_index
        return new_state

    def add_constraint(self, cond: SymExpr):
        """添加路径条件"""
        self.path_cond.append(cond)

    def eval(self, var_name: str) -> SymExpr:
        """求值变量"""
        if var_name in self.env:
            return self.env[var_name]
        return SymExpr(ExprKind.VAR, value=var_name)

    def assign(self, var_name: str, expr: SymExpr):
        """赋值"""
        self.env[var_name] = expr


class StmtKind(Enum):
    """语句类型"""
    ASSIGN = "assign"
    IF = "if"
    WHILE = "while"
    ASSUME = "assume"
    ASSERT = "assert"
    INPUT = "input"
    OUTPUT = "output"
    SKIP = "skip"


class Stmt:
    """语句"""
    def __init__(self, kind: StmtKind, **kwargs):
        self.kind = kind
        for key, val in kwargs.items():
            setattr(self, key, val)


class SymbolicExecutor:
    """
    符号执行引擎
    
    使用DFS探索程序路径
    """

    def __init__(self):
        self.stmts: List[Stmt] = []
        self.paths: List[List[SymExpr]] = []  # 收集的路径条件
        self.state_count = 0

    def load_program(self, stmts: List[Stmt]):
        """加载程序语句"""
        self.stmts = stmts

    def execute(self) -> List[List[SymExpr]]:
        """
        执行符号执行
        
        Returns:
            所有可行路径的条件列表
        """
        initial_state = SymState()
        self._execute_recursive(initial_state, 0)
        return self.paths

    def _execute_recursive(self, state: SymState, pc: int):
        """递归执行"""
        if pc >= len(self.stmts):
            # 程序结束：记录路径
            self.paths.append(state.path_cond.copy())
            return
        
        stmt = self.stmts[pc]
        
        if stmt.kind == StmtKind.ASSIGN:
            # x := e
            expr = self._eval_expr(stmt.expr, state)
            state.assign(stmt.lhs, expr)
            self._execute_recursive(state, pc + 1)
        
        elif stmt.kind == StmtKind.IF:
            # if b then s1 else s2
            cond = self._eval_expr(stmt.cond, state)
            
            # then分支：添加cond为真
            then_state = state.copy()
            then_state.add_constraint(cond)
            self._execute_recursive(then_state, stmt.then_pc)
            
            # else分支：添加cond为假
            else_state = state.copy()
            else_state.add_constraint(SymExpr(ExprKind.NOT, args=[cond]))
            self._execute_recursive(else_state, stmt.else_pc)
        
        elif stmt.kind == StmtKind.WHILE:
            # while b do s
            # 展平为if分支
            loop_state = state.copy()
            cond = self._eval_expr(stmt.cond, loop_state)
            loop_state.add_constraint(cond)
            self._execute_recursive(loop_state, stmt.body_pc)
        
        elif stmt.kind == StmtKind.ASSUME:
            # assume b（假设条件成立）
            cond = self._eval_expr(stmt.cond, state)
            new_state = state.copy()
            new_state.add_constraint(cond)
            self._execute_recursive(new_state, pc + 1)
        
        elif stmt.kind == StmtKind.INPUT:
            # read x → x变为符号输入
            state.assign(stmt.var, SymExpr(ExprKind.VAR, value=stmt.var))
            self._execute_recursive(state, pc + 1)
        
        elif stmt.kind == StmtKind.SKIP:
            self._execute_recursive(state, pc + 1)

    def _eval_expr(self, expr_data, state: SymState) -> SymExpr:
        """求值表达式"""
        if isinstance(expr_data, tuple):
            op = expr_data[0]
            args = [self._eval_expr(a, state) for a in expr_data[1:]]
            
            if op == '+':
                return SymExpr(ExprKind.ADD, args=args)
            if op == '-':
                return SymExpr(ExprKind.SUB, args=args)
            if op == '*':
                return SymExpr(ExprKind.MUL, args=args)
            if op == '<':
                return SymExpr(ExprKind.LT, args=args)
            if op == '<=':
                return SymExpr(ExprKind.LE, args=args)
            if op == '>':
                return SymExpr(ExprKind.GT, args=args)
            if op == '>=':
                return SymExpr(ExprKind.GE, args=args)
            if op == '==':
                return SymExpr(ExprKind.EQ, args=args)
            if op == '!=':
                neq = SymExpr(ExprKind.EQ, args=args)
                return SymExpr(ExprKind.NOT, args=[neq])
        
        if isinstance(expr_data, (int, float)):
            return SymExpr(ExprKind.CONST, value=expr_data)
        
        if isinstance(expr_data, str):
            return state.eval(expr_data)
        
        return SymExpr(ExprKind.VAR, value=str(expr_data))


def example_simple():
    """简单示例"""
    executor = SymbolicExecutor()
    
    # 程序: x = input; if x > 0 then y = x else y = -x
    stmts = [
        Stmt(StmtKind.INPUT, var='x'),
        Stmt(StmtKind.ASSIGN, lhs='y', expr=('+', 'x', 0)),  # 临时
        Stmt(StmtKind.IF, cond=('>', 'x', 0), then_pc=5, else_pc=7),
        # then分支: y = x
        Stmt(StmtKind.ASSIGN, lhs='y', expr='x'),
        Stmt(StmtKind.SKIP),  # placeholder
        # else分支: y = -x
        Stmt(StmtKind.ASSIGN, lhs='y', expr=('*', -1, 'x')),
        Stmt(StmtKind.SKIP),
    ]
    
    executor.load_program(stmts)
    paths = executor.execute()
    
    print(f"找到 {len(paths)} 条路径")
    for i, path in enumerate(paths):
        print(f"  路径{i+1}: {[str(p) for p in path]}")


def example_branch():
    """多分支示例"""
    executor = SymbolicExecutor()
    
    # x = input; if x > 0: if x > 10: y = 2 else y = 1 else y = 0
    stmts = [
        Stmt(StmtKind.INPUT, var='x'),
        Stmt(StmtKind.IF, cond=('>', 'x', 0), then_pc=2, else_pc=6),
        # outer then: inner if
        Stmt(StmtKind.IF, cond=('>', 'x', 10), then_pc=4, else_pc=5),
        Stmt(StmtKind.ASSIGN, lhs='y', expr=2),
        Stmt(StmtKind.SKIP),
        Stmt(StmtKind.ASSIGN, lhs='y', expr=1),
        Stmt(StmtKind.SKIP),
        # outer else
        Stmt(StmtKind.ASSIGN, lhs='y', expr=0),
        Stmt(StmtKind.SKIP),
    ]
    
    executor.load_program(stmts)
    paths = executor.execute()
    
    print(f"找到 {len(paths)} 条路径")
    for i, path in enumerate(paths):
        print(f"  路径{i+1}: {path}")


if __name__ == "__main__":
    print("=" * 50)
    print("符号执行引擎 测试")
    print("=" * 50)
    
    example_simple()
    print()
    example_branch()
