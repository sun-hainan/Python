"""
表算法 (Tableau Method)
=====================
功能：实现命题逻辑的表算法
一种基于树结构的证明方法

核心概念：
1. 表(Tableau): 表示公式结构的树结构
2. α规则: 合取分解
   - α1 ∧ α2 → α1, α2
3. β规则: 析取分解
   - β1 ∨ β2 → β1 | β2 (分支)
4. γ规则: 双重否定消除
5. 封闭表: 枝上同时出现p和¬p

证明策略：深度优先搜索表的封闭
"""

from typing import Set, Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum, auto


class Sign(Enum):
    """文字符号"""
    POSITIVE = auto()                            # 正
    NEGATIVE = auto()                            # 负


@dataclass
class Literal:
    """命题文字"""
    name: str
    sign: Sign
    
    def __str__(self):
        if self.sign == Sign.NEGATIVE:
            return f"¬{self.name}"
        return self.name
    
    def complement(self) -> 'Literal':
        return Literal(self.name, Sign.NEGATIVE if self.sign == Sign.POSITIVE else Sign.POSITIVE)


@dataclass
class FormulaType(Enum):
    """公式类型"""
    LITERAL = auto()                             # 文字
    AND = auto()                                 # 合取
    OR = auto()                                  # 析取
    NOT = auto()                                 # 否定
    IMPLIES = auto()                             # 蕴含


@dataclass
class Formula:
    """命题公式"""
    kind: FormulaType
    name: str = ""                               # 文字名（如果是文字）
    left: Optional['Formula'] = None            # 左子公式
    right: Optional['Formula'] = None           # 右子公式
    child: Optional['Formula'] = None           # 单子公式
    
    def to_literals(self) -> Set[Literal]:
        """转换为文字集合（用于检查封闭）"""
        if self.kind == FormulaType.LITERAL:
            return {Literal(self.name, Sign.POSITIVE if self.name[0].isupper() else Sign.NEGATIVE)}
        elif self.kind == FormulaType.NOT and self.child:
            if self.child.kind == FormulaType.LITERAL:
                neg = Sign.NEGATIVE if self.child.name[0].isupper() else Sign.POSITIVE
                return {Literal(self.child.name, neg)}
        return set()


@dataclass
class Branch:
    """
    表枝
    - formulas: 枝上的公式集合
    - closed: 是否封闭
    """
    formulas: List[Formula] = field(default_factory=list)
    closed: bool = False
    closure_reason: Optional[str] = None       # 封闭原因


@dataclass
class Tableau:
    """
    表
    - branches: 分支列表
    - root: 根公式
    """
    branches: List[Branch] = field(default_factory=list)


class AlphaRule:
    """α规则: 合取分解"""
    
    @staticmethod
    def apply(formula: Formula) -> Tuple[Formula, Formula]:
        """
        α: A ∧ B → A, B
        
        Returns:
            (A, B)
        """
        return formula.left, formula.right


class BetaRule:
    """β规则: 析取分解（产生分支）"""
    
    @staticmethod
    def apply(formula: Formula) -> Tuple[Formula, Formula]:
        """
        β: A ∨ B → A | B (分支)
        
        Returns:
            (A, B)
        """
        return formula.left, formula.right


class GammaRule:
    """γ规则: 双重否定消除"""
    
    @staticmethod
    def apply(formula: Formula) -> Formula:
        """
        γ: ¬¬A → A
        """
        if formula.child and formula.child.kind == FormulaType.NOT:
            return formula.child.child
        return formula


