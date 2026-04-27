# -*- coding: utf-8 -*-
"""
算法实现：程序分析 / symbolic_execution

本文件实现 symbolic_execution 相关的算法功能。
"""

from typing import Dict, List, Set, Optional, Tuple, Any, Union
from abc import ABC, abstractmethod
from collections import defaultdict
import operator


class SymbolicExpression(ABC):
    """
    符号表达式的基类
    """
    
    @abstractmethod
    def __str__(self) -> str:
        pass
    
    @abstractmethod
    def substitute(self, var: str, expr: 'SymbolicExpression') -> 'SymbolicExpression':
        """替换变量"""
        pass
    
    @abstractmethod
    def get_free_variables(self) -> Set[str]:
        """获取自由变量集合"""
        pass


class SymbolicConstant(SymbolicExpression):
    """
    符号常量
    """
    
    def __init__(self, value: Any):
        """
        初始化符号常量
        
        Args:
            value: 常量值
        """
        self.value = value
    
    def __str__(self) -> str:
        return str(self.value)
    
    def substitute(self, var: str, expr: SymbolicExpression) -> 'SymbolicConstant':
        return self
    
    def get_free_variables(self) -> Set[str]:
        return set()


class SymbolicVariable(SymbolicExpression):
    """
    符号变量
    """
    
    def __init__(self, name: str):
        """
        初始化符号变量
        
        Args:
            name: 变量名
        """
        self.name = name
    
    def __str__(self) -> str:
        return self.name
    
    def substitute(self, var: str, expr: SymbolicExpression) -> SymbolicExpression:
        if self.name == var:
            return expr
        return self
    
    def get_free_variables(self) -> Set[str]:
        return {self.name}


class SymbolicBinaryOp(SymbolicExpression):
    """
    符号二元运算
    """
    
    def __init__(self, left: SymbolicExpression, op: str, right: SymbolicExpression):
        """
        初始化符号二元运算
        
        Args:
            left: 左操作数
            op: 运算符
            right: 右操作数
        """
        self.left = left
        self.op = op
        self.right = right
    
    def __str__(self) -> str:
        return f"({self.left} {self.op} {self.right})"
    
    def substitute(self, var: str, expr: SymbolicExpression) -> 'SymbolicBinaryOp':
        return SymbolicBinaryOp(
            self.left.substitute(var, expr),
            self.op,
            self.right.substitute(var, expr)
        )
    
    def get_free_variables(self) -> Set[str]:
        return self.left.get_free_variables() | self.right.get_free_variables()


class SymbolicPathCondition:
    """
    符号路径条件
    
    管理路径约束，支持添加约束和求解。
    注意：这里使用简化的约束表示，实际需要SMT求解器。
    """
    
    def __init__(self):
        """初始化路径条件"""
        self.constraints: List[Tuple[str, Any, Any]] = []  # (op, left, right)
        # op 可以是: '==', '!=', '<', '>', '<=', '>=', 'and', 'or'
    
    def add_constraint(self, left: SymbolicExpression, op: str, right: SymbolicExpression):
        """
        添加路径约束
        
        Args:
            left: 左表达式
            op: 运算符
            right: 右表达式
        """
        self.constraints.append((left, op, right))
    
    def add_path(self, constraint: Tuple):
        """
        添加一个完整约束
        
        Args:
            constraint: (left, op, right) 元组
        """
        self.constraints.append(constraint)
    
    def is_satisfiable(self) -> bool:
        """
        检查路径条件是否可满足
        
        这是一个简化实现，假设所有约束都是线性的。
        实际需要使用SMT求解器（如Z3）。
        
        Returns:
            如果可满足返回True
        """
        # 简化检查：没有明显冲突就认为可满足
        # 收集所有变量约束
        var_constraints: Dict[str, List] = defaultdict(list)
        
        for left, op, right in self.constraints:
            for var in left.get_free_variables():
                var_constraints[var].append((op, right))
        
        # 简化检查：如果存在 var < c1 和 var > c2 且 c1 < c2，则冲突
        for var, constrs in var_constraints.items():
            lowers = []
            uppers = []
            for op, right in constrs:
                # 尝试解析数值
                try:
                    val = int(str(right))
                    if op == '<':
                        uppers.append(val - 1)
                    elif op == '>':
                        lowers.append(val + 1)
                    elif op == '<=':
                        uppers.append(val)
                    elif op == '>=':
                        lowers.append(val)
                except:
                    pass
        
        if lowers and uppers:
            if max(lowers) > min(uppers):
                return False
        
        return True
    
    def solve(self, var: str) -> Optional[Any]:
        """
        尝试求解变量的一个可行值
        
        简化实现，不使用SMT求解器。
        
        Args:
            var: 要求解的变量名
            
        Returns:
            一个可行值，如果不可满足返回None
        """
        if not self.is_satisfiable():
            return None
        
        # 简化实现：收集约束
        lower = None
        upper = None
        
        for left, op, right in self.constraints:
            if str(left) != var:
                continue
            try:
                val = int(str(right))
                if op in ['>=', '>']:
                    lower = max(lower if lower else float('-inf'), val)
                if op in ['<=', '<']:
                    upper = min(upper if upper else float('inf'), val)
            except:
                pass
        
        # 返回一个简单解
        if lower is not None:
            return lower
        if upper is not None:
            return upper
        
        return 0  # 默认值
    
    def __str__(self) -> str:
        parts = []
        for left, op, right in self.constraints:
            parts.append(f"{left} {op} {right}")
        return " ∧ ".join(parts) if parts else "true"


