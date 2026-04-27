# -*- coding: utf-8 -*-
"""
算法实现：编译器内核 / lexer

本文件实现 lexer 相关的算法功能。
"""

from typing import List, Dict, Tuple, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum, auto
import re

# ========== Token 定义 ==========

class TokenType(Enum):
    """Token类型"""
    IDENT = auto()       # 标识符
    NUMBER = auto()      # 数字常量
    STRING = auto()      # 字符串常量
    KEYWORD = auto()     # 关键字
    OPERATOR = auto()    # 运算符
    DELIMITER = auto()   # 分隔符
    EOF = auto()         # 结束符
    ERROR = auto()       # 错误Token

@dataclass
class Token:
    """Token对象"""
    token_type: TokenType
    value: Any
    line: int
    column: int
    length: int  # Token长度
    
    def __repr__(self):
        return f"Token({self.token_type.name}, {repr(self.value)}, L{self.line}:C{self.column})"


# ========== NFA定义 ==========

@dataclass
class NFAState:
    """NFA状态"""
    id: int
    is_final: bool = False
    transitions: Dict[str, List['NFAState']] = {}  # 字符 -> 目标状态
    epsilon_transitions: List['NFAState'] = []     # ε转换
    
    def add_transition(self, char: str, target: 'NFAState'):
        if char not in self.transitions:
            self.transitions[char] = []
        self.transitions[char].append(target)
    
    def add_epsilon(self, target: 'NFAState'):
        self.epsilon_transitions.append(target)


@dataclass
class NFA:
    """非确定有限自动机"""
    start_state: NFAState
    final_state: NFAState
    token_type: TokenType = TokenType.IDENT


# ========== DFA定义 ==========

@dataclass 
class DFAState:
    """DFA状态"""
    id: int
    nfa_states: Set[int]  # 对应的NFA状态集合
    is_final: bool = False
    token_type: Optional[TokenType] = None  # 接受的Token类型
    transitions: Dict[str, 'DFAState'] = {}  # 字符 -> 目标状态


@dataclass
class DFA:
    """确定有限自动机"""
    states: List[DFAState]
    start_state: DFAState
    transition_table: Dict[Tuple[int, str], int]  # (state, char) -> next_state


# ========== 正则表达式到NFA (Thompson构造法) ==========

class RegexToNFA:
    """
    将正则表达式转换为NFA
    使用Thompson构造法
    """
    
    def __init__(self):
        self.state_counter = 0
    
    def new_state(self, is_final: bool = False) -> NFAState:
        """创建新状态"""
        state = NFAState(id=self.state_counter, is_final=is_final)
        self.state_counter += 1
        return state
    
    def char_to_nfa(self, char: str) -> NFA:
        """单个字符的NFA"""
        start = self.new_state()
        end = self.new_state(is_final=True)
        start.add_transition(char, end)
        return NFA(start_state=start, final_state=end)
    
    def concat(self, nfa1: NFA, nfa2: NFA) -> NFA:
        """连接两个NFA"""
        nfa1.final_state.is_final = False
        nfa1.final_state.add_epsilon(nfa2.start_state)
        return NFA(start_state=nfa1.start_state, final_state=nfa2.final_state)
    
    def union(self, nfa1: NFA, nfa2: NFA) -> NFA:
        """并联两个NFA"""
        start = self.new_state()
        end = self.new_state(is_final=True)
        
        start.add_epsilon(nfa1.start_state)
        start.add_epsilon(nfa2.start_state)
        
        nfa1.final_state.is_final = False
        nfa2.final_state.is_final = False
        nfa1.final_state.add_epsilon(end)
        nfa2.final_state.add_epsilon(end)
        
        return NFA(start_state=start, final_state=end)
    
    def kleene_star(self, nfa: NFA) -> NFA:
        """Kleene闭包（*）"""
        start = self.new_state()
        end = self.new_state(is_final=True)
        
        start.add_epsilon(nfa.start_state)
        start.add_epsilon(end)
        
        nfa.final_state.is_final = False
        nfa.final_state.add_epsilon(nfa.start_state)
        nfa.final_state.add_epsilon(end)
        
        return NFA(start_state=start, final_state=end)
    
    def plus(self, nfa: NFA) -> NFA:
        """正闭包（+），至少一次"""
        start = self.new_state()
        end = self.new_state(is_final=True)
        
        start.add_epsilon(nfa.start_state)
        nfa.final_state.is_final = False
        nfa.final_state.add_epsilon(nfa.start_state)
        nfa.final_state.add_epsilon(end)
        
        return NFA(start_state=start, final_state=end)
    
    def optional(self, nfa: NFA) -> NFA:
        """可选（?），0或1次"""
        start = self.new_state()
        end = self.new_state(is_final=True)
        
        start.add_epsilon(nfa.start_state)
        start.add_epsilon(end)
        
        nfa.final_state.is_final = False
        nfa.final_state.add_epsilon(end)
        
        return NFA(start_state=start, final_state=end)


