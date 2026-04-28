# -*- coding: utf-8 -*-
"""
SMT-LIB格式解析器
功能：解析SMT-LIB 2.x格式的SMT问题文件

SMT-LIB是SMT求解器的标准输入格式
支持 theories: AUFLIA, AUFLIRA, AUFNIRA, BFPLIA, QF_ABV, QF_AUFLIA 等

作者：SMT-LIB Parser Team
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from enum import Enum


class TokenType(Enum):
    """词法标记类型"""
    LPAREN = "("
    RPAREN = ")"
    SYMBOL = "symbol"
    NUMERAL = "numeral"
    DECIMAL = "decimal"
    STRING = "string"
    KEYWORD = "keyword"


class Token:
    """词法标记"""
    def __init__(self, type_: TokenType, value: str):
        self.type = type_
        self.value = value
    
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}')"


class Lexer:
    """词法分析器：将SMT-LIB文本转换为标记流"""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.tokens: List[Token] = []

    def tokenize(self) -> List[Token]:
        """词法分析"""
        while self.pos < len(self.text):
            self._skip_whitespace()
            if self.pos >= len(self.text):
                break
            
            ch = self.text[self.pos]
            
            if ch == ';':
                self._skip_comment()
            elif ch == '(':
                self.tokens.append(Token(TokenType.LPAREN, '('))
                self.pos += 1
            elif ch == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')'))
                self.pos += 1
            elif ch == '#':
                self._read_hex()
            elif ch.isdigit():
                self._read_number()
            elif ch == '"':
                self._read_string()
            elif ch == ':':
                self._read_keyword()
            elif ch.isalpha() or ch in '+-*/=<>!?_':
                self._read_symbol()
            else:
                self.pos += 1
        
        return self.tokens

    def _skip_whitespace(self):
        """跳过空白字符"""
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def _skip_comment(self):
        """跳过注释（分号到行尾）"""
        while self.pos < len(self.text) and self.text[self.pos] != '\n':
            self.pos += 1

    def _read_hex(self):
        """读取十六进制数 #x... """
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] in '0123456789abcdefABCDEF':
            self.pos += 1
        self.tokens.append(Token(TokenType.SYMBOL, self.text[start:self.pos]))

    def _read_number(self):
        """读取数字"""
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        if self.pos < len(self.text) and self.text[self.pos] == '.':
            self.pos += 1
            while self.pos < len(self.text) and self.text[self.pos].isdigit():
                self.pos += 1
            self.tokens.append(Token(TokenType.DECIMAL, self.text[start:self.pos]))
        else:
            self.tokens.append(Token(TokenType.NUMERAL, self.text[start:self.pos]))

    def _read_string(self):
        """读取字符串"""
        self.pos += 1  # 跳过开头引号
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] != '"':
            if self.text[self.pos] == '\\':
                self.pos += 2
            else:
                self.pos += 1
        self.tokens.append(Token(TokenType.STRING, self.text[start:self.pos]))
        if self.pos < len(self.text):
            self.pos += 1  # 跳过结尾引号

    def _read_keyword(self):
        """读取关键字 :keyword """
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] in '-_'):
            self.pos += 1
        self.tokens.append(Token(TokenType.KEYWORD, self.text[start:self.pos]))

    def _read_symbol(self):
        """读取符号"""
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] in '+-*/=<>!?_.'):
            self.pos += 1
        self.tokens.append(Token(TokenType.SYMBOL, self.text[start:self.pos]))


class SMTExpr:
    """SMT表达式"""
    pass


class Identifier(SMTExpr):
    """标识符"""
    def __init__(self, name: str):
        self.name = name


class QualifiedIdent(SMTExpr):
    """限定标识符（可能带排序）"""
    def __init__(self, ident: Identifier, sort: 'SMT Sort' = None):
        self.ident = ident
        self.sort = sort


class SMTApp(SMTExpr):
    """函数应用"""
    def __init__(self, func: Identifier, args: List[SMTExpr]):
        self.func = func
        self.args = args


class SMTLet(SMTExpr):
    """let绑定"""
    def __init__(self, bindings: List[Tuple[str, SMTExpr]], body: SMTExpr):
        self.bindings = bindings
        self.body = body


class SMTForall(SMTExpr):
    """forall量词"""
    def __init__(self, vars_: List[Tuple[str, 'SMT Sort']], body: SMTExpr):
        self.vars = vars_
        self.body = body


class SMTSort:
    """SMT排序（类型）"""
    def __init__(self, name: str, params: List['SMTSort'] = None):
        self.name = name
        self.params = params or []


class Declaration:
    """声明"""
    def __init__(self, name: str, sort: SMTSort):
        self.name = name
        self.sort = sort


class Assert:
    """断言"""
    def __init__(self, term: SMTExpr):
        self.term = term


