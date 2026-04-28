# -*- coding: utf-8 -*-
"""
Concolic执行（混合符号执行）
功能：结合具体执行和符号执行，利用具体值引导符号分析

Concolic = Con(crete) + Sym(bolic)

工作流程：
1. 使用具体输入运行程序，记录分支
2. 对路径条件取反，生成新输入
3. 重复直到覆盖所有分支

优点：
- 避免路径爆炸（具体值引导）
- 能发现深层bug
- 自动生成测试用例

作者：Concolic Testing Team
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict


class ConcolicValue:
    """混合值：具体值+符号表达式"""
    
    def __init__(self, concrete: Any, symbolic: 'SymExpr'):
        self.concrete = concrete
        self.symbolic = symbolic


class SymExpr:
    """符号表达式（简化版）"""
    
    def __init__(self, name: str = None, value: Any = None, 
                 op: str = None, args: List['SymExpr'] = None):
        self.name = name  # 变量名或None
        self.value = value  # 具体常量值
        self.op = op  # 操作符 +, -, *, etc
        self.args = args or []
    
    def __repr__(self):
        if self.name:
            return self.name
        if self.value is not None:
            return str(self.value)
        if self.op and self.args:
            arg_str = f" {self.op} ".join(str(a) for a in self.args)
            return f"({arg_str})"
        return "?"


class ConcolicState:
    """Concolic执行状态"""
    
    def __init__(self):
        self.concrete_env: Dict[str, Any] = {}  # 具体环境
        self.symbolic_env: Dict[str, SymExpr] = {}  # 符号环境
        self.path_constraint: List[Tuple[str, SymExpr]] = []  # 路径约束 (op, expr)
        self.constraints: List[Tuple[str, SymExpr]] = []  # 所有约束

    def set_var(self, name: str, concrete: Any, symbolic: SymExpr):
        """设置变量"""
        self.concrete_env[name] = concrete
        self.symbolic_env[name] = symbolic

    def get_concrete(self, name: str) -> Any:
        return self.concrete_env.get(name)

    def get_symbolic(self, name: str) -> SymExpr:
        if name in self.symbolic_env:
            return self.symbolic_env[name]
        return SymExpr(name=name)

    def add_constraint(self, cond: str, expr: SymExpr):
        """添加约束"""
        self.constraints.append((cond, expr))
        self.path_constraint.append((cond, expr))


class ConcolicExecutor:
    """
    Concolic执行引擎
    
    使用DFS探索分支，配合SMT求解器生成新输入
    """

    def __init__(self):
        self.branches_covered: Set[Tuple[int, bool]] = set()  # (pc, condition_is_true)
        self.test_cases: List[Dict[str, Any]] = []  # 生成的测试用例

    def concolic_execute(self, program: List, initial_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行concolic测试生成
        
        Args:
            program: 程序语句列表
            initial_input: 初始具体输入
            
        Returns:
            生成的测试用例列表
        """
        state = ConcolicState()
        for name, val in initial_input.items():
            state.set_var(name, val, SymExpr(name=name))
        
        self._execute_recursive(program, state, 0)
        return self.test_cases

    def _execute_recursive(self, program: List, state: ConcolicState, pc: int):
        """递归执行"""
        if pc >= len(program):
            # 记录测试用例
            self.test_cases.append(state.concrete_env.copy())
            return
        
        stmt = program[pc]
        stmt_type = stmt['type']
        
        if stmt_type == 'assign':
            # y = expr
            concrete_val = self._eval_concrete(stmt['expr'], state.concrete_env)
            symbolic_val = self._eval_symbolic(stmt['expr'], state)
            state.set_var(stmt['lhs'], concrete_val, symbolic_val)
            self._execute_recursive(program, state, pc + 1)
        
        elif stmt_type == 'if':
            # 分支处理
            cond_sym = self._eval_symbolic(stmt['cond'], state)
            cond_conc = self._eval_concrete(stmt['cond'], state.concrete_env)
            
            # 尝试then分支
            if (pc, True) not in self.branches_covered:
                self.branches_covered.add((pc, True))
                then_state = self._copy_state(state)
                then_state.add_constraint('true', cond_sym)
                self._execute_recursive(program, then_state, stmt['then_pc'])
            
            # 尝试else分支
            if (pc, False) not in self.branches_covered:
                self.branches_covered.add((pc, False))
                else_state = self._copy_state(state)
                neg_cond = self._negate(cond_sym)
                else_state.add_constraint('false', neg_cond)
                self._execute_recursive(program, else_state, stmt['else_pc'])
        
        elif stmt_type == 'input':
            # 输入变量：使用符号值
            state.set_var(stmt['var'], 0, SymExpr(name=stmt['var']))
            self._execute_recursive(program, state, pc + 1)
        
        elif stmt_type == 'output':
            # 输出：记录
            print(f"Output: {state.concrete_env.get(stmt['var'], '?')}")
            self._execute_recursive(program, state, pc + 1)

    def _eval_concrete(self, expr, env: Dict[str, Any]) -> Any:
        """具体求值"""
        if isinstance(expr, dict):
            op = expr['op']
            args = [self._eval_concrete(expr['args'][i], env) for i in range(len(expr['args']))]
            
            if op == '+':
                return args[0] + args[1]
            if op == '-':
                return args[0] - args[1]
            if op == '*':
                return args[0] * args[1]
            if op == '/':
                return args[0] // args[1]
            if op == '>':
                return args[0] > args[1]
            if op == '>=':
                return args[0] >= args[1]
            if op == '<':
                return args[0] < args[1]
            if op == '<=':
                return args[0] <= args[1]
            if op == '==':
                return args[0] == args[1]
        
        if isinstance(expr, str):
            return env.get(expr, 0)
        
        return expr  # 常量

    def _eval_symbolic(self, expr, state: ConcolicState) -> SymExpr:
        """符号求值"""
        if isinstance(expr, dict):
            args = [self._eval_symbolic(expr['args'][i], state) for i in range(len(expr['args']))]
            return SymExpr(op=expr['op'], args=args)
        
        if isinstance(expr, str):
            return state.get_symbolic(expr)
        
        return SymExpr(value=expr)

    def _negate(self, sym: SymExpr) -> SymExpr:
        """否定符号表达式"""
        if sym.op == '>':
            return SymExpr(op='<=', args=[sym.args[0], sym.args[1]])
        if sym.op == '>=':
            return SymExpr(op='<', args=[sym.args[0], sym.args[1]])
        if sym.op == '<':
            return SymExpr(op='>=', args=[sym.args[0], sym.args[1]])
        if sym.op == '<=':
            return SymExpr(op='>', args=[sym.args[0], sym.args[1]])
        if sym.op == '==':
            return SymExpr(op='!=', args=[sym.args[0], sym.args[1]])
        return SymExpr(op='!', args=[sym])

    def _copy_state(self, state: ConcolicState) -> ConcolicState:
        """复制状态"""
        new_state = ConcolicState()
        new_state.concrete_env = dict(state.concrete_env)
        new_state.symbolic_env = dict(state.symbolic_env)
        new_state.constraints = list(state.constraints)
        new_state.path_constraint = list(state.path_constraint)
        return new_state

    def generate_input_from_constraint(self, constraint: Tuple[str, SymExpr]) -> Dict[str, Any]:
        """
        从约束生成具体输入（简化版）
        
        实际应用中应调用SMT求解器
        """
        cond, expr = constraint
        # 简化：猜测一个满足约束的值
        if expr.name:
            return {expr.name: 1}
        return {}


