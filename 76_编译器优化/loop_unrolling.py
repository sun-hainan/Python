# -*- coding: utf-8 -*-

"""

算法实现：编译器优化 / loop_unrolling



本文件实现 loop_unrolling 相关的算法功能。

"""



from typing import List, Dict, Optional, Tuple





class Loop:

    """循环表示"""

    def __init__(self, var: str, start: int, end: int, step: int, body: List):

        """

        初始化

        

        Args:

            var: 循环变量

            start: 起始值

            end: 结束值

            step: 步长

            body: 循环体语句

        """

        self.var = var

        self.start = start

        self.end = end

        self.step = step

        self.body = body

    

    def trip_count(self) -> int:

        """计算循环次数"""

        if self.step > 0:

            return max(0, (self.end - self.start + self.step - 1) // self.step)

        elif self.step < 0:

            return max(0, (self.start - self.end - self.step - 1) // (-self.step))

        return 0





class Statement:

    """语句基类"""

    pass





class Assign(Statement):

    """赋值语句"""

    def __init__(self, lhs: str, rhs: str):

        self.lhs = lhs

        self.rhs = rhs

    

    def __repr__(self):

        return f"{self.lhs} = {self.rhs}"





class LoopUnroller:

    """

    循环展开优化器

    """

    

    def __init__(self, max_unroll_factor: int = 4):

        """

        初始化

        

        Args:

            max_unroll_factor: 最大展开因子

        """

        self.max_unroll = max_unroll_factor

    

    def unroll(self, loop: Loop, factor: int = None) -> List[Statement]:

        """

        展开循环

        

        Args:

            loop: 要展开的循环

            factor: 展开因子(默认自动选择)

        

        Returns:

            展开后的语句列表

        """

        trip_count = loop.trip_count()

        

        if trip_count == 0:

            return []  # 空循环

        

        # 选择展开因子

        if factor is None:

            factor = self._choose_unroll_factor(trip_count)

        

        if factor < 2:

            return self._partial_unroll(loop, trip_count)

        

        # 完全展开(如果次数少)

        if trip_count <= factor:

            return self._fully_unroll(loop, trip_count)

        

        # 部分展开

        return self._partial_unroll(loop, factor)

    

    def _choose_unroll_factor(self, trip_count: int) -> int:

        """选择最佳展开因子"""

        for f in [2, 4, 8]:

            if f <= trip_count and f <= self.max_unroll:

                return f

        return 1

    

    def _fully_unroll(self, loop: Loop, count: int) -> List[Statement]:

        """

        完全展开循环

        

        Args:

            loop: 循环

            count: 迭代次数

        

        Returns:

            展开后的语句

        """

        result = []

        

        for i in range(count):

            # 计算循环变量的值

            iter_val = loop.start + i * loop.step

            

            # 添加展开后的语句

            for stmt in loop.body:

                expanded = self._expand_statement(stmt, loop.var, iter_val)

                result.append(expanded)

        

        return result

    

    def _partial_unroll(self, loop: Loop, factor: int) -> List[Statement]:

        """

        部分展开循环

        

        Args:

            loop: 循环

            factor: 展开因子

        

        Returns:

            展开后的语句

        """

        result = []

        

        # 剩余迭代次数

        remaining = loop.trip_count() % factor

        

        # 主体部分:展开factor次

        for _ in range(loop.trip_count() // factor):

            for i in range(factor):

                iter_val = loop.start

                for stmt in loop.body:

                    expanded = self._expand_statement(stmt, loop.var, iter_val)

                    result.append(expanded)

                loop.start += loop.step

        

        # 尾部:处理剩余迭代

        for _ in range(remaining):

            for stmt in loop.body:

                expanded = self._expand_statement(stmt, loop.var, loop.start)

                result.append(expanded)

            loop.start += loop.step

        

        return result

    

    def _expand_statement(self, stmt: Assign, loop_var: str, iter_val: int) -> Statement:

        """

        展开语句,将循环变量替换为常量

        

        Args:

            stmt: 语句

            loop_var: 循环变量名

            iter_val: 迭代变量的值

        

        Returns:

            展开后的语句

        """

        new_rhs = stmt.rhs.replace(loop_var, str(iter_val))

        return Assign(stmt.lhs, new_rhs)

    

    def unroll_with_peeling(self, loop: Loop, factor: int = 4) -> Tuple[List[Statement], Optional[Loop]]:

        """

        展开并剥离(适合不知道确切迭代次数的情况)

        

        Args:

            loop: 循环

            factor: 展开因子

        

        Returns:

            (展开后的语句, 剩余循环或None)

        """

        trip_count = loop.trip_count()

        

        if trip_count == 0:

            return [], None

        

        if trip_count <= factor:

            # 完全展开

            return self._fully_unroll(loop, trip_count), None

        

        # 剥离前factor次

        peeled = []

        for _ in range(factor):

            for stmt in loop.body:

                expanded = self._expand_statement(stmt, loop.var, loop.start)

                peeled.append(expanded)

            loop.start += loop.step

            trip_count -= 1

        

        return peeled, loop





def unroll_loop(loop: Loop, factor: int = None) -> List[Statement]:

    """

    循环展开便捷函数

    

    Args:

        loop: 要展开的循环

        factor: 展开因子

    

    Returns:

        展开后的语句列表

    """

    unroller = LoopUnroller()

    return unroller.unroll(loop, factor)





# 测试代码

if __name__ == "__main__":

    # 测试1: 简单循环展开

    print("测试1 - 简单循环展开:")

    

    # for i in range(0, 8):

    #     a[i] = b[i] * 2

    

    loop1 = Loop(

        var='i',

        start=0,

        end=8,

        step=1,

        body=[

            Assign('a[i]', 'b[i] * 2'),

        ]

    )

    

    unrolled1 = unroll_loop(loop1, factor=4)

    

    print(f"  循环次数: {loop1.trip_count()}")

    print("  展开后的语句:")

    for stmt in unrolled1:

        print(f"    {stmt}")

    

    # 测试2: 部分展开

    print("\n测试2 - 部分展开:")

    

    # for i in range(0, 10):

    #     sum += a[i]

    

    loop2 = Loop(

        var='i',

        start=0,

        end=10,

        step=1,

        body=[

            Assign('sum', 'sum + a[i]'),

        ]

    )

    

    unrolled2 = unroll_loop(loop2, factor=4)

    

    print(f"  循环次数: {loop2.trip_count()}")

    print("  展开后的语句:")

    for i, stmt in enumerate(unrolled2[:16]):

        print(f"    {stmt}")

    if len(unrolled2) > 16:

        print(f"    ... 还有{len(unrolled2)-16}条语句")

    

    # 测试3: 完全展开

    print("\n测试3 - 完全展开:")

    

    # for i in range(0, 4):

    #     x[i] = i * i

    

    loop3 = Loop(

        var='i',

        start=0,

        end=4,

        step=1,

        body=[

            Assign('x[i]', 'i * i'),

        ]

    )

    

    unrolled3 = unroll_loop(loop3)

    

    print(f"  循环次数: {loop3.trip_count()}")

    print("  完全展开:")

    for stmt in unrolled3:

        print(f"    {stmt}")

    

    # 测试4: 复杂循环体

    print("\n测试4 - 复杂循环体:")

    

    # for i in range(0, 6):

    #     a[i] = b[i] + c[i]

    #     d[i] = a[i] * 2

    

    loop4 = Loop(

        var='i',

        start=0,

        end=6,

        step=1,

        body=[

            Assign('a[i]', 'b[i] + c[i]'),

            Assign('d[i]', 'a[i] * 2'),

        ]

    )

    

    unrolled4 = unroll_loop(loop4, factor=2)

    

    print(f"  循环次数: {loop4.trip_count()}")

    print("  展开(factor=2):")

    for stmt in unrolled4:

        print(f"    {stmt}")

    

    # 测试5: 验证展开正确性

    print("\n测试5 - 验证正确性:")

    

    # 模拟执行原始循环

    n = 6

    a_orig = [0] * n

    for i in range(n):

        a_orig[i] = i * 2

    

    # 模拟执行展开后的代码

    a_unrolled = [0] * n

    stmts = unroll_loop(Loop('i', 0, n, 1, [Assign('a[i]', 'i * 2')]), factor=3)

    

    # 简化模拟

    for stmt in stmts:

        # 解析 x[n] = value 形式

        lhs, rhs = str(stmt).split(' = ')

        # 提取索引和值

        if '[' in lhs:

            var_name = lhs[:lhs.index('[')]

            idx = int(lhs[lhs.index('[') + 1:lhs.index(']')])

            a_unrolled[idx] = eval(rhs.replace('i', str(idx)))

    

    print(f"  原始循环结果: {a_orig}")

    print(f"  展开后结果: {a_unrolled}")

    print(f"  一致: {a_orig == a_unrolled}")

    

    # 测试6: 步长不为1

    print("\n测试6 - 步长为2的循环:")

    

    # for i in range(0, 10, 2):

    #     a[i] = i / 2

    

    loop6 = Loop(

        var='i',

        start=0,

        end=10,

        step=2,

        body=[

            Assign('a[i]', 'i / 2'),

        ]

    )

    

    unrolled6 = unroll_loop(loop6)

    

    print(f"  循环次数: {loop6.trip_count()}")

    print("  展开后:")

    for stmt in unrolled6:

        print(f"    {stmt}")

    

    print("\n所有测试完成!")

