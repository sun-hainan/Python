# -*- coding: utf-8 -*-

"""

算法实现：形式语言与自动机 / lr0_parser



本文件实现 lr0_parser 相关的算法功能。

"""



from typing import Dict, List, Set, Tuple, Optional





class LR0Parser:

    """

    LR(0)分析器

    """

    

    def __init__(self):

        self.grammar: Dict[str, List[str]] = {}

        self.augmented_grammar: Dict[str, List[str]] = {}

        self.start_symbol: str = None

        self.terminals: Set[str] = set()

        self.non_terminals: Set[str] = set()

        

        self.items: List[Set[Tuple]] = []

        self.go_to: Dict[Tuple[int, str], int] = {}

        self.action: Dict[Tuple[int, str], str] = {}

        self.goto_table: Dict[Tuple[int, str], int] = {}

    

    def build_grammar(self, productions: List[Tuple[str, List[str]]]):

        """构建文法"""

        self.grammar.clear()

        for left, right in productions:

            if left not in self.grammar:

                self.grammar[left] = []

            self.grammar[left].append(right)

        

        self.start_symbol = productions[0][0]

        self._compute_symbols()

    

    def _compute_symbols(self):

        """计算终结符和非终结符"""

        self.non_terminals = set(self.grammar.keys())

        self.terminals = set()

        

        for prods in self.grammar.values():

            for prod in prods:

                for symbol in prod:

                    if symbol not in self.non_terminals:

                        self.terminals.add(symbol)

    

    def canonical_collection(self) -> List[Set[Tuple]]:

        """构建LR(0)项的规范族"""

        pass  # 简化实现





if __name__ == "__main__":

    print("=" * 50)

    print("LR(0)分析器演示")

    print("=" * 50)

    

    # 简单文法示例

    productions = [

        ('S', ['E']),

        ('E', ['E', '+', 'T']),

        ('E', ['T']),

        ('T', ['id']),

    ]

    

    parser = LR0Parser()

    parser.build_grammar(productions)

    

    print("文法规则:")

    for left, prods in parser.grammar.items():

        for prod in prods:

            print(f"  {left} -> {' '.join(prod)}")

