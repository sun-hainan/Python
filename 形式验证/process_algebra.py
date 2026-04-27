# -*- coding: utf-8 -*-

"""

算法实现：形式验证 / process_algebra



本文件实现 process_algebra 相关的算法功能。

"""



import numpy as np

from collections import defaultdict





class CCSProcess:

    """

    CCS进程

    

    语法：

    - 0: 空进程（不做任何事）

    - a.P: 前缀（先执行动作a，再执行P）

    - P|Q: 并行组合

    - P\L: 限制（禁止某些动作）

    - P[f]: 重标记（动作重命名）

    - rec X.P: 递归

    """

    

    def __init__(self, name="Process"):

        self.name = name

        self.actions = set()

        self.transitions = defaultdict(set)  # action -> set of next processes

        self.definitions = {}  # 递归定义

    

    def __repr__(self):

        return self.name

    

    def __add__(self, other):

        """并行组合 P | Q"""

        result = CCSProcess(f"{self.name}|{other.name}")

        result.actions = self.actions | other.actions

        # 组合转移

        for action in self.transitions:

            for next_proc in self.transitions[action]:

                result.transitions[action].add(next_proc | other)

        for action in other.transitions:

            for next_proc in other.transitions[action]:

                result.transitions[action].add(self | next_proc)

        return result

    

    def __or__(self, other):

        """选择 P + Q"""

        result = CCSProcess(f"{self.name}+{other.name}")

        result.actions = self.actions | other.actions

        result.transitions = defaultdict(set, self.transitions)

        for action, next_set in other.transitions.items():

            result.transitions[action].update(next_set)

        return result

    

    def restrict(self, L):

        """

        限制：禁止集合L中的动作

        

        参数:

            L: 禁止的动作集合

        """

        result = CCSProcess(f"{self.name}\\{L}")

        result.actions = self.actions - L

        for action in self.transitions:

            if action not in L:

                result.transitions[action] = self.transitions[action]

        return result

    

    def relabel(self, f):

        """

        重标记：通过函数f重命名动作

        

        参数:

            f: 重命名函数 action -> action

        """

        result = CCSProcess(f"{self.name}[f]")

        result.actions = {f(a) for a in self.actions}

        for action, next_set in self.transitions.items():

            new_action = f(action)

            result.transitions[new_action] = set()

            for proc in next_set:

                result.transitions[new_action].add(proc.relabel(f))

        return result

    

    def step(self, action):

        """

        执行一个动作

        

        参数:

            action: 要执行的动作

        

        返回:

            动作执行后的进程集合

        """

        return self.transitions.get(action, set())

    

    def can_step(self, action):

        """检查是否可以执行动作"""

        return len(self.step(action)) > 0





class CCSParser:

    """CCS表达式解析器"""

    

    def __init__(self):

        self.tokens = []

        self.pos = 0

    

    def parse(self, s):

        """解析CCS表达式"""

        s = s.strip()

        

        if not s or s == '0':

            return self._make_nil()

        

        if s.startswith('(') and s.endswith(')'):

            return self._parse(s[1:-1])

        

        if '|' in s:

            parts = self._split_alternatives(s, '|')

            if len(parts) == 2:

                left = self._parse(parts[0])

                right = self._parse(parts[1])

                return left + right

        

        if '+' in s:

            parts = self._split_alternatives(s, '+')

            if len(parts) == 2:

                left = self._parse(parts[0])

                right = self._parse(parts[1])

                return left | right

        

        # 前缀: a.P

        if '.' in s:

            parts = s.split('.', 1)

            action = parts[0].strip()

            rest = parts[1].strip()

            return self._make_prefix(action, self._parse(rest))

        

        # 限制: P\L

        if '\\' in s:

            parts = s.rsplit('\\', 1)

            proc = self._parse(parts[0])

            L = set(parts[1].strip().split(','))

            return proc.restrict(L)

        

        # 重标记: P[f]

        if '[' in s and ']' in s:

            # 简化处理

            pass

        

        return self._make_nil()

    

    def _split_alternatives(self, s, op):

        """分割选择或并行操作"""

        result = []

        current = []

        depth = 0

        

        for c in s:

            if c == '(':

                depth += 1

            elif c == ')':

                depth -= 1

            elif c == op and depth == 0:

                result.append(''.join(current))

                current = []

            else:

                current.append(c)

        

        result.append(''.join(current))

        return result

    

    def _make_nil(self):

        """创建空进程"""

        proc = CCSProcess("0")

        return proc

    

    def _make_prefix(self, action, next_proc):

        """创建前缀进程"""

        proc = CCSProcess(f"{action}.{next_proc.name}")

        proc.actions.add(action)

        proc.transitions[action].add(next_proc)

        return proc





