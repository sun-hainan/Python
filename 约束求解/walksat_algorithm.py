# -*- coding: utf-8 -*-

"""

算法实现：约束求解 / walksat_algorithm



本文件实现 walksat_algorithm 相关的算法功能。

"""



import random

from typing import List, Set, Dict, Optional, Tuple





class WalkSATSolver:

    """

    WalkSAT/GSAT局部搜索求解器

    结合贪心策略和随机重启来求解SAT问题

    """

    

    def __init__(self, clauses: List[Set[int]], max_iterations: int = 10000, 

                 tabu_tenure: int = 10, noise_prob: float = 0.5):

        """

        初始化求解器

        

        Args:

            clauses: CNF公式的子句列表

            max_iterations: 最大迭代次数

            tabu_tenure: Tabu搜索的禁忌长度

            noise_prob: 随机噪声概率(用于WalkSAT)

        """

        self.clauses = clauses

        self.max_iterations = max_iterations

        self.tabu_tenure = tabu_tenure

        self.noise_prob = noise_prob

        

        # 找出所有变量

        self.all_vars = set()

        for clause in clauses:

            for lit in clause:

                self.all_vars.add(abs(lit))

        

        # 记录每个变量出现在哪些子句中

        self.var_to_clauses: Dict[int, List[Set[int]]] = {v: [] for v in self.all_vars}

        for clause in clauses:

            for lit in clause:

                self.var_to_clauses[abs(lit)].append(clause)

    

    def random_assignment(self) -> Dict[int, bool]:

        """

        随机生成初始赋值

        

        Returns:

            随机赋值字典

        """

        return {var: random.choice([True, False]) for var in self.all_vars}

    

    def count_satisfied_clauses(self, assignment: Dict[int, bool]) -> int:

        """

        统计当前赋值满足的子句数量

        

        Args:

            assignment: 当前赋值

        

        Returns:

            满足的子句数

        """

        count = 0

        for clause in self.clauses:

            for lit in clause:

                var = abs(lit)

                if (lit > 0 and assignment.get(var)) or (lit < 0 and not assignment.get(var)):

                    count += 1

                    break

        return count

    

    def get_break_count(self, var: int, assignment: Dict[int, bool]) -> int:

        """

        计算翻转某变量会破坏多少个满足的子句

        

        Args:

            var: 要翻转的变量

            assignment: 当前赋值

        

        Returns:

            被破坏的子句数

        """

        break_count = 0

        current_value = assignment[var]

        

        for clause in self.var_to_clauses[var]:

            # 检查这个子句是否被当前赋值满足

            clause_satisfied = False

            for lit in clause:

                v = abs(lit)

                if (lit > 0 and assignment.get(v, False)) or (lit < 0 and not assignment.get(v, True)):

                    clause_satisfied = True

                    break

            

            if clause_satisfied:

                # 检查翻转后是否会破坏这个子句

                new_value = not current_value

                will_satisfy = False

                for lit in clause:

                    v = abs(lit)

                    val = new_value if v == var else assignment.get(v, False)

                    if (lit > 0 and val) or (lit < 0 and not val):

                        will_satisfy = True

                        break

                

                if not will_satisfy:

                    break_count += 1

        

        return break_count

    

    def gsat_step(self, assignment: Dict[int, bool], tabu_list: Dict[int, int]) -> Dict[int, bool]:

        """

        GSAT单步:选择最好或随机翻转

        

        Args:

            assignment: 当前赋值

            tabu_list: Tabu列表

        

        Returns:

            新赋值

        """

        best_var = None

        best_satisfied = self.count_satisfied_clauses(assignment)

        

        # 遍历所有变量,找出能最大化满足子句数的变量

        for var in self.all_vars:

            if var in tabu_list and tabu_list[var] > 0:

                continue  # 在Tabu列表中,跳过

            

            # 模拟翻转

            new_assignment = assignment.copy()

            new_assignment[var] = not new_assignment[var]

            satisfied = self.count_satisfied_clauses(new_assignment)

            

            if satisfied > best_satisfied:

                best_satisfied = satisfied

                best_var = var

        

        # 如果找到更好的翻转

        if best_var is not None:

            assignment[best_var] = not assignment[best_var]

            tabu_list[best_var] = self.tabu_tenure

        else:

            # 随机翻转(避免卡在局部最优)

            var = random.choice(list(self.all_vars))

            assignment[var] = not assignment[var]

            tabu_list[var] = self.tabu_tenure

        

        return assignment

    

    def walksat_step(self, assignment: Dict[int, bool], tabu_list: Dict[int, int]) -> Dict[int, bool]:

        """

        WalkSAT单步:从破坏最少的子句中随机选择翻转

        

        Args:

            assignment: 当前赋值

            tabu_list: Tabu列表

        

        Returns:

            新赋值

        """

        # 找出所有不满足的子句

        unsatisfied = []

        for clause in self.clauses:

            satisfied = False

            for lit in clause:

                var = abs(lit)

                if (lit > 0 and assignment.get(var, False)) or (lit < 0 and not assignment.get(var, True)):

                    satisfied = True

                    break

            if not satisfied:

                unsatisfied.append(clause)

        

        if not unsatisfied:

            return assignment

        

        # 随机选择一个不满足的子句

        clause = random.choice(unsatisfied)

        

        # 如果随机值小于噪声概率,则完全随机翻转

        if random.random() < self.noise_prob:

            var = random.choice([abs(lit) for lit in clause])

        else:

            # 选择破坏最少的变量

            min_break = float('inf')

            best_var = None

            

            for lit in clause:

                var = abs(lit)

                break_count = self.get_break_count(var, assignment)

                if break_count < min_break:

                    min_break = break_count

                    best_var = var

            

            var = best_var

        

        # 执行翻转

        if var not in tabu_list or tabu_list[var] == 0:

            assignment[var] = not assignment[var]

            tabu_list[var] = self.tabu_tenure

        

        return assignment

    

    def solve_gsat(self) -> Optional[Dict[int, bool]]:

        """

        使用GSAT+TABU求解

        

        Returns:

            满足赋值或None

        """

        for restart in range(100):  # 最多100次重启

            assignment = self.random_assignment()

            tabu_list = {var: 0 for var in self.all_vars}

            

            for _ in range(self.max_iterations):

                # 检查是否满足所有子句

                if self.count_satisfied_clauses(assignment) == len(self.clauses):

                    return assignment

                

                # GSAT步骤

                assignment = self.gsat_step(assignment, tabu_list)

                

                # 更新Tabu列表

                for var in tabu_list:

                    if tabu_list[var] > 0:

                        tabu_list[var] -= 1

            

            # 随机重启

            assignment = self.random_assignment()

        

        return None

    

    def solve_walksat(self) -> Optional[Dict[int, bool]]:

        """

        使用WalkSAT求解

        

        Returns:

            满足赋值或None

        """

        for restart in range(100):

            assignment = self.random_assignment()

            tabu_list = {var: 0 for var in self.all_vars}

            

            for _ in range(self.max_iterations):

                # 检查是否满足所有子句

                if self.count_satisfied_clauses(assignment) == len(self.clauses):

                    return assignment

                

                # WalkSAT步骤

                assignment = self.walksat_step(assignment, tabu_list)

                

                # 更新Tabu列表

                for var in tabu_list:

                    if tabu_list[var] > 0:

                        tabu_list[var] -= 1

            

            # 随机重启

            assignment = self.random_assignment()

        

        return None





