# -*- coding: utf-8 -*-

"""

算法实现：形式验证 / ctl_model_checking



本文件实现 ctl_model_checking 相关的算法功能。

"""



import numpy as np

from collections import defaultdict, deque





class KripkeStructure:

    """

    Kripke结构（状态转换系统）

    

    M = (S, S0, R, L, AP)

    - S: 状态集合

    - S0: 初始状态集合

    - R: 转换关系 S × S

    - L: 标签函数 S -> 2^AP

    - AP: 原子命题集合

    """

    

    def __init__(self, ap_list):

        """

        初始化Kripke结构

        

        参数:

            ap_list: 原子命题列表

        """

        self.AP = set(ap_list)

        self.S = set()          # 状态集合

        self.S0 = set()         # 初始状态

        self.R = defaultdict(set)  # 转换关系: state -> set of states

        self.labels = {}        # state -> set of atomic propositions

        

        # 反向转换（用于计算predecessors）

        self.reverse_R = defaultdict(set)

    

    def add_state(self, s, ap_subset=None):

        """添加状态"""

        self.S.add(s)

        if ap_subset is not None:

            self.labels[s] = set(ap_subset)

        else:

            self.labels[s] = set()

    

    def set_initial(self, s):

        """设置初始状态"""

        self.S0.add(s)

    

    def add_transition(self, s1, s2):

        """添加转换 s1 -> s2"""

        self.R[s1].add(s2)

        self.reverse_R[s2].add(s1)

    

    def get_predecessors(self, s):

        """获取前驱状态集合"""

        return self.reverse_R[s]

    

    def get_successors(self, s):

        """获取后继状态集合"""

        return self.R.get(s, set())

    

    def labels_of(self, s):

        """获取状态的标签"""

        return self.labels.get(s, set())

    

    def check_ap(self, s, ap):

        """检查状态s是否满足原子命题ap"""

        return ap in self.labels[s]





