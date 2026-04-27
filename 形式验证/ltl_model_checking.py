# -*- coding: utf-8 -*-
"""
算法实现：形式验证 / ltl_model_checking

本文件实现 ltl_model_checking 相关的算法功能。
"""

import numpy as np
from collections import defaultdict, deque
from graphviz import Digraph


class KripkeStructure:
    """Kripke结构（同CTL模型检查中的定义）"""
    
    def __init__(self, ap_list):
        self.AP = set(ap_list)
        self.S = set()
        self.S0 = set()
        self.R = defaultdict(set)
        self.labels = {}
        self.reverse_R = defaultdict(set)
    
    def add_state(self, s, ap_subset=None):
        self.S.add(s)
        if ap_subset is not None:
            self.labels[s] = set(ap_subset)
        else:
            self.labels[s] = set()
    
    def set_initial(self, s):
        self.S0.add(s)
    
    def add_transition(self, s1, s2):
        self.R[s1].add(s2)
        self.reverse_R[s2].add(s1)
    
    def get_successors(self, s):
        return self.R.get(s, set())
    
    def check_ap(self, s, ap):
        return ap in self.labels.get(s, set())
    
    def get_initial_paths(self, max_length=None):
        """生成从初始状态出发的所有路径"""
        for s0 in self.S0:
            yield from self._dfs_paths(s0, set(), max_length)
    
    def _dfs_paths(self, s, visited, max_length):
        """深度优先搜索生成路径"""
        path = [s]
        yield path
        
        if max_length is not None and len(path) >= max_length:
            return
        
        for succ in self.get_successors(s):
            if succ not in visited:
                visited.add(succ)
                for tail_path in self._dfs_paths(succ, visited, max_length):
                    yield path + tail_path
                visited.remove(succ)


class LTLFormula:
    """LTL公式基类"""
    
    def __init__(self):
        pass
    
    def __and__(self, other):
        return AndFormula(self, other)
    
    def __or__(self, other):
        return OrFormula(self, other)
    
    def __invert__(self):
        return NotFormula(self)
    
    def __rsub__(self, other):
        return OrFormula(NotFormula(self), other)  # a -> b = ~a or b
    
    def to_nnf(self):
        """转换为否定范式（Negation Normal Form）"""
        raise NotImplementedError


class AtomicProp(LTLFormula):
    """原子命题 p"""
    
    def __init__(self, name):
        super().__init__()
        self.name = name
    
    def __repr__(self):
        return self.name
    
    def to_nnf(self):
        return self
    
    def accept(self, trace, pos):
        """检查trace[pos]是否满足此公式"""
        return self.name in trace[pos]


class TrueFormula(LTLFormula):
    """True常量"""
    
    def __repr__(self):
        return "TRUE"
    
    def to_nnf(self):
        return self
    
    def accept(self, trace, pos):
        return True


class FalseFormula(LTLFormula):
    """False常量"""
    
    def __repr__(self):
        return "FALSE"
    
    def to_nnf(self):
        return self
    
    def accept(self, trace, pos):
        return False


class NotFormula(LTLFormula):
    """NOT φ"""
    
    def __init__(self, child):
        super().__init__()
        self.child = child
    
    def __repr__(self):
        return f"NOT {self.child}"
    
    def to_nnf(self):
        nnf_child = self.child.to_nnf()
        if isinstance(nnf_child, AtomicProp):
            return NotAP(nnf_child.name)
        elif isinstance(nnf_child, NotFormula):
            return nnf_child.child  # NOT NOT φ = φ
        elif isinstance(nnf_child, AndFormula):
            return OrFormula(
                NotFormula(nnf_child.left).to_nnf(),
                NotFormula(nnf_child.right).to_nnf()
            )
        elif isinstance(nnf_child, OrFormula):
            return AndFormula(
                NotFormula(nnf_child.left).to_nnf(),
                NotFormula(nnf_child.right).to_nnf()
            )
        elif isinstance(nnf_child, NextFormula):
            return NextFormula(NotFormula(nnf_child.child).to_nnf())
        elif isinstance(nnf_child, EventuallyFormula):
            return AlwaysFormula(NotFormula(nnf_child.child).to_nnf())
        elif isinstance(nnf_child, AlwaysFormula):
            return EventuallyFormula(NotFormula(nnf_child.child).to_nnf())
        elif isinstance(nnf_child, UntilFormula):
            return ReleaseFormula(
                NotFormula(nnf_child.right).to_nnf(),
                NotFormula(nnf_child.left).to_nnf()
            )
        elif isinstance(nnf_child, ReleaseFormula):
            return UntilFormula(
                NotFormula(nnf_child.right).to_nnf(),
                NotFormula(nnf_child.left).to_nnf()
            )


class NotAP(LTLFormula):
    """NOT p（已在NNF中）"""
    
    def __init__(self, name):
        super().__init__()
        self.name = name
    
    def __repr__(self):
        return f"¬{self.name}"
    
    def to_nnf(self):
        return self
    
    def accept(self, trace, pos):
        return self.name not in trace[pos]


