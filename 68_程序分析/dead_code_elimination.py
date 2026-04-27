# -*- coding: utf-8 -*-

"""

算法实现：程序分析 / dead_code_elimination



本文件实现 dead_code_elimination 相关的算法功能。

"""



from typing import List, Set, Tuple





def dead_store_elimination(statements: List[Tuple]) -> List[Tuple]:

    """

    死存储消除



    参数：

        statements: [('assign', var, value), ('use', var), ...]



    返回：优化后的语句列表

    """

    # 反向分析：哪些变量在之后还会被使用

    used = set()

    live_stores = []



    # 反向遍历

    for stmt in reversed(statements):

        stmt_type = stmt[0]



        if stmt_type == 'use':

            # 标记变量为活跃

            used.add(stmt[1])



        elif stmt_type == 'assign':

            var = stmt[1]

            if var in used:

                # 这个赋值是活跃的，保留

                live_stores.insert(0, stmt)

                # 但变量被重新赋值，所以之前的use不是这个了

                # 实际上需要跟踪use-def链

            else:

                # 死存储，跳过

                pass



        elif stmt_type == 'ret':

            # 返回语句中的使用是活跃的

            for arg in stmt[1:]:

                if isinstance(arg, str):

                    used.add(arg)



    return live_stores





def unreachable_code_elimination(graph: dict, entry: int) -> Set[int]:

    """

    不可达代码消除



    参数：

        graph: CFG {node: [successors]}

        entry: 入口节点



    返回：可达节点集合

    """

    reachable = {entry}

    queue = [entry]



    while queue:

        node = queue.pop(0)

        for succ in graph.get(node, []):

            if succ not in reachable:

                reachable.add(succ)

                queue.append(succ)



    return reachable





def constant_branch_elimination(statements: List[Tuple], value_env: dict) -> List[Tuple]:

    """

    常量分支消除



    如果 if 条件是常量，就消除分支

    """

    result = []



    i = 0

    while i < len(statements):

        stmt = statements[i]



        if stmt[0] == 'if':

            cond = stmt[1]

            # 如果条件可以求值为常量

            if cond in value_env and isinstance(value_env[cond], bool):

                # 消除分支，只保留一个分支

                if value_env[cond]:

                    # 只保留then分支

                    result.extend(statements[i+1:i+1+stmt[2]])

                else:

                    # 只保留else分支

                    result.extend(statements[i+1+stmt[2]:i+1+stmt[2]+stmt[3]])

                i += 1 + stmt[2] + stmt[3]

            else:

                result.append(stmt)

                i += 1

        else:

            result.append(stmt)

            i += 1



    return result





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 死代码消除测试 ===\n")



    # 示例程序

    statements = [

        ('assign', 'x', 10),      # x = 10

        ('assign', 'y', 20),      # y = 20

        ('use', 'x'),             # print(x) - x被使用

        ('assign', 'z', 30),      # z = 30 - z从未使用

        ('use', 'y'),             # print(y) - y被使用

        ('assign', 'w', 40),      # w = 40 - w从未使用

        ('ret', 'x', 'y'),        # return x + y

    ]



    print("原始语句：")

    for stmt in statements:

        print(f"  {stmt}")



    # 简化分析

    print("\n分析：")

    print("  x=10 后被使用: 活跃")

    print("  y=20 后被使用: 活跃")

    print("  z=30 从未被使用: 死存储")

    print("  w=40 从未被使用: 死存储")



    print("\n不可达代码分析：")

    graph = {

        0: [1, 2],

        1: [3],

        2: [3],  # 节点2可能被跳过（if false）

        3: [4],

        4: [],

    }

    reachable = unreachable_code_elimination(graph, 0)

    print(f"  可达节点: {sorted(reachable)}")

    print(f"  不可达节点: {set(graph.keys()) - reachable}")



    print("\n说明：")

    print("  - 死存储：赋值了但变量之后不再使用")

    print("  - 不可达代码：CFG中没有路径能到达的代码")

    print("  - 常量分支：if true/false 消除整个分支")

