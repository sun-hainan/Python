# -*- coding: utf-8 -*-

"""

算法实现：形式验证 / temporal_fairness



本文件实现 temporal_fairness 相关的算法功能。

"""



import numpy as np

from collections import defaultdict, deque





class FairKripkeStructure:

    """

    带公平性约束的Kripke结构

    

    Kripke + 公平性约束

    """

    

    def __init__(self, ap_list):

        self.AP = set(ap_list)

        self.S = set()           # 状态集合

        self.S0 = set()          # 初始状态

        self.R = defaultdict(set)  # 转换关系

        self.labels = {}         # 状态标签

        

        # 公平性约束

        self.justice_set = []      # 弱公平（justice）：无限次出现

        self.compassion_set = []  # 强公平（compassion）：最终一直出现

    

    def add_state(self, s, ap_subset=None):

        self.S.add(s)

        if ap_subset:

            self.labels[s] = set(ap_subset)

        else:

            self.labels[s] = set()

    

    def set_initial(self, s):

        self.S0.add(s)

    

    def add_transition(self, s1, s2):

        self.R[s1].add(s2)

    

    def add_justice(self, condition):

        """

        添加弱公平约束（justice）

        

        语义：如果某个状态满足condition无限次出现，

        则无限次执行包含该状态的转换

        """

        self.justice_set.append(condition)

    

    def add_compassion(self, condition1, condition2):

        """

        添加强公平约束（compassion）

        

        语义：如果condition1无限次出现，则condition2最终一直出现

        """

        self.compassion_set.append((condition1, condition2))

    

    def get_successors(self, s):

        return self.R.get(s, set())

    

    def labels_of(self, s):

        return self.labels.get(s, set())





class FairnessChecker:

    """

    公平性检查器

    """

    

    def __init__(self, model):

        self.model = model

    

    def has_fair_path(self, from_state, condition):

        """

        检查是否存在从from_state出发的公平路径满足condition

        

        参数:

            from_state: 起始状态

            condition: 要满足的条件（无限次）

        

        返回:

            (存在公平路径, 路径)

        """

        # BFS + 公平性检查

        visited = set()

        queue = deque()

        

        # (state, path, condition_satisfied_count)

        queue.append((from_state, [from_state], 0))

        

        while queue:

            state, path, sat_count = queue.popleft()

            

            if state in visited and sat_count <= 0:

                continue

            visited.add(state)

            

            # 检查条件是否满足

            if self._check_condition(state, condition):

                sat_count += 1

            

            # 如果条件满足足够多次，认为是"无限次"

            if sat_count >= 5:  # 简化：用有限近似无限

                return True, path

            

            # 扩展

            for succ in self.model.get_successors(state):

                if succ not in visited:

                    queue.append((succ, path + [succ], sat_count))

        

        return False, []

    

    def _check_condition(self, state, condition):

        """检查状态是否满足条件"""

        if isinstance(condition, str):

            return condition in self.model.labels_of(state)

        elif isinstance(condition, tuple):

            # 处理更复杂的条件

            return True

        return False

    

    def check_strong_fairness(self, trigger_cond, effect_cond):

        """

        检查强公平性：A无限次出现 => B最终一直出现

        

        参数:

            trigger_cond: 触发条件A

            effect_cond: 效果条件B

        

        返回:

            是否满足强公平性

        """

        # 简化：检查每个无限路径是否满足

        for s0 in self.model.S0:

            path = self._find_infinite_path(s0)

            

            if path:

                # 检查路径上A是否无限次出现

                a_count = sum(1 for s in path if self._check_condition(s, trigger_cond))

                

                # 如果A无限次出现，检查B是否最终一直出现

                if a_count >= len(path) // 2:  # 近似无限

                    b_count = sum(1 for s in path if self._check_condition(s, effect_cond))

                    if b_count < len(path) // 2:

                        return False

        

        return True

    

    def _find_infinite_path(self, start):

        """找一条无限路径"""

        visited = {}

        queue = deque()

        

        queue.append((start, []))

        

        while queue:

            state, path = queue.popleft()

            

            if state in visited:

                # 找到环，可能是无限路径

                return path + [state]

            

            visited[state] = len(path)

            

            successors = list(self.model.get_successors(state))

            if successors:

                succ = successors[0]  # 简化：只选一个

                queue.append((succ, path + [state]))

            else:

                # 有限路径

                if len(path) > 10:

                    return path

        

        return None

    

    def check_weak_fairness(self, condition):

        """

        检查弱公平性：如果状态满足condition无限次，

        则无限次执行离开该状态的转换

        

        参数:

            condition: 条件

        

        返回:

            是否满足弱公平性

        """

        for s0 in self.model.S0:

            path = self._find_infinite_path(s0)

            

            if path:

                # 检查condition是否在路径上无限次出现

                cond_count = sum(1 for s in path if self._check_condition(s, condition))

                

                if cond_count >= len(path) // 2:  # 近似无限

                    # 检查从满足condition的状态是否有出边

                    for s in path:

                        if self._check_condition(s, condition):

                            if not self.model.get_successors(s):

                                return False

        

        return True





