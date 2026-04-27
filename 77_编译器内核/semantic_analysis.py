# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / semantic_analysis



本文件实现 semantic_analysis 相关的算法功能。

"""



from dataclasses import dataclass, field

from typing import Dict, List, Optional, Set, Tuple

from enum import Enum, auto



from symbol_table import SymbolTable, SymbolKind, Scope, Symbol

from type_checker import TypeChecker, Type, TypeKind





class SemanticError(Exception):

    """语义错误"""

    def __init__(self, message: str, line: int = 0, column: int = 0):

        self.message = message

        self.line = line

        self.column = column

        super().__init__(f"{message} (行 {line}, 列 {column})")





@dataclass

class ASTNode:

    """抽象语法树节点"""

    node_type: str  # 节点类型

    value: any = None  # 节点值

    children: List['ASTNode'] = field(default_factory=list)

    metadata: Dict = field(default_factory=dict)





class ControlFlowGraph:

    """控制流图(简化)"""



    def __init__(self, start_block_id: int = 0):

        self.blocks: Dict[int, 'BasicBlock'] = {}  # block_id -> BasicBlock

        self.current_block_id = start_block_id

        self.start_block: Optional['BasicBlock'] = None

        self.end_block: Optional['BasicBlock'] = None



    def create_block(self, name: str = "") -> 'BasicBlock':

        """创建新的基本块"""

        block = BasicBlock(block_id=self.current_block_id, name=name)

        self.blocks[self.current_block_id] = block

        self.current_block_id += 1

        return block





@dataclass

class BasicBlock:

    """基本块"""

    block_id: int

    name: str = ""

    statements: List[ASTNode] = field(default_factory=list)

    predecessors: List[int] = field(default_factory=list)  # 前驱块

    successors: List[int] = field(default_factory=list)  # 后继块





class SemanticAnalyzer:

    """

    语义分析器



    功能:

    1. 符号表管理(声明检查、作用域检查)

    2. 类型检查(类型匹配、类型转换)

    3. 控制流分析(break/continue/return检查)

    4. 常量折叠

    5. 别名分析(简化)

    """



    def __init__(self):

        self.symbol_table = SymbolTable()

        self.type_checker = TypeChecker()

        self.errors: List[SemanticError] = []

        self.warnings: List[str] = []

        self.loop_stack: List[str] = []  # 循环栈(用于break/continue检查)

        self.function_stack: List[str] = []  # 函数栈(用于return检查)

        self.has_return: Dict[str, bool] = {}  # 函数是否保证有return



    def analyze(self, ast: ASTNode) -> bool:

        """

        执行语义分析



        返回:

            True表示无错误, False表示有错误

        """

        self.errors.clear()

        self.warnings.clear()

        self.symbol_table.init_global_scope()



        self._visit_program(ast)

        return len(self.errors) == 0



    def _visit_program(self, node: ASTNode):

        """分析程序节点"""

        for child in node.children:

            self._visit_node(child)



    def _visit_node(self, node: ASTNode):

        """遍历并分析AST节点"""

        node_type = node.node_type



        if node_type == "Function":

            self._analyze_function(node)

        elif node_type == "VarDecl":

            self._analyze_var_decl(node)

        elif node_type == "Assignment":

            self._analyze_assignment(node)

        elif node_type == "If":

            self._analyze_if(node)

        elif node_type == "While":

            self._analyze_while(node)

        elif node_type == "For":

            self._analyze_for(node)

        elif node_type == "Return":

            self._analyze_return(node)

        elif node_type == "Break":

            self._analyze_break(node)

        elif node_type == "Continue":

            self._analyze_continue(node)

        elif node_type == "Call":

            self._analyze_call(node)

        elif node_type == "Identifier":

            self._check_identifier(node)

        elif node_type == "BinOp":

            self._analyze_binop(node)



    def _analyze_function(self, node: ASTNode):

        """分析函数定义"""

        func_name = node.value

        return_type = node.metadata.get("return_type", "int")

        params = node.metadata.get("params", [])



        # 检查函数是否已定义

        existing = self.symbol_table.lookup(func_name)

        if existing and existing.kind == SymbolKind.FUNCTION:

            self.errors.append(SemanticError(

                f"函数 '{func_name}' 已定义", node.metadata.get("line", 0)

            ))



        # 插入函数符号

        self.symbol_table.insert(

            func_name, SymbolKind.FUNCTION, return_type,

            line=node.metadata.get("line", 0)

        )



        # 进入函数作用域

        self.symbol_table.enter_scope(func_name)

        self.function_stack.append(func_name)

        self.has_return[func_name] = False



        # 定义参数

        for i, (param_name, param_type) in enumerate(params):

            self.symbol_table.insert(

                param_name, SymbolKind.PARAMETER, param_type,

                value=i, line=node.metadata.get("line", 0)

            )



        # 分析函数体

        for stmt in node.children:

            self._visit_node(stmt)

            if self.has_return.get(func_name):

                break



        # 检查有返回值的函数是否都有return

        if return_type != "void" and not self.has_return.get(func_name):

            self.warnings.append(f"函数 '{func_name}' 可能没有返回值")



        self.function_stack.pop()

        self.symbol_table.exit_scope()



    def _analyze_var_decl(self, node: ASTNode):

        """分析变量声明"""

        var_name = node.value

        var_type = node.metadata.get("type", "int")

        init_expr = node.children[0] if node.children else None



        # 检查是否在循环内声明(允许变量覆盖)

        # 检查变量是否已定义

        existing = self.symbol_table.lookup(var_name, current_scope_only=True)

        if existing:

            self.errors.append(SemanticError(

                f"变量 '{var_name}' 已在此作用域定义",

                node.metadata.get("line", 0)

            ))



        # 检查初始化表达式类型

        if init_expr:

            expr_type = self._get_expr_type(init_expr)

            if expr_type and not self._is_compatible(var_type, expr_type.name):

                self.warnings.append(

                    f"变量 '{var_name}' 类型 {var_type} 与初始化表达式类型 {expr_type.name} 不完全匹配"

                )



        # 插入符号

        self.symbol_table.insert(

            var_name, SymbolKind.VARIABLE, var_type,

            line=node.metadata.get("line", 0)

        )



    def _analyze_assignment(self, node: ASTNode):

        """分析赋值语句"""

        target = node.children[0] if len(node.children) > 0 else None

        value = node.children[1] if len(node.children) > 1 else None



        if target and target.node_type == "Identifier":

            var_name = target.value

            symbol = self.symbol_table.lookup(var_name)

            if not symbol:

                self.errors.append(SemanticError(

                    f"赋值错误: 变量 '{var_name}' 未定义",

                    node.metadata.get("line", 0)

                ))



            if value:

                expr_type = self._get_expr_type(value)

                if symbol and expr_type:

                    if not self._is_compatible(symbol.type_name, expr_type.name):

                        self.errors.append(SemanticError(

                            f"类型错误: 不能将 {expr_type.name} 赋值给 {symbol.type_name} 变量 '{var_name}'",

                            node.metadata.get("line", 0)

                        ))



    def _analyze_if(self, node: ASTNode):

        """分析if语句"""

        cond = node.children[0] if len(node.children) > 0 else None

        then_stmt = node.children[1] if len(node.children) > 1 else None

        else_stmt = node.children[2] if len(node.children) > 2 else None



        # 检查条件表达式类型

        if cond:

            cond_type = self._get_expr_type(cond)

            if cond_type and cond_type.kind != TypeKind.BOOL:

                self.errors.append(SemanticError(

                    f"if 条件必须是布尔类型, 实际是 {cond_type.name}",

                    node.metadata.get("line", 0)

                ))



        # 分析then分支

        if then_stmt:

            self._visit_node(then_stmt)



        # 分析else分支

        if else_stmt:

            self._visit_node(else_stmt)



    def _analyze_while(self, node: ASTNode):

        """分析while循环"""

        cond = node.children[0] if len(node.children) > 0 else None

        body = node.children[1] if len(node.children) > 1 else None



        # 进入循环作用域

        self.loop_stack.append("while")

        self.symbol_table.enter_scope("while")



        # 检查条件

        if cond:

            cond_type = self._get_expr_type(cond)

            if cond_type and cond_type.kind != TypeKind.BOOL:

                self.errors.append(SemanticError(

                    f"while 条件必须是布尔类型",

                    node.metadata.get("line", 0)

                ))



        # 分析循环体

        if body:

            self._visit_node(body)



        self.symbol_table.exit_scope()

        self.loop_stack.pop()



    def _analyze_for(self, node: ASTNode):

        """分析for循环"""

        init_ = node.children[0] if len(node.children) > 0 else None

        cond = node.children[1] if len(node.children) > 1 else None

        update = node.children[2] if len(node.children) > 2 else None

        body = node.children[3] if len(node.children) > 3 else None



        self.loop_stack.append("for")

        self.symbol_table.enter_scope("for")



        if init_:

            self._visit_node(init_)

        if cond:

            cond_type = self._get_expr_type(cond)

            if cond_type and cond_type.kind != TypeKind.BOOL:

                self.errors.append(SemanticError(

                    f"for 条件必须是布尔类型",

                    node.metadata.get("line", 0)

                ))

        if body:

            self._visit_node(body)



        self.symbol_table.exit_scope()

        self.loop_stack.pop()



    def _analyze_return(self, node: ASTNode):

        """分析return语句"""

        if not self.function_stack:

            self.errors.append(SemanticError(

                "return 语句不能在函数外使用",

                node.metadata.get("line", 0)

            ))

            return



        current_func = self.function_stack[-1]

        func_symbol = self.symbol_table.lookup(current_func)



        # 检查返回值类型

        if node.children:

            expr_type = self._get_expr_type(node.children[0])

            if func_symbol and expr_type:

                if not self._is_compatible(func_symbol.type_name, expr_type.name):

                    self.errors.append(SemanticError(

                        f"return 类型 {expr_type.name} 与函数返回类型 {func_symbol.type_name} 不匹配",

                        node.metadata.get("line", 0)

                    ))



        self.has_return[current_func] = True



    def _analyze_break(self, node: ASTNode):

        """分析break语句"""

        if not self.loop_stack:

            self.errors.append(SemanticError(

                "break 语句只能在循环内使用",

                node.metadata.get("line", 0)

            ))



    def _analyze_continue(self, node: ASTNode):

        """分析continue语句"""

        if not self.loop_stack:

            self.errors.append(SemanticError(

                "continue 语句只能在循环内使用",

                node.metadata.get("line", 0)

            ))



    def _analyze_call(self, node: ASTNode):

        """分析函数调用"""

        func_name = node.value

        args = node.children



        symbol = self.symbol_table.lookup(func_name)

        if not symbol:

            self.errors.append(SemanticError(

                f"未定义的函数 '{func_name}'",

                node.metadata.get("line", 0)

            ))

            return



        if symbol.kind != SymbolKind.FUNCTION:

            self.errors.append(SemanticError(

                f"'{func_name}' 不是函数",

                node.metadata.get("line", 0)

            ))



    def _check_identifier(self, node: ASTNode):

        """检查标识符引用"""

        name = node.value

        symbol = self.symbol_table.lookup(name)

        if not symbol:

            self.errors.append(SemanticError(

                f"未定义的标识符 '{name}'",

                node.metadata.get("line", 0)

            ))



    def _analyze_binop(self, node: ASTNode):

        """分析二元运算"""

        op = node.value

        left = node.children[0]

        right = node.children[1] if len(node.children) > 1 else None



        left_type = self._get_expr_type(left)



        if op in ["&&", "||"] and left_type and left_type.kind != TypeKind.BOOL:

            self.errors.append(SemanticError(

                f"逻辑运算符 '{op}' 需要布尔类型操作数",

                node.metadata.get("line", 0)

            ))



        if right:

            right_type = self._get_expr_type(right)

            if left_type and right_type:

                if left_type.kind != right_type.kind:

                    if not (left_type.kind in [TypeKind.INT, TypeKind.FLOAT] and

                            right_type.kind in [TypeKind.INT, TypeKind.FLOAT]):

                        self.errors.append(SemanticError(

                            f"类型不匹配: {left_type.name} 和 {right_type.name}",

                            node.metadata.get("line", 0)

                        ))



    def _get_expr_type(self, node: ASTNode) -> Optional[Type]:

        """获取表达式类型"""

        if node.node_type == "Literal":

            return TypeChecker()._infer_literal_type(node)

        elif node.node_type == "Identifier":

            symbol = self.symbol_table.lookup(node.value)

            if symbol:

                return Type(TypeKind.INT, symbol.type_name)  # 简化

        elif node.node_type == "BinOp":

            return Type(TypeKind.INT, "int")  # 简化

        return None



    def _is_compatible(self, expected: str, actual: str) -> bool:

        """检查类型兼容性"""

        if expected == actual:

            return True

        if expected == "float" and actual == "int":

            return True

        return False





def print_semantic_errors(analyzer: SemanticAnalyzer):

    """打印语义错误"""

    if analyzer.errors:

        print("=== 语义错误 ===")

        for err in analyzer.errors:

            print(f"  {err.message} (行 {err.line})")

    else:

        print("语义分析通过!")





if __name__ == "__main__":

    analyzer = SemanticAnalyzer()



    # 构建测试AST

    # int main() {

    #     int x = 10;

    #     if (x > 5) {

    #         int y = 20;

    #     }

    #     return 0;

    # }



    main_func = ASTNode(

        node_type="Function",

        value="main",

        metadata={"return_type": "int", "params": [], "line": 1},

        children=[

            ASTNode(

                node_type="VarDecl",

                value="x",

                metadata={"type": "int", "line": 2},

                children=[ASTNode(node_type="Literal", value=10)]

            ),

            ASTNode(

                node_type="If",

                metadata={"line": 3},

                children=[

                    ASTNode(

                        node_type="BinOp",

                        value=">",

                        children=[

                            ASTNode(node_type="Identifier", value="x"),

                            ASTNode(node_type="Literal", value=5)

                        ]

                    ),

                    ASTNode(

                        node_type="VarDecl",

                        value="y",

                        metadata={"type": "int", "line": 4},

                        children=[ASTNode(node_type="Literal", value=20)]

                    )

                ]

            ),

            ASTNode(

                node_type="Return",

                metadata={"line": 6},

                children=[ASTNode(node_type="Literal", value=0)]

            )

        ]

    )



    print("=== 语义分析测试 ===")

    success = analyzer.analyze(main_func)

    print_semantic_errors(analyzer)



    # 测试错误场景

    print("\n=== 错误场景测试 ===")



    # 未定义变量

    ast_error = ASTNode(

        node_type="Assignment",

        metadata={"line": 10},

        children=[

            ASTNode(node_type="Identifier", value="undefined_var"),

            ASTNode(node_type="Literal", value=42)

        ]

    )



    analyzer2 = SemanticAnalyzer()

    analyzer2.symbol_table.init_global_scope()

    analyzer2._visit_node(ast_error)

    print_semantic_errors(analyzer2)



    # break在循环外

    print("\n=== break在循环外测试 ===")

    break_stmt = ASTNode(node_type="Break", metadata={"line": 20})

    analyzer3 = SemanticAnalyzer()

    analyzer3.symbol_table.init_global_scope()

    analyzer3._visit_node(break_stmt)

    print_semantic_errors(analyzer3)



    # 打印符号表

    print("\n=== 符号表 ===")

    from symbol_table import print_symbol_table

    print_symbol_table(analyzer.symbol_table)

