# -*- coding: utf-8 -*-

"""

算法实现：形式语言与自动机 / ll_parser



本文件实现 ll_parser 相关的算法功能。

"""



from typing import List, Dict, Set, Tuple





class LL1Parser:

    """LL(1)语法分析器"""



    def __init__(self, productions: Dict[str, List[str]],

                 terminals: Set[str], nonterminals: Set[str]):

        """

        参数：

            productions: 产生式 {A: [α1, α2, ...]}

            terminals: 终结符集合

            nonterminals: 非终结符集合

        """

        self.productions = productions

        self.terminals = terminals

        self.nonterminals = nonterminals

        self.parsing_table = {}

        self.first = {}

        self.follow = {}



    def first_sets(self) -> Dict[str, Set[str]]:

        """计算FIRST集合"""

        self.first = {t: {t} for t in self.terminals}

        self.first.update({A: set() for A in self.nonterminals})



        changed = True

        while changed:

            changed = False

            for A, rhs_list in self.productions.items():

                for rhs in rhs_list:

                    if not rhs:  # ε产生式

                        if 'ε' not in self.first[A]:

                            self.first[A].add('ε')

                            changed = True

                    else:

                        first_sym = rhs[0]

                        if first_sym in self.terminals:

                            if first_sym not in self.first[A]:

                                self.first[A].add(first_sym)

                                changed = True

                        elif first_sym in self.nonterminals:

                            before = len(self.first[A])

                            self.first[A].update(self.first[first_sym] - {'ε'})

                            if len(self.first[A]) > before:

                                changed = True

                            # 如果first(first_sym)包含ε，继续看下一个符号

                            if 'ε' in self.first[first_sym]:

                                pass  # 继续



        return self.first



    def parse(self, input_str: str) -> bool:

        """

        解析输入字符串



        返回：是否接受

        """

        # 假设已经构建好parsing_table

        # 简化实现

        input_tokens = list(input_str) + ['$']

        stack = ['$', 'S']  # S是起始符



        i = 0

        while stack:

            top = stack[-1]

            current = input_tokens[i]



            if top == current:

                stack.pop()

                i += 1

            elif top in self.terminals:

                return False

            elif (top, current) in self.parsing_table:

                stack.pop()

                rhs = self.parsing_table[(top, current)]

                if rhs != ['ε']:

                    for sym in reversed(rhs):

                        stack.append(sym)

            else:

                return False



        return i == len(input_tokens)





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== LL(1)语法分析测试 ===\n")



    # 简单算术表达式文法

    # E -> T E'

    # E' -> + T E' | ε

    # T -> F T'

    # T' -> * F T' | ε

    # F -> ( E ) | id



    productions = {

        'E': ['T Ep'],

        'Ep': ['+ T Ep', 'ε'],

        'T': ['F Tp'],

        'Tp': ['* F Tp', 'ε'],

        'F': ['( E )', 'id'],

    }



    terminals = {'+', '*', '(', ')', 'id'}

    nonterminals = {'E', 'Ep', 'T', 'Tp', 'F'}



    parser = LL1Parser(productions, terminals, nonterminals)

    parser.first_sets()



    print("FIRST集合:")

    for var, first_set in parser.first.items():

        print(f"  FIRST({var}) = {first_set}")



    print("\n说明：")

    print("  - LL(1)分析需要没有左递归和左因子")

    print("  - Java、C++等主流语言用LL或LR分析器")

    print("  - ANTLR等工具自动生成LL(*)分析器")

