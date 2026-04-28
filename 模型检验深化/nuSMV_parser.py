"""
NuSMV模型描述解析器
====================
功能：解析NuSMV风格的SMV模型描述文件
支持变量声明、模块定义、TRANS/INIT/ASSIGN等语句

NuSMV语法概要：
- VAR: 变量声明
- INIT: 初始状态约束
- TRANS: 转移关系约束
- DEFINE: 命名表达式
- ASSIGN: 变量赋值
- FAIRNESS: 公平性约束
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import re


class TokenType(Enum):
    """词法记号类型"""
    KEYWORD = auto()                             # 关键字
    IDENTIFIER = auto()                          # 标识符
    NUMBER = auto()                              # 数字
    SYMBOL = auto()                              # 符号
    LPAREN = auto()                              # 左括号
    RPAREN = auto()                              # 右括号
    COMMA = auto()                               # 逗号
    DOT = auto()                                 # 点号
    EOF = auto()                                  # 文件结束


@dataclass
class Token:
    """词法记号"""
    type: TokenType                               # 记号类型
    value: str                                   # 记号值
    line: int                                     # 行号
    column: int                                   # 列号


@dataclass
class VarDeclaration:
    """变量声明"""
    name: str                                     # 变量名
    var_type: str                                 # 变量类型: boolean, range, enum
    range_start: Optional[int] = None             # 范围下界（如为range类型）
    range_end: Optional[int] = None               # 范围上界


@dataclass
class ModuleDefinition:
    """
    模块定义
    - name: 模块名
    - vars: 变量声明列表
    - init_constraints: INIT约束
    - trans_constraints: TRANS约束
    - fairness_constraints: FAIRNESS约束
    - defines: DEFINE定义
    """
    name: str
    vars: List[VarDeclaration] = field(default_factory=list)
    init_constraints: List[str] = field(default_factory=list)
    trans_constraints: List[str] = field(default_factory=list)
    fairness_constraints: List[str] = field(default_factory=list)
    defines: Dict[str, str] = field(default_factory=dict)
    assigns: Dict[str, str] = field(default_factory=dict)


class Lexer:
    """词法分析器：SMV源码→记号流"""
    
    KEYWORDS = {
        "MODULE", "VAR", "INIT", "TRANS", "DEFINE",
        "ASSIGN", "FAIRNESS", "CONSTRAINT", "SPEC",
        "LTLSPEC", "CTLSPEC", "PROCESS", "ARRAY",
        "OF", "boolean", "signed", "unsigned", "word"
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def peek(self) -> str:
        """查看当前字符"""
        if self.pos < len(self.source):
            return self.source[self.pos]
        return '\0'
    
    def advance(self) -> str:
        """前进到下一字符"""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch
    
    def skip_whitespace(self):
        """跳过空白字符"""
        while self.pos < len(self.source) and self.peek() in ' \t\n\r':
            self.advance()
    
    def skip_comment(self):
        """跳过注释"""
        if self.peek() == '-' and self.pos + 1 < len(self.source) and self.source[self.pos + 1] == '-':
            while self.pos < len(self.source) and self.peek() != '\n':
                self.advance()
    
    def read_identifier(self) -> str:
        """读取标识符"""
        result = ""
        while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() in '_-'):
            result += self.advance()
        return result
    
    def read_number(self) -> str:
        """读取数字"""
        result = ""
        while self.pos < len(self.source) and self.peek().isdigit():
            result += self.advance()
        return result
    
    def tokenize(self) -> List[Token]:
        """执行词法分析"""
        while self.pos < len(self.source):
            self.skip_whitespace()
            self.skip_comment()
            
            if self.pos >= len(self.source):
                break
            
            ch = self.peek()
            line, col = self.line, self.column
            
            if ch.isalpha() or ch == '_':
                self.advance()
                word = ch + self.read_identifier()
                if word.upper() in self.KEYWORDS:
                    self.tokens.append(Token(TokenType.KEYWORD, word.upper(), line, col))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, word, line, col))
            
            elif ch.isdigit():
                self.advance()
                num = ch + self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, num, line, col))
            
            elif ch == '(':
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, '(', line, col))
            elif ch == ')':
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ')', line, col))
            elif ch == ',':
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ',', line, col))
            elif ch == '.':
                self.advance()
                self.tokens.append(Token(TokenType.DOT, '.', line, col))
            elif ch == ':':
                self.advance()
                self.tokens.append(Token(TokenType.SYMBOL, ':', line, col))
            elif ch == ';':
                self.advance()
                self.tokens.append(Token(TokenType.SYMBOL, ';', line, col))
            elif ch == '=':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                self.tokens.append(Token(TokenType.SYMBOL, '=', line, col))
            else:
                self.advance()
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens


class SMVParser:
    """NuSMV模型解析器"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.modules: Dict[str, ModuleDefinition] = {}
        self.main_module: Optional[ModuleDefinition] = None
        self.specs: List[str] = []
    
    def peek(self) -> Token:
        """查看当前记号"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, '', -1, -1)
    
    def advance(self) -> Token:
        """消费记号"""
        tok = self.peek()
        self.pos += 1
        return tok
    
    def expect(self, expected_type: TokenType, expected_value: str = None) -> Token:
        """期望特定记号"""
        tok = self.peek()
        if tok.type != expected_type:
            raise SyntaxError(f"期望 {expected_type}, 得到 {tok.type}")
        if expected_value and tok.value != expected_value:
            raise SyntaxError(f"期望 '{expected_value}', 得到 '{tok.value}'")
        return self.advance()
    
    def parse(self) -> 'SMVParser':
        """执行解析"""
        while self.peek().type != TokenType.EOF:
            tok = self.peek()
            
            if tok.type == TokenType.KEYWORD and tok.value == "MODULE":
                self.parse_module()
            elif tok.type == TokenType.KEYWORD and tok.value == "SPEC":
                self.parse_spec()
            else:
                self.advance()
        
        return self
    
    def parse_module(self):
        """解析模块定义"""
        self.expect(TokenType.KEYWORD, "MODULE")
        name_tok = self.expect(TokenType.IDENTIFIER)
        module = ModuleDefinition(name=name_tok.value)
        
        # 解析模块体
        self.expect(TokenType.LPAREN)
        while self.peek().type != TokenType.RPAREN:
            self.expect(TokenType.IDENTIFIER)
            if self.peek().type == TokenType.COMMA:
                self.advance()
        self.expect(TokenType.RPAREN)
        
        # 解析模块内部
        while self.peek().type != TokenType.EOF:
            tok = self.peek()
            
            if tok.type == TokenType.KEYWORD and tok.value == "VAR":
                self.parse_var(module)
            elif tok.type == TokenType.KEYWORD and tok.value == "INIT":
                self.parse_init(module)
            elif tok.type == TokenType.KEYWORD and tok.value == "TRANS":
                self.parse_trans(module)
            elif tok.type == TokenType.KEYWORD and tok.value == "FAIRNESS":
                self.parse_fairness(module)
            elif tok.type == TokenType.KEYWORD and tok.value == "DEFINE":
                self.parse_define(module)
            elif tok.type == TokenType.KEYWORD and tok.value == "ASSIGN":
                self.parse_assign(module)
            elif tok.type == TokenType.IDENTIFIER:
                # 模块结束或下一模块
                break
            else:
                self.advance()
        
        self.modules[module.name] = module
        if self.main_module is None:
            self.main_module = module
    
    def parse_var(self, module: ModuleDefinition):
        """解析VAR声明"""
        self.expect(TokenType.KEYWORD, "VAR")
        while self.peek().type == TokenType.IDENTIFIER:
            var_name_tok = self.expect(TokenType.IDENTIFIER)
            self.expect(TokenType.SYMBOL, ':')
            
            # 解析类型
            type_tok = self.peek()
            if type_tok.value == "boolean":
                self.advance()
                var_decl = VarDeclaration(var_name_tok.value, "boolean")
            else:
                self.advance()
                var_decl = VarDeclaration(var_name_tok.value, type_tok.value)
            
            module.vars.append(var_decl)
    
    def parse_init(self, module: ModuleDefinition):
        """解析INIT约束"""
        self.expect(TokenType.KEYWORD, "INIT")
        # 简化：记录约束表达式位置
        expr = self.read_expression()
        module.init_constraints.append(expr)
    
    def parse_trans(self, module: ModuleDefinition):
        """解析TRANS约束"""
        self.expect(TokenType.KEYWORD, "TRANS")
        expr = self.read_expression()
        module.trans_constraints.append(expr)
    
    def parse_fairness(self, module: ModuleDefinition):
        """解析FAIRNESS约束"""
        self.expect(TokenType.KEYWORD, "FAIRNESS")
        expr = self.read_expression()
        module.fairness_constraints.append(expr)
    
    def parse_define(self, module: ModuleDefinition):
        """解析DEFINE定义"""
        self.expect(TokenType.KEYWORD, "DEFINE")
        name_tok = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.SYMBOL, '=')
        expr = self.read_expression()
        module.defines[name_tok.value] = expr
    
    def parse_assign(self, module: ModuleDefinition):
        """解析ASSIGN赋值"""
        self.expect(TokenType.KEYWORD, "ASSIGN")
        name_tok = self.expect(TokenType.IDENTIFIER)
        self.expect(TokenType.SYMBOL, '=')
        expr = self.read_expression()
        module.assigns[name_tok.value] = expr
    
    def parse_spec(self):
        """解析SPEC规格"""
        self.expect(TokenType.KEYWORD, "SPEC")
        expr = self.read_expression()
        self.specs.append(expr)
    
    def read_expression(self) -> str:
        """读取表达式（简化实现）"""
        expr_parts = []
        paren_depth = 0
        
        while self.peek().type != TokenType.EOF:
            tok = self.peek()
            if tok.value == ';':
                if paren_depth == 0:
                    break
            if tok.value == '(':
                paren_depth += 1
            if tok.value == ')':
                paren_depth -= 1
            
            expr_parts.append(tok.value)
            self.advance()
        
        return ' '.join(expr_parts[:-1]) if expr_parts else ''


def parse_smv_file(source_code: str) -> SMVParser:
    """
    解析SMV模型文件
    入口函数
    
    Args:
        source_code: SMV模型源码
    
    Returns:
        SMVParser解析器（包含解析结果）
    """
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    parser = SMVParser(tokens)
    return parser.parse()


# ----------------------- 测试代码 -----------------------

if __name__ == "__main__":
    sample_smv = """
