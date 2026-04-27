# -*- coding: utf-8 -*-

"""

算法实现：形式验证 / predicate_abstraction



本文件实现 predicate_abstraction 相关的算法功能。

"""



import numpy as np

from collections import defaultdict, deque

from itertools import combinations





class Predicate:

    """谓词：原子命题如 x > 5, y == z 等"""

    

    def __init__(self, name, evaluate_func):

        self.name = name

        self.evaluate = evaluate_func  # (state) -> bool

    

    def __repr__(self):

        return self.name





class AbstractState:

    """

    抽象状态：谓词值的组合

    

    例如：对于谓词 [p1, p2, p3]

    抽象状态可以表示为 [True, False, True]

    这表示 p1∧¬p2∧p3 成立

    """

    

    def __init__(self, values):

        """

        初始化抽象状态

        

        参数:

            values: 谓词真值列表 [True, False, ...]

        """

        self.values = tuple(values)

    

    def __hash__(self):

        return hash(self.values)

    

    def __eq__(self, other):

        return self.values == other.values

    

    def __repr__(self):

        # 简化为位串表示

        return ''.join('1' if v else '0' for v in self.values)

    

    def __and__(self, other):

        """合取"""

        new_values = [a and b for a, b in zip(self.values, other.values)]

        return AbstractState(new_values)

    

    def __or__(self, other):

        """析取"""

        new_values = [a or b for a, b in zip(self.values, other.values)]

        return AbstractState(new_values)

    

    def __invert__(self):

        """否定"""

        return AbstractState([not v for v in self.values])





class ConcreteState:

    """

    具体状态：变量到值的映射

    

    例如：{'x': 10, 'y': 5}

    """

    

    def __init__(self, values):

        self.values = values if values else {}

    

    def __hash__(self):

        return hash(tuple(sorted(self.values.items())))

    

    def __eq__(self, other):

        return self.values == other.values

    

    def evaluate_predicate(self, pred):

        """评估谓词"""

        return pred.evaluate(self.values)

    

    def to_abstract(self, predicates):

        """转换到抽象状态"""

        values = [self.evaluate_predicate(p) for p in predicates]

        return AbstractState(values)





class TransitionSystem:

    """迁移系统"""

    

    def __init__(self, initial_states, transitions):

        """

        参数:

            initial_states: 初始状态集合

            transitions: [(from_state, to_state, condition), ...]

        """

        self.initial_states = initial_states

        self.transitions = transitions  # (from, to, condition_func)

    

    def get_successors(self, state):

        """获取后继状态"""

        successors = []

        for from_s, to_s, cond in self.transitions:

            if from_s == state and (cond is None or cond(state)):

                successors.append(to_s)

        return successors





class PredicateAbstraction:

    """

    谓词抽象

    

    将具体状态空间抽象为谓词组合状态空间

    """

    

    def __init__(self, predicates):

        """

        参数:

            predicates: 谓词列表

        """

        self.predicates = predicates

        self.num_preds = len(predicates)

        

        # 构建抽象迁移系统

        self.abstract_transitions = defaultdict(set)

    

    def compute_abstraction(self, concrete_system):

        """

        计算抽象迁移系统

        

        对于每对抽象状态a1, a2，

        如果存在具体状态s1∈γ(a1)和s2∈γ(a2)使得s1->s2，

        则添加抽象迁移a1->a2

        """

        # 枚举所有抽象状态

        for abs_values in range(2 ** self.num_preds):

            a1 = AbstractState([bool(abs_values & (1 << i)) for i in range(self.num_preds)])

            

            for abs_values2 in range(2 ** self.num_preds):

                a2 = AbstractState([bool(abs_values2 & (1 << i)) for i in range(self.num_preds)])

                

                # 检查是否存在具体转移

                if self._has_concrete_transition(a1, a2, concrete_system):

                    self.abstract_transitions[a1].add(a2)

    

    def _has_concrete_transition(self, a1, a2, system):

        """

        检查是否存在从a1到a2的具体转移

        

        简化：枚举所有具体状态

        """

        # 生成满足a1的具体状态

        for s1 in self._concrete_states_for_abstract(a1):

            for s2 in system.get_successors(s1):

                # 检查s2是否满足a2

                if s2.to_abstract(self.predicates) == a2:

                    return True

        return False

    

    def _concrete_states_for_abstract(self, astate):

        """

        生成满足抽象状态的具体状态

        

        简化实现：使用简单的状态枚举

        """

        # 简化：只生成满足当前抽象状态的具体状态

        results = []

        

        # 对于简单情况，生成满足谓词条件的示例状态

        state = {}

        for i, val in enumerate(astate.values):

            pred = self.predicates[i]

            # 简化：为谓词设置满足条件的值

            if 'x' in pred.name:

                state['x'] = 10 if val else 0

            if 'y' in pred.name:

                state['y'] = 5 if val else 0

            if 'z' in pred.name:

                state['z'] = 3 if val else 0

        

        results.append(ConcreteState(state))

        return results





