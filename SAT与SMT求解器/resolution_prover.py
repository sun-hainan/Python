# -*- coding: utf-8 -*-
"""
命题逻辑归结证明系统（Resolution Prover）
功能：使用归结原理证明命题公式的永真性/可满足性/蕴含关系

归结原理：
若两个子句 C1, C2 包含互补文字 L 和 ¬L，则可以推导新子句
C = (C1 - {L}) ∪ (C2 - {¬L})
称为 C1 和 C2 的归结结果

作者：Automated Theorem Proving Team
"""

from typing import List, Set, Tuple, Optional, FrozenSet
from collections import defaultdict


class Literal:
    """文字：正或负的原子公式"""
    __slots__ = ['atom', 'sign']
    
    def __init__(self, atom: str, sign: bool = True):
        """
        Args:
            atom: 原子公式名称
            sign: True=正文字, False=负文字
        """
        self.atom = atom
        self.sign = sign
    
    def is_negation_of(self, other: 'Literal') -> bool:
        """检查是否为另一个文字的否定"""
        return self.atom == other.atom and self.sign != other.sign
    
    def negated(self) -> 'Literal':
        """返回否定的文字"""
        return Literal(self.atom, not self.sign)
    
    def __hash__(self):
        return hash((self.atom, self.sign))
    
    def __eq__(self, other):
        return isinstance(other, Literal) and self.atom == other.atom and self.sign == other.sign
    
    def __repr__(self):
        return self.atom if self.sign else f"¬{self.atom}"


class Clause:
    """子句：文字的集合（析取）"""
    __slots__ = ['literals', 'frozen']
    
    def __init__(self, literals: Set[Literal] = None):
        self.literals = frozenset(literals) if literals else frozenset()
        self.frozen = True
    
    def add(self, lit: Literal):
        if self.frozen:
            self.literals = set(self.literals)
            self.frozen = False
        self.literals.add(lit)
    
    def resolved_with(self, other: 'Clause', lit: Literal) -> Optional['Clause']:
        """
        对两个子句关于文字lit进行归结
        
        Args:
            other: 另一个子句
            lit: 进行归结的互补文字
            
        Returns:
            归结结果子句，若为空则表示冲突（矛盾）
        """
        neg_lit = lit.negated()
        
        # 检查other是否包含neg_lit
        if neg_lit not in other.literals:
            return None
        
        # 归结：删除互补文字后合并
        new_lits = set(self.literals)
        new_lits.discard(lit)
        other_lits = set(other.literals)
        other_lits.discard(neg_lit)
        new_lits.update(other_lits)
        
        return Clause(new_lits) if new_lits else None
    
    def is_empty(self) -> bool:
        return len(self.literals) == 0
    
    def __hash__(self):
        return hash(self.literals)
    
    def __eq__(self, other):
        return isinstance(other, Clause) and self.literals == other.literals
    
    def __repr__(self):
        if not self.literals:
            return "⊥"  # 空子句
        return " ∨ ".join(str(lit) for lit in self.literals)


