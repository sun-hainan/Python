# -*- coding: utf-8 -*-

"""

算法实现：约束求解 / dpll_algorithm



本文件实现 dpll_algorithm 相关的算法功能。

"""



from typing import List, Dict, Optional, Set, Tuple





def unit_propagate(clauses: List[Set[int]], assignment: Dict[int, bool]) -> Tuple[List[Set[int]], Dict[int, bool]]:

    """

    单元传播:如果一个子句只有一个未赋值的文字,则该文字必须为真

    持续传播直到没有单元子句为止

    

    Args:

        clauses: 子句列表,每个子句是一个文字集合(整数,正负表示真假)

        assignment: 当前变量的赋值字典 {var: True/False}

    

    Returns:

        传播后的子句集和赋值

    """

    # 持续传播,直到没有新的单元子句

    while True:

        changed = False

        new_clauses = []

        

        for clause in clauses:

            # 过滤掉被满足的子句(包含真文字的子句)

            satisfied_literals = [lit for lit in clause if (lit > 0 and assignment.get(lit, None) == True) or (lit < 0 and assignment.get(-lit, None) == False)]

            if satisfied_literals:

                continue

            

            # 找出未赋值的文字

            unassigned = [lit for lit in clause if lit > 0 and lit not in assignment or lit < 0 and -lit not in assignment]

            

            # 如果子句为空(所有文字都为假),则冲突

            if not unassigned:

                return [], {}

            

            # 单元子句:只有一个未赋值文字

            if len(unassigned) == 1:

                lit = unassigned[0]

                var = abs(lit)

                val = lit > 0

                # 如果该变量已有相反赋值,则冲突

                if var in assignment and assignment[var] != val:

                    return [], {}

                assignment[var] = val

                changed = True

            else:

                new_clauses.append(set(unassigned))

        

        clauses = new_clauses

        if not changed:

            break

    

    return clauses, assignment





def pure_literal_assign(clauses: List[Set[int]], assignment: Dict[int, bool]) -> Tuple[List[Set[int]], Dict[int, bool]]:

    """

    纯文字传播:如果一个文字在所有子句中只以单一极性出现,

    则该文字可以设为真(正文字)或假(负文字)

    

    Args:

        clauses: 子句列表

        assignment: 当前赋值

    

    Returns:

        传播后的子句集和赋值

    """

    # 统计每个变量的正负出现次数

    pos_count = {}  # 变量 -> 正文字出现次数

    neg_count = {}  # 变量 -> 负文字出现次数

    

    for clause in clauses:

        for lit in clause:

            var = abs(lit)

            if lit > 0:

                pos_count[var] = pos_count.get(var, 0) + 1

            else:

                neg_count[var] = neg_count.get(var, 0) + 1

    

    # 找出纯文字并赋值

    all_vars = set(pos_count.keys()) | set(neg_count.keys())

    for var in all_vars:

        if var in assignment:

            continue

        pos = pos_count.get(var, 0)

        neg = neg_count.get(var, 0)

        

        if pos > 0 and neg == 0:  # 纯正文字

            assignment[var] = True

        elif neg > 0 and pos == 0:  # 纯负文字

            assignment[var] = False

    

    return clauses, assignment





def dpll(clauses: List[Set[int]], assignment: Optional[Dict[int, bool]] = None) -> Optional[Dict[int, bool]]:

    """

    DPLL递归求解SAT问题

    

    Args:

        clauses: CNF公式的子句列表

        assignment: 当前部分赋值

    

    Returns:

        满足赋值(如果存在),否则None

    """

    if assignment is None:

        assignment = {}

    

    # 单元传播

    clauses, assignment = unit_propagate(clauses, assignment)

    if clauses is None:  # 冲突

        return None

    if not clauses:  # 所有子句都满足

        return assignment

    

    # 纯文字传播

    clauses, assignment = pure_literal_assign(clauses, assignment)

    if not clauses:  # 所有子句都满足

        return assignment

    

    # 选择一个未赋值的变量(最简单的选择策略:选择第一个出现的变量)

    all_vars = set()

    for clause in clauses:

        for lit in clause:

            all_vars.add(abs(lit))

    

    unassigned = [v for v in all_vars if v not in assignment]

    if not unassigned:  # 所有变量都已赋值

        return assignment

    

    var = unassigned[0]

    

    # 尝试将变量设为True

    new_assignment = assignment.copy()

    new_assignment[var] = True

    new_clauses = [clause.copy() for clause in clauses]

    result = dpll(new_clauses, new_assignment)

    if result is not None:

        return result

    

    # 尝试将变量设为False

    new_assignment = assignment.copy()

    new_assignment[var] = False

    new_clauses = [clause.copy() for clause in clauses]

    return dpll(new_clauses, new_assignment)





def parse_cnf(filename: str) -> List[Set[int]]:

    """

    解析CNF文件的简化格式(不含前缀行)

    每行是一个子句,数字用空格分隔,正数表示正文字,负数表示负文字,0表示子句结束

    

    Args:

        filename: CNF文件名

    

    Returns:

        子句列表

    """

    clauses = []

    with open(filename, 'r') as f:

        for line in f:

            line = line.strip()

            if not line or line.startswith('c'):

                continue

            if line.startswith('p'):

                continue

            parts = list(map(int, line.split()))

            clause = set()

            for p in parts:

                if p == 0:

                    break

                clause.add(p)

            if clause:

                clauses.append(clause)

    return clauses





def solve_sat(clauses: List[Set[int]]) -> Optional[Dict[int, bool]]:

    """

    SAT求解的入口函数

    

    Args:

        clauses: CNF公式

    

    Returns:

        满足赋值或None

    """

    return dpll(clauses)





# 测试代码

if __name__ == "__main__":

    # 测试1: 简单公式 (x1 OR x2) AND (NOT x1 OR x3) AND (NOT x2 OR NOT x3) AND x1

    # 期望: x1=True, x2=False, x3=False

    test_clauses = [

        {1, 2},           # x1 OR x2

        {-1, 3},          # NOT x1 OR x3

        {-2, -3},         # NOT x2 OR NOT x3

        {1},              # x1

    ]

    

    result = solve_sat(test_clauses)

    print("测试1 - 简单SAT实例:")

    print(f"  子句: {test_clauses}")

    print(f"  结果: {result}")

    

    # 测试2: 另一个简单公式

    # (x1 OR x2) AND (NOT x1 OR x2) AND (NOT x2)

    # 期望: x1=False, x2=False

    test_clauses2 = [

        {1, 2},

        {-1, 2},

        {-2}

    ]

    

    result2 = solve_sat(test_clauses2)

    print("\n测试2:")

    print(f"  子句: {test_clauses2}")

    print(f"  结果: {result2}")

    

    # 测试3: 不可满足的例子

    # x1 AND NOT x1

    test_clauses3 = [

        {1},

        {-1}

    ]

    

    result3 = solve_sat(test_clauses3)

    print("\n测试3 - 不可满足:")

    print(f"  子句: {test_clauses3}")

    print(f"  结果: {result3}")

    

    # 测试4: 3-SAT例子

    # (x1 OR x2 OR x3) AND (NOT x1 OR x2 OR NOT x3) AND (x1 OR NOT x2 OR x3)

    test_clauses4 = [

        {1, 2, 3},

        {-1, 2, -3},

        {1, -2, 3}

    ]

    

    result4 = solve_sat(test_clauses4)

    print("\n测试4 - 3-SAT:")

    print(f"  子句: {test_clauses4}")

    print(f"  结果: {result4}")

    

    print("\n所有测试完成!")

