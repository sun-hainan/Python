# -*- coding: utf-8 -*-

"""

算法实现：约束求解 / arc_consistency



本文件实现 arc_consistency 相关的算法功能。

"""



from typing import Dict, List, Set, Any, Tuple, Optional

from collections import deque





class CSPSolver:

    """支持 AC-3 的 CSP 求解器"""

    

    def __init__(self, variables: List[str], domains: Dict[str, List[Any]]):

        self.variables = variables

        self.domains = {v: list(d) for v, d in domains.items()}

        self.constraints: Dict[str, List[Tuple[str, callable]]] = {v: [] for v in variables}

    

    def add_constraint(self, var1: str, var2: str, is_compatible: callable):

        """

        添加二元约束

        

        参数:

            var1: 变量1

            var2: 变量2

            is_compatible: 兼容性检查函数 (value1, value2) -> bool

        """

        self.constraints[var1].append((var2, is_compatible))

        self.constraints[var2].append((var1, lambda a, b: is_compatible(b, a)))

    

    def get_neighbors(self, var: str) -> List[str]:

        """获取与 var 相邻的所有变量"""

        return [neighbor for neighbor, _ in self.constraints[var]]

    

    def has_support(self, var: str, value: Any, neighbor: str) -> bool:

        """

        检查值是否有邻居的支持（存在兼容值）

        

        参数:

            var: 变量名

            value: 值

            neighbor: 邻居变量名

        

        返回:

            是否存在兼容的邻居值

        """

        for neighbor_value in self.domains[neighbor]:

            # 检查约束是否满足

            for _, check_func in self.constraints[var]:

                if check_func(value, neighbor_value):

                    return True

        return False

    

    def revise(self, var1: str, var2: str) -> bool:

        """

        修订 var1 的域，删除没有 var2 支持的值

        

        参数:

            var1: 要修订的变量

            var2: 邻居变量

        

        返回:

            是否有域值被删除

        """

        revised = False

        new_domain = []

        

        for value in self.domains[var1]:

            # 检查是否有 var2 中的值支持

            supported = False

            for neighbor_value in self.domains[var2]:

                # 检查 var1 和 var2 之间的约束

                for _, check_func in self.constraints[var1]:

                    if check_func(value, neighbor_value):

                        supported = True

                        break

                if supported:

                    break

            

            if supported:

                new_domain.append(value)

            else:

                revised = True

        

        self.domains[var1] = new_domain

        return revised

    

    def ac3(self) -> bool:

        """

        AC-3 主算法

        

        返回:

            是否成功（没有域为空）

        """

        # 初始化队列：所有弧 (Xi, Xj)

        queue = deque()

        for var in self.variables:

            for neighbor, _ in self.constraints[var]:

                queue.append((var, neighbor))

        

        while queue:

            var1, var2 = queue.popleft()

            

            # 修订 var1 的域

            if self.revise(var1, var2):

                # 如果 var1 域变为空，则失败

                if not self.domains[var1]:

                    return False

                

                # 将 var1 的其他邻居加入队列

                for neighbor, _ in self.constraints[var1]:

                    if neighbor != var2:

                        queue.append((neighbor, var1))

        

        return True

    

    def solve(self) -> Optional[Dict[str, Any]]:

        """

        求解 CSP（带 AC-3 预处理）

        

        返回:

            完整赋值或 None

        """

        # 运行 AC-3 约束传播

        if not self.ac3():

            return None  # 域为空，无解

        

        # 简单回溯求解

        return self._backtrack({})

    

    def _backtrack(self, assignment: Dict[str, Any]) -> Optional[Dict[str, Any]]:

        """带 AC-3 的回溯搜索"""

        if len(assignment) == len(self.variables):

            return assignment

        

        # 选择剩余值最少的变量

        var = min(

            [v for v in self.variables if v not in assignment],

            key=lambda v: len(self.domains[v])

        )

        

        for value in self.domains[var]:

            assignment[var] = value

            result = self._backtrack(assignment)

            if result is not None:

                return result

            del assignment[var]

        

        return None





def ac3(variables: List[str], 

       domains: Dict[str, List[Any]], 

       constraints: List[Tuple[str, str, callable]]) -> Dict[str, List[Any]]:

    """

    AC-3 约束传播算法（独立函数版本）

    

    参数:

        variables: 变量列表

        domains: 域字典

        constraints: 约束列表 [(var1, var2, check_func)]

    

    返回:

        传播后的域字典

    """

    # 构建邻接表

    neighbors: Dict[str, List[str]] = {v: [] for v in variables}

    constraint_map: Dict[Tuple[str, str], callable] = {}

    

    for var1, var2, check_func in constraints:

        neighbors[var1].append(var2)

        neighbors[var2].append(var1)

        constraint_map[(var1, var2)] = check_func

        constraint_map[(var2, var1)] = lambda a, b: check_func(b, a)

    

    # 复制域

    current_domains = {v: list(d) for v, d in domains.items()}

    

    # 初始化队列

    queue = deque()

    for var in variables:

        for neighbor in neighbors[var]:

            queue.append((var, neighbor))

    

    while queue:

        var1, var2 = queue.popleft()

        

        # 修订 var1 的域

        revised = False

        new_domain = []

        

        for value in current_domains[var1]:

            # 检查是否有 var2 的值支持

            has_support = False

            for neighbor_value in current_domains[var2]:

                check_func = constraint_map.get((var1, var2))

                if check_func and check_func(value, neighbor_value):

                    has_support = True

                    break

            

            if has_support:

                new_domain.append(value)

            else:

                revised = True

        

        if revised:

            current_domains[var1] = new_domain

            if not new_domain:

                return {}  # 失败

        

        if revised:

            for neighbor in neighbors[var1]:

                if neighbor != var2:

                    queue.append((neighbor, var1))

    

    return current_domains





