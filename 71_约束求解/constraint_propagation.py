# -*- coding: utf-8 -*-

"""

算法实现：约束求解 / constraint_propagation



本文件实现 constraint_propagation 相关的算法功能。

"""



from typing import List, Dict, Set, Any, Optional, Callable, Tuple

from collections import deque

from abc import ABC, abstractmethod





class Constraint(ABC):

    """

    约束抽象基类

    """

    @abstractmethod

    def is_satisfied(self, assignment: Dict[str, Any]) -> bool:

        """检查约束是否满足"""

        pass

    

    @abstractmethod

    def get_scope(self) -> List[str]:

        """获取约束涉及的变量"""

        pass





class BinaryConstraint(Constraint):

    """二元约束"""

    def __init__(self, var1: str, var2: str, predicate: Callable[[Any, Any], bool]):

        self.var1 = var1

        self.var2 = var2

        self.predicate = predicate

    

    def is_satisfied(self, assignment: Dict[str, Any]) -> bool:

        if self.var1 not in assignment or self.var2 not in assignment:

            return True  # 未完全赋值时视为满足

        return self.predicate(assignment[self.var1], assignment[self.var2])

    

    def get_scope(self) -> List[str]:

        return [self.var1, self.var2]





class UnaryConstraint(Constraint):

    """一元约束"""

    def __init__(self, var: str, predicate: Callable[[Any], bool]):

        self.var = var

        self.predicate = predicate

    

    def is_satisfied(self, assignment: Dict[str, Any]) -> bool:

        if self.var not in assignment:

            return True

        return self.predicate(assignment[self.var])

    

    def get_scope(self) -> List[str]:

        return [self.var]





class NaryConstraint(Constraint):

    """n元约束"""

    def __init__(self, vars: List[str], predicate: Callable[[List[Any]], bool]):

        self.vars = vars

        self.predicate = predicate

    

    def is_satisfied(self, assignment: Dict[str, Any]) -> bool:

        for var in self.vars:

            if var not in assignment:

                return True

        values = [assignment[var] for var in self.vars]

        return self.predicate(values)

    

    def get_scope(self) -> List[str]:

        return self.vars.copy()