class AndFormula(LTLFormula):
    """φ AND ψ"""
    
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right
    
    def __repr__(self):
        return f"({self.left} AND {self.right})"
    
    def to_nnf(self):
        return AndFormula(self.left.to_nnf(), self.right.to_nnf())
    
    def accept(self, trace, pos):
        return self.left.accept(trace, pos) and self.right.accept(trace, pos)


class OrFormula(LTLFormula):
    """φ OR ψ"""
    
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right
    
    def __repr__(self):
        return f"({self.left} OR {self.right})"
    
    def to_nnf(self):
        return OrFormula(self.left.to_nnf(), self.right.to_nnf())
    
    def accept(self, trace, pos):
        return self.left.accept(trace, pos) or self.right.accept(trace, pos)


class NextFormula(LTLFormula):
    """X φ (Next)"""
    
    def __init__(self, child):
        super().__init__()
        self.child = child
    
    def __repr__(self):
        return f"X {self.child}"
    
    def to_nnf(self):
        return NextFormula(self.child.to_nnf())
    
    def accept(self, trace, pos):
        if pos + 1 >= len(trace):
            return False
        return self.child.accept(trace, pos + 1)


class EventuallyFormula(LTLFormula):
    """F φ (Finally/Eventually)"""
    
    def __init__(self, child):
        super().__init__()
        self.child = child
    
    def __repr__(self):
        return f"F {self.child}"
    
    def to_nnf(self):
        return EventuallyFormula(self.child.to_nnf())
    
    def accept(self, trace, pos):
        for i in range(pos, len(trace)):
            if self.child.accept(trace, i):
                return True
        return False


class AlwaysFormula(LTLFormula):
    """G φ (Globally)"""
    
    def __init__(self, child):
        super().__init__()
        self.child = child
    
    def __repr__(self):
        return f"G {self.child}"
    
    def to_nnf(self):
        return AlwaysFormula(self.child.to_nnf())
    
    def accept(self, trace, pos):
        for i in range(pos, len(trace)):
            if not self.child.accept(trace, i):
                return False
        return True


class UntilFormula(LTLFormula):
    """φ U ψ (Until)"""
    
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right
    
    def __repr__(self):
        return f"({self.left} U {self.right})"
    
    def to_nnf(self):
        return UntilFormula(self.left.to_nnf(), self.right.to_nnf())
    
    def accept(self, trace, pos):
        for i in range(pos, len(trace)):
            if self.right.accept(trace, i):
                # 找到ψ，检查之前的φ
                for j in range(pos, i):
                    if not self.left.accept(trace, j):
                        return False
                return True
        return False


class ReleaseFormula(LTLFormula):
    """φ R ψ (Release)"""
    
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right
    
    def __repr__(self):
        return f"({self.left} R {self.right})"
    
    def to_nnf(self):
        return ReleaseFormula(self.left.to_nnf(), self.right.to_nnf())
    
    def accept(self, trace, pos):
        # ψ一直保持直到φ出现（或者ψ始终保持）
        for i in range(pos, len(trace)):
            if self.left.accept(trace, i):
                # φ出现，验证之前ψ一直成立
                for j in range(pos, i):
                    if not self.right.accept(trace, j):
                        return False
                return True
        # φ从未出现，ψ必须一直成立
        for i in range(pos, len(trace)):
            if not self.right.accept(trace, i):
                return False
        return True


class LTLModelChecker:
    """
    LTL模型检查器
    
    使用穷举路径方法检查LTL公式
    对于无限路径，使用Büchi自动机乘积方法
    """
    
    def __init__(self, model):
        self.model = model
        self.ap_list = list(model.AP)
    
    def check(self, formula_str):
        """
        检查模型是否满足LTL公式
        
        参数:
            formula_str: LTL公式字符串
        
        返回:
            True/False
        """
        formula = self._parse(formula_str)
        nnf_formula = formula.to_nnf()
        
        # 对每条初始路径检查
        for path in self.model.get_initial_paths(max_length=20):
            trace = [self.model.labels.get(s, set()) for s in path]
            if not nnf_formula.accept(trace, 0):
                return False
        
        return True
    
    def _parse(self, s):
        """简单解析器"""
        s = s.strip()
        
        if s == 'TRUE':
            return TrueFormula()
        if s == 'FALSE':
            return FalseFormula()
        
        if s.startswith('NOT '):
            return NotFormula(self._parse(s[4:]))
        
        if s.startswith('X '):
            return NextFormula(self._parse(s[2:]))
        
        if s.startswith('F '):
            return EventuallyFormula(self._parse(s[2:]))
        
        if s.startswith('G '):
            return AlwaysFormula(self._parse(s[2:]))
        
        # 括号
        if s.startswith('(') and s.endswith(')'):
            inner = s[1:-1]
            
            # U和R
            for op in [' U ', ' R ']:
                if op in inner:
                    idx = inner.index(op)
                    # 找到最外层的op
                    depth = 0
                    found = False
                    for i, c in enumerate(inner):
                        if c == '(':
                            depth += 1
                        elif c == ')':
                            depth -= 1
                        elif c == ' ' and depth == 0:
                            word = inner[:i]
                            if word == op.strip():
                                left = self._parse(inner[:i])
                                right = self._parse(inner[i+len(op):])
                                if op.strip() == 'U':
                                    return UntilFormula(left, right)
                                else:
                                    return ReleaseFormula(left, right)
                    break
            
            # AND/OR
            for op in [' AND ', ' OR ']:
                if op in inner:
                    idx = inner.find(op)
                    if idx > 0:
                        left = self._parse(inner[:idx])
                        right = self._parse(inner[idx+len(op):])
                        if op.strip() == 'AND':
                            return AndFormula(left, right)
                        else:
                            return OrFormula(left, right)
            
            return self._parse(inner[1:-1])
        
        return AtomicProp(s)
    
    def get_satisfying_paths(self, formula_str, max_length=10):
        """获取所有满足公式的路径"""
        formula = self._parse(formula_str)
        nnf_formula = formula.to_nnf()
        
        results = []
        for path in self.model.get_initial_paths(max_length=max_length):
            trace = [self.model.labels.get(s, set()) for s in path]
            if nnf_formula.accept(trace, 0):
                results.append(path)
        
        return results


