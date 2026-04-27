# -*- coding: utf-8 -*-

"""

算法实现：约束求解 / cdcl_algorithm



本文件实现 cdcl_algorithm 相关的算法功能。

"""



from typing import List, Dict, Set, Optional, Tuple

from collections import defaultdict





class CDCLSolver:

    """

    CDCL SAT求解器类

    包含冲突分析、决策、回溯、子句学习等核心组件

    """

    

    def __init__(self, clauses: List[Set[int]]):

        """

        初始化求解器

        

        Args:

            clauses: CNF公式的子句列表

        """

        # 深度拷贝,避免修改原公式

        self.original_clauses = [c.copy() for c in clauses]

        # 当前子句集

        self.clauses = [c.copy() for c in clauses]

        # 变量赋值: {var: value (True/False)}

        self.assignment: Dict[int, bool] = {}

        # 决策栈: 记录每一步的决策 [(var, value, explanation_clause)]

        self.decision_stack: List[Tuple[int, bool, Optional[Set[int]]]] = []

        # 变量层级: {var: decision_level}

        self.level: Dict[int, int] = {}

        # 当前决策层级

        self.current_level = 0

        # 冲突次数统计

        self.conflict_count = 0

        # 约束传播队列

        self.trail: List[int] = []

        

    def propagate(self) -> Tuple[bool, Optional[Set[int]]]:

        """

        约束传播(Unit Propagation, BCP)

        遍历所有子句,找出单元子句并传播

        

        Returns:

            (是否有冲突, 冲突子句或None)

        """

        while True:

            conflict_clause = None

            

            for clause in self.clauses:

                # 检查子句是否已满足

                satisfied = False

                unassigned_literals = []

                

                for lit in clause:

                    var = abs(lit)

                    if var in self.assignment:

                        # 检查文字是否为真

                        if (lit > 0 and self.assignment[var]) or (lit < 0 and not self.assignment[var]):

                            satisfied = True

                            break

                    else:

                        unassigned_literals.append(lit)

                

                if satisfied:

                    continue

                

                # 子句为空:所有文字都为假 -> 冲突

                if not unassigned_literals:

                    conflict_clause = clause.copy()

                    break

                

                # 单元子句:只有一个未赋值文字

                if len(unassigned_literals) == 1:

                    lit = unassigned_literals[0]

                    var = abs(lit)

                    value = lit > 0

                    

                    # 如果变量已有相反赋值 -> 冲突

                    if var in self.assignment and self.assignment[var] != value:

                        conflict_clause = clause.copy()

                        break

                    

                    # 传播这个赋值

                    self.assignment[var] = value

                    self.level[var] = self.current_level

                    self.trail.append(var)

            

            if conflict_clause:

                return False, conflict_clause

            

            # 如果没有新的传播,退出

            if len(self.trail) == len(self.assignment):

                break

        

        return True, None

    

    def analyze_conflict(self, conflict_clause: Set[int]) -> Tuple[Set[int], int]:

        """

        冲突分析:从冲突子句中学习新子句

        使用1UIP方法(First UIP)找到决策层级最高的变量

        

        Args:

            conflict_clause: 导致冲突的子句

        

        Returns:

            (学习子句, 回溯层级)

        """

        # 分配给冲突子句中每个文字一个标记

        assigned_lits = {}

        for lit in conflict_clause:

            var = abs(lit)

            if var in self.level:

                assigned_lits[lit] = self.level[var]

        

        # 1UIP: 找到除了当前决策层级外,最后一个出现的层级

        # 计算当前层级的赋值次数

        current_level_vars = [v for v in self.trail if self.level.get(v, -1) == self.current_level]

        counter = len(current_level_vars)

        

        # 从后向前遍历trail

        learn_clause = conflict_clause.copy()

        

        for var in reversed(self.trail):

            if self.level.get(var, -1) != self.current_level:

                continue

            

            counter -= 1

            if counter == 0:

                # 找到1UIP,在这个变量处停止

                break

            

            # 从学习子句中移除这个变量

            # 实际实现需要更复杂的CDCL,这里简化处理

        

        # 简化版本:返回冲突子句本身,回溯到层级0

        return learn_clause, 0

    

    def decide(self) -> bool:

        """

        决策:选择一个未赋值变量并赋予值

        使用最简单的策略:选择第一个未赋值变量

        

        Returns:

            是否还有未赋值变量

        """

        # 找出所有出现的变量

        all_vars = set()

        for clause in self.clauses:

            for lit in clause:

                all_vars.add(abs(lit))

        

        # 找一个未赋值变量

        unassigned = [v for v in all_vars if v not in self.assignment]

        if not unassigned:

            return False  # 所有变量都已赋值

        

        var = unassigned[0]

        value = True  # 默认设为True

        

        self.current_level += 1

        self.decision_stack.append((var, value, None))

        self.assignment[var] = value

        self.level[var] = self.current_level

        self.trail.append(var)

        

        return True

    

    def backtrack(self, target_level: int):

        """

        回溯到目标层级

        

        Args:

            target_level: 目标决策层级

        """

        # 撤销赋值

        vars_to_unassign = [v for v in self.trail if self.level.get(v, 0) > target_level]

        for var in vars_to_unassign:

            if var in self.assignment:

                del self.assignment[var]

            if var in self.level:

                del self.level[var]

        

        # 截断trail

        self.trail = [v for v in self.trail if self.level.get(v, 0) <= target_level]

        

        # 截断决策栈

        self.decision_stack = [(v, val, cls) for v, val, cls in self.decision_stack if self.level.get(v, 0) <= target_level]

        

        self.current_level = target_level

    

    def solve(self) -> Optional[Dict[int, bool]]:

        """

        CDCL求解主循环

        

        Returns:

            满足赋值或None

        """

        while True:

            # 约束传播

            success, conflict_clause = self.propagate()

            

            if not success:  # 冲突

                self.conflict_count += 1

                

                # 如果在层级0冲突,则公式不可满足

                if self.current_level == 0:

                    return None

                

                # 冲突分析

                learn_clause, backtrack_level = self.analyze_conflict(conflict_clause)

                

                # 添加学习子句

                self.clauses.append(learn_clause)

                

                # 回溯

                self.backtrack(backtrack_level)

            

            # 检查是否所有变量都已赋值

            all_vars = set()

            for clause in self.clauses:

                for lit in clause:

                    all_vars.add(abs(lit))

            

            if len(self.assignment) == len(all_vars):

                # 验证解是否正确

                if self.verify():

                    return self.assignment

                else:

                    return None

            

            # 决策

            if not self.decide():

                return self.assignment if self.verify() else None

    

    def verify(self) -> bool:

        """

        验证当前赋值是否满足所有子句

        

        Returns:

            是否满足

        """

        for clause in self.original_clauses:

            clause_satisfied = False

            for lit in clause:

                var = abs(lit)

                if var not in self.assignment:

                    continue

                if (lit > 0 and self.assignment[var]) or (lit < 0 and not self.assignment[var]):

                    clause_satisfied = True

                    break

            if not clause_satisfied:

                return False

        return True





