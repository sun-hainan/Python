# -*- coding: utf-8 -*-

"""

算法实现：约束求解 / backtracking_search



本文件实现 backtracking_search 相关的算法功能。

"""



from typing import Dict, List, Set, Tuple, Optional, Any





# 约束类型别名：(变量1, 变量2) -> 是否相容

Constraint = Tuple[str, str, callable]  # (var1, var2, is_compatible_func)





class CSP:

    """

    约束满足问题

    

    属性:

        variables: 变量列表

        domains: 变量域字典 {变量名: [值列表]}

        constraints: 约束列表 [(变量1, 变量2, 检查函数)]

    """

    

    def __init__(self, variables: List[str], domains: Dict[str, List[Any]]):

        self.variables = variables

        self.domains = domains

        self.constraints: Dict[str, List[Tuple[str, callable]]] = {v: [] for v in variables}

    

    def add_constraint(self, var1: str, var2: str, is_compatible: callable):

        """

        添加二元约束

        

        参数:

            var1: 变量1

            var2: 变量2

            is_compatible: 检查函数 (value1, value2) -> bool

        """

        self.constraints[var1].append((var2, is_compatible))

        self.constraints[var2].append((var1, lambda a, b: is_compatible(b, a)))

    

    def is_consistent(self, var: str, value: Any, assignment: Dict[str, Any]) -> bool:

        """

        检查变量赋值是否与已有赋值一致

        

        参数:

            var: 变量名

            value: 候选值

            assignment: 当前部分赋值

        

        返回:

            是否一致

        """

        for neighbor, check_func in self.constraints[var]:

            if neighbor in assignment:

                if not check_func(value, assignment[neighbor]):

                    return False

        return True

    

    def get_neighbors(self, var: str) -> List[str]:

        """获取与变量相邻的所有变量"""

        return [neighbor for neighbor, _ in self.constraints[var]]





def select_unassigned_variable(csp: CSP, assignment: Dict[str, Any]) -> Optional[str]:

    """

    MRV 启发式：选择受限最多的变量

    

    参数:

        csp: CSP 实例

        assignment: 当前赋值

    

    返回:

        未赋值的变量中域最小的那个

    """

    unassigned = [v for v in csp.variables if v not in assignment]

    if not unassigned:

        return None

    

    # 选择剩余合法值最少的变量（MRV 启发式）

    def count_legal_values(var):

        count = 0

        for value in csp.domains[var]:

            if csp.is_consistent(var, value, assignment):

                count += 1

        return count

    

    return min(unassigned, key=count_legal_values)





def order_domain_values(var: str, csp: CSP, assignment: Dict[str, Any]) -> List[Any]:

    """

    值排序：对变量所有可能取值排序

    

    参数:

        var: 变量名

        csp: CSP 实例

        assignment: 当前赋值

    

    返回:

        排序后的值列表

    """

    return list(csp.domains[var])





def forward_checking(csp: CSP, var: str, value: Any, assignment: Dict[str, Any]) -> bool:

    """

    前向检验：检查赋值是否会导致邻居无合法值

    

    参数:

        csp: CSP 实例

        var: 已赋值的变量

        value: 赋予的值

        assignment: 当前部分赋值

    

    返回:

        是否通过检验

    """

    for neighbor, _ in csp.constraints[var]:

        if neighbor not in assignment:

            # 检查邻居的每个值是否与当前赋值兼容

            has_legal = False

            for neighbor_value in csp.domains[neighbor]:

                if csp.is_consistent(neighbor, neighbor_value, assignment):

                    has_legal = True

                    break

            if not has_legal:

                return False

    return True





