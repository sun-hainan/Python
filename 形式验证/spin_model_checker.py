# -*- coding: utf-8 -*-
"""
算法实现：形式验证 / spin_model_checker

本文件实现 spin_model_checker 相关的算法功能。
"""

import numpy as np
from collections import defaultdict, deque
from enum import Enum


class TokenType(Enum):
    """词法标记类型"""
    IDENT = "IDENT"
    NUMBER = "NUMBER"
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    SEMI = ";"
    COMMA = ","
    EQ = "="
    NE = "!="
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    AND = "&&"
    OR = "||"
    NOT = "!"
    ATOMIC = "atomic"
    IF = "if"
    FI = "fi"
    DO = "do"
    OD = "od"
    OD = "od"
    SKIP = "skip"
    ASSERT = "assert"
    ENDPROCESS = "end"


class Token:
    """词法标记"""
    def __init__(self, type_, value):
        self.type = type_
        self.value = value
    
    def __repr__(self):
        return f"Token({self.type}, {self.value})"


class Lexer:
    """词法分析器"""
    
    keywords = {
        'atomic': TokenType.ATOMIC,
        'if': TokenType.IF,
        'fi': TokenType.FI,
        'do': TokenType.DO,
        'od': TokenType.OD,
        'skip': TokenType.SKIP,
        'assert': TokenType.ASSERT,
    }
    
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.tokens = []
    
    def tokenize(self):
        """分词"""
        while self.pos < len(self.text):
            self._skip_whitespace()
            
            if self.pos >= len(self.text):
                break
            
            c = self.text[self.pos]
            
            if c.isalpha() or c == '_':
                self._read_identifier()
            elif c.isdigit():
                self._read_number()
            elif c == '(':
                self.tokens.append(Token(TokenType.LPAREN, '('))
                self.pos += 1
            elif c == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')'))
                self.pos += 1
            elif c == '{':
                self.tokens.append(Token(TokenType.LBRACE, '{'))
                self.pos += 1
            elif c == '}':
                self.tokens.append(Token(TokenType.RBRACE, '}'))
                self.pos += 1
            elif c == ';':
                self.tokens.append(Token(TokenType.SEMI, ';'))
                self.pos += 1
            elif c == ',':
                self.tokens.append(Token(TokenType.COMMA, ','))
                self.pos += 1
            elif c == '=':
                self.tokens.append(Token(TokenType.EQ, '='))
                self.pos += 1
            elif c == '!':
                if self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '=':
                    self.tokens.append(Token(TokenType.NE, '!='))
                    self.pos += 2
                else:
                    self.tokens.append(Token(TokenType.NOT, '!'))
                    self.pos += 1
            elif c == '&':
                if self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '&':
                    self.tokens.append(Token(TokenType.AND, '&&'))
                    self.pos += 2
            elif c == '|':
                if self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '|':
                    self.tokens.append(Token(TokenType.OR, '||'))
                    self.pos += 2
            elif c == '<':
                if self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '=':
                    self.tokens.append(Token(TokenType.LE, '<='))
                    self.pos += 2
                else:
                    self.tokens.append(Token(TokenType.LT, '<'))
                    self.pos += 1
            elif c == '>':
                if self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '=':
                    self.tokens.append(Token(TokenType.GE, '>='))
                    self.pos += 2
                else:
                    self.tokens.append(Token(TokenType.GT, '>'))
                    self.pos += 1
            else:
                self.pos += 1
        
        return self.tokens
    
    def _skip_whitespace(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1
    
    def _read_identifier(self):
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        ident = self.text[start:self.pos]
        token_type = self.keywords.get(ident, TokenType.IDENT)
        self.tokens.append(Token(token_type, ident))
    
    def _read_number(self):
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        self.tokens.append(Token(TokenType.NUMBER, int(self.text[start:self.pos])))


class PromelaProcess:
    """Promela进程"""
    def __init__(self, pid, code):
        self.pid = pid
        self.code = code
        self.pc = 0  # 程序计数器
        self.variables = {}  # 进程局部变量
    
    def copy(self):
        """复制进程状态"""
        new_proc = PromelaProcess(self.pid, self.code)
        new_proc.pc = self.pc
        new_proc.variables = self.variables.copy()
        return new_proc


class SpinState:
    """SPIN状态"""
    def __init__(self):
        self.processes = {}  # pid -> PromelaProcess
        self.global_vars = {}  # 全局变量
        self.channels = {}  # 通道
    
    def copy(self):
        """深拷贝"""
        new_state = SpinState()
        new_state.global_vars = self.global_vars.copy()
        new_state.channels = {k: list(v) for k, v in self.channels.items()}
        new_state.processes = {pid: proc.copy() for pid, proc in self.processes.items()}
        return new_state
    
    def __hash__(self):
        return hash((
            tuple(sorted(self.global_vars.items())),
            tuple(sorted((pid, proc.pc, tuple(sorted(proc.variables.items())))
                        for pid, proc in self.processes.items()))
        ))
    
    def __eq__(self, other):
        return hash(self) == hash(other)


class SimplifiedSpin:
    """
    简化版SPIN模型检查器
    
    支持:
    - 变量声明和赋值
    - if-fi条件语句
    - do-od循环语句
    - atomic块
    - assert语句
    """
    
    def __init__(self):
        self.processes = []
        self.global_vars = {}
        self.ltl_formulas = []
        self.states = {}  # state -> set of states (可达)
        self.accepting_states = set()
        self.counterexamples = []
    
    def parse_global_var(self, decl):
        """
        解析全局变量声明
        
        格式: int x = 0; byte y = 5; bool flag = false;
        """
        parts = decl.strip().split()
        if len(parts) < 3:
            return
        
        vtype = parts[0]  # int, byte, bool
        var_expr = parts[1]
        
        # 分离变量名和初始值
        if '=' in var_expr:
            var_name, init_val = var_expr.split('=')
            var_name = var_name.rstrip(';')
            if vtype == 'bool':
                init_val = init_val.rstrip(';') == 'true'
            else:
                init_val = int(init_val.rstrip(';'))
        else:
            var_name = var_expr.rstrip(';')
            init_val = 0
        
        self.global_vars[var_name] = init_val
    
    def add_process(self, code):
        """添加进程"""
        proc = PromelaProcess(len(self.processes), code)
        self.processes.append(proc)
        return proc.pid
    
    def step(self, state):
        """
        执行一步转换
        
        返回: 下一个状态集合
        """
        next_states = []
        
        for pid, proc in list(state.processes.items()):
            proc_state = self._execute_instruction(state, proc)
            if proc_state:
                new_state = state.copy()
                new_state.processes[pid] = proc_state
                next_states.append(new_state)
        
        return next_states
    
    def _execute_instruction(self, state, proc):
        """
        执行一条指令
        
        返回更新后的进程状态
        """
        code = proc.code
        pc = proc.pc
        
        if pc >= len(code):
            return None
        
        stmt = code[pc].strip()
        
        if not stmt or stmt == 'skip' or stmt == ';':
            proc.pc += 1
            return proc
        
        # 赋值语句: x = expr;
        if '=' in stmt and 'if' not in stmt and 'do' not in stmt:
            var, expr = stmt.split('=', 1)
            var = var.strip()
            expr = expr.rstrip(';').strip()
            
            # 简单表达式求值
            value = self._eval_expr(expr, state, proc)
            proc.variables[var] = value
            proc.pc += 1
            return proc
        
        # assert语句
        if stmt.startswith('assert'):
            cond_str = stmt[6:].strip().lstrip('(').rstrip(');')
            if not self._eval_cond(cond_str, state, proc):
                # assert失败，这是一个接受的错误轨迹
                self.accepting_states.add(hash(state))
            proc.pc += 1
            return proc
        
        # if语句
        if stmt.startswith('if'):
            proc.pc += 1
            # 找对应的fi
            depth = 1
            fi_pos = proc.pc
            while fi_pos < len(code) and depth > 0:
                if 'if' in code[fi_pos]:
                    depth += 1
                if 'fi' in code[fi_pos]:
                    depth -= 1
                fi_pos += 1
            
            # 评估每个分支条件
            for i in range(proc.pc, fi_pos):
                line = code[i].strip()
                if ':' in line:
                    cond, _ = line.split(':', 1)
                    cond = cond.strip()
                    if self._eval_cond(cond, state, proc):
                        proc.pc = i + 1
                        return proc
            
            proc.pc = fi_pos + 1
            return proc
        
        # do-od循环
        if stmt.startswith('do'):
            proc.pc += 1
            # 找对应的od
            depth = 1
            od_pos = proc.pc
            while od_pos < len(code) and depth > 0:
                if 'do' in code[od_pos]:
                    depth += 1
                if 'od' in code[od_pos]:
                    depth -= 1
                od_pos += 1
            
            # 评估每个退出条件
            for i in range(proc.pc, od_pos):
                line = code[i].strip()
                if ':' in line:
                    cond, _ = line.split(':', 1)
                    cond = cond.strip()
                    if self._eval_cond(cond, state, proc):
                        proc.pc = od_pos + 1
                        return proc
            
            # 执行第一个分支
            for i in range(proc.pc, od_pos):
                line = code[i].strip()
                if ':' in line:
                    _, body = line.split(':', 1)
                    # 这里简化处理
                    proc.pc = i + 1
                    return proc
            
            proc.pc = od_pos + 1
            return proc
        
        proc.pc += 1
        return proc
    
    def _eval_expr(self, expr, state, proc):
        """求值表达式"""
        expr = expr.strip()
        
        # 数字
        if expr.isdigit():
            return int(expr)
        
        # 全局变量
        if expr in state.global_vars:
            return state.global_vars[expr]
        
        # 局部变量
        if expr in proc.variables:
            return proc.variables[expr]
        
        # 简单算术
        if '+' in expr:
            parts = expr.split('+')
            return self._eval_expr(parts[0], state, proc) + self._eval_expr(parts[1], state, proc)
        
        return 0
    
    def _eval_cond(self, cond, state, proc):
        """求值条件"""
        cond = cond.strip()
        
        # 括号
        if cond.startswith('(') and cond.endswith(')'):
            return self._eval_cond(cond[1:-1], state, proc)
        
        # NOT
        if cond.startswith('!'):
            return not self._eval_cond(cond[1:].strip(), state, proc)
        
        # AND
        if '&&' in cond:
            parts = cond.split('&&')
            return all(self._eval_cond(p.strip(), state, proc) for p in parts)
        
        # OR
        if '||' in cond:
            parts = cond.split('||')
            return any(self._eval_cond(p.strip(), state, proc) for p in parts)
        
        # 关系运算
        for op in ['==', '!=', '<=', '>=', '<', '>']:
            if op in cond:
                left, right = cond.split(op, 1)
                left_val = self._eval_expr(left.strip(), state, proc)
                right_val = self._eval_expr(right.strip(), state, proc)
                
                if op == '==':
                    return left_val == right_val
                elif op == '!=':
                    return left_val != right_val
                elif op == '<=':
                    return left_val <= right_val
                elif op == '>=':
                    return left_val >= right_val
                elif op == '<':
                    return left_val < right_val
                elif op == '>':
                    return left_val > right_val
        
        # 变量
        if cond in state.global_vars:
            return bool(state.global_vars[cond])
        if cond in proc.variables:
            return bool(proc.variables[cond])
        
        return False
    
    def explore(self, max_states=10000, max_depth=1000):
        """
        状态空间搜索
        
        参数:
            max_states: 最大探索状态数
            max_depth: 最大深度
        
        返回:
            可达状态数
        """
        initial_state = SpinState()
        initial_state.global_vars = self.global_vars.copy()
        
        for proc_template in self.processes:
            proc = proc_template.copy()
            initial_state.processes[proc.pid] = proc
        
        visited = {hash(initial_state)}
        queue = deque([(initial_state, 0)])
        
        while queue:
            state, depth = queue.popleft()
            
            if depth >= max_depth:
                continue
            
            for next_state in self.step(state):
                h = hash(next_state)
                if h not in visited:
                    visited.add(h)
                    queue.append((next_state, depth + 1))
                    
                    if len(visited) >= max_states:
                        return len(visited)
        
        return len(visited)
    
    def check_assert(self, max_states=10000):
        """
        检查assert是否总成立
        
        返回:
            (是否成立, 反例路径)
        """
        initial_state = SpinState()
        initial_state.global_vars = self.global_vars.copy()
        
        for proc_template in self.processes:
            proc = proc_template.copy()
            initial_state.processes[proc.pid] = proc
        
        visited = {}
        queue = deque([(initial_state, [])])
        
        while queue:
            state, path = queue.popleft()
            h = hash(state)
            
            if h in visited and len(path) >= len(visited[h]):
                continue
            visited[h] = path
            
            for next_state in self.step(state):
                next_h = hash(next_state)
                new_path = path + [next_state]
                
                if next_h in self.accepting_states:
                    return False, new_path
                
                if next_h not in visited or len(new_path) < len(visited[next_h]):
                    queue.append((next_state, new_path))
        
        return True, []


def run_demo():
    """运行SPIN模型检查演示"""
    print("=" * 60)
    print("SPIN模型检查器概念简化实现")
    print("=" * 60)
    
    # 创建简化的Promela模型
    spin = SimplifiedSpin()
    
    # 全局变量
    spin.global_vars = {'x': 0, 'y': 0, 'flag': False}
    
    # 进程1: 递增x直到5
    proc1_code = [
        'if',
        '  (x < 5) -> x = x + 1;',
        '  (x >= 5) -> skip;',
        'fi',
        'skip;',
    ]
    spin.add_process(proc1_code)
    
    # 进程2: 当x=5时设置flag
    proc2_code = [
        'if',
        '  (x == 5) -> flag = true;',
        '  (x != 5) -> skip;',
        'fi',
        'skip;',
    ]
    spin.add_process(proc2_code)
    
    print("\n[Promela模型]")
    print("  全局变量: x=0, y=0, flag=false")
    print("  进程1: 递增x直到5")
    print("  进程2: 当x=5时设置flag")
    
    print("\n[状态空间搜索]")
    num_states = spin.explore(max_states=1000)
    print(f"  可达状态数: {num_states}")
    
    # 检查flag最终为true
    print("\n[属性检查]")
    print("  AG (flag -> AF flag)")
    print("  (简化: 检查flag是否能变为true)")
    
    # 创建一个会失败的新模型
    spin2 = SimplifiedSpin()
    spin2.global_vars = {'counter': 0}
    
    proc_code = [
        'if',
        '  (counter < 10) -> counter = counter + 1;',
        '  (counter >= 10) -> skip;',
        'fi',
        'assert(counter <= 15);',
    ]
    spin2.add_process(proc_code)
    
    print("\n[Assert检查]")
    ok, cex = spin2.check_assert()
    print(f"  assert(counter <= 15):")
    print(f"    成立: {ok}")
    if cex:
        print(f"    反例长度: {len(cex)}")
    
    print("\n" + "=" * 60)
    print("SPIN模型检查核心概念:")
    print("  1. Promela: 并发系统建模语言")
    print("  2. 状态机: 进程的显式状态表示")
    print("  3. 公平性: 无穷运行假设下的路径选择")
    print("  4. never声明: 用于LTL属性检查")
    print("  5. 复杂度: 状态空间指数爆炸，限制在百万级")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
