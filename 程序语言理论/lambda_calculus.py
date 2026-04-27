# -*- coding: utf-8 -*-
"""
算法实现：程序语言理论 / lambda_calculus

本文件实现 lambda_calculus 相关的算法功能。
"""

from typing import List, Optional, Set, Dict, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import string


class Lambda_Expr:
    """λ表达式基类"""
    def free_vars(self) -> Set[str]:
        """返回自由变量集合"""
        raise NotImplementedError

    def bound_vars(self) -> Set[str]:
        """返回约束变量集合"""
        raise NotImplementedError

    def substitute(self, var: str, expr: 'Lambda_Expr') -> 'Lambda_Expr':
        """替换：expr[x/e]"""
        raise NotImplementedError

    def beta_reduce(self) -> Optional['Lambda_Expr']:
        """β归约一步"""
        raise NotImplementedError


@dataclass
class Var(Lambda_Expr):
    """变量 x"""
    name: str

    def __str__(self):
        return self.name

    def free_vars(self) -> Set[str]:
        return {self.name}

    def bound_vars(self) -> Set[str]:
        return set()

    def substitute(self, var: str, expr: Lambda_Expr) -> Lambda_Expr:
        if self.name == var:
            return expr
        return self

    def beta_reduce(self) -> Optional[Lambda_Expr]:
        return None


@dataclass
class Abs(Lambda_Expr):
    """抽象 λx.M"""
    var: str
    body: Lambda_Expr

    def __str__(self):
        if '.' in self.body.__str__():
            return f"(λ{self.var}. {self.body})"
        return f"λ{self.var}. {self.body}"

    def free_vars(self) -> Set[str]:
        return self.body.free_vars() - {self.var}

    def bound_vars(self) -> Set[str]:
        return self.body.bound_vars() | {self.var}

    def substitute(self, var: str, expr: Lambda_Expr) -> Lambda_Expr:
        if var == self.var:
            return self  # 变量被遮蔽
        if self.var not in expr.free_vars():
            # 安全替换
            new_body = self.body.substitute(var, expr)
            return Abs(self.var, new_body)
        else:
            # 需要α转换
            new_var = self._fresh_var()
            new_body = self.body.substitute(self.var, Var(new_var))
            new_body = new_body.substitute(var, expr)
            return Abs(new_var, new_body)

    def beta_reduce(self) -> Optional[Lambda_Expr]:
        return None

    def _fresh_var(self) -> str:
        """生成新的变量名"""
        return "_x"


@dataclass
class App(Lambda_Expr):
    """应用 (M N)"""
    func: Lambda_Expr
    arg: Lambda_Expr

    def __str__(self):
        func_str = str(self.func)
        arg_str = str(self.arg)
        if isinstance(self.func, Abs):
            func_str = f"({func_str})"
        if isinstance(self.arg, Abs):
            arg_str = f"({arg_str})"
        return f"{func_str} {arg_str}"

    def free_vars(self) -> Set[str]:
        return self.func.free_vars() | self.arg.free_vars()

    def bound_vars(self) -> Set[str]:
        return self.func.bound_vars() | self.arg.bound_vars()

    def substitute(self, var: str, expr: Lambda_Expr) -> Lambda_Expr:
        return App(
            self.func.substitute(var, expr),
            self.arg.substitute(var, expr)
        )

    def beta_reduce(self) -> Optional[Lambda_Expr]:
        # 如果func是λ抽象，执行β归约
        if isinstance(self.func, Abs):
            return self.func.body.substitute(self.func.var, self.arg)
        # 尝试归约func
        reduced_func = self.func.beta_reduce()
        if reduced_func:
            return App(reduced_func, self.arg)
        # 尝试归约arg
        reduced_arg = self.arg.beta_reduce()
        if reduced_arg:
            return App(self.func, reduced_arg)
        return None


class Alpha_Conversion:
    """α转换"""
    @staticmethod
    def convert(expr: Lambda_Expr, old_var: str, new_var: str) -> Lambda_Expr:
        """α转换：重命名约束变量"""
        if isinstance(expr, Var):
            return expr
        elif isinstance(expr, Abs):
            if expr.var == old_var:
                new_body = Alpha_Conversion.convert(expr.body, old_var, new_var)
                return Abs(new_var, new_body)
            else:
                new_body = Alpha_Conversion.convert(expr.body, old_var, new_var)
                return Abs(expr.var, new_body)
        elif isinstance(expr, App):
            new_func = Alpha_Conversion.convert(expr.func, old_var, new_var)
            new_arg = Alpha_Conversion.convert(expr.arg, old_var, new_var)
            return App(new_func, new_arg)
        return expr


