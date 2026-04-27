# -*- coding: utf-8 -*-

"""

算法实现：程序分析 / dataflow_available_expressions



本文件实现 dataflow_available_expressions 相关的算法功能。

"""



from typing import Dict, List, Set, Tuple, Optional

from collections import defaultdict





class Expression:

    """

    表达式类

    

    表示一个算术表达式，用于可用表达式分析。

    """

    

    def __init__(self, op: str, left: str, right: str):

        """

        初始化表达式

        

        Args:

            op: 运算符

            left: 左操作数

            right: 右操作数

        """

        self.op = op

        self.left = left

        self.right = right

    

    def __str__(self) -> str:

        return f"({self.left} {self.op} {self.right})"

    

    def __repr__(self) -> str:

        return f"Expr({self.left} {self.op} {self.right})"

    

    def __hash__(self) -> int:

        return hash((self.op, self.left, self.right))

    

    def __eq__(self, other) -> bool:

        if isinstance(other, Expression):

            return self.op == other.op and self.left == other.left and self.right == other.right

        return False

    

    def get_variables(self) -> Set[str]:

        """

        获取表达式中的变量集合

        

        Returns:

            变量名集合

        """

        vars_set = set()

        if self.left.isidentifier():

            vars_set.add(self.left)

        if self.right.isidentifier():

            vars_set.add(self.right)

        return vars_set





class AvailableExpressions:

    """

    可用表达式分析器

    

    使用数据流方程迭代计算每个基本块的可用表达式集合。

    """

    

    def __init__(self, num_blocks: int):

        """

        初始化可用表达式分析器

        

        Args:

            num_blocks: 基本块数量

        """

        self.num_blocks = num_blocks

        # 每个块的GEN集合：block_id -> {Expressions}

        self.gen: Dict[int, Set[Expression]] = {i: set() for i in range(num_blocks)}

        # 每个块的KILL集合：block_id -> {Expressions}

        self.kill: Dict[int, Set[Expression]] = {i: set() for i in range(num_blocks)}

        # 每个块的IN集合

        self.in_set: Dict[int, Set[Expression]] = {i: set() for i in range(num_blocks)}

        # 每个块的OUT集合

        self.out_set: Dict[int, Set[Expression]] = {i: set() for i in range(num_blocks)}

        # 前驱关系

        self.predecessors: Dict[int, List[int]] = defaultdict(list)

        # 所有表达式的映射

        self.all_expressions: Set[Expression] = set()

    

    def add_expression(self, expr: Expression):

        """

        添加一个表达式到全局表达式集合

        

        Args:

            expr: 表达式对象

        """

        self.all_expressions.add(expr)

    

    def add_gen(self, block_id: int, expr: Expression):

        """

        添加表达式到块的GEN集合

        

        Args:

            block_id: 基本块ID

            expr: 表达式

        """

        self.gen[block_id].add(expr)

        self.all_expressions.add(expr)

    

    def add_kill(self, block_id: int, expr: Expression):

        """

        添加表达式到块的KILL集合

        

        Args:

            block_id: 基本块ID

            expr: 表达式

        """

        self.kill[block_id].add(expr)

    

    def set_predecessors(self, predecessors: Dict[int, List[int]]):

        """

        设置每个基本块的前驱块列表

        

        Args:

            predecessors: block_id -> [predecessor_block_ids]

        """

        self.predecessors = predecessors

    

    def analyze(self, max_iterations: int = 100) -> bool:

        """

        执行可用表达式分析迭代

        

        可用表达式使用交集作为IN的计算方式（与到达定义不同）

        

        Args:

            max_iterations: 最大迭代次数

            

        Returns:

            是否在有限次迭代内收敛

        """

        iteration = 0

        changed = True

        

        while changed and iteration < max_iterations:

            changed = False

            iteration += 1

            

            for block_id in range(self.num_blocks):

                # 计算IN[B] = ∩_{P∈pred(B)} OUT[P]

                preds = self.predecessors.get(block_id, [])

                

                if not preds:

                    # 没有前驱，IN为空

                    new_in: Set[Expression] = set()

                else:

                    # 取所有前驱OUT的交集

                    new_in = None

                    for pred_id in preds:

                        pred_out = self.out_set[pred_id]

                        if new_in is None:

                            new_in = pred_out.copy()

                        else:

                            new_in &= pred_out

                    

                    if new_in is None:

                        new_in = set()

                

                if new_in != self.in_set[block_id]:

                    self.in_set[block_id] = new_in

                    changed = True

                

                # 计算OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])

                new_out = self.gen[block_id] | (self.in_set[block_id] - self.kill[block_id])

                

                if new_out != self.out_set[block_id]:

                    self.out_set[block_id] = new_out

                    changed = True

        

        return iteration < max_iterations

    

    def get_available_in(self, block_id: int) -> Set[Expression]:

        """

        获取进入基本块时可用的表达式集合

        

        Args:

            block_id: 基本块ID

            

        Returns:

            可用表达式集合

        """

        return self.in_set[block_id].copy()

    

    def get_available_out(self, block_id: int) -> Set[Expression]:

        """

        获取离开基本块时可用的表达式集合

        

        Args:

            block_id: 基本块ID

            

        Returns:

            可用表达式集合

        """

        return self.out_set[block_id].copy()

    

    def is_available(self, block_id: int, expr: Expression) -> bool:

        """

        检查表达式在基本块入口是否可用

        

        Args:

            block_id: 基本块ID

            expr: 表达式

            

        Returns:

            如果可用返回True

        """

        return expr in self.in_set[block_id]

    

    def display_results(self):

        """打印分析结果（用于调试）"""

        print("=" * 60)

        print("Available Expressions Analysis Results")

        print("=" * 60)

        

        for block_id in range(self.num_blocks):

            gen_exprs = [str(e) for e in sorted(self.gen[block_id], key=str)]

            kill_exprs = [str(e) for e in sorted(self.kill[block_id], key=str)]

            in_exprs = [str(e) for e in sorted(self.in_set[block_id], key=str)]

            out_exprs = [str(e) for e in sorted(self.out_set[block_id], key=str)]

            

            print(f"\nBlock {block_id}:")

            print(f"  GEN:  {{{', '.join(gen_exprs) if gen_exprs else 'empty}'}}}")

            print(f"  KILL: {{{', '.join(kill_exprs) if kill_exprs else 'empty}'}}}")

            print(f"  IN:   {{{', '.join(in_exprs) if in_exprs else 'empty}'}}}")

            print(f"  OUT:  {{{', '.join(out_exprs) if out_exprs else 'empty}'}}}")





