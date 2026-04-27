# -*- coding: utf-8 -*-

"""

算法实现：约束求解 / cdcl_sat



本文件实现 cdcl_sat 相关的算法功能。

"""



from typing import List, Set, Dict, Optional, Tuple

from collections import defaultdict





class CDCLSolver:

    """CDCL SAT 求解器"""

    

    def __init__(self, clauses: List[Set[int]]):

        """

        初始化求解器

        

        参数:

            clauses: CNF 子句列表

        """

        self.original_clauses = [c.copy() for c in clauses]  # 原始子句（不删除）

        self.clauses = [c.copy() for c in clauses]  # 当前工作子句

        self.num_vars = self._count_vars()

        

        # 决策层级

        self.decision_level = 0

        

        # 变量赋值: {var: value}

        self.assignment: Dict[int, bool] = {}

        

        # 变量层级: {var: decision_level}

        self.var_level: Dict[int, int] = {}

        

        # 变量来源（用于冲突分析）: {var: clause}

        self.var_reason: Dict[int, Optional[Set[int]]] = {}

        

        # 活动度（用于 VSIDS 启发式）

        self.var_activity: Dict[int, int] = defaultdict(int)

        

        # 学习的子句数量

        self.learned_count = 0

        

        # 冲突次数

        self.conflict_count = 0

    

    def _count_vars(self) -> int:

        """统计变量数量"""

        max_var = 0

        for clause in self.clauses:

            for lit in clause:

                max_var = max(max_var, abs(lit))

        return max_var

    

    def _literal_value(self, literal: int) -> Optional[bool]:

        """

        获取文字的值

        

        参数:

            literal: 文字（正=正文字，负=负文字）

        

        返回:

            True/False（已赋值），None（未赋值）

        """

        var = abs(literal)

        if var not in self.assignment:

            return None

        value = self.assignment[var]

        return value if literal > 0 else not value

    

    def _is_satisfied(self, clause: Set[int]) -> bool:

        """检查子句是否满足"""

        for literal in clause:

            if self._literal_value(literal):

                return True

        return False

    

    def _is_conflicting(self, clause: Set[int]) -> bool:

        """检查子句是否冲突（所有文字都为假）"""

        if not clause:

            return True

        for literal in clause:

            if self._literal_value(literal) is None:

                return False  # 还有未赋值的文字

        return True  # 所有文字都已赋值且为假

    

    def _get_unit_literal(self, clause: Set[int]) -> Optional[int]:

        """

        获取单元子句的唯一未赋值文字

        

        返回:

            单元文字，如果没有则为 None

        """

        unassigned = []

        for literal in clause:

            val = self._literal_value(literal)

            if val is True:

                return None  # 子句已满足

            if val is None:

                unassigned.append(literal)

        

        if len(unassigned) == 1:

            return unassigned[0]

        return None

    

    def _unit_propagate(self) -> Optional[Set[int]]:

        """

        单元传播

        

        返回:

            冲突子句（如果有），否则 None

        """

        while True:

            conflict = None

            for clause in self.clauses:

                if self._is_satisfied(clause):

                    continue

                if self._is_conflicting(clause):

                    return clause  # 冲突

                

                unit_lit = self._get_unit_literal(clause)

                if unit_lit is not None:

                    var = abs(unit_lit)

                    value = unit_lit > 0

                    

                    # 如果变量已有赋值且冲突

                    if var in self.assignment and self.assignment[var] != value:

                        return clause

                    

                    # 执行赋值

                    self.assignment[var] = value

                    self.var_level[var] = self.decision_level

                    self.var_reason[var] = clause

                    

                    # 增加活动度

                    self.var_activity[var] += 1

            

            if conflict:

                break

            

            # 检查是否还有新的单元子句

            new_unit = False

            for clause in self.clauses:

                if not self._is_satisfied(clause) and not self._is_conflicting(clause):

                    unit_lit = self._get_unit_literal(clause)

                    if unit_lit is not None:

                        new_unit = True

                        break

            

            if not new_unit:

                break

        

        return None

    

    def _choose_literal(self) -> int:

        """

        选择决策文字（VSIDS 启发式）

        

        返回:

            被选中的文字

        """

        # VSIDS: 优先选择活动度高的变量

        best_var = None

        best_activity = -1

        

        for clause in self.clauses:

            for literal in clause:

                var = abs(literal)

                if var not in self.assignment:

                    if self.var_activity[var] > best_activity:

                        best_activity = self.var_activity[var]

                        best_var = var

        

        if best_var is None:

            return 0

        

        # 随机选择符号

        return best_var if random.choice([True, False]) else -best_var

    

    def _analyze_conflict(self, conflict_clause: Set[int]) -> Tuple[Set[int], int]:

        """

        冲突分析

        

        参数:

            conflict_clause: 冲突子句

        

        返回:

            (学习子句, 回跳层级)

        """

        self.conflict_count += 1

        

        # 简化冲突分析

        learned = conflict_clause.copy()

        backtrack_level = 0

        

        # 找出决策层级最高的变量

        for literal in learned:

            var = abs(literal)

            if var in self.var_level:

                backtrack_level = max(backtrack_level, self.var_level[var])

        

        # 回跳到下一个层级

        backtrack_level = max(0, backtrack_level - 1)

        

        return learned, backtrack_level

    

    def _backtrack(self, level: int):

        """

        回跳到指定层级

        

        参数:

            level: 目标层级

        """

        # 删除指定层级以上的赋值

        to_remove = [v for v, lvl in self.var_level.items() if lvl > level]

        for var in to_remove:

            del self.assignment[var]

            del self.var_level[var]

            if var in self.var_reason:

                del self.var_reason[var]

        

        self.decision_level = level

    

    def _add_learned_clause(self, clause: Set[int]):

        """添加学习子句"""

        self.clauses.append(clause)

        self.learned_count += 1

    

    def solve(self) -> Optional[Dict[int, bool]]:

        """

        CDCL 主求解循环

        

        返回:

            满足赋值或 None

        """

        import random

        

        while True:

            # 单元传播

            conflict = self._unit_propagate()

            

            if conflict is not None:

                # 冲突分析

                if self.decision_level == 0:

                    return None  # 顶层冲突，无法解决

                

                learned, backtrack_level = self._analyze_conflict(conflict)

                self._add_learned_clause(learned)

                self._backtrack(backtrack_level)

            else:

                # 检查是否所有变量都已赋值

                if len(self.assignment) == self.num_vars:

                    return self.assignment

                

                # 检查是否还有未满足的子句

                all_satisfied = all(self._is_satisfied(c) for c in self.clauses)

                if all_satisfied:

                    return self.assignment

                

                # 决策：选择一个变量赋值

                self.decision_level += 1

                literal = self._choose_literal()

                

                if literal == 0:

                    return self.assignment

                

                var = abs(literal)

                value = literal > 0

                

                self.assignment[var] = value

                self.var_level[var] = self.decision_level

                self.var_reason[var] = None  # 决策变量





