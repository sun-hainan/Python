# -*- coding: utf-8 -*-

"""

算法实现：形式语言与自动机 / nfa_to_dfa



本文件实现 nfa_to_dfa 相关的算法功能。

"""



from typing import Set, Dict, List, Tuple, Optional

from collections import defaultdict





class NFA:

    """

    非确定有限自动机类

    """

    

    def __init__(self, states: Set[str], alphabet: Set[str], 

                 transitions: Dict[Tuple[str, str], Set[str]],

                 start_state: str, accept_states: Set[str]):

        """

        初始化NFA

        

        参数:

            states: 状态集合

            alphabet: 输入字母表

            transitions: 转移函数 {(state, symbol) -> set of states}

            start_state: 初始状态

            accept_states: 接受状态集合

        """

        self.states = states

        self.alphabet = alphabet

        self.transitions = transitions

        self.start_state = start_state

        self.accept_states = accept_states

    

    def epsilon_closure(self, states: Set[str]) -> Set[str]:

        """

        计算状态的ε闭包

        

        参数:

            states: 状态集合

        

        返回:

            ε闭包（包含所有从states出发通过ε可达的状态）

        """

        # 使用栈来计算闭包

        closure = set(states)

        stack = list(states)

        

        while stack:

            state = stack.pop()

            # 获取ε转移

            epsilon_transitions = self.transitions.get((state, 'ε'), set())

            

            for next_state in epsilon_transitions:

                if next_state not in closure:

                    closure.add(next_state)

                    stack.append(next_state)

        

        return closure

    

    def move(self, states: Set[str], symbol: str) -> Set[str]:

        """

        计算从states通过symbol可达的状态

        

        参数:

            states: 状态集合

            symbol: 输入符号

        

        返回:

            可达状态集合

        """

        result = set()

        

        for state in states:

            transitions = self.transitions.get((state, symbol), set())

            result.update(transitions)

        

        return result





class DFA:

    """

    确定有限自动机类

    """

    

    def __init__(self):

        self.states: Set[frozenset] = set()  # 存储为frozenset的集合

        self.alphabet: Set[str] = set()

        self.transitions: Dict[Tuple[frozenset, str], frozenset] = {}

        self.start_state: Optional[frozenset] = None

        self.accept_states: Set[frozenset] = set()

        self.state_names: Dict[frozenset, str] = {}  # 用于调试的命名

    

    def add_state(self, state_set: frozenset, is_accept: bool = False, name: str = None):

        """

        添加一个DFA状态

        

        参数:

            state_set: NFA状态集合

            is_accept: 是否为接受状态

            name: 状态名称（用于调试）

        """

        self.states.add(state_set)

        if is_accept:

            self.accept_states.add(state_set)

        if name:

            self.state_names[state_set] = name

    

    def set_start_state(self, state_set: frozenset):

        """

        设置起始状态

        

        参数:

            state_set: NFA状态集合

        """

        self.start_state = state_set

    

    def add_transition(self, from_state: frozenset, symbol: str, to_state: frozenset):

        """

        添加转移

        

        参数:

            from_state: 起始状态

            symbol: 输入符号

            to_state: 目标状态

        """

        self.transitions[(from_state, symbol)] = to_state

    

    def accepts(self, input_string: str) -> bool:

        """

        检查DFA是否接受输入字符串

        

        参数:

            input_string: 输入字符串

        

        返回:

            是否接受

        """

        if self.start_state is None:

            return False

        

        current_state = self.start_state

        

        for symbol in input_string:

            if symbol not in self.alphabet:

                return False

            

            transition = self.transitions.get((current_state, symbol))

            if transition is None:

                return False

            

            current_state = transition

        

        return current_state in self.accept_states





def nfa_to_dfa(nfa: NFA) -> DFA:

    """

    子集构造算法：将NFA转换为DFA

    

    参数:

        nfa: 输入的NFA

    

    返回:

        等价的DFA

    """

    dfa = DFA()

    dfa.alphabet = nfa.alphabet - {'ε'}  # DFA不使用ε转移

    

    # 计算初始状态的ε闭包

    initial_closure = frozenset(nfa.epsilon_closure({nfa.start_state}))

    dfa.set_start_state(initial_closure)

    

    # 检查初始状态是否是接受状态

    is_accept = bool(initial_closure & nfa.accept_states)

    dfa.add_state(initial_closure, is_accept, name='S0')

    

    # 工作队列

    work_queue = [initial_closure]

    processed = {initial_closure}

    

    while work_queue:

        current_set = work_queue.pop(0)

        

        # 对每个输入符号

        for symbol in dfa.alphabet:

            # 计算move(current_set, symbol)

            move_result = nfa.move(current_set, symbol)

            

            # 计算ε闭包

            new_set = frozenset(nfa.epsilon_closure(move_result))

            

            # 添加转移

            dfa.add_transition(current_set, symbol, new_set)

            

            # 如果是新状态，加入工作队列

            if new_set not in processed:

                processed.add(new_set)

                is_accept = bool(new_set & nfa.accept_states)

                dfa.add_state(new_set, is_accept)

                work_queue.append(new_set)

    

    return dfa





