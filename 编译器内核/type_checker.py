# -*- coding: utf-8 -*-

"""

算法实现：编译器内核 / type_checker



本文件实现 type_checker 相关的算法功能。

"""



from dataclasses import dataclass, field

from typing import Dict, List, Optional, Set, Tuple, Union

from enum import Enum, auto





class TypeKind(Enum):

    """类型种类"""

    INT = auto()

    FLOAT = auto()

    STRING = auto()

    BOOL = auto()

    VOID = auto()

    ARRAY = auto()

    FUNCTION = auto()

    STRUCT = auto()

    GENERIC = auto()

    UNKNOWN = auto()





@dataclass

class Type:

    """类型表示"""

    kind: TypeKind  # 类型种类

    name: str = ""  # 类型名称

    params: List['Type'] = field(default_factory=list)  # 类型参数(泛型)

    return_type: Optional['Type'] = None  # 返回类型(函数)

    element_type: Optional['Type'] = None  # 元素类型(数组)

    fields: Dict[str, 'Type'] = field(default_factory=dict)  # 字段(结构体)





class TypeEnvironment:

    """类型环境(符号表的类型部分)"""



    def __init__(self, parent: Optional['TypeEnvironment'] = None):

        self.types: Dict[str, Type] = {}  # 类型名 -> Type

        self.variables: Dict[str, Type] = {}  # 变量名 -> Type

        self.parent = parent  # 父作用域



    def define_type(self, name: str, type_info: Type):

        """定义类型"""

        self.types[name] = type_info



    def define_variable(self, name: str, var_type: Type):

        """定义变量"""

        self.variables[name] = var_type



    def lookup_type(self, name: str) -> Optional[Type]:

        """查找类型"""

        if name in self.types:

            return self.types[name]

        if self.parent:

            return self.parent.lookup_type(name)

        return None



    def lookup_variable(self, name: str) -> Optional[Type]:

        """查找变量"""

        if name in self.variables:

            return self.variables[name]

        if self.parent:

            return self.parent.lookup_variable(name)

        return None



    def push_scope(self) -> 'TypeEnvironment':

        """进入新作用域"""

        return TypeEnvironment(parent=self)



    def pop_scope(self) -> Optional['TypeEnvironment']:

        """退出作用域"""

        return self.parent





@dataclass

class ASTNode:

    """抽象语法树节点(简化版)"""

    node_type: str  # 节点类型: Program, Function, VarDecl, BinOp, Call, etc.

    value: any = None

    children: List['ASTNode'] = field(default_factory=list)

    metadata: Dict = field(default_factory=dict)





