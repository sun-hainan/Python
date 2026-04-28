"""
归结原理证明器 (Resolution Theorem Prover)
==========================================
功能：实现命题逻辑的归结原理证明器
支持子句归结、消解律、反证法

核心概念：
1. 子句(Clause): 文字的析取范式
2. 归结(Resolution): 从C1∨L和¬L∨C2导出C1∨C2
3. 反证法: 要证P，即证¬P不可满足
4. 归结序列: 归结步骤的序列

算法：
1. 将公式转换为CNF
2. 加入否定命题
3. 归结直到产生空子句(⊥)或无可归结
"""

from typing import Set, Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum, auto


@dataclass
class Literal:
    """
    文字
    - atom: 原子命题
    - negated: 是否为否定
    """
    atom: str
    negated: bool = False
    
    def __str__(self):
        if self.negated:
            return f"¬{self.atom}"
        return self.atom
    
    def __hash__(self):
        return hash((self.atom, self.negated))
    
    def __eq__(self, other):
        return self.atom == other.atom and self.negated == other.negated
    
    def complement(self) -> 'Literal':
        """返回该文字的补"""
        return Literal(self.atom, not self.negated)


@dataclass
class Clause:
    """
    子句：文字的析取
    - literals: 文字集合
    """
    literals: Set[Literal] = field(default_factory=set)
    
    def __str__(self):
        if not self.literals:
            return "⊥"                          # 空子句
        return " ∨ ".join(str(lit) for lit in self.literals)
    
    def is_empty(self) -> bool:
        """是否为空子句"""
        return len(self.literals) == 0
    
    def is_unit(self) -> bool:
        """是否为单位子句"""
        return len(self.literals) == 1
    
    def is_tautology(self) -> bool:
        """是否重言式（含有L和¬L）"""
        for lit in self.literals:
            if lit.complement() in self.literals:
                return True
        return False


class CNF:
    """
    合取范式
    - clauses: 子句集合
    """
    
    def __init__(self, clauses: List[Clause] = None):
        self.clauses = clauses or []
    
    def add_clause(self, clause: Clause):
        """添加子句"""
        # 忽略重言式
        if not clause.is_tautology():
            self.clauses.append(clause)
    
    def __str__(self):
        return " ∧ ".join(f"({c})" for c in self.clauses)


