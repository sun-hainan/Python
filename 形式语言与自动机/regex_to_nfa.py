# -*- coding: utf-8 -*-
"""
算法实现：形式语言与自动机 / regex_to_nfa

本文件实现 regex_to_nfa 相关的算法功能。
"""

from typing import Dict, Set, Tuple, List, Optional
from collections import defaultdict


class NFAFragment:
    """
    NFA片段类
    
    用于Thompson构造过程中表示一个NFA片段
    """
    def __init__(self, start_state: str, accept_states: Set[str], 
                 transitions: Dict[Tuple[str, str], Set[str]]):
        self.start_state = start_state
        self.accept_states = accept_states
        self.transitions = transitions
    
    def merge_with(self, other: 'NFAFragment', 
                   connect_with_epsilon: bool = True) -> 'NFAFragment':
        """
        将两个NFA片段连接（顺序连接）
        
        参数:
            other: 另一个NFA片段
            connect_with_epsilon: 是否用ε连接
        
        返回:
            合并后的NFA片段
        """
        if connect_with_epsilon:
            # 从第一个的接受状态到第二个的起始状态添加ε转移
            for accept in self.accept_states:
                key = (accept, 'ε')
                if key in self.transitions:
                    self.transitions[key].add(other.start_state)
                else:
                    self.transitions[key] = {other.start_state}
        
        return NFAFragment(
            self.start_state,
            other.accept_states,
            self.transitions
        )


class ThompsonNFABuilder:
    """
    Thompson NFA构造器
    """
    
    def __init__(self):
        self.state_counter = 0
        self.states = set()
        self.alphabet = set()
        self.transitions = defaultdict(set)
    
    def new_state(self) -> str:
        """
        创建新状态
        
        返回:
            新状态名
        """
        state = f'q{self.state_counter}'
        self.state_counter += 1
        self.states.add(state)
        return state
    
    def build_basic(self, symbol: str) -> NFAFragment:
        """
        构建基本符号的NFA
        
        参数:
            symbol: 输入符号
        
        返回:
            NFA片段
        """
        state1 = self.new_state()
        state2 = self.new_state()
        
        self.transitions[(state1, symbol)].add(state2)
        self.alphabet.add(symbol)
        
        return NFAFragment(
            start_state=state1,
            accept_states={state2},
            transitions=dict(self.transitions)
        )
    
    def build_epsilon(self) -> NFAFragment:
        """
        构建ε转移
        
        返回:
            NFA片段
        """
        state1 = self.new_state()
        state2 = self.new_state()
        
        self.transitions[(state1, 'ε')].add(state2)
        
        return NFAFragment(
            start_state=state1,
            accept_states={state2},
            transitions=dict(self.transitions)
        )
    
    def build_union(self, nfa1: NFAFragment, nfa2: NFAFragment) -> NFAFragment:
        """
        构建并运算 (a|b)
        
        参数:
            nfa1: 第一个NFA片段
            nfa2: 第二个NFA片段
        
        返回:
            并后的NFA片段
        """
        # 创建新的起始和接受状态
        new_start = self.new_state()
        new_accept = self.new_state()
        
        # 添加ε转移
        self.transitions[(new_start, 'ε')].add(nfa1.start_state)
        self.transitions[(new_start, 'ε')].add(nfa2.start_state)
        
        # 连接两个片段的接受状态到新的接受状态
        for accept in nfa1.accept_states:
            self.transitions[(accept, 'ε')].add(new_accept)
        for accept in nfa2.accept_states:
            self.transitions[(accept, 'ε')].add(new_accept)
        
        return NFAFragment(
            start_state=new_start,
            accept_states={new_accept},
            transitions=dict(self.transitions)
        )
    
    def build_concatenation(self, nfa1: NFAFragment, nfa2: NFAFragment) -> NFAFragment:
        """
        构建连接运算 (ab)
        
        参数:
            nfa1: 第一个NFA片段
            nfa2: 第二个NFA片段
        
        返回:
            连接后的NFA片段
        """
        # 将nfa2的接受状态连接到nfa1的接受状态
        # 通过ε转移
        for accept in nfa1.accept_states:
            self.transitions[(accept, 'ε')].add(nfa2.start_state)
        
        return NFAFragment(
            start_state=nfa1.start_state,
            accept_states=nfa2.accept_states,
            transitions=dict(self.transitions)
        )
    
    def build_kleene(self, nfa: NFAFragment) -> NFAFragment:
        """
        构建Kleene闭包 (a*)
        
        参数:
            nfa: 基础NFA片段
        
        返回:
            闭包后的NFA片段
        """
        new_start = self.new_state()
        new_accept = self.new_state()
        
        # new_start -> ε -> old_accept
        for accept in nfa.accept_states:
            self.transitions[(accept, 'ε')].add(new_accept)
        
        # new_start -> ε -> new_accept (零次)
        self.transitions[(new_start, 'ε')].add(new_accept)
        
        # new_start -> ε -> old_start
        self.transitions[(new_start, 'ε')].add(nfa.start_state)
        
        # old_accept -> ε -> old_start (循环)
        for accept in nfa.accept_states:
            self.transitions[(accept, 'ε')].add(nfa.start_state)
        
        return NFAFragment(
            start_state=new_start,
            accept_states={new_accept},
            transitions=dict(self.transitions)
        )