def cdcl_solve(clauses: List[Set[int]]) -> Optional[Dict[int, bool]]:

    """

    CDCL 求解器入口

    

    参数:

        clauses: CNF 子句列表

    

    返回:

        满足赋值或 None

    """

    if not clauses:

        return {}

    

    solver = CDCLSolver(clauses)

    return solver.solve()





if __name__ == "__main__":

    import random

    

    # 测试用例 1：简单可满足实例

    test_clauses = [

        {1, 2},

        {-1, 3},

        {-2, 3}

    ]

    

    print("测试1 - CDCL 简单实例:")

    print(f"  公式: (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ x3)")

    

    result = cdcl_solve(test_clauses)

    print(f"  结果: {result}")

    

    if result:

        for clause in test_clauses:

            satisfied = any(

                (lit > 0 and result[abs(lit)]) or (lit < 0 and not result[abs(lit)])

                for lit in clause

            )

            print(f"    子句 {clause} 满足: {satisfied}")

    

    print()

    

    # 测试用例 2：不可满足实例

    test_unsat = [

        {1, 2},

        {-1, 2},

        {1, -2},

        {-1, -2}

    ]

    

    print("测试2 - 不可满足实例:")

    print(f"  公式: (x1 ∨ x2) ∧ (¬x1 ∨ x2) ∧ (x1 ∨ ¬x2) ∧ (¬x1 ∨ ¬x2)")

    print(f"  结果: {cdcl_solve(test_unsat)}")

    

    print()

    

    # 测试用例 3：较大实例

    random.seed(42)

    print("测试3 - 较大随机实例 (10 变量):")

    

    # 生成一个随机但可满足的实例

    true_assignment = {i: random.choice([True, False]) for i in range(1, 11)}

    

    large_clauses = []

    for _ in range(30):

        clause = set()

        for _ in range(3):

            var = random.randint(1, 10)

            lit = var if true_assignment[var] else -var

            clause.add(lit)

        large_clauses.append(clause)

    

    result = cdcl_solve(large_clauses)

    print(f"  子句数: 30, 变量数: 10")

    print(f"  结果: {result is not None}")

    

    if result:

        # 验证

        all_sat = all(

            any((lit > 0 and result[abs(lit)]) or (lit < 0 and not result[abs(lit)])

                for lit in clause)

            for clause in large_clauses

        )

        print(f"  验证通过: {all_sat}")

    

    print()

    print("=" * 50)

    print("复杂度分析:")

    print("  时间复杂度: 最坏指数级，实际平均多项式")

    print("  空间复杂度: O(n + m + learned)")

    print("  优势: 通过子句学习避免重复搜索相似空间")

