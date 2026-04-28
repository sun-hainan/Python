"""
一阶逻辑归结证明 (First-Order Logic Resolution)
============================================
功能：实现一阶逻辑的归结原理
支持谓词、量词、函数符号

核心概念：
1. 子句形式：文字的析取（无量词）
2. Skolem化：消除存在量词
3. 合一：用于寻找可归结的文字对
4. 二元归结：找到互补文字对后消去

算法步骤：
1. 将公式转换为前束范式
2. Skolem化消除存在量词
3. 化为子句形式
4. 应用归结原理
"""

from typing import Set, Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


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
    """
    原子公式
    - predicate: 谓词名
    - args: 参数列表
    """
    predicate: str
    args: List[Term]
    
    def __str__(self):
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.predicate}({args_str})"


@dataclass
class FOLLiteral:
    """一阶逻辑文字"""
    atom: Atom
    negated: bool = False
    
    def __str__(self):
        if self.negated:
            return f"¬{self.atom}"
        return str(self.atom)
    
    def complement(self) -> 'FOLLiteral':
        return FOLLiteral(self.atom, not self.negated)


@dataclass
class Clause:
    """子句"""
    literals: Set[FOLLiteral] = field(default_factory=set)
    
    def __str__(self):
        if not self.literals:
            return "⊥"
        return " ∨ ".join(str(l) for l in self.literals)


@dataclass
class Formula:
    """一阶公式节点"""
    op: str                                       # and, or, not, forall, exists
    children: List['Formula'] = field(default_factory=list)
    atom: Optional[Atom] = None


class Substitution:
    """替换"""
    mapping: Dict[str, Term] = {}
    
    def apply_term(self, term: Term) -> Term:
        if term.kind == "var" and term.name in self.mapping:
            return self.mapping[term.name]
        if term.kind == "func":
            return Term("func", term.name, [self.apply_term(a) for a in term.args])
        return term
    
    def apply_atom(self, atom: Atom) -> Atom:
        return Atom(atom.predicate, [self.apply_term(a) for a in atom.args])
    
    def apply_literal(self, lit: FOLLiteral) -> FOLLiteral:
        return FOLLiteral(self.apply_atom(lit.atom), lit.negated)


