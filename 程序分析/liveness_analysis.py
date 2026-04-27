# -*- coding: utf-8 -*-
"""
算法实现：程序分析 / liveness_analysis

本文件实现 liveness_analysis 相关的算法功能。
"""

from typing import Set, List, Dict


def liveness_analysis(block_statements: List[tuple], cfg_edges: List[tuple]) -> Dict[int, Set[str]]:
    """
    活跃变量分析

    参数：
        block_statements: 每个块的语句 [(var, 'def'/'use'), ...]
        cfg_edges: 控制流边 [(src, dst), ...]

    返回：每个块的IN集合（活变量）
    """
    n = len(block_statements)

    # USE和DEF
    use = [set() for _ in range(n)]
    def_set = [set() for _ in range(n)]

    for i, stmts in enumerate(block_statements):
        for var, kind in stmts:
            if kind == 'use':
                use[i].add(var)
            elif kind == 'def':
                def_set[i].add(var)

    # 构建后继关系
    succs = [[] for _ in range(n)]
    preds = [[] for _ in range(n)]
    for src, dst in cfg_edges:
        succs[src].append(dst)
        preds[dst].append(src)

    # 反向迭代
    out_sets = [set() for _ in range(n)]
    changed = True

    while changed:
        changed = False
        for i in range(n - 1, -1, -1):
            # OUT[B] = ∪ IN[Succ]
            new_out = set()
            for s in succs[i]:
                new_out |= out_sets[s]

            # IN[B] = USE[B] ∪ (OUT[B] - DEF[B])
            new_in = use[i] | (new_out - def_set[i])

            if new_out != out_sets[i]:
                out_sets[i] = new_out
                changed = True

    return {i: out_sets[i] for i in range(n)}


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 活跃变量分析测试 ===\n")

    # 示例程序：
    # 1: a = input()      # def a
    # 2: b = a + 1        # use a, def b
    # 3: c = b * 2        # use b, def c
    # 4: output(c)        # use c
    # 5: d = c + a        # use c, use a, def d

    statements = [
        [('a', 'def')],                    # 块0: a = input
        [('a', 'use'), ('b', 'def')],      # 块1: b = a + 1
        [('b', 'use'), ('c', 'def')],      # 块2: c = b * 2
        [('c', 'use')],                    # 块3: output(c)
        [('c', 'use'), ('a', 'use'), ('d', 'def')],  # 块4: d = c + a
    ]

    # 控制流
    edges = [
        (0, 1), (1, 2), (2, 3), (2, 4),
        (3, 4), (4, 1),  # 循环
    ]

    results = liveness_analysis(statements, edges)

    print("程序块：")
    block_names = ["a=input", "b=a+1", "c=b*2", "output(c)", "d=c+a"]
    for i, name in enumerate(block_names):
        print(f"  BB{i}: {name}")

    print("\n活跃变量（IN集合）：")
    for i in range(len(statements)):
        print(f"  BB{i} ({block_names[i]}): {results[i]}")

    print("\n说明：")
    print("  - 块1的IN包含a（因为a在块1被使用前已定义）")
    print("  - 块2的IN包含b和a（因为b和a在c=b*2前需要是活跃的）")
    print("  - 块3的IN包含c（因为output(c)需要c）")