class Bisimulation:

    """

    互模拟等价

    

    两个进程P和Q是互模拟的，当：

    1. P --a--> P' 意味着 Q --a--> Q' 且 P' ~ Q'

    2. Q --a--> Q' 意味着 P --a--> P' 且 P' ~ Q'

    

    这称为强互模拟（Strong Bisimulation）

    """

    

    @staticmethod

    def is_bisimilar(P, Q, visited=None):

        """

        检查P和Q是否强互模拟

        

        使用协同递归算法

        

        参数:

            P, Q: CCS进程

            visited: 已访问的状态对集合（用于检测环）

        

        返回:

            True/False

        """

        if visited is None:

            visited = set()

        

        # 检查是否已访问

        pair = (id(P), id(Q))

        if pair in visited:

            return True

        visited.add(pair)

        

        # 检查P的每个转移

        for action in P.actions:

            P_prime_set = P.step(action)

            Q_prime_set = Q.step(action)

            

            if not Q_prime_set:

                return False

            

            # 存在P'使得P --a--> P'

            if P_prime_set:

                found = False

                for P_prime in P_prime_set:

                    for Q_prime in Q_prime_set:

                        if Bisimulation.is_bisimilar(P_prime, Q_prime, visited):

                            found = True

                            break

                    if found:

                        break

                

                if not found:

                    return False

        

        # 检查Q的每个转移

        for action in Q.actions:

            P_prime_set = P.step(action)

            Q_prime_set = Q.step(action)

            

            if not P_prime_set:

                return False

        

        return True

    

    @staticmethod

    def weak_bisimilar(P, Q, visited=None):

        """

        弱互模拟（Weak Bisimulation）

        

        忽略内部动作τ

        """

        if visited is None:

            visited = set()

        

        pair = (id(P), id(Q))

        if pair in visited:

            return True

        visited.add(pair)

        

        # 简化：τ动作用*表示

        def get_visible_transitions(proc):

            return {a for a in proc.actions if a != 'τ'}

        

        for action in get_visible_transitions(P):

            P_prime_set = P.step(action)

            Q_prime_set = Q.step(action)

            

            if P_prime_set and not Q_prime_set:

                return False

            

            for P_prime in P_prime_set:

                found = False

                for Q_prime in Q_prime_set:

                    # 递归检查（可能需要通过τ动作）

                    if Bisimulation.weak_bisimilar(P_prime, Q_prime, visited):

                        found = True

                        break

                if not found:

                    return False

        

        for action in get_visible_transitions(Q):

            if not Q.step(action):

                return False

        

        return True





class ProcessEquivalence:

    """

    进程等价检测工具

    """

    

    @staticmethod

    def trace_equivalence(P, Q):

        """

        迹等价（Trace Equivalence）

        

        两个进程有相同的可观察迹集合

        """

        P_traces = ProcessEquivalence._compute_traces(P)

        Q_traces = ProcessEquivalence._compute_traces(Q)

        return P_traces == Q_traces

    

    @staticmethod

    def _compute_traces(proc, prefix=()):

        """计算进程的所有迹"""

        traces = {prefix}

        

        for action in proc.actions:

            for next_proc in proc.step(action):

                traces.update(

                    ProcessEquivalence._compute_traces(next_proc, prefix + (action,))

                )

        

        return traces

    

    @staticmethod

    def failure_equivalence(P, Q):

        """

        失败等价（Failure Equivalence）

        

        包含迹和拒绝集

        """

        P_failures = ProcessEquivalence._compute_failures(P)

        Q_failures = ProcessEquivalence._compute_failures(Q)

        return P_failures == Q_failures

    

    @staticmethod

    def _compute_failures(proc, prefix=(), refusals=None):

        """计算失败对"""

        if refusals is None:

            refusals = set()

        

        result = {(prefix, frozenset(refusals))}

        

        for action in proc.actions:

            for next_proc in proc.step(action):

                new_refusals = set(refusals)

                # 当进程停止时可以拒绝的动作

                if not next_proc.actions:

                    new_refusals.update(proc.actions)

                result.update(

                    ProcessEquivalence._compute_failures(

                        next_proc, prefix + (action,), new_refusals

                    )

                )

        

        return result





