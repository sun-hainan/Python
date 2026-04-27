# -*- coding: utf-8 -*-

"""

算法实现：编译器优化 / loop_optimization



本文件实现 loop_optimization 相关的算法功能。

"""



from typing import List, Tuple, Set, Dict

from collections import defaultdict





class LoopInvariantCodeMotion:

    """

    循环不变代码外提(LICM)

    将循环中不依赖于循环变量的计算移到循环外

    """

    

    def __init__(self, loops: List[Dict]):

        """

        初始化

        

        Args:

            loops: 循环列表,每项包含{'header': block_id, 'body': [block_ids], 'preheader': block_id}

        """

        self.loops = loops

    

    def find_invariant(self, stmt, loop_vars: Set[str]) -> bool:

        """

        检查语句是否循环不变

        

        Args:

            stmt: 语句

            loop_vars: 循环中定义的变量集合

        

        Returns:

            是否循环不变

        """

        if not hasattr(stmt, 'uses'):

            return True

        

        uses = stmt.uses()

        

        # 如果所有使用的变量都在循环外定义,则不变

        for var in uses:

            if var in loop_vars:

                return False

        

        return True

    

    def find_loop_invariant_code(self, loop: Dict, statements: List) -> List:

        """

        找出循环中的不变代码

        

        Args:

            loop: 循环信息

            statements: 循环中的语句列表

        

        Returns:

            不变语句列表

        """

        invariant_stmts = []

        loop_vars = set()

        

        # 第一步:收集循环中定义的变量

        for stmt in statements:

            if hasattr(stmt, 'defines'):

                loop_vars.update(stmt.defines())

        

        # 第二步:找出不变语句

        for stmt in statements:

            if hasattr(stmt, 'lhs') and self.find_invariant(stmt, loop_vars):

                invariant_stmts.append(stmt)

        

        return invariant_stmts

    

    def move_out(self, loop: Dict, invariant_stmts: List) -> Tuple[List, List]:

        """

        将不变代码外提

        

        Args:

            loop: 循环信息

            invariant_stmts: 不变语句

        

        Returns:

            (移动到preheader的语句, 保留在循环中的语句)

        """

        moved = []

        remaining = []

        

        loop_body_ids = set(loop.get('body', []))

        

        for stmt in invariant_stmts:

            # 检查语句的副作用

            if self.has_side_effects(stmt):

                remaining.append(stmt)

            else:

                moved.append(stmt)

        

        return moved, remaining

    

    def has_side_effects(self, stmt) -> bool:

        """检查语句是否有副作用"""

        # 假设赋值语句没有副作用

        if hasattr(stmt, 'lhs'):

            return False

        # 函数调用可能有副作用

        if hasattr(stmt, 'is_call') and stmt.is_call:

            return True

        return False





class LoopUnswitching:

    """

    循环分裂

    将包含条件分支的循环拆分为多个循环

    """

    

    def split_by_condition(self, loop: Dict, condition_var: str) -> List[Dict]:

        """

        根据条件拆分循环

        

        Args:

            loop: 循环信息

            condition_var: 条件变量

        

        Returns:

            拆分后的循环列表

        """

        # 假设条件在循环入口处检查

        true_loop = loop.copy()

        false_loop = loop.copy()

        

        # 设置新的条件

        true_loop['condition'] = f"{condition_var} == true"

        false_loop['condition'] = f"{condition_var} == false"

        

        return [true_loop, false_loop]





class LoopFusion:

    """

    循环合并

    将相邻的同类循环合并

    """

    

    def can_fuse(self, loop1: Dict, loop2: Dict) -> bool:

        """

        检查两个循环是否可以合并

        

        Args:

            loop1: 第一个循环

            loop2: 第二个循环

        

        Returns:

            是否可以合并

        """

        # 检查循环变量是否相同

        if loop1.get('var') != loop2.get('var'):

            return False

        

        # 检查范围是否连续

        end1 = loop1.get('end', 0)

        start2 = loop2.get('start', 0)

        

        if end1 != start2:

            return False

        

        # 检查循环体是否兼容

        body1 = loop1.get('body', [])

        body2 = loop2.get('body', [])

        

        # 简化:假设如果语句列表相同则兼容

        return body1 == body2

    

    def fuse(self, loop1: Dict, loop2: Dict) -> Dict:

        """

        合并两个循环

        

        Args:

            loop1: 第一个循环

            loop2: 第二个循环

        

        Returns:

            合并后的循环

        """

        fused = loop1.copy()

        

        # 更新范围

        fused['end'] = loop2['end']

        

        return fused