-- 简单互斥模型
MODULE main
VAR
    x : boolean;
    y : boolean;
INIT
    x = FALSE & y = FALSE
TRANS
    (x = FALSE -> next(x) = TRUE) &
    (x = TRUE -> next(x) = FALSE) &
    (y = FALSE -> next(y) = TRUE) &
    (y = TRUE -> next(y) = FALSE)
FAIRNESS
    x = TRUE
SPEC
    AG (x != y)
"""
    
    print("=" * 50)
    print("NuSMV模型解析器测试")
    print("=" * 50)
    
    parser = parse_smv_file(sample_smv)
    
    print(f"\n解析结果:")
    print(f"  模块数量: {len(parser.modules)}")
    print(f"  主模块: {parser.main_module.name if parser.main_module else 'None'}")
    
    if parser.main_module:
        mod = parser.main_module
        print(f"  变量数: {len(mod.vars)}")
        print(f"  INIT约束: {mod.init_constraints}")
        print(f"  TRANS约束数: {len(mod.trans_constraints)}")
        print(f"  FAIRNESS约束数: {len(mod.fairness_constraints)}")
    
    print(f"  规格数: {len(parser.specs)}")
    for i, spec in enumerate(parser.specs):
        print(f"    SPEC {i+1}: {spec}")
    
    print("\n✓ NuSMV解析器测试完成")