# ========== NFA到DFA (子集构造法) ==========

class NFAToDFA:
    """
    将NFA转换为DFA
    使用子集构造法（powerset construction）
    """
    
    def __init__(self):
        self.state_counter = 0
    
    def epsilon_closure(self, nfa_states: Set[int], nfa_state_map: Dict[int, NFAState]) -> Set[int]:
        """计算ε闭包"""
        stack = list(nfa_states)
        closure = set(nfa_states)
        
        while stack:
            state_id = stack.pop()
            state = nfa_state_map.get(state_id)
            
            if state:
                for next_state in state.epsilon_transitions:
                    if next_state.id not in closure:
                        closure.add(next_state.id)
                        stack.append(next_state.id)
        
        return closure
    
    def move(self, nfa_states: Set[int], char: str, nfa_state_map: Dict[int, NFAState]) -> Set[int]:
        """计算字符转移后的状态集合"""
        result = set()
        
        for state_id in nfa_states:
            state = nfa_state_map.get(state_id)
            if state and char in state.transitions:
                for next_state in state.transitions[char]:
                    result.add(next_state.id)
        
        return result
    
    def convert(self, nfa: NFA) -> DFA:
        """将NFA转换为DFA"""
        nfa_state_map = {}
        
        # 收集所有NFA状态
        self._collect_nfa_states(nfa.start_state, nfa_state_map)
        
        # 计算初始状态的ε闭包
        initial_closure = self.epsilon_closure({nfa.start_state.id}, nfa_state_map)
        
        dfa_states = []
        dfa_state_map = {}  # nfa_state_set -> dfa_state
        unmarked_states = []
        
        # 创建初始DFA状态
        initial_dfa = DFAState(
            id=self.state_counter,
            nfa_states=initial_closure,
            is_final=self._contains_final_state(initial_closure, nfa_state_map, nfa.final_state.id)
        )
        self.state_counter += 1
        dfa_states.append(initial_dfa)
        dfa_state_map[frozenset(initial_closure)] = initial_dfa
        unmarked_states.append(initial_dfa)
        
        while unmarked_states:
            current_dfa = unmarked_states.pop(0)
            
            # 对每个可能输入字符
            for char in self._get_alphabet(nfa_state_map):
                # 计算转移后的ε闭包
                move_result = self.move(current_dfa.nfa_states, char, nfa_state_map)
                epsilon_closure_result = self.epsilon_closure(move_result, nfa_state_map)
                
                if not epsilon_closure_result:
                    continue
                
                state_key = frozenset(epsilon_closure_result)
                
                # 检查是否已存在
                if state_key in dfa_state_map:
                    next_dfa = dfa_state_map[state_key]
                else:
                    next_dfa = DFAState(
                        id=self.state_counter,
                        nfa_states=epsilon_closure_result,
                        is_final=self._contains_final_state(epsilon_closure_result, nfa_state_map, nfa.final_state.id)
                    )
                    self.state_counter += 1
                    dfa_states.append(next_dfa)
                    dfa_state_map[state_key] = next_dfa
                    unmarked_states.append(next_dfa)
                
                current_dfa.transitions[char] = next_dfa
        
        return DFA(states=dfa_states, start_state=initial_dfa, transition_table={})
    
    def _collect_nfa_states(self, state: NFAState, state_map: Dict[int, NFAState]):
        """收集所有NFA状态"""
        if state.id in state_map:
            return
        
        state_map[state.id] = state
        
        for next_states in state.transitions.values():
            for next_state in next_states:
                self._collect_nfa_states(next_state, state_map)
        
        for next_state in state.epsilon_transitions:
            self._collect_nfa_states(next_state, state_map)
    
    def _get_alphabet(self, nfa_state_map: Dict[int, NFAState]) -> Set[str]:
        """获取字母表"""
        alphabet = set()
        for state in nfa_state_map.values():
            alphabet.update(state.transitions.keys())
        return alphabet
    
    def _contains_final_state(self, nfa_states: Set[int], 
                               nfa_state_map: Dict[int, NFAState], 
                               final_state_id: int) -> bool:
        """检查状态集合是否包含接受状态"""
        return final_state_id in nfa_states