class SymbolicState:
    """
    符号执行状态
    
    包含符号存储和路径条件。
    """
    
    def __init__(self):
        """初始化符号状态"""
        # 符号存储：变量名 -> 符号表达式
        self.symbolic_store: Dict[str, SymbolicExpression] = {}
        # 路径条件
        self.path_condition = SymbolicPathCondition()
        # 约束计数器
        self.constraint_id = 0
    
    def assign(self, var: str, expr: SymbolicExpression):
        """
        赋值语句
        
        Args:
            var: 变量名
            expr: 符号表达式
        """
        self.symbolic_store[var] = expr
    
    def read(self, var: str) -> SymbolicExpression:
        """
        读取变量
        
        Args:
            var: 变量名
            
        Returns:
            变量的符号表达式
        """
        if var in self.symbolic_store:
            return self.symbolic_store[var]
        return SymbolicVariable(var)
    
    def add_path_condition(self, left: SymbolicExpression, op: str, right: SymbolicExpression):
        """
        添加路径条件
        
        Args:
            left: 左表达式
            op: 运算符
            right: 右表达式
        """
        self.path_condition.add_constraint(left, op, right)
    
    def fork(self) -> 'SymbolicState':
        """
        派生（复制）当前状态
        
        用于分支处的状态分裂。
        
        Returns:
            新的符号状态（副本）
        """
        new_state = SymbolicState()
        new_state.symbolic_store = dict(self.symbolic_store)
        new_state.path_condition = SymbolicPathCondition()
        new_state.path_condition.constraints = list(self.path_condition.constraints)
        return new_state
    
    def __str__(self) -> str:
        lines = ["Symbolic State:", "  Store:"]
        for var, expr in sorted(self.symbolic_store.items()):
            lines.append(f"    {var} = {expr}")
        lines.append(f"  Path Condition: {self.path_condition}")
        return "\n".join(lines)


class SymbolicExecutor:
    """
    符号执行引擎
    """
    
    def __init__(self):
        """初始化符号执行引擎"""
        self.states: List[SymbolicState] = [SymbolicState()]  # 初始状态
        self.executed_paths: List[Tuple[SymbolicState, List[str]]] = []
    
    def execute_program(self, program: List[Tuple[str, str, str]]):
        """
        执行符号程序
        
        Args:
            program: 程序语句列表，每条语句为 (stmt_type, lhs, rhs)
                     stmt_type 可以是: 'assign', 'if', 'goto', 'return'
        """
        self._execute_block(0, program, self.states[0])
    
    def _execute_block(self, pc: int, program: List, state: SymbolicState):
        """
        执行程序块
        
        Args:
            pc: 程序计数器
            program: 程序列表
            state: 当前符号状态
        """
        while pc < len(program):
            stmt_type, lhs, rhs = program[pc]
            
            if stmt_type == 'assign':
                # 赋值语句
                result = self._eval_expr(rhs, state)
                state.assign(lhs, result)
                pc += 1
            
            elif stmt_type == 'if':
                # 条件分支
                cond = self._eval_condition(lhs, rhs, state)
                if cond:
                    # then分支：添加约束，继续执行
                    new_state = state.fork()
                    new_state.add_path_condition(
                        SymbolicVariable(lhs), rhs, SymbolicConstant(0)
                    )
                    self.executed_paths.append((new_state, ['if-then']))
                    self._execute_block(pc + 1, program, new_state)
                pc += 1
            
            elif stmt_type == 'goto':
                # 无条件跳转
                try:
                    target = int(rhs)
                    pc = target
                except:
                    pc += 1
            
            elif stmt_type == 'return':
                # 返回语句
                self.executed_paths.append((state, [f'return {lhs}']))
                return
            
            else:
                pc += 1
    
    def _eval_expr(self, expr_str: str, state: SymbolicState) -> SymbolicExpression:
        """
        评估符号表达式
        
        Args:
            expr_str: 表达式字符串
            state: 当前状态
            
        Returns:
            符号表达式
        """
        expr_str = expr_str.strip()
        
        # 检查是否是数字
        try:
            return SymbolicConstant(int(expr_str))
        except ValueError:
            pass
        
        # 检查是否是简单变量
        if expr_str.isidentifier():
            return state.read(expr_str)
        
        # 检查二元运算
        for op in ['+', '-', '*', '/']:
            if op in expr_str:
                parts = expr_str.split(op, 1)
                if len(parts) == 2:
                    left = self._eval_expr(parts[0], state)
                    right = self._eval_expr(parts[1], state)
                    return SymbolicBinaryOp(left, op, right)
        
        return SymbolicVariable(expr_str)
    
    def _eval_condition(self, var: str, op: str, state: SymbolicState) -> bool:
        """
        评估条件（简化实现，假设总是可以满足）
        
        Args:
            var: 变量名
            op: 运算符
            state: 当前状态
            
        Returns:
            是否为真
        """
        # 简化实现
        return True
    
    def get_feasible_paths(self) -> List[SymbolicState]:
        """
        获取所有可行路径
        
        Returns:
            可行路径状态列表
        """
        return [state for state, _ in self.executed_paths if state.path_condition.is_satisfiable()]
    
    def generate_test_cases(self) -> List[Dict[str, int]]:
        """
        生成测试用例
        
        Returns:
            测试用例列表
        """
        test_cases = []
        for state, _ in self.executed_paths:
            if state.path_condition.is_satisfiable():
                test_case = {}
                for var in state.symbolic_store:
                    val = state.path_condition.solve(var)
                    if val is not None:
                        test_case[var] = val
                if test_case:
                    test_cases.append(test_case)
        return test_cases


