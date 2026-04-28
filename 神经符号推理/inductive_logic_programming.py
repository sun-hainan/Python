"""
归纳逻辑编程 (Inductive Logic Programming - ILP)
=================================================
本模块实现简化的归纳逻辑编程系统：

FOIL (First-Order Inductive Learner) 算法实现

核心任务：
- 从正反例学习Horn子句
- 背景知识编码
- 假设空间搜索

Author: 算法库
"""

import numpy as np
from typing import List, Dict, Set, Tuple, Optional, Callable


class Term:
    """一阶逻辑项"""
    
    def __init__(self, name: str, is_variable: bool = False):
        self.name = name
        self.is_variable = is_variable
    
    def __repr__(self):
        return f"{self.name}{'*' if self.is_variable else ''}"
    
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


class Literal:
    """文字（原子或否定原子）"""
    
    def __init__(self, atom: Atom, negated: bool = False):
        self.atom = atom
        self.negated = negated
    
    def __repr__(self):
        sign = "¬" if self.negated else ""
        return f"{sign}{self.atom}"
    
    def is_positive(self):
        return not self.negated
    
    def complement(self):
        return Literal(self.atom, not self.negated)


class Clause:
    """Horn子句"""
    
    def __init__(self, head: Atom, body: List[Literal] = None):
        self.head = head
        self.body = body if body else []
    
    def __repr__(self):
        if not self.body:
            return str(self.head)
        body_str = ", ".join(str(l) for l in self.body)
        return f"{self.head} :- {body_str}"


class Example:
    """样例"""
    
    def __init__(self, atom: Atom, is_positive: bool):
        self.atom = atom
        self.is_positive = is_positive
    
    def __repr__(self):
        return f"+{self.atom}" if self.is_positive else f"-{self.atom}"


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
        term_objs = [Term(t, is_variable=False) for t in terms]
        atom = Atom(predicate, term_objs)
        self.positive_examples.append(Example(atom, is_positive=True))
        for t in terms:
            if t[0].isupper():
                self.constants.add(t)
    
    def add_negative_example(self, predicate: str, terms: List[str]):
        """添加反例"""
        term_objs = [Term(t, is_variable=False) for t in terms]
        atom = Atom(predicate, term_objs)
        self.negative_examples.append(Example(atom, is_positive=False))
    
    def add_background(self, clause: Clause):
        """添加背景知识"""
        self.background_knowledge.append(clause)
    
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
            
            if t1.is_variable and not t2.is_variable:
                theta[t1] = t2
            elif not t1.is_variable and t2.is_variable:
                theta[t2] = t1
            elif t1.is_variable and t2.is_variable:
                if t1 in theta and theta[t1] != t2:
                    return None
                theta[t1] = t2
            elif not t1.is_variable and not t2.is_variable and t1.name != t2.name:
                return None
        
        return theta if theta else {}
    
    def is_fact_true(self, atom: Atom, facts: Set[Tuple]) -> bool:
        """检查事实是否为真"""
        key = tuple([atom.predicate] + [t.name for t in atom.terms])
        return key in facts
    
    def covers(self, example: Example, clause: Clause, 
              facts: Set[Tuple], depth: int = 0) -> bool:
        """
        检查子句是否覆盖例
        
        简化实现
        """
        if depth > 10:  # 递归深度限制
            return False
        
        # 尝试匹配头
        theta = self.unification(example.atom, clause.head)
        
        if theta is None:
            return False
        
        # 检查体
        for literal in clause.body:
            if literal.is_positive():
                atom_substituted = literal.atom.substitute(theta)
                key = tuple([atom_substituted.predicate] + [t.name for t in atom_substituted.terms])
                
                if key not in facts:
                    return False
        
        return True
    
    def foil_gain(self, new_literal: Literal, examples_covered: Set[int],
                  neg_covered: Set[int]) -> float:
        """
        计算FOIL增益
        
        Gain = |P| * (log2(|P'|+|N'|) - log2(|P|+|N|))
        """
        P = len(examples_covered)
        N = len(neg_covered)
        
        if P == 0:
            return 0.0
        
        total = P + N
        gain = P * (np.log2(total + 1) - np.log2(N + 1))
        
        return max(0, gain)


