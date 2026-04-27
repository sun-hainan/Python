# -*- coding: utf-8 -*-
"""
算法实现：程序语言理论 / operational_semantics

本文件实现 operational_semantics 相关的算法功能。
"""

from typing import List, Optional, Dict, Tuple, Set, Generic, TypeVar
from dataclasses import dataclass, field
from enum import Enum, auto


T = TypeVar('T')


class Expr:
    """表达式基类"""
    def free_vars(self) -> Set[str]:
        raise NotImplementedError


@dataclass
class E_Var(Expr):
    """变量 x"""
    name: str

    def __str__(self):
        return self.name

    def free_vars(self) -> Set[str]:
        return {self.name}


@dataclass
class E_Num(Expr):
    """数值 n"""
    value: int

    def __str__(self):
        return str(self.value)


@dataclass
class E_Bool(Expr):
    """布尔值 b"""
    value: bool

    def __str__(self):
        return str(self.value).lower()


@dataclass
class E_Abs(Expr):
    """λ抽象 λx.e"""
    var: str
    body: Expr

    def __str__(self):
        return f"(λ{self.var}. {self.body})"

    def free_vars(self) -> Set[str]:
        return self.body.free_vars() - {self.var}


@dataclass
class E_App(Expr):
    """函数应用 e1 e2"""
    func: Expr
    arg: Expr

    def __str__(self):
        func_str = str(self.func)
        if isinstance(self.func, (E_Abs, E_If)):
            func_str = f"({func_str})"
        arg_str = str(self.arg)
        if isinstance(self.arg, (E_Abs, E_If)):
            arg_str = f"({arg_str})"
        return f"{func_str} {arg_str}"

    def free_vars(self) -> Set[str]:
        return self.func.free_vars() | self.arg.free_vars()


@dataclass
class E_If(Expr):
    """条件 if e1 then e2 else e3"""
    cond: Expr
    then_branch: Expr
    else_branch: Expr

    def __str__(self):
        return f"if {self.cond} then {self.then_branch} else {self.else_branch}"

    def free_vars(self) -> Set[str]:
        return self.cond.free_vars() | self.then_branch.free_vars() | self.else_branch.free_vars()


@dataclass
class E_Let(Expr):
    """Let绑定 let x = e1 in e2"""
    var: str
    value: Expr
    body: Expr

    def __str__(self):
        return f"let {self.var} = {self.value} in {self.body}"

    def free_vars(self) -> Set[str]:
        return self.value.free_vars() | (self.body.free_vars() - {self.var})


@dataclass
class E_Op(Expr):
    """二元操作 e1 op e2"""
    left: Expr
    op: str
    right: Expr

    def __str__(self):
        return f"({self.left} {self.op} {self.right})"

    def free_vars(self) -> Set[str]:
        return self.left.free_vars() | self.right.free_vars()


# 配置（配置 = 表达式 + 环境）
@dataclass
class Configuration:
    """小步语义配置"""
    expr: Expr
    env: Dict[str, any]  # 环境