class LoopParallelization:

    """

    循环并行化

    检查循环是否可以并行执行

    """

    

    def is_parallelizable(self, loop: Dict, statements: List) -> Tuple[bool, str]:

        """

        检查循环是否可并行化

        

        Args:

            loop: 循环信息

            statements: 循环中的语句

        

        Returns:

            (是否可并行, 原因)

        """

        # 检查循环迭代之间是否有依赖

        loop_vars = set()

        

        for stmt in statements:

            if hasattr(stmt, 'defines'):

                for var in stmt.defines():

                    loop_vars.add(var)

        

        # 检查是否有循环携带依赖

        for stmt in statements:

            if hasattr(stmt, 'uses'):

                for var in stmt.uses():

                    if var in loop_vars:

                        return False, f"循环携带依赖: {var}"

        

        # 检查是否有归纳变量

        for stmt in statements:

            if hasattr(stmt, 'is_induction') and stmt.is_induction:

                return True, ""

        

        return True, ""





# 测试代码

if __name__ == "__main__":

    # 测试1: 循环不变代码检测

    print("测试1 - 循环不变代码检测:")

    

    class Stmt:

        def __init__(self, lhs, rhs1, rhs2=None, uses=None, defines=None):

            self.lhs = lhs

            self.rhs1 = rhs1

            self.rhs2 = rhs2

            self.uses = uses or set()

            self.defines = defines or set()

        

        def __repr__(self):

            if self.rhs2:

                return f"{self.lhs} = {self.rhs1} + {self.rhs2}"

            return f"{self.lhs} = {self.rhs1}"

    

    loop = {

        'header': 1,

        'body': [1, 2, 3],

        'preheader': 0

    }

    

    # 循环中的语句

    # a = 10  (不变)

    # b = a + c  (不变,依赖c但c在循环外)

    # x = x + 1  (变化)

    # y = x + b  (变化,依赖x)

    

    statements = [

        Stmt('a', '10', uses=set(), defines={'a'}),

        Stmt('b', 'a', 'c', uses={'a', 'c'}, defines={'b'}),

        Stmt('x', 'x', '1', uses={'x'}, defines={'x'}),

        Stmt('y', 'x', 'b', uses={'x', 'b'}, defines={'y'}),

    ]

    

    licm = LoopInvariantCodeMotion([loop])

    loop_vars = {'x', 'y'}

    

    print("  语句:")

    for i, stmt in enumerate(statements):

        print(f"    {i}: {stmt} (uses={stmt.uses}, defines={stmt.defines})")

    

    invariant = licm.find_loop_invariant_code(loop, statements)

    print(f"\n  不变语句: {[str(s) for s in invariant]}")

    

    # 测试2: 循环合并

    print("\n测试2 - 循环合并:")

    

    loop1 = {'var': 'i', 'start': 0, 'end': 100, 'body': ['stmt1']}

    loop2 = {'var': 'i', 'start': 100, 'end': 200, 'body': ['stmt1']}

    loop3 = {'var': 'j', 'start': 0, 'end': 100, 'body': ['stmt1']}

    

    fusion = LoopFusion()

    

    print(f"  loop1和loop2可合并: {fusion.can_fuse(loop1, loop2)}")

    print(f"  loop1和loop3可合并: {fusion.can_fuse(loop1, loop3)}")

    

    if fusion.can_fuse(loop1, loop2):

        fused = fusion.fuse(loop1, loop2)

        print(f"  合并后: var={fused['var']}, range=[{fused['start']}, {fused['end']})")

    

    # 测试3: 循环并行化

    print("\n测试3 - 循环并行化:")

    

    # 可并行的循环

    parallel_loop = {

        'var': 'i',

        'start': 0,

        'end': 100

    }

    

    parallel_stmts = [

        Stmt('a[i]', 'b[i]', 'c[i]', uses={'b', 'c'}, defines={'a'}),

    ]

    

    parallelizer = LoopParallelization()

    is_parallel, reason = parallelizer.is_parallelizable(parallel_loop, parallel_stmts)

    

    print(f"  可并行化: {is_parallel}")

    if reason:

        print(f"  原因: {reason}")

    

    # 不可并行的循环(有依赖)

    dependent_stmts = [

        Stmt('a[i]', 'a[i-1]', '1', uses={'a'}, defines={'a'}),  # 循环携带依赖

    ]

    

    is_parallel2, reason2 = parallelizer.is_parallelizable(parallel_loop, dependent_stmts)

    print(f"  依赖循环可并行化: {is_parallel2}")

    if reason2:

        print(f"  原因: {reason2}")

    

    print("\n所有测试完成!")

