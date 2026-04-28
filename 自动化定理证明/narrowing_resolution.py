"""
Narrowing归结 (Narrowing Resolution)
=================================
功能：实现Narrowing技术用于函数式逻辑编程
支持带变量的项的重写与合一

核心概念：
1. Narrowing: 在重写时同时进行变量替换
2. 用于函数式逻辑语言（如Maude、Curry）
3. 支持逻辑变量和模式匹配
4. 可用于重写逻辑程序的执行和证明

与重写的区别：
- 重写: t → s (无变量替换)
- Narrowing: t → θ(s) (有变量替换θ)
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field


@dataclass
class Term:
    """一阶项（可能含逻辑变量）"""
    kind: str                                     # const, var, func
    name: str
    args: List['Term'] = field(default_factory=list)
    
    def __str__(self):
        if self.kind == "var":
            return f"?{self.name}"
        elif self.kind == "func":
            args_str = ", ".join(str(a) for a in self.args)
            return f"{self.name}({args_str})" if args_str else self.name
        return self.name
    
    def has_vars(self) -> bool:
        """检查是否含变量"""
        if self.kind == "var":
            return True
        if self.kind == "func":
            return any(a.has_vars() for a in self.args)
        return False


@dataclass
class Substitution:
    """替换"""
    mapping: Dict[str, Term] = field(default_factory=dict)
    
    def apply(self, term: Term) -> Term:
        if term.kind == "var":
            if term.name in self.mapping:
                return self.apply(self.mapping[term.name])
            return term
        if term.kind == "func":
            return Term("func", term.name, [self.apply(a) for a in term.args])
        return term
    
    def compose(self, other: 'Substitution') -> 'Substitution':
        new_map = {}
        for v, t in self.mapping.items():
            new_map[v] = other.apply(t)
        for v, t in other.mapping.items():
            if v not in new_map:
                new_map[v] = t
        return Substitution(new_map)
    
    def get_vars(self) -> Set[str]:
        """获取替换中出现的变量"""
        result = set()
        for t in self.mapping.values():
            result |= self._collect_vars(t)
        return result
    
    def _collect_vars(self, term: Term) -> Set[str]:
        if term.kind == "var":
            return {term.name}
        if term.kind == "func":
            result = set()
            for a in term.args:
                result |= self._collect_vars(a)
            return result
        return set()


@dataclass
class RewriteRule:
    """重写规则"""
    left: Term
    right: Term
    name: str = ""


class NarrowingResolver:
    """
    Narrowing归结系统
    
    结合重写与合一，用于逻辑变量的求解
    """
    
    def __init__(self):
        self.rules: List[RewriteRule] = []
        self.theta: Optional[Substitution] = None  # 当前替换
    
    def add_rule(self, rule: RewriteRule):
        """添加重写规则"""
        self.rules.append(rule)
    
    def occurs_check(self, var: str, term: Term) -> bool:
        """发生检测"""
        if term.kind == "var":
            return term.name == var
        if term.kind == "func":
            return any(self.occurs_check(var, a) for a in term.args)
        return False
    
    def unify(self, t1: Term, t2: Term) -> Optional[Substitution]:
        """
        合一算法
        
        Args:
            t1: 第一个项
            t2: 第二个项
        
        Returns:
            MGU替换或None
        """
        sigma = Substitution({})
        
        # 迭代合一
        worklist = [(t1, t2)]
        
        while worklist:
            s, t = worklist.pop()
            
            # 应用当前替换
            s = sigma.apply(s)
            t = sigma.apply(t)
            
            if s == t:
                continue
            
            if s.kind == "var":
                if self.occurs_check(s.name, t):
                    return None
                new_map = sigma.mapping.copy()
                new_map[s.name] = t
                sigma = Substitution(new_map)
            
            elif t.kind == "var":
                if self.occurs_check(t.name, s):
                    return None
                new_map = sigma.mapping.copy()
                new_map[t.name] = s
                sigma = Substitution(new_map)
            
            elif s.kind == "func" and t.kind == "func":
                if s.name != t.name or len(s.args) != len(t.args):
                    return None
                for a1, a2 in zip(s.args, t.args):
                    worklist.append((a1, a2))
            else:
                return None
        
        return sigma
    
    def find_narrowing_position(self, term: Term) -> List[Tuple[List[int], Substitution]]:
        """
        找到可以进行narrowing的位置
        
        Returns:
            [(路径, 合一替换)]
        """
        results = []
        
        for rule in self.rules:
            # 尝试将rule.left与term的子项匹配
            # 需要找到替换θ使得 term[pos] = θ(rule.left)
            
            # 顶层匹配
            sigma = self.unify(rule.left, term)
            if sigma is not None:
                results.append(([], sigma))
            
            # 递归检查子项
            if term.kind == "func":
                for i, arg in enumerate(term.args):
                    sub_results = self.find_narrowing_position(arg)
                    for path, sub in sub_results:
                        results.append(([i] + path, sub))
        
        return results
    
    def narrow_at(
        self,
        term: Term,
        position: List[int],
        rule: RewriteRule,
        sigma: Substitution
    ) -> Term:
        """
        在指定位置执行narrowing
        
        Args:
            term: 原始项
            position: 位置路径
            rule: 重写规则
            sigma: 合一替换
        
        Returns:
            Narrowing结果项
        """
        if not position:
            # 在根节点narrow
            return sigma.apply(rule.right)
        
        # 递归到子项
        idx = position[0]
        if term.kind == "func" and idx < len(term.args):
            new_arg = self.narrow_at(term.args[idx], position[1:], rule, sigma)
            new_args = list(term.args)
            new_args[idx] = new_arg
            return Term("func", term.name, new_args)
        
        return term
    
    def narrow(self, term: Term) -> List[Tuple[Term, Substitution]]:
        """
        对项执行一步narrowing
        
        Returns:
            [(结果项, 应用替换)]
        """
        results = []
        
        # 找所有narrowing位置
        narrowing_positions = self.find_narrowing_position(term)
        
        for position, sigma in narrowing_positions:
            # 找到对应的规则
            for rule in self.rules:
                # 检查是否与当前位置匹配
                test_sigma = self.unify(rule.left, self._get_subterm(term, position))
                if test_sigma is not None:
                    combined_sigma = sigma.compose(test_sigma)
                    
                    # 应用narrowing
                    new_term = self.narrow_at(term, position, rule, combined_sigma)
                    results.append((new_term, combined_sigma))
        
        return results
    
    def _get_subterm(self, term: Term, position: List[int]) -> Term:
        """获取子项"""
        if not position:
            return term
        if term.kind == "func" and position[0] < len(term.args):
            return self._get_subterm(term.args[position[0]], position[1:])
        return term
    
    def normalize_narrowing(
        self,
        term: Term,
        max_steps: int = 20
    ) -> List[Tuple[Term, List[Substitution]]]:
        """
        Narrowing归约到范式
        
        返回所有可能的归约路径和结果
        """
        print(f"[Narrowing] 归约: {term}")
        
        results = []
        self._narrow_recursive(term, [], results, max_steps)
        
        return results
    
    def _narrow_recursive(
        self,
        term: Term,
        path: List[Substitution],
        results: List[Tuple[Term, List[Substitution]]],
        max_steps: int
    ):
        """递归narrowing"""
        if len(path) >= max_steps:
            return
        
        # 找narrowing结果
        narrow_results = self.narrow(term)
        
        if not narrow_results:
            # 无法继续，记录结果
            results.append((term, path.copy()))
            return
        
        for new_term, sigma in narrow_results:
            new_path = path + [sigma]
            print(f"[Narrowing] 步骤 {len(new_path)}: {new_term}")
            
            # 检查是否已ground
            if not new_term.has_vars():
                results.append((new_term, new_path.copy()))
            else:
                # 继续narrow
                self._narrow_recursive(new_term, new_path, results, max_steps)


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("Narrowing归结测试")
    print("=" * 50)
    
    ns = NarrowingResolver()
    
    # 添加规则: append(nil, y) → y
    rule1 = RewriteRule(
        Term("func", "append", [
            Term("func", "nil", []),
            Term("var", "Y")
        ]),
        Term("var", "Y"),
        name="append-nil"
    )
    
    # 添加规则: append(cons(x, xs), y) → cons(x, append(xs, y))
    rule2 = RewriteRule(
        Term("func", "append", [
            Term("func", "cons", [Term("var", "X"), Term("var", "XS")]),
            Term("var", "Y")
        ]),
        Term("func", "cons", [
            Term("var", "X"),
            Term("func", "append", [
                Term("var", "XS"),
                Term("var", "Y")
            ])
        ]),
        name="append-cons"
    )
    
    ns.add_rule(rule1)
    ns.add_rule(rule2)
    
    print(f"规则数: {len(ns.rules)}")
    for r in ns.rules:
        print(f"  {r}")
    
    # 测试合一
    print("\n--- 合一测试 ---")
    t1 = Term("func", "append", [
        Term("func", "nil", []),
        Term("var", "Y")
    ])
    t2 = Term("func", "append", [
        Term("func", "nil", []),
        Term("func", "a", [])
    ])
    
    sigma = ns.unify(t1, t2)
    print(f"合一 {t1} = {t2}")
    print(f"结果: {sigma.mapping if sigma else '失败'}")
    
    # 测试narrowing
    print("\n--- Narrowing测试 ---")
    # append(nil, cons(a, nil)) → cons(a, nil)
    test_term = Term("func", "append", [
        Term("func", "nil", []),
        Term("func", "cons", [
            Term("func", "a", []),
            Term("func", "nil", [])
        ])
    ])
    
    results = ns.normalize_narrowing(test_term, max_steps=5)
    
    print(f"\n归约结果数: {len(results)}")
    for term, path in results:
        print(f"  {term} (路径长度={len(path)})")
    
    print("\n✓ Narrowing归结测试完成")