class ResolutionProver:
    """
    归结原理证明器
    
    支持命题逻辑的自动证明
    """
    
    def __init__(self):
        self.cnf: Optional[CNF] = None
        self.resolution_steps: List[Tuple[Clause, Clause, Clause]] = []
        self.max_steps = 1000
    
    def parse_formula(self, formula_str: str) -> CNF:
        """
        解析公式字符串为CNF
        简化实现：支持简单的文字和∧/∨/¬
        
        格式: "p ∨ q ∧ ¬r"
        """
        print(f"[归结] 解析公式: {formula_str}")
        
        # 简化：解析简单的析取范式
        clauses = []
        
        # 分割子句
        if "∧" in formula_str:
            clause_strs = formula_str.split("∧")
        else:
            clause_strs = [formula_str]
        
        for clause_str in clause_strs:
            clause_str = clause_str.strip().strip("()")
            literals = set()
            
            # 分割文字
            if "∨" in clause_str:
                lit_strs = clause_str.split("∨")
            else:
                lit_strs = [clause_str]
            
            for lit_str in lit_strs:
                lit_str = lit_str.strip()
                if lit_str.startswith("¬"):
                    literals.add(Literal(lit_str[1:], negated=True))
                else:
                    literals.add(Literal(lit_str, negated=False))
            
            clause = Clause(literals)
            if not clause.is_tautology():
                clauses.append(clause)
        
        cnf = CNF(clauses)
        print(f"[归结] CNF子句数: {len(clauses)}")
        
        return cnf
    
    def negate_formula(self, cnf: CNF) -> CNF:
        """
        对公式取否定并转换为CNF
        
        实际上：直接添加否定命题
        要证P，只需证明¬P不可满足
        """
        print(f"[归结] 添加否定命题")
        
        new_cnf = CNF(list(cnf.clauses))
        
        # 简化实现：添加假子句作为目标
        # 实际应用中需要正确处理否定
        return new_cnf
    
    def resolve(self, c1: Clause, c2: Clause) -> List[Clause]:
        """
        归结两个子句
        
        找到 c1 中的文字 L 和 c2 中的文字 ¬L（或反之）
        消去 L 和 ¬L，合并剩余部分
        
        Args:
            c1: 第一个子句
            c2: 第二个子句
        
        Returns:
            归结结果子句列表
        """
        results = []
        
        for lit1 in c1.literals:
            for lit2 in c2.literals:
                # 检查是否互补
                if lit1.atom == lit2.atom and lit1.negated != lit2.negated:
                    # 构建归结子句
                    new_literals = set()
                    
                    for lit in c1.literals:
                        if lit != lit1:
                            new_literals.add(lit)
                    
                    for lit in c2.literals:
                        if lit != lit2:
                            new_literals.add(lit)
                    
                    resolvent = Clause(new_literals)
                    
                    # 忽略重言式
                    if not resolvent.is_tautology():
                        results.append(resolvent)
        
        return results
    
    def prove(self, premises: List[str], goal: str) -> Tuple[bool, Optional[List[Clause]]]:
        """
        证明主方法
        
        Args:
            premises: 前提公式列表
            goal: 目标公式
        
        Returns:
            (是否可证明, 归结序列)
        """
        print(f"\n{'='*50}")
        print(f"归结证明开始")
        print(f"{'='*50}")
        
        # 构建初始CNF
        all_formulas = premises + [f"¬{goal}"]
        self.cnf = CNF()
        
        for formula_str in all_formulas:
            formula_cnf = self.parse_formula(formula_str)
            for clause in formula_cnf.clauses:
                self.cnf.add_clause(clause)
        
        print(f"[归结] 初始子句数: {len(self.cnf.clauses)}")
        
        # 归结过程
        self.resolution_steps = []
        new_clauses = set(self.cnf.clauses)
        
        for step in range(self.max_steps):
            if not new_clauses:
                break
            
            current_new = set()
            
            # 对每对新子句进行归结
            clause_list = list(new_clauses)
            for i, c1 in enumerate(clause_list):
                for c2 in clause_list[i+1:]:
                    resolvents = self.resolve(c1, c2)
                    
                    for res in resolvents:
                        if res.is_empty():
                            # 空子句！证明成功
                            print(f"[归结] ✓ 推导出空子句 (步骤 {step+1})")
                            self.cnf.add_clause(res)
                            return True, self.resolution_steps
                        
                        if res not in self.cnf.clauses and res not in current_new:
                            current_new.add(res)
                            self.resolution_steps.append((c1, c2, res))
                            print(f"[归结] 归结: {c1} + {c2} → {res}")
            
            # 添加新子句
            for clause in current_new:
                self.cnf.add_clause(clause)
            
            new_clauses = current_new
            
            if not new_clauses:
                break
        
        print(f"[归结] ✗ 无法推导出空子句")
        return False, self.resolution_steps


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("归结原理证明器测试")
    print("=" * 50)
    
    prover = ResolutionProver()
    
    # 测试1: 简单肯定前件
    print("\n--- 测试1: 肯定前件 (Modus Ponens) ---")
    # 前提: p, p → q
    # 目标: q
    premises = ["p", "p ∨ r"]
    goal = "q"
    
    # 注意：简化实现，直接添加归结
    prover.cnf = CNF([
        Clause({Literal("p")}),
        Clause({Literal("p"), Literal("q")}),     # p → q = ¬p ∨ q
    ])
    
    # 添加目标否定
    prover.cnf.add_clause(Clause({Literal("q", negated=True)}))
    
    print(f"子句集合:")
    for c in prover.cnf.clauses:
        print(f"  {c}")
    
    # 归结
    print("\n归结过程:")
    new_clauses = set(prover.cnf.clauses)
    
    for c1 in list(prover.cnf.clauses):
        for c2 in prover.cnf.clauses:
            resolvents = prover.resolve(c1, c2)
            for res in resolvents:
                if res.is_empty():
                    print(f"\n✓ 证明成功: 推导出空子句")
                    break
                if res not in prover.cnf.clauses:
                    new_clauses.add(res)
                    print(f"  {c1} + {c2} → {res}")
    
    # 测试2: 简单证明
    print("\n--- 测试2: 简单逻辑证明 ---")
    # 要证: (p → q) → (¬q → ¬p) (逆否命题)
    prover2 = ResolutionProver()
    prover2.cnf = CNF([
        Clause({Literal("p", negated=True), Literal("q")}),  # ¬p ∨ q
    ])
    
    # 添加结论否定: ¬(¬q → ¬p) = ¬(q ∨ ¬p) = ¬q ∧ p
    prover2.cnf.add_clause(Clause({Literal("q", negated=True)}))
    prover2.cnf.add_clause(Clause({Literal("p")}))
    
    print(f"子句集合:")
    for c in prover2.cnf.clauses:
        print(f"  {c}")
    
    print("\n✓ 归结原理证明器测试完成")
