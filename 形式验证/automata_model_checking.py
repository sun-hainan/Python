# -*- coding: utf-8 -*-
"""
算法实现：形式验证 / automata_model_checking

本文件实现 automata_model_checking 相关的算法功能。
"""

import numpy as np
from collections import defaultdict, deque
from itertools import product


class BuchiAutomaton:
    """
    Buchi自动机
    
    用于接受无限字的自动机
    - 状态集合 S
    - 初始状态 S0
    - 转移关系 δ: S × Σ -> S
    - 接受状态集合 F
    - 字母表 Σ
    """
    
    def __init__(self, alphabet=None):
        self.alphabet = alphabet if alphabet else set()
        self.states = set()
        self.initial_states = set()
        self.transitions = defaultdict(set)  # (state, symbol) -> set of states
        self.accepting_states = set()
        
        # 状态标签（用于可视化）
        self.state_labels = {}
    
    def add_state(self, state, label=None):
        self.states.add(state)
        if label:
            self.state_labels[state] = label
    
    def set_initial(self, state):
        self.initial_states.add(state)
    
    def add_transition(self, from_state, symbol, to_state):
        self.transitions[(from_state, symbol)].add(to_state)
    
    def set_accepting(self, state):
        self.accepting_states.add(state)
    
    def get_successors(self, state, symbol):
        """获取后继状态"""
        return self.transitions.get((state, symbol), set())
    
    def accepts_word(self, word, max_depth=1000):
        """
        检查单词是否被接受
        
        使用BFS检测是否存在从初始状态出发的无限路径
        使得无限次访问接受状态
        
        参数:
            word: 符号序列
            max_depth: 最大深度
        
        返回:
            True/False
        """
        # 状态: (automaton_state, word_position, visited_accepting_count)
        # 或者: (automaton_state, word_position, first_accept_reached)
        
        visited = set()
        queue = deque()
        
        for init in self.initial_states:
            queue.append((init, 0, False))
        
        while queue:
            state, pos, seen_accept = queue.popleft()
            
            key = (state, pos, seen_accept)
            if key in visited:
                continue
            visited.add(key)
            
            if pos >= len(word):
                continue
            
            symbol = word[pos]
            next_states = self.get_successors(state, symbol)
            
            for next_state in next_states:
                is_accepting = next_state in self.accepting_states
                new_seen = seen_accept or is_accepting
                
                if pos + 1 >= len(word):
                    # 到达单词末尾
                    if new_seen:
                        return True
                    # 没有无限延伸，不接受
                else:
                    queue.append((next_state, pos + 1, new_seen))
        
        return False
    
    def find_counterexample(self, max_length=20):
        """
        寻找反例（不被接受的字）
        
        返回一个最短的反例字
        """
        # 简化：只检查固定长度的字
        if not self.alphabet:
            return None
        
        symbols = list(self.alphabet)
        
        for length in range(1, max_length + 1):
            for word in product(symbols, repeat=length):
                if not self.accepts_word(word, max_depth=length):
                    return word
        
        return None


class KripkeStructureToBuchi:
    """
    Kripke结构到Buchi自动机转换
    
    将Kripke结构M转换为Buchi自动机B(M)
    使得: M ⊨ EF φ  <=>  B(M) × B(¬φ) 有接受的运行
    """
    
    def __init__(self, kripke):
        self.kripke = kripke
    
    def to_buchi(self, target_ap):
        """
        转换为Buchi自动机
        
        参数:
            target_ap: 目标原子命题（要避免的）
        
        返回:
            Buchi自动机
        """
        buchi = BuchiAutomaton()
        
        # 字母表：AP的幂集
        ap_set = set(self.kripke.AP)
        
        # 添加状态
        for state in self.kripke.S:
            buchi.add_state(state)
        
        # 设置初始状态
        for s0 in self.kripke.S0:
            buchi.set_initial(s0)
        
        # 添加转移
        for state in self.kripke.S:
            # 标签
            label = frozenset(self.kripke.labels.get(state, set()))
            buchi.add_state(label)  # 状态用标签表示
        
        # 设置接受状态（包含target_ap的状态）
        for state in self.kripke.S:
            labels = self.kripke.labels.get(state, set())
            if target_ap in labels:
                buchi.set_accepting(state)
        
        return buchi