class TableauProver:
    """
    表算法证明器
    """
    
    def __init__(self):
        self.tableau: Optional[Tableau] = None
        self.alpha_rules = AlphaRule()
        self.beta_rules = BetaRule()
        self.gamma_rules = GammaRule()
    
    def parse_formula(self, formula_str: str) -> Formula:
        """
        解析公式字符串
        
        支持: ∧, ∨, →, ¬
        """
        formula_str = formula_str.strip()
        
        # 括号处理
        if formula_str.startswith("(") and formula_str.endswith(")"):
            return self.parse_formula(formula_str[1:-1])
        
        # 否定
        if formula_str.startswith("¬"):
            child = self.parse_formula(formula_str[1:])
            return Formula(FormulaType.NOT, child=child)
        
        # 蕴含
        if "→" in formula_str:
            parts = formula_str.split("→")
            if len(parts) == 2:
                left = self.parse_formula(parts[0])
                right = self.parse_formula(parts[1])
                # A → B ≡ ¬A ∨ B
                not_left = Formula(FormulaType.NOT, child=left)
                return Formula(FormulaType.OR, left=not_left, right=right)
        
        # 合取
        if "∧" in formula_str:
            parts = formula_str.split("∧")
            if len(parts) == 2:
                left = self.parse_formula(parts[0])
                right = self.parse_formula(parts[1])
                return Formula(FormulaType.AND, left=left, right=right)
        
        # 析取
        if "∨" in formula_str:
            parts = formula_str.split("∨")
            if len(parts) == 2:
                left = self.parse_formula(parts[0])
                right = self.parse_formula(parts[1])
                return Formula(FormulaType.OR, left=left, right=right)
        
        # 文字
        return Formula(FormulaType.LITERAL, name=formula_str.strip())
    
    def is_literal(self, formula: Formula) -> bool:
        """检查是否为文字"""
        return formula.kind == FormulaType.LITERAL or (
            formula.kind == FormulaType.NOT and 
            formula.child and 
            formula.child.kind == FormulaType.LITERAL
        )
    
    def get_literal(self, formula: Formula) -> Optional[Literal]:
        """获取文字"""
        if formula.kind == FormulaType.LITERAL:
            return Literal(formula.name, Sign.POSITIVE)
        if formula.kind == FormulaType.NOT and formula.child:
            if formula.child.kind == FormulaType.LITERAL:
                return Literal(formula.child.name, Sign.NEGATIVE)
        return None
    
    def check_branch_closure(self, branch: Branch) -> bool:
        """
        检查分支是否封闭
        
        封闭条件：枝上同时存在p和¬p
        """
        literals: Set[str] = set()
        
        for formula in branch.formulas:
            lit = self.get_literal(formula)
            if lit:
                key = f"{'+' if lit.sign == Sign.POSITIVE else '-'}{lit.name}"
                if key in literals:
                    branch.closed = True
                    branch.closure_reason = f"包含 {lit} 和其补"
                    return True
                literals.add(key)
        
        return False
    
    def expand_branch(self, branch: Branch) -> List[Branch]:
        """
        展开分支
        
        策略：
        1. 找α公式（合取），直接展开
        2. 找β公式（析取），分支展开
        3. 找γ公式（双重否定），直接展开
        """
        new_branches = [branch]
        
        for formula in branch.formulas:
            if formula.kind == FormulaType.AND:
                # α规则
                f1, f2 = self.alpha_rules.apply(formula)
                
                for nb in new_branches:
                    nb.formulas.append(f1)
                    nb.formulas.append(f2)
                
                return self.expand_branch(new_branches[0])
            
            elif formula.kind == FormulaType.OR:
                # β规则：分支
                f1, f2 = self.beta_rules.apply(formula)
                
                # 创建两个分支
                branch1 = Branch(list(branch.formulas) + [f1])
                branch2 = Branch(list(branch.formulas) + [f2])
                
                new_branches = [branch1, branch2]
            
            elif formula.kind == FormulaType.NOT and formula.child:
                if formula.child.kind == FormulaType.NOT:
                    # γ规则
                    new_formula = self.gamma_rules.apply(formula)
                    
                    for nb in new_branches:
                        nb.formulas.append(new_formula)
                    
                    return self.expand_branch(new_branches[0])
        
        return new_branches
    
    def prove(self, formula_str: str) -> bool:
        """
        证明公式
        
        表算法证明：构造闭表则证明成功
        
        Args:
            formula_str: 要证明的公式
        
        Returns:
            是否可证明
        """
        print(f"\n{'='*50}")
        print(f"表算法证明: {formula_str}")
        print(f"{'='*50}")
        
        # 解析公式
        formula = self.parse_formula(formula_str)
        
        # 否定公式
        negated = Formula(FormulaType.NOT, child=formula)
        
        # 创建初始分支
        initial_branch = Branch([negated])
        self.tableau = Tableau([initial_branch])
        
        # 递归展开
        return self._prove_recursive()
    
    def _prove_recursive(self) -> bool:
        """递归证明"""
        if not self.tableau:
            return False
        
        for branch in self.tableau.branches:
            if branch.closed:
                continue
            
            # 检查封闭
            if self.check_branch_closure(branch):
                continue
            
            # 展开分支
            expanded = self.expand_branch(branch)
            
            # 更新表
            self.tableau.branches = expanded
        
        # 检查所有分支是否封闭
        all_closed = all(b.closed for b in self.tableau.branches)
        
        if all_closed:
            print(f"[表算法] ✓ 证明成功：所有分支封闭")
            return True
        
        # 打印状态
        print(f"[表算法] 分支数: {len(self.tableau.branches)}")
        for i, b in enumerate(self.tableau.branches):
            if not b.closed:
                print(f"  分支 {i+1}: {len(b.formulas)} 公式")
        
        return False


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("表算法测试")
    print("=" * 50)
    
    prover = TableauProver()
    
    # 测试1: 简单重言式
    print("\n--- 测试1: p ∨ ¬p ---")
    result = prover.prove("p ∨ ¬p")
    print(f"结果: {'可证明' if result else '不可证明'}")
    
    # 测试2: 肯定前件
    print("\n--- 测试2: (p ∧ (p → q)) → q ---")
    result = prover.prove("(p ∧ (p → q)) → q")
    print(f"结果: {'可证明' if result else '不可证明'}")
    
    # 测试3: 排中律
    print("\n--- 测试3: ¬¬p → p ---")
    result = prover.prove("¬¬p → p")
    print(f"结果: {'可证明' if result else '不可证明'}")
    
    # 测试4: De Morgan律
    print("\n--- 测试4: ¬(p ∧ q) → (¬p ∨ ¬q) ---")
    result = prover.prove("¬(p ∧ q) → (¬p ∨ ¬q)")
    print(f"结果: {'可证明' if result else '不可证明'}")
    
    print("\n✓ 表算法测试完成")
