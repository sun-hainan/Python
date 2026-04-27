# -*- coding: utf-8 -*-

"""

算法实现：计算复杂性理论 / cook_levin



本文件实现 cook_levin 相关的算法功能。

"""



from typing import List, Dict, Set, Tuple, Optional

import random





class BooleanFormula:

    """

    布尔公式类

    """

    

    def __init__(self, num_variables: int = 0):

        self.num_variables = num_variables

        self.clauses: List[Set[int]] = []  # 每个子句是文字集合

        # 正文字 x_i，负文字 -x_i

    

    def add_variable(self):

        """添加一个新变量"""

        self.num_variables += 1

        return self.num_variables

    

    def add_clause(self, literals: List[int]):

        """

        添加子句（OR连接）

        

        参数:

            literals: 文字列表，如 [1, -2, 3] 表示 x1 ∨ ¬x2 ∨ x3

        """

        self.clauses.append(set(literals))

    

    def evaluate(self, assignment: Dict[int, bool]) -> bool:

        """

        在给定赋值下求值

        

        参数:

            assignment: {变量索引: True/False}

        

        返回:

            公式的真值

        """

        for clause in self.clauses:

            clause_value = False

            for literal in clause:

                if literal > 0:

                    clause_value = clause_value or assignment.get(literal, False)

                else:

                    clause_value = clause_value or (not assignment.get(-literal, True))

            if not clause_value:

                return False

        return True

    

    def __repr__(self):

        clause_strs = []

        for clause in self.clauses:

            literals = []

            for lit in clause:

                if lit > 0:

                    literals.append(f'x{lit}')

                else:

                    literals.append(f'¬x{-lit}')

            clause_strs.append(' ∨ '.join(literals))

        return ' ∧ '.join(f'({s})' for s in clause_strs)





class SATSolver:

    """

    SAT求解器（简单的随机算法）

    """

    

    def __init__(self):

        self.max_iterations = 1000

    

    def random_walk_sat(self, formula: BooleanFormula, 

                       iterations: int = 10000) -> Tuple[bool, Optional[Dict[int, bool]]]:

        """

        随机游走SAT求解器

        

        对于3-SAT，性能较好：

        - 时间复杂度期望为 O((4/3)^n)

        

        参数:

            formula: 布尔公式

            iterations: 最大迭代次数

        

        返回:

            (是否可满足, 满足的赋值)

        """

        n = formula.num_variables

        

        if n == 0:

            return True, {}

        

        for _ in range(iterations):

            # 随机赋值

            assignment = {i: random.choice([True, False]) 

                         for i in range(1, n + 1)}

            

            # 随机游走

            for _ in range(2 * n):  # 2-SAT 理论上是P

                if formula.evaluate(assignment):

                    return True, assignment

                

                # 找到一个不满足的子句

                unsatisfied = []

                for clause in formula.clauses:

                    clause_value = False

                    for literal in clause:

                        if literal > 0:

                            clause_value = clause_value or assignment.get(literal, False)

                        else:

                            clause_value = clause_value or (not assignment.get(-literal, True))

                    

                    if not clause_value:

                        unsatisfied.append(clause)

                

                if not unsatisfied:

                    return True, assignment

                

                # 随机翻转一个变量

                clause = random.choice(unsatisfied)

                literal = random.choice(list(clause))

                var = literal if literal > 0 else -literal

                assignment[var] = not assignment[var]

        

        return False, None





def prove_sat_in_np() -> Dict:

    """

    证明 SAT ∈ NP

    

    返回:

        证明概述

    """

    proof = {

        'problem': 'SAT (布尔可满足性)',

        'definition': '给定一个布尔公式，是否存在一组赋值使公式为真？',

        'steps': [

            '1. 猜测一组赋值（每个变量 True/False）',

            '2. 赋值长度 = O(n)，多项式长度',

            '3. 验证：遍历公式每个子句，检查是否至少有一个文字为真',

            '4. 验证时间 = O(n²)，多项式时间',

            '5. 存在多项式时间验证器 => SAT ∈ NP'

        ],

        'conclusion': 'SAT 是 NP 问题'

    }

    return proof





def prove_sat_np_hard() -> Dict:

    """

    证明 SAT 是 NP 难的（Cook-Levin定理核心）

    

    思路：任何NP问题都可以归约到SAT

    

    返回:

        证明概述

    """

    proof = {

        'theorem': 'Cook-Levin 定理',

        'statement': 'SAT 是 NP 完全的',

        'proof_idea': '''

        要证明 L 是 NP 完全的：

        1. 证明 L ∈ NP

        2. 证明所有 NP 问题多项式归约到 L

        

        对于 SAT：

        1. 已有 SAT ∈ NP

        

        2. 对任何 NP 问题 L：

           - L 有多项式时间验证器 V

           - V(x, certificate) 在 |x|^k 时间内验证

           

        3. 构造布尔公式模拟 V 的计算：

           - 为每个计算步骤创建变量

           - 为每个带单元创建变量

           - 为每个状态创建变量

           

        4. 公式大小 = O((计算步骤)²) = O((|x|^k)²) = O(|x|^{2k})

           多项式大小

           

        5. 公式可满足 ⟺ 存在正确的计算历史 ⟺ x ∈ L

        ''',

        'conclusion': 'SAT 是 NP 完全的'

    }

    return proof





