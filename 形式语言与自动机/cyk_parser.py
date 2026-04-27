# -*- coding: utf-8 -*-
"""
算法实现：形式语言与自动机 / cyk_parser

本文件实现 cyk_parser 相关的算法功能。
"""

from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


class CYKParser:
    """
    CYK算法实现
    
    用于判定字符串是否属于由CNF文法生成的语言
    """
    
    def __init__(self):
        self.variables: Set[str] = set()      # 变量集合
        self.terminals: Set[str] = set()       # 终结符集合
        self.productions: Dict[str, List] = {} # 产生式 A -> [B,C] 或 A -> 'a'
        self.start_symbol: str = None          # 起始符号
    
    def add_production(self, left: str, right: List):
        """
        添加产生式
        
        参数:
            left: 产生式左部（变量）
            right: 产生式右部（变量列表或终结符字符串）
        """
        self.variables.add(left)
        
        if left not in self.productions:
            self.productions[left] = []
        
        self.productions[left].append(right)
        
        # 检查是否有终结符产生式
        if len(right) == 1 and isinstance(right[0], str) and len(right[0]) == 1:
            # 检查是否是小写（终结符约定）
            if right[0].islower() or right[0] in '(){}[]':
                self.terminals.add(right[0])
    
    def set_start_symbol(self, symbol: str):
        """
        设置起始符号
        
        参数:
            symbol: 起始变量
        """
        self.start_symbol = symbol
        self.variables.add(symbol)
    
    def to_cnf(self) -> bool:
        """
        将文法转换为Chomsky范式
        
        返回:
            是否转换成功
        """
        # 这是简化版本，假设输入已经是CNF格式
        # 完整的CNF转换需要多步
        return True
    
    def parse(self, string: str) -> Tuple[bool, Optional[Dict]]:
        """
        使用CYK算法解析字符串
        
        参数:
            string: 输入字符串
        
        返回:
            (是否能解析, 解析表)
        """
        n = len(string)
        
        if n == 0:
            # 检查是否能产生空字符串
            if '' in [''.join(p) for p in self.productions.get(self.start_symbol, [])]:
                return True, {}
            return False, None
        
        # DP表：table[i][j] 表示子串string[i:j+1]能推出的变量集合
        table = [[set() for _ in range(n)] for _ in range(n)]
        
        # 第一列（长度1的子串）
        for i, char in enumerate(string):
            for variable, productions in self.productions.items():
                for prod in productions:
                    if len(prod) == 1 and prod[0] == char:
                        table[i][i].add(variable)
        
        # 长度从2到n
        for length in range(2, n + 1):
            for i in range(n - length + 1):
                j = i + length - 1
                
                # 尝试所有分割点
                for k in range(i, j):
                    # table[i][k] 乘以 table[k+1][j]
                    for variable, productions in self.productions.items():
                        for prod in productions:
                            if len(prod) == 2:
                                B, C = prod
                                if B in table[i][k] and C in table[k+1][j]:
                                    table[i][j].add(variable)
        
        # 检查起始符号是否在table[0][n-1]中
        if self.start_symbol in table[0][n-1]:
            return True, {'table': table, 'derivation': self._find_derivation(table, string)}
        
        return False, None
    
    def _find_derivation(self, table: List[List[Set]], string: str) -> Dict:
        """
        找到一种推导方式
        
        参数:
            table: CYK表
            string: 输入字符串
        
        返回:
            推导信息
        """
        n = len(string)
        
        return {
            'start': self.start_symbol,
            'length': n,
            'can_derive': self.start_symbol in table[0][n-1]
        }
    
    def is_member(self, string: str) -> bool:
        """
        判定字符串是否是文法的成员
        
        参数:
            string: 输入字符串
        
        返回:
            是否属于语言
        """
        result, _ = self.parse(string)
        return result


def create_cnf_grammar(rules: List[Tuple[str, str]]) -> CYKParser:
    """
    从产生式规则创建CNF文法
    
    参数:
        rules: 产生式列表，格式为 ('A', 'BC') 或 ('A', 'a')
    
    返回:
        CYKParser对象
    """
    parser = CYKParser()
    
    for left, right in rules:
        # 将字符串转换为列表
        prod = list(right) if len(right) > 1 else [right]
        parser.add_production(left, prod)
    
    if rules:
        parser.set_start_symbol(rules[0][0])
    
    return parser


def example_s_simple() -> CYKParser:
    """
    创建简单文法 S -> AB | BC, A -> a, B -> b, C -> c
    
    该文法生成语言: {ab, abc}
    """
    parser = CYKParser()
    
    parser.add_production('S', ['A', 'B'])
    parser.add_production('S', ['B', 'C'])
    parser.add_production('A', ['a'])
    parser.add_production('B', ['b'])
    parser.add_production('C', ['c'])
    parser.set_start_symbol('S')
    
    return parser