def backtracking_search(csp: CSP, assignment: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:

    """

    回溯搜索主算法

    

    参数:

        csp: CSP 实例

        assignment: 当前部分赋值

    

    返回:

        完整赋值（成功）或 None（失败）

    """

    if assignment is None:

        assignment = {}

    

    # 检查是否所有变量都已赋值

    if len(assignment) == len(csp.variables):

        return assignment

    

    # 选择变量

    var = select_unassigned_variable(csp, assignment)

    if var is None:

        return assignment

    

    # 尝试每个值

    for value in order_domain_values(var, csp, assignment):

        # 检查约束是否满足

        if csp.is_consistent(var, value, assignment):

            assignment[var] = value

            

            # 前向检验

            if forward_checking(csp, var, value, assignment):

                # 递归求解

                result = backtracking_search(csp, assignment)

                if result is not None:

                    return result

            

            # 回溯：撤销赋值

            del assignment[var]

    

    return None





def ac3_constraint_propagation(csp: CSP, assignment: Dict[str, Any]) -> bool:

    """

    AC-3 约束传播（简化版本）

    

    参数:

        csp: CSP 实例

        assignment: 当前部分赋值

    

    返回:

        是否仍有合法赋值

    """

    # 待处理队列：(变量1, 变量2)

    queue = []

    for var in csp.variables:

        for neighbor, _ in csp.constraints[var]:

            if neighbor not in assignment:

                queue.append((var, neighbor))

    

    while queue:

        var1, var2 = queue.pop(0)

        

        # 检查 var1 的值是否都有对应的 var2 合法值

        changed = False

        new_domain = []

        

        for val1 in csp.domains[var1]:

            # 检查是否有兼容的 val2

            has_support = False

            for val2 in csp.domains[var2]:

                if csp.is_consistent(var1, val1, {var2: val2}):

                    has_support = True

                    break

            

            if has_support:

                new_domain.append(val1)

            else:

                changed = True

        

        if changed:

            csp.domains[var1] = new_domain

            if not new_domain:

                return False  # 域为空，失败

    

    return True





def backtracking_with_ac3(csp: CSP, assignment: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:

    """

    带 AC-3 约束传播的回溯搜索

    

    参数:

        csp: CSP 实例

        assignment: 当前部分赋值

    

    返回:

        完整赋值或 None

    """

    if assignment is None:

        assignment = {}

    

    # 检查是否所有变量都已赋值

    if len(assignment) == len(csp.variables):

        return assignment

    

    # 选择变量

    var = select_unassigned_variable(csp, assignment)

    if var is None:

        return assignment

    

    # 尝试每个值

    for value in order_domain_values(var, csp, assignment):

        if csp.is_consistent(var, value, assignment):

            assignment[var] = value

            

            # 记录原始域以支持回溯

            original_domains = {v: csp.domains[v].copy() for v in csp.variables}

            

            # AC-3 传播

            if forward_checking(csp, var, value, assignment):

                result = backtracking_with_ac3(csp, assignment)

                if result is not None:

                    return result

            

            # 恢复域

            for v, dom in original_domains.items():

                csp.domains[v] = dom

            

            del assignment[var]

    

    return None





# ============ 示例问题 ============



def create_n_queens_csp(n: int) -> CSP:

    """

    创建 N 皇后问题 CSP

    

    参数:

        n: 皇后数量

    

    返回:

        CSP 实例

    """

    variables = [f"Q{i}" for i in range(n)]

    domains = {v: list(range(n)) for v in variables}

    

    csp = CSP(variables, domains)

    

    # 添加约束：同一行不能有皇后

    # 同一列不能有两个皇后

    for i in range(n):

        for j in range(i + 1, n):

            # 不能在同一列

            csp.add_constraint(f"Q{i}", f"Q{j}", lambda a, b: a != b)

    

    return csp





def create_map_coloring_csp() -> CSP:

    """创建地图着色问题 CSP（澳大利亚地图）"""

    variables = ["WA", "NT", "SA", "Q", "NSW", "V", "T"]

    domains = {v: ["红", "绿", "蓝"] for v in variables}

    

    csp = CSP(variables, domains)

    

    # 添加邻居约束

    neighbors = [

        ("WA", "NT"), ("WA", "SA"),

        ("NT", "SA"), ("NT", "Q"),

        ("SA", "Q"), ("SA", "NSW"), ("SA", "V"),

        ("Q", "NSW"),

        ("NSW", "V")

    ]

    

    for v1, v2 in neighbors:

        csp.add_constraint(v1, v2, lambda a, b: a != b)

    

    return csp





if __name__ == "__main__":

    print("=" * 60)

    print("测试1 - 地图着色问题 (澳大利亚)")

    print("=" * 60)

    

    csp = create_map_coloring_csp()

    result = backtracking_search(csp)

    

    if result:

        print("  找到解:")

        for var in sorted(result.keys()):

            print(f"    {var}: {result[var]}")

    else:

        print("  未找到解")

    

    print()

    print("=" * 60)

    print("测试2 - N 皇后问题")

    print("=" * 60)

    

    for n in [4, 8, 10]:

        csp = create_n_queens_csp(n)

        result = backtracking_search(csp)

        

        if result:

            print(f"  {n}皇后: 找到解")

            # 可视化

            board = [["." for _ in range(n)] for _ in range(n)]

            for var, col in result.items():

                row = int(var[1:])

                board[row][col] = "Q"

            for row in board:

                print("    " + " ".join(row))

        else:

            print(f"  {n}皇后: 未找到解")

        print()

    

    print("=" * 60)

    print("复杂度分析:")

    print("=" * 60)

    print("  时间复杂度: 最坏 O(d^n)，d=域大小，n=变量数")

    print("  空间复杂度: O(n) 递归栈深度")

    print("  优化:")

    print("    - MRV 启发式: 减少分支因子")

    print("    - 前向检验: 提前检测失败")

    print("    - AC-3: 全局约束传播")

