# -*- coding: utf-8 -*-
"""
算法实现：程序语言理论 / curry_howard

本文件实现 curry_howard 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum, auto


class Logical_Connective(Enum):
    """逻辑联结词"""
    TOP = auto()       # ⊤ (True)
    BOTTOM = auto()     # ⊥ (False)
    AND = auto()        # ∧ (Conjunction)
    OR = auto()         # ∨ (Disjunction)
    IMPLIES = auto()    # → (Implication)
    NOT = auto()        # ¬ (Negation)


@dataclass
class Proposition:
    """命题"""
    connective: Logical_Connective
    operands: List['Proposition'] = field(default_factory=list)


class Type:
    """类型（对应命题）"""
    pass


@dataclass
class T_Var(Type):
    """类型变量"""
    name: str


@dataclass
class T_Unit(Type):
    """单元类型（对应⊤）"""
    pass


@dataclass
class T_Empty(Type):
    """空类型（对应⊥）"""
    pass


@dataclass
class T_Prod(Type):
    """乘积类型（对应∧）"""
    left: Type
    right: Type


@dataclass
class T_Sum(Type):
    """和类型（对应∨）"""
    left: Type
    right: Type


@dataclass
class T_Fun(Type):
    """函数类型（对应→）"""
    domain: Type
    codomain: Type


class Curry_Howard_Correspondence:
    """Curry-Howard对应"""
    # 逻辑联结词 <-> 类型构造器
    CONNECTIVE_TO_TYPE = {
        Logical_Connective.TOP: T_Unit,
        Logical_Connective.BOTTOM: T_Empty,
        Logical_Connective.AND: T_Prod,
        Logical_Connective.OR: T_Sum,
        Logical_Connective.IMPLIES: T_Fun,
    }

    @classmethod
    def proposition_to_type(cls, prop: Proposition) -> Type:
        """将命题转换为类型"""
        if prop.connective == Logical_Connective.NOT:
            # ¬A = A → ⊥
            inner = cls.proposition_to_type(prop.operands[0]) if prop.operands else T_Unit
            return T_Fun(inner, T_Empty())
        if prop.connective in cls.CONNECTIVE_TO_TYPE:
            tc = cls.CONNECTIVE_TO_TYPE[prop.connective]
            if prop.connective in [Logical_Connective.TOP, Logical_Connective.BOTTOM]:
                return tc()
            if prop.connective == Logical_Connective.AND:
                return T_Prod(
                    cls.proposition_to_type(prop.operands[0]),
                    cls.proposition_to_type(prop.operands[1])
                )
            if prop.connective == Logical_Connective.OR:
                return T_Sum(
                    cls.proposition_to_type(prop.operands[0]),
                    cls.proposition_to_type(prop.operands[1])
                )
            if prop.connective == Logical_Connective.IMPLIES:
                return T_Fun(
                    cls.proposition_to_type(prop.operands[0]),
                    cls.proposition_to_type(prop.operands[1])
                )
        raise ValueError(f"Unknown connective: {prop.connective}")


class Natural_Deduction:
    """
    自然演绎系统
    证明规则对应类型构造
    """
    @staticmethod
    def var_rule(name: str) -> Tuple[str, str]:
        """变量规则：引入假设"""
        return (f"Assume {name}", f"⊢ {name} : {name}")

    @staticmethod
    def implies_intro_rule(assumption: str, proof: str) -> Tuple[str, str]:
        """→引入规则：λ抽象"""
        return (f"From {assumption} prove {proof}", f"⊢ λx.{proof} : A → B")

    @staticmethod
    def implies_elim_rule(func: str, arg: str) -> Tuple[str, str]:
        """→消去规则：函数应用"""
        return (f"{func} : A → B, {arg} : A", f"⊢ {func} {arg} : B")


class Sequent_Calculus:
    """矢列演算"""
    @staticmethod
    def sequent_to_type(antecedents: List[str], succedent: str) -> Type:
        """
        将矢列 Γ ⊢ A 转换为类型
        解释为 Γ 的类型上下文产生 A 的类型
        """
        # 简化：假设所有假设是变量，结论是函数类型
        if not antecedents:
            return T_Var(succedent)
        # Γ, A ⊢ B 对应 Γ → (A → B)
        result = T_Var(succedent)
        for ant in reversed(antecedents):
            result = T_Fun(T_Var(ant), result)
        return result


class Proof_to_Program:
    """证明到程序转换"""
    @staticmethod
    def translate_proof_to_lambda(proof_tree: str) -> str:
        """将证明树翻译为λ表达式"""
        # 简化翻译
        return "λx.x"  # 占位


@dataclass
class Typed_Lambda_Expr:
    """带类型的λ表达式（证明的表示）"""
    pass


@dataclass
class TL_Var(Typed_Lambda_Expr):
    """类型化变量"""
    name: str
    type_info: Type


@dataclass
class TL_Abs(Typed_Lambda_Expr):
    """类型化λ抽象"""
    var: str
    var_type: Type
    body: Typed_Lambda_Expr


@dataclass
class TL_App(Typed_Lambda_Expr):
    """类型化应用"""
    func: Typed_Lambda_Expr
    arg: Typed_Lambda_Expr


class Type_Checker:
    """简单的类型检查器（证明检查器）"""
    def __init__(self):
        self.context: Dict[str, Type] = {}


    def check(self, expr: Typed_Lambda_Expr, expected: Type) -> bool:
        """检查表达式是否有期望的类型"""
        if isinstance(expr, TL_Var):
            return self._check_var(expr, expected)
        elif isinstance(expr, TL_Abs):
            return self._check_abs(expr, expected)
        elif isinstance(expr, TL_App):
            return self._check_app(expr, expected)
        return False


    def _check_var(self, expr: TL_Var, expected: Type) -> bool:
        """检查变量"""
        if expr.name in self.context:
            return self._type_equal(self.context[expr.name], expected)
        return False


    def _check_abs(self, expr: TL_Abs, expected: Type) -> bool:
        """检查λ抽象"""
        if not isinstance(expected, T_Fun):
            return False
        # 添加绑定到上下文
        self.context[expr.var] = expr.var_type
        result = self.check(expr.body, expected.codomain)
        del self.context[expr.var]
        return result


    def _check_app(self, expr: TL_App, expected: Type) -> bool:
        """检查应用"""
        # 简化实现
        return True


    def _type_equal(self, t1: Type, t2: Type) -> bool:
        """类型相等检查"""
        if isinstance(t1, T_Var) and isinstance(t2, T_Var):
            return t1.name == t2.name
        if isinstance(t1, T_Fun) and isinstance(t2, T_Fun):
            return (self._type_equal(t1.domain, t2.domain) and
                    self._type_equal(t1.codomain, t2.codomain))
        return type(t1) == type(t2)


# 经典逻辑 vs 直觉逻辑
class Classical_Logic:
    """经典逻辑联结词"""
    @staticmethod
    def double_negation_elimination(prop: Proposition) -> Proposition:
        """双重否定消除（需要排中律）"""
        return prop  # 简化


class Intuitionistic_Logic:
    """直觉主义逻辑（不允许双重否定消除）"""
    @staticmethod
    def no_double_negation(prop: Proposition) -> bool:
        """双重否定不可证明"""
        return True  # 简化


class Linear_Logic:
    """线性逻辑（资源敏感）"""
    # ⊗ (times), ⊕ (plus), & (with), ⅋ (par), ! (of course), ? (why not)


def basic_test():
    """基本功能测试"""
    print("=== Curry-Howard同构测试 ===")
    # 命题到类型的转换
    print("\n[命题即类型]")
    # A → B
    prop_implies = Proposition(Logical_Connective.IMPLIES,
                               [Proposition(T_Var('A'), [], Logical_Connective.TOP),
                                Proposition(T_Var('B'), [], Logical_Connective.TOP)])
    # 简化：直接创建
    print("  A → B 对应 函数类型 α → β")
    # A ∧ B 对应 (α, β)
    print("  A ∧ B 对应 乘积类型 α × β")
    # A ∨ B 对应 Either α β
    print("  A ∨ B 对应 和类型 α + β")
    # ⊤ 对应 Unit
    print("  ⊤ 对应 单元类型 ()")
    # ⊥ 对应 Void/Empty
    print("  ⊥ 对应 空类型")
    # 自然演绎
    print("\n[自然演绎证明规则]")
    print("  →引入: 如果在假设A下能证明B，则可证明A→B")
    print("  →消去: 如果能证明A→B且能证明A，则能证明B")
    print("  ∧引入: 如果能证明A且能证明B，则能证明A∧B")
    print("  ∧消去: 如果能证明A∧B，则能证明A（或B）")
    print("  ∨引入: 如果能证明A，则能证明A∨B")
    print("  ∨消去: 如果能证明A∨B，且能从A证明C，且从B证明C，则能证明C")
    # 证明即程序
    print("\n[证明即程序]")
    # 恒等函数 id : ∀A. A → A
    id_proof = TL_Abs("x", T_Var("A"), TL_Var("x", T_Var("A")))
    print("  恒等函数: λx.x : ∀α. α → α")
    # K组合子: λx.λy.x : ∀AB. A → B → A
    k_proof = TL_Abs("x", T_Var("A"),
                     TL_Abs("y", T_Var("B"),
                            TL_Var("x", T_Var("A"))))
    print("  K组合子: λx.λy.x : ∀αβ. α → β → α")
    # S组合子: λx.λy.λz. x z (y z) : ∀ABC. (A → B → C) → (A → B) → A → C
    print("  S组合子: λx.λy.λz. x z (y z) : ∀αβγ. (α → β → γ) → (α → β) → α → γ")
    # 矢列演算
    print("\n[矢列演算]")
    # A ⊢ A
    seq1 = sequent_to_type(["A"], "A")
    print("  A ⊢ A : A")
    # A, B ⊢ A → B → (A ∧ B)
    seq2 = sequent_to_type(["A", "B"], "A ∧ B")
    print("  A, B ⊢ A ∧ B : (A → B → (A × B))")
    # 经典vs直觉
    print("\n[经典逻辑 vs 直觉逻辑]")
    print("  经典逻辑: 允许双重否定消除 ¬¬A ⊢ A")
    print("  直觉逻辑: 不允许双重否定消除，需要显式证明A")
    print("  对应: 经典逻辑 ↔ 支持call/cc的λ演算")


if __name__ == "__main__":
    basic_test()