class Small_Step_Semantics:
    """
    小步语义（Structural Operational Semantics, SOS）
    定义单步归约关系: (e, σ) → (e', σ')
    """
    def __init__(self):
        self.steps: List[Tuple[Configuration, Configuration]] = []
        self.max_steps = 1000


    def is_value(self, e: Expr) -> bool:
        """判断是否是值（不需进一步归约）"""
        return isinstance(e, (E_Num, E_Bool, E_Abs))


    def step(self, config: Configuration) -> Optional[Configuration]:
        """
        单步归约
        返回: 归约后的配置，如果没有归约规则适用则返回None
        """
        expr = config.expr
        env = config.env
        # E-IfTrue
        if isinstance(expr, E_If):
            cond = expr.cond
            if isinstance(cond, E_Bool):
                if cond.value:
                    return Configuration(expr.then_branch, env)
                else:
                    return Configuration(expr.else_branch, env)
            else:
                # 归约条件
                next_cond = self.step(Configuration(cond, env))
                if next_cond:
                    return Configuration(E_If(next_cond.expr, expr.then_branch, expr.else_branch), env)
        # E-App
        if isinstance(expr, E_App):
            func = expr.func
            arg = expr.arg
            if isinstance(func, E_Abs):
                # β归约
                new_body = substitute(expr.body, expr.var, arg)
                return Configuration(new_body, env)
            else:
                # 归约函数
                next_func = self.step(Configuration(func, env))
                if next_func:
                    return Configuration(E_App(next_func.expr, arg), env)
                # 归约参数
                next_arg = self.step(Configuration(arg, env))
                if next_arg:
                    return Configuration(E_App(func, next_arg.expr), env)
        # E-Let
        if isinstance(expr, E_Let):
            if isinstance(expr.value, E_Abs):
                # 立即归约
                new_body = substitute(expr.body, expr.var, expr.value)
                return Configuration(new_body, env)
            else:
                # 归约值
                next_value = self.step(Configuration(expr.value, env))
                if next_value:
                    return Configuration(E_Let(expr.var, next_value.expr, expr.body), env)
        # E-Op
        if isinstance(expr, E_Op):
            left = expr.left
            right = expr.right
            if isinstance(left, E_Num) and isinstance(right, E_Num):
                result = eval_op(expr.op, left.value, right.value)
                return Configuration(E_Num(result), env)
            else:
                next_left = self.step(Configuration(left, env))
                if next_left:
                    return Configuration(E_Op(next_left.expr, expr.op, right), env)
                next_right = self.step(Configuration(right, env))
                if next_right:
                    return Configuration(E_Op(left, expr.op, next_right.expr), env)
        return None


    def reduce_to_normal_form(self, config: Configuration) -> Tuple[Configuration, int]:
        """
        归约到范式
        返回: (最终配置, 步数)
        """
        current = config
        for i in range(self.max_steps):
            next_config = self.step(current)
            if next_config is None:
                return current, i
            current = next_config
        return current, self.max_steps


class Big_Step_Semantics:
    """
    大步语义（自然语义）
    定义求值关系: (e, σ) ⇒ v
    """
    def __init__(self):
        self.derivations: List = []


    def eval(self, expr: Expr, env: Dict[str, any] = None) -> any:
        """
        大步求值
        返回: 求值结果
        """
        if env is None:
            env = {}
        # E-Var
        if isinstance(expr, E_Var):
            if expr.name in env:
                return env[expr.name]
            raise RuntimeError(f"Undefined variable: {expr.name}")
        # E-Num, E_Bool
        if isinstance(expr, (E_Num, E_Bool)):
            return expr.value
        # E-Abs
        if isinstance(expr, E_Abs):
            return ('closure', expr, env)
        # E-If
        if isinstance(expr, E_If):
            cond_val = self.eval(expr.cond, env)
            if cond_val:
                return self.eval(expr.then_branch, env)
            else:
                return self.eval(expr.else_branch, env)
        # E-App
        if isinstance(expr, E_App):
            func_val = self.eval(expr.func, env)
            arg_val = self.eval(expr.arg, env)
            if isinstance(func_val, tuple) and func_val[0] == 'closure':
                _, abs_expr, cls_env = func_val
                new_env = dict(cls_env)
                new_env[abs_expr.var] = arg_val
                return self.eval(abs_expr.body, new_env)
            raise RuntimeError("Not a function")
        # E-Let
        if isinstance(expr, E_Let):
            val = self.eval(expr.value, env)
            new_env = dict(env)
            new_env[expr.var] = val
            return self.eval(expr.body, new_env)
        # E-Op
        if isinstance(expr, E_Op):
            left_val = self.eval(expr.left, env)
            right_val = self.eval(expr.right, env)
            return eval_op(expr.op, left_val, right_val)
        raise RuntimeError(f"Unknown expression type: {expr}")