def ccs_laws():

    """打印CCS演算律"""

    print("""

╔══════════════════════════════════════════════════════════╗

║                    CCS 演算律                            ║

╠══════════════════════════════════════════════════════════╣

║                                                          ║

║  【并行组合律】                                           ║

║    P | Q = Q | P           (交换律)                      ║

║    P | (Q | R) = (P | Q) | R  (结合律)                   ║

║    P | 0 = P               (单位律)                      ║

║                                                          ║

║  【选择律】                                              ║

║    P + Q = Q + P           (交换律)                      ║

║    (P + Q) + R = P + (Q + R)  (结合律)                   ║

║    P + 0 = P               (单位律)                      ║

║                                                          ║

║  【前缀律】                                              ║

║    a.0 | b.0 = a.0 + b.0                                 ║

║                                                          ║

║  【限制律】                                              ║

║    (P \\L)\\M = P\\(L ∪ M)                                      ║

║    (a.P)\\L = a.(P\\L)      (如果 a ∉ L)                    ║

║    (a.P)\\L = 0            (如果 a ∈ L)                    ║

║                                                          ║

║  【互模拟律】                                            ║

║    a.(P + Q) = a.P + a.Q    (分配律)                     ║

║    a.(P | Q) = a.P | Q      (如果a不与P/Q内部通信)       ║

║                                                          ║

╚══════════════════════════════════════════════════════════╝

    """)





def run_demo():

    """运行CCS演示"""

    print("=" * 60)

    print("进程代数 - CCS通信系统演算")

    print("=" * 60)

    

    # 创建简单进程

    # P = a.b.0 + c.0

    parser = CCSParser()

    

    print("\n[CCS进程示例]")

    

    # P = a.P1 + b.0

    P = parser.parse("a.b.0 + b.0")

    print(f"  P = a.b.0 + b.0")

    print(f"    动作: {P.actions}")

    print(f"    a转移: {P.step('a')}")

    print(f"    b转移: {P.step('b')}")

    

    # Q = a.0 + a.b.0

    Q = parser.parse("a.0 + a.b.0")

    print(f"\n  Q = a.0 + a.b.0")

    print(f"    动作: {Q.actions}")

    print(f"    a转移: {Q.step('a')}")

    

    # 检查互模拟

    print("\n[互模拟检查]")

    is_bisim = Bisimulation.is_bisimilar(P, Q)

    print(f"  P ~ Q: {is_bisim}")

    

    # Trace等价

    print("\n[迹等价检查]")

    is_trace = ProcessEquivalence.trace_equivalence(P, Q)

    print(f"  P ≈trace Q: {is_trace}")

    

    # 迹集合

    print(f"  P的迹: {ProcessEquivalence._compute_traces(P)}")

    print(f"  Q的迹: {ProcessEquivalence._compute_traces(Q)}")

    

    # 并行组合

    print("\n[并行组合]")

    R = parser.parse("a.0 | b.0")

    print(f"  R = a.0 | b.0")

    print(f"    动作: {R.actions}")

    

    # 限制

    print("\n[限制]")

    S = parser.parse("a.b.0 + a.c.0 \\{a}")

    print(f"  S = (a.b.0 + a.c.0)\\\\{a}")

    print(f"    动作: {S.actions}")

    print(f"    a转移: {S.step('a')}")

    

    # 打印演算律

    ccs_laws()

    

    print("=" * 60)

    print("进程代数核心概念:")

    print("  1. CCS: 通信系统演算，用于描述并发系统")

    print("  2. 进程: 通过前缀、选择、并行等运算符组合")

    print("  3. 互模拟: 行为等价的精细概念")

    print("  4. 迹等价: 较粗的行为等价")

    print("  5. 死锁检测: 进程是否可能停止")

    print("=" * 60)





if __name__ == "__main__":

    run_demo()

