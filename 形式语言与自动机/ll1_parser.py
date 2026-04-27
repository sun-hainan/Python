# -*- coding: utf-8 -*-

"""

算法实现：形式语言与自动机 / ll1_parser



本文件实现 ll1_parser 相关的算法功能。

"""



from typing import Dict, List, Set, Optional, Tuple

from collections import defaultdict





class LL1Parser:

    """

    LL(1)语法分析器

    """

    

    def __init__(self):

        self.variables: Set[str] = set()          # 非终结符集合

        self.terminals: Set[str] = set()          # 终结符集合

        self.productions: Dict[str, List] = {}    # 产生式

        self.start_symbol: str = None             # 起始符号

        

        self.first_sets: Dict[str, Set] = {}      # FIRST集

        self.follow_sets: Dict[str, Set] = {}     # FOLLOW集

        self.parse_table: Dict[Tuple[str, str], List] = {}  # 分析表

        

        self.epsilon = 'ε'

        self.end_marker = '$'  # 输入结束标记

    

    def add_production(self, left: str, right: List[str]):

        """

        添加产生式

        

        参数:

            left: 产生式左部（非终结符）

            right: 产生式右部（符号列表）

        """

        self.variables.add(left)

        

        if left not in self.productions:

            self.productions[left] = []

        

        self.productions[left].append(right)

        

        # 更新终结符

        for symbol in right:

            if symbol not in self.variables:

                self.terminals.add(symbol)

    

    def set_start_symbol(self, symbol: str):

        """

        设置起始符号

        

        参数:

            symbol: 起始非终结符

        """

        self.start_symbol = symbol

        self.variables.add(symbol)

    

    def compute_first_sets(self):

        """

        计算所有非终结符的FIRST集

        

        FIRST(X) 包含从X推导出的任何字符串的首个终结符

        """

        # 初始化FIRST集

        for var in self.variables:

            self.first_sets[var] = set()

        

        # 终结符的FIRST集就是自身

        for term in self.terminals:

            if term != self.epsilon:

                pass  # 终结符不在first_sets中管理

        

        # 迭代计算直到不动点

        changed = True

        while changed:

            changed = False

            

            for left, right_prods in self.productions.items():

                for prod in right_prods:

                    # 规则1：如果产生式是 A -> a...，且a是终结符，则a ∈ FIRST(A)

                    if prod and prod[0] != self.epsilon:

                        if prod[0] in self.terminals:

                            if prod[0] not in self.first_sets[left]:

                                self.first_sets[left].add(prod[0])

                                changed = True

                    

                    # 规则2：如果产生式是 A -> B...，则 FIRST(B) \ {ε} ⊆ FIRST(A)

                    first_of_prod = self._first_of_string(prod)

                    old_size = len(self.first_sets[left])

                    self.first_sets[left].update(first_of_prod - {self.epsilon})

                    if len(self.first_sets[left]) > old_size:

                        changed = True

    

    def _first_of_string(self, string: List[str]) -> Set[str]:

        """

        计算字符串的FIRST集

        

        参数:

            string: 符号列表

        

        返回:

            FIRST(string)

        """

        if not string:

            return {self.epsilon}

        

        result = set()

        

        for i, symbol in enumerate(string):

            if symbol in self.terminals:

                result.add(symbol)

                break

            elif symbol in self.variables:

                result.update(self.first_sets.get(symbol, set()) - {self.epsilon})

                if self.epsilon not in self.first_sets.get(symbol, set()):

                    break

            else:

                # 未知符号

                break

        

        # 如果所有符号都能推导出ε，则添加ε

        if all(s == self.epsilon or (s in self.variables and self.epsilon in self.first_sets.get(s, set())) 

               for s in string):

            result.add(self.epsilon)

        

        return result

    

    def compute_follow_sets(self):

        """

        计算所有非终结符的FOLLOW集

        

        FOLLOW(A) 包含在某些推导中可能出现在A右边的首个终结符

        """

        # 初始化FOLLOW集

        for var in self.variables:

            self.follow_sets[var] = set()

        

        # 起始符号的FOLLOW集包含$

        if self.start_symbol:

            self.follow_sets[self.start_symbol].add(self.end_marker)

        

        # 迭代计算直到不动点

        changed = True

        while changed:

            changed = False

            

            for left, right_prods in self.productions.items():

                for prod in right_prods:

                    # 对于产生式 A -> αBβ

                    # FOLLOW(B) 包含 FIRST(β) - {ε}

                    

                    for i, B in enumerate(prod):

                        if B not in self.variables:

                            continue

                        

                        # 计算β (beta)

                        beta = prod[i + 1:]

                        

                        if beta:

                            # FOLLOW(B) += FIRST(β) - {ε}

                            first_beta = self._first_of_string(beta)

                            old_size = len(self.follow_sets[B])

                            self.follow_sets[B].update(first_beta - {self.epsilon})

                            if len(self.follow_sets[B]) > old_size:

                                changed = True

                        else:

                            # β为空，A -> αB

                            # FOLLOW(B) += FOLLOW(A)

                            old_size = len(self.follow_sets[B])

                            self.follow_sets[B].update(self.follow_sets.get(left, set()))

                            if len(self.follow_sets[B]) > old_size:

                                changed = True

    

    def build_parse_table(self):

        """

        构建LL(1)分析表

        

        对于每个产生式 A -> α：

        - 对于 FIRST(α) 中的每个终结符 a，在 table[A, a] 中放入 A -> α

        - 如果 ε ∈ FIRST(α)，则对于 FOLLOW(A) 中的每个终结符 b，在 table[A, b] 中放入 A -> α

        """

        # 初始化分析表

        for var in self.variables:

            for term in self.terminals:

                if term != self.epsilon:

                    self.parse_table[(var, term)] = None

            self.parse_table[(var, self.end_marker)] = None

        

        # 填充分析表

        for left, right_prods in self.productions.items():

            for prod in right_prods:

                first_prod = self._first_of_string(prod)

                

                # 对于每个 FIRST(α) 中的终结符 a

                for term in first_prod:

                    if term != self.epsilon:

                        self.parse_table[(left, term)] = prod

                

                # 如果 ε ∈ FIRST(α)

                if self.epsilon in first_prod:

                    follow_a = self.follow_sets.get(left, set())

                    for term in follow_a:

                        self.parse_table[(left, term)] = prod

    

    def parse(self, input_string: str) -> Tuple[bool, List[str]]:

        """

        解析输入字符串

        

        参数:

            input_string: 输入字符串

        

        返回:

            (是否成功, 推导过程)

        """

        if not self.parse_table:

            self.compute_first_sets()

            self.compute_follow_sets()

            self.build_parse_table()

        

        # 初始化分析栈

        stack = [self.end_marker, self.start_symbol]

        input_tokens = list(input_string) + [self.end_marker]

        

        derivations = []

        step = 0

        

        while stack:

            step += 1

            if step > 1000:  # 防止无限循环

                return False, derivations

            

            top = stack[-1]

            current_input = input_tokens[0]

            

            if top == self.end_marker and current_input == self.end_marker:

                # 成功接受

                derivations.append(f"Accept!")

                return True, derivations

            

            if top == current_input:

                # 匹配

                stack.pop()

                input_tokens.pop(0)

                derivations.append(f"Match: {current_input}")

            

            elif (top, current_input) in self.parse_table:

                prod = self.parse_table[(top, current_input)]

                

                if prod is None:

                    return False, derivations

                

                stack.pop()

                derivations.append(f"Output: {top} -> {' '.join(prod) if prod else 'ε'}")

                

                # 将产生式右部逆序入栈

                if prod:

                    for symbol in reversed(prod):

                        if symbol != self.epsilon:

                            stack.append(symbol)

            

            else:

                # 语法错误

                derivations.append(f"Error: Unexpected {current_input}")

                return False, derivations

        

        return False, derivations

    

    def is_ll1(self) -> bool:

        """

        检查文法是否是LL(1)文法

        

        LL(1)文法的条件：每个产生式的SELECT集不相交

        

        返回:

            是否是LL(1)文法

        """

        if not self.first_sets:

            self.compute_first_sets()

        if not self.follow_sets:

            self.compute_follow_sets()

        

        # 检查每个非终结符的产生式

        for left, right_prods in self.productions.items():

            select_sets = []

            

            for prod in right_prods:

                first_prod = self._first_of_string(prod)

                

                if self.epsilon in first_prod:

                    select = first_prod - {self.epsilon} | self.follow_sets.get(left, set())

                else:

                    select = first_prod

                

                select_sets.append(select)

            

            # 检查是否有交集

            for i, set1 in enumerate(select_sets):

                for j, set2 in enumerate(select_sets):

                    if i < j and set1 & set2:

                        return False

        

        return True





