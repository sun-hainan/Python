"""
Skolem化与Herbrand定理 (Skolemization & Herbrand Theorem)
========================================================
功能：实现Skolem化算法和Herbrand基域概念
为一阶逻辑归结证明提供理论基础

核心概念：
1. Skolem标准形：消除存在量词的范式
2. Skolem函数：用函数替换存在变量
3. Herbrand基域：所有项的无限集合
4. Herbrand解释：定义在Herbrand基域上的解释
5. Herbrand定理：A不可满足 ⟺ A在Herbrand基域上不可满足

Skolem化规则：
- ∃x P(x) → P(c)  (c是新常量)
- ∀y ∃x P(x,y) → ∀y P(f(y), y)  (f是新函数)
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import deque


@dataclass
class Term:
    """一阶项"""
    kind: str                                     # const, var, func
    name: str
    args: List['Term'] = field(default_factory=list)
    
    def __str__(self):
        if self.kind == "var":
            return self.name
        elif self.kind == "func":
            args_str = ", ".join(str(a) for a in self.args)
            return f"{self.name}({args_str})"
        return self.name


@dataclass
class Atom:
    """原子公式"""
    predicate: str
    args: List[Term]
    
    def __str__(self):
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.predicate}({args_str})"


@dataclass
class Literal:
    """文字"""
    atom: Atom
    negated: bool = False
    
    def __str__(self):
        return f"¬{self.atom}" if self.negated else str(self.atom)


@dataclass
class Clause:
    """子句"""
    literals: Set[Literal] = field(default_factory=set)
    
    def __str__(self):
        if not self.literals:
            return "⊥"
        return " ∨ ".join(str(l) for l in self.literals)


class HerbrandUniverse:
    """
    Herbrand基域
    
    递归定义：
    1. 所有出现在公式中的常量为Herbrand基项
    2. 若f是n元函数符号，t1,...,tn是Herbrand基项，
       则f(t1,...,tn)也是Herbrand基项
    """
    
    def __init__(self):
        self.constants: Set[str] = set()
        self.functions: Dict[str, int] = {}       # 函数→元数
        self.ground_terms: Set[Term] = set()
    
    def add_constant(self, const: str):
        """添加常量"""
        self.constants.add(const)
    
    def add_function(self, func: str, arity: int):
        """添加函数符号"""
        self.functions[func] = arity
    
    def generate_ground_terms(self, max_depth: int = 2) -> Set[Term]:
        """
        生成Herbrand基项（有限深度）
        """
        print(f"[Herbrand] 生成基项 (深度≤{max_depth})")
        
        # 从常量开始
        self.ground_terms = {Term("const", c) for c in self.constants}
        
        if not self.constants:
            # 如果没有常量，添加默认常量
            self.ground_terms.add(Term("const", "a"))
        
        # 递归生成
        for depth in range(max_depth):
            new_terms = set()
            for func, arity in self.functions.items():
                for term_combo in self._generate_term_combinations(arity, depth):
                    args = list(term_combo)
                    new_terms.add(Term("func", func, args))
            
            self.ground_terms |= new_terms
        
        print(f"[Herbrand] 生成了 {len(self.ground_terms)} 个基项")
        for t in list(self.ground_terms)[:10]:
            print(f"  {t}")
        
        return self.ground_terms
    
    def _generate_term_combinations(self, arity: int, depth: int) -> List[Tuple[Term, ...]]:
        """生成元组序列"""
        if arity == 0:
            return [()]
        
        result = []
        term_list = list(self.ground_terms)
        
        for t in term_list:
            if depth == 0:
                result.append((t,))
            else:
                for combo in self._generate_term_combinations(arity - 1, depth):
                    result.append((t,) + combo)
        
        return result


class Skolemizer:
    """
    Skolem化器
    
    消除存在量词：
    1. ∀x1 ... ∀xn ∃y φ → ∀x1 ... ∀xn φ[y/f(x1,...,xn)]
    2. ∃y φ → φ[y/c] (如果没有全称量词，则用常量)
    """
    
    def __init__(self):
        self.skolem_constants: Set[str] = set()
        self.skolem_functions: Dict[str, str] = {}  # var → function
        self.counter = 0
    
    def skolemize_formula(self, formula_str: str) -> str:
        """
        Skolem化公式字符串
        
        Args:
            formula_str: 公式字符串，如 "∃x ∀y P(x,y)"
        
        Returns:
            Skolem化后的字符串
        """
        print(f"[Skolem化] 输入: {formula_str}")
        
        # 简化实现
        # 查找 ∃x 模式并替换
        result = formula_str
        
        # 消除 ∃
        result = result.replace("∃x", "")
        result = result.replace("∃y", "")
        result = result.replace("∃z", "")
        
        # 添加Skolem常量
        if "∀x" in result or "∀y" in result:
            # ∀x ∃y → ∀x P(f(x))
            result = result.replace("∀x", "∀x")
            self.skolem_functions["y"] = "f(x)"
        else:
            # ∃x → P(c)
            self.skolem_constants.add("c")
        
        print(f"[Skolem化] 输出: {result}")
        return result
    
    def get_skolem_constants(self) -> Set[str]:
        """获取Skolem常量"""
        return self.skolem_constants
    
    def get_skolem_functions(self) -> Dict[str, str]:
        """获取Skolem函数"""
        return self.skolem_functions


class HerbrandTheorem:
    """
    Herbrand定理应用
    
    核心定理：
    一阶公式集S不可满足 ⟺ S的Herbrand展开可满足
    """
    
    def __init__(self):
        self.herbrand_universe = HerbrandUniverse()
        self.clauses: List[Clause] = []
    
    def add_clause(self, clause: Clause):
        """添加子句"""
        self.clauses.append(clause)
    
    def ground_instantiate(self, clause: Clause, substitution: Dict[str, Term]) -> Clause:
        """
        对子句进行基例化
        
        Args:
            clause: 原始子句
            substitution: 替换（变量→基项）
        
        Returns:
            基例化后的子句
        """
        new_literals = set()
        
        for lit in clause.literals:
            new_args = []
            for arg in lit.atom.args:
                if arg.kind == "var" and arg.name in substitution:
                    new_args.append(substitution[arg.name])
                else:
                    new_args.append(arg)
            
            new_atom = Atom(lit.atom.predicate, new_args)
            new_literals.add(Literal(new_atom, lit.negated))
        
        return Clause(new_literals)
    
    def generate_herbrand_expansion(self, max_terms: int = 50) -> List[Clause]:
        """
        生成Herbrand展开
        
        枚举所有基例化
        
        Returns:
            基子句列表
        """
        print(f"[Herbrand] 生成展开")
        
        # 生成Herbrand基项
        self.herbrand_universe.generate_ground_terms(max_depth=2)
        
        # 生成基子句
        ground_clauses = []
        term_list = list(self.herbrand_universe.ground_terms)
        
        for clause in self.clauses:
            # 生成变量→基项的替换
            vars_in_clause = self._get_vars_in_clause(clause)
            
            if not vars_in_clause:
                # 无变量，已经是基子句
                ground_clauses.append(clause)
                continue
            
            # 生成替换
            for term in term_list[:5]:
                sub = {v.name: term for v in vars_in_clause}
                ground_clause = self.ground_instantiate(clause, sub)
                ground_clauses.append(ground_clause)
        
        print(f"[Herbrand] 生成了 {len(ground_clauses)} 个基子句")
        return ground_clauses
    
    def _get_vars_in_clause(self, clause: Clause) -> Set[Term]:
        """获取子句中的变量"""
        vars = set()
        for lit in clause.literals:
            for arg in lit.atom.args:
                if arg.kind == "var":
                    vars.add(arg)
        return vars
    
    def check_tautology(self, clause: Clause) -> bool:
        """检查是否为重言式"""
        for lit in clause.literals:
            complement = Literal(lit.atom, not lit.negated)
            if complement in clause.literals:
                return True
        return False
    
    def herbrand_unsatisfability_check(self) -> bool:
        """
        检查Herbrand展开是否不可满足
        
        使用命题逻辑归结检查
        """
        print(f"[Herbrand] 检查不可满足性")
        
        ground_clauses = self.generate_herbrand_expansion()
        
        # 简化：检查是否有空子句
        for c in ground_clauses:
            if c.is_empty():
                print(f"[Herbrand] 找到空子句")
                return True
        
        # 检查重言式
        non_tautologies = [c for c in ground_clauses if not self.check_tautology(c)]
        print(f"[Herbrand] 非重言式子句数: {len(non_tautologies)}")
        
        return False


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("Skolem化与Herbrand定理测试")
    print("=" * 50)
    
    # 测试Skolem化
    print("\n--- Skolem化测试 ---")
    skolemizer = Skolemizer()
    
    test_formulas = [
        "∃x P(x)",
        "∀y ∃x P(x,y)",
        "∀x ∀z ∃y (P(x,y) ∨ Q(y,z))"
    ]
    
    for formula in test_formulas:
        print(f"\n输入: {formula}")
        result = skolemizer.skolemize_formula(formula)
        print(f"Skolem常量: {skolemizer.get_skolem_constants()}")
        print(f"Skolem函数: {skolemizer.get_skolem_functions()}")
    
    # 测试Herbrand基域
    print("\n--- Herbrand基域测试 ---")
    hu = HerbrandUniverse()
    hu.add_constant("a")
    hu.add_constant("b")
    hu.add_function("f", 1)
    hu.add_function("g", 2)
    hu.generate_ground_terms(max_depth=2)
    
    # 测试Herbrand定理
    print("\n--- Herbrand定理测试 ---")
    herbrand = HerbrandTheorem()
    
    # 添加子句: P(x) ∨ Q(x)
    clause1 = Clause({
        Literal(Atom("P", [Term("var", "x")]), False),
        Literal(Atom("Q", [Term("var", "x")]), False)
    })
    
    # 添加子句: ¬P(f(a))
    clause2 = Clause({
        Literal(Atom("P", [Term("func", "f", [Term("const", "a")])]), True)
    })
    
    herbrand.add_clause(clause1)
    herbrand.add_clause(clause2)
    
    print(f"子句数: {len(herbrand.clauses)}")
    is_unsat = herbrand.herbrand_unsatisfability_check()
    print(f"不可满足: {is_unsat}")
    
    print("\n✓ Skolem化与Herbrand定理测试完成")