class TypeChecker:

    """

    类型检查器



    功能:

    1. 表达式类型推断

    2. 语句类型检查

    3. 函数调用匹配

    4. 类型兼容检查

    """



    def __init__(self):

        self.env = TypeEnvironment()  # 全局类型环境

        self.errors: List[str] = []  # 类型错误

        self.warnings: List[str] = []  # 警告

        self._setup_builtin_types()



    def _setup_builtin_types(self):

        """设置内置类型"""

        self.env.define_type("int", Type(TypeKind.INT, "int"))

        self.env.define_type("float", Type(TypeKind.FLOAT, "float"))

        self.env.define_type("string", Type(TypeKind.STRING, "string"))

        self.env.define_type("bool", Type(TypeKind.BOOL, "bool"))

        self.env.define_type("void", Type(TypeKind.VOID, "void"))



    def check(self, ast: ASTNode) -> bool:

        """

        检查AST的类型正确性



        返回:

            True表示无错误, False表示有错误

        """

        self.errors.clear()

        self._visit_node(ast)

        return len(self.errors) == 0



    def _visit_node(self, node: ASTNode) -> Optional[Type]:

        """遍历AST节点"""

        if node.node_type == "Program":

            return self._check_program(node)

        elif node.node_type == "Function":

            return self._check_function(node)

        elif node.node_type == "VarDecl":

            return self._check_var_decl(node)

        elif node.node_type == "BinOp":

            return self._check_binop(node)

        elif node.node_type == "Call":

            return self._check_call(node)

        elif node.node_type == "If":

            return self._check_if(node)

        elif node.node_type == "Return":

            return self._check_return(node)

        elif node.node_type == "Identifier":

            return self._check_identifier(node)

        elif node.node_type == "Literal":

            return self._infer_literal_type(node)

        return None



    def _check_program(self, node: ASTNode) -> Type:

        """检查程序节点"""

        for child in node.children:

            self._visit_node(child)

        return Type(TypeKind.VOID)



    def _check_function(self, node: ASTNode) -> Type:

        """检查函数定义"""

        func_name = node.value  # 函数名

        return_type_name = node.metadata.get("return_type", "int")

        params = node.metadata.get("params", [])  # 参数列表



        # 创建函数作用域

        func_env = self.env.push_scope()



        # 定义参数类型

        param_types = []

        for param in params:

            param_name, param_type_name = param

            param_type = self.env.lookup_type(param_type_name)

            if not param_type:

                param_type = Type(TypeKind.UNKNOWN, param_type_name)

            func_env.define_variable(param_name, param_type)

            param_types.append(param_type)



        # 构建函数类型

        func_type = Type(

            kind=TypeKind.FUNCTION,

            name=func_name,

            return_type=self.env.lookup_type(return_type_name) or Type(TypeKind.UNKNOWN, return_type_name),

            params=param_types

        )

        self.env.define_variable(func_name, func_type)



        # 检查函数体

        for stmt in node.children:

            self._visit_node(stmt)



        self.env.pop_scope()

        return func_type



    def _check_var_decl(self, node: ASTNode) -> Type:

        """检查变量声明"""

        var_name = node.value

        var_type_name = node.metadata.get("type", "int")

        init_expr = node.children[0] if node.children else None



        var_type = self.env.lookup_type(var_type_name)

        if not var_type:

            var_type = Type(TypeKind.UNKNOWN, var_type_name)



        if init_expr:

            expr_type = self._visit_node(init_expr)

            if expr_type and not self._isAssignable(expr_type, var_type):

                self.errors.append(

                    f"类型错误: 变量 '{var_name}' 类型 {var_type.name} 不能由 {expr_type.name} 赋值"

                )



        self.env.define_variable(var_name, var_type)

        return var_type



    def _check_binop(self, node: ASTNode) -> Type:

        """检查二元运算"""

        op = node.value

        left = node.children[0]

        right = node.children[1]



        left_type = self._visit_node(left)

        right_type = self._visit_node(right)



        # 算术运算

        if op in ["+", "-", "*", "/"]:

            if left_type.kind == TypeKind.INT and right_type.kind == TypeKind.INT:

                return Type(TypeKind.INT, "int")

            if left_type.kind in [TypeKind.INT, TypeKind.FLOAT] and \

               right_type.kind in [TypeKind.INT, TypeKind.FLOAT]:

                return Type(TypeKind.FLOAT, "float")

            self.errors.append(f"类型错误: 算术运算 '{op}' 不能用于 {left_type.name} 和 {right_type.name}")



        # 比较运算

        elif op in ["==", "!=", "<", ">", "<=", ">="]:

            return Type(TypeKind.BOOL, "bool")



        # 逻辑运算

        elif op in ["&&", "||"]:

            if left_type.kind != TypeKind.BOOL or right_type.kind != TypeKind.BOOL:

                self.errors.append(f"类型错误: 逻辑运算 '{op}' 需要布尔类型")

            return Type(TypeKind.BOOL, "bool")



        return Type(TypeKind.UNKNOWN, "unknown")



    def _check_call(self, node: ASTNode) -> Type:

        """检查函数调用"""

        func_name = node.value

        args = node.children



        func_type = self.env.lookup_variable(func_name)

        if not func_type or func_type.kind != TypeKind.FUNCTION:

            self.errors.append(f"错误: '{func_name}' 不是函数")

            return Type(TypeKind.UNKNOWN, "unknown")



        # 检查参数数量

        if len(args) != len(func_type.params):

            self.errors.append(

                f"参数数量错误: 函数 '{func_name}' 需要 {len(func_type.params)} 个参数, 实际 {len(args)} 个"

            )



        # 检查参数类型

        for i, (arg, expected_type) in enumerate(zip(args, func_type.params)):

            arg_type = self._visit_node(arg)

            if arg_type and not self._isAssignable(arg_type, expected_type):

                self.errors.append(

                    f"参数类型错误: 第 {i+1} 个参数类型 {arg_type.name} 不能赋给 {expected_type.name}"

                )



        return func_type.return_type or Type(TypeKind.UNKNOWN, "unknown")



    def _check_if(self, node: ASTNode) -> Type:

        """检查if语句"""

        cond = node.children[0]

        then_stmt = node.children[1] if len(node.children) > 1 else None

        else_stmt = node.children[2] if len(node.children) > 2 else None



        cond_type = self._visit_node(cond)

        if cond_type.kind != TypeKind.BOOL:

            self.errors.append(f"类型错误: if 条件必须是 bool 类型, 实际是 {cond_type.name}")



        if then_stmt:

            self._visit_node(then_stmt)

        if else_stmt:

            self._visit_node(else_stmt)



        return Type(TypeKind.VOID)



    def _check_return(self, node: ASTNode) -> Type:

        """检查return语句"""

        if node.children:

            return self._visit_node(node.children[0])

        return Type(TypeKind.VOID, "void")



    def _check_identifier(self, node: ASTNode) -> Type:

        """检查标识符"""

        name = node.value

        var_type = self.env.lookup_variable(name)

        if not var_type:

            self.errors.append(f"错误: 未定义的变量 '{name}'")

            return Type(TypeKind.UNKNOWN, "unknown")

        return var_type



    def _infer_literal_type(self, node: ASTNode) -> Type:

        """推断字面量类型"""

        value = node.value

        if isinstance(value, int):

            return Type(TypeKind.INT, "int")

        elif isinstance(value, float):

            return Type(TypeKind.FLOAT, "float")

        elif isinstance(value, str):

            return Type(TypeKind.STRING, "string")

        elif isinstance(value, bool):

            return Type(TypeKind.BOOL, "bool")

        return Type(TypeKind.UNKNOWN, "unknown")



    def _isAssignable(self, from_type: Type, to_type: Type) -> bool:

        """检查类型赋值兼容性"""

        if from_type.kind == TypeKind.UNKNOWN or to_type.kind == TypeKind.UNKNOWN:

            return True

        if from_type.kind == to_type.kind:

            return True

        # int 可以赋给 float (隐式转换)

        if from_type.kind == TypeKind.INT and to_type.kind == TypeKind.FLOAT:

            return True

        return False