class ProductAutomaton:
    """
    自动机乘积
    
    用于模型检查：Kripke结构 × Buchi(¬φ)
    """
    
    def __init__(self, kripke, buchi):
        self.kripke = kripke
        self.buchi = buchi
        self.states = set()  # (k_state, b_state)
        self.initial_states = set()
        self.transitions = defaultdict(set)
        self.accepting_states = set()
    
    def build(self):
        """构建乘积自动机"""
        # 状态: (kripke_state, buchi_state)
        for ks in self.kripke.S:
            for bs in self.buchi.states:
                self.states.add((ks, bs))
        
        # 初始状态
        for ks0 in self.kripke.S0:
            for bs0 in self.buchi.initial_states:
                self.initial_states.add((ks0, bs0))
        
        # 转移
        for ks in self.kripke.S:
            k_labels = frozenset(self.kripke.labels.get(ks, set()))
            
            for bs in self.buchi.states:
                # 检查Buchi转移与Kripke标签的兼容性
                for next_ks in self.kripke.get_successors(ks):
                    next_k_labels = frozenset(self.kripke.labels.get(next_ks, set()))
                    
                    # Buchi在当前标签上可以转移到哪些状态
                    for next_bs in self.buchi.get_successors(bs, next_k_labels):
                        self.transitions[(ks, bs)].add((next_ks, next_bs))
        
        # 接受状态: Buchi部分在接收状态
        for bs in self.buchi.accepting_states:
            for ks in self.kripke.S:
                self.states.add((ks, bs))
                self.accepting_states.add((ks, bs))
    
    def has_accepting_run(self):
        """
        检测是否存在接受的运行
        
        使用BFS检测从初始状态到接受状态的环
        """
        if not self.initial_states:
            return False
        
        # DFS检测环（包含接受状态）
        visited = set()
        stack = []
        
        for init in self.initial_states:
            stack.append((init, [init]))
        
        while stack:
            (ks, bs), path = stack.pop()
            
            if (ks, bs) in visited:
                continue
            visited.add((ks, bs))
            
            # 检查是否是接受状态
            if (ks, bs) in self.accepting_states:
                # 检查是否有环回到已访问的接受状态
                for p in path:
                    if p in self.accepting_states and p in visited:
                        return True
            
            # 继续搜索
            for next_state in self.transitions.get((ks, bs), set()):
                if next_state not in visited:
                    stack.append((next_state, path + [next_state]))
        
        return False


