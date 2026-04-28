"""
矢列演算 (Sequent Calculus)
==========================
功能：实现一阶逻辑的矢列演算系统
基于 Gentzen 的 LK 系统

核心概念：
1. 矢列(Sequent): Γ ⊢ Δ 左右两边的公式序列
2. 左规则(Left Rules): 处理左侧公式的规则
3. 右规则(Right Rules): 处理右侧公式的规则
4. 结构规则: 交换、弱化、收缩
5. 逻辑规则: ∧, ∨, →, ¬, ∀, ∃

矢列形式：
- Γ: 前件(Antecedent)公式列表
- ⊢: 推出符号
- Δ: 后件(Succedent)公式列表

矢列有效：Γ ⊢ Δ 当且仅当 Γ 的合取蕴含 Δ 的析取
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto


@dataclass
class Formula:
    """公式"""
    kind: str                                     # atom, and, or, implies, not, forall, exists
    name: str = ""                                # 原子名
    left: Optional['Formula'] = None             # 左子公式
    right: Optional['Formula'] = None            # 右子公式
    child: Optional['Formula'] = None             # 单子公式
    var: str = ""                                 # 变量名（量词用）
    
    def __str__(self):
        if self.kind == "atom":
            return self.name
        elif self.kind == "and":
            return f"({self.left} ∧ {self.right})"
        elif self.kind == "or":
            return f"({self.left} ∨ {self.right})"
        elif self.kind == "implies":
            return f"({self.left} → {self.right})"
        elif self.kind == "not":
            return f"¬{self.child}"
        elif self.kind == "forall":
            return f"∀{self.var}.{self.child}"
        elif self.kind == "exists":
            return f"∃{self.var}.{self.child}"
        return "?"


@dataclass
class Sequent:
    """
    矢列
    Γ ⊢ Δ
    
    - antecedent: 前件列表 (Γ)
    - succedent: 后件列表 (Δ)
    """
    antecedent: List[Formula] = field(default_factory=list)
    succedent: List[Formula] = field(default_factory=list)
    
    def __str__(self):
        gamma = ", ".join(str(f) for f in self.antecedent) or "⊥"
        delta = ", ".join(str(f) for f in self.succedent) or "⊥"
        return f"{gamma} ⊢ {delta}"
    
    def is_axiom(self) -> bool:
        """检查是否是公理（有相同公式在两侧）"""
        for f in self.antecedent:
            if f.kind == "atom":
                for g in self.succedent:
                    if g.kind == "atom" and f.name == g.name:
                        return True
        return False


@dataclass
class ProofNode:
    """证明树节点"""
    sequent: Sequent
    rule: str = ""                                # 应用规则名
    children: List['ProofNode'] = field(default_factory=list)
    active_formula: Optional[Formula] = None      # 活动公式
    depth: int = 0


class SequentCalculus:
    """
    矢列演算系统 (Gentzen LK)
    """
    
    def __init__(self):
        self.proof_tree: Optional[ProofNode] = None
        self.stats: Dict[str, int] = {}          # 规则使用统计
    
    # -------------------- 矢列规则 --------------------
    
    def apply_left_and(self, seq: Sequent, formula: Formula) -> List[Sequent]:
        """
        ∧L: Γ, A ∧ B, A ⊢ Δ  →  Γ, A ∧ B ⊢ Δ
        """
        if formula.kind != "and":
            return []
        
        new_seq = Sequent(
            antecedent=seq.antecedent.copy(),
            succedent=seq.succedent.copy()
        )
        # 用A替换A∧B
        idx = next((i for i, f in enumerate(new_seq.antecedent) if f == formula), -1)
        if idx >= 0:
            new_seq.antecedent[idx] = formula.left
        
        return [new_seq]
    
    def apply_right_and(self, seq: Sequent, formula: Formula) -> List[Sequent]:
        """
        ∧R: Γ ⊢ A, Δ 且 Γ ⊢ B, Δ  →  Γ ⊢ A ∧ B, Δ
        """
        if formula.kind != "and":
            return []
        
        seq1 = Sequent(
            antecedent=seq.antecedent.copy(),
            succedent=seq.succedent.copy() + [formula.left]
        )
        seq2 = Sequent(
            antecedent=seq.antecedent.copy(),
            succedent=seq.succedent.copy() + [formula.right]
        )
        
        return [seq1, seq2]
    
    def apply_left_or(self, seq: Sequent, formula: Formula) -> List[Sequent]:
        """
        ∨L: Γ, A ⊢ Δ 且 Γ, B ⊢ Δ  →  Γ, A ∨ B ⊢ Δ
        """
        if formula.kind != "or":
            return []
        
        seq1 = Sequent(
            antecedent=seq.antecedent.copy() + [formula.left],
            succedent=seq.succedent.copy()
        )
        seq2 = Sequent(
            antecedent=seq.antecedent.copy() + [formula.right],
            succedent=seq.succedent.copy()
        )
        
        return [seq1, seq2]
    
    def apply_right_or(self, seq: Sequent, formula: Formula) -> List[Sequent]:
        """
        ∨R: Γ ⊢ A ∨ B, Δ  →  Γ ⊢ A ∨ B, Δ
        """
        if formula.kind != "or":
            return []
        
        new_seq = Sequent(
            antecedent=seq.antecedent.copy(),
            succedent=seq.succedent.copy()
        )
        idx = next((i for i, f in enumerate(new_seq.succedent) if f == formula), -1)
        if idx >= 0:
            new_seq.succedent[idx] = formula.right
        
        return [new_seq]
    
    def apply_left_implies(self, seq: Sequent, formula: Formula) -> List[Sequent]:
        """
        →L: Γ ⊢ A, Δ 且 Γ, B ⊢ Δ  →  Γ, A → B ⊢ Δ
        """
        if formula.kind != "implies":
            return []
        
        seq1 = Sequent(
            antecedent=seq.antecedent.copy(),
            succedent=seq.succedent.copy() + [formula.left]
        )
        seq2 = Sequent(
            antecedent=seq.antecedent.copy() + [formula.right],
            succedent=seq.succedent.copy()
        )
        
        return [seq1, seq2]
    
    def apply_right_implies(self, seq: Sequent, formula: Formula) -> List[Sequent]:
        """
        →R: Γ, A ⊢ B, Δ  →  Γ ⊢ A → B, Δ
        """
        if formula.kind != "implies":
            return []
        
        new_seq = Sequent(
            antecedent=seq.antecedent.copy() + [formula.left],
            succedent=seq.succedent.copy()
        )
        idx = next((i for i, f in enumerate(new_seq.succedent) if f == formula), -1)
        if idx >= 0:
            new_seq.succedent[idx] = formula.right
        
        return [new_seq]
    
    def apply_left_not(self, seq: Sequent, formula: Formula) -> List[Sequent]:
        """
        ¬L: Γ ⊢ A, Δ  →  Γ, ¬A ⊢ Δ
        """
        if formula.kind != "not":
            return []
        
        new_seq = Sequent(
            antecedent=seq.antecedent.copy(),
            succedent=seq.succedent.copy()
        )
        idx = next((i for i, f in enumerate(new_seq.succedent) if f == formula.child), -1)
        if idx < 0:
            new_seq.succedent.append(formula.child)
        
        return [new_seq]
    
    def apply_right_not(self, seq: Sequent, formula: Formula) -> List[Sequent]:
        """
        ¬R: Γ, A ⊢ Δ  →  Γ ⊢ ¬A, Δ
        """
        if formula.kind != "not":
            return []
        
        new_seq = Sequent(
            antecedent=seq.antecedent.copy()
        )
        idx = next((i for i, f in enumerate(new_seq.antecedent) if f == formula.child), -1)
        if idx < 0:
            new_seq.antecedent.append(formula.child)
        new_seq.succedent = seq.succedent.copy()
        
        return [new_seq]
    
    # -------------------- 证明搜索 --------------------
    
    def prove(self, premises: List[str], conclusion: str) -> bool:
        """
        证明矢列
        
        要证: premises ⊢ conclusion
        即: 合取(premises) ⊢ conclusion
        
        Args:
            premises: 前提公式列表
            conclusion: 结论公式
        
        Returns:
            是否可证明
        """
        print(f"\n{'='*50}")
        print(f"矢列演算证明")
        print(f"{'='*50}")
        print(f"前提: {premises}")
        print(f"结论: {conclusion}")
        
        # 解析公式
        antecedent = [self._parse_formula(p) for p in premises]
        succedent = [self._parse_formula(conclusion)]
        
        initial_sequent = Sequent(antecedent, succedent)
        print(f"矢列: {initial_sequent}")
        
        # 构建证明树
        self.proof_tree = ProofNode(initial_sequent, depth=0)
        
        # 递归证明
        result = self._prove_recursive(self.proof_tree)
        
        if result:
            print(f"\n✓ 证明成功")
        else:
            print(f"\n✗ 证明失败")
        
        return result
    
    def _parse_formula(self, s: str) -> Formula:
        """解析公式字符串"""
        s = s.strip()
        
        # 括号
        if s.startswith("(") and s.endswith(")"):
            return self._parse_formula(s[1:-1])
        
        # 否定
        if s.startswith("¬"):
            child = self._parse_formula(s[1:])
            return Formula(kind="not", child=child)
        
        # 二元运算符
        for op, kind in [("∧", "and"), ("∨", "or"), ("→", "implies")]:
            if op in s:
                parts = s.split(op)
                if len(parts) == 2:
                    left = self._parse_formula(parts[0])
                    right = self._parse_formula(parts[1])
                    return Formula(kind=kind, left=left, right=right)
        
        # 量词
        if "∀" in s:
            idx = s.index("∀")
            var = s[idx+1]
            rest = s[idx+2:].lstrip(". ")
            child = self._parse_formula(rest)
            return Formula(kind="forall", var=var, child=child)
        
        if "∃" in s:
            idx = s.index("∃")
            var = s[idx+1]
            rest = s[idx+2:].lstrip(". ")
            child = self._parse_formula(rest)
            return Formula(kind="exists", var=var, child=child)
        
        # 原子
        return Formula(kind="atom", name=s)
    
    def _prove_recursive(self, node: ProofNode) -> bool:
        """递归证明"""
        seq = node.sequent
        
        # 公理检查
        if seq.is_axiom():
            node.rule = "公理"
            print(f"[证明] 深度{node.depth}: 公理 {seq}")
            return True
        
        # 尝试应用规则
        # 先处理右侧
        for i, formula in enumerate(seq.succedent):
            if formula.kind in ("and", "or", "implies"):
                new_seqs = self.apply_right_and(seq, formula) if formula.kind == "and" else \
                           self.apply_right_or(seq, formula) if formula.kind == "or" else \
                           self.apply_right_implies(seq, formula)
                
                if new_seqs:
                    node.rule = f"R{formula.kind}"
                    node.active_formula = formula
                    for new_seq in new_seqs:
                        child = ProofNode(new_seq, depth=node.depth + 1)
                        node.children.append(child)
                    
                    # 递归证明子节点
                    results = [self._prove_recursive(c) for c in node.children]
                    return all(results)
            
            elif formula.kind == "not":
                new_seqs = self.apply_right_not(seq, formula)
                if new_seqs:
                    node.rule = "¬R"
                    node.active_formula = formula
                    for new_seq in new_seqs:
                        child = ProofNode(new_seq, depth=node.depth + 1)
                        node.children.append(child)
                    return all(self._prove_recursive(c) for c in node.children)
        
        # 处理左侧
        for i, formula in enumerate(seq.antecedent):
            if formula.kind in ("and", "or", "implies"):
                new_seqs = self.apply_left_and(seq, formula) if formula.kind == "and" else \
                           self.apply_left_or(seq, formula) if formula.kind == "or" else \
                           self.apply_left_implies(seq, formula)
                
                if new_seqs:
                    node.rule = f"L{formula.kind}"
                    node.active_formula = formula
                    for new_seq in new_seqs:
                        child = ProofNode(new_seq, depth=node.depth + 1)
                        node.children.append(child)
                    
                    results = [self._prove_recursive(c) for c in node.children]
                    return all(results)
            
            elif formula.kind == "not":
                new_seqs = self.apply_left_not(seq, formula)
                if new_seqs:
                    node.rule = "¬L"
                    node.active_formula = formula
                    for new_seq in new_seqs:
                        child = ProofNode(new_seq, depth=node.depth + 1)
                        node.children.append(child)
                    return all(self._prove_recursive(c) for c in node.children)
        
        # 无法继续
        print(f"[证明] 深度{node.depth}: 无法继续 {seq}")
        return False


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("矢列演算测试")
    print("=" * 50)
    
    prover = SequentCalculus()
    
    # 测试1: 恒真式
    print("\n--- 测试1: ⊢ p ∨ ¬p ---")
    result = prover.prove([], "p ∨ ¬p")
    print(f"结果: {'可证明' if result else '不可证明'}")
    
    # 测试2: 肯定前件
    print("\n--- 测试2: p, p → q ⊢ q ---")
    result = prover.prove(["p", "p → q"], "q")
    print(f"结果: {'可证明' if result else '不可证明'}")
    
    # 测试3: 逆否命题
    print("\n--- 测试3: ⊢ (p → q) → (¬q → ¬p) ---")
    result = prover.prove([], "(p → q) → (¬q → ¬p)")
    print(f"结果: {'可证明' if result else '不可证明'}")
    
    # 测试4: De Morgan律
    print("\n--- 测试4: ¬(p ∧ q) ⊢ ¬p ∨ ¬q ---")
    result = prover.prove(["¬(p ∧ q)"], "¬p ∨ ¬q")
    print(f"结果: {'可证明' if result else '不可证明'}")
    
    print("\n✓ 矢列演算测试完成")
