# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / query_compiler



本文件实现 query_compiler 相关的算法功能。

"""



from typing import List, Optional, Tuple, Dict, Any

from dataclasses import dataclass

from enum import Enum, auto



# ========== 词法分析器 (Lexer) ==========



class TokenType(Enum):

    """Token类型"""

    KEYWORD = auto()       # 关键字 (SELECT, FROM, WHERE, etc.)

    IDENTIFIER = auto()   # 标识符 (表名, 列名)

    NUMBER = auto()       # 数字

    STRING = auto()       # 字符串常量

    OPERATOR = auto()     # 运算符 (+, -, *, /, =, >, <, etc.)

    LPAREN = auto()       # 左括号

    RPAREN = auto()       # 右括号

    COMMA = auto()        # 逗号

    DOT = auto()          # 点

    EOF = auto()          # 结束符





@dataclass

class Token:

    """Token对象"""

    token_type: TokenType

    value: Any

    line: int = 0

    column: int = 0

    

    def __repr__(self):

        return f"Token({self.token_type.name}, {repr(self.value)})"





class Lexer:

    """

    词法分析器

    将SQL字符串转换为Token流

    """

    

    KEYWORDS = {

        'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT',

        'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET',

        'DELETE', 'CREATE', 'TABLE', 'DROP', 'ALTER',

        'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'ON',

        'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT',

        'AS', 'IN', 'BETWEEN', 'LIKE', 'IS', 'NULL',

        'DISTINCT', 'ALL', 'UNION', 'INTERSECT', 'EXCEPT'

    }

    

    def __init__(self, text: str):

        self.text = text                    # 输入文本

        self.pos = 0                        # 当前读取位置

        self.line = 1

        self.column = 1

    

    def _skip_whitespace(self):

        """跳过空白字符"""

        while self.pos < len(self.text) and self.text[self.pos].isspace():

            if self.text[self.pos] == '\n':

                self.line += 1

                self.column = 1

            else:

                self.column += 1

            self.pos += 1

    

    def _read_identifier(self) -> str:

        """读取标识符"""

        start = self.pos

        while self.pos < len(self.text) and (

            self.text[self.pos].isalnum() or self.text[self.pos] == '_'

        ):

            self.pos += 1

            self.column += 1

        return self.text[start:self.pos]

    

    def _read_number(self) -> float:

        """读取数字"""

        start = self.pos

        has_dot = False

        while self.pos < len(self.text) and (

            self.text[self.pos].isdigit() or self.text[self.pos] == '.'

        ):

            if self.text[self.pos] == '.':

                if has_dot:

                    break

                has_dot = True

            self.pos += 1

            self.column += 1

        return float(self.text[start:self.pos])

    

    def _read_string(self) -> str:

        """读取字符串常量"""

        self.pos += 1  # 跳过开头的引号

        self.column += 1

        start = self.pos

        quote_char = self.text[self.pos - 1]

        

        while self.pos < len(self.text) and self.text[self.pos] != quote_char:

            if self.text[self.pos] == '\\' and self.pos + 1 < len(self.text):

                self.pos += 2  # 转义字符

            else:

                self.pos += 1

            self.column += 1

        

        if self.pos < len(self.text):

            self.pos += 1  # 跳过结尾引号

            self.column += 1

        

        return self.text[start:self.pos - 1]

    

    def _read_operator(self) -> str:

        """读取运算符"""

        op_map = {

            '>=': '>=', '<=': '<=', '!=': '!=', '<>': '<>',

            '=': '=', '>': '>', '<': '<',

            '+': '+', '-': '-', '*': '*', '/': '/', '%': '%'

        }

        

        # 尝试两字符运算符

        if self.pos + 1 < len(self.text):

            two_char = self.text[self.pos:self.pos + 2]

            if two_char in op_map:

                self.pos += 2

                self.column += 2

                return two_char

        

        # 单字符运算符

        one_char = self.text[self.pos]

        if one_char in op_map:

            self.pos += 1

            self.column += 1

            return one_char

        

        return ''

    

    def next_token(self) -> Token:

        """获取下一个Token"""

        self._skip_whitespace()

        

        if self.pos >= len(self.text):

            return Token(TokenType.EOF, None, self.line, self.column)

        

        char = self.text[self.pos]

        

        # 标识符或关键字

        if char.isalpha() or char == '_':

            ident = self._read_identifier()

            token_type = TokenType.KEYWORD if ident.upper() in self.KEYWORDS else TokenType.IDENTIFIER

            return Token(token_type, ident, self.line, self.column)

        

        # 数字

        if char.isdigit():

            num = self._read_number()

            return Token(TokenType.NUMBER, num, self.line, self.column)

        

        # 字符串

        if char in ('"', "'"):

            s = self._read_string()

            return Token(TokenType.STRING, s, self.line, self.column)

        

        # 运算符

        if char in '=<>!+-*/%':

            op = self._read_operator()

            return Token(TokenType.OPERATOR, op, self.line, self.column)

        

        # 括号

        if char == '(':

            self.pos += 1

            self.column += 1

            return Token(TokenType.LPAREN, '(', self.line, self.column - 1)

        

        if char == ')':

            self.pos += 1

            self.column += 1

            return Token(TokenType.RPAREN, ')', self.line, self.column - 1)

        

        # 逗号

        if char == ',':

            self.pos += 1

            self.column += 1

            return Token(TokenType.COMMA, ',', self.line, self.column - 1)

        

        # 点

        if char == '.':

            self.pos += 1

            self.column += 1

            return Token(TokenType.DOT, '.', self.line, self.column - 1)

        

        # 未知字符，跳过

        self.pos += 1

        self.column += 1

        return self.next_token()

    

    def tokenize(self) -> List[Token]:

        """将整个输入转换为Token列表"""

        tokens = []

        while True:

            token = self.next_token()

            tokens.append(token)

            if token.token_type == TokenType.EOF:

                break

        return tokens





# ========== 语法分析器 (Parser) ==========



@dataclass

class ASTNode:

    """抽象语法树节点基类"""

    pass





@dataclass

class SelectNode(ASTNode):

    """SELECT语句节点"""

    columns: List[Any]           # 列表达式列表

    from_clause: Any              # FROM子句

    where: Optional[Any] = None   # WHERE条件

    group_by: List[Any] = None

    having: Optional[Any] = None

    order_by: List[Any] = None

    limit: Optional[int] = None





@dataclass

class TableNode(ASTNode):

    """表引用节点"""

    table_name: str

    alias: Optional[str] = None





@dataclass

class ColumnNode(ASTNode):

    """列引用节点"""

    name: str

    table: Optional[str] = None





@dataclass

class BinaryOpNode(ASTNode):

    """二元操作节点"""

    left: Any

    operator: str

    right: Any





@dataclass

class LiteralNode(ASTNode):

    """字面量节点"""

    value: Any





class Parser:

    """

    语法分析器（递归下降）

    将Token流解析为AST

    """

    

    def __init__(self, tokens: List[Token]):

        self.tokens = tokens

        self.pos = 0

    

    def _current_token(self) -> Token:

        """获取当前Token"""

        if self.pos < len(self.tokens):

            return self.tokens[self.pos]

        return Token(TokenType.EOF, None, 0, 0)

    

    def _consume(self, expected_type: TokenType = None, 

                 expected_value: str = None) -> Token:

        """消费一个Token"""

        token = self._current_token()

        

        if expected_type and token.token_type != expected_type:

            raise SyntaxError(f"Expected {expected_type}, got {token.token_type}")

        

        if expected_value and token.value != expected_value:

            raise SyntaxError(f"Expected '{expected_value}', got '{token.value}'")

        

        self.pos += 1

        return token

    

    def _peek(self) -> Token:

        """查看下一个Token但不消费"""

        saved_pos = self.pos

        token = self._current_token()

        self.pos = saved_pos

        return token

    

    def parse_select(self) -> SelectNode:

        """解析SELECT语句"""

        # SELECT

        self._consume(TokenType.KEYWORD, 'SELECT')

        

        # 列

        columns = self._parse_column_list()

        

        # FROM

        from_clause = None

        if self._current_token().value == 'FROM':

            self._consume(TokenType.KEYWORD, 'FROM')

            from_clause = self._parse_table_reference()

        

        # WHERE

        where = None

        if self._current_token().value == 'WHERE':

            self._consume(TokenType.KEYWORD, 'WHERE')

            where = self._parse_expression()

        

        # ORDER BY

        order_by = None

        if self._current_token().value == 'ORDER':

            self._consume(TokenType.KEYWORD, 'ORDER')

            self._consume(TokenType.KEYWORD, 'BY')

            order_by = self._parse_column_list()

        

        return SelectNode(

            columns=columns,

            from_clause=from_clause,

            where=where,

            order_by=order_by

        )

    

    def _parse_column_list(self) -> List[Any]:

        """解析列表达式列表"""

        columns = [self._parse_expression()]

        

        while self._current_token().token_type == TokenType.COMMA:

            self._consume(TokenType.COMMA)

            columns.append(self._parse_expression())

        

        return columns

    

    def _parse_table_reference(self) -> TableNode:

        """解析表引用"""

        table_name = self._consume(TokenType.IDENTIFIER).value

        alias = None

        

        # 检查AS别名

        if self._current_token().value == 'AS':

            self._consume(TokenType.KEYWORD, 'AS')

            alias = self._consume(TokenType.IDENTIFIER).value

        elif self._current_token().token_type == TokenType.IDENTIFIER:

            # 没有AS关键字的别名

            alias = self._current_token().value

            self.pos += 1

        

        return TableNode(table_name=table_name, alias=alias)

    

    def _parse_expression(self) -> ASTNode:

        """解析表达式（简单实现）"""

        left = self._parse_primary()

        

        if self._current_token().token_type == TokenType.OPERATOR:

            op = self._consume().value

            right = self._parse_expression()

            return BinaryOpNode(left=left, operator=op, right=right)

        

        return left

    

    def _parse_primary(self) -> ASTNode:

        """解析基本表达式"""

        token = self._current_token()

        

        if token.token_type == TokenType.NUMBER:

            self._consume()

            return LiteralNode(value=token.value)

        

        if token.token_type == TokenType.STRING:

            self._consume()

            return LiteralNode(value=token.value)

        

        if token.token_type == TokenType.IDENTIFIER:

            self._consume()

            # 检查是否是有表名的列

            if self._current_token().token_type == TokenType.DOT:

                self._consume()  # 消费点

                col_name = self._consume(TokenType.IDENTIFIER).value

                return ColumnNode(name=col_name, table=token.value)

            return ColumnNode(name=token.value)

        

        if token.token_type == TokenType.LPAREN:

            self._consume()

            expr = self._parse_expression()

            self._consume(TokenType.RPAREN)

            return expr

        

        raise SyntaxError(f"Unexpected token: {token}")





# ========== 查询重写 (Query Rewriter) ==========



class QueryRewriter:

    """

    查询重写器

    应用优化规则：谓词下推、常量折叠等

    """

    

    def __init__(self, ast: ASTNode):

        self.ast = ast

    

    def rewrite(self) -> ASTNode:

        """执行所有重写规则"""

        self._predicate_push_down()

        self._constant_folding()

        self._subquery_flattening()

        return self.ast

    

    def _predicate_push_down(self):

        """谓词下推：将Filter尽可能下推到叶子节点"""

        # 简化实现

        pass

    

    def _constant_folding(self):

        """常量折叠：在编译时计算常量表达式"""

        def fold(node: ASTNode) -> ASTNode:

            if isinstance(node, BinaryOpNode):

                left = fold(node.left)

                right = fold(node.right)

                

                if isinstance(left, LiteralNode) and isinstance(right, LiteralNode):

                    # 可以在编译时计算

                    result = self._evaluate_constant(node.operator, left.value, right.value)

                    return LiteralNode(value=result)

                

                return BinaryOpNode(left=left, operator=node.operator, right=right)

            

            return node

        

        if hasattr(self.ast, 'where') and self.ast.where:

            self.ast.where = fold(self.ast.where)

    

    def _evaluate_constant(self, op: str, left: Any, right: Any) -> Any:

        """计算常量表达式"""

        if op == '+':

            return left + right

        elif op == '-':

            return left - right

        elif op == '*':

            return left * right

        elif op == '/':

            return left / right if right != 0 else None

        elif op == '=':

            return left == right

        elif op == '>':

            return left > right

        elif op == '<':

            return left < right

        return None

    

    def _subquery_flattening(self):

        """子查询扁平化"""

        pass





if __name__ == "__main__":

    print("=" * 60)

    print("查询编译演示")

    print("=" * 60)

    

    # 测试词法分析

    sql = "SELECT id, name, price * 1.1 AS new_price FROM orders WHERE status = 'active' AND amount > 100 ORDER BY amount DESC"

    

    print("\n--- 词法分析 ---")

    lexer = Lexer(sql)

    tokens = lexer.tokenize()

    

    print("Token流:")

    for token in tokens:

        print(f"  {token}")

    

    # 测试语法分析

    print("\n--- 语法分析 ---")

    parser = Parser(tokens)

    ast = parser.parse_select()

    

    print(f"解析结果: {ast}")

    

    # 测试查询重写

    print("\n--- 查询重写 ---")

    rewriter = QueryRewriter(ast)

    optimized = rewriter.rewrite()

    

    print(f"优化后: {optimized}")

    

    print("\n查询编译流程:")

    print("  1. 词法分析: SQL字符串 -> Token流")

    print("  2. 语法分析: Token流 -> AST（抽象语法树）")

    print("  3. 语义分析: 类型检查、作用域解析")

    print("  4. 查询重写: 谓词下推、常量折叠、子查询扁平化")

    print("  5. 计划生成: AST -> 执行计划")