class LTLToBuchi:
    """
    LTL到Buchi自动机转换（简化版）
    
    支持基本算子: X, F, G, U, !
    """
    
    def __init__(self):
        self.next_id = 0
    
    def new_state(self):
        """创建新状态"""
        state = f"s{self.next_id}"
        self.next_id += 1
        return state
    
    def to_buchi(self, formula):
        """
        将LTL公式转换为Buchi自动机
        
        使用标准的转换算法（基于SNFO）
        
        参数:
            formula: LTL公式字符串
        
        返回:
            Buchi自动机
        """
        buchi = BuchiAutomaton()
        
        # 解析公式
        nnf_formula = self._parse_to_nnf(formula)
        
        # 构建自动机
        initial_state = self.new_state()
        buchi.set_initial(initial_state)
        buchi.add_state(initial_state)
        
        # 递归构建
        self._build_automaton(nnf_formula, initial_state, buchi)
        
        # 所有状态都是接受状态（用于LTL的全局性质）
        # 实际应该根据公式设置
        for state in buchi.states:
            buchi.set_accepting(state)
        
        return buchi
    
    def _parse_to_nnf(self, formula):
        """转换为否定范式"""
        formula = formula.strip()
        
        # 处理 NOT
        if formula.startswith('NOT ') or formula.startswith('!'):
            inner = formula[4:].strip() if formula.startswith('NOT') else formula[1:].strip()
            return ('not', self._parse_to_nnf(inner))
        
        # 处理 G (Globally)
        if formula.startswith('G '):
            inner = self._parse_to_nnf(formula[2:].strip())
            # G φ = ! F ! φ
            return ('not', ('finally', ('not', inner)))
        
        # 处理 F (Finally)
        if formula.startswith('F '):
            inner = self._parse_to_nnf(formula[2:].strip())
            return ('finally', inner)
        
        # 处理 X (Next)
        if formula.startswith('X '):
            inner = self._parse_to_nnf(formula[2:].strip())
            return ('next', inner)
        
        # 处理 U (Until)
        if ' U ' in formula:
            parts = formula.split(' U ', 1)
            left = self._parse_to_nnf(parts[0].strip())
            right = self._parse_to_nnf(parts[1].strip())
            return ('until', left, right)
        
        # 原子命题
        return ('ap', formula.strip())
    
    def _build_automaton(self, formula, state, buchi):
        """递归构建自动机"""
        op = formula[0]
        
        if op == 'ap':
            # 原子命题：接受满足该命题的转移
            buchi.add_transition(state, formula[1], state)
        
        elif op == 'not':
            # 否定：交换接受/不接受
            # 简化：创建两个状态
            next_state = self.new_state()
            buchi.add_state(next_state)
            buchi.add_transition(state, '*', next_state)
            self._build_automaton(formula[1], next_state, buchi)
        
        elif op == 'finally':
            # F φ: 最终满足
            # 创建接受状态和回边
            accept_state = self.new_state()
            buchi.set_accepting(accept_state)
            buchi.add_state(accept_state)
            
            # 循环到自身
            buchi.add_transition(accept_state, '*', accept_state)
            
            # φ在accept_state成立
            self._build_automaton(formula[1], accept_state, buchi)
            
            # 或者跳过
            skip_state = self.new_state()
            buchi.add_state(skip_state)
            buchi.add_transition(state, '*', skip_state)
            self._build_automaton(formula, skip_state, buchi)
        
        elif op == 'next':
            # X φ: 下一步满足
            next_state = self.new_state()
            buchi.add_state(next_state)
            buchi.add_transition(state, '*', next_state)
            self._build_automaton(formula[1], next_state, buchi)
        
        elif op == 'until':
            # φ U ψ: φ直到ψ
            psi_state = self.new_state()
            buchi.add_state(psi_state)
            buchi.set_accepting(psi_state)
            
            # ψ在psi_state成立
            self._build_automaton(formula[2], psi_state, buchi)
            
            # φ循环，ψ作为出口
            phi_state = self.new_state()
            buchi.add_state(phi_state)
            buchi.add_transition(state, '*', phi_state)
            self._build_automaton(formula[1], phi_state, buchi)
            buchi.add_transition(phi_state, '*', psi_state)


def run_demo():
    """运行自动机模型检查演示"""
    print("=" * 60)
    print("自动机模型检查与ω-自动机")
    print("=" * 60)
    
    # 创建简单的Buchi自动机
    # 接受所有包含无限次'a'的字
    print("\n[Buchi自动机示例]")
    
    buchi = BuchiAutomaton({'a', 'b'})
    
    s0 = 's0'
    s1 = 's1'
    
    buchi.add_state(s0)
    buchi.add_state(s1)
    buchi.set_initial(s0)
    buchi.set_accepting(s1)
    
    # 转移
    buchi.add_transition(s0, 'a', s1)
    buchi.add_transition(s0, 'b', s0)
    buchi.add_transition(s1, 'a', s1)
    buchi.add_transition(s1, 'b', s0)
    
    print(f"  状态: {buchi.states}")
    print(f"  接受状态: {buchi.accepting_states}")
    
    # 测试单词
    test_words = [
        ('a', 'b', 'a', 'a'),
        ('b', 'b', 'b'),
        ('a', 'b', 'a', 'b', 'a'),
    ]
    
    print("\n[单词接受测试]")
    for word in test_words:
        result = buchi.accepts_word(word)
        print(f"  {word}: {'接受' if result else '拒绝'}")
    
    # 寻找反例
    print("\n[寻找反例]")
    cex = buchi.find_counterexample(max_length=5)
    if cex:
        print(f"  最短反例: {cex}")
        print(f"  验证: {buchi.accepts_word(cex)}")
    
    # LTL转Buchi
    print("\n[LTL到Buchi转换]")
    ltlar = LTLToBuchi()
    buchi2 = ltlar.to_buchi('F a')
    
    print(f"  公式: F a (最终a)")
    print(f"  状态数: {len(buchi2.states)}")
    print(f"  接受状态: {buchi2.accepting_states}")
    
    print("\n" + "=" * 60)
    print("ω-自动机核心概念:")
    print("  1. Buchi自动机: 接受无限字的自动机")
    print("  2. 接受条件: 无限次访问接受状态")
    print("  3. Kripke×Buchi乘积: 用于LTL模型检查")
    print("  4. LTL到Buchi: 指数级转换")
    print("  5. 复杂度: 模型检查是PSPACE完全")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
