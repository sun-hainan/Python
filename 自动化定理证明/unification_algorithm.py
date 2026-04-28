"""
合一算法 (Unification Algorithm)
================================
功能：实现一阶逻辑最一般合一(MGU)算法
用于定理证明中的表达式匹配

核心概念：
1. 合一(Unification)：找到使两个表达式相同的替换
2. 最一般合一(MGU, Most General Unifier)：最通用的合一替换
3. 合一器(Unifier)：使两个表达式相等的替换集合

算法步骤：
1. 初始化：σ = {}
2. 遍历：比较表达式对的对应位置
3. 冲突检测：函数符号/常量位置冲突
4. 替换应用：递归应用替换
5. 循环直到无可变或冲突
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import copy


@dataclass
class Term:
    """
    一阶项
    - kind: "const", "var", "func"
    - name: 名称
    - args: 子项（仅func类型）
    """
    kind: str                                     # const, var, func
    name: str
    args: List['Term'] = field(default_factory=list)
    
    def __str__(self):
        if self.kind == "var":
            return self.name
        elif self.kind == "const":
            return self.name
        elif self.kind == "func":
            args_str = ", ".join(str(a) for a in self.args)
            return f"{self.name}({args_str})"
        return self.name
    
    def __hash__(self):
        return hash((self.kind, self.name, tuple(self.args)))
    
    def __eq__(self, other):
        if not isinstance(other, Term):
            return False
        return (self.kind == other.kind and 
                self.name == other.name and 
                self.args == other.args)


@dataclass
class Substitution:
    """
    替换
    - mapping: 变量→项的映射
    """
    mapping: Dict[str, Term] = field(default_factory=dict)
    
    def __str__(self):
        if not self.mapping:
            return "{}"
        pairs = [f"{v} → {t}" for v, t in self.mapping.items()]
        return "{" + ", ".join(pairs) + "}"
    
    def apply(self, term: Term) -> Term:
        """应用替换到项"""
        if term.kind == "var":
            if term.name in self.mapping:
                return self.mapping[term.name]
            return term
        elif term.kind == "func":
            new_args = [self.apply(arg) for arg in term.args]
            return Term(term.kind, term.name, new_args)
        return term
    
    def compose(self, other: 'Substitution') -> 'Substitution':
        """
        合成替换
        σ ∘ θ: 先应用θ，再应用σ
        """
        new_mapping = {}
        
        # θ 的映射应用到 σ 的域
        for var, term in self.mapping.items():
            new_mapping[var] = other.apply(term)
        
        # 添加 θ 中不在 σ 域中的映射
        for var, term in other.mapping.items():
            if var not in self.mapping:
                new_mapping[var] = term
        
        return Substitution(mapping=new_mapping)


class UnificationResult:
    """合一结果"""
    def __init__(self, success: bool, mgu: Optional[Substitution] = None, conflict: Optional[str] = None):
        self.success = success
        self.mgu = mgu
        self.conflict = conflict


class UnificationAlgorithm:
    """
    最一般合一算法实现
    
    使用标准算法：
    1. 构建差异集合(difference set)
    2. 替换直到差异集合为空
    """
    
    def __init__(self):
        self.occurs_check_enabled = True           # 启用发生检测
    
    def occurs_check(self, var: str, term: Term) -> bool:
        """
        发生检测
        检测 x 是否出现在 t 中
        用于避免 x = f(x) 这样的无限替换
        """
        if term.kind == "var":
            return term.name == var
        elif term.kind == "func":
            return any(self.occurs_check(var, arg) for arg in term.args)
        return False
    
    def get_diff_set(self, term1: Term, term2: Term) -> List[Tuple[Term, Term]]:
        """
        获取差异集合
        返回两个项中第一个不同的位置对
        """
        if term1.kind == "func" and term2.kind == "func":
            if term1.name != term2.name:
                return [(term1, term2)]
            if len(term1.args) != len(term2.args):
                return [(term1, term2)]
            
            # 递归比较参数
            for arg1, arg2 in zip(term1.args, term2.args):
                diff = self.get_diff_set(arg1, arg2)
                if diff:
                    return diff
        
        elif term1 != term2:
            return [(term1, term2)]
        
        return []
    
    def compute_mgu(self, term1: Term, term2: Term) -> UnificationResult:
        """
        计算最一般合一
        
        Args:
            term1: 第一个项
            term2: 第二个项
        
        Returns:
            UnificationResult: 成功+ MGU，或失败+冲突信息
        """
        print(f"[合一] MGU({term1}, {term2})")
        
        # 如果相同，无需替换
        if term1 == term2:
            return UnificationResult(success=True, mgu=Substitution({}))
        
        # 差异集合
        sigma = Substitution({})
        
        # 迭代直到差异集合为空
        for iteration in range(100):
            diff = self.get_diff_set(sigma.apply(term1), sigma.apply(term2))
            
            if not diff:
                print(f"[合一] ✓ 成功, MGU = {sigma}")
                return UnificationResult(success=True, mgu=sigma)
            
            # 取第一个差异对
            t1, t2 = diff[0]
            
            print(f"[合一] 差异对: ({t1}, {t2})")
            
            # Case 1: t1是变量
            if t1.kind == "var":
                if self.occurs_check_enabled and self.occurs_check(t1.name, t2):
                    print(f"[合一] ✗ 失败: 发生检测 x ∈ f(x)")
                    return UnificationResult(
                        success=False, 
                        conflict=f"Occurs check: {t1.name} in {t2}"
                    )
                
                # 构建替换 {t1 → t2}
                new_subst = Substitution({t1.name: t2})
                sigma = sigma.compose(new_subst)
                print(f"[合一] 替换: {t1.name} → {t2}")
            
            # Case 2: t2是变量
            elif t2.kind == "var":
                if self.occurs_check_enabled and self.occurs_check(t2.name, t1):
                    print(f"[合一] ✗ 失败: 发生检测 x ∈ f(x)")
                    return UnificationResult(
                        success=False, 
                        conflict=f"Occurs check: {t2.name} in {t1}"
                    )
                
                new_subst = Substitution({t2.name: t1})
                sigma = sigma.compose(new_subst)
                print(f"[合一] 替换: {t2.name} → {t1}")
            
            # Case 3: 都是函数但符号不同
            elif t1.kind == "func" and t2.kind == "func":
                if t1.name != t2.name or len(t1.args) != len(t2.args):
                    print(f"[合一] ✗ 失败: 函数符号冲突 {t1.name} vs {t2.name}")
                    return UnificationResult(
                        success=False,
                        conflict=f"Function clash: {t1.name}/{len(t1.args)} vs {t2.name}/{len(t2.args)}"
                    )
            
            # Case 4: 其他冲突
            else:
                print(f"[合一] ✗ 失败: 类型冲突")
                return UnificationResult(
                    success=False,
                    conflict=f"Type mismatch: {t1.kind} vs {t2.kind}"
                )
        
        print(f"[合一] ✗ 失败: 迭代超限")
        return UnificationResult(success=False, conflict="Iteration limit")
    
    def unify_list(self, terms1: List[Term], terms2: List[Term]) -> UnificationResult:
        """
        合一项列表
        对应位置逐一合一
        """
        if len(terms1) != len(terms2):
            return UnificationResult(success=False, conflict="Arity mismatch")
        
        sigma = Substitution({})
        
        for t1, t2 in zip(terms1, terms2):
            # 应用当前替换后合一
            result = self.compute_mgu(sigma.apply(t1), sigma.apply(t2))
            if not result.success:
                return result
            sigma = sigma.compose(result.mgu)
        
        return UnificationResult(success=True, mgu=sigma)


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("合一算法测试")
    print("=" * 50)
    
    unifier = UnificationAlgorithm()
    
    # 测试1: x = f(y)
    print("\n--- 测试1: 简单变量-函数合一 ---")
    t1 = Term("var", "x")
    t2 = Term("func", "f", [Term("var", "y")])
    result = unifier.compute_mgu(t1, t2)
    print(f"  结果: {'成功' if result.success else '失败'}")
    if result.mgu:
        print(f"  MGU: {result.mgu}")
    
    # 测试2: f(x, y) = f(a, b)
    print("\n--- 测试2: 函数项合一 ---")
    t1 = Term("func", "f", [Term("var", "x"), Term("var", "y")])
    t2 = Term("func", "f", [Term("const", "a"), Term("const", "b")])
    result = unifier.compute_mgu(t1, t2)
    print(f"  结果: {'成功' if result.success else '失败'}")
    if result.mgu:
        print(f"  MGU: {result.mgu}")
    
    # 测试3: f(x) = g(x)
    print("\n--- 测试3: 函数符号冲突 ---")
    t1 = Term("func", "f", [Term("var", "x")])
    t2 = Term("func", "g", [Term("var", "x")])
    result = unifier.compute_mgu(t1, t2)
    print(f"  结果: {'成功' if result.success else '失败'}")
    if result.conflict:
        print(f"  冲突: {result.conflict}")
    
    # 测试4: 发生检测 x = f(x)
    print("\n--- 测试4: 发生检测 ---")
    t1 = Term("var", "x")
    t2 = Term("func", "f", [Term("var", "x")])
    result = unifier.compute_mgu(t1, t2)
    print(f"  结果: {'成功' if result.success else '失败'}")
    if result.conflict:
        print(f"  冲突: {result.conflict}")
    
    # 测试5: 列表合一
    print("\n--- 测试5: 列表合一 ---")
    terms1 = [Term("var", "x"), Term("func", "f", [Term("var", "y")])]
    terms2 = [Term("const", "a"), Term("func", "f", [Term("const", "b")])]
    result = unifier.unify_list(terms1, terms2)
    print(f"  结果: {'成功' if result.success else '失败'}")
    if result.mgu:
        print(f"  MGU: {result.mgu}")
    
    print("\n✓ 合一算法测试完成")