# ============ 示例问题 ============



def create_map_coloring_csp() -> CSPSolver:

    """创建地图着色问题"""

    variables = ["WA", "NT", "SA", "Q", "NSW", "V", "T"]

    colors = ["红", "绿", "蓝"]

    domains = {v: colors.copy() for v in variables}

    

    csp = CSPSolver(variables, domains)

    

    # 添加约束：相邻区域不能同色

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





def create_sudoku_csp(board: List[List[int]]) -> CSPSolver:

    """

    创建数独 CSP

    

    参数:

        board: 9x9 棋盘，0 表示空格

    

    返回:

        CSP 实例

    """

    variables = []

    domains = {}

    

    for row in range(9):

        for col in range(9):

            var = f"R{row}C{col}"

            variables.append(var)

            

            if board[row][col] == 0:

                domains[var] = list(range(1, 10))

            else:

                domains[var] = [board[row][col]]

    

    csp = CSPSolver(variables, domains)

    

    # 行约束

    for row in range(9):

        for col1 in range(9):

            for col2 in range(col1 + 1, 9):

                csp.add_constraint(

                    f"R{row}C{col1}", f"R{row}C{col2}",

                    lambda a, b: a != b

                )

    

    # 列约束

    for col in range(9):

        for row1 in range(9):

            for row2 in range(row1 + 1, 9):

                csp.add_constraint(

                    f"R{row1}C{col}", f"R{row2}C{col}",

                    lambda a, b: a != b

                )

    

    # 3x3 宫约束

    for box_row in range(3):

        for box_col in range(3):

            cells = []

            for r in range(box_row * 3, box_row * 3 + 3):

                for c in range(box_col * 3, box_col * 3 + 3):

                    cells.append((r, c))

            

            for i in range(len(cells)):

                for j in range(i + 1, len(cells)):

                    r1, c1 = cells[i]

                    r2, c2 = cells[j]

                    csp.add_constraint(

                        f"R{r1}C{c1}", f"R{r2}C{c2}",

                        lambda a, b: a != b

                    )

    

    return csp





if __name__ == "__main__":

    print("=" * 60)

    print("测试1 - 地图着色问题")

    print("=" * 60)

    

    csp = create_map_coloring_csp()

    result = csp.solve()

    

    if result:

        print("  找到解:")

        for var in sorted(result.keys()):

            print(f"    {var}: {result[var]}")

    else:

        print("  未找到解")

    

    print()

    print("=" * 60)

    print("测试2 - 数独 (简单开局)")

    print("=" * 60)

    

    # 简单数独

    sudoku_board = [

        [5, 3, 0, 0, 7, 0, 0, 0, 0],

        [6, 0, 0, 1, 9, 5, 0, 0, 0],

        [0, 9, 8, 0, 0, 0, 0, 6, 0],

        [8, 0, 0, 0, 6, 0, 0, 0, 3],

        [4, 0, 0, 8, 0, 3, 0, 0, 1],

        [7, 0, 0, 0, 2, 0, 0, 0, 6],

        [0, 6, 0, 0, 0, 0, 2, 8, 0],

        [0, 0, 0, 4, 1, 9, 0, 0, 5],

        [0, 0, 0, 0, 8, 0, 0, 7, 9]

    ]

    

    csp = create_sudoku_csp(sudoku_board)

    result = csp.solve()

    

    if result:

        print("  解:")

        for row in range(9):

            row_values = []

            for col in range(9):

                var = f"R{row}C{col}"

                row_values.append(str(result[var]))

            print("    " + " ".join(row_values[i] if i % 3 != 2 else row_values[i] + " |" for i in range(9)))

            if row == 2 or row == 5:

                print("    " + "-" * 21)

    else:

        print("  未找到解")

    

    print()

    print("=" * 60)

    print("复杂度分析:")

    print("=" * 60)

    print("  AC-3 时间复杂度: O(e × d³)")

    print("    e = 弧(约束)数量")

    print("    d = 域大小")

    print("  AC-3 空间复杂度: O(e)")

    print("  改进:")

    print("    - AC-4: 更精确但更复杂")

    print("    - AC-6: 处理高阶约束")