def create_sample_grammar() -> LL1Parser:

    """

    创建示例文法

    

    E -> T E'

    E' -> + T E' | ε

    T -> F T'

    T' -> * F T' | ε

    F -> ( E ) | id

    """

    parser = LL1Parser()

    

    # E -> T E'

    parser.add_production('E', ['T', "E'"])

    # E' -> + T E' | ε

    parser.add_production("E'", ['+', 'T', "E'"])

    parser.add_production("E'", [])

    # T -> F T'

    parser.add_production('T', ['F', "T'"])

    # T' -> * F T' | ε

    parser.add_production("T'", ['*', 'F', "T'"])

    parser.add_production("T'", [])

    # F -> ( E ) | id

    parser.add_production('F', ['(', 'E', ')'])

    parser.add_production('F', ['id'])

    

    parser.set_start_symbol('E')

    

    return parser





# ==================== 测试代码 ====================

if __name__ == "__main__":

    # 测试用例1：基本LL(1)文法

    print("=" * 50)

    print("测试1: LL(1)文法分析")

    print("=" * 50)

    

    parser = create_sample_grammar()

    

    print("文法规则:")

    for left, prods in parser.productions.items():

        for prod in prods:

            right = ' '.join(prod) if prod else 'ε'

            print(f"  {left} -> {right}")

    

    # 计算FIRST和FOLLOW集

    parser.compute_first_sets()

    parser.compute_follow_sets()

    

    print("\nFIRST集:")

    for var, first in parser.first_sets.items():

        print(f"  FIRST({var}) = {first}")

    

    print("\nFOLLOW集:")

    for var, follow in parser.follow_sets.items():

        print(f"  FOLLOW({var}) = {follow}")

    

    # 测试用例2：构建分析表

    print("\n" + "=" * 50)

    print("测试2: LL(1)分析表")

    print("=" * 50)

    

    parser.build_parse_table()

    

    print("分析表 (部分):")

    terminals = ['(', ')', '+', '*', 'id', '$']

    for var in ['E', "E'", 'T', "T'", 'F']:

        print(f"\n{var}:")

        for term in terminals:

            prod = parser.parse_table.get((var, term))

            if prod is not None:

                right = ' '.join(prod) if prod else 'ε'

                print(f"  [{term}] -> {right}")

    

    # 测试用例3：解析字符串

    print("\n" + "=" * 50)

    print("测试3: 解析输入字符串")

    print("=" * 50)

    

    test_inputs = ['id', 'id+id', '(id)', '(id+id)*id']

    

    for input_str in test_inputs:

        success, derivations = parser.parse(input_str)

        print(f"\n输入: '{input_str}'")

        print(f"结果: {'成功' if success else '失败'}")

        if success:

            print("推导过程:")

            for d in derivations[:10]:  # 只显示前10步

                print(f"  {d}")

    

    # 测试用例4：检查是否是LL(1)

    print("\n" + "=" * 50)

    print("测试4: LL(1)性检查")

    print("=" * 50)

    

    parser2 = LL1Parser()

    parser2.add_production('S', ['i', 'E', 't', 'S', 'E'])

    parser2.add_production('S', ['c'])

    parser2.add_production('E', ['E', '+', 'T'])

    parser2.add_production('E', ['T'])

    parser2.add_production('T', ['T', '*', 'F'])

    parser2.add_production('T', ['F'])

    parser2.add_production('F', ['(', 'E', ')'])

    parser2.add_production('F', ['i'])

    parser2.set_start_symbol('S')

    

    is_ll1 = parser2.is_ll1()

    print(f"文法是否是LL(1): {is_ll1}")

    

    # 测试用例5：简单算术表达式

    print("\n" + "=" * 50)

    print("测试5: 简单表达式文法")

    print("=" * 50)

    

    parser3 = LL1Parser()

    parser3.add_production('E', ['E', '+', 'T'])

    parser3.add_production('E', ['T'])

    parser3.add_production('T', ['T', '*', 'F'])

    parser3.add_production('T', ['F'])

    parser3.add_production('F', ['(', 'E', ')'])

    parser3.add_production('F', ['id'])

    parser3.set_start_symbol('E')

    

    # 注意：这个文法不是LL(1)，因为左递归

    is_ll1 = parser3.is_ll1()

    print(f"文法是否是LL(1): {is_ll1}")

    

    if not is_ll1:

        print("说明: 该文法有左递归，不是LL(1)文法")

        print("需要消除左递归才能用于LL(1)分析")