class RegexToNFAConverter:
    """
    正则表达式到NFA转换器
    """
    
    def __init__(self):
        self.builder = ThompsonNFABuilder()
    
    def convert(self, regex: str) -> Dict:
        """
        将正则表达式转换为NFA
        
        参数:
            regex: 正则表达式字符串
        
        返回:
            包含NFA组件的字典
        """
        # 解析正则表达式
        nfa = self.parse_regex(regex)
        
        return {
            'states': self.builder.states,
            'alphabet': self.builder.alphabet,
            'transitions': dict(self.builder.transitions),
            'start_state': nfa.start_state,
            'accept_states': nfa.accept_states
        }
    
    def parse_regex(self, regex: str) -> NFAFragment:
        """
        解析正则表达式（递归下降）
        
        参数:
            regex: 正则表达式字符串
        
        返回:
            NFA片段
        """
        # 移除空格
        regex = regex.replace(' ', '')
        
        return self.parse_union(regex)
    
    def parse_union(self, regex: str) -> NFAFragment:
        """
        解析并运算
        
        参数:
            regex: 正则表达式字符串
        
        返回:
            NFA片段
        """
        # 找到最外层的 |
        depth = 0
        for i, c in enumerate(regex):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            elif c == '|' and depth == 0:
                # 分割
                left = self.parse_concatenation(regex[:i])
                right = self.parse_union(regex[i+1:])
                return self.builder.build_union(left, right)
        
        return self.parse_concatenation(regex)
    
    def parse_concatenation(self, regex: str) -> NFAFragment:
        """
        解析连接运算
        
        参数:
            regex: 正则表达式字符串
        
        返回:
            NFA片段
        """
        # 分割连续的基础表达式
        fragments = []
        i = 0
        
        while i < len(regex):
            c = regex[i]
            
            if c == '(':
                # 找对应的右括号
                depth = 1
                j = i + 1
                while j < len(regex) and depth > 0:
                    if regex[j] == '(':
                        depth += 1
                    elif regex[j] == ')':
                        depth -= 1
                    j += 1
                fragment = self.parse_union(regex[i+1:j-1])
                fragments.append(fragment)
                i = j
            elif c == '*':
                # Kleene闭包应用到前一个片段
                if fragments:
                    fragments[-1] = self.builder.build_kleene(fragments[-1])
                i += 1
            elif c == '|':
                # 在parse_union中处理
                fragments.append(self.parse_union(regex[i:]))
                break
            else:
                # 基本符号
                fragment = self.builder.build_basic(c)
                fragments.append(fragment)
                i += 1
        
        # 连接所有片段
        if not fragments:
            # 空表达式
            return self.builder.build_epsilon()
        
        result = fragments[0]
        for fragment in fragments[1:]:
            result = self.builder.build_concatenation(result, fragment)
        
        return result


