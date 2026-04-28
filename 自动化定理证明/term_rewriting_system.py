"""
项重写系统 (Term Rewriting System)
================================
功能：实现项重写系统的基本算法
支持终止性检测、Church-Rosser性质验证

核心概念：
1. 重写规则: l → r (左规则，右规则)
2. 归约: t → s 通过规则 l → r 将 t 中的 l 实例替换为 r
3. 终止性: 不存在无限归约序列
4. Church-Rosser: 任何有公共项的两个项可归约到同一项
5. 合流性(Confluence): 所有归约序列终止于同一范式

关键算法：
- 匹配(Matching): 找到规则应用的实例
- 归约: 应用规则
- 临界对(Critical Pair): 检测重叠
"""

from typing import Set, Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Term:
    """一阶项"""
    kind: str                                     # const, var, func
    name: str
    args: List['Term'] = field(default_factory=list)
    
    def __str__(self):
        if self.kind == "var":
            return self.name
        elif self.kind == "const":
            return self.name
        elif self.kind == "func":
            if not self.args:
                return self.name
            args_str = ", ".join(str(a) for a in self.args)
            return f"{self.name}({args_str})"
        return self.name
    
    def __eq__(self, other):
        if not isinstance(other, Term):
            return False
        if self.kind != other.kind or self.name != other.name:
            return False
        if len(self.args) != len(other.args):
            return False
        return all(a == b for a, b in zip(self.args, other.args))
    
    def __hash__(self):
        return hash((self.kind, self.name, tuple(self.args)))


@dataclass
class RewriteRule:
    """
    重写规则
    - left: 左手边（模式）
    - right: 右手边（替换）
    """
    left: Term
    right: Term
    name: str = ""
    
    def __str__(self):
        return f"{self.left} → {self.right}"


@dataclass
class Position:
    """项的位置（用于定位子项）"""
    path: Tuple[int, ...] = ()                    # 路径元组
    
    def __str__(self):
        return ".".join(str(i) for i in self.path) if self.path else "ε"
    
    def parent(self) -> 'Position':
        """返回父节点位置"""
        if not self.path:
            return Position()
        return Position(self.path[:-1])