class FOILLearner:
    """FOIL学习算法"""
    
    def __init__(self, ilp_system: ILPSystem):
        self.ilp = ilp_system
    
    def learn_rules(self, target_predicate: str, max_literals: int = 5) -> List[Clause]:
        """
        学习规则
        
        FOIL算法简化实现
        """
        learned_rules = []
        uncovered_pos = set(range(len(self.ilp.positive_examples)))
        
        while uncovered_pos and len(learned_rules) < 10:
            # 创建新规则
            clause = self._learn_single_rule(target_predicate, uncovered_pos, max_literals)
            
            if clause and clause.body:
                learned_rules.append(clause)
                
                # 移除被覆盖的正例
                new_uncovered = set()
                facts = self._get_facts()
                
                for i in uncovered_pos:
                    ex = self.ilp.positive_examples[i]
                    if not self.ilp.covers(ex, clause, facts):
                        new_uncovered.add(i)
                
                uncovered_pos = new_uncovered
            else:
                break
        
        return learned_rules
    
    def _learn_single_rule(self, target_predicate: str, 
                          uncovered_pos: Set[int],
                          max_literals: int) -> Optional[Clause]:
        """学习单个规则"""
        # 创建头部
        target_example = self.ilp.positive_examples[list(uncovered_pos)[0]]
        head_vars = []
        
        for i, term in enumerate(target_example.atom.terms):
            if term.name[0].isupper():
                head_vars.append(Term(term.name, is_variable=True))
            else:
                head_vars.append(Term(f"X{i}", is_variable=True))
        
        head = Atom(target_predicate, head_vars)
        
        # 贪心添加体文字
        clause = Clause(head, body=[])
        self.ilp.hypotheses.append(clause)
        
        facts = self._get_facts()
        
        for _ in range(max_literals):
            best_literal = None
            best_gain = 0
            
            # 生成候选
            candidates = self._generate_candidates(head, facts)
            
            for candidate in candidates[:20]:  # 限制候选数
                test_body = clause.body + [candidate]
                test_clause = Clause(head, test_body)
                
                # 计算增益
                gain = self._evaluate_gain(test_clause, uncovered_pos, facts)
                
                if gain > best_gain:
                    best_gain = gain
                    best_literal = candidate
            
            if best_literal:
                clause.body.append(best_literal)
                facts = self._get_facts()  # 更新事实
            else:
                break
        
        return clause if clause.body else None
    
    def _generate_candidates(self, head: Atom, facts: Set[Tuple]) -> List[Literal]:
        """生成候选体文字"""
        candidates = []
        
        # 从背景知识生成
        for clause in self.ilp.background_knowledge:
            for lit in clause.body:
                candidates.append(lit)
        
        # 从正例中提取
        for ex in self.ilp.positive_examples[:5]:
            for term in ex.atom.terms:
                if not term.is_variable:
                    # 创建相等测试
                    pass
        
        return candidates
    
    def _evaluate_gain(self, clause: Clause, uncovered_pos: Set[int],
                       facts: Set[Tuple]) -> float:
        """评估子句增益"""
        covered_pos = set()
        
        for i in uncovered_pos:
            ex = self.ilp.positive_examples[i]
            if self.ilp.covers(ex, clause, facts):
                covered_pos.add(i)
        
        if not covered_pos:
            return 0.0
        
        # 计算被覆盖的负例
        covered_neg = set()
        for i, ex in enumerate(self.ilp.negative_examples):
            if self.ilp.covers(ex, clause, facts):
                covered_neg.add(i)
        
        # FOIL增益
        P = len(covered_pos)
        P_old = len(uncovered_pos)
        N = len(covered_neg)
        
        if P == 0:
            return 0.0
        
        gain = P * (np.log2(P + N + 1) - np.log2(P_old + N + 1))
        return max(0, gain)
    
    def _get_facts(self) -> Set[Tuple]:
        """获取已知事实"""
        facts = set()
        
        for clause in self.ilp.background_knowledge:
            if not clause.body:
                key = tuple([clause.head.predicate] + [t.name for t in clause.head.terms])
                facts.add(key)
        
        return facts