def regex_to_nfa(regex: str) -> Dict:
    """
    将正则表达式转换为NFA的便捷函数
    
    参数:
        regex: 正则表达式字符串
    
    返回:
        NFA定义字典
    """
    converter = RegexToNFAConverter()
    return converter.convert(regex)


def print_nfa(nfa_dict: Dict):
    """
    打印NFA定义
    
    参数:
        nfa_dict: NFA定义字典
    """
    print("NFA定义:")
    print(f"  状态: {sorted(nfa_dict['states'])}")
    print(f"  字母表: {sorted(nfa_dict['alphabet'])}")
    print(f"  起始状态: {nfa_dict['start_state']}")
    print(f"  接受状态: {sorted(nfa_dict['accept_states'])}")
    print("  转移函数:")
    for (state, symbol), targets in sorted(nfa_dict['transitions'].items()):
        print(f"    δ({state}, {symbol}) = {sorted(targets)}")


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本符号
    print("=" * 50)
    print("测试1: 基本符号 'a'")
    print("=" * 50)
    
    nfa = regex_to_nfa('a')
    print_nfa(nfa)
    
    # 测试用例2：并运算
    print("\n" + "=" * 50)
    print("测试2: 并运算 'a|b'")
    print("=" * 50)
    
    nfa = regex_to_nfa('a|b')
    print_nfa(nfa)
    
    # 测试用例3：连接运算
    print("\n" + "=" * 50)
    print("测试3: 连接运算 'ab'")
    print("=" * 50)
    
    nfa = regex_to_nfa('ab')
    print_nfa(nfa)
    
    # 测试用例4：Kleene闭包
    print("\n" + "=" * 50)
    print("测试4: Kleene闭包 'a*'")
    print("=" * 50)
    
    nfa = regex_to_nfa('a*')
    print_nfa(nfa)
    
    # 测试用例5：复杂表达式
    print("\n" + "=" * 50)
    print("测试5: 复杂表达式 '(a|b)*abb'")
    print("=" * 50)
    
    nfa = regex_to_nfa('(a|b)*abb')
    print_nfa(nfa)
    print(f"\n状态数: {len(nfa['states'])}")
    
    # 测试用例6：更多复杂表达式
    print("\n" + "=" * 50)
    print("测试6: 更多复杂表达式")
    print("=" * 50)
    
    expressions = [
        'a*b*',
        '(a*)(b*)',
        '((a|b)*)((a|b)*)',
        'a*|b*',
    ]
    
    for expr in expressions:
        nfa = regex_to_nfa(expr)
        print(f"\n表达式: '{expr}'")
        print(f"  状态数: {len(nfa['states'])}")
        print(f"  转移数: {len(nfa['transitions'])}")
    
    # 测试用例7：验证表达式等价性
    print("\n" + "=" * 50)
    print("测试7: 验证Thompson构造正确性")
    print("=" * 50)
    
    # 简单测试：a|ε 应该等于 a?
    nfa1 = regex_to_nfa('a')
    nfa2 = regex_to_nfa('a|ε')
    
    print("表达式 'a' 和 'a|ε' 的NFA状态数:")
    print(f"  'a': {len(nfa1['states'])}")
    print(f"  'a|ε': {len(nfa2['states'])}")
    
    # 测试：a* vs aa*
    nfa1 = regex_to_nfa('aa*')
    nfa2 = regex_to_nfa('a*')
    
    print("\n表达式 'aa*' vs 'a*' 的NFA状态数:")
    print(f"  'aa*': {len(nfa1['states'])}")
    print(f"  'a*': {len(nfa2['states'])}")