def create_cse_example():

    """

    创建公共子表达式消除示例

    

    程序：

        a = x + y

        b = x + y  # 可用表达式，可以复用a的计算结果

        c = a + b

        x = 5      # 杀死 a 和 b 的可用性

        d = x + y  # 需要重新计算

    

    预期：

    - Block 1: IN={}, OUT={(x+y)}

    - Block 2: IN={(x+y)}, OUT={(x+y)} （因为c的计算不会杀死(x+y)）

    - Block 3: IN={(x+y)}, OUT={} （因为x被重新定义，杀死(x+y)）

    - Block 4: IN={}, OUT={(x+y)} （重新计算）

    """

    analyzer = AvailableExpressions(num_blocks=4)

    

    # 表达式

    expr_xy = Expression('+', 'x', 'y')

    expr_ac = Expression('+', 'a', 'b')

    

    # Block 0: a = x + y

    analyzer.add_gen(0, expr_xy)

    # x和y被用于计算(x+y)，但没有被重新定义，所以不kill

    # 注意：实际上赋值语句会kill被赋值的变量的使用该表达式的效果

    # 这里简化处理

    

    # Block 1: b = x + y

    analyzer.add_gen(1, expr_xy)

    # KILL不需要设置，因为表达式还是一样的

    

    # Block 2: c = a + b

    analyzer.add_gen(2, expr_ac)

    # 不kill (x+y)

    

    # Block 3: x = 5

    # 这个块会kill (x+y) 因为x被重新定义

    # 任何使用x的表达式都被kill

    # 简化：手动kill

    analyzer.add_kill(3, expr_xy)

    

    # Block 4: d = x + y

    analyzer.add_gen(4, expr_xy)

    

    # 前驱关系

    analyzer.set_predecessors({

        0: [],

        1: [0],

        2: [1],

        3: [2],

        4: [3]

    })

    

    return analyzer





def create_branch_example():

    """

    创建分支程序的可用表达式分析示例

    

    程序：

        x = a + b

        if condition:

            y = a + b  # 分支内可用

        else:

            z = a + b  # 分支内可用

        w = x + y + z  # 汇合点，(a+b)可能不可用

    

    由于分支的汇合，表达式(a+b)在汇合点不可用（因为交集）。

    """

    analyzer = AvailableExpressions(num_blocks=5)

    

    expr_ab = Expression('+', 'a', 'b')

    

    # Block 0: x = a + b

    analyzer.add_gen(0, expr_ab)

    

    # Block 1: y = a + b (then分支)

    analyzer.add_gen(1, expr_ab)

    

    # Block 2: z = a + b (else分支)

    analyzer.add_gen(2, expr_ab)

    

    # Block 3: w = x + y + z (汇合点)

    # 汇合点的IN是Block 1和Block 2的OUT的交集

    # 由于两个分支都计算了(a+b)，交集仍然包含(a+b)

    # 所以(a+b)在汇合点可用

    # 但这里简化处理，不添加新的GEN

    

    # 前驱关系

    analyzer.set_predecessors({

        0: [],

        1: [0],

        2: [0],

        3: [1, 2],

        4: [3]  # 假设有出口块

    })

    

    return analyzer





if __name__ == "__main__":

    print("=" * 60)

    print("测试1：公共子表达式消除示例")

    print("=" * 60)

    

    analyzer = create_cse_example()

    converged = analyzer.analyze()

    

    print(f"\n迭代收敛: {converged}")

    analyzer.display_results()

    

    print("\n" + "=" * 60)

    print("测试2：分支程序的可用表达式分析")

    print("=" * 60)

    

    analyzer2 = create_branch_example()

    converged2 = analyzer2.analyze()

    

    print(f"\n迭代收敛: {converged2}")

    analyzer2.display_results()

    

    print("\n" + "=" * 60)

    print("测试3：表达式可用性查询")

    print("=" * 60)

    

    # 使用第一个例子的分析器

    expr_xy = Expression('+', 'x', 'y')

    

    print(f"\n表达式 (x+y) 在各块的可用性:")

    for block_id in range(5):

        available = analyzer.is_available(block_id, expr_xy)

        print(f"  Block {block_id}: {'可用' if available else '不可用'}")

    

    print("\n可用表达式分析测试完成!")

    print("\n注意：可用表达式分析使用交集，因此：")

    print("  1. 入口块的IN为空")

    print("  2. 汇合点的IN是前驱OUT的交集")

    print("  3. 只有当所有路径都产生表达式时，才认为可用")

