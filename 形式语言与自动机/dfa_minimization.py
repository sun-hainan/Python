# -*- coding: utf-8 -*-

"""

算法实现：形式语言与自动机 / dfa_minimization



本文件实现 dfa_minimization 相关的算法功能。

"""



from typing import Dict, Set, List, FrozenSet

from collections import defaultdict, deque





def hopcroft_minimize(states: Set[str], alphabet: Set[str],

                      transitions: Dict[tuple, str],

                      start: str, accept: Set[str]) -> Dict:

    """

    Hopcroft DFA最小化



    返回：最小化的DFA

    """

    # 初始分割：P = {F, Q-F}

    non_accept = states - accept

    P = [frozenset(non_accept), frozenset(accept)] if non_accept else [frozenset(accept)]

    P = [s for s in P if s]  # 移除空集



    # 工作队列

    W = deque(P.copy())



    # 逆转移表：for each (a, state), who transitions to state?

    inv = defaultdict(set)

    for (s, a), t in transitions.items():

        inv[(a, t)].add(s)



    while W:

        A = W.popleft()



        for c in alphabet:

            # 找到所有在某个转移下进入A的状态

            R = set()

            for (symbol, state), pre_states in inv.items():

                if symbol == c and state in A:

                    R.update(pre_states)



            # 分割包含R的集合

            new_P = []

            for G in P:

                # G ∩ R 和 G - R

                intersection = G & R

                diff = G - R

                if intersection and diff:

                    new_P.append(intersection)

                    new_P.append(diff)

                    # 将G替换为两个小块

                    P.remove(G)

                    if G in W:

                        W.remove(G)

                        W.append(intersection)

                        W.append(diff)

                    else:

                        # 选择较小的加入W

                        if len(intersection) <= len(diff):

                            W.append(intersection)

                        else:

                            W.append(diff)

                else:

                    new_P.append(G)



            P = new_P



    # 构建最小化的DFA

    state_to_class = {}

    for S in P:

        for s in S:

            state_to_class[s] = S



    # 转移表

    new_transitions = {}

    for (s, a), t in transitions.items():

        new_s = state_to_class[s]

        new_t = state_to_class[t]

        new_transitions[(new_s, a)] = new_t



    # 新状态集

    new_states = set(P)

    new_start = state_to_class[start]

    new_accept = {S for S in P if S & accept}



    return {

        'states': new_states,

        'alphabet': alphabet,

        'transitions': new_transitions,

        'start': new_start,

        'accept': new_accept

    }





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== DFA最小化测试 ===\n")



    # 简单DFA：接受以a结尾的字符串

    states = {'0', '1', '2', '3'}

    alphabet = {'a', 'b'}

    transitions = {

        ('0', 'a'): '1',

        ('0', 'b'): '2',

        ('1', 'a'): '3',

        ('1', 'b'): '2',

        ('2', 'a'): '1',

        ('2', 'b'): '2',

        ('3', 'a'): '3',

        ('3', 'b'): '2',

    }

    start = '0'

    accept = {'1', '3'}



    print(f"原始DFA状态数: {len(states)}")



    # 最小化

    result = hopcroft_minimize(states, alphabet, transitions, start, accept)



    print(f"最小化后状态数: {len(result['states'])}")

    print(f"合并了 {len(states) - len(result['states'])} 个等价状态")



    print("\n说明：")

    print("  - Hopcroft算法是O(n log n)的最小化算法")

    print("  - 最小DFA唯一（同构意义下）")

    print("  - 用于正则表达式到最简DFA的转换")