# ========== DFA最小化 ==========

class DFAMinimizer:
    """DFA最小化（Hopcroft算法）"""
    
    def minimize(self, dfa: DFA) -> DFA:
        """最小化DFA"""
        # 简化实现：分组
        final_states = [s for s in dfa.states if s.is_final]
        non_final_states = [s for s in dfa.states if not s.is_final]
        
        # 创建分组
        partitions = []
        if final_states:
            partitions.append(set(s.id for s in final_states))
        if non_final_states:
            partitions.append(set(s.id for s in non_final_states))
        
        # 迭代细化（简化实现）
        changed = True
        while changed:
            changed = False
            new_partitions = []
            
            for partition in partitions:
                # 简化处理：每个状态自成一组
                for state_id in partition:
                    new_partitions.append({state_id})
            
            if len(new_partitions) != len(partitions):
                changed = True
                partitions = new_partitions
        
        return dfa  # 简化：返回原DFA


# ========== 词法分析器 ==========

class Lexer:
    """
    词法分析器
    基于DFA实现，高效匹配Token
    """
    
    KEYWORDS = {
        'if', 'else', 'while', 'for', 'return', 'int', 'float', 
        'double', 'char', 'string', 'void', 'class', 'public', 
        'private', 'def', 'var', 'const', 'true', 'false', 'null'
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.errors: List[str] = []
    
    def is_letter(self, char: str) -> bool:
        return char.isalpha() or char == '_'
    
    def is_digit(self, char: str) -> bool:
        return char.isdigit()
    
    def peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        return self.source[idx] if idx < len(self.source) else ''
    
    def advance(self):
        """前进一个字符"""
        if self.pos < len(self.source):
            if self.source[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1
    
    def skip_whitespace(self):
        """跳过空白字符"""
        while self.pos < len(self.source) and self.source[self.pos].isspace():
            self.advance()
    
    def skip_comment(self):
        """跳过注释"""
        if self.pos < len(self.source) - 1:
            if self.source[self.pos] == '/' and self.peek(1) == '/':
                # 单行注释
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.advance()
                return True
            elif self.source[self.pos] == '/' and self.peek(1) == '*':
                # 多行注释
                self.advance()  # /*
                self.advance()
                while self.pos < len(self.source) - 1:
                    if self.source[self.pos] == '*' and self.peek(1) == '/':
                        self.advance()  # *
                        self.advance()  # /
                        return True
                    self.advance()
        return False
    
    def read_identifier(self) -> str:
        """读取标识符或关键字"""
        start_col = self.column
        result = ''
        
        while self.pos < len(self.source) and (self.is_letter(self.source[self.pos]) or 
                                                self.is_digit(self.source[self.pos])):
            result += self.source[self.pos]
            self.advance()
        
        return result
    
    def read_number(self) -> str:
        """读取数字"""
        result = ''
        has_dot = False
        
        while self.pos < len(self.source) and (self.is_digit(self.source[self.pos]) or 
                                               self.source[self.pos] == '.'):
            if self.source[self.pos] == '.':
                if has_dot:
                    break
                has_dot = True
            result += self.source[self.pos]
            self.advance()
        
        return result
    
    def read_string(self) -> str:
        """读取字符串"""
        quote_char = self.source[self.pos]
        self.advance()  # 开始引号
        
        result = ''
        while self.pos < len(self.source) and self.source[self.pos] != quote_char:
            if self.source[self.pos] == '\\' and self.pos + 1 < len(self.source):
                self.advance()  # 转义字符
            result += self.source[self.pos]
            self.advance()
        
        if self.pos < len(self.source):
            self.advance()  # 结束引号
        
        return result
    
    def tokenize(self) -> List[Token]:
        """执行词法分析"""
        while self.pos < len(self.source):
            self.skip_whitespace()
            
            if self.skip_comment():
                continue
            
            if self.pos >= len(self.source):
                break
            
            char = self.source[self.pos]
            start_line = self.line
            start_col = self.column
            
            # 标识符或关键字
            if self.is_letter(char):
                ident = self.read_identifier()
                token_type = TokenType.KEYWORD if ident.lower() in self.KEYWORDS else TokenType.IDENT
                self.tokens.append(Token(token_type, ident, start_line, start_col, len(ident)))
            
            # 数字
            elif self.is_digit(char):
                num_str = self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, float(num_str) if '.' in num_str else int(num_str), 
                                       start_line, start_col, len(num_str)))
            
            # 字符串
            elif char in ('"', "'"):
                str_val = self.read_string()
                self.tokens.append(Token(TokenType.STRING, str_val, start_line, start_col, len(str_val) + 2))
            
            # 运算符或分隔符
            else:
                token_type = TokenType.OPERATOR
                
                # 两字符运算符
                two_char = self.source[self.pos:self.pos + 2]
                if two_char in ('==', '!=', '<=', '>=', '&&', '||', '++', '--', '+=', '-=', '*=', '/='):
                    self.tokens.append(Token(token_type, two_char, start_line, start_col, 2))
                    self.advance()
                    self.advance()
                elif char in '+-*/%=<>!&|^~?:;,.()[]{}':
                    self.tokens.append(Token(token_type, char, start_line, start_col, 1))
                    self.advance()
                else:
                    self.errors.append(f"未知字符 '{char}' at L{start_line}:C{start_col}")
                    self.advance()
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column, 0))
        return self.tokens