def substitute(body: Expr, var: str, replacement: Expr) -> Expr:
    """代换：body[x/e]"""
    if isinstance(body, E_Var):
        if body.name == var:
            return replacement
        return body
    elif isinstance(body, E_Num):
        return body
    elif isinstance(body, E_Bool):
        return body
    elif isinstance(body, E_Abs):
        if body.var == var:
            return body
        new_body = substitute(body.body, var, replacement)
        return E_Abs(body.var, new_body)
    elif isinstance(body, E_App):
        new_func = substitute(body.func, var, replacement)
        new_arg = substitute(body.arg, var, replacement)
        return E_App(new_func, new_arg)
    elif isinstance(body, E_If):
        new_cond = substitute(body.cond, var, replacement)
        new_then = substitute(body.then_branch, var, replacement)
        new_else = substitute(body.else_branch, var, replacement)
        return E_If(new_cond, new_then, new_else)
    elif isinstance(body, E_Let):
        new_value = substitute(body.value, var, replacement)
        if body.var == var:
            new_body = body.body
        else:
            new_body = substitute(body.body, var, replacement)
        return E_Let(body.var, new_value, new_body)
    elif isinstance(body, E_Op):
        new_left = substitute(body.left, var, replacement)
        new_right = substitute(body.right, var, replacement)
        return E_Op(new_left, body.op, new_right)
    return body


def eval_op(op: str, left: any, right: any) -> any:
    """求值二元操作"""
    if op == '+':
        return left + right
    elif op == '-':
        return left - right
    elif op == '*':
        return left * right
    elif op == '/':
        return left // right if isinstance(left, int) else left / right
    elif op == '==':
        return left == right
    elif op == '<':
        return left < right
    elif op == '>':
        return left > right
    elif op == 'and':
        return left and right
    elif op == 'or':
        return left or right
    raise ValueError(f"Unknown operator: {op}")


def basic_test():
    """基本功能测试"""
    print("=== 操作语义测试 ===")
    # 小步语义
    print("\n[小步语义]")
    sos = Small_Step_Semantics()
    # if True then 1 else 2
    expr1 = E_If(E_Bool(True), E_Num(1), E_Num(2))
    config1 = Configuration(expr1, {})
    result, steps = sos.reduce_to_normal_form(config1)
    print(f"  if True then 1 else 2 ->* {result.expr}")
    print(f"  归约步数: {steps}")
    # (λx. x + 1) 5
    expr2 = E_App(E_Abs("x", E_Op(E_Var("x"), "+", E_Num(1))), E_Num(5))
    config2 = Configuration(expr2, {})
    result, steps = sos.reduce_to_normal_form(config2)
    print(f"  (λx. x+1) 5 ->* {result.expr}")
    print(f"  归约步数: {steps}")
    # let x = 3 in x + 1
    expr3 = E_Let("x", E_Num(3), E_Op(E_Var("x"), "+", E_Num(1)))
    config3 = Configuration(expr3, {})
    result, steps = sos.reduce_to_normal_form(config3)
    print(f"  let x = 3 in x + 1 ->* {result.expr}")
    print(f"  归约步数: {steps}")
    # 大步语义
    print("\n[大步语义]")
    bss = Big_Step_Semantics()
    # if True then 1 else 2
    result = bss.eval(E_If(E_Bool(True), E_Num(1), E_Num(2)))
    print(f"  eval(if True then 1 else 2) = {result}")
    # (λx. x + 1) 5
    result = bss.eval(E_App(E_Abs("x", E_Op(E_Var("x"), "+", E_Num(1))), E_Num(5)))
    print(f"  eval((λx. x+1) 5) = {result}")
    # let x = 3 in x + 1
    result = bss.eval(E_Let("x", E_Num(3), E_Op(E_Var("x"), "+", E_Num(1))))
    print(f"  eval(let x = 3 in x + 1) = {result}")
    # 复杂表达式
    print("\n[复杂表达式]")
    expr4 = E_App(E_Abs("f", E_App(E_Var("f"), E_Num(2))), E_Abs("y", E_Op(E_Var("y"), "*", E_Num(3))))
    result = bss.eval(expr4)
    print(f"  eval((λf. f 2) (λy. y*3)) = {result}")


if __name__ == "__main__":
    basic_test()
