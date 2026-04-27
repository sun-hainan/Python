# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / parser



本文件实现 parser 相关的算法功能。

"""



from typing import List, Dict, Tuple, Optional, Any

from dataclasses import dataclass

from enum import Enum, auto



# ========== 文法定义 ==========



class GrammarSymbol:

    """文法符号基类"""

    pass



@dataclass

class NonTerminal(GrammarSymbol):

    """非终结符"""

    name: str

    

    def __repr__(self):

        return f"NT({self.name})"



@dataclass

class Terminal(GrammarSymbol):

    """终结符"""

    name: str

    

    def __repr__(self):

        return f"T({self.name})"



@dataclass

class Epsilon(GrammarSymbol):

    """空串（ε）"""

    def __repr__(self):

        return "ε"



class Production:

    """产生式"""

    def __init__(self, lhs: NonTerminal, rhs: List[GrammarSymbol]):

        self.lhs = lhs

        self.rhs = rhs

    

    def __repr__(self):

        return f"{self.lhs} -> {' '.join(str(s) for s in self.rhs)}"





@dataclass

class Item:

    """LR项目（产生式 + 位置）"""

    production: Production

    dot_position: int  # · 的位置（0表示在最左边）

    

    def __repr__(self):

        rhs_with_dot = self.rhs[:self.dot_position] + [Terminal('·')] + self.rhs[self.dot_position:]

        return f"[{self.production.lhs} -> {' '.join(str(s) for s in rhs_with_dot)}]"

    

    def next_symbol(self) -> Optional[GrammarSymbol]:

        """获取·后面的符号"""

        if self.dot_position < len(self.production.rhs):

            return self.production.rhs[self.dot_position]

        return None

    

    def is_reduced(self) -> bool:

        """是否可规约（·在末尾）"""

        return self.dot_position >= len(self.production.rhs)





# ========== FIRST和FOLLOW集 ==========



class FirstSetCalculator:

    """计算FIRST集"""

    

    def __init__(self, productions: List[Production]):

        self.productions = productions

        self.first: Dict[str, set] = {}

        self._compute_first()

    

    def _compute_first(self):

        """迭代计算FIRST集"""

        # 初始化：所有终结符的FIRST是自身

        for prod in self.productions:

            nt_name = prod.lhs.name

            if nt_name not in self.first:

                self.first[nt_name] = set()

        

        changed = True

        while changed:

            changed = False

            

            for prod in self.productions:

                lhs_name = prod.lhs.name

                

                for symbol in prod.rhs:

                    if isinstance(symbol, Terminal):

                        if symbol.name not in self.first.get(lhs_name, set()):

                            self.first[lhs_name].add(symbol.name)

                            changed = True

                        break

                    elif isinstance(symbol, NonTerminal):

                        first_of_symbol = self.first.get(symbol.name, set())

                        for t in first_of_symbol:

                            if t != 'ε' and t not in self.first[lhs_name]:

                                self.first[lhs_name].add(t)

                                changed = True

                        

                        if 'ε' not in first_of_symbol:

                            break

                    else:

                        break





class FollowSetCalculator:

    """计算FOLLOW集"""

    

    def __init__(self, productions: List[Production], first_calc: FirstSetCalculator, start_symbol: str):

        self.productions = productions

        self.first_calc = first_calc

        self.start_symbol = start_symbol

        self.follow: Dict[str, set] = {}

        self._compute_follow()

    

    def _compute_follow(self):

        """计算FOLLOW集"""

        # 初始化

        for prod in self.productions:

            nt_name = prod.lhs.name

            if nt_name not in self.follow:

                self.follow[nt_name] = set()

        

        # 开始符号的FOLLOW包含$

        self.follow[self.start_symbol].add('$')

        

        changed = True

        while changed:

            changed = False

            

            for prod in self.productions:

                for i, symbol in enumerate(productions.rhs if hasattr(productions, 'rhs') else prod.rhs):

                    if not isinstance(symbol, NonTerminal):

                        continue

                    

                    # 计算FOLLOW(symbol)

                    rest = prod.rhs[i + 1:] if isinstance(productions, list) else prod.rhs[i + 1:]

                    

                    if not rest:

                        # A → α·B，FOLLOW(B) ⊆ FOLLOW(A)

                        for f in self.follow.get(prod.lhs.name, set()):

                            if f not in self.follow[symbol.name]:

                                self.follow[symbol.name].add(f)

                                changed = True

                    else:

                        # FIRST(β) - {ε} ⊆ FOLLOW(B)

                        for sym in rest:

                            if isinstance(sym, Terminal):

                                if sym.name not in self.follow[symbol.name]:

                                    self.follow[symbol.name].add(sym.name)

                                    changed = True

                                break

                            elif isinstance(sym, NonTerminal):

                                first_sym = self.first_calc.first.get(sym.name, set())

                                for t in first_sym:

                                    if t != 'ε' and t not in self.follow[symbol.name]:

                                        self.follow[symbol.name].add(t)

                                        changed = True

                                

                                if 'ε' not in first_sym:

                                    break

                        

                        # 如果所有β都能推出ε

                        all_epsilon = all(

                            'ε' in self.first_calc.first.get(s.name, set()) 

                            if isinstance(s, NonTerminal) else s.name == 'ε'

                            for s in rest

                        )

                        

                        if all_epsilon:

                            for f in self.follow.get(prod.lhs.name, set()):

                                if f not in self.follow[symbol.name]:

                                    self.follow[symbol.name].add(f)

                                    changed = True





# ========== LL(1) 分析表 ==========



class LL1Parser:

    """

    LL(1)语法分析器

    自顶向下预测分析，无需回溯

    """

    

    def __init__(self, grammar: Dict[str, List[List[str]]]):

        self.grammar = grammar

        self.terminals = set()

        self.nonterminals = set(grammar.keys())

        self.first = {}

        self.follow = {}

        self.parse_table: Dict[Tuple[str, str], Tuple[str, List[str]]] = {}

        

        self._build_first_follow()

        self._build_parse_table()

    

    def _build_first_follow(self):

        """构建FIRST和FOLLOW集"""

        # 简化实现

        for nt in self.nonterminals:

            self.first[nt] = set()

            self.follow[nt] = set()

        

        # 计算FIRST

        for _ in range(10):  # 迭代直到收敛

            for nt, productions in self.grammar.items():

                for prod in productions:

                    for sym in prod:

                        if sym.isupper() and len(sym) == 1:

                            self.first[nt].add(sym)

                            break

                        elif sym == 'ε':

                            self.first[nt].add('ε')

        

        # FOLLOW = FOLLOW

        self.follow[self.nonterminals.pop()].add('$')

    

    def _build_parse_table(self):

        """构建LL(1)分析表"""

        for nt, productions in self.grammar.items():

            for prod in productions:

                # 简化：每个产生式对应唯一的输入符号

                if prod:

                    first_sym = prod[0] if prod[0] != 'ε' else 'ε'

                    self.parse_table[(nt, first_sym)] = (nt, prod)

    

    def parse(self, tokens: List[str]) -> bool:

        """

        执行LL(1)分析

        返回: 是否成功解析

        """

        stack = ['$', 'S']  # S是开始符号

        input_tokens = tokens + ['$']

        idx = 0

        

        while stack:

            top = stack.pop()

            current = input_tokens[idx]

            

            if top == '$':

                return current == '$'

            

            if top.isupper() and len(top) == 1:

                # 非终结符，查找分析表

                key = (top, current)

                if key in self.parse_table:

                    _, production = self.parse_table[key]

                    for sym in reversed(production):

                        if sym != 'ε':

                            stack.append(sym)

                elif 'ε' in self.grammar.get(top, []):

                    pass  # 推导空串

                else:

                    return False

            elif top == current:

                idx += 1

            else:

                return False

        

        return True





# ========== LR(0) 和 SLR 分析表 ==========



class LRParser:

    """

    LR语法分析器基类

    支持LR(0)和SLR(1)

    """

    

    def __init__(self, productions: List[Production], start_symbol: NonTerminal):

        self.productions = productions

        self.start_symbol = start_symbol

        self.terminals: Set[str] = set()

        self.nonterminals: Set[str] = set()

        self.items: List[List[Item]] = []  # 项目集族

        self.parse_table: Dict[int, Dict[str, Any]] = {}  # 状态 -> 动作/跳转

        

        self._collect_symbols()

        self._build_canonical_collection()

    

    def _collect_symbols(self):

        """收集终结符和非终结符"""

        for prod in self.productions:

            self.nonterminals.add(prod.lhs.name)

            for sym in prod.rhs:

                if isinstance(sym, Terminal):

                    self.terminals.add(sym.name)

                elif isinstance(sym, NonTerminal):

                    self.nonterminals.add(sym.name)

        self.terminals.add('$')  # 输入结束标记

    

    def closure(self, items: List[Item]) -> List[Item]:

        """

        计算项目集的闭包

        LR(0)项目集闭包

        """

        result = list(items)

        queue = list(items)

        

        while queue:

            item = queue.pop(0)

            

            # 获取·后面的非终结符

            next_sym = item.next_symbol()

            if isinstance(next_sym, NonTerminal):

                # 找到该非终结符的所有产生式

                for prod in self.productions:

                    if prod.lhs.name == next_sym.name:

                        new_item = Item(prod, 0)  # ·在开始位置

                        if new_item not in result:

                            result.append(new_item)

                            queue.append(new_item)

        

        return result

    

    def goto(self, items: List[Item], symbol: GrammarSymbol) -> List[Item]:

        """

        GOTO(I, X) - 项目集I经过符号X后的项目集

        """

        next_items = []

        

        for item in items:

            next_sym = item.next_symbol()

            if next_sym and str(next_sym) == str(symbol):

                new_item = Item(item.production, item.dot_position + 1)

                next_items.append(new_item)

        

        return self.closure(next_items)

    

    def _build_canonical_collection(self):

        """构建LR(0)项目集族的规范集合"""

        # 创建增广文法的起始项目

        start_prod = Production(

            NonTerminal(f"{self.start_symbol.name}'"),

            [self.start_symbol]

        )

        all_productions = [start_prod] + self.productions

        

        start_item = Item(start_prod, 0)

        start_items = self.closure([start_item])

        

        self.items.append(start_items)

        

        # 遍历所有项目集

        for i, item_set in enumerate(self.items):

            for symbol in list(self.nonterminals) + list(self.terminals):

                next_items = self.goto(item_set, symbol)

                

                if next_items and next_items not in self.items:

                    self.items.append(next_items)

    

    def build_slr_table(self):

        """构建SLR分析表"""

        # 计算FIRST和FOLLOW

        first_calc = FirstSetCalculator(self.productions)

        follow_calc = FollowSetCalculator(self.productions, first_calc, self.start_symbol.name)

        

        # 为每个状态构建动作

        for i, item_set in enumerate(self.items):

            self.parse_table[i] = {}

            

            for item in item_set:

                if item.is_reduced():

                    # 规约动作

                    prod = item.production

                    

                    if prod.lhs.name == f"{self.start_symbol.name}'":

                        # 接受

                        self.parse_table[i]['$'] = ('accept', None)

                    else:

                        # FOLLOW集决定何时规约

                        follow_set = follow_calc.follow.get(prod.lhs.name, set())

                        for terminal in follow_set:

                            self.parse_table[i][terminal] = ('reduce', prod)

                else:

                    # 移入或跳转

                    next_sym = item.next_symbol()

                    next_items = self.goto(item_set, next_sym)

                    

                    if next_items:

                        next_state = self.items.index(next_items)

                        

                        if isinstance(next_sym, Terminal):

                            self.parse_table[i][next_sym.name] = ('shift', next_state)

                        else:

                            self.parse_table[i][next_sym.name] = ('goto', next_state)





# ========== LALR(1) 分析表 ==========



class LALRParser(LRParser):

    """

    LALR(1)语法分析器

    比LR(0)和SLR更强大，合并同心项

    """

    

    def build_lalr_table(self):

        """构建LALR(1)分析表"""

        # 1. 构建LR(0)项集族

        # 2. 合并同心项（具有相同核心的项）

        # 3. 构建分析表

        

        # 简化：使用SLR表构建方法

        self.build_slr_table()





# ========== 递归下降分析器 ==========



class RecursiveDescentParser:

    """

    递归下降语法分析器

    适用于LL(1)文法，简洁高效

    """

    

    def __init__(self, tokens: List[Tuple[str, Any]]):

        self.tokens = tokens

        self.pos = 0

    

    def current_token(self) -> Optional[Tuple[str, Any]]:

        """获取当前Token"""

        return self.tokens[self.pos] if self.pos < len(self.tokens) else ('EOF', None)

    

    def consume(self, expected_type: str):

        """消费Token"""

        token_type, token_value = self.current_token()

        if token_type == expected_type:

            self.pos += 1

        else:

            raise SyntaxError(f"期望 {expected_type}, 得到 {token_type}")

    

    def parse_program(self) -> Dict:

        """解析程序"""

        statements = []

        

        while self.current_token()[0] != 'EOF':

            stmt = self.parse_statement()

            statements.append(stmt)

        

        return {'type': 'Program', 'body': statements}

    

    def parse_statement(self) -> Dict:

        """解析语句"""

        token_type, token_value = self.current_token()

        

        if token_type == 'IF':

            return self.parse_if_statement()

        elif token_type == 'WHILE':

            return self.parse_while_statement()

        elif token_type == 'RETURN':

            return self.parse_return_statement()

        elif token_type == 'IDENT':

            return self.parse_assignment_or_expr()

        else:

            return self.parse_expression()

    

    def parse_if_statement(self) -> Dict:

        """解析if语句"""

        self.consume('IF')

        self.consume('LPAREN')

        condition = self.parse_expression()

        self.consume('RPAREN')

        

        then_block = self.parse_statement()

        

        result = {'type': 'IfStatement', 'condition': condition, 'consequent': then_block}

        

        if self.current_token()[0] == 'ELSE':

            self.consume('ELSE')

            result['alternate'] = self.parse_statement()

        

        return result

    

    def parse_while_statement(self) -> Dict:

        """解析while语句"""

        self.consume('WHILE')

        self.consume('LPAREN')

        condition = self.parse_expression()

        self.consume('RPAREN')

        body = self.parse_statement()

        

        return {'type': 'WhileStatement', 'condition': condition, 'body': body}

    

    def parse_return_statement(self) -> Dict:

        """解析return语句"""

        self.consume('RETURN')

        value = self.parse_expression()

        

        return {'type': 'ReturnStatement', 'value': value}

    

    def parse_assignment_or_expr(self) -> Dict:

        """解析赋值或表达式"""

        ident = self.current_token()[1]

        self.consume('IDENT')

        

        if self.current_token()[0] == 'ASSIGN':

            self.consume('ASSIGN')

            value = self.parse_expression()

            return {'type': 'AssignmentExpression', 'left': ident, 'right': value}

        else:

            return {'type': 'Identifier', 'name': ident}

    

    def parse_expression(self) -> Dict:

        """解析表达式"""

        return self.parse_additive()

    

    def parse_additive(self) -> Dict:

        """解析加法表达式"""

        left = self.parse_multiplicative()

        

        while self.current_token()[0] in ('PLUS', 'MINUS'):

            op = self.current_token()[0]

            self.consume(op)

            right = self.parse_multiplicative()

            left = {'type': 'BinaryExpression', 'operator': op, 'left': left, 'right': right}

        

        return left

    

    def parse_multiplicative(self) -> Dict:

        """解析乘法表达式"""

        left = self.parse_primary()

        

        while self.current_token()[0] in ('STAR', 'SLASH'):

            op = self.current_token()[0]

            self.consume(op)

            right = self.parse_primary()

            left = {'type': 'BinaryExpression', 'operator': op, 'left': left, 'right': right}

        

        return left

    

    def parse_primary(self) -> Dict:

        """解析基本表达式"""

        token_type, token_value = self.current_token()

        

        if token_type == 'NUMBER':

            self.consume('NUMBER')

            return {'type': 'Literal', 'value': token_value}

        elif token_type == 'IDENT':

            self.consume('IDENT')

            return {'type': 'Identifier', 'name': token_value}

        elif token_type == 'LPAREN':

            self.consume('LPAREN')

            expr = self.parse_expression()

            self.consume('RPAREN')

            return expr

        else:

            raise SyntaxError(f"Unexpected token: {token_type}")





if __name__ == "__main__":

    print("=" * 60)

    print("语法分析器演示")

    print("=" * 60)

    

    # 1. LL(1)分析表示例

    print("\n--- LL(1) 分析表 ---")

    grammar = {

        'S': [['IDENT', 'ASSIGN', 'E'], ['IF', 'LPAREN', 'E', 'RPAREN', 'S']],

        'E': [['E', 'PLUS', 'T'], ['T']],

        'T': [['NUMBER'], ['IDENT']]

    }

    

    ll1 = LL1Parser(grammar)

    print("LL(1)分析表构建完成")

    print(f"非终结符: {ll1.nonterminals}")

    print(f"终结符: {ll1.terminals}")

    

    # 2. LR(0)项目集族

    print("\n--- LR(0) 项目集族 ---")

    productions = [

        Production(NonTerminal('S'), [NonTerminal('E')]),

        Production(NonTerminal('E'), [Terminal('a'), NonTerminal('E')]),

        Production(NonTerminal('E'), [Terminal('b')]),

    ]

    

    lr = LRParser(productions, NonTerminal('S'))

    print(f"LR(0) 项目集数量: {len(lr.items)}")

    

    for i, item_set in enumerate(lr.items):

        print(f"  状态 {i}:")

        for item in item_set[:5]:  # 只显示前5个

            print(f"    {item}")

    

    # 3. 递归下降分析

    print("\n--- 递归下降分析 ---")

    tokens = [

        ('IF', 'if'),

        ('LPAREN', '('),

        ('IDENT', 'x'),

        ('GT', '>'),

        ('NUMBER', 0),

        ('RPAREN', ')'),

        ('RETURN', 'return'),

        ('IDENT', 'y'),

        ('SEMICOLON', ';'),

        ('EOF', None)

    ]

    

    parser = RecursiveDescentParser(tokens)

    ast = parser.parse_if_statement()

    print(f"解析结果: {ast}")





# ========== LR分析表构建辅助函数 ==========



def build_lr0_automaton(productions: List[Production], start: NonTerminal) -> Tuple[List[Set[Item]], Dict]:

    """

    构建LR(0)自动机

    返回: (项目集列表, 转换表)

    """

    # 增广文法

    augmented_prod = Production(NonTerminal(f"{start.name}'"), [start])

    all_productions = [augmented_prod] + productions

    

    # 项目集0的闭包

    start_item = Item(augmented_prod, 0)

    item_sets = [closure(set([start_item]), all_productions)]

    

    transitions = {}  # (state, symbol) -> state

    

    # BFS构建

    queue = [0]

    while queue:

        current_set_idx = queue.pop(0)

        current_set = item_sets[current_set_idx]

        

        # 收集所有可能的符号

        symbols = set()

        for item in current_set:

            next_sym = item.next_symbol()

            if next_sym:

                symbols.add(next_sym)

        

        for symbol in symbols:

            next_set = goto(current_set, symbol, all_productions)

            

            if next_set:

                # 检查是否已存在

                if next_set not in item_sets:

                    item_sets.append(next_set)

                    queue.append(len(item_sets) - 1)

                

                target_idx = item_sets.index(next_set)

                transitions[(current_set_idx, str(symbol))] = target_idx

    

    return item_sets, transitions





def closure(items: Set[Item], productions: List[Production]) -> Set[Item]:

    """计算项目集的闭包"""

    result = set(items)

    queue = list(items)

    

    while queue:

        item = queue.pop(0)

        next_sym = item.next_symbol()

        

        if isinstance(next_sym, NonTerminal):

            for prod in productions:

                if prod.lhs.name == next_sym.name:

                    new_item = Item(prod, 0)

                    if new_item not in result:

                        result.add(new_item)

                        queue.append(new_item)

    

    return result





def goto(items: Set[Item], symbol: GrammarSymbol, productions: List[Production]) -> Set[Item]:

    """计算GOTO(I, X)"""

    next_items = set()

    

    for item in items:

        if item.next_symbol() == symbol:

            new_item = Item(item.production, item.dot_position + 1)

            next_items.add(new_item)

    

    return closure(next_items, productions)