def print_type_errors(checker: TypeChecker):

    """打印类型错误"""

    if checker.errors:

        print("=== 类型错误 ===")

        for err in checker.errors:

            print(f"  {err}")

    else:

        print("类型检查通过!")





if __name__ == "__main__":

    checker = TypeChecker()



    # 构建测试AST

    # int add(int a, int b) { return a + b; }

    add_func = ASTNode(

        node_type="Function",

        value="add",

        metadata={

            "return_type": "int",

            "params": [("a", "int"), ("b", "int")]

        },

        children=[

            ASTNode(

                node_type="Return",

                children=[

                    ASTNode(

                        node_type="BinOp",

                        value="+",

                        children=[

                            ASTNode(node_type="Identifier", value="a"),

                            ASTNode(node_type="Identifier", value="b")

                        ]

                    )

                ]

            )

        ]

    )



    print("=== 类型检查测试 ===")

    checker.check(add_func)

    print_type_errors(checker)



    # 测试类型不匹配

    # float x = "hello";  // 错误

    var_decl = ASTNode(

        node_type="VarDecl",

        value="x",

        metadata={"type": "float"},

        children=[ASTNode(node_type="Literal", value="hello")]

    )



    print("\n=== 类型不匹配测试 ===")

    checker.check(var_decl)

    print_type_errors(checker)



    # 测试未定义变量

    # int y = z + 1;

    var_decl2 = ASTNode(

        node_type="VarDecl",

        value="y",

        metadata={"type": "int"},

        children=[

            ASTNode(

                node_type="BinOp",

                value="+",

                children=[

                    ASTNode(node_type="Identifier", value="z"),

                    ASTNode(node_type="Literal", value=1)

                ]

            )

        ]

    )



    print("\n=== 未定义变量测试 ===")

    checker.check(var_decl2)

    print_type_errors(checker)