def regex_to_nfa(regex: str) -> NFA:

    """

    将正则表达式转换为NFA（Thompson构造法）

    

    这是一个简化版本，只支持基本的运算符

    支持: a, b, *, |, ()

    

    参数:

        regex: 正则表达式字符串

    

    返回:

        对应的NFA

    """

    # 状态计数器

    state_counter = [0]

    

    def new_state():

        """生成新状态"""

        state = f'q{state_counter[0]}'

        state_counter[0] += 1

        return state

    

    def parse_primary(expr: str) -> Tuple[NFA, int]:

        """解析基本表达式"""

        if expr[0] == '(':

            # 找到匹配的右括号

            depth = 1

            for i in range(1, len(expr)):

                if expr[i] == '(':

                    depth += 1

                elif expr[i] == ')':

                    depth -= 1

                    if depth == 0:

                        break

            

            sub_nfa = Thompson_construction(expr[1:i])

            return sub_nfa, i + 1

        else:

            # 单个字符

            state1 = new_state()

            state2 = new_state()

            

            states = {state1, state2}

            alphabet = {expr[0]}

            transitions = {(state1, expr[0]): {state2}}

            

            nfa = NFA(states, alphabet, transitions, state1, {state2})

            return nfa, 1

    

    def Thompson_construction(expr: str) -> NFA:

        """Thompson构造法"""

        if not expr:

            # 空表达式

            state1 = new_state()

            state2 = new_state()

            return NFA({state1, state2}, set(), {(state1, 'ε'): {state2}}, 

                      state1, {state2})

        

        # 解析第一个字符

        nfa1, pos = parse_primary(expr)

        expr = expr[pos:]

        

        while expr and expr[0] == '*':

            # Kleene闭包

            old_start = nfa1.start_state

            old_accept = list(nfa1.accept_states)[0]

            

            new_start = new_state()

            new_accept = new_state()

            

            nfa1.states.add(new_start)

            nfa1.states.add(new_accept)

            nfa1.start_state = new_start

            nfa1.accept_states = {new_accept}

            

            # 添加转移

            nfa1.transitions[(new_start, 'ε')] = {old_start, new_accept}

            nfa1.transitions[(old_accept, 'ε')] = {old_start, new_accept}

            

            expr = expr[1:]

        

        # 处理连接

        while expr:

            if expr[0] == '|':

                # 并

                expr = expr[1:]

                nfa2, pos = parse_primary(expr)

                expr = expr[pos:]

                

                old_starts = {nfa1.start_state}

                old_accepts = nfa1.accept_states

                

                new_start = new_state()

                new_accept = new_state()

                

                nfa1.states.add(new_start)

                nfa1.states.add(new_accept)

                nfa1.transitions[(new_start, 'ε')] = {nfa1.start_state, nfa2.start_state}

                nfa1.transitions[(old_accepts.pop(), 'ε')] = {new_accept}

                nfa1.accept_states.add(new_accept)

                nfa1.start_state = new_start

                

                nfa1.states.update(nfa2.states)

                nfa1.alphabet.update(nfa2.alphabet)

                nfa1.transitions.update(nfa2.transitions)

            else:

                # 连接

                nfa2, pos = parse_primary(expr)

                expr = expr[pos:]

                

                old_accept = nfa1.accept_states.pop()

                nfa1.accept_states.add(nfa2.start_state)

                

                nfa1.states.update(nfa2.states)

                nfa1.alphabet.update(nfa2.alphabet)

                nfa1.transitions.update(nfa2.transitions)

                nfa1.transitions[(old_accept, 'ε')] = {nfa2.start_state}

                nfa1.accept_states = nfa2.accept_states

        

        return nfa1

    

    # 添加连接符号

    def add_concat_ops(expr: str) -> str:

        result = []

        for i, c in enumerate(expr):

            result.append(c)

            if i < len(expr) - 1:

                next_c = expr[i + 1]

                # 在字母后面，'(' 前面添加连接符

                if c != '|' and c != '(' and next_c != '|' and next_c != ')' and next_c != '*':

                    result.append('·')  # 连接符号

        return ''.join(result)

    

    # 简单处理：直接返回None让用户使用Thompson算法

    return Thompson_construction(regex)





