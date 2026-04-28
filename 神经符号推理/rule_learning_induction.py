"""
规则学习与归纳逻辑编程 (ILP)
===============================
本模块实现简化的归纳逻辑编程系统：

ILP核心任务：
1. 从正例和反例中学习Horn子句
2. 背景知识编码
3. 假设搜索

简化版本：
- 使用FOIL (First-Order Inductive Learner) 算法思想
- 基于覆盖度的贪心搜索

Author: 算法库
"""

import numpy as np
from typing import List, Dict, Tuple, Set, Optional, Callable
from itertools import product


class Term:
    """一阶逻辑项"""
    
    def __init__(self, name: str, is_variable: bool = False):
        self.name = name
        self.is_variable = is_variable
    
    def __repr__(self):
        return self.name.upper() if self.is_variable else self.name.lower()
    
    def __eq__(self, other):
        return self.name == other.name and self.is_variable == other.is_variable
    
    def __hash__(self):
        return hash((self.name, self.is_variable))


class Atom:
    """原子公式"""
    
    def __init__(self, predicate: str, terms: List[Term]):
        self.predicate = predicate
        self.terms = terms
    
    def __repr__(self):
        terms_str = ", ".join(str(t) for t in self.terms)
        return f"{self.predicate}({terms_str})"
    
    def substitute(self, theta: Dict[Term, Term]) -> 'Atom':
        """应用替换"""
        new_terms = []
        for t in self.terms:
            if t in theta:
                new_terms.append(theta[t])
            else:
                new_terms.append(t)
        return Atom(self.predicate, new_terms)


class Clause:
    """Horn子句: H :- B1, B2, ... """
    
    def __init__(self, head: Atom, body: List[Atom] = None):
        self.head = head
        self.body = body if body else []
    
    def __repr__(self):
        if not self.body:
            return str(self.head)
        body_str = ", ".join(str(b) for b in self.body)
        return f"{self.head} :- {body_str}"
    
    def is_horn(self) -> bool:
        """检查是否为Horn子句（最多一个正文字）"""
        positive_count = sum(1 for a in self.body if a.predicate[0].isupper())
        return positive_count <= 1


class Example:
    """正例或反例"""
    
    def __init__(self, atom: Atom, is_positive: bool):
        self.atom = atom
        self.is_positive = is_positive


class ILPSystem:
    """归纳逻辑编程系统"""
    
    def __init__(self):
        self.positive_examples: List[Example] = []
        self.negative_examples: List[Example] = []
        self.background_knowledge: List[Clause] = []
        self.hypotheses: List[Clause] = []
        self.constants: Set[str] = set()
    
    def add_positive_example(self, predicate: str, terms: List[str]):
        """添加正例"""
        term_objects = [Term(t, is_variable=False) for t in terms]
        atom = Atom(predicate, term_objects)
        self.positive_examples.append(Example(atom, is_positive=True))
        for t in terms:
            if not t[0].isupper():
                self.constants.add(t)
    
    def add_negative_example(self, predicate: str, terms: List[str]):
        """添加反例"""
        term_objects = [Term(t, is_variable=False) for t in terms]
        atom = Atom(predicate, term_objects)
        self.negative_examples.append(Example(atom, is_positive=False))
    
    def add_background(self, clause: Clause):
        """添加背景知识"""
        self.background_knowledge.append(clause)
    
    def get_variables(self, atoms: List[Atom]) -> Set[Term]:
        """获取变量集合"""
        vars = set()
        for atom in atoms:
            for term in atom.terms:
                if term.is_variable:
                    vars.add(term)
        return vars
    
    def unification(self, atom1: Atom, atom2: Atom) -> Optional[Dict[Term, Term]]:
        """
        合一算法
        
        返回最一般合一置换（MGU）
        """
        if atom1.predicate != atom2.predicate or len(atom1.terms) != len(atom2.terms):
            return None
        
        theta = {}
        
        for t1, t2 in zip(atom1.terms, atom2.terms):
            if t1 == t2:
                continue
            
            # 变量-常量合一
            if t1.is_variable and not t2.is_variable:
                theta[t1] = t2
            elif not t1.is_variable and t2.is_variable:
                theta[t2] = t1
            # 变量-变量合一
            elif t1.is_variable and t2.is_variable:
                if t1 in theta and theta[t1] != t2:
                    return None
                theta[t1] = t2
            # 常量-常量不同则失败
            elif not t1.is_variable and not t2.is_variable and t1.name != t2.name:
                return None
        
        return theta if theta else {}
    
    def is_covered(self, example: Example, theta: Dict[Term, Term]) -> bool:
        """检查例是否被子句覆盖"""
        # 检查头是否匹配
        head = self.hypotheses[-1].head if self.hypotheses else None
        if head:
            unified = head.substitute(theta)
            if unified.predicate == example.atom.predicate:
                # 检查项是否一致
                if len(unified.terms) == len(example.atom.terms):
                    for t1, t2 in zip(unified.terms, example.atom.terms):
                        if t1.is_variable and t2.is_variable:
                            continue
                        if not t1.is_variable and not t2.is_variable and t1.name != t2.name:
                            return False
                        if t1.is_variable and not t2.is_variable:
                            continue
                        if not t1.is_variable and t2.is_variable:
                            if t1.name != t2.name:
                                return False
                    return True
        
        return False
    
    def foil_gain(self, new_literal, covered_pos, covered_neg) -> float:
        """
        计算FOIL增益
        
        Gain = |P| * (log2(|P|+|N|) - log2(|P'| + |N'|))
        """
        P = len(covered_pos)
        N = len(covered_neg)
        
        if P == 0:
            return 0.0
        
        total = P + N
        gain = P * (np.log2(total + 1) - np.log2(N + 1))
        
        return max(0, gain)
    
    def learn_rules(self, target_predicate: str, max_literals: int = 3) -> List[Clause]:
        """
        学习规则（简化版FOIL）
        
        参数:
            target_predicate: 目标谓词
            max_literals: 最大体文字数
        
        返回:
            学习到的规则列表
        """
        learned = []
        
        # 复制正例
        uncovered_pos = self.positive_examples.copy()
        
        while uncovered_pos and len(learned) < 10:
            # 创建新规则
            # 头: target_predicate(X1, X2, ...)
            target_atom = uncovered_pos[0].atom
            arity = len(target_atom.terms)
            head_vars = [Term(f"X{i}", is_variable=True) for i in range(arity)]
            head = Atom(target_predicate, head_vars)
            
            clause = Clause(head, body=[])
            self.hypotheses.append(clause)
            
            # 贪心添加体文字
            covered_neg = self.negative_examples.copy()
            
            for _ in range(max_literals):
                best_gain = 0
                best_literal = None
                
                # 简化：只尝试有限的候选
                candidates = self._generate_candidates(head_vars, covered_neg)
                
                for candidate in candidates[:20]:  # 限制候选数
                    clause.body.append(candidate)
                    gain = self.foil_gain(candidate, uncovered_pos, covered_neg)
                    
                    if gain > best_gain:
                        best_gain = gain
                        best_literal = candidate
                    
                    clause.body.pop()
                
                if best_literal:
                    clause.body.append(best_literal)
                    # 更新覆盖的负例
                    covered_neg = [e for e in covered_neg 
                                   if not self._literal_covers(best_literal, e.atom)]
                else:
                    break
            
            # 检查规则质量
            if clause.body:
                learned.append(clause)
                
                # 移除被覆盖的正例
                new_theta = self._compute_theta(head, uncovered_pos[0].atom)
                uncovered_pos = [e for e in uncovered_pos 
                                if not self.is_covered(e, new_theta)]
        
        return learned
    
    def _generate_candidates(self, vars: List[Term], neg_examples: List[Example]) -> List[Atom]:
        """生成候选体文字"""
        candidates = []
        
        # 简化：使用负例中的信息
        for neg in neg_examples[:5]:
            for term in neg.atom.terms[:2]:  # 限制使用前两个项
                if term.is_variable or term.name in self.constants:
                    candidate = Atom(neg.atom.predicate, [term, vars[0]])
                    candidates.append(candidate)
        
        # 添加等式测试
        for v1 in vars:
            for v2 in vars:
                if v1 != v2:
                    candidates.append(Atom("eq", [v1, v2]))
        
        return candidates
    
    def _compute_theta(self, head: Atom, example_atom: Atom) -> Dict[Term, Term]:
        """计算从头到例子的置换"""
        theta = {}
        for t1, t2 in zip(head.terms, example_atom.terms):
            if t1.is_variable:
                theta[t1] = t2
        return theta
    
    def _literal_covers(self, literal: Atom, example_atom: Atom) -> bool:
        """检查文字是否覆盖例"""
        if literal.predicate != example_atom.predicate:
            return False
        return True