def example_balanced_parens() -> CYKParser:
    """
    创建平衡括号文法
    
    S -> SS | (S) | ε
    需要转换为CNF
    """
    parser = CYKParser()
    
    # CNF格式
    parser.add_production('S', ['A', 'B'])  # ( )
    parser.add_production('S', ['S', 'S'])  # SS
    parser.add_production('A', ['('])
    parser.add_production('B', [')'])
    
    parser.set_start_symbol('S')
    
    return parser


def example_an_bn() -> CYKParser:
    """
    创建语言 a^n b^n 的文法（CNF格式）
    
    S -> AB | aSb | ε
    转换为CNF需要额外处理
    """
    # 简化版本
    parser = CYKParser()
    
    # S -> AB, A -> a, B -> b
    parser.add_production('S', ['A', 'B'])
    parser.add_production('A', ['a'])
    parser.add_production('B', ['b'])
    
    parser.set_start_symbol('S')
    
    return parser


def print_parse_table(table: List[List[Set]], string: str):
    """
    打印CYK解析表
    
    参数:
        table: CYK表
        string: 输入字符串
    """
    n = len(string)
    
    print("CYK解析表:")
    print(" " * 8, end='')
    
    for i, char in enumerate(string):
        print(f"{char:^7}", end='')
    print()
    
    for length in range(n):
        start = n - 1 - length
        print(f"长度{length+1:2d}: ", end='')
        
        for i in range(n):
            if i < start:
                print(" " * 8, end='')
            elif i > start + length:
                print(" " * 8, end='')
            else:
                j = start + length
                if i == j:
                    vars = ','.join(sorted(table[i][j])) if table[i][j] else '∅'
                    print(f"{vars:^7}", end='')
                else:
                    print(" " * 8, end='')
        print()


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：简单文法
    print("=" * 50)
    print("测试1: 简单文法 S -> AB, A -> a, B -> b")
    print("=" * 50)
    
    parser = example_s_simple()
    
    test_strings = ['ab', 'abc', 'a', 'b', 'ac', 'ba']
    
    for s in test_strings:
        result, _ = parser.parse(s)
        print(f"  '{s}': {'∈' if result else '∉'}")
    
    # 测试用例2：更复杂的文法
    print("\n" + "=" * 50)
    print("测试2: 更复杂的文法")
    print("=" * 50)
    
    # 文法: S -> AS | a, A -> SA | b
    parser = CYKParser()
    parser.add_production('S', ['A', 'S'])
    parser.add_production('S', ['a'])
    parser.add_production('A', ['S', 'A'])
    parser.add_production('A', ['b'])
    parser.set_start_symbol('S')
    
    test_strings = ['a', 'b', 'ab', 'ba', 'aba', 'bab']
    
    print("文法: S -> AS | a, A -> SA | b")
    for s in test_strings:
        result, info = parser.parse(s)
        print(f"  '{s}': {'∈' if result else '∉'}")
    
    # 测试用例3：CYK表打印
    print("\n" + "=" * 50)
    print("测试3: CYK解析表")
    print("=" * 50)
    
    parser = example_s_simple()
    string = 'abc'
    
    result, info = parser.parse(string)
    if info and 'table' in info:
        print_parse_table(info['table'], string)
    
    # 测试用例4：a^n b^n 文法
    print("\n" + "=" * 50)
    print("测试4: 语言 a^n b^n")
    print("=" * 50)
    
    parser = example_an_bn()
    
    test_strings = ['ab', 'aabb', 'aaabbb', 'aaaabbbb']
    
    for s in test_strings:
        result, _ = parser.parse(s)
        print(f"  '{s}': {'∈' if result else '∉'}")
    
    # 测试用例5：从规则创建文法
    print("\n" + "=" * 50)
    print("测试5: 从规则创建文法")
    print("=" * 50)
    
    rules = [
        ('S', 'AB'),
        ('S', 'BC'),
        ('A', 'BA'),
        ('A', 'a'),
        ('B', 'CC'),
        ('B', 'b'),
        ('C', 'AB'),
        ('C', 'a'),
    ]
    
    parser = create_cnf_grammar(rules)
    
    print("文法规则:")
    for left, right in rules:
        print(f"  {left} -> {right}")
    
    test_strings = ['aba', 'baa', 'aab', 'aaa']
    
    for s in test_strings:
        result, _ = parser.parse(s)
        print(f"  '{s}': {'∈' if result else '∉'}")
    
    # 测试用例6：性能测试
    print("\n" + "=" * 50)
    print("测试6: 性能测试")
    print("=" * 50)
    
    import time
    
    # 简单文法
    parser = example_s_simple()
    
    for n in [5, 10, 15, 20]:
        string = 'a' + 'b' * (n - 1)
        start = time.time()
        result, _ = parser.parse(string)
        elapsed = time.time() - start
        print(f"  长度={n}: {'∈' if result else '∉'} ({elapsed*1000:.2f}ms)")
