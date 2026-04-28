"""
Curry-Howard同构 (Curry-Howard Isomorphism)
==========================================
功能：实现证明与程序之间的对应关系
基于Curry-Howard-Lambek对应

核心概念：
1. 命题即类型：公式对应类型
2. 证明即程序：证明对应λ项
3. 证明步骤即计算：归约对应证明变换

对应关系：
- 原子命题 p : 类型 P
- 蕴含 A → B : 函数类型 A → B
- 合取 A ∧ B : 积类型 A × B
- 析取 A ∨ B : 和类型 A + B
- 证明 ⊥ : 空类型 ⊥
- 自然演绎规则 : λ演算规则

核心规则：
- →引入 (λ抽象): ⊢ A → B 对应 λx:A. B
- →消除 (函数应用): ⊢ A → B, ⊢ A 对应 应用
- ∧引入: ⊢ A, ⊢ B 对应 ⟨M, N⟩
- ∧消除: ⊢ A ∧ B 对应 fst 或 snd
- ∨引入: ⊢ A 对应 inl 或 inr
- ∨消除: ⊢ A ∨ B, ⊢ A → C, ⊢ B → C 对应 case
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum, auto


class TypeKind(Enum):
    """类型种类"""
    BASE = auto()                                # 基本类型
    FUN = auto()                                 # 函数类型
    PROD = auto()                                # 积类型
    SUM = auto()                                 # 和类型
    UNIT = auto()                                # 单位类型
    EMPTY = auto()                               # 空类型 (⊥)


@dataclass
class Type:
    """类型"""
    kind: TypeKind
    name: str = ""                               # 基本类型名
    arg1: Optional['Type'] = None               # 左参数
    arg2: Optional['Type'] = None               # 右参数
    
    def __str__(self):
        if self.kind == TypeKind.BASE:
            return self.name
        elif self.kind == TypeKind.FUN:
            return f"({self.arg1} → {self.arg2})"
        elif self.kind == TypeKind.PROD:
            return f"({self.arg1} × {self.arg2})"
        elif self.kind == TypeKind.SUM:
            return f"({self.arg1} + {self.arg2})"
        elif self.kind == TypeKind.UNIT:
            return "⊤"
        elif self.kind == TypeKind.EMPTY:
            return "⊥"
        return "?"
    
    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        if self.kind != other.kind:
            return False
        if self.kind == TypeKind.BASE:
            return self.name == other.name
        return self.arg1 == other.arg1 and self.arg2 == other.arg2


@dataclass
class Term:
    """λ项/证明项"""
    kind: str                                     # var, abs, app, pair, fst, snd, inl, inr, case
    name: str = ""                                # 变量名
    var: str = ""                                 # 抽象变量
    body: Optional['Term'] = None                # 函数体
    fun: Optional['Term'] = None                 # 函数
    arg: Optional['Term'] = None                 # 参数
    left: Optional['Term'] = None               # 左边
    right: Optional['Term'] = None               # 右边
    term_type: Optional[Type] = None              # 类型标注
    
    def __str__(self):
        if self.kind == "var":
            return self.name
        elif self.kind == "abs":
            return f"λ{self.var}.{self.body}"
        elif self.kind == "app":
            return f"({self.fun} {self.arg})"
        elif self.kind == "pair":
            return f"⟨{self.left}, {self.right}⟩"
        elif self.kind == "fst":
            return f"fst {self.body}"
        elif self.kind == "snd":
            return f"snd {self.body}"
        elif self.kind == "inl":
            return f"inl {self.body}"
        elif self.kind == "inr":
            return f"inr {self.body}"
        elif self.kind == "case":
            return f"case {self.body} of inl→{self.left}|inr→{self.right}"
        elif self.kind == "unit":
            return "()"
        return "?"


@dataclass
class ProofNode:
    """证明/类型推导节点"""
    formula: str                                 # 公式名
    term: Optional[Term] = None                  # 对应的项
    rule: str = ""                               # 推理规则
    premises: List['ProofNode'] = field(default_factory=list)
    type_annotation: Optional[Type] = None       # 类型


class CurryHowardIsomorphism:
    """
    Curry-Howard同构实现
    
    核心功能：
    1. 命题到类型的映射
    2. 证明到程序的转换
    3. 证明归约到计算归约
    """
    
    def __init__(self):
        self.propositions: Dict[str, Type] = {}  # 命题→类型映射
        self.proofs: Dict[str, Term] = {}       # 命题→证明项
        self.type_env: Dict[str, Type] = {}     # 类型环境
    
    def proposition_to_type(self, prop: str) -> Type:
        """
        将命题转换为类型
        
        规则：
        - p : P (原子)
        - A → B : A → B (蕴含)
        - A ∧ B : A × B (合取)
        - A ∨ B : A + B (析取)
        - ⊥ : ⊥ (矛盾)
        - ⊤ : ⊤ (真)
        """
        prop = prop.strip()
        
        # 原子
        if prop.isalpha() and len(prop) == 1:
            return Type(TypeKind.BASE, name=prop)
        
        # 蕴含 →
        if "→" in prop:
            parts = prop.split("→")
            if len(parts) == 2:
                left = self.proposition_to_type(parts[0])
                right = self.proposition_to_type(parts[1])
                return Type(TypeKind.FUN, arg1=left, arg2=right)
        
        # 合取 ∧
        if "∧" in prop:
            parts = prop.split("∧")
            if len(parts) == 2:
                left = self.proposition_to_type(parts[0])
                right = self.proposition_to_type(parts[1])
                return Type(TypeKind.PROD, arg1=left, arg2=right)
        
        # 析取 ∨
        if "∨" in prop:
            parts = prop.split("∨")
            if len(parts) == 2:
                left = self.proposition_to_type(parts[0])
                right = self.proposition_to_type(parts[1])
                return Type(TypeKind.SUM, arg1=left, arg2=right)
        
        # ⊥
        if prop == "⊥":
            return Type(TypeKind.EMPTY)
        
        # ⊤
        if prop == "⊤":
            return Type(TypeKind.UNIT)
        
        return Type(TypeKind.BASE, name=prop)
    
    def type_to_proposition(self, typ: Type) -> str:
        """将类型转换回命题"""
        if typ.kind == TypeKind.BASE:
            return typ.name
        elif typ.kind == TypeKind.FUN:
            return f"{self.type_to_proposition(typ.arg1)} → {self.type_to_proposition(typ.arg2)}"
        elif typ.kind == TypeKind.PROD:
            return f"{self.type_to_proposition(typ.arg1)} ∧ {self.type_to_proposition(typ.arg2)}"
        elif typ.kind == TypeKind.SUM:
            return f"{self.type_to_proposition(typ.arg1)} ∨ {self.type_to_proposition(typ.arg2)}"
        elif typ.kind == TypeKind.UNIT:
            return "⊤"
        elif typ.kind == TypeKind.EMPTY:
            return "⊥"
        return "?"
    
    def prove(self, prop: str) -> Optional[Term]:
        """
        构造命题的证明
        
        基于自然演绎规则
        """
        print(f"\n[CH] 证明: {prop}")
        
        typ = self.proposition_to_type(prop)
        print(f"[CH] 类型: {typ}")
        
        # 根据类型构造证明项
        term = self._construct_proof(prop, typ)
        
        if term:
            print(f"[CH] 证明项: {term}")
        else:
            print(f"[CH] 无法构造证明")
        
        return term
    
    def _construct_proof(self, prop: str, typ: Type) -> Optional[Term]:
        """构造证明"""
        prop = prop.strip()
        
        if "→" in prop:
            # →引入规则: 假设A，证明B → λx:A. proof_B
            parts = prop.split("→")
            left = parts[0].strip()
            right = parts[1].strip()
            
            # 递归构造
            proof_right = self._construct_proof(right, typ.arg2)
            if proof_right:
                # 创建抽象变量
                var_type = self.proposition_to_type(left)
                abs_term = Term(kind="abs", var=left, body=proof_right)
                abs_term.term_type = typ
                return abs_term
        
        elif "∧" in prop:
            # ∧引入规则: 证明A和B → ⟨proof_A, proof_B⟩
            parts = prop.split("∧")
            if len(parts) == 2:
                left = parts[0].strip()
                right = parts[1].strip()
                
                proof_left = self._construct_proof(left, typ.arg1)
                proof_right = self._construct_proof(right, typ.arg2)
                
                if proof_left and proof_right:
                    pair_term = Term(kind="pair", left=proof_left, right=proof_right)
                    pair_term.term_type = typ
                    return pair_term
        
        elif prop == "⊤":
            # ⊤引入: 单位证明
            return Term(kind="unit", term_type=Type(TypeKind.UNIT))
        
        elif prop == "⊥":
            # ⊥消除: 无法构造
            return None
        
        # 默认：原子命题作为变量
        var_term = Term(kind="var", name=prop)
        var_term.term_type = typ
        return var_term
    
    def beta_reduce(self, term: Term) -> Term:
        """
        β归约
        
        (λx. M) N → M[N/x]
        """
        if term.kind == "app" and term.fun.kind == "abs":
            # 执行β归约
            substituted = self._substitute(term.fun.body, term.fun.var, term.arg)
            return substituted
        return term
    
    def _substitute(self, term: Term, var: str, replacement: Term) -> Term:
        """替换"""
        if term.kind == "var":
            if term.name == var:
                return replacement
            return term
        
        elif term.kind == "abs":
            if term.var == var:
                return term
            new_body = self._substitute(term.body, var, replacement)
            return Term(kind="abs", var=term.var, body=new_body)
        
        elif term.kind == "app":
            new_fun = self._substitute(term.fun, var, replacement)
            new_arg = self._substitute(term.arg, var, replacement)
            return Term(kind="app", fun=new_fun, arg=new_arg)
        
        return term
    
    def normalize(self, term: Term, max_steps: int = 20) -> Term:
        """归一化（归约到范式）"""
        current = term
        
        for step in range(max_steps):
            reduced = self.beta_reduce(current)
            if reduced == current:
                break
            current = reduced
            print(f"[CH] 归约 {step+1}: {current}")
        
        return current
    
    def extract_program(self, prop: str) -> Optional[str]:
        """
        从证明中提取程序
        
        返回可运行的代码片段
        """
        term = self.prove(prop)
        if not term:
            return None
        
        # 归一化
        normal_form = self.normalize(term)
        
        # 转换为代码
        return self._term_to_code(normal_form)
    
    def _term_to_code(self, term: Term) -> str:
        """将项转换为代码"""
        if term.kind == "abs":
            body_code = self._term_to_code(term.body)
            return f"λ({term.var}) → {body_code}"
        elif term.kind == "app":
            fun_code = self._term_to_code(term.fun)
            arg_code = self._term_to_code(term.arg)
            return f"{fun_code}({arg_code})"
        elif term.kind == "pair":
            left_code = self._term_to_code(term.left)
            right_code = self._term_to_code(term.right)
            return f"({left_code}, {right_code})"
        else:
            return term.name


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("Curry-Howard同构测试")
    print("=" * 50)
    
    ch = CurryHowardIsomorphism()
    
    # 测试1: 简单蕴含
    print("\n--- 测试1: A → A ---")
    prop1 = "A → A"
    typ1 = ch.proposition_to_type(prop1)
    print(f"命题: {prop1}")
    print(f"类型: {typ1}")
    term1 = ch.prove(prop1)
    print(f"证明项: {term1}")
    
    # 测试2: 肯定后件
    print("\n--- 测试2: (A → B) → (A → B) ---")
    prop2 = "(A → B) → (A → B)"
    typ2 = ch.proposition_to_type(prop2)
    print(f"命题: {prop2}")
    print(f"类型: {typ2}")
    term2 = ch.prove(prop2)
    
    # 测试3: S combinator类型
    print("\n--- 测试3: (A → B → C) → (A → B) → A → C ---")
    prop3 = "(A → B → C) → (A → B) → A → C"
    typ3 = ch.proposition_to_type(prop3)
    print(f"命题: {prop3}")
    print(f"类型: {typ3}")
    term3 = ch.prove(prop3)
    
    # 测试4: 归约
    print("\n--- 测试4: β归约 ---")
    if term1:
        reduced = ch.beta_reduce(term1)
        print(f"归约: {term1} → {reduced}")
    
    # 测试5: 合取
    print("\n--- 测试5: A ∧ B → A ---")
    prop5 = "A ∧ B → A"
    typ5 = ch.proposition_to_type(prop5)
    print(f"命题: {prop5}")
    print(f"类型: {typ5}")
    term5 = ch.prove(prop5)
    
    print("\n✓ Curry-Howard同构测试完成")