class CTLModelChecker:

    """

    CTL模型检查器

    

    CTL语法:

    - 原子命题: p, q, r, ...

    - 逻辑联结词: AND, OR, NOT

    - CTL算子: AX, EX, AF, EF, AG, EG, AU, EU, AR, ER

    

    CTL算子结构: [路径量词][时序算子]

    - 路径量词: A (所有路径), E (存在路径)

    - 时序算子: X (下一步), F (最终), G (全局), U (直到), R (释放)

    """

    

    def __init__(self, model):

        self.model = model

        self.cache = {}

    

    def check(self, formula, state):

        """

        检查公式在给定状态下是否成立

        

        参数:

            formula: CTL公式（字符串或元组）

            state: 状态

        

        返回:

            True/False

        """

        f = self._parse_formula(formula)

        sat_states = self._eval(f)

        return state in sat_states

    

    def _parse_formula(self, formula):

        """解析公式"""

        if isinstance(formula, str):

            return self._parse_string(formula)

        return formula

    

    def _parse_string(self, s):

        """解析字符串公式为元组形式"""

        s = s.strip()

        

        # 括号处理

        if s.startswith('(') and s.endswith(')'):

            return self._parse_string(s[1:-1])

        

        # NOT

        if s.startswith('NOT ') or s.startswith('not '):

            return ('not', self._parse_string(s[4:]))

        

        # 找出主要联结词（最外层）

        paren_depth = 0

        for i, c in enumerate(s):

            if c == '(':

                paren_depth += 1

            elif c == ')':

                paren_depth -= 1

            elif c == ' ' and paren_depth == 0:

                first_word = s[:i]

                

                # CTL算子检测

                if first_word in ('AX', 'EX', 'AF', 'EF', 'AG', 'EG', 'AU', 'EU', 'AR', 'ER'):

                    return (first_word.lower(), self._parse_string(s[i+1:]))

                

                # 二元联结词

                if first_word in ('AND', 'OR', 'IMPLIES', 'U', 'R'):

                    if first_word == 'AND':

                        parts = self._split_binary(s[i+1:], 'AND')

                        if len(parts) == 2:

                            return ('and', self._parse_string(parts[0]), self._parse_string(parts[1]))

                    elif first_word == 'OR':

                        parts = self._split_binary(s[i+1:], 'OR')

                        if len(parts) == 2:

                            return ('or', self._parse_string(parts[0]), self._parse_string(parts[1]))

                    elif first_word == 'IMPLIES':

                        parts = self._split_binary(s[i+1:], 'IMPLIES')

                        if len(parts) == 2:

                            return ('imp', self._parse_string(parts[0]), self._parse_string(parts[1]))

        

        # 原子命题

        return ('ap', s.strip())

    

    def _split_binary(self, s, op):

        """分割二元表达式"""

        s = s.strip()

        depth = 0

        start = 0

        

        for i, c in enumerate(s):

            if c == '(':

                depth += 1

            elif c == ')':

                depth -= 1

            elif c == ' ' and depth == 0:

                word = s[start:i]

                if word == op:

                    return [s[:start], s[i+1:]]

                start = i + 1

        

        return [s]

    

    def _eval(self, formula):

        """

        计算公式的满足状态集合

        

        参数:

            formula: 解析后的公式元组

        

        返回:

            满足状态集合

        """

        op = formula[0]

        

        # 缓存

        cache_key = ('eval', formula)

        if cache_key in self.cache:

            return self.cache[cache_key]

        

        if op == 'ap':

            # 原子命题

            ap = formula[1]

            result = {s for s in self.model.S if self.model.check_ap(s, ap)}

        

        elif op == 'not':

            # NOT

            sub = self._eval(formula[1])

            result = self.model.S - sub

        

        elif op == 'and':

            # AND

            sub1 = self._eval(formula[1])

            sub2 = self._eval(formula[2])

            result = sub1 & sub2

        

        elif op == 'or':

            # OR

            sub1 = self._eval(formula[1])

            sub2 = self._eval(formula[2])

            result = sub1 | sub2

        

        elif op == 'imp':

            # IMPLIES

            sub1 = self._eval(formula[1])

            sub2 = self._eval(formula[2])

            result = (self.model.S - sub1) | sub2

        

        elif op == 'ax':

            # AX: 所有后继都满足

            sub = self._eval(formula[1])

            result = self._ax(sub)

        

        elif op == 'ex':

            # EX: 存在后继满足

            sub = self._eval(formula[1])

            result = self._ex(sub)

        

        elif op == 'af':

            # AF: 最终到达（所有路径）

            sub = self._eval(formula[1])

            result = self._af(sub)

        

        elif op == 'ef':

            # EF: 最终到达（存在路径）

            sub = self._eval(formula[1])

            result = self._ef(sub)

        

        elif op == 'ag':

            # AG: 全局满足（所有路径）

            sub = self._eval(formula[1])

            result = self._ag(sub)

        

        elif op == 'eg':

            # EG: 全局满足（存在路径）

            sub = self._eval(formula[1])

            result = self._eg(sub)

        

        elif op == 'au':

            # AU: Until（所有路径）

            sub1 = self._eval(formula[1])

            sub2 = self._eval(formula[2])

            result = self._au(sub1, sub2)

        

        elif op == 'eu':

            # EU: Until（存在路径）

            sub1 = self._eval(formula[1])

            sub2 = self._eval(formula[2])

            result = self._eu(sub1, sub2)

        

        elif op == 'ar':

            # AR: Release

            sub1 = self._eval(formula[1])

            sub2 = self._eval(formula[2])

            result = self._ar(sub1, sub2)

        

        elif op == 'er':

            # ER: Release

            sub1 = self._eval(formula[1])

            sub2 = self._eval(formula[2])

            result = self._er(sub1, sub2)

        

        else:

            raise ValueError(f"Unknown operator: {op}")

        

        self.cache[cache_key] = result

        return result

    

    def _ax(self, Q):

        """AX Q: 所有后继状态都满足Q"""

        result = set()

        for s in self.model.S:

            # 检查所有后继是否都在Q中

            successors = self.model.get_successors(s)

            if successors and all(succ in Q for succ in successors):

                result.add(s)

        return result

    

    def _ex(self, Q):

        """EX Q: 存在后继状态满足Q"""

        result = set()

        for s in self.model.S:

            successors = self.model.get_successors(s)

            if successors and any(succ in Q for succ in successors):

                result.add(s)

        return result

    

    def _af(self, Q):

        """AF Q: 所有路径最终到达Q（Fixpoint计算）"""

        Y = set(Q)  # 初始：所有Q状态

        W = self.model.S - Q  # 不在Q中的状态

        

        # 迭代直到稳定

        while True:

            new_Y = Y.copy()

            for s in W:

                # 如果所有后继都在Y中，则加入Y

                successors = self.model.get_successors(s)

                if successors and all(succ in new_Y for succ in successors):

                    new_Y.add(s)

            

            if new_Y == Y:

                break

            Y = new_Y

            W = W - Y

        

        return Y

    

    def _ef(self, Q):

        """EF Q: 存在路径最终到达Q"""

        Y = set(Q)  # 初始：所有Q状态

        W = set(self.model.S) - Y

        

        # 反向传播：加入能到达Y的状态

        changed = True

        while changed:

            changed = False

            for s in W:

                successors = self.model.get_successors(s)

                if successors and any(succ in Y for succ in successors):

                    Y.add(s)

                    W.remove(s)

                    changed = True

        

        return Y

    

    def _ag(self, Q):

        """AG Q: 所有路径上Q始终成立"""

        # AG Q = NOT EF NOT Q

        not_Q = self.model.S - Q

        ef_not_Q = self._ef(not_Q)

        return self.model.S - ef_not_Q

    

    def _eg(self, Q):

        """EG Q: 存在路径上Q始终成立（最大Fixpoint）"""

        Y = set(Q)  # 初始：Q

        

        # 迭代：移除不能保持Q的状态

        changed = True

        while changed:

            changed = False

            to_remove = set()

            

            for s in Y:

                successors = self.model.get_successors(s)

                if successors and not all(succ in Y for succ in successors):

                    to_remove.add(s)

            

            if to_remove:

                Y = Y - to_remove

                changed = True

        

        return Y

    

    def _au(self, P, Q):

        """AU P U Q: 所有路径上P直到Q"""

        # 相当于 (EG NOT Q) AND (AF Q) 的更复杂版本

        # 使用Fixpoint计算

        W = self.model.S - Q  # 不在Q中的状态

        Y = set(Q)  # 已在Q中的状态

        

        while True:

            new_Y = Y.copy()

            for s in W:

                successors = self.model.get_successors(s)

                # s的所有后继要么已在Y中，要么满足P且能到达Y

                if successors:

                    all_valid = True

                    for succ in successors:

                        if succ not in Y and succ not in P:

                            all_valid = False

                            break

                    if all_valid:

                        new_Y.add(s)

            

            if new_Y == Y:

                break

            Y = new_Y

            W = W - Y

        

        return Y

    

    def _eu(self, P, Q):

        """EU P U Q: 存在路径上P直到Q"""

        Y = set(Q)  # 已在Q中的状态

        W = set(self.model.S) - Y  # 不在Q中的状态

        

        # 扩展：加入满足P且能到达Y的状态

        changed = True

        while changed:

            changed = False

            for s in W:

                if s not in P:

                    continue

                successors = self.model.get_successors(s)

                if successors and any(succ in Y for succ in successors):

                    Y.add(s)

                    W.remove(s)

                    changed = True

        

        return Y

    

    def _ar(self, P, Q):

        """AR P R Q: 所有路径上P释放Q"""

        # A R Q P = NOT E U NOT Q NOT P

        not_P = self.model.S - P

        not_Q = self.model.S - Q

        return self._ar_impl(not_P, not_Q)

    

    def _er(self, P, Q):

        """ER P R Q: 存在路径上P释放Q"""

        # E R Q P = NOT A U NOT Q NOT P

        not_P = self.model.S - P

        not_Q = self.model.S - Q

        return self._er_impl(not_P, not_Q)

    

    def _ar_impl(self, P, Q):

        """AR实现：NOT (E U NOT Q NOT P)"""

        # 计算 E Q U P 的区域

        Y = set(Q)

        W = self.model.S - Y

        

        while True:

            new_Y = Y.copy()

            for s in W:

                successors = self.model.get_successors(s)

                if successors:

                    # s的后继中有在Y中的，且s不在P中

                    if any(succ in Y for succ in successors) and s not in P:

                        new_Y.add(s)

            

            if new_Y == Y:

                break

            Y = new_Y

            W = W - Y

        

        return self.model.S - Y

    

    def _er_impl(self, P, Q):

        """ER实现：NOT (A U NOT Q NOT P)"""

        # 计算能保持NOT P或最终达到NOT Q的状态

        Y = set(self.model.S) - P  # NOT P状态

        W = P & set(self.model.S)  # P状态

        

        while True:

            new_Y = Y.copy()

            for s in W:

                successors = self.model.get_successors(s)

                if successors and any(succ in new_Y for succ in successors):

                    new_Y.add(s)

            

            if new_Y == Y:

                break

            Y = new_Y

            W = W - Y

        

        return Y

    

    def check_all_initial(self, formula):

        """检查所有初始状态是否满足公式"""

        f = self._parse_formula(formula)

        sat_states = self._eval(f)

        return self.model.S0 <= sat_states

    

    def model_check(self, formula):

        """

        完整的模型检查过程

        

        参数:

            formula: CTL公式

        

        返回:

            (满足状态集合, 是否所有初始状态满足)

        """

        self.cache.clear()

        f = self._parse_formula(formula)

        sat_states = self._eval(f)

        all_initial = self.model.S0 <= sat_states

        return sat_states, all_initial