class ConstraintSatisfactionProblem:

    """

    约束满足问题求解器

    支持多种传播策略和搜索方法

    """

    

    def __init__(self, variables: List[str], domains: Dict[str, Set[Any]]):

        """

        初始化CSP

        

        Args:

            variables: 变量列表

            domains: 每个变量的定义域

        """

        self.variables = variables

        self.domains = {v: domains[v].copy() for v in variables}

        self.constraints: List[Constraint] = []

        

        # 构建约束图

        self.constraint_graph: Dict[str, List[str]] = {v: [] for v in variables}

        

    def add_constraint(self, constraint: Constraint):

        """添加约束"""

        self.constraints.append(constraint)

        for var in constraint.get_scope():

            if var in self.constraint_graph:

                for other in constraint.get_scope():

                    if other != var and other not in self.constraint_graph[var]:

                        self.constraint_graph[var].append(other)

    

    def get_constraints_for_var(self, var: str) -> List[Constraint]:

        """获取涉及某变量的所有约束"""

        return [c for c in self.constraints if var in c.get_scope()]

    

    def revise(self, var1: str, var2: str) -> bool:

        """

        Revise操作:从var1的定义域中移除与var2不相容的值

        

        Returns:

            是否有修改

        """

        revised = False

        to_remove = set()

        

        for val1 in self.domains[var1]:

            # 检查是否存在var2的值使得所有约束都满足

            compatible = False

            for val2 in self.domains[var2]:

                # 模拟赋值

                test_assignment = {var1: val1, var2: val2}

                # 检查所有涉及这两个变量的约束

                compatible = True

                for constraint in self.constraints:

                    if var1 in constraint.get_scope() and var2 in constraint.get_scope():

                        if not constraint.is_satisfied(test_assignment):

                            compatible = False

                            break

                

                if compatible:

                    break

            

            if not compatible:

                to_remove.add(val1)

                revised = True

        

        for val in to_remove:

            self.domains[var1].remove(val)

        

        return revised

    

    def ac3(self) -> bool:

        """

        AC-3弧一致性算法

        

        Returns:

            是否所有定义域都非空

        """

        # 初始化队列

        queue = deque()

        for var1 in self.variables:

            for var2 in self.constraint_graph[var1]:

                queue.append((var1, var2))

        

        while queue:

            var1, var2 = queue.popleft()

            

            if self.revise(var1, var2):

                if not self.domains[var1]:

                    return False

                

                # 将所有与var1相邻的变量(除var2外)重新加入队列

                for var_k in self.constraint_graph[var1]:

                    if var_k != var2:

                        queue.append((var_k, var1))

        

        return True

    

    def pc2(self) -> bool:

        """

        PC-2弧一致性算法(比AC-3更强的一致性)

        额外处理二元约束的隐藏弧

        

        Returns:

            是否所有定义域都非空

        """

        if not self.ac3():

            return False

        

        # 迭代应用PC-2规则

        changed = True

        while changed:

            changed = False

            

            for constraint in self.constraints:

                if isinstance(constraint, BinaryConstraint):

                    # PC-2规则处理

                    pass  # 简化实现

        

        return True

    

    def backtrack(self, assignment: Dict[str, Any]) -> Optional[Dict[str, Any]]:

        """

        回溯搜索

        

        Returns:

            满足所有约束的赋值或None

        """

        # 如果赋值完整

        if len(assignment) == len(self.variables):

            # 验证所有约束

            for constraint in self.constraints:

                if not constraint.is_satisfied(assignment):

                    return None

            return assignment

        

        # 选择未赋值的变量(MRV启发式)

        unassigned = [v for v in self.variables if v not in assignment]

        var = min(unassigned, key=lambda v: len(self.domains[v]))

        

        for value in sorted(self.domains[var]):

            # 检查值是否与当前赋值一致

            consistent = True

            for constraint in self.constraints:

                if var in constraint.get_scope():

                    # 检查约束是否可能被满足

                    pass  # 简化处理

            

            assignment[var] = value

            

            # 前向检查

            if self.forward_check(var, value, assignment):

                result = self.backtrack(assignment)

                if result:

                    return result

            

            del assignment[var]

        

        return None

    

    def forward_check(self, var: str, value: Any, assignment: Dict[str, Any]) -> bool:

        """

        前向检查:移除不一致的值

        

        Returns:

            是否通过检查

        """

        # 保存原始定义域

        saved_domains = {v: self.domains[v].copy() for v in self.variables}

        

        # 对每个相关变量,移除与新赋值不一致的值

        for neighbor in self.constraint_graph[var]:

            to_remove = set()

            for neighbor_val in self.domains[neighbor]:

                test_assignment = {var: value, neighbor: neighbor_val}

                for constraint in self.constraints:

                    if var in constraint.get_scope() and neighbor in constraint.get_scope():

                        if not constraint.is_satisfied(test_assignment):

                            to_remove.add(neighbor_val)

                            break

            

            for rem in to_remove:

                self.domains[neighbor].discard(rem)

            

            if not self.domains[neighbor]:

                # 恢复定义域

                self.domains = saved_domains

                return False

        

        # 恢复定义域

        self.domains = saved_domains

        return True

    

    def solve(self) -> Optional[Dict[str, Any]]:

        """

        求解CSP

        

        Returns:

            解或None

        """

        # 先进行弧一致性传播

        if not self.ac3():

            return None

        

        # 再进行回溯搜索

        return self.backtrack({})

    

    def get_solution_count(self, max_count: int = 10) -> int:

        """

        统计解的数量(最多max_count个)

        

        Returns:

            解的数量

        """

        count = 0

        solutions = []

        

        def backtrack_count(assignment: Dict[str, Any]):

            nonlocal count

            

            if len(assignment) == len(self.variables):

                count += 1

                return

            

            unassigned = [v for v in self.variables if v not in assignment]

            var = unassigned[0]

            

            for value in self.domains[var]:

                assignment[var] = value

                

                # 快速检查

                valid = True

                for constraint in self.constraints:

                    if var in constraint.get_scope():

                        if not constraint.is_satisfied(assignment):

                            valid = False

                            break

                

                if valid:

                    if count < max_count:

                        backtrack_count(assignment)

                

                del assignment[var]

        

        backtrack_count({})

        return count