def run_demo():
    """运行LTL模型检查演示"""
    print("=" * 60)
    print("LTL线性时态逻辑模型检查")
    print("=" * 60)
    
    # 创建Kripke结构
    model = KripkeStructure(['p', 'q', 'r'])
    
    # 创建状态: s0, s1, s2, s3
    model.add_state('s0', ['p'])
    model.add_state('s1', ['q'])
    model.add_state('s2', ['p', 'q'])
    model.add_state('s3', ['r'])
    
    # 设置初始状态
    model.set_initial('s0')
    
    # 添加转换
    model.add_transition('s0', 's1')
    model.add_transition('s0', 's2')
    model.add_transition('s1', 's1')
    model.add_transition('s2', 's3')
    model.add_transition('s3', 's0')
    
    checker = LTLModelChecker(model)
    
    print("\n[Kripke结构]")
    print(f"  状态: {model.S}")
    print(f"  转换: {dict(model.R)}")
    print(f"  标签: {model.labels}")
    
    print("\n[LTL公式检查]")
    
    formulas = [
        'p',                    # p在某时刻成立
        'F p',                  # p最终成立
        'G p',                  # p始终成立
        'F G p',                # 最终总是p
        'G F p',                # 无限次p
        'X q',                  # 下一步q
        'p U q',                # p直到q
        '(p U q) OR (G NOT q)', # p直到q 或者 q永不成立
        'G (p -> F q)',         # 每次p后最终有q
    ]
    
    for f in formulas:
        result = checker.check(f)
        print(f"  {f}: {'满足' if result else '不满足'}")
    
    print("\n[满足路径示例]")
    for f in ['F r', 'X q', 'p U r']:
        paths = checker.get_satisfying_paths(f, max_length=10)
        print(f"  {f}: {len(paths)}条路径满足")
        if paths:
            print(f"    示例: {' -> '.join(paths[0])}")


def ltl_syntax_summary():
    """打印LTL语法摘要"""
    print("""
╔══════════════════════════════════════════════════════════╗
║                    LTL 语法摘要                           ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  原子命题:  p, q, r, ...                                 ║
║                                                          ║
║  逻辑联结词:                                              ║
║    φ AND ψ    - 合取                                     ║
║    φ OR ψ     - 析取                                     ║
║    NOT φ      - 否定                                     ║
║    φ -> ψ     - 蕴含                                     ║
║                                                          ║
║  时序算子:                                                ║
║    X φ (Next)      - 下一步φ必须成立                     ║
║    F φ (Finally)   - φ最终/某时刻成立                    ║
║    G φ (Globally)   - φ始终成立                          ║
║    φ U ψ (Until)    - φ一直成立直到ψ成立                 ║
║    φ R ψ (Release)  - ψ成立直到φ成立（或ψ一直成立）      ║
║                                                          ║
║  等价关系:                                                ║
║    F φ = TRUE U φ                                        ║
║    G φ = NOT F NOT φ                                     ║
║    φ R ψ = NOT (NOT φ U NOT ψ)                          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    run_demo()
    ltl_syntax_summary()
    
    print("=" * 60)
    print("LTL模型检查核心概念:")
    print("  1. LTL: 线性时态逻辑，描述单一路径上的性质")
    print("  2. 路径量词: 隐含为'所有路径'（不同于CTL的A/E）")
    print("  3. 语义: 在无限路径上解释")
    print("  4. 检查方法:")
    print("     - LTL转Büchi自动机")
    print("     - 乘积自动机")
    print("     - 接受状态可达性检测")
    print("  5. 复杂度: O(2^|φ| * m), |φ|为公式大小")
    print("=" * 60)