def run_demo():

    """运行CTL模型检查演示"""

    print("=" * 60)

    print("CTL模型检查 - 计算树逻辑")

    print("=" * 60)

    

    # 创建简单的Kripke结构

    # 3个状态：s0, s1, s2

    # s0 -> s1, s0 -> s2

    # s1 -> s1

    # s2 -> s2

    

    model = KripkeStructure(['p', 'q', 'r'])

    

    # 添加状态和标签

    model.add_state('s0', ['p'])

    model.add_state('s1', ['q'])

    model.add_state('s2', ['q', 'r'])

    

    # 设置初始状态

    model.set_initial('s0')

    

    # 添加转换

    model.add_transition('s0', 's1')

    model.add_transition('s0', 's2')

    model.add_transition('s1', 's1')

    model.add_transition('s2', 's2')

    

    # 创建模型检查器

    checker = CTLModelChecker(model)

    

    print("\n[Kripke结构]")

    print(f"  状态: {model.S}")

    print(f"  初始状态: {model.S0}")

    print(f"  转换关系: {dict(model.R)}")

    print(f"  标签: {model.labels}")

    

    print("\n[CTL公式检查]")

    

    # EX p

    result, ok = checker.model_check('EX p')

    print(f"  EX p: 满足状态 = {result}, 初始状态满足 = {ok}")

    

    # EG q

    result, ok = checker.model_check('EG q')

    print(f"  EG q: 满足状态 = {result}, 初始状态满足 = {ok}")

    

    # AG (p -> EF q)

    result, ok = checker.model_check('AG (p -> EF q)')

    print(f"  AG (p -> EF q): 满足状态 = {result}, 初始状态满足 = {ok}")

    

    # AF q

    result, ok = checker.model_check('AF q')

    print(f"  AF q: 满足状态 = {result}, 初始状态满足 = {ok}")

    

    # E (p U q)

    result, ok = checker.model_check('E (p U q)')

    print(f"  E (p U q): 满足状态 = {result}, 初始状态满足 = {ok}")

    

    # EF (p AND r)

    result, ok = checker.model_check('EF (p AND r)')

    print(f"  EF (p AND r): 满足状态 = {result}, 初始状态满足 = {ok}")

    

    # AG EF p

    result, ok = checker.model_check('AG EF p')

    print(f"  AG EF p: 满足状态 = {result}, 初始状态满足 = {ok}")

    

    print("\n" + "=" * 60)

    print("CTL模型检查核心概念:")

    print("  1. CTL: 计算树逻辑，每个路径算子配对路径量词A/E")

    print("  2. 路径量词: A(所有路径), E(存在路径)")

    print("  3. 时序算子:")

    print("     X (Next): 下一步")

    print("     F (Future): 最终/某时刻")

    print("     G (Global): 全局/始终")

    print("     U (Until): 直到")

    print("     R (Release): 释放")

    print("  4. 算法: 基于不动点迭代和CTL标记算法")

    print("  5. 复杂度: O(m * |φ|), m为转换数，|φ|为公式大小")

    print("=" * 60)





if __name__ == "__main__":

    run_demo()