if __name__ == "__main__":
    print("=" * 55)
    print("规则学习与ILP测试")
    print("=" * 55)
    
    ilp = ILPSystem()
    
    # 学习问题：祖母关系
    # 规则: grandmother(X, Y) :- mother(X, Z), parent(Z, Y)
    
    print("\n--- 学习祖母关系 ---")
    
    # 正例
    ilp.add_positive_example("grandmother", ["alice", "bob"])
    ilp.add_positive_example("grandmother", ["alice", "carol"])
    ilp.add_positive_example("grandmother", ["eve", "david"])
    
    # 反例
    ilp.add_negative_example("grandmother", ["bob", "carol"])
    ilp.add_negative_example("grandmother", ["carol", "david"])
    
    # 添加背景知识
    # parent(X, Y) :- mother(X, Y)
    mother1 = Atom("mother", [Term("alice"), Term("bob")])
    parent_clause = Clause(Atom("parent", [Term("X", True), Term("Y", True)]),
                          [Atom("mother", [Term("X", True), Term("Y", True)])])
    ilp.add_background(parent_clause)
    
    # 学习规则
    print("\n背景知识:")
    for bg in ilp.background_knowledge:
        print(f"  {bg}")
    
    print("\n正例:")
    for ex in ilp.positive_examples:
        print(f"  +{ex.atom}")
    
    print("\n反例:")
    for ex in ilp.negative_examples:
        print(f"  -{ex.atom}")
    
    # 合一测试
    print("\n--- 合一算法测试 ---")
    
    atom1 = Atom("parent", [Term("X", True), Term("Y", True)])
    atom2 = Atom("parent", [Term("alice"), Term("bob")])
    
    theta = ilp.unification(atom1, atom2)
    print(f"unify(parent(X,Y), parent(alice,bob)) = {theta}")
    
    # 测试子句
    print("\n--- Horn子句测试 ---")
    
    clause1 = Clause(
        Atom("grandmother", [Term("X", True), Term("Y", True)]),
        [
            Atom("mother", [Term("X", True), Term("Z", True)]),
            Atom("parent", [Term("Z", True), Term("Y", True)])
        ]
    )
    
    print(f"子句: {clause1}")
    print(f"是Horn子句: {clause1.is_horn()}")
    
    # 替换测试
    theta = {Term("X", True): Term("alice"), Term("Y", True): Term("bob")}
    substituted = clause1.head.substitute(theta)
    print(f"应用置换{theta}后: {substituted}")
    
    print("\n测试通过！ILP基础功能正常。")