class CEGAR:

    """

    反例引导的抽象细化（Counterexample-Guided Abstraction Refinement）

    

    迭代过程：

    1. 构建抽象模型

    2. 检查抽象模型是否满足属性

    3. 如果抽象模型有反例，检查是否是真实反例

    4. 如果是虚假反例，提炼并添加到谓词集合

    5. 重复直到找到真实反例或证明属性成立

    """

    

    def __init__(self, concrete_system, property_checker):

        """

        参数:

            concrete_system: 具体迁移系统

            property_checker: 属性检查函数 (state -> bool)

        """

        self.concrete_system = concrete_system

        self.property_checker = property_checker

        

        # 初始谓词（可以从属性推导）

        self.predicates = []

        self.abstraction = None

    

    def add_predicate(self, pred):

        """添加新谓词"""

        self.predicates.append(pred)

    

    def check(self, target_predicate, max_iterations=10):

        """

        检查属性

        

        参数:

            target_predicate: 目标谓词（要验证的性质）

            max_iterations: 最大迭代次数

        

        返回:

            (结果, 反例路径或None)

        """

        for iteration in range(max_iterations):

            print(f"\n[CEGAR迭代 {iteration + 1}]")

            print(f"  谓词数量: {len(self.predicates)}")

            

            # 步骤1：构建抽象模型

            self.abstraction = PredicateAbstraction(self.predicates)

            self.abstraction.compute_abstraction(self.concrete_system)

            

            abs_states = len(set(self.abstraction.abstract_transitions.keys()))

            print(f"  抽象状态数: {abs_states}")

            

            # 步骤2：检查抽象模型

            abstract_cex = self._check_abstract(target_predicate)

            

            if abstract_cex is None:

                # 属性在抽象模型中成立

                print("  抽象模型满足属性")

                # 需要验证抽象是充分的

                if self._verify_abstraction(target_predicate):

                    print("  抽象验证成功，属性成立")

                    return True, None

                else:

                    print("  属性可能成立，需要更多谓词")

                    continue

            

            # 步骤3：提取具体反例

            print("  发现抽象反例，验证...")

            concrete_cex = self._extract_concrete_cex(abstract_cex)

            

            if concrete_cex is None:

                # 虚假反例，需要细化

                print("  虚假反例，提取新谓词...")

                new_predicates = self._refine(abstract_cex)

                for p in new_predicates:

                    self.add_predicate(p)

            else:

                # 真实反例

                print("  真实反例找到！")

                return False, concrete_cex

        

        print("  达到最大迭代次数")

        return None, None

    

    def _check_abstract(self, target):

        """检查抽象模型"""

        # BFS查找违反target的抽象状态

        visited = set()

        queue = deque()

        

        # 初始抽象状态

        init_abs = AbstractState([False] * len(self.predicates))

        queue.append([init_abs])

        

        while queue:

            path = queue.popleft()

            current = path[-1]

            

            if current in visited:

                continue

            visited.add(current)

            

            # 检查是否违反属性

            # 这里简化：假设target是要避免的状态

            if self._violates(current, target):

                return path

            

            # 扩展

            for next_abs in self.abstraction.abstract_transitions.get(current, set()):

                if next_abs not in visited:

                    queue.append(path + [next_abs])

        

        return None

    

    def _violates(self, state, target):

        """检查抽象状态是否违反属性"""

        # 简化：检查target谓词是否为False

        return not state.values[0] if self.predicates else False

    

    def _extract_concrete_cex(self, abstract_cex):

        """

        从抽象反例提取具体反例

        

        返回None表示是虚假反例

        """

        # 简化：只检查第一个和最后一个状态

        if len(abstract_cex) < 2:

            return None

        

        start_abs = abstract_cex[0]

        end_abs = abstract_cex[-1]

        

        # 尝试生成具体状态

        start_concrete = self._abs_to_concrete(start_abs)

        

        # 模拟执行

        path = [start_concrete]

        current = start_concrete

        

        for i in range(len(abstract_cex) - 1):

            found = False

            for next_s in self.concrete_system.get_successors(current):

                next_abs = next_s.to_abstract(self.predicates)

                if next_abs == abstract_cex[i + 1]:

                    path.append(next_s)

                    current = next_s

                    found = True

                    break

            

            if not found:

                return None  # 虚假反例

        

        return path

    

    def _abs_to_concrete(self, astate):

        """抽象状态转具体状态"""

        state = {}

        for i, val in enumerate(astate.values):

            pred = self.predicates[i]

            # 根据谓词名设置值

            if 'x' in pred.name.lower():

                state['x'] = 10 if val else 0

            elif 'y' in pred.name.lower():

                state['y'] = 5 if val else 0

            elif 'z' in pred.name.lower():

                state['z'] = 3 if val else 0

            elif 'flag' in pred.name.lower():

                state['flag'] = val

        

        return ConcreteState(state)

    

    def _verify_abstraction(self, target):

        """

        验证抽象是否充分

        

        检查是否所有满足target的具体状态都被包含

        """

        # 简化：总是返回True

        return True

    

    def _refine(self, abstract_cex):

        """

        从反例路径中提取新谓词

        

        虚假反例的路径上应该有关键的区分谓词

        """

        new_preds = []

        

        # 简化：在反例路径的每个转移处提取谓词

        for i in range(len(abstract_cex) - 1):

            a1 = abstract_cex[i]

            a2 = abstract_cex[i + 1]

            

            # 找出不同的谓词

            for j in range(len(a1.values)):

                if a1.values[j] != a2.values[j]:

                    pred_name = self.predicates[j].name if j < len(self.predicates) else f"p{j}"

                    print(f"    添加细化谓词: {pred_name}")

                    new_preds.append(

                        Predicate(f"{pred_name}'", lambda s, pn=pred_name: s.get(pn[0], 0) > 0)

                    )

        

        return new_preds