def fairness_types():

    """打印公平性类型说明"""

    print("""

╔══════════════════════════════════════════════════════════╗

║                    公平性类型说明                         ║

╠══════════════════════════════════════════════════════════╣

║                                                          ║

║  【弱公平（Weak Fairness / Justice）】                   ║

║                                                          ║

║    定义: 如果一个转换（或状态）被无限次启用，              ║

║          则它必须被无限次执行                             ║

║                                                          ║

║    形式: justice φ                                       ║

║          含义: 如果φ无限次成立，则相关转换无限次执行      ║

║                                                          ║

║  【强公平（Strong Fairness / Compassion）】              ║

║                                                          ║

║    定义: 如果一个转换（或状态）被无限次启用，              ║

║          则最终它必须一直执行                             ║

║                                                          ║

║    形式: compassion(φ, ψ)                                ║

║          含义: 如果φ无限次成立，则ψ最终一直成立          ║

║                                                          ║

║  【实现考虑】                                            ║

║                                                          ║

║    1. 调度器必须保证公平性                               ║

║    2. 模型检查时需要考虑公平性约束                       ║

║    3. 公平性假设影响活性性质的验证                       ║

║                                                          ║

╚══════════════════════════════════════════════════════════╝

    """)





def run_demo():

    """运行公平性检查演示"""

    print("=" * 60)

    print("时态逻辑与公平性")

    print("=" * 60)

    

    # 创建带公平性的Kripke结构

    model = FairKripkeStructure(['enabled', 'taken', 'done'])

    

    # 创建状态

    model.add_state('s0', ['enabled'])

    model.add_state('s1', ['enabled', 'taken'])

    model.add_state('s2', ['done'])

    model.add_state('s3', [])

    

    # 初始状态

    model.set_initial('s0')

    

    # 转换

    model.add_transition('s0', 's1')

    model.add_transition('s1', 's0')

    model.add_transition('s0', 's2')

    model.add_transition('s2', 's3')

    model.add_transition('s3', 's0')

    

    # 添加公平性约束

    # 弱公平：enabled状态无限次出现

    model.add_justice('enabled')

    

    # 强公平：如果enabled无限次，则taken最终一直

    model.add_compassion('enabled', 'taken')

    

    print("\n[Kripke结构]")

    print(f"  状态: {model.S}")

    print(f"  转换: {dict(model.R)}")

    print(f"  标签: {model.labels}")

    print(f"  弱公平约束: {model.justice_set}")

    print(f"  强公平约束: {model.compassion_set}")

    

    # 创建检查器

    checker = FairnessChecker(model)

    

    print("\n[公平路径检查]")

    exists, path = checker.has_fair_path('s0', 'enabled')

    print(f"  存在满足'enabled'的公平路径: {exists}")

    if path:

        print(f"  路径: {' -> '.join(path)}")

    

    print("\n[公平性验证]")

    

    # 弱公平性检查

    weak_fair = checker.check_weak_fairness('enabled')

    print(f"  弱公平 (enabled): {'满足' if weak_fair else '不满足'}")

    

    # 强公平性检查

    strong_fair = checker.check_strong_fairness('enabled', 'taken')

    print(f"  强公平 (enabled -> taken): {'满足' if strong_fair else '不满足'}")

    

    # 打印公平性类型说明

    fairness_types()

    

    print("=" * 60)

    print("公平性核心概念:")

    print("  1. 弱公平: 无限启用则无限执行")

    print("  2. 强公平: 无限启用则最终一直执行")

    print("  3. 公平路径: 满足所有公平性约束的无限路径")

    print("  4. 模型检查: 在公平路径上验证性质")

    print("  5. 调度: 公平性假设影响系统行为")

    print("=" * 60)





if __name__ == "__main__":

    run_demo()