class SetLogic:
    """设置逻辑"""
    def __init__(self, logic: str):
        self.logic = logic


class SetOption:
    """设置选项"""
    def __init__(self, option: str, value: Any):
        self.option = option
        self.value = value


class Parser:
    """SMT-LIB语法分析器"""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.declarations: List[Declaration] = []
        self.assertions: List[SMTExpr] = []
        self.logic: Optional[str] = None
        self.options: Dict[str, Any] = {}

    def parse(self):
        """解析整个文件"""
        while self.pos < len(self.tokens):
            self._parse_command()
        return {
            'logic': self.logic,
            'declarations': self.declarations,
            'assertions': self.assertions,
            'options': self.options
        }

    def _peek(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _consume(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _expect(self, expected_type: TokenType, expected_value: str = None):
        token = self._consume()
        if token.type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {token.type}")
        if expected_value and token.value != expected_value:
            raise SyntaxError(f"Expected '{expected_value}', got '{token.value}'")
        return token

    def _parse_command(self):
        """解析命令"""
        token = self._peek()
        if token is None:
            return
        
        if token.type == TokenType.LPAREN:
            self._consume()
            cmd_token = self._consume()
            cmd = cmd_token.value
            
            if cmd == 'set-logic':
                logic_tok = self._consume()
                self.logic = logic_tok.value
                self._expect(TokenType.RPAREN)
            
            elif cmd == 'set-option':
                opt_tok = self._consume()
                val_tok = self._consume()
                self.options[opt_tok.value] = val_tok.value
                self._expect(TokenType.RPAREN)
            
            elif cmd == 'declare-sort':
                sym = self._consume()
                num_tok = self._consume()
                sort = SMTSort(sym.value)
                self.declarations.append(Declaration(sym.value, sort))
                self._expect(TokenType.RPAREN)
            
            elif cmd == 'declare-fun':
                name_tok = self._consume()
                self._expect(TokenType.LPAREN)  # 空参数列表
                self._expect(TokenType.RPAREN)
                sort = self._parse_sort()
                self.declarations.append(Declaration(name_tok.value, sort))
                self._expect(TokenType.RPAREN)
            
            elif cmd == 'assert':
                term = self._parse_term()
                self.assertions.append(term)
                self._expect(TokenType.RPAREN)
            
            elif cmd == 'check-sat':
                self._expect(TokenType.RPAREN)
            
            elif cmd == 'get-model':
                self._expect(TokenType.RPAREN)
            
            else:
                # 跳过未知命令
                depth = 1
                while depth > 0:
                    t = self._consume()
                    if t.type == TokenType.LPAREN:
                        depth += 1
                    elif t.type == TokenType.RPAREN:
                        depth -= 1

    def _parse_sort(self) -> SMTSort:
        """解析排序"""
        token = self._consume()
        if token.type == TokenType.LPAREN:
            name_tok = self._consume()
            params = []
            while self._peek().type != TokenType.RPAREN:
                params.append(self._parse_sort())
            self._expect(TokenType.RPAREN)
            return SMTSort(name_tok.value, params)
        else:
            return SMTSort(token.value)

    def _parse_term(self) -> SMTExpr:
        """解析项"""
        token = self._peek()
        
        if token.type == TokenType.LPAREN:
            self._consume()
            next_tok = self._peek()
            
            if next_tok.value == 'let':
                return self._parse_let()
            elif next_tok.value == 'forall':
                return self._parse_forall()
            elif next_tok.value == 'exists':
                return self._parse_exists()
            else:
                return self._parse_app()
        
        elif token.type == TokenType.SYMBOL:
            self._consume()
            return Identifier(token.value)
        
        else:
            self._consume()
            return Identifier(token.value)


def parse_smtlib(smt_str: str) -> dict:
    """解析SMT-LIB格式字符串"""
    lexer = Lexer(smt_str)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def example_parser():
    """解析示例"""
    smt_input = """
    (set-logic QF_LIA)
    (declare-const x Int)
    (declare-const y Int)
    (assert (> x 0))
    (assert (> y 0))
    (assert (= (+ x y) 10))
    (check-sat)
    """
    
    result = parse_smtlib(smt_input)
    print(f"Logic: {result['logic']}")
    print(f"Declarations: {len(result['declarations'])}")
    print(f"Assertions: {len(result['assertions'])}")


def example_simple():
    """简单SMT问题"""
    smt = """
    (set-logic QF_BV)
    (declare-const a (_ BitVec 8))
    (declare-const b (_ BitVec 8))
    (assert (= (bvmul a #x02) b))
    (check-sat)
    """
    
    result = parse_smtlib(smt)
    print(f"解析结果: {result}")


if __name__ == "__main__":
    print("=" * 50)
    print("SMT-LIB解析器 测试")
    print("=" * 50)
    
    example_parser()
    print()
    example_simple()