class FirstOrderResolver:
    """
    一阶逻辑归结证明器
    """
    
    def __init__(self):
        self.clauses: List[Clause] = []
        self.skolem_functions: Dict[str, str] = {}
        self.skolem_counter = 0
    
    def skolemize(self, formula: Formula) -> Formula:
        """
        Skolem化：消除存在量词
        
        策略：用新的Skolem函数替换存在变量
        ∀x∃y P(x,y) → ∀x P(x, f(x))
        """
        print(f"[Skolem化] 处理公式")
        
        # 简化实现
        if formula.op == "exists":
            var_name = formula.children[0].atom.args[0].name if formula.children else "x"
            # 创建Skolem函数
            skolem_func = f"f{self.skolem_counter}"
            self.skolem_counter += 1
            self.skolem_functions[var_name] = skolem_func
            
            # 替换
            new_formula = formula.children[1] if len(formula.children) > 1 else formula
            return self.skolemize(new_formula)
        
        elif formula.op == "forall":
            # 递归处理
            new_children = [self.skolemize(c) for c in formula.children]
            return Formula(formula.op, new_children, formula.atom)
        
        elif formula.op == "and" or formula.op == "or":
            new_children = [self.skolemize(c) for c in formula.children]
            return Formula(formula.op, new_children)
        
        elif formula.op == "not":
            new_children = [self.skolemize(c) for c in formula.children]
            return Formula(formula.op, new_children)
        
        return formula
    
    def to_clausal_form(self, formula: Formula) -> List[Clause]:
        """
        转换为子句形式
        """
        print(f"[子句化] 转换公式为子句形式")
        
        clauses = []
        
        # 简化实现：直接处理
        if formula.op == "or":
            clause = Clause(set())
            for child in formula.children:
                if child.atom:
                    clause.literals.add(FOLLiteral(child.atom, False))
                elif child.op == "not" and child.children:
                    inner = child.children[0]
                    if inner.atom:
                        clause.literals.add(FOLLiteral(inner.atom, True))
            clauses.append(clause)
        
        elif formula.op == "and":
            for child in formula.children:
                sub_clauses = self.to_clausal_form(child)
                clauses.extend(sub_clauses)
        
        return clauses
    
    def unify_atoms(self, atom1: Atom, atom2: Atom) -> Optional[Substitution]:
        """
        合一同谓词的两个原子公式
        
        Args:
            atom1: 第一个原子公式
            atom2: 第二个原子公式
        
        Returns:
            合一替换或None
        """
        if atom1.predicate != atom2.predicate:
            return None
        
        if len(atom1.args) != len(atom2.args):
            return None
        
        sigma = Substitution()
        
        # 递归合一每个参数
        for arg1, arg2 in zip(atom1.args, atom2.args):
            result = self.unify_terms(arg1, arg2, sigma)
            if result is None:
                return None
            sigma = result
        
        return sigma
    
    def unify_terms(self, t1: Term, t2: Term, sigma: Substitution) -> Optional[Substitution]:
        """
        合一项
        """
        # 应用当前替换
        t1 = sigma.apply_term(t1)
        t2 = sigma.apply_term(t2)
        
        # 变量-项合一
        if t1.kind == "var":
            if t1.name == t2.name:
                return sigma
            new_sigma = Substitution()
            new_sigma.mapping = sigma.mapping.copy()
            new_sigma.mapping[t1.name] = t2
            return new_sigma
        
        if t2.kind == "var":
            new_sigma = Substitution()
            new_sigma.mapping = sigma.mapping.copy()
            new_sigma.mapping[t2.name] = t1
            return new_sigma
        
        if t1.kind == "func" and t2.kind == "func":
            if t1.name != t2.name or len(t1.args) != len(t2.args):
                return None
            
            for arg1, arg2 in zip(t1.args, t2.args):
                result = self.unify_terms(arg1, arg2, sigma)
                if result is None:
                    return None
                sigma = result
            
            return sigma
        
        return None
    
    def resolve_clauses(self, c1: Clause, c2: Clause) -> List[Clause]:
        """
        归结两个子句
        
        Args:
            c1: 第一个子句
            c2: 第二个子句
        
        Returns:
            归结结果列表
        """
        results = []
        
        for lit1 in c1.literals:
            for lit2 in c2.literals:
                # 检查是否互补
                if (lit1.atom.predicate == lit2.atom.predicate and 
                    lit1.negated != lit2.negated):
                    
                    # 尝试合一
                    sigma = self.unify_atoms(lit1.atom, lit2.atom)
                    
                    if sigma is not None:
                        # 构建归结子句
                        new_literals = set()
                        
                        for lit in c1.literals:
                            if lit != lit1:
                                new_literals.add(sigma.apply_literal(lit))
                        
                        for lit in c2.literals:
                            if lit != lit2:
                                new_literals.add(sigma.apply_literal(lit))
                        
                        results.append(Clause(new_literals))
        
        return results
    
    def prove(self, premises: List[Formula], goal: Formula) -> bool:
        """
        证明目标
        
        Args:
            premises: 前提公式列表
            goal: 目标公式
        
        Returns:
            是否可证明
        """
        print(f"\n{'='*50}")
        print(f"一阶归结证明")
        print(f"{'='*50}")
        
        # Step 1: Skolem化
        print("\n步骤1: Skolem化")
        skolemized_premises = [self.skolemize(p) for p in premises]
        skolemized_goal = self.skolemize(Formula("not", [goal]))
        
        # Step 2: 化为子句形式
        print("\n步骤2: 子句化")
        self.clauses = []
        for p in skolemized_premises:
            self.clauses.extend(self.to_clausal_form(p))
        self.clauses.extend(self.to_clausal_form(skolemized_goal))
        
        print(f"生成 {len(self.clauses)} 个子句")
        for c in self.clauses:
            print(f"  {c}")
        
        # Step 3: 归结
        print("\n步骤3: 归结")
        seen_clauses = set()
        for c in self.clauses:
            key = tuple(sorted(str(l) for l in c.literals))
            seen_clauses.add(key)
        
        worklist = list(self.clauses)
        
        for iteration in range(1000):
            if not worklist:
                break
            
            new_clauses = []
            
            for i, c1 in enumerate(worklist):
                for c2 in worklist[i+1:]:
                    resolvents = self.resolve_clauses(c1, c2)
                    
                    for res in resolvents:
                        if res.is_empty():
                            print(f"\n✓ 证明成功: 空子句")
                            return True
                        
                        key = tuple(sorted(str(l) for l in res.literals))
                        if key not in seen_clauses:
                            seen_clauses.add(key)
                            new_clauses.append(res)
                            print(f"  归结: {c1} + {c2} → {res}")
            
            worklist = new_clauses
        
        print(f"\n✗ 无法证明")
        return False


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("一阶逻辑归结证明测试")
    print("=" * 50)
    
    resolver = FirstOrderResolver()
    
    # 创建测试公式
    # 所有人都会死, 苏格拉底是人 → 苏格拉底会死
    # ∀x (Man(x) → Mortal(x)), Man(Socrates) ⊢ Mortal(Socrates)
    
    # Man(x) → Mortal(x) = ¬Man(x) ∨ Mortal(x)
    p1 = Formula("or", [], 
                 Atom("Mortal", [Term("var", "x")]))
    
    # Man(Socrates)
    p2 = Formula("atom", [], 
                 Atom("Man", [Term("const", "Socrates")]))
    
    # ¬Mortal(Socrates)
    g = Formula("atom", [], 
                Atom("Mortal", [Term("const", "Socrates")]))
    
    print("\n测试: 苏格拉底悖论")
    result = resolver.prove([p1, p2], g)
    print(f"\n结果: {'可证明' if result else '不可证明'}")
    
    print("\n✓ 一阶归结证明测试完成")