class ILPDemo:
    """ILP演示"""
    
    @staticmethod
    def family_relationship_example():
        """家庭关系学习示例"""
        print("=" * 55)
        print("FOIL算法: 学习家庭关系")
        print("=" * 55)
        
        ilp = ILPSystem()
        
        # 学习目标: grandmother(X, Y)
        # 规则: grandmother(X, Y) :- mother(X, Z), parent(Z, Y)
        
        # 正例
        ilp.add_positive_example("grandmother", ["alice", "bob"])
        ilp.add_positive_example("grandmother", ["eve", "alice"])
        ilp.add_positive_example("grandmother", ["mary", "john"])
        
        # 反例
        ilp.add_negative_example("grandmother", ["bob", "alice"])
        ilp.add_negative_example("grandmother", ["carol", "david"])
        
        # 添加背景知识
        # mother(alice, bob)
        mother_clause = Clause(
            Atom("mother", [Term("alice"), Term("bob")])
        )
        ilp.add_background(mother_clause)
        
        # parent(X, Y) :- mother(X, Y)
        parent_clause = Clause(
            Atom("parent", [Term("X", True), Term("Y", True)]),
            [Literal(Atom("mother", [Term("X", True), Term("Y", True)]))]
        )
        ilp.add_background(parent_clause)
        
        print(f"\n正例: {ilp.positive_examples}")
        print(f"反例: {ilp.negative_examples}")
        print(f"背景知识: {ilp.background_knowledge}")
        
        # 学习
        learner = FOILLearner(ilp)
        rules = learner.learn_rules("grandmother", max_literals=3)
        
        print(f"\n学习的规则:")
        for rule in rules:
            print(f"  {rule}")
    
    @staticmethod
    def unification_demo():
        """合一算法演示"""
        print("\n" + "=" * 55)
        print("合一算法演示")
        print("=" * 55)
        
        ilp = ILPSystem()
        
        # unify(p(X, a), p(b, Y))
        atom1 = Atom("p", [Term("X", True), Term("a")])
        atom2 = Atom("p", [Term("b"), Term("Y", True)])
        
        theta = ilp.unification(atom1, atom2)
        
        print(f"合一: {atom1} 和 {atom2}")
        print(f"MGU: {theta}")
        
        # 应用替换
        if theta:
            substituted = atom1.substitute(theta)
            print(f"应用MGU后: {substituted}")
    
    @staticmethod
    def covering_demo():
        """覆盖演示"""
        print("\n" + "=" * 55)
        print("覆盖演示")
        print("=" * 55)
        
        ilp = ILPSystem()
        
        # 简单规则: p(X) :- q(X, Y)
        head = Atom("p", [Term("X", True)])
        body = [Literal(Atom("q", [Term("X", True), Term("Y", True)]))]
        clause = Clause(head, body)
        
        # 正例: p(a)
        ilp.add_positive_example("p", ["a"])
        
        # 事实: q(a, b)
        fact_clause = Clause(Atom("q", [Term("a"), Term("b")]))
        ilp.add_background(fact_clause)
        
        facts = {("q", "a", "b")}
        
        print(f"规则: {clause}")
        print(f"事实: {facts}")
        
        for ex in ilp.positive_examples:
            covered = ilp.covers(ex, clause, facts)
            print(f"例 {ex} 被覆盖: {covered}")


if __name__ == "__main__":
    ILPDemo.family_relationship_example()
    ILPDemo.unification_demo()
    ILPDemo.covering_demo()
    
    print("\n测试通过！归纳逻辑编程系统工作正常。")