def reduce_3sat_to_sat(formula: "BooleanFormula") -> "BooleanFormula":

    """

    将一般SAT规约为3-SAT

    

    参数:

        formula: 原始SAT公式

    

    返回:

        等价的3-SAT公式

    """

    result = BooleanFormula(formula.num_variables)

    

    # 添加原始变量

    for _ in range(formula.num_variables):

        result.add_variable()

    

    # 转换每个子句

    for clause in formula.clauses:

        clause_list = list(clause)

        

        if len(clause_list) <= 3:

            # 直接添加

            result.add_clause(clause_list)

        else:

            # 引入新变量

            # (x1 ∨ x2 ∨ x3 ∨ x4 ∨ x5)

            # =>

            # (x1 ∨ x2 ∨ y1) ∧ (¬y1 ∨ x3 ∨ y2) ∧ (¬y2 ∨ x4 ∨ x5)

            

            y = result.add_variable()

            new_clause = [clause_list[0], clause_list[1], y]

            result.add_clause(new_clause)

            

            for i in range(2, len(clause_list) - 1):

                prev_y = y

                y = result.add_variable()

                new_clause = [-prev_y, clause_list[i], y]

                result.add_clause(new_clause)

            

            result.add_clause([-y, clause_list[-1], clause_list[-2]])

    

    return result





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：布尔公式基本操作

    print("=" * 50)

    print("测试1: 布尔公式")

    print("=" * 50)

    

    # 创建公式: (x1 ∨ x2) ∧ (x1 ∨ ¬x3)

    formula = BooleanFormula(3)

    formula.add_clause([1, 2])       # x1 ∨ x2

    formula.add_clause([1, -3])      # x1 ∨ ¬x3

    

    print(f"公式: {formula}")

    

    # 测试赋值

    test_assignments = [

        {1: True, 2: False, 3: True},   # 满足

        {1: False, 2: False, 3: True},  # 不满足

        {1: True, 2: True, 3: False},   # 满足

    ]

    

    for assignment in test_assignments:

        value = formula.evaluate(assignment)

        print(f"  {assignment}: {'满足' if value else '不满足'}")

    

    # 测试用例2：SAT求解器

    print("\n" + "=" * 50)

    print("测试2: SAT求解器")

    print("=" * 50)

    

    solver = SATSolver()

    

    # 创建可满足的公式

    sat_formula = BooleanFormula(3)

    sat_formula.add_clause([1, 2, 3])

    sat_formula.add_clause([-1, 2, 3])

    sat_formula.add_clause([1, -2, 3])

    

    print(f"公式: {sat_formula}")

    satisfiable, assignment = solver.random_walk_sat(sat_formula, iterations=1000)

    print(f"可满足: {satisfiable}")

    if assignment:

        print(f"满足赋值: {assignment}")

    

    # 测试用例3：Cook-Levin定理概述

    print("\n" + "=" * 50)

    print("测试3: Cook-Levin定理")

    print("=" * 50)

    

    proof = prove_sat_in_np()

    print(f"问题: {proof['problem']}")

    print(f"定义: {proof['definition']}")

    print("证明步骤:")

    for step in proof['steps']:

        print(f"  {step}")

    

    # 测试用例4：NP完全性证明思路

    print("\n" + "=" * 50)

    print("测试4: NP完全性证明思路")

    print("=" * 50)

    

    proof = prove_sat_np_hard()

    print(f"定理: {proof['theorem']}")

    print(f"陈述: {proof['statement']}")

    print(f"结论: {proof['conclusion']}")

    

    # 测试用例5：SAT到3-SAT规约

    print("\n" + "=" * 50)

    print("测试5: SAT到3-SAT规约")

    print("=" * 50)

    

    # 创建长子句

    long_clause_formula = BooleanFormula(5)

    long_clause_formula.add_clause([1, 2, 3, 4, 5])

    

    print(f"原始公式 (长 clause): {long_clause_formula}")

    print(f"变量数: {long_clause_formula.num_variables}, 子句数: {len(long_clause_formula.clauses)}")

    

    reduced = reduce_3sat_to_sat(long_clause_formula)

    print(f"\n规约后的3-SAT公式:")

    print(f"  变量数: {reduced.num_variables}, 子句数: {len(reduced.clauses)}")

    print(f"  公式: {reduced}")

    

    # 测试用例6：SAT求解性能

    print("\n" + "=" * 50)

    print("测试6: SAT求解性能")

    print("=" * 50)

    

    import time

    

    # 测试不同变量数的公式

    for n in [5, 10, 15]:

        formula = BooleanFormula(n)

        

        # 添加2-SAT约束使其更可能可满足

        for _ in range(n):

            clause = [random.randint(1, n), random.randint(1, n)]

            if random.random() > 0.5:

                clause[1] = -clause[1]

            formula.add_clause(clause)

        

        start = time.time()

        satisfiable, _ = solver.random_walk_sat(formula, iterations=1000)

        elapsed = time.time() - start

        

        print(f"  n={n:2d}: {'可满足' if satisfiable else '不确定'} ({elapsed*1000:.2f}ms)")