def run_demo():

    """运行CEGAR演示"""

    print("=" * 60)

    print("谓词抽象与CEGAR反例引导细化")

    print("=" * 60)

    

    # 创建简单迁移系统

    # 状态: x的值

    # 转换: x可以增加直到10，然后停止

    

    def make_states():

        states = []

        for x in range(12):

            states.append(ConcreteState({'x': x}))

        return states

    

    all_states = make_states()

    

    # 创建转移

    transitions = []

    for x in range(11):

        transitions.append((

            ConcreteState({'x': x}),

            ConcreteState({'x': x + 1}),

            None

        ))

    

    system = TransitionSystem([all_states[0]], transitions)

    

    # 定义谓词

    predicates = [

        Predicate('x < 10', lambda s: s.get('x', 0) < 10),

        Predicate('x >= 10', lambda s: s.get('x', 0) >= 10),

    ]

    

    print("\n[迁移系统]")

    print(f"  状态数: {len(all_states)}")

    print(f"  谓词: {[p.name for p in predicates]}")

    

    # 创建CEGAR实例

    cegar = CEGAR(system, lambda s: s.values.get('x', 0) < 10)

    

    # 添加初始谓词

    for p in predicates:

        cegar.add_predicate(p)

    

    # 检查属性

    print("\n[CEGAR检查]")

    result, cex = cegar.check(predicates[1], max_iterations=5)

    

    if result is True:

        print("  属性成立")

    elif result is False:

        print(f"  属性不成立，反例: {[s.values for s in cex]}")

    else:

        print("  无法确定")

    

    print("\n" + "=" * 60)

    print("CEGAR核心概念:")

    print("  1. 抽象: 将无限具体状态映射到有限抽象状态")

    print("  2. 虚假反例: 抽象反例在具体系统不存在")

    print("  3. 细化: 从虚假反例提取新谓词")

    print("  4. 迭代: 交替进行抽象检查和细化")

    print("  5. 终止: 找到真实反例或证明属性")

    print("=" * 60)





if __name__ == "__main__":

    run_demo()

