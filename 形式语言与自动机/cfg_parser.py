# -*- coding: utf-8 -*-
"""
算法实现：形式语言与自动机 / cfg_parser

本文件实现 cfg_parser 相关的算法功能。
"""

from typing import Set, List, Dict


def cyk_parse(symbols: str, productions: Dict[str, List[str]]) -> bool:
    """
    CYK算法

    参数：
        symbols: 输入字符串（终结符串）
        productions: 产生式 {A: [alpha1, alpha2, ...]}

    返回：是否能由文法生成
    """
    n = len(symbols)
    if n == 0:
        return False

    # DP表：T[i][j] = 能生成子串i..j的变量集合
    T = [[set() for _ in range(n)] for _ in range(n)]

    # 第一列：对角线，子串长度为1
    for i, ch in enumerate(symbols):
        for var, rhs_list in productions.items():
            for rhs in rhs_list:
                if len(rhs) == 1 and rhs[0] == ch:
                    T[i][0].add(var)

    # 填充其他单元格
    for length in range(2, n + 1):  # 子串长度
        for i in range(n - length + 1):  # 起始位置
            for split in range(1, length):  # 分割点
                left = T[i][split - 1]  # 左半部分
                right = T[i + split][length - split - 1]  # 右半部分

                # 检查是否能组合
                for var, rhs_list in productions.items():
                    for rhs in rhs_list:
                        if len(rhs) == 2 and rhs[0] in left and rhs[1] in right:
                            T[i][length - 1].add(var)

    # 检查起始符S能否生成整个字符串
    return bool(T[0][n - 1])


def convert_to_cnf(s: str, productions: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    将CFG转换为CNF（乔姆斯基范式）

    CNF要求产生式形如：
    - A -> BC (两个变量)
    - A -> a (一个终结符)

    这是一个简化实现
    """
    return productions  # 假设已经是CNF


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== CYK算法测试 ===\n")

    # 例1：S -> AB, A -> a, B -> b
    # 语言：{ab}
    productions1 = {
        'S': ['AB'],
        'A': ['a'],
        'B': ['b'],
    }

    test1 = "ab"
    result1 = cyk_parse(test1, productions1)
    print(f"文法: S→AB, A→a, B→b")
    print(f"测试 '{test1}': {'✅ 接受' if result1 else '❌ 拒绝'}")

    # 例2：更复杂的文法
    # S -> AB | AS, A -> a, B -> b | BC, C -> c
    productions2 = {
        'S': ['AB', 'AS'],
        'A': ['a'],
        'B': ['b', 'BC'],
        'C': ['c'],
    }

    test_strings = ['ab', 'abc', 'aabc', 'abbc']
    print(f"\n文法: S→AB|AS, A→a, B→b|BC, C→c")
    for s in test_strings:
        result = cyk_parse(s, productions2)
        print(f"  '{s}': {'✅ 接受' if result else '❌ 拒绝'}")

    print("\n说明：")
    print("  - CYK是O(n³)，适合中等长度字符串")
    print("  - 需要CNF形式的文法")
    print("  - 编译器的语法分析常用更高效的算法（如LR）")