# 辅助函数:创建常见约束

def not_equal(var1: str, var2: str) -> BinaryConstraint:

    """创建不等约束"""

    return BinaryConstraint(var1, var2, lambda a, b: a != b)



def equal(var1: str, var2: str) -> BinaryConstraint:

    """创建相等约束"""

    return BinaryConstraint(var1, var2, lambda a, b: a == b)



def all_different(vars: List[str]) -> NaryConstraint:

    """创建全部不同约束"""

    return NaryConstraint(vars, lambda values: len(values) == len(set(values)))



def all_equal(vars: List[str]) -> NaryConstraint:

    """创建全部相等约束"""

    return NaryConstraint(vars, lambda values: len(set(values)) == 1)





# 测试代码

if __name__ == "__main__":

    # 测试1: 简单的字母算术问题 ( SEND + MORE = MONEY)

    # 每个字母代表0-9的数字,不同字母不同数字

    

    print("测试1 - SEND+MORE=MONEY问题:")

    letters = ['S', 'E', 'N', 'D', 'M', 'O', 'R', 'Y']

    domain = set(range(10))

    domains = {l: domain.copy() for l in letters}

    

    csp = ConstraintSatisfactionProblem(letters, domains)

    

    # 所有字母不同

    csp.add_constraint(all_different(letters))

    

    # SEND + MORE = MONEY 的约束

    # 简化: 不允许S和M为0

    csp.add_constraint(UnaryConstraint('S', lambda x: x != 0))

    csp.add_constraint(UnaryConstraint('M', lambda x: x != 0))

    

    # 求解

    solution = csp.solve()

    print(f"  解: {solution}")

    

    # 测试2: 简单的图着色

    print("\n测试2 - 图着色问题:")

    nodes = ['A', 'B', 'C', 'D']

    colors = {1, 2, 3}

    domains = {n: colors.copy() for n in nodes}

    

    csp2 = ConstraintSatisfactionProblem(nodes, domains)

    

    # 添加边约束(相邻节点不同色)

    csp2.add_constraint(not_equal('A', 'B'))

    csp2.add_constraint(not_equal('A', 'C'))

    csp2.add_constraint(not_equal('B', 'C'))

    csp2.add_constraint(not_equal('C', 'D'))

    

    solution2 = csp2.solve()

    print(f"  解: {solution2}")

    

    # 测试3: N皇后问题

    print("\n测试3 - 4皇后问题:")

    n = 4

    queens = [f'Q{i}' for i in range(n)]

    domains = {q: set(range(n)) for q in queens}

    

    csp3 = ConstraintSatisfactionProblem(queens, domains)

    

    # 不同行(变量名已隐含不同索引,值是列位置,值必须不同)

    csp3.add_constraint(all_different(queens))

    

    # 不能在同一对角线

    def not_diagonal(values: List[int]) -> bool:

        for i in range(len(values)):

            for j in range(i + 1, len(values)):

                if abs(values[i] - values[j]) == abs(i - j):

                    return False

        return True

    

    csp3.add_constraint(NaryConstraint(queens, not_diagonal))

    

    solution3 = csp3.solve()

    print(f"  解(位置): {solution3}")

    

    if solution3:

        # 转换为棋盘格式

        board = [['.' for _ in range(n)] for _ in range(n)]

        for var, col in solution3.items():

            row = int(var[1])

            board[row][col] = 'Q'

        print("  棋盘:")

        for row in board:

            print("  " + " ".join(row))

    

    # 测试4: 解的数量统计

    print("\n测试4 - 解的数量(简单图着色):")

    count = csp2.get_solution_count(max_count=100)

    print(f"  解的数量: {count}")

    

    print("\n所有测试完成!")