def solve_gsat(clauses: List[Set[int]], max_iterations: int = 10000) -> Optional[Dict[int, bool]]:

    """GSAT求解入口"""

    solver = WalkSATSolver(clauses, max_iterations=max_iterations, tabu_tenure=10)

    return solver.solve_gsat()





def solve_walksat(clauses: List[Set[int]], max_iterations: int = 10000, noise: float = 0.5) -> Optional[Dict[int, bool]]:

    """WalkSAT求解入口"""

    solver = WalkSATSolver(clauses, max_iterations=max_iterations, noise_prob=noise)

    return solver.solve_walksat()





# 测试代码

if __name__ == "__main__":

    random.seed(42)  # 固定随机种子以便复现

    

    # 测试1: 简单公式

    test_clauses = [

        {1, 2},

        {-1, 3},

        {-2, -3},

        {1},

    ]

    

    print("测试1 - 简单SAT实例:")

    result = solve_gsat(test_clauses)

    print(f"  GSAT结果: {result}")

    result = solve_walksat(test_clauses)

    print(f"  WalkSAT结果: {result}")

    

    # 测试2: 较大实例

    test_clauses2 = [

        {1, 2, 3, 4},

        {-1, 5, 6},

        {-2, -5, 7},

        {-3, -6, -7},

        {1, -4},

        {8, 9},

        {-8, -9},

        {1, 8},

    ]

    

    print("\n测试2 - 中等实例:")

    result = solve_gsat(test_clauses2)

    print(f"  GSAT结果: {result}")

    result = solve_walksat(test_clauses2)

    print(f"  WalkSAT结果: {result}")

    

    # 测试3: 随机生成的较大实例

    def generate_random_sat(num_vars: int, num_clauses: int, clause_size: int = 3) -> List[Set[int]]:

        """生成随机SAT实例"""

        clauses = []

        for _ in range(num_clauses):

            clause = set()

            while len(clause) < clause_size:

                var = random.randint(1, num_vars)

                sign = random.choice([1, -1])

                clause.add(sign * var)

            clauses.append(clause)

        return clauses

    

    test_clauses3 = generate_random_sat(10, 50, 3)

    print("\n测试3 - 随机实例(10变量,50子句):")

    result = solve_walksat(test_clauses3, max_iterations=5000)

    print(f"  WalkSAT结果: {result}")

    

    print("\n所有测试完成!")