class ResolutionProver:
    """
    归结定理证明器
    
    使用归结原理证明 φ ⊨ ψ 等价于证明 φ ∧ ¬ψ ⊨ ⊥
    即 φ ∧ ¬ψ 永假（不可满足）
    """

    def __init__(self):
        self.clauses: Set[Clause] = set()  # 已知子句集
        self.proof_steps: List[Tuple[Clause, Clause, Literal]] = []  # 证明步骤记录

    def add_clause(self, clause: Clause):
        """添加子句到知识库"""
        self.clauses.add(clause)

    def prove(self, premises: List[Clause], goal: Clause) -> Tuple[bool, List]:
        """
        证明 goal 可以从 premises 推出
        
        φ ⊨ ψ  ⟺  φ ∧ ¬ψ 不可满足
        
        Args:
            premises: 前提子句列表
            goal: 目标子句
            
        Returns:
            (可证明, 证明步骤列表)
        """
        # 构建前提 + 目标否定
        working_set = set(premises)
        neg_goal_lits = {lit.negated() for lit in goal.literals}
        working_set.add(Clause(neg_goal_lits))
        
        new_clauses = set(working_set)
        iteration = 0
        max_iterations = 10000
        
        while new_clauses and iteration < max_iterations:
            iteration += 1
            current = new_clauses
            new_clauses = set()
            
            # 对所有子句对进行归结
            clause_list = list(working_set)
            for i, c1 in enumerate(clause_list):
                for c2 in clause_list[i + 1:]:
                    # 找互补文字对
                    for lit in c1.literals:
                        if lit.negated() in c2.literals:
                            resolvent = c1.resolved_with(c2, lit)
                            if resolvent is None:
                                continue
                            
                            if resolvent.is_empty():
                                # 空子句！证明完成
                                self.proof_steps.append((c1, c2, lit))
                                return True, self.proof_steps
                            
                            if resolvent not in working_set:
                                working_set.add(resolvent)
                                new_clauses.add(resolvent)
                                self.proof_steps.append((c1, c2, lit))
            
            # 剪枝：避免子句爆炸
            if len(working_set) > 5000:
                # 删除包含冗余文字的子句
                working_set = self._subsume(working_set)
        
        return False, self.proof_steps

    def _subsume(self, clauses: Set[Clause]) -> Set[Clause]:
        """包含删除：若C1 ⊆ C2则删除C2"""
        result = set()
        for c in clauses:
            subsumed = False
            for other in result:
                if other.literals <= c.literals and other.literals != c.literals:
                    subsumed = True
                    break
            if not subsumed:
                result.add(c)
        return result

    def is_satisfiable(self, clauses: List[Clause]) -> Tuple[bool, Optional[Clause]]:
        """
        检查子句集是否可满足
        
        Returns:
            (可满足, None) 或 (不可满足, 空子句)
        """
        _, proof = self.prove([], Clause())
        if proof:
            return False, Clause()
        return True, None


def parse_clause(text: str) -> Clause:
    """
    解析简单文字表达式为子句
    
    格式: "p q ~r" → {p, q, ¬r}
    ~ 或 - 表示否定
    """
    tokens = text.split()
    lits = set()
    for tok in tokens:
        if tok.startswith('~') or tok.startswith('-'):
            lits.add(Literal(tok[1:], sign=False))
        else:
            lits.add(Literal(tok, sign=True))
    return Clause(lits)


def example_basic_resolution():
    """基本归结示例"""
    prover = ResolutionProver()
    
    # 例：p ∨ q, ¬p ∨ r, ¬q ∨ r ⊨ r
    # 对应: (p∨q) ∧ (¬p∨r) ∧ (¬q∨r) → r
    # 即: (p∨q) ∧ (¬p∨r) ∧ (¬q∨r) ∧ ¬r 不可满足
    
    c1 = parse_clause("p q")        # p ∨ q
    c2 = parse_clause("~p r")       # ¬p ∨ r
    c3 = parse_clause("~q r")       # ¬q ∨ r
    goal = parse_clause("r")        # goal: r
    neg_goal = Clause({Literal("r", False)})  # ¬r
    
    # (p∨q), (¬p∨r), (¬q∨r), ¬r
    provable, steps = prover.prove([c1, c2, c3], goal)
    print(f"归结证明 {len(steps)} 步: {'成功' if provable else '失败'}")


def example_unsat_proof():
    """不可满足性证明示例"""
    prover = ResolutionProver()
    
    # 经典矛盾: p, ¬p
    c1 = parse_clause("p")
    c2 = parse_clause("~p")
    
    sat, empty = prover.is_satisfiable([c1, c2])
    print(f"子句集 {{p, ¬p}} 可满足: {sat}")


def example_transitivity():
    """传递性证明: p→q, q→r ⊨ p→r"""
    prover = ResolutionProver()
    
    # p→q ≡ ¬p ∨ q
    # q→r ≡ ¬q ∨ r
    # goal: p→r ≡ ¬p ∨ r
    
    c1 = parse_clause("~p q")  # ¬p ∨ q
    c2 = parse_clause("~q r")  # ¬q ∨ r
    goal = parse_clause("~p r")  # ¬p ∨ r
    
    provable, _ = prover.prove([c1, c2], goal)
    print(f"传递性证明: {'成功' if provable else '失败'}")


if __name__ == "__main__":
    print("=" * 50)
    print("归结证明系统 测试")
    print("=" * 50)
    
    example_basic_resolution()
    print()
    example_unsat_proof()
    print()
    example_transitivity()
