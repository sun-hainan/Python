# -*- coding: utf-8 -*-

"""

算法实现：程序分析 / data_flow_analysis



本文件实现 data_flow_analysis 相关的算法功能。

"""



from typing import Set, List, Dict, Tuple





class BasicBlock:

    """简化的基本块"""



    def __init__(self, block_id: int):

        self.id = block_id

        self.statements = []  # [(var, 'def'/'use'), ...]



    def get_def(self) -> Set[str]:

        """获取此块中定义的变量"""

        return {stmt[0] for stmt in self.statements if stmt[1] == 'def'}



    def get_use(self) -> Set[str]:

        """获取此块中使用的变量"""

        return {stmt[0] for stmt in self.statements if stmt[1] == 'use'}





def reaching_definitions(blocks: List[BasicBlock]) -> List[Dict[str, Set[str]]]:

    """

    计算每个块的到达定义集合



    算法：迭代求解

        IN[B] = ∪(OUT[P]) for P in pred(B)

        OUT[B] = GEN[B] ∪ (IN[B] - KILL[B])



    返回：每个块的IN集合列表

    """

    n = len(blocks)



    # GEN[B]: 此块生成的定义（块内最后一条定义覆盖之前）

    gen = [set() for _ in range(n)]

    # KILL[B]: 此块杀死的定义（变量被重新定义）

    kill = [set() for _ in range(n)]



    for i, block in enumerate(blocks):

        defined_vars = set()

        killed_vars = set()



        for stmt in block.statements:

            var, kind = stmt

            if kind == 'def':

                # 如果之前这个变量被定义过，现在就杀死之前的定义

                if var not in defined_vars:

                    killed_vars.add(var)

                defined_vars.add(var)



        gen[i] = defined_vars

        kill[i] = killed_vars



    # 迭代求解

    in_sets = [set() for _ in range(n)]



    changed = True

    iterations = 0

    while changed:

        changed = False

        iterations += 1



        for i, block in enumerate(blocks):

            # IN[B] = ∪ OUT[P] for P in pred(B)

            new_in = set()

            for pred in block.preds:

                pred_idx = blocks.index(pred)

                new_in |= in_sets[pred_idx]



            if new_in != in_sets[i]:

                in_sets[i] = new_in

                changed = True



    return in_sets





def liveness_analysis(blocks: List[BasicBlock]) -> List[Set[str]]:

    """

    活跃变量分析



    算法：反向迭代

        USE[B] = 在B中使用的变量

        DEF[B] = 在B中定义的变量

        IN[B] = USE[B] ∪ (OUT[B] - DEF[B])

        OUT[B] = ∪ IN[Succ] for Succ in succ(B)



    返回：每个块的IN集合（活跃变量）

    """

    n = len(blocks)



    use = [set() for _ in range(n)]

    def_set = [set() for _ in range(n)]



    for i, block in enumerate(blocks):

        for var, kind in block.statements:

            if kind == 'use':

                use[i].add(var)

            elif kind == 'def':

                def_set[i].add(var)



    # 反向迭代

    out_sets = [set() for _ in range(n)]



    changed = True

    iterations = 0

    while changed:

        changed = False

        iterations += 1



        for i in range(n - 1, -1, -1):  # 反向

            block = blocks[i]



            # OUT[B] = ∪ IN[Succ]

            new_out = set()

            for succ in block.succs:

                succ_idx = blocks.index(succ)

                new_out |= out_sets[succ_idx]



            # IN[B] = USE[B] ∪ (OUT[B] - DEF[B])

            new_in = use[i] | (new_out - def_set[i])



            if new_out != out_sets[i]:

                out_sets[i] = new_out

                changed = True



    return out_sets





def build_blocks_from_statements(statements: List[Tuple]) -> List[BasicBlock]:

    """从语句列表构建基本块"""

    blocks = [BasicBlock(0)]

    current = blocks[0]



    for stmt in statements:

        var, kind = stmt

        current.statements.append((var, kind))



    return blocks





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 数据流分析测试 ===\n")



    # 示例程序：

    # x = 10        # def x

    # y = x + 5     # use x, def y

    # if y > 0:     # use y

    #   x = y      # use y, def x

    # else:

    #   x = 0      # def x

    # z = x         # use x, def z



    statements = [

        ('x', 'def'),   # x = 10

        ('x', 'use'),   # y = x + 5 (use x)

        ('y', 'def'),  # y = ...

        ('y', 'use'),   # if y > 0 (use y)

        ('y', 'use'),  # x = y (use y)

        ('x', 'def'),  # x = ...

        ('x', 'use'),  # z = x (use x)

        ('z', 'def'),  # z = ...

    ]



    blocks = build_blocks_from_statements(statements)



    print("程序语句:")

    for i, (var, kind) in enumerate(statements):

        print(f"  {i}: {var} ({kind})")



    print()



    print("1. 到达定义分析：")

    in_sets = reaching_definitions(blocks)

    for i, in_set in enumerate(in_sets):

        print(f"  BB{i}: IN = {in_set}")



    print()

    print("2. 活跃变量分析：")

    # 需要构建CFG（简化：线性连接）

    blocks[0].succs.append(blocks[1] if len(blocks) > 1 else None)

    for i in range(len(blocks) - 1):

        blocks[i].succs = [blocks[i + 1]]



    live_sets = liveness_analysis(blocks)

    for i, live_set in enumerate(live_sets):

        print(f"  BB{i}: LIVE = {live_set}")



    print("\n说明：")

    print("  - 到达定义：变量在某点之前的定义能否到达该点")

    print("  - 活跃变量：在某点之后还会被使用的变量")

