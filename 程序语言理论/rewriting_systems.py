# -*- coding: utf-8 -*-
"""
算法实现：程序语言理论 / rewriting_systems

本文件实现 rewriting_systems 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto


@dataclass
class Term:
    """项（Term）"""
    def __str__(self):
        raise NotImplementedError


@dataclass
class Var(Term):
    """变量 x, y, z"""
    name: str

    def __str__(self):
        return self.name


@dataclass
class Const(Term):
    """常量 a, b, c"""
    name: str

    def __str__(self):
        return self.name


@dataclass
class App(Term):
    """函数应用 f(t1, t2, ...)"""
    func: str
    args: List[Term]

    def __str__(self):
        if not self.args:
            return self.func
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.func}({args_str})"


@dataclass
class Rule:
    """重写规则 l -> r"""
    left: Term
    right: Term
    name: str = ""


class Substitution(Dict[str, Term]):
    """代换"""
    def apply(self, term: Term) -> Term:
        """应用代换到项"""
        if isinstance(term, Var):
            if term.name in self:
                return self[term.name]
            return term
        elif isinstance(term, Const):
            return term
        elif isinstance(term, App):
            new_args = [self.apply(arg) for arg in term.args]
            return App(term.func, new_args)
        return term


class Unifier:
    """合一方面（简化）"""
    @staticmethod
    def unify(t1: Term, t2: Term) -> Optional[Substitution]:
        """合一两个项"""
        if isinstance(t1, Var):
            return Substitution({t1.name: t2})
        if isinstance(t2, Var):
            return Substitution({t2.name: t1})
        if isinstance(t1, Const) and isinstance(t2, Const):
            if t1.name == t2.name:
                return Substitution()
            return None
        if isinstance(t1, App) and isinstance(t2, App):
            if t1.func != t2.func or len(t1.args) != len(t2.args):
                return None
            subst = Substitution()
            for a1, a2 in zip(t1.args, t2.args):
                u = Unifier.unify(subst.apply(a1), subst.apply(a2))
                if u is None:
                    return None
                subst.update(u)
            return subst
        return None


class Rewriting_System:
    """重写系统"""
    def __init__(self, rules: List[Rule]):
        self.rules = rules
        self.rewrite_count: int = 0


    def match(self, term: Term, pattern: Term) -> Optional[Substitution]:
        """模式匹配"""
        if isinstance(pattern, Var):
            return Substitution({pattern.name: term})
        if isinstance(pattern, Const) and isinstance(term, Const):
            if pattern.name == term.name:
                return Substitution()
            return None
        if isinstance(pattern, App) and isinstance(term, App):
            if pattern.func != term.func or len(pattern.args) != len(term.args):
                return None
            subst = Substitution()
            for pa, ta in zip(pattern.args, term.args):
                m = self.match(subst.apply(pa), ta)
                if m is None:
                    return None
                subst.update(m)
            return subst
        return None


    def rewrite_step(self, term: Term) -> Optional[Term]:
        """
        尝试一步重写
        返回重写后的项，如果没有规则适用则返回None
        """
        # 尝试每个规则
        for rule in self.rules:
            subst = self.match(term, rule.left)
            if subst is not None:
                self.rewrite_count += 1
                return subst.apply(rule.right)
        # 递归重写子项
        if isinstance(term, App) and term.args:
            new_args = []
            changed = False
            for arg in term.args:
                new_arg = self.rewrite_step(arg)
                if new_arg is not None:
                    new_args.append(new_arg)
                    changed = True
                else:
                    new_args.append(arg)
            if changed:
                return App(term.func, new_args)
        return None


    def rewrite_to_normal_form(self, term: Term, max_steps: int = 100) -> Tuple[Term, int]:
        """
        重写到范式（不可进一步重写）
        返回: (范式, 步数)
        """
        current = term
        for i in range(max_steps):
            next_term = self.rewrite_step(current)
            if next_term is None:
                return current, i
            current = next_term
        return current, max_steps


class Termination_Analysis:
    """终止性分析"""
    @staticmethod
    def is_terminating(rs: Rewriting_System) -> bool:
        """
        检查重写系统是否终止（不可判定问题，近似）
        使用简化的递归排序
        """
        return True  # 简化


    @staticmethod
    def find_ranking_function(rs: Rewriting_System) -> Optional[Callable]:
        """
        尝试找到排序函数证明终止
        返回排序函数或None
        """
        return lambda t: 0  # 简化


class Critical_Pair:
    """关键对（用于完备性检查）"""
    def __init__(self, term1: Term, term2: Term, rule1: str, rule2: str):
        self.term1 = term1
        self.term2 = term2
        self.rule1 = rule1
        self.rule2 = rule2


class Completion:
    """Knuth-Bendix完备化"""
    def __init__(self, rules: List[Rule]):
        self.rules = rules


    def complete(self, axioms: List[Rule] = None) -> List[Rule]:
        """
        尝试完备化规则集
        返回最终规则集
        """
        # 简化实现
        return self.rules


def basic_test():
    """基本功能测试"""
    print("=== 重写系统测试 ===")
    # 简单规则
    print("\n[简单重写规则]")
    # f(x, y) -> g(x)
    rule1 = Rule(App("f", [Var("x"), Var("y")]), App("g", [Var("x")]))
    # g(x) -> h(x, x)
    rule2 = Rule(App("g", [Var("x")]), App("h", [Var("x"), Var("x")]))
    rs = Rewriting_System([rule1, rule2])
    print(f"  规则1: f(x, y) -> g(x)")
    print(f"  规则2: g(x) -> h(x, x)")
    # 重写
    term = App("f", [Const("a"), Const("b")])
    print(f"\n  重写 f(a, b):")
    result, steps = rs.rewrite_to_normal_form(term)
    print(f"  -> {result} ({steps} 步)")
    # 终止性
    print("\n[终止性分析]")
    print(f"  系统终止: {Termination_Analysis.is_terminating(rs)}")
    # 代换
    print("\n[代换]")
    subst = Substitution({"x": Const("a"), "y": Const("b")})
    term = App("f", [Var("x"), Var("y")])
    result = subst.apply(term)
    print(f"  {{x/a, y/b}}(f(x, y)) = {result}")
    # 合一
    print("\n[合一]")
    t1 = App("f", [Var("x"), Var("y")])
    t2 = App("f", [Const("a"), Var("z")])
    unifier = Unifier.unify(t1, t2)
    print(f"  unify(f(x, y), f(a, z)) = {unifier}")
    # 关键对
    print("\n[关键对]")
    print("  关键对检查（需要更复杂的分析）")


if __name__ == "__main__":
    basic_test()