class Beta_Reduction:
    """β归约"""
    def __init__(self, strategy: str = "normal"):
        self.strategy = strategy
        self.steps: List[Tuple[Lambda_Expr, str]] = []


    def reduce(self, expr: Lambda_Expr, max_steps: int = 1000) -> Lambda_Expr:
        """归约到范式"""
        current = expr
        for i in range(max_steps):
            reduced = current.beta_reduce()
            if reduced is None:
                break
            self.steps.append((reduced, f"Step {i+1}"))
            current = reduced
        return current


class Church_Encoding:
    """Church编码"""
    @staticmethod
    def church_numeral(n: int) -> Lambda_Expr:
        """Church数 n = λf.λx.f^n x"""
        # n = λf.λx.(f (f ... (f x)))
        body = Var("x")
        for _ in range(n):
            body = App(Var("f"), body)
        return Abs("f", Abs("x", body))


    @staticmethod
    def church_zero() -> Lambda_Expr:
        return Church_Encoding.church_numeral(0)


    @staticmethod
    def church_one() -> Lambda_Expr:
        return Church_Encoding.church_numeral(1)


    @staticmethod
    def church_succ() -> Lambda_Expr:
        """后继函数 succ = λn.λf.λx.f (n f x)"""
        n = Var("n")
        f = Var("f")
        x = Var("x")
        # n f x
        nfx = App(App(Var("n"), Var("f")), Var("x"))
        # f (n f x)
        fnfx = App(Var("f"), nfx)
        # λx.f (n f x)
        body1 = Abs("x", fnfx)
        # λf.λx.f (n f x)
        body2 = Abs("f", body1)
        # λn.λf.λx.f (n f x)
        return Abs("n", body2)


    @staticmethod
    def church_add() -> Lambda_Expr:
        """加法 plus = λm.λn.λf.λx.m f (n f x)"""
        m = Var("m")
        n = Var("n")
        f = Var("f")
        x = Var("x")
        # n f x
        nfx = App(App(Var("n"), Var("f")), Var("x"))
        # m f (n f x)
        mfnfx = App(App(Var("m"), Var("f")), nfx)
        # λx.m f (n f x)
        body1 = Abs("x", mfnfx)
        # λf.λx.m f (n f x)
        body2 = Abs("f", body1)
        # λn.λf.λx.m f (n f x)
        body3 = Abs("n", body2)
        # λm.λn.λf.λx.m f (n f x)
        return Abs("m", body3)


    @staticmethod
    def church_mul() -> Lambda_Expr:
        """乘法 mult = λm.λn.λf.m (n f)"""
        m = Var("m")
        n = Var("n")
        f = Var("f")
        # n f
        nf = App(Var("n"), Var("f"))
        # m (n f)
        mnf = App(Var("m"), nf)
        # λf.m (n f)
        body1 = Abs("f", mnf)
        # λn.λf.m (n f)
        body2 = Abs("n", body1)
        # λm.λn.λf.m (n f)
        return Abs("m", body2)


    @staticmethod
    def church_pred() -> Lambda_Expr:
        """前驱 pred = λn.λf.λx.n (λg.λh.h (g f)) (λu.x) (λu.u)"""
        # 简化版本
        return Abs("n", Abs("f", Abs("x", App(Var("n"), Abs("g", Abs("h", App(Var("h"), App(Var("g"), Var("f")))))))))


    @staticmethod
    def church_bool(b: bool) -> Lambda_Expr:
        """Church布尔值 true = λt.λf.t, false = λt.λf.f"""
        if b:
            return Abs("t", Abs("f", Var("t")))
        else:
            return Abs("t", Abs("f", Var("f")))


    @staticmethod
    def church_if() -> Lambda_Expr:
        """if = λp.λa.λb.p a b"""
        p = Var("p")
        a = Var("a")
        b = Var("b")
        # p a b
        pab = App(App(Var("p"), Var("a")), Var("b"))
        # λb.p a b
        body1 = Abs("b", pab)
        # λa.λb.p a b
        body2 = Abs("a", body1)
        # λp.λa.λb.p a b
        return Abs("p", body2)


    @staticmethod
    def church_pair() -> Lambda_Expr:
        """pair = λx.λy.λf.f x y"""
        x = Var("x")
        y = Var("y")
        f = Var("f")
        # f x y
        fxy = App(App(Var("f"), Var("x")), Var("y"))
        # λy.λf.f x y
        body1 = Abs("y", Abs("f", fxy))
        # λx.λy.λf.f x y
        return Abs("x", body1)


    @staticmethod
    def church_nil() -> Lambda_Expr:
        """nil = λc.λn.n"""
        return Abs("c", Abs("n", Var("n")))


    @staticmethod
    def church_cons() -> Lambda_Expr:
        """cons = λh.λt.λc.λn.c h (t c n)"""
        h = Var("h")
        t = Var("t")
        c = Var("c")
        n = Var("n")
        # t c n
        tcn = App(App(Var("t"), Var("c")), Var("n"))
        # c h (t c n)
        ch_tcn = App(App(Var("c"), Var("h")), tcn)
        # λn.c h (t c n)
        body1 = Abs("n", ch_tcn)
        # λc.λn.c h (t c n)
        body2 = Abs("c", body1)
        # λh.λt.λc.λn.c h (t c n)
        return Abs("h", Abs("t", body2))