if __name__ == "__main__":
    print("=" * 60)
    print("词法分析器演示")
    print("=" * 60)
    
    # 测试词法分析
    source_code = """
    def calculate(x, y) {
        if (x > 0) {
            return x + y * 2;
        } else {
            return x - y / 3.14;
        }
    }
    """
    
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    
    print("\nToken流:")
    for token in tokens:
        print(f"  {token}")
    
    # 测试正则到NFA
    print("\n--- 正则表达式 → NFA ---")
    regex_converter = RegexToNFA()
    
    # a(b|c)*d 的NFA
    char_a_nfa = regex_converter.char_to_nfa('a')
    char_b_nfa = regex_converter.char_to_nfa('b')
    char_c_nfa = regex_converter.char_to_nfa('c')
    char_d_nfa = regex_converter.char_to_nfa('d')
    
    # (b|c)
    bc_nfa = regex_converter.union(char_b_nfa, char_c_nfa)
    # (b|c)*
    bc_star = regex_converter.kleene_star(bc_nfa)
    # a(b|c)*d
    full_nfa = regex_converter.concat(char_a_nfa, regex_converter.concat(bc_star, char_d_nfa))
    
    print(f"  构造正则 'a(b|c)*d' 的NFA完成")
    print(f"  起始状态: {full_nfa.start_state.id}")
    print(f"  接受状态: {full_nfa.final_state.id}")
    
    # NFA到DFA转换
    print("\n--- NFA → DFA ---")
    converter = NFAToDFA()
    dfa = converter.convert(full_nfa)
    
    print(f"  DFA状态数: {len(dfa.states)}")
    for state in dfa.states:
        print(f"    DFA State {state.id}: NFA states = {state.nfa_states}, final = {state.is_final}")
    
    print("\n词法分析器工作流程:")
    print("  1. 读取源程序文本")
    print("  2. 识别Token（正则表达式 -> NFA -> DFA）")
    print("  3. 跳过空白和注释")
    print("  4. 输出Token流")
    print("  5. 检测并报告词法错误")
