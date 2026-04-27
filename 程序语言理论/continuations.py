# -*- coding: utf-8 -*-
"""
算法实现：程序语言理论 / continuations

本文件实现 continuations 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto


class Value:
    """CPS值"""
    pass


@dataclass
class V_Var(Value):
    """变量"""
    name: str


@dataclass
class V_Lit(Value):
    """字面量"""
    value: any


@dataclass
class V_Lam(Value):
    """λ表达式（值）"""
    var: str
    body: 'Expr'


@dataclass
class Expr:
    """CPS表达式"""
    pass


@dataclass
class E_Halt(Expr):
    """停止（返回最终值）"""
    value: Value


@dataclass
class E_App(Expr):
    """函数应用"""
    func: Value
    arg: Value
    kont: Value  # 续延


@dataclass
class E_If(Expr):
    """条件"""
    cond: Value
    then_k: Value
    else_k: Value


@dataclass
class E_Let(Expr):
    """Let绑定"""
    var: str
    value: Value
    body: Expr


class CPS_Transformer:
    """CPS变换器"""
    def __init__(self):
        self.counter: int = 0
        self.fresh_var = self._make_fresh_var()


    def _make_fresh_var(self) -> str:
        """生成新变量名"""
        name = f"k{self.counter}"
        self.counter += 1
        return name


@dataclass
class CPS_Program:
    """CPS程序"""
    bindings: List[Tuple[str, Value]]
    main: Expr


class CPS_Evaluator:
    """CPS求值器（简化）"""
    def __init__(self):
        self.env: Dict[str, any] = {}
        self.functions: Dict[str, Tuple[str, Expr]] = {}


    def eval_expr(self, expr: Expr) -> any:
        """求值CPS表达式"""
        if isinstance(expr, E_Halt):
            return self.eval_value(expr.value)
        if isinstance(expr, E_App):
            func = self.eval_value(expr.func)
            arg = self.eval_value(expr.arg)
            kont = self.eval_value(expr.kont)
            # 应用函数和续延
            if callable(func):
                result = func(arg)
                return self.apply_kont(kont, result)
            return None
        if isinstance(expr, E_If):
            cond = self.eval_value(expr.cond)
            kont = self.eval_value(expr.then_k if cond else expr.else_k)
            return self.apply_kont(kont, cond)
        if isinstance(expr, E_Let):
            val = self.eval_value(expr.value)
            self.env[expr.var] = val
            return self.eval_expr(expr.body)
        return None


    def eval_value(self, v: Value) -> any:
        """求值值"""
        if isinstance(v, V_Var):
            return self.env.get(v.name)
        if isinstance(v, V_Lit):
            return v.value
        if isinstance(v, V_Lam):
            return self._closure(v)
        return None


    def _closure(self, lam: V_Lam) -> Callable:
        """创建闭包"""
        def closure(arg):
            self.env[lam.var] = arg
            return self.eval_expr(lam.body)
        return closure


    def apply_kont(self, kont: any, value: any) -> any:
        """应用续延"""
        if callable(kont):
            return kont(value)
        return value


class Call_CC:
    """call/cc实现（续延捕獲）"""
    def __init__(self):
        self.current_kont: Optional[Callable] = None


    def call_cc(self, f: Callable) -> any:
        """
        call/cc 捕获当前续延并传递给f
        f应该接收一个接收任意值的续延
        """
        captured_kont = self.current_kont
        def escape_kont(value):
            # 替换当前续延
            self.current_kont = captured_kont
            return value
        return f(escape_kont)


class CPS_Transform:
    """CPS变换算法"""
    def __init__(self):
        self.fresh_counter = 0


    def fresh(self, prefix: str = "v") -> str:
        """生成fresh变量"""
        name = f"{prefix}{self.fresh_counter}"
        self.fresh_counter += 1
        return name


    def transform(self, expr) -> Tuple[List, Expr]:
        """
        将lambda表达式变换为CPS
        返回: (bindings, body)
        """
        if isinstance(expr, int):
            # 整数常量
            v = self.fresh("v")
            return [(v, V_Lit(expr))], E_Halt(V_Var(v))
        if isinstance(expr, str):
            # 变量
            v = self.fresh("v")
            return [(v, V_Var(expr))], E_Halt(V_Var(v))
        if isinstance(expr, tuple) and len(expr) == 3 and expr[0] == 'lambda':
            # λ抽象
            _, var, body = expr
            k = self.fresh("k")
            v = self.fresh("v")
            new_body_bindings, new_body_expr = self.transform(body)
            return [(k, V_Lam(var, new_body_expr))], E_Halt(V_Var(k))
        if isinstance(expr, tuple) and len(expr) == 2:
            # 函数应用
            func, arg = expr
            k = self.fresh("k")
            func_bindings, func_expr = self.transform(func)
            arg_bindings, arg_expr = self.transform(arg)
            v = self.fresh("v")
            # 简化
            return func_bindings + arg_bindings, E_Halt(V_Var(v))
        if isinstance(expr, tuple) and len(expr) == 4 and expr[0] == 'if':
            # 条件
            _, cond, then_e, else_e = expr
            cond_bindings, cond_expr = self.transform(cond)
            then_bindings, then_expr = self.transform(then_e)
            else_bindings, else_expr = self.transform(else_e)
            return cond_bindings, E_If(V_Var(self.fresh("c")), None, None)  # 简化
        # 默认
        v = self.fresh("v")
        return [(v, V_Var("unit"))], E_Halt(V_Var(v))


class Tail_Call_Optimization:
    """尾调用优化"""
    @staticmethod
    def is_tail_position(expr, var: str) -> bool:
        """检查expr是否在尾位置"""
        if isinstance(expr, tuple):
            if len(expr) == 2:
                # 应用：最后一个参数是尾位置
                return True
        return False


def basic_test():
    """基本功能测试"""
    print("=== 续延传递风格测试 ===")
    # CPS值
    print("\n[CPS值]")
    v1 = V_Var("x")
    v2 = V_Lit(42)
    print(f"  V_Var('x') = {v1}")
    print(f"  V_Lit(42) = {v2}")
    # CPS表达式
    print("\n[CPS表达式]")
    halt = E_Halt(V_Lit(42))
    print(f"  E_Halt(V_Lit(42))")
    # CPS变换
    print("\n[CPS变换]")
    transformer = CPS_Transform()
    # λx.x
    lam = ('lambda', 'x', 'x')
    bindings, body = transformer.transform(lam)
    print(f"  λx.x -> CPS: {len(bindings)} bindings")
    # (λx.x) 42
    app = (('lambda', 'x', 'x'), 42)
    transformer2 = CPS_Transform()
    bindings, body = transformer2.transform(app)
    print(f"  (λx.x) 42 -> CPS: {len(bindings)} bindings")
    # CPS求值
    print("\n[CPS求值]")
    evaluator = CPS_Evaluator()
    evaluator.env["x"] = 10
    # 简单表达式
    simple_expr = E_Halt(V_Var("x"))
    result = evaluator.eval_expr(simple_expr)
    print(f"  eval(halt(x)) with x=10 = {result}")
    # call/cc
    print("\n[call/cc]")
    cc = Call_CC()
    result = cc.call_cc(lambda k: (k(42), 100)[0])
    print(f"  call/cc(λk. k(42)) = {result}")


if __name__ == "__main__":
    basic_test()