class Lambda_Normalizer:
    """λ表达式规范化器"""
    @staticmethod
    def normalize(expr: Lambda_Expr, max_steps: int = 100) -> Tuple[Lambda_Expr, int]:
        """归约到范式，返回(结果, 步数)"""
        current = expr
        for i in range(max_steps):
            reduced = current.beta_reduce()
            if reduced is None:
                return current, i
            current = reduced
        return current, max_steps


def basic_test():
    """基本功能测试"""
    print("=== λ演算测试 ===")
    # 简单变量
    print("\n[变量]")
    x = Var("x")
    print(f"  x = {x}")
    print(f"  FV(x) = {x.free_vars()}")
    # λ抽象
    print("\n[λ抽象]")
    lam = Abs("x", App(Var("x"), Var("y")))
    print(f"  λx.x y = {lam}")
    print(f"  FV(λx.x y) = {lam.free_vars()}")
    print(f"  BV(λx.x y) = {lam.bound_vars()}")
    # 函数应用
    print("\n[函数应用]")
    app = App(Abs("x", Var("x")), Var("y"))
    print(f"  (λx.x) y = {app}")
    # β归约
    print("\n[β归约]")
    reducer = Beta_Reduction()
    result = reducer.reduce(app)
    print(f"  (λx.x) y ->β {result}")
    # Church数
    print("\n[Church编码]")
    zero = Church_Encoding.church_zero()
    one = Church_Encoding.church_one()
    two = Church_Encoding.church_numeral(2)
    three = Church_Encoding.church_numeral(3)
    print(f"  0 = {zero}")
    print(f"  1 = {one}")
    print(f"  2 = {two}")
    print(f"  3 = {three}")
    # Church加法
    print("\n[Church加法]")
    plus = Church_Encoding.church_add()
    print(f"  plus = {plus}")
    # 2 + 3
    expr_2_3 = App(App(plus, two), three)
    result, steps = Lambda_Normalizer.normalize(expr_2_3)
    print(f"  2 + 3 = {result}")
    # Church乘法
    print("\n[Church乘法]")
    mul = Church_Encoding.church_mul()
    expr_2_3_mul = App(App(mul, two), three)
    result, _ = Lambda_Normalizer.normalize(expr_2_3_mul)
    print(f"  2 * 3 = {result}")
    # Church布尔
    print("\n[Church布尔]")
    true = Church_Encoding.church_bool(True)
    false = Church_Encoding.church_bool(False)
    print(f"  true = {true}")
    print(f"  false = {false}")
    # if true then 1 else 2
    if_then_else = App(App(App(Church_Encoding.church_if(), true), Church_Encoding.church_numeral(1)), Church_Encoding.church_numeral(2))
    result, _ = Lambda_Normalizer.normalize(if_then_else)
    print(f"  if true then 1 else 2 = {result}")


if __name__ == "__main__":
    basic_test()