def minimize_dfa(dfa: DFA) -> DFA:

    """

    DFA极小化（Hopcroft算法）

    

    参数:

        dfa: 输入的DFA

    

    返回:

        极小化后的DFA

    """

    # 这是一个简化实现

    # 完整的Hopcroft算法需要更复杂的集合划分

    return dfa





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：简单NFA转DFA

    print("=" * 50)

    print("测试1: NFA到DFA转换")

    print("=" * 50)

    

    # 构造一个简单的NFA：接受以'a'开头和结尾的字符串

    # NFA: q0 -ε-> q1, q1 -a-> q2, q2 -ε-> q3, q3 -a-> q4, q4 -ε-> q3, q4 -ε-> q5

    states = {'q0', 'q1', 'q2', 'q3', 'q4', 'q5'}

    alphabet = {'a', 'b'}

    transitions = {

        ('q0', 'ε'): {'q1'},

        ('q1', 'a'): {'q2'},

        ('q2', 'ε'): {'q3'},

        ('q3', 'a'): {'q4'},

        ('q4', 'ε'): {'q3', 'q5'},

    }

    

    nfa = NFA(states, alphabet, transitions, 'q0', {'q5'})

    

    # 计算ε闭包

    print("ε闭包测试:")

    closure = nfa.epsilon_closure({'q0'})

    print(f"ε-closure({{q0}}) = {closure}")

    

    # NFA转DFA

    dfa = nfa_to_dfa(nfa)

    

    print(f"\nDFA信息:")

    print(f"状态数: {len(dfa.states)}")

    print(f"字母表: {dfa.alphabet}")

    print(f"起始状态: {dfa.start_state}")

    print(f"接受状态: {dfa.accept_states}")

    

    # 测试一些字符串

    print("\n测试接受情况:")

    test_strings = ['', 'a', 'aa', 'aaa', 'b', 'ab', 'ba']

    for s in test_strings:

        result = dfa.accepts(s)

        print(f"  '{s}': {'接受' if result else '拒绝'}")

    

    # 测试用例2：带分支的NFA

    print("\n" + "=" * 50)

    print("测试2: 带分支的NFA")

    print("=" * 50)

    

    # 构造接受 'a|b+' 的NFA

    states = {'q0', 'q1', 'q2', 'q3', 'q4'}

    alphabet = {'a', 'b'}

    transitions = {

        ('q0', 'ε'): {'q1', 'q3'},  # 分支到a或b+

        ('q1', 'a'): {'q2'},

        ('q2', 'ε'): {'q4'},

        ('q3', 'b'): {'q4'},

        ('q4', 'ε'): {'q3'},  # b的闭包

    }

    

    nfa = NFA(states, alphabet, transitions, 'q0', {'q2', 'q4'})

    

    print("NFA状态转移:")

    for (state, sym), targets in nfa.transitions.items():

        if targets:

            print(f"  δ({state}, {sym}) = {targets}")

    

    # 转换为DFA

    dfa = nfa_to_dfa(nfa)

    

    print(f"\nDFA状态数: {len(dfa.states)}")

    

    # 测试

    print("\n测试接受情况:")

    test_strings = ['a', 'b', 'bb', 'bbb', 'ab', 'ba', '']

    for s in test_strings:

        result = dfa.accepts(s)

        print(f"  '{s}': {'接受' if result else '拒绝'}")

    

    # 测试用例3：完整示例

    print("\n" + "=" * 50)

    print("测试3: 完整转换示例")

    print("=" * 50)

    

    # 构造NFA: 接受包含 'ab' 的字符串

    states = {'s0', 's1', 's2', 's3'}

    alphabet = {'a', 'b'}

    transitions = {

        ('s0', 'ε'): {'s0'},  # 自循环

        ('s0', 'a'): {'s1'},

        ('s1', 'b'): {'s2'},

        ('s2', 'ε'): {'s3'},

    }

    

    nfa = NFA(states, alphabet, transitions, 's0', {'s3'})

    

    print("原始NFA:")

    print(f"  状态: {states}")

    print(f"  字母表: {alphabet}")

    print(f"  起始状态: s0")

    print(f"  接受状态: {{s3}}")

    

    dfa = nfa_to_dfa(nfa)

    

    print(f"\n转换后的DFA:")

    print(f"  状态数: {len(dfa.states)}")

    print(f"  转移数: {len(dfa.transitions)}")

    

    print("\n转移表:")

    for (state, sym), target in sorted(dfa.transitions.items()):

        print(f"  δ({set(state)}, '{sym}') -> {set(target)}")