def solve_cdcl(clauses: List[Set[int]]) -> Optional[Dict[int, bool]]:

    """

    CDCL求解入口

    

    Args:

        clauses: CNF公式

    

    Returns:

        满足赋值或None

    """

    solver = CDCLSolver(clauses)

    return solver.solve()





# 测试代码

if __name__ == "__main__":

    # 测试1: 简单公式

    test_clauses = [

        {1, 2},           # x1 OR x2

        {-1, 3},          # NOT x1 OR x3

        {-2, -3},         # NOT x2 OR NOT x3

        {1},              # x1

    ]

    

    print("测试1 - 简单SAT实例:")

    result = solve_cdcl(test_clauses)

    print(f"  结果: {result}")

    

    # 测试2: 更复杂的公式

    test_clauses2 = [

        {1, 2, 3},

        {-1, 4},

        {-2, -4},

        {-3, 5},

        {-5, 6},

        {-6, 1},

    ]

    

    print("\n测试2 - 复杂实例:")

    result2 = solve_cdcl(test_clauses2)

    print(f"  结果: {result2}")

    

    # 测试3: 不可满足

    test_clauses3 = [

        {1},

        {-1}

    ]

    

    print("\n测试3 - 不可满足:")

    result3 = solve_cdcl(test_clauses3)

    print(f"  结果: {result3}")

    

    # 测试4: 大型例子

    test_clauses4 = [

        {1, 2, 3},

        {1, -2},

        {2, -3},

        {3, -1},

        {-1, -2, -3},

    ]

    

    print("\n测试4 - 大型实例:")

    result4 = solve_cdcl(test_clauses4)

    print(f"  结果: {result4}")

    

    print("\n所有测试完成!")

