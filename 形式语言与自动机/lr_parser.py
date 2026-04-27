# -*- coding: utf-8 -*-
"""
算法实现：形式语言与自动机 / lr_parser

本文件实现 lr_parser 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple
from collections import deque


class LR0Item:
    """LR(0)项目"""

    def __init__(self, production: str, dot: int):
        self.production = production  # "A -> α.β"
        self.dot = dot

    def __eq__(self, other):
        return self.production == other.production and self.dot == other.dot

    def __hash__(self):
        return hash((self.production, self.dot))


class LR0Parser:
    """LR(0)分析器"""

    def __init__(self, productions: Dict[str, List[str]]):
        self.productions = productions
        self.augmented_grammar()

    def augmented_grammar(self):
        """增广文法：添加 S' -> S"""
        start = list(self.productions.keys())[0]
        self.productions["S'"] = [start]
        self.start = "S'"

    def closure(self, items: Set[LR0Item]) -> Set[LR0Item]:
        """计算项目集的闭包"""
        closure_set = set(items)
        queue = deque(items)

        while queue:
            item = queue.popleft()
            prod = item.production
            rhs_list = self.productions.get(prod, [])

            for rhs in rhs_list:
                if not rhs:  # ε产生式
                    continue
                # 找到点的位置（简化处理）
                dot_pos = item.dot
                # 点后的符号
                if dot_pos < len(prod.split('->')[1].strip()):
                    beta = prod.split('->')[1].strip()[dot_pos:]
                    if beta and beta[0].isupper():
                        # 添加B -> .γ
                        for alt_rhs in self.productions.get(beta[0], []):
                            new_item = LR0Item(f"{beta[0]} -> .{alt_rhs}", 0)
                            if new_item not in closure_set:
                                closure_set.add(new_item)
                                queue.append(new_item)

        return closure_set

    def goto(self, items: Set[LR0Item], symbol: str) -> Set[LR0Item]:
        """从items通过symbol的转移"""
        next_items = set()
        for item in items:
            prod = item.production
            dot_pos = item.dot
            rhs = prod.split('->')[1].strip()

            if dot_pos < len(rhs):
                if rhs[dot_pos] == symbol:
                    new_item = LR0Item(prod, dot_pos + 1)
                    next_items.add(new_item)

        return self.closure(next_items) if next_items else set()


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== LR(0)分析器测试 ===\n")

    # 简单算术表达式文法（增广后）
    productions = {
        "S'": ['E'],
        'E': ['E + T', 'T'],
        'T': ['T * F', 'F'],
        'F': ['( E )', 'id'],
    }

    parser = LR0Parser(productions)

    print("LR(0)项目集构造：")
    print("  S' -> .E (初始项目)")

    # 项目闭包
    init_item = LR0Item("S' -> .E", 0)
    closure_set = parser.closure({init_item})

    print(f"\n初始项目集的闭包:")
    for item in closure_set:
        print(f"  {item.production} (dot at {item.dot})")

    print("\n说明：")
    print("  - LR(0)是最简单的LR分析方法")
    print("  - 实际常用LR(1)或LALR(1)")
    print("  - Yacc/Bison使用LALR(1)")
    print("  - LR分析器能检测所有语法错误")