def example_max():
    """
    示例：求最大值程序的符号执行
    
    程序：
        input x
        input y
        if x > y:
            max = x
        else:
            max = y
        return max
    """
    program = [
        ('assign', 'x', 'x'),     # input x (简化)
        ('assign', 'y', 'y'),     # input y
        ('if', 'x', '>', 'y'),    # if x > y then goto 4 else 5
        ('assign', 'max', 'x'),   # then分支
        ('goto', '', '6'),        # 跳过else
        ('assign', 'max', 'y'),   # else分支
        ('return', 'max', ''),
    ]
    
    return program


def example_absolute():
    """
    示例：求绝对值程序的符号执行
    
    程序：
        input x
        if x < 0:
            x = -x
        return x
    """
    program = [
        ('assign', 'x', 'x'),     # input x
        ('if', 'x', '<', '0'),     # if x < 0 then goto 3 else 4
        ('assign', 'x', '-x'),    # then分支
        ('return', 'x', ''),      # return x
    ]
    
    return program


if __name__ == "__main__":
    print("=" * 60)
    print("测试1：求最大值程序的符号执行")
    print("=" * 60)
    
    executor = SymbolicExecutor()
    program = example_max()
    
    print("\n程序:")
    for i, (t, l, r) in enumerate(program):
        print(f"  {i}: {t} {l} {r}")
    
    executor.execute_program(program)
    
    print(f"\n执行路径数: {len(executor.executed_paths)}")
    
    print("\n可行路径的测试用例:")
    for i, tc in enumerate(executor.generate_test_cases()):
        print(f"  Test {i+1}: {tc}")
    
    print("\n" + "=" * 60)
    print("测试2：求绝对值程序的符号执行")
    print("=" * 60)
    
    executor2 = SymbolicExecutor()
    program2 = example_absolute()
    
    print("\n程序:")
    for i, (t, l, r) in enumerate(program2):
        print(f"  {i}: {t} {l} {r}")
    
    executor2.execute_program(program2)
    
    print(f"\n执行路径数: {len(executor2.executed_paths)}")
    
    print("\n可行路径的测试用例:")
    for i, tc in enumerate(executor2.generate_test_cases()):
        print(f"  Test {i+1}: {tc}")
    
    print("\n" + "=" * 60)
    print("测试3：符号表达式操作")
    print("=" * 60)
    
    # 创建符号表达式
    x = SymbolicVariable("x")
    y = SymbolicVariable("y")
    
    expr1 = SymbolicBinaryOp(x, '+', SymbolicConstant(5))
    expr2 = SymbolicBinaryOp(expr1, '*', y)
    
    print(f"\n符号表达式: {expr2}")
    print(f"自由变量: {expr2.get_free_variables()}")
    
    # 替换
    substituted = expr2.substitute("x", SymbolicConstant(10))
    print(f"替换 x=10 后: {substituted}")
    
    print("\n符号执行测试完成!")
    print("\n注意：实际符号执行需要集成SMT求解器（如Z3）来：")
    print("  1. 正确判断路径可行性")
    print("  2. 生成精确的测试用例")
    print("  3. 处理复杂的非线性约束")
