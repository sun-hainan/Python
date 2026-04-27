# -*- coding: utf-8 -*-

"""

算法实现：程序分析 / dataflow_reaching_definitions



本文件实现 dataflow_reaching_definitions 相关的算法功能。

"""



from typing import Dict, List, Set, Tuple, Optional

from collections import defaultdict





class ReachingDefinitions:

    """

    到达定义分析器

    

    使用数据流方程迭代计算每个基本块的IN和OUT集合：

    - OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])

    - IN[B] = ∪_{P∈pred(B)} OUT[P]

    

    迭代直到不动点（集合不再变化）为止。

    """

    

    def __init__(self, num_blocks: int):

        """

        初始化到达定义分析器

        

        Args:

            num_blocks: 程序中基本块的数量

        """

        self.num_blocks = num_blocks  # 基本块总数

        # 每个块的GEN集合：block_id -> {(variable, definition_id)}

        self.gen: Dict[int, Set[Tuple[str, int]]] = {i: set() for i in range(num_blocks)}

        # 每个块的KILL集合：block_id -> {(variable, definition_id)}

        self.kill: Dict[int, Set[Tuple[str, int]]] = {i: set() for i in range(num_blocks)}

        # 每个块的IN集合

        self.in_set: Dict[int, Set[Tuple[str, int]]] = {i: set() for i in range(num_blocks)}

        # 每个块的OUT集合

        self.out_set: Dict[int, Set[Tuple[str, int]]] = {i: set() for i in range(num_blocks)}

        # 记录所有定义的计数器

        self.definition_counter: int = 0

        # 定义注册表：definition_id -> (block_id, variable, description)

        self.definitions: Dict[int, Tuple[int, str, str]] = {}

    

    def add_definition(self, block_id: int, variable: str, description: str):

        """

        添加一个定义到指定块的GEN集合

        

        Args:

            block_id: 基本块ID

            variable: 被定义的变量名

            description: 定义的描述文本

        """

        self.definition_counter += 1

        def_id = self.definition_counter

        self.definitions[def_id] = (block_id, variable, description)

        self.gen[block_id].add((variable, def_id))

    

    def add_kill(self, block_id: int, variable: str, def_id: int):

        """

        添加一个KILL项，表示该定义被覆盖

        

        Args:

            block_id: 基本块ID

            variable: 被重新定义的变量名

            def_id: 被杀死的定义ID

        """

        self.kill[block_id].add((variable, def_id))

    

    def set_predecessors(self, predecessors: Dict[int, List[int]]):

        """

        设置每个基本块的前驱块列表

        

        Args:

            predecessors: block_id -> [predecessor_block_ids]

        """

        self.predecessors = predecessors

    

    def analyze(self, max_iterations: int = 100) -> bool:

        """

        执行到达定义分析迭代

        

        Args:

            max_iterations: 最大迭代次数，防止无限循环

            

        Returns:

            是否在有限次迭代内收敛

        """

        iteration = 0

        changed = True

        

        while changed and iteration < max_iterations:

            changed = False

            iteration += 1

            

            # 遍历每个基本块

            for block_id in range(self.num_blocks):

                # 计算IN[B] = ∪_{P∈pred(B)} OUT[P]

                new_in: Set[Tuple[str, int]] = set()

                for pred_id in self.predecessors.get(block_id, []):

                    new_in |= self.out_set[pred_id]

                

                # 检查IN是否变化

                if new_in != self.in_set[block_id]:

                    self.in_set[block_id] = new_in

                    changed = True

                

                # 计算OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])

                killed = self.kill[block_id]

                new_out = self.gen[block_id] | (self.in_set[block_id] - killed)

                

                # 检查OUT是否变化

                if new_out != self.out_set[block_id]:

                    self.out_set[block_id] = new_out

                    changed = True

        

        return iteration < max_iterations

    

    def get_reaching_definitions(self, block_id: int) -> Set[Tuple[str, int]]:

        """

        获取到达指定基本块入口的定义集合

        

        Args:

            block_id: 基本块ID

            

        Returns:

            (variable, definition_id) 的集合

        """

        return self.in_set[block_id].copy()

    

    def get_out_definitions(self, block_id: int) -> Set[Tuple[str, int]]:

        """

        获取从指定基本块出口离开的定义集合

        

        Args:

            block_id: 基本块ID

            

        Returns:

            (variable, definition_id) 的集合

        """

        return self.out_set[block_id].copy()

    

    def format_definition(self, def_id: int) -> str:

        """

        格式化定义ID为可读字符串

        

        Args:

            def_id: 定义ID

            

        Returns:

            格式化的字符串，如 "d1: x = ..."

        """

        if def_id in self.definitions:

            block_id, var, desc = self.definitions[def_id]

            return f"d{def_id}: {var} = {desc}"

        return f"d{def_id}: unknown"