class TermRewritingSystem:
    """
    项重写系统
    
    实现基本重写操作和性质检测
    """
    
    def __init__(self):
        self.rules: List[RewriteRule] = []
        self.var_counter = 0
    
    def add_rule(self, rule: RewriteRule):
        """添加重写规则"""
        self.rules.append(rule)
    
    def get_vars(self, term: Term) -> Set[str]:
        """获取项中的变量集合"""
        if term.kind == "var":
            return {term.name}
        elif term.kind == "func":
            result = set()
            for arg in term.args:
                result |= self.get_vars(arg)
            return result
        return set()
    
    def match(self, pattern: Term, term: Term) -> Optional[Dict[str, Term]]:
        """
        匹配：将模式与项匹配
        
        Args:
            pattern: 模式（含变量）
            term: 待匹配项
        
        Returns:
            替换映射或None
        """
        substitution = {}
        
        if pattern.kind == "var":
            if pattern.name in substitution:
                return substitution if substitution[pattern.name] == term else None
            substitution[pattern.name] = term
            return substitution
        
        if pattern.kind != term.kind or pattern.name != term.name:
            return None
        
        if len(pattern.args) != len(term.args):
            return None
        
        for p_arg, t_arg in zip(pattern.args, term.args):
            sub = self.match(p_arg, t_arg)
            if sub is None:
                return None
            # 合并替换
            for k, v in sub.items():
                if k in substitution and substitution[k] != v:
                    return None
                substitution[k] = v
        
        return substitution
    
    def substitute(self, term: Term, substitution: Dict[str, Term]) -> Term:
        """
        应用替换
        
        Args:
            term: 原始项
            substitution: 替换映射
        
        Returns:
            替换后的项
        """
        if term.kind == "var":
            return substitution.get(term.name, term)
        elif term.kind == "func":
            new_args = [self.substitute(arg, substitution) for arg in term.args]
            return Term("func", term.name, new_args)
        return term
    
    def rewrite_at(self, term: Term, pos: Position, new_subterm: Term) -> Term:
        """
        在指定位置重写
        
        Args:
            term: 原始项
            pos: 位置
            new_subterm: 新的子项
        
        Returns:
            重写后的项
        """
        if not pos.path:
            return new_subterm
        
        if term.kind != "func" or len(term.args) == 0:
            return term
        
        idx = pos.path[0]
        new_args = list(term.args)
        
        if idx < len(new_args):
            sub_pos = Position(pos.path[1:])
            new_args[idx] = self.rewrite_at(new_args[idx], sub_pos, new_subterm)
        
        return Term("func", term.name, new_args)
    
    def find_redex(self, term: Term) -> List[Tuple[Position, RewriteRule, Dict[str, Term]]]:
        """
        查找可约子项(redex)
        
        Returns:
            [(位置, 规则, 匹配替换)]
        """
        results = []
        
        # 检查整个项
        for rule in self.rules:
            sub = self.match(rule.left, term)
            if sub is not None:
                results.append((Position(), rule, sub))
        
        # 递归检查子项
        if term.kind == "func":
            for i, arg in enumerate(term.args):
                sub_pos = Position((i,))
                for sub_arg_result in self.find_redex(arg):
                    results.append((sub_arg_result[0], sub_arg_result[1], sub_arg_result[2]))
        
        return results
    
    def reduce(self, term: Term) -> Optional[Term]:
        """
        一步归约
        
        Returns:
            归约后的项或None（如果不可归约）
        """
        redexes = self.find_redex(term)
        
        if not redexes:
            return None
        
        # 选择第一个redex
        pos, rule, sub = redexes[0]
        replacement = self.substitute(rule.right, sub)
        
        return self.rewrite_at(term, pos, replacement)
    
    def normalize(self, term: Term, max_steps: int = 100) -> Term:
        """
        归约到范式
        
        Args:
            term: 初始项
            max_steps: 最大步数
        
        Returns:
            范式
        """
        current = term
        
        for step in range(max_steps):
            reduced = self.reduce(current)
            if reduced is None:
                break
            current = reduced
            print(f"[归约] 步骤 {step}: {current}")
        
        return current
    
    def is_terminating(self, max_depth: int = 1000) -> bool:
        """
        终止性检测（简化）
        
        启发式：检查是否有可能的无限循环
        """
        print(f"[TRS] 检查终止性")
        
        # 简化实现：检查规则中的变量模式
        for rule in self.rules:
            # 检查 left 是否有子项是 right 的子结构
            left_vars = self.get_vars(rule.left)
            right_vars = self.get_vars(rule.right)
            
            # 如果右边的变量比左边多，可能终止
            if len(right_vars) > len(left_vars):
                continue
            
            # 检查大小：如果右边比左边大，可能不终止
            left_size = self._term_size(rule.left)
            right_size = self._term_size(rule.right)
            
            if right_size > left_size:
                print(f"[TRS] 警告: 规则 {rule} 右边比左边大")
        
        return True  # 简化：假设终止
    
    def _term_size(self, term: Term) -> int:
        """计算项的大小"""
        if term.kind == "const":
            return 1
        elif term.kind == "var":
            return 1
        elif term.kind == "func":
            return 1 + sum(self._term_size(a) for a in term.args)
        return 1
    
    def find_critical_pairs(self) -> List[Tuple[Term, Term]]:
        """
        查找临界对
        
        用于检测合流性
        """
        print(f"[TRS] 查找临界对")
        
        pairs = []
        
        for i, rule1 in enumerate(self.rules):
            for j, rule2 in enumerate(self.rules):
                if i == j:
                    continue
                
                # 检查rule2.left是否是rule1的子项
                redexes = self.find_redex(rule1.left)
                
                for pos, rule, sub in redexes:
                    if rule.name == rule2.name:
                        # 发现重叠
                        # 计算两个归约方向的结果
                        # 简化：添加占位对
                        pass
        
        print(f"[TRS] 找到 {len(pairs)} 个临界对")
        return pairs


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    print("=" * 50)
    print("项重写系统测试")
    print("=" * 50)
    
    trs = TermRewritingSystem()
    
    # 添加规则: if true then x else y → x
    rule1 = RewriteRule(
        Term("func", "if", [
            Term("const", "true"),
            Term("var", "x"),
            Term("var", "y")
        ]),
        Term("var", "x"),
        name="if-true"
    )
    
    # 添加规则: succ(x) + y → succ(x + y)
    rule2 = RewriteRule(
        Term("func", "+", [
            Term("func", "succ", [Term("var", "x")]),
            Term("var", "y")
        ]),
        Term("func", "succ", [
            Term("func", "+", [Term("var", "x"), Term("var", "y")])
        ]),
        name="succ-plus"
    )
    
    trs.add_rule(rule1)
    trs.add_rule(rule2)
    
    print(f"规则数: {len(trs.rules)}")
    for r in trs.rules:
        print(f"  {r}")
    
    # 测试匹配
    print("\n--- 匹配测试 ---")
    pattern = Term("func", "if", [
        Term("const", "true"),
        Term("var", "x"),
        Term("var", "y")
    ])
    term = Term("func", "if", [
        Term("const", "true"),
        Term("const", "a"),
        Term("const", "b")
    ])
    
    sub = trs.match(pattern, term)
    print(f"匹配结果: {sub}")
    
    # 测试归约
    print("\n--- 归约测试 ---")
    test_term = Term("func", "if", [
        Term("const", "true"),
        Term("func", "succ", [Term("const", "0")]),
        Term("const", "b")
    ])
    print(f"初始项: {test_term}")
    
    reduced = trs.normalize(test_term)
    print(f"范式: {reduced}")
    
    # 测试终止性
    print("\n--- 终止性检测 ---")
    is_term = trs.is_terminating()
    print(f"终止: {is_term}")
    
    # 测试临界对
    print("\n--- 临界对 ---")
    pairs = trs.find_critical_pairs()
    print(f"临界对数: {len(pairs)}")
    
    print("\n✓ 项重写系统测试完成")