def example_simple():
    """简单concolic测试"""
    executor = ConcolicExecutor()
    
    # 程序: input x; if x > 0: y = 1 else: y = 0
    program = [
        {'type': 'input', 'var': 'x'},
        {'type': 'if', 'cond': {'op': '>', 'args': ['x', 0]}, 'then_pc': 3, 'else_pc': 5},
        {'type': 'assign', 'lhs': 'y', 'expr': 1},
        {'type': 'output', 'var': 'y'},
        {'type': 'assign', 'lhs': 'y', 'expr': 0},
        {'type': 'output', 'var': 'y'},
    ]
    
    test_cases = executor.concolic_execute(program, {'x': 1})
    print(f"生成 {len(test_cases)} 个测试用例:")
    for tc in test_cases:
        print(f"  {tc}")


def example_branch_coverage():
    """分支覆盖示例"""
    executor = ConcolicExecutor()
    
    # x = input; if x > 10: if x > 20: y = 3 else y = 2 else y = 1
    program = [
        {'type': 'input', 'var': 'x'},
        {'type': 'if', 'cond': {'op': '>', 'args': ['x', 10]}, 'then_pc': 2, 'else_pc': 7},
        {'type': 'if', 'cond': {'op': '>', 'args': ['x', 20]}, 'then_pc': 4, 'else_pc': 5},
        {'type': 'assign', 'lhs': 'y', 'expr': 3},
        {'type': 'assign', 'lhs': 'y', 'expr': 2},
        {'type': 'assign', 'lhs': 'y', 'expr': 1},
        {'type': 'output', 'var': 'y'},
    ]
    
    test_cases = executor.concolic_execute(program, {'x': 15})
    print(f"分支覆盖: {len(executor.branches_covered)} 个分支被覆盖")
    print(f"生成 {len(test_cases)} 个测试用例")


if __name__ == "__main__":
    print("=" * 50)
    print("Concolic执行测试")
    print("=" * 50)
    
    example_simple()
    print()
    example_branch_coverage()