def simple_cfg_example():

    """

    创建一个简单的CFG示例用于测试

    

    程序示例：

        1: x = 5

        2: y = x + 1

        3: x = 10

        4: z = x + y

    

    定义编号：

        d1: x = 5

        d2: y = x + 1 (使用d1)

        d3: x = 10

        d4: z = x + y (使用d3和d2)

    

    预期到达定义：

        Block 1入口: {}

        Block 1出口: {d1}

        Block 2入口: {d1}

        Block 2出口: {d1, d2}

        Block 3入口: {d1, d2}

        Block 3出口: {d2, d3}

        Block 4入口: {d2, d3}

        Block 4出口: {d2, d3, d4}

    """

    analyzer = ReachingDefinitions(num_blocks=4)

    

    # Block 0: x = 5

    analyzer.add_definition(0, "x", "5")

    # 注意：Block 0没有KILL任何之前定义（这是第一个块）

    

    # Block 1: y = x + 1

    # 这个块会KILL任何之前对y的定义，但不KILL对x的定义

    # 这里简化处理，不预先添加KILL

    analyzer.add_definition(1, "y", "x + 1")

    

    # Block 2: x = 10

    # 这个块KILL了d1（对x的赋值）

    analyzer.add_definition(2, "x", "10")

    analyzer.add_kill(2, "x", def_id=1)  # KILL d1

    

    # Block 3: z = x + y

    analyzer.add_definition(3, "z", "x + y")

    

    # 设置CFG的前驱关系（顺序执行，无分支）

    analyzer.set_predecessors({

        0: [],           # Block 0没有前驱（入口）

        1: [0],          # Block 1前驱是Block 0

        2: [1],          # Block 2前驱是Block 1

        3: [2]           # Block 3前驱是Block 2

    })

    

    return analyzer





def branch_cfg_example():

    """

    创建带分支的CFG示例

    

    程序示例（if-then-else）：

        1: x = 5

        2: if condition:

        3:     x = 10

        4: else:

        5:     x = 15

        6: y = x

    

    这个例子展示了分支如何影响到达定义：

    - Block 6的x可能来自d3(x=10)或d5(x=15)

    """

    analyzer = ReachingDefinitions(num_blocks=4)

    

    # Block 0: x = 5 (初始赋值)

    analyzer.add_definition(0, "x", "5")

    analyzer.add_kill(0, "x", def_id=1)  # KILL之前可能存在的定义

    

    # Block 1: x = 10 (then分支)

    analyzer.add_definition(1, "x", "10")

    analyzer.add_kill(1, "x", def_id=1)  # KILL Block 0的定义

    

    # Block 2: x = 15 (else分支)

    analyzer.add_definition(2, "x", "15")

    analyzer.add_kill(2, "x", def_id=1)  # KILL Block 0的定义

    

    # Block 3: y = x (汇合点)

    analyzer.add_definition(3, "y", "x")

    analyzer.add_kill(3, "y", def_id=0)  # KILL Block 0对y的（如果有的话）

    

    # CFG结构：

    #     [Block 0]

    #    /        \

    # [Block 1]  [Block 2]

    #    \        /

    #     [Block 3]

    

    analyzer.set_predecessors({

        0: [],

        1: [0],

        2: [0],

        3: [1, 2]  # Block 3有两个前驱

    })

    

    return analyzer





if __name__ == "__main__":

    print("=" * 60)

    print("测试1：简单顺序程序的到达定义分析")

    print("=" * 60)

    

    analyzer = simple_cfg_example()

    converged = analyzer.analyze()

    

    print(f"\n迭代收敛: {converged}")

    print("\n各基本块的IN/OUT集合:")

    

    for block_id in range(analyzer.num_blocks):

        in_defs = analyzer.get_reaching_definitions(block_id)

        out_defs = analyzer.get_out_definitions(block_id)

        

        in_str = ", ".join(analyzer.format_definition(d[1]) for d in sorted(in_defs, key=lambda x: x[1]))

        out_str = ", ".join(analyzer.format_definition(d[1]) for d in sorted(out_defs, key=lambda x: x[1]))

        

        print(f"\n  Block {block_id}:")

        print(f"    IN:  {{{in_str if in_str else 'empty}'}}}")

        print(f"    OUT: {{{out_str if out_str else 'empty}'}}}")

    

    print("\n" + "=" * 60)

    print("测试2：分支程序的到达定义分析")

    print("=" * 60)

    

    analyzer2 = branch_cfg_example()

    converged2 = analyzer2.analyze()

    

    print(f"\n迭代收敛: {converged2}")

    print("\n各基本块的IN/OUT集合:")

    

    for block_id in range(analyzer2.num_blocks):

        in_defs = analyzer2.get_reaching_definitions(block_id)

        out_defs = analyzer2.get_out_definitions(block_id)

        

        in_str = ", ".join(analyzer2.format_definition(d[1]) for d in sorted(in_defs, key=lambda x: x[1]))

        out_str = ", ".join(analyzer2.format_definition(d[1]) for d in sorted(out_defs, key=lambda x: x[1]))

        

        print(f"\n  Block {block_id}:")

        print(f"    IN:  {{{in_str if in_str else 'empty}'}}}")

        print(f"    OUT: {{{out_str if out_str else 'empty}'}}}")

    

    print("\n到达定义分析测试完成!")

